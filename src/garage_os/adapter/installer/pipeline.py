"""End-to-end install pipeline: ``packs/`` → host directories.

Implements F007 FR-704 / FR-706a / FR-706b / FR-708 + design D7 §10 / §14.

Five phases:

1. **discover**: walk ``packs/`` → list[Pack]
2. **resolve targets**: compute (src, dst, host, pack_id) tuples via adapter
3. **decide**: for each target, classify as WRITE_NEW / UPDATE_FROM_SOURCE /
   SKIP_LOCALLY_MODIFIED / OVERWRITE_FORCED based on existing manifest +
   on-disk content hash
4. **apply**: execute writes (skipping no-op writes per NFR-702 mtime rule);
   emit stable stderr markers for skipped/forced cases
5. **manifest**: write the new manifest with updated entries

All file IO is concentrated here so the lower-level modules
(pack_discovery / marker / manifest / hosts) remain pure and unit-testable.
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import IO

from garage_os.adapter.installer.host_registry import (
    HostInstallAdapter,
    UnknownHostError,
    get_adapter,
)
from garage_os.adapter.installer.manifest import (
    MANIFEST_SCHEMA_VERSION,
    Manifest,
    ManifestFileEntry,
    UserHomeNotFoundError,
    read_manifest,
    write_manifest,
)
from garage_os.adapter.installer.marker import (
    MalformedFrontmatterError,
    SourceKind,
    inject,
)
from garage_os.adapter.installer.pack_discovery import (
    InvalidPackError,
    Pack,
    PackManifestMismatchError,
    discover_packs,
)

# Stable stderr/stdout markers; CLI layer (cli.py) imports these or matches on prefix.
WARN_LOCALLY_MODIFIED_FMT = "Skipped {path} (locally modified, pass --force to overwrite)"
WARN_OVERWRITE_FORCED_FMT = "Overwrote locally modified file {path}"
MSG_NO_PACKS_FMT = "No packs found under {packs_root}"


class ConflictingSkillError(ValueError):
    """Raised when two packs ship the same skill_id targeting the same dst."""


class WriteAction(Enum):
    WRITE_NEW = "write_new"
    UPDATE_FROM_SOURCE = "update_from_source"  # tracked & unchanged-locally
    SKIP_LOCALLY_MODIFIED = "skip_locally_modified"
    OVERWRITE_FORCED = "overwrite_forced"


@dataclass(frozen=True)
class _Target:
    src_abs: Path
    dst_abs: Path
    src_rel: str  # POSIX, project-rooted
    dst_rel: str  # POSIX (project-rooted for project scope; absolute home-rooted for user scope, F009)
    host: str
    pack_id: str
    source_kind: SourceKind  # "skill" or "agent"
    skill_or_agent_id: str
    # F009 ADR-D9-2: scope 字段 (project / user). 默认 "project" 兼容 F007/F008 既有调用方
    # (CON-901 严守: phase 1 + phase 3 算法主体字节级不变, 仅扩展 type signature).
    scope: str = "project"


@dataclass
class InstallSummary:
    """Returned to the CLI layer for stdout marker formatting."""

    n_skills: int
    n_agents: int
    hosts: list[str] = field(default_factory=list)


def install_packs(
    workspace_root: Path,
    packs_root: Path,
    hosts: list[str],
    *,
    force: bool = False,
    scopes_per_host: dict[str, str] | None = None,
    stderr: IO[str] | None = None,
    stdout: IO[str] | None = None,
) -> InstallSummary:
    """Install all packs under ``packs_root`` into the requested ``hosts``.

    Args:
        workspace_root: Project root (parent of ``.garage/``).
        packs_root: Usually ``workspace_root / "packs"``; passed explicitly so
            tests can fixture-construct alternate locations.
        hosts: Pre-resolved host id list (CLI layer handles ``all``/``none``).
        force: When True, overwrite locally-modified files; otherwise skip.
        scopes_per_host: F009 (FR-906 + ADR-D9-2) optional dict mapping host_id
            → "project" | "user". Hosts not present default to "project"
            (CON-901 兼容). When None (F007/F008 既有调用), 全部 host 默认
            "project" 完全等价 F007/F008 行为字节级.
        stderr / stdout: Streams for stable markers; default to ``sys.stderr``
            / ``sys.stdout``.

    Returns:
        InstallSummary with counts and the host list.

    Raises:
        UnknownHostError: when any host id is not in HOST_REGISTRY.
        ConflictingSkillError: when two packs ship the same skill_id mapping
            to the same dst (CLI maps to exit code 2).
        InvalidPackError / PackManifestMismatchError: from pack_discovery.
        MalformedFrontmatterError: from marker.inject for bad SKILL.md.
        OSError: for file system errors (CLI maps to exit code 1).
    """
    # F009 ADR-D9-2: 归一化 scopes_per_host (None 或缺失 host → "project")
    scopes_resolved: dict[str, str] = {h: "project" for h in hosts}
    if scopes_per_host is not None:
        for host_id, scope in scopes_per_host.items():
            if host_id in scopes_resolved:
                scopes_resolved[host_id] = scope
    err = stderr if stderr is not None else sys.stderr
    out = stdout if stdout is not None else sys.stdout

    # Phase 1: discover (may raise InvalidPackError / PackManifestMismatchError).
    packs = discover_packs(packs_root)

    # Resolve adapters early so unknown host fails before we touch disk.
    adapters: dict[str, HostInstallAdapter] = {h: get_adapter(h) for h in hosts}

    # Phase 2: resolve targets + conflict detection.
    targets = _resolve_targets(workspace_root, packs, adapters, scopes_resolved)
    _check_conflicts(targets)

    if not packs:
        # Spec FR-704 acceptance #3: no packs → empty manifest, stdout note,
        # but installed_hosts records the user's choice.
        print(MSG_NO_PACKS_FMT.format(packs_root=packs_root), file=out)
        manifest = Manifest(
            schema_version=MANIFEST_SCHEMA_VERSION,
            installed_hosts=sorted(set(hosts)),
            installed_packs=[],
            installed_at=_now_iso(),
            files=[],
        )
        # Merge with any existing manifest so prior installs aren't dropped.
        merged = _merge_with_existing(workspace_root, manifest)
        write_manifest(workspace_root / ".garage", merged)
        return InstallSummary(n_skills=0, n_agents=0, hosts=sorted(set(hosts)))

    # Phase 3-4: decide + apply.
    # F009 ADR-D9-2: prior_entries_index key 从 F007 二元组 (src, dst) 扩展为
    # 5 元组 (src, dst, host, pack_id, scope) — 让跨 scope 同 src+dst 不串扰
    # (e.g. claude:user 与 claude:project 装同一 SKILL.md 是两条独立 entry).
    # F008 schema 1 manifest 由 manifest.read_manifest 自动 migrate 到 schema 2
    # (T3 commit 实施); 在 T3 之前 schema 1 entry 没有 scope 字段, 暂用 "project" 兜底.
    prior_manifest = read_manifest(workspace_root / ".garage")
    prior_entries_index: dict[tuple[str, str, str, str, str], ManifestFileEntry] = {}
    if prior_manifest is not None:
        for e in prior_manifest.files:
            # F009: getattr 兜底兼容 schema 1 entry (无 scope 字段) — T3 实施 migration 后
            # entry.scope 字段始终存在, 此处兼容只在 T2 单 commit 中起作用.
            scope_val = getattr(e, "scope", "project")
            prior_entries_index[(e.src, e.dst, e.host, e.pack_id, scope_val)] = e

    new_entries: list[ManifestFileEntry] = []
    n_skills_written = 0
    n_agents_written = 0

    for target in targets:
        rendered = inject(
            target.src_abs.read_text(encoding="utf-8"),
            target.pack_id,
            target.source_kind,
        )
        # Apply optional adapter render (default identity).
        rendered = adapters[target.host].render(rendered)
        rendered_bytes = rendered.encode("utf-8")
        rendered_hash = hashlib.sha256(rendered_bytes).hexdigest()

        # F009 ADR-D9-3: prior_entries_index key 用 absolute dst (与 schema 2
        # 写 manifest 时 dst=target.dst_abs.as_posix() 一致). schema 1 manifest
        # 经 read_manifest 自动 migrate 后 dst 已是 absolute, 与本 key 对齐.
        prior_entry: ManifestFileEntry | None = prior_entries_index.get(
            (
                target.src_rel,
                target.dst_abs.as_posix(),
                target.host,
                target.pack_id,
                target.scope,
            )
        )

        action = _decide_action(
            target=target,
            rendered_hash=rendered_hash,
            existing_entry=prior_entry,
            force=force,
        )

        if action == WriteAction.SKIP_LOCALLY_MODIFIED:
            print(
                WARN_LOCALLY_MODIFIED_FMT.format(path=target.dst_rel),
                file=err,
            )
            # Carry over the prior manifest entry (if any) so it survives;
            # untracked dst (no prior_entry) leaves nothing to carry. The
            # SKIP path does NOT count toward the "Installed N" stdout marker
            # so the summary stays consistent with what was actually written.
            if prior_entry is not None:
                new_entries.append(prior_entry)
            continue

        if action == WriteAction.OVERWRITE_FORCED:
            print(
                WARN_OVERWRITE_FORCED_FMT.format(path=target.dst_rel),
                file=err,
            )

        # Write only if bytes differ (NFR-702 mtime stability).
        target.dst_abs.parent.mkdir(parents=True, exist_ok=True)
        if (
            not target.dst_abs.exists()
            or target.dst_abs.read_bytes() != rendered_bytes
        ):
            target.dst_abs.write_bytes(rendered_bytes)

        new_entries.append(
            ManifestFileEntry(
                src=target.src_rel,
                # F009 ADR-D9-3: schema 2 dst 是 absolute POSIX path (含 cwd 或 home).
                # 比对 key 用 dst (5 元组) 与 prior_entry 一致.
                dst=target.dst_abs.as_posix(),
                host=target.host,
                pack_id=target.pack_id,
                content_hash=rendered_hash,
                scope=target.scope,  # F009 ADR-D9-2: phase 5 写 manifest 含 scope 字段
            )
        )
        if target.source_kind == "skill":
            n_skills_written += 1
        else:
            n_agents_written += 1

    # Phase 5: manifest. Merge with prior entries for hosts NOT in this run
    # so extend mode is additive rather than destructive.
    new_manifest = Manifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        installed_hosts=sorted(set(hosts)),
        installed_packs=sorted({p.pack_id for p in packs}),
        installed_at=_now_iso(),
        files=new_entries,
    )
    merged = _merge_with_existing(workspace_root, new_manifest)
    write_manifest(workspace_root / ".garage", merged)

    return InstallSummary(
        n_skills=n_skills_written,
        n_agents=n_agents_written,
        hosts=sorted(set(hosts) | set(merged.installed_hosts)),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_targets(
    workspace_root: Path,
    packs: Iterable[Pack],
    adapters: dict[str, HostInstallAdapter],
    scopes_resolved: dict[str, str] | None = None,
) -> list[_Target]:
    """Expand each pack × host × (skill|agent) into a list of _Target.

    F009 ADR-D9-2: phase 2 scope 分流主改动点。按 target.scope 选 base path
    (project = workspace_root, user = Path.home()) 和 adapter method
    (target_skill_path vs target_skill_path_user). dst_abs / dst_rel 字段
    在 user scope 下是 absolute POSIX path (含 home), 在 project scope 下
    保持 F007/F008 既有相对路径行为 (CON-901).

    F008 既有调用方 (scopes_resolved=None) 行为字节级保留: 全部 host 默认
    project scope, 完全等价 F007 _resolve_targets 算法.
    """
    # F009: scopes_resolved=None → F007/F008 既有行为 (全 host 默认 project)
    if scopes_resolved is None:
        scopes_resolved = {host_id: "project" for host_id in adapters}

    # F009 ADR-D9-10 (code-review I-3 fix): 真正接通 UserHomeNotFoundError 链.
    # 任何 user scope target 解析涉及到的 Path.home() / adapter.target_*_user()
    # 抛 RuntimeError 时, 在此统一转译为 UserHomeNotFoundError, 由 cli._init catch
    # → exit 1 + stderr 'Cannot determine user home directory: ...'.
    needs_home = any(scope == "user" for scope in scopes_resolved.values())
    if needs_home:
        try:
            Path.home()
        except RuntimeError as exc:
            raise UserHomeNotFoundError(str(exc)) from exc

    out: list[_Target] = []
    for pack in packs:
        for skill_id in pack.skills:
            skill_src_abs = pack.skill_source_path(skill_id)
            for host_id, adapter in adapters.items():
                scope = scopes_resolved.get(host_id, "project")
                if scope == "user":
                    # F009 user scope: absolute path under Path.home()
                    try:
                        skill_dst_abs = adapter.target_skill_path_user(skill_id)
                    except RuntimeError as exc:
                        raise UserHomeNotFoundError(str(exc)) from exc
                    skill_dst_rel = _to_posix(skill_dst_abs)  # absolute POSIX
                else:
                    # F007/F008 project scope: relative path under workspace_root
                    skill_dst_path: Path = adapter.target_skill_path(skill_id)
                    skill_dst_abs = workspace_root / skill_dst_path
                    skill_dst_rel = _to_posix(skill_dst_path)
                out.append(
                    _Target(
                        src_abs=skill_src_abs,
                        dst_abs=skill_dst_abs,
                        src_rel=_to_posix(
                            skill_src_abs.relative_to(workspace_root)
                        ),
                        dst_rel=skill_dst_rel,
                        host=host_id,
                        pack_id=pack.pack_id,
                        source_kind="skill",
                        skill_or_agent_id=skill_id,
                        scope=scope,
                    )
                )
        for agent_id in pack.agents:
            agent_src_abs = pack.agent_source_path(agent_id)
            for host_id, adapter in adapters.items():
                scope = scopes_resolved.get(host_id, "project")
                if scope == "user":
                    try:
                        agent_dst_path: Path | None = adapter.target_agent_path_user(agent_id)
                    except RuntimeError as exc:
                        raise UserHomeNotFoundError(str(exc)) from exc
                    if agent_dst_path is None:
                        continue  # cursor: no agent surface (user 与 project scope 一致)
                    agent_dst_abs = agent_dst_path
                    agent_dst_rel = _to_posix(agent_dst_path)
                else:
                    agent_dst_path = adapter.target_agent_path(agent_id)
                    if agent_dst_path is None:
                        continue  # cursor: no agent surface
                    agent_dst_abs = workspace_root / agent_dst_path
                    agent_dst_rel = _to_posix(agent_dst_path)
                out.append(
                    _Target(
                        src_abs=agent_src_abs,
                        dst_abs=agent_dst_abs,
                        src_rel=_to_posix(
                            agent_src_abs.relative_to(workspace_root)
                        ),
                        dst_rel=agent_dst_rel,
                        host=host_id,
                        pack_id=pack.pack_id,
                        source_kind="agent",
                        skill_or_agent_id=agent_id,
                        scope=scope,
                    )
                )
    return out


def _check_conflicts(targets: list[_Target]) -> None:
    """Raise ConflictingSkillError when two different srcs map to the same dst.

    F009 ADR-D9-2 / FR-907: 比对 key 从 F007 二元组 ``(host, dst_rel)`` 扩展为
    三元组 ``(host, scope, dst_rel)`` —— 跨 scope 同 dst_rel 不视作冲突
    (e.g. ``--hosts claude:user,claude:project`` 同一 SKILL.md 同时装到 user +
    project 是合法的, 由 dst 不同 (~/... vs ./...) 自然区分). 算法分支结构
    字节级保持原状, 仅 key 扩展 (CON-902 enum 内允许的最小改动).
    """
    by_dst: dict[tuple[str, str, str], _Target] = {}
    for t in targets:
        key = (t.host, t.scope, t.dst_rel)
        if key in by_dst and by_dst[key].src_rel != t.src_rel:
            other = by_dst[key]
            raise ConflictingSkillError(
                f"Conflicting skill {t.skill_or_agent_id!r} for host {t.host!r}: "
                f"both {other.pack_id!r} ({other.src_rel}) and "
                f"{t.pack_id!r} ({t.src_rel}) target {t.dst_rel}"
            )
        by_dst[key] = t


def _decide_action(
    target: _Target,
    rendered_hash: str,
    existing_entry: ManifestFileEntry | None,
    force: bool,
) -> WriteAction:
    """D7 §10.2 decision table."""
    dst_exists = target.dst_abs.exists()

    if existing_entry is None:
        if not dst_exists:
            return WriteAction.WRITE_NEW
        # Untracked file at our dst: treat as locally authored.
        return WriteAction.OVERWRITE_FORCED if force else WriteAction.SKIP_LOCALLY_MODIFIED

    if not dst_exists:
        # Tracked previously but user removed → restore from source.
        return WriteAction.WRITE_NEW

    local_hash = hashlib.sha256(target.dst_abs.read_bytes()).hexdigest()
    if local_hash == existing_entry.content_hash:
        # User hasn't edited; safe to refresh from source (or no-op if source unchanged).
        return WriteAction.UPDATE_FROM_SOURCE
    return WriteAction.OVERWRITE_FORCED if force else WriteAction.SKIP_LOCALLY_MODIFIED


def _merge_with_existing(workspace_root: Path, fresh: Manifest) -> Manifest:
    """Merge a fresh manifest with the previous manifest's entries for OTHER hosts.

    Extend-mode rule (FR-704 acceptance #5):
        ``garage init --hosts cursor`` after a previous ``--hosts claude``
        must keep the claude entries intact and add cursor on top.

    F009 ADR-D9-2 (code-review I-4 fix): drop key 由 ``host`` 单维升级为
    ``(host, scope)`` 二元 host-scope key — 仅 drop "本次 init 涉及到的
    (host, scope) 组合" 的 prior entry, 而不是 "本次 init 涉及到的 host"
    全部 prior entry. 否则用户先 ``garage init --hosts claude --scope user``,
    再 ``garage init --hosts claude --scope project`` 时, 第二次 init 会 drop
    所有 prior user scope claude entry → manifest 丢失记录但磁盘文件仍在
    (manifest 与磁盘漂移).

    fresh_keys 同步升级为五元组 ``(src, dst, host, pack_id, scope)`` 与 phase 4
    比对 key 对称.
    """
    prior = read_manifest(workspace_root / ".garage")
    if prior is None:
        return fresh

    # F009 ADR-D9-2: (host, scope) 二元 key — 跨 scope 不串扰
    fresh_host_scopes = {(e.host, e.scope) for e in fresh.files}
    # 五元组 key — 与 phase 4 prior_entries_index 对称
    fresh_keys = {
        (e.src, e.dst, e.host, e.pack_id, e.scope) for e in fresh.files
    }

    carried_files: list[ManifestFileEntry] = [
        e
        for e in prior.files
        if (e.host, e.scope) not in fresh_host_scopes
        and (e.src, e.dst, e.host, e.pack_id, e.scope) not in fresh_keys
    ]
    carried_hosts = sorted(set(fresh.installed_hosts) | set(prior.installed_hosts))
    carried_packs = sorted(set(prior.installed_packs) | set(fresh.installed_packs))

    return Manifest(
        schema_version=fresh.schema_version,
        installed_hosts=carried_hosts,
        installed_packs=carried_packs,
        installed_at=fresh.installed_at,
        files=fresh.files + carried_files,
    )


def _to_posix(path: Path) -> str:
    return path.as_posix()


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


# Re-export common error symbols so callers don't need 4 imports.
__all__ = [
    "ConflictingSkillError",
    "InstallSummary",
    "InvalidPackError",
    "MalformedFrontmatterError",
    "PackManifestMismatchError",
    "UnknownHostError",
    "WARN_LOCALLY_MODIFIED_FMT",
    "WARN_OVERWRITE_FORCED_FMT",
    "MSG_NO_PACKS_FMT",
    "WriteAction",
    "install_packs",
]


