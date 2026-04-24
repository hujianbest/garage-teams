"""Host install adapter registry and ``--hosts`` argument resolver.

Implements F007 FR-707 + design D7 §11.1 / ADR-D7-1.
F009 (FR-902 + ADR-D9-6 + ADR-D9-9) adds:

- Optional ``target_skill_path_user`` / ``target_agent_path_user`` methods
  on ``HostInstallAdapter`` (return absolute Path under ``Path.home()``).
- ``host_id`` MUST NOT contain literal ``:`` character (used as scope
  override delimiter in ``--hosts <host>:<scope>`` syntax). Enforced by
  import-time assert in ``_build_registry()``.
- ``resolve_hosts_arg`` returns ``list[tuple[str, str | None]]`` (host_id +
  optional per-host scope override) instead of ``list[str]``.
- New ``UnknownScopeError`` for invalid scope values.

Design choice (ADR-D7-1):
    The install-time adapter (``HostInstallAdapter`` here) is a **separate
    Protocol** from F001 ``HostAdapterProtocol`` (runtime execution). Each
    host can have two distinct classes — e.g. ``ClaudeCodeAdapter`` (runtime,
    F001) and ``ClaudeInstallAdapter`` (install, F007) — because the two
    concerns are orthogonal: invoking a skill is unrelated to deciding
    where to drop a SKILL.md file at init time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

# F009 ADR-D9-1: scope literal type. Used by FR-901/902 + manifest schema 2.
ScopeLiteral = Literal["project", "user"]
SUPPORTED_SCOPES: tuple[str, ...] = ("project", "user")


class UnknownHostError(ValueError):
    """Raised when a host id is not found in HOST_REGISTRY.

    The error message must enumerate the supported host ids so users can
    self-correct without having to read source.
    """


class UnknownScopeError(ValueError):
    """F009: Raised when a scope value is not in SUPPORTED_SCOPES.

    Symmetric with UnknownHostError. The error message must enumerate the
    supported scopes so users can self-correct without having to read source.
    """


@runtime_checkable
class HostInstallAdapter(Protocol):
    """Install-time adapter mapping (skill_id, agent_id) to host-specific paths.

    Each first-class host implements this protocol with these slots:

    - ``host_id``: stable identifier; must equal the key in HOST_REGISTRY.
      **MUST NOT contain literal ``:`` character** (F009 ADR-D9-9 — used as
      scope override delimiter in ``--hosts <host>:<scope>`` syntax).
    - ``target_skill_path(skill_id)``: project-scope (cwd-relative) ``Path``
      to the installed SKILL.md. Mandatory for every host.
    - ``target_agent_path(agent_id)``: project-scope (cwd-relative) ``Path``
      to the installed agent file, or ``None`` if the host has no native
      agent surface (e.g. Cursor).
    - ``target_skill_path_user(skill_id)``: F009 user-scope (absolute,
      ``Path.home()``-rooted) ``Path`` to the installed SKILL.md.
    - ``target_agent_path_user(agent_id)``: F009 user-scope (absolute) Path
      to the installed agent file, or ``None`` if no agent surface in user
      scope (cursor: returns ``None`` like project scope).
    - ``target_context_path(name)``: F010 (FR-1004 + ADR-D10-2) project-scope
      (cwd-relative) ``Path`` to the host's auto-loaded context surface file
      (CLAUDE.md / .cursor/rules/<name>.mdc / .opencode/AGENTS.md). The
      ``name`` parameter is currently used only by cursor (for ``<name>.mdc``);
      claude/opencode use a fixed filename and ignore ``name``.
    - ``target_context_path_user(name)``: F010 user-scope (absolute) ``Path``
      to the host's auto-loaded context surface file under ``Path.home()``.
    - ``render(content)``: optional content transform applied before write;
      defaults to identity passthrough. Reserved for future host-specific
      metadata injection beyond the standard marker.
    """

    host_id: str

    def target_skill_path(self, skill_id: str) -> Path: ...
    def target_agent_path(self, agent_id: str) -> Path | None: ...
    def target_skill_path_user(self, skill_id: str) -> Path: ...
    def target_agent_path_user(self, agent_id: str) -> Path | None: ...
    def target_context_path(self, name: str) -> Path: ...
    def target_context_path_user(self, name: str) -> Path: ...
    def render(self, content: str) -> str: ...


def _build_registry() -> dict[str, HostInstallAdapter]:
    """Construct HOST_REGISTRY at import time.

    Indirected through a function so tests can introspect without triggering
    circular imports between this module and adapters/hosts/*.

    F009 ADR-D9-9: assert no host_id contains literal ``:`` (scope override
    delimiter). Triple守门: docstring + import-time assert + test.
    """
    # Local import to keep the Protocol module standalone-importable without
    # pulling adapter implementations.
    from garage_os.adapter.installer.hosts.claude import ClaudeInstallAdapter
    from garage_os.adapter.installer.hosts.cursor import CursorInstallAdapter
    from garage_os.adapter.installer.hosts.opencode import OpenCodeInstallAdapter

    registry: dict[str, HostInstallAdapter] = {
        "claude": ClaudeInstallAdapter(),
        "opencode": OpenCodeInstallAdapter(),
        "cursor": CursorInstallAdapter(),
    }

    # F009 ADR-D9-9 host_id 命名约束 import-time 守门
    invalid = [hid for hid in registry if ":" in hid]
    assert not invalid, (
        f"F009 ADR-D9-9 violation: host_id MUST NOT contain literal ':' "
        f"(used as --hosts <host>:<scope> override delimiter). Offenders: {invalid}"
    )

    return registry


HOST_REGISTRY: dict[str, HostInstallAdapter] = _build_registry()


def list_host_ids() -> list[str]:
    """Return all registered host ids in stable ASCII-sorted order.

    Used by ``garage init --hosts all`` to expand to the full first-class
    set, and by the unknown-host error message to enumerate alternatives.
    """
    return sorted(HOST_REGISTRY.keys())


def get_adapter(host_id: str) -> HostInstallAdapter:
    """Fetch the install adapter for ``host_id``.

    Raises:
        UnknownHostError: when ``host_id`` is not in ``HOST_REGISTRY``. The
            error enumerates supported ids per FR-702 acceptance #4.
    """
    try:
        return HOST_REGISTRY[host_id]
    except KeyError:
        supported = ", ".join(list_host_ids())
        raise UnknownHostError(
            f"Unknown host: {host_id}. Supported hosts: {supported}"
        ) from None


def resolve_hosts_arg(arg: str) -> list[tuple[str, str | None]]:
    """Resolve a ``--hosts`` argument value to a sorted host (host_id, scope_override?) list.

    Accepted shapes:

    - ``"all"``  → every registered host id with ``scope_override=None``, ASCII sorted
    - ``"none"`` → empty list
    - ``""``     → empty list (matches "none" semantics for safety)
    - ``"a,b,c"`` → individual host ids; whitespace trimmed; deduped; sorted; ``scope_override=None``
    - ``"a:user,b:project,c"`` → F009 per-host scope override syntax (FR-902 + ADR-D9-9):
        - ``a:user`` → ``("a", "user")``
        - ``b:project`` → ``("b", "project")``
        - ``c`` → ``("c", None)`` (用 ``--scope`` 全局默认)

    Returns:
        list[tuple[str, str | None]]: 按 (host_id ASCII, scope_override stable order) 排序，
        每项为 ``(host_id, scope_override)`` 二元组。``scope_override=None`` 表示用 ``--scope``
        全局默认 (CLI 层接收后注入)。

    Raises:
        UnknownHostError: when any host id is not registered.
        UnknownScopeError: when any scope value is not in SUPPORTED_SCOPES (F009).
    """
    if arg in ("all",):
        # F009: ``all`` 默认 scope_override=None (用 --scope 全局默认)
        return [(hid, None) for hid in list_host_ids()]
    if arg in ("", "none"):
        return []

    tokens = [token.strip() for token in arg.split(",")]
    tokens = [t for t in tokens if t]  # drop empty after trim

    # F009 FR-902: parse each token as either "<host>" or "<host>:<scope>"
    parsed: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    for token in tokens:
        if ":" in token:
            host_part, scope_part = token.split(":", 1)
            host_part = host_part.strip()
            scope_part = scope_part.strip()
            if host_part not in HOST_REGISTRY:
                supported = ", ".join(list_host_ids())
                raise UnknownHostError(
                    f"Unknown host: {host_part}. Supported hosts: {supported}"
                )
            if scope_part not in SUPPORTED_SCOPES:
                supported_scopes = ", ".join(SUPPORTED_SCOPES)
                raise UnknownScopeError(
                    f"Unknown scope: {scope_part} in '{token}'. "
                    f"Supported scopes: {supported_scopes}"
                )
            entry: tuple[str, str | None] = (host_part, scope_part)
        else:
            if token not in HOST_REGISTRY:
                supported = ", ".join(list_host_ids())
                raise UnknownHostError(
                    f"Unknown host: {token}. Supported hosts: {supported}"
                )
            entry = (token, None)

        if entry not in seen:
            seen.add(entry)
            parsed.append(entry)

    # F009: 排序按 host_id ASCII (主键), scope_override 稳定 (None < 'project' < 'user')
    return sorted(parsed, key=lambda x: (x[0], x[1] or ""))
