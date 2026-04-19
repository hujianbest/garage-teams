"""Host install adapter registry and ``--hosts`` argument resolver.

Implements F007 FR-707 + design D7 §11.1 / ADR-D7-1.

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
from typing import Optional, Protocol, runtime_checkable


class UnknownHostError(ValueError):
    """Raised when a host id is not found in HOST_REGISTRY.

    The error message must enumerate the supported host ids so users can
    self-correct without having to read source.
    """


@runtime_checkable
class HostInstallAdapter(Protocol):
    """Install-time adapter mapping (skill_id, agent_id) to host-specific paths.

    Each first-class host implements this protocol with three slots:

    - ``host_id``: stable identifier; must equal the key in HOST_REGISTRY.
    - ``target_skill_path(skill_id)``: project-root-relative ``Path`` to the
      installed SKILL.md. Mandatory for every host.
    - ``target_agent_path(agent_id)``: project-root-relative ``Path`` to the
      installed agent file, or ``None`` if the host has no native agent
      surface (e.g. Cursor).
    - ``render(content)``: optional content transform applied before write;
      defaults to identity passthrough. Reserved for future host-specific
      metadata injection beyond the standard marker.
    """

    host_id: str

    def target_skill_path(self, skill_id: str) -> Path: ...
    def target_agent_path(self, agent_id: str) -> Optional[Path]: ...
    def render(self, content: str) -> str: ...


def _build_registry() -> dict[str, HostInstallAdapter]:
    """Construct HOST_REGISTRY at import time.

    Indirected through a function so tests can introspect without triggering
    circular imports between this module and adapters/hosts/*.
    """
    # Local import to keep the Protocol module standalone-importable without
    # pulling adapter implementations.
    from garage_os.adapter.installer.hosts.claude import ClaudeInstallAdapter
    from garage_os.adapter.installer.hosts.cursor import CursorInstallAdapter
    from garage_os.adapter.installer.hosts.opencode import OpenCodeInstallAdapter

    return {
        "claude": ClaudeInstallAdapter(),
        "opencode": OpenCodeInstallAdapter(),
        "cursor": CursorInstallAdapter(),
    }


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


def resolve_hosts_arg(arg: str) -> list[str]:
    """Resolve a ``--hosts`` argument value to a sorted, deduplicated host id list.

    Accepted shapes (FR-702):

    - ``"all"``  → every registered host id, ASCII sorted
    - ``"none"`` → empty list
    - ``""``     → empty list (matches "none" semantics for safety)
    - ``"a,b,c"`` → individual host ids; whitespace trimmed; deduped; sorted

    Raises:
        UnknownHostError: when any member of a comma list is not registered.
    """
    if arg in ("all",):
        return list_host_ids()
    if arg in ("", "none"):
        return []

    tokens = [token.strip() for token in arg.split(",")]
    tokens = [t for t in tokens if t]  # drop empty after trim

    # Validate each token before returning, so the user gets a clear error
    # listing all supported ids (consistent with get_adapter's error shape).
    seen: set[str] = set()
    for token in tokens:
        if token not in HOST_REGISTRY:
            supported = ", ".join(list_host_ids())
            raise UnknownHostError(
                f"Unknown host: {token}. Supported hosts: {supported}"
            )
        seen.add(token)

    return sorted(seen)
