"""F010 sync pipeline: orchestrate compile → write to host context surface.

Implements FR-1001..1003 + ADR-D10-3 (三方 hash decision) + ADR-D10-13 (--force).

Three-way hash decision (ADR-D10-3 r2 决策表):
- disk_marker_hash == prior_synced_hash AND fresh != prior → UPDATE_FROM_SOURCE 覆写
- disk_marker_hash == prior_synced_hash AND fresh == prior → mtime 不刷新 (NFR-1002)
- disk_marker_hash != prior_synced_hash → SKIP_LOCALLY_MODIFIED + stderr warn (除非 force=True)
- 文件不存在 → WRITE_NEW
- force=True 且 SKIP → OVERWRITE_FORCED
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import IO

from garage_os.adapter.installer.host_registry import (
    HOST_REGISTRY,
    UnknownHostError,
    UnknownScopeError,
    SUPPORTED_SCOPES,
    get_adapter,
)
from garage_os.sync.compiler import compile_garage_section
from garage_os.sync.manifest import (
    SyncManifest,
    SyncSources,
    SyncTargetEntry,
    read_sync_manifest,
    write_sync_manifest,
)
from garage_os.sync.render.markdown import (
    extract_marker_block,
    has_marker_block,
    wrap_with_markers,
)
from garage_os.sync.render.mdc import render_mdc_with_front_matter


class SyncWriteAction(str, Enum):
    """Per-host write decision (ADR-D10-3 r2 决策表 + F007 SKIP_LOCALLY_MODIFIED 同精神)."""

    WRITE_NEW = "write_new"
    UPDATE_FROM_SOURCE = "update_from_source"
    SKIP_LOCALLY_MODIFIED = "skip_locally_modified"
    OVERWRITE_FORCED = "overwrite_forced"
    UNCHANGED = "unchanged"  # disk == prior == fresh; mtime not refreshed (NFR-1002)


@dataclass
class SyncSummary:
    synced_at: str
    n_hosts_written: int = 0
    n_hosts_skipped: int = 0
    knowledge_count: int = 0
    experience_count: int = 0
    targets: list[SyncTargetEntry] = field(default_factory=list)


def sync_hosts(
    workspace_root: Path,
    hosts: list[str],
    *,
    scopes_per_host: dict[str, str] | None = None,
    force: bool = False,
    stderr: IO[str] | None = None,
) -> SyncSummary:
    """Sync Garage knowledge + experience to host context surface files.

    Args:
        workspace_root: project root containing .garage/
        hosts: pre-resolved host id list (CLI handles 'all'/'none')
        scopes_per_host: optional dict mapping host_id → 'project' | 'user'.
            Hosts not present default to 'project'. None → all 'project'.
        force: True overrides SKIP_LOCALLY_MODIFIED → OVERWRITE_FORCED
        stderr: stream for SKIP warnings + budget truncation

    Returns:
        SyncSummary with counts + targets[].

    Raises:
        UnknownHostError: any host_id not in HOST_REGISTRY
        UnknownScopeError: any scope not in SUPPORTED_SCOPES
    """
    err = stderr if stderr is not None else sys.stderr

    # Validate hosts + scopes (CON-1001 fast-fail before any disk write)
    for host_id in hosts:
        if host_id not in HOST_REGISTRY:
            raise UnknownHostError(
                f"Unknown host: {host_id}. Supported hosts: {', '.join(sorted(HOST_REGISTRY))}"
            )
    if scopes_per_host:
        for host_id, scope in scopes_per_host.items():
            if scope not in SUPPORTED_SCOPES:
                raise UnknownScopeError(
                    f"Unknown scope: {scope} for host {host_id}. "
                    f"Supported scopes: {', '.join(SUPPORTED_SCOPES)}"
                )

    # Normalize scopes: missing host → "project"
    resolved_scopes: dict[str, str] = {h: "project" for h in hosts}
    if scopes_per_host:
        for h, s in scopes_per_host.items():
            if h in resolved_scopes:
                resolved_scopes[h] = s

    # Phase 1: compile Garage section once (shared across all hosts; same content)
    compiled = compile_garage_section(workspace_root, stderr=err)
    fresh_marker_block_body = compiled.body_markdown.strip("\n")
    fresh_marker_block_full = wrap_with_markers(fresh_marker_block_body)
    fresh_inner = extract_marker_block(fresh_marker_block_full) or ""
    # NFR-1002 守门: hash 不算 footer 时间戳 (`_Synced at ... by garage sync`),
    # 否则同知识库二次 sync timestamp 变化导致永远 UPDATE 而非 UNCHANGED.
    fresh_hash = _sha256_text(_strip_footer(fresh_inner))

    # Phase 2: load prior manifest for three-way hash comparison
    garage_dir = workspace_root / ".garage"
    prior_manifest = read_sync_manifest(garage_dir)
    prior_targets: dict[tuple[str, str], SyncTargetEntry] = {}
    if prior_manifest is not None:
        for t in prior_manifest.targets:
            prior_targets[(t.host, t.scope)] = t

    # Phase 3-4: per host: decide action + write
    synced_at = _now_iso()
    new_targets: list[SyncTargetEntry] = []
    n_written = 0
    n_skipped = 0

    for host_id in sorted(set(hosts)):
        adapter = get_adapter(host_id)
        scope = resolved_scopes[host_id]

        if scope == "user":
            try:
                dst = adapter.target_context_path_user("garage-context")
            except RuntimeError as exc:
                # Path.home() failed — propagate per F009 ADR-D9-10 spirit
                raise RuntimeError(
                    f"Cannot determine user home directory: {exc}"
                ) from exc
        else:
            dst = workspace_root / adapter.target_context_path("garage-context")

        # Build the bytes we WOULD write (host-format aware)
        if host_id == "cursor":
            # cursor .mdc needs front matter at top
            new_full_content = render_mdc_with_front_matter(fresh_marker_block_full)
        else:
            # claude / opencode: plain markdown body (just the marker block at file bottom)
            new_full_content = fresh_marker_block_full

        # Three-way hash decision
        prior_entry = prior_targets.get((host_id, scope))
        action = _decide_action(
            dst=dst,
            fresh_hash=fresh_hash,
            prior_entry=prior_entry,
            host_id=host_id,
            new_full_content=new_full_content,
            force=force,
            err=err,
        )

        # Apply action
        if action in (SyncWriteAction.SKIP_LOCALLY_MODIFIED, SyncWriteAction.UNCHANGED):
            n_skipped += 1
            # Carry over prior entry, but reflect the current action verdict
            # (NFR-1002: do NOT touch disk; mtime stays unchanged)
            if prior_entry is not None:
                new_targets.append(
                    SyncTargetEntry(
                        host=prior_entry.host,
                        scope=prior_entry.scope,
                        path=prior_entry.path,
                        content_hash=prior_entry.content_hash,
                        wrote_at=prior_entry.wrote_at,  # preserve original wrote_at
                        action=action.value,  # current action (UNCHANGED / SKIP_LOCALLY_MODIFIED)
                    )
                )
            continue

        # WRITE_NEW / UPDATE_FROM_SOURCE / OVERWRITE_FORCED → write
        bytes_to_write = _compose_full_file_content(
            host_id=host_id,
            dst=dst,
            new_marker_block_full=fresh_marker_block_full,
        )

        dst.parent.mkdir(parents=True, exist_ok=True)
        # Idempotent: only write if bytes differ
        if not dst.exists() or dst.read_bytes() != bytes_to_write:
            dst.write_bytes(bytes_to_write)

        new_targets.append(
            SyncTargetEntry(
                host=host_id,
                scope=scope,
                path=str(_resolve_absolute(dst)),
                content_hash=fresh_hash,
                wrote_at=synced_at,
                action=action.value,
            )
        )
        n_written += 1

    # Phase 5: write fresh manifest
    sources = SyncSources(
        knowledge_count=compiled.knowledge_count,
        experience_count=compiled.experience_count,
        knowledge_kinds=list(compiled.knowledge_kinds),
        size_bytes=compiled.size_bytes,
        size_budget_bytes=16384,  # default budget; T2 ADR-D10-4
    )
    new_manifest = SyncManifest(
        schema_version=1,
        synced_at=synced_at,
        sources=sources,
        targets=new_targets,
    )
    write_sync_manifest(garage_dir, new_manifest)

    return SyncSummary(
        synced_at=synced_at,
        n_hosts_written=n_written,
        n_hosts_skipped=n_skipped,
        knowledge_count=compiled.knowledge_count,
        experience_count=compiled.experience_count,
        targets=new_targets,
    )


def _decide_action(
    *,
    dst: Path,
    fresh_hash: str,
    prior_entry: SyncTargetEntry | None,
    host_id: str,
    new_full_content: str,
    force: bool,
    err: IO[str],
) -> SyncWriteAction:
    """ADR-D10-3 r2 三方 hash 决策表."""
    if not dst.exists():
        return SyncWriteAction.WRITE_NEW

    disk_content = dst.read_text(encoding="utf-8")
    if not has_marker_block(disk_content):
        # File exists but no Garage marker yet → we'll add one (append at end)
        return SyncWriteAction.WRITE_NEW

    disk_inner = extract_marker_block(disk_content) or ""
    disk_hash = _sha256_text(_strip_footer(disk_inner))
    prior_hash = prior_entry.content_hash if prior_entry else None

    # Decision matrix
    if disk_hash == prior_hash:
        # User did NOT modify marker block
        if fresh_hash == prior_hash:
            # All three match: nothing to do (NFR-1002 mtime stability)
            return SyncWriteAction.UNCHANGED
        # Garage knowledge changed → safe to update
        return SyncWriteAction.UPDATE_FROM_SOURCE
    else:
        # User modified marker block (or no prior manifest)
        if force:
            print(
                f"[{host_id}] OVERWRITE_FORCED: marker block locally modified, --force overrides",
                file=err,
            )
            return SyncWriteAction.OVERWRITE_FORCED
        print(
            f"[{host_id}] SKIP_LOCALLY_MODIFIED: marker block at {dst} has been "
            f"manually edited since last sync; use --force to overwrite",
            file=err,
        )
        return SyncWriteAction.SKIP_LOCALLY_MODIFIED


def _compose_full_file_content(
    *,
    host_id: str,
    dst: Path,
    new_marker_block_full: str,
) -> bytes:
    """Build full file bytes preserving user content outside markers.

    For .mdc (cursor): add YAML front matter on top.
    For .md (claude/opencode): preserve existing user content; replace marker block in place.
    """
    if host_id == "cursor":
        return _compose_mdc_content(dst, new_marker_block_full).encode("utf-8")
    else:
        return _compose_md_content(dst, new_marker_block_full).encode("utf-8")


def _compose_mdc_content(dst: Path, new_marker_block_full: str) -> str:
    """For cursor .mdc: front matter on top + marker block.

    If file exists with user content between front matter and marker, preserve it.
    If file exists WITHOUT marker, append marker block at end (preserve all user content),
    BUT inject ``alwaysApply: true`` YAML front matter at the top if absent
    (FR-1004 + HYP-1002 hard requirement; IMP-2 fix from code-review-F010-r1).
    If file does NOT exist, fresh: front matter + marker block.
    """
    from garage_os.sync.render.mdc import MDC_FRONT_MATTER

    if not dst.exists():
        return render_mdc_with_front_matter(new_marker_block_full)

    existing = dst.read_text(encoding="utf-8")
    if not has_marker_block(existing):
        # File exists, no marker yet → preserve user content + ensure front matter at top
        if existing.strip():
            # IMP-2 fix: check if front matter already present; if not, prepend
            has_front_matter = existing.lstrip().startswith("---\n")
            if has_front_matter:
                # User already has YAML front matter → preserve user content + append marker
                return f"{existing.rstrip()}\n\n{new_marker_block_full}"
            else:
                # Inject front matter at top (FR-1004 + HYP-1002 hard requirement)
                return f"{MDC_FRONT_MATTER}\n{existing.rstrip()}\n\n{new_marker_block_full}"
        return render_mdc_with_front_matter(new_marker_block_full)

    # Marker exists → replace just the marker block, preserve everything else
    return _replace_marker_block(existing, new_marker_block_full)


def _compose_md_content(dst: Path, new_marker_block_full: str) -> str:
    """For claude/opencode: preserve user content; replace marker block in place.

    If file does not exist, just write marker block.
    If file exists without marker, append marker block at end.
    If file has marker, replace block in place.
    """
    if not dst.exists():
        return new_marker_block_full

    existing = dst.read_text(encoding="utf-8")
    if not has_marker_block(existing):
        if existing.strip():
            return f"{existing.rstrip()}\n\n{new_marker_block_full}"
        return new_marker_block_full

    return _replace_marker_block(existing, new_marker_block_full)


def _replace_marker_block(existing: str, new_marker_block_full: str) -> str:
    """Replace the marker block (begin..end inclusive) in existing content.

    NFR-1003: bytes outside the marker block preserved exactly.
    """
    from garage_os.sync.render.markdown import MARKER_BEGIN, MARKER_END

    begin_idx = existing.index(MARKER_BEGIN)
    end_idx = existing.index(MARKER_END) + len(MARKER_END)
    # Include trailing newline after marker_end if present
    if end_idx < len(existing) and existing[end_idx] == "\n":
        end_idx += 1
    before = existing[:begin_idx]
    after = existing[end_idx:]
    new_block = new_marker_block_full
    if not new_block.endswith("\n"):
        new_block += "\n"
    return before + new_block + after


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _strip_footer(marker_inner: str) -> str:
    """Remove the `_Synced at ... by garage sync ...)_` footer line and its
    leading separator from the marker inner content for hash computation.

    NFR-1002 idempotency requires that two syncs with same knowledge produce
    same content_hash; the footer timestamp would otherwise change every call.
    """
    lines = marker_inner.splitlines()
    # Walk back from the end; remove footer line + preceding `---` separator + blanks
    out = list(lines)
    # Find footer line (starts with "_Synced at" pattern)
    while out and not out[-1].strip().startswith("_Synced at "):
        out.pop()
    if out:  # remove footer line
        out.pop()
    # Remove trailing blank lines + `---` separator
    while out and (not out[-1].strip() or out[-1].strip() == "---"):
        out.pop()
    return "\n".join(out)


def _resolve_absolute(path: Path) -> str:
    """Return absolute POSIX path (M-4 minor: cross-platform safe)."""
    return path.resolve(strict=False).as_posix()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z"
