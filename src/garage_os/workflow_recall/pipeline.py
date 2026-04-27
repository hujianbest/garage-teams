"""F014 T3: ``WorkflowRecallHook`` callback + status summary.

Wires together cache + path_recaller into the existing F003-F013 EI write
chain via 4 caller insertion points (ADR-D14-3 r2 Cr-1+Cr-2+Im-1):

- Path 1: ``SessionManager._trigger_memory_extraction`` (after F013-A
  SkillMiningHook; archive-level safety net)
- Path 2: ``cli.py _experience_add`` (after ``experience_index.store(record)``;
  user explicit ``garage experience add``)
- Path 3: ``publisher.py`` (after if-else, ~ L144; covers store + update
  branches per Im-1 r2)
- Path 4: ``knowledge/integration.py`` (after ``experience_index.store(experience)``;
  F006 integration path)

NOT INCLUDED (Cr-1 r2 USER-INPUT decision option b):
- ``cli.py:1172`` (skill execution record path) — explicitly excluded because
  that record's task_type is "skill_run" granularity, not cycle-level task
  path that workflow recall advisories represent. Users rely on
  ``--rebuild-cache`` if they want this path counted.

NOT INCLUDED (Cr-2 r2):
- ``ingest/pipeline.py`` — does not directly call ``experience_index.store``;
  invalidate happens transitively via publisher (Path 3).

All 4 callers wrap the hook in try/except so hook failure does NOT block
the caller (best-effort, matching F010 ingest pattern).

Status summary (FR-1405 + Im-6 pattern):
- Always emit metadata line "Workflow recall: scanned X / Y / Z (last scan: ...)"
- Append "(stale, will rebuild on next recall call)" when cache stale
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.storage.file_storage import FileStorage
from garage_os.workflow_recall.cache import WorkflowRecallCache
from garage_os.workflow_recall.path_recaller import DEFAULT_THRESHOLD


def _hook_enabled_in_platform(garage_dir: Path) -> bool:
    """ADR-D14-3 fallback: ``platform.json workflow_recall.enabled`` config gate.
    Defaults to True. Set False to disable invalidate hooks (advisories still
    work via ``--rebuild-cache``).
    """
    storage = FileStorage(garage_dir)
    try:
        platform = storage.read_json("config/platform.json") or {}
    except Exception:
        return True
    workflow_recall_cfg = platform.get("workflow_recall", {})
    return bool(workflow_recall_cfg.get("enabled", True))


# ---------- Hook entry point ----------


@dataclass
class HookResult:
    """Returned by ``WorkflowRecallHook.invalidate`` for diagnostics."""

    skipped_reason: str | None
    """'hook_disabled' / None on success"""

    invalidated: bool
    """True if last-indexed.json was actually removed"""

    error: str | None
    """exception message if invalidate raised, or None"""


class WorkflowRecallHook:
    """Callback hook that callers invoke after writing an ExperienceRecord
    (best-effort; failure does NOT block the caller).
    """

    @staticmethod
    def invalidate(garage_dir: Path) -> HookResult:
        """Invalidate the recall cache lazily (delete last-indexed.json).

        Honors ``platform.json workflow_recall.enabled`` config gate
        (default True).
        """
        if not _hook_enabled_in_platform(garage_dir):
            return HookResult(
                skipped_reason="hook_disabled",
                invalidated=False,
                error=None,
            )
        try:
            cache = WorkflowRecallCache(garage_dir)
            invalidated = cache.invalidate()
            return HookResult(
                skipped_reason=None,
                invalidated=invalidated,
                error=None,
            )
        except Exception as exc:
            return HookResult(
                skipped_reason=None,
                invalidated=False,
                error=str(exc),
            )


# ---------- Status summary ----------


@dataclass
class WorkflowRecallStatusSummary:
    """Returned by ``compute_status_summary`` for ``garage status`` rendering."""

    scanned_records: int
    bucket_count: int
    advisory_count: int
    last_scan: datetime | None
    stale: bool
    enabled: bool
    metadata_line: str
    """Always emitted (Im-6 pattern matching F013-A skill mining status)."""


def compute_status_summary(garage_dir: Path) -> WorkflowRecallStatusSummary:
    """Compute the ``Workflow recall: scanned X / Y / Z`` line.

    Reads ``last-indexed.json`` for cache freshness; reads cache.json for
    bucket/advisory counts. When stale or absent, emits live count from
    ExperienceIndex with a "(stale)" suffix.
    """
    enabled = _hook_enabled_in_platform(garage_dir)
    cache = WorkflowRecallCache(garage_dir)
    last_indexed_data = cache.load_last_indexed()
    cache_data = cache.load_cache()

    if last_indexed_data is not None:
        scanned = int(last_indexed_data.get("scanned_count", 0))
        ts = last_indexed_data.get("last_indexed_at")
        last_scan = datetime.fromisoformat(ts) if ts else None
        stale = False
    else:
        # Stale or never indexed; compute live via EI
        try:
            storage = FileStorage(garage_dir)
            scanned = len(ExperienceIndex(storage).list_records())
        except Exception:
            scanned = 0
        last_scan = None
        stale = True

    if cache_data is not None:
        bucket_count = len(cache_data)
        advisory_count = sum(
            1 for v in cache_data.values()
            if isinstance(v, dict)
            and v.get("total_records", 0) >= DEFAULT_THRESHOLD
        )
    else:
        bucket_count = 0
        advisory_count = 0

    last_scan_str = last_scan.strftime("%Y-%m-%d %H:%M:%S") if last_scan else "never"
    metadata_line = (
        f"Workflow recall: scanned {scanned} records / {bucket_count} buckets "
        f"/ {advisory_count} advisories (last scan: {last_scan_str})"
    )
    if not enabled:
        metadata_line += " (disabled via platform.json)"
    elif stale:
        metadata_line += " (stale, will rebuild on next recall call)"

    return WorkflowRecallStatusSummary(
        scanned_records=scanned,
        bucket_count=bucket_count,
        advisory_count=advisory_count,
        last_scan=last_scan,
        stale=stale,
        enabled=enabled,
        metadata_line=metadata_line,
    )
