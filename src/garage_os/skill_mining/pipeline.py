"""F013-A T4: ``SkillMiningHook`` callback + audit/decay + status summary.

Wires together ``pattern_detector`` + ``suggestion_store`` into the existing
F003 extraction chain via two caller insertion points (ADR-D13-3 r2 Cr-1):

- Path 1: ``SessionManager._trigger_memory_extraction`` (after
  ``orchestrator.extract_for_archived_session`` returns)
- Path 2: ``ingest/pipeline.py`` (after ``orchestrator.extract_for_archived_session_id``
  returns; bypasses ``extraction_enabled`` for explicit ``garage session import`` opt-in)

Both call sites use try/except so hook failure does NOT block archive / import
(best-effort semantics, matching F010 ingest pattern).

Audit / decay (FR-1305):
- proposed → expired after ``expires_at`` (default created_at + 30 days)
- expired → physically deleted via ``garage skill suggest --purge-expired``

Status summary (FR-1305 + Im-6 r2):
- Always emit metadata line "Skill mining: scanned X / Y / Z (last scan: <ts>)"
- Emit 💡 line ONLY when proposed > 0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.skill_mining.pattern_detector import (
    DEFAULT_EXPIRY_DAYS,
    DEFAULT_THRESHOLD,
    detect_and_write,
)
from garage_os.skill_mining.suggestion_store import SUGGESTIONS_DIR_NAME, SuggestionStore
from garage_os.skill_mining.types import SkillSuggestion, SkillSuggestionStatus
from garage_os.storage.file_storage import FileStorage

LAST_SCAN_FILE = ".last-scan.json"


def _last_scan_path(garage_dir: Path) -> Path:
    return Path(garage_dir) / SUGGESTIONS_DIR_NAME / LAST_SCAN_FILE


def _read_last_scan(garage_dir: Path) -> dict | None:
    path = _last_scan_path(garage_dir)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_last_scan(
    garage_dir: Path,
    *,
    entries_count: int,
    records_count: int,
    proposed_count: int,
    timestamp: datetime,
) -> None:
    target_dir = Path(garage_dir) / SUGGESTIONS_DIR_NAME
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "entries_count": entries_count,
        "records_count": records_count,
        "proposed_count": proposed_count,
        "timestamp": timestamp.isoformat(),
    }
    _last_scan_path(garage_dir).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ---------- User-config ----------


def _load_user_config() -> dict:
    """Mi-1 r2: read ``~/.garage/skill-mining-config.json`` for user prefs.

    Falls back to defaults silently. Schema:
    ```json
    {
      "threshold": 5,
      "expiry_days": 30,
      "hook_enabled": true,
      "exclude_domains": []
    }
    ```
    """
    cfg_path = Path.home() / ".garage" / "skill-mining-config.json"
    if not cfg_path.is_file():
        return {}
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _hook_enabled_in_platform(garage_dir: Path) -> bool:
    """ADR-D13-3 Im-4 fallback: ``platform.json skill_mining.hook_enabled``
    config gate. Defaults to ``True``.
    """
    storage = FileStorage(garage_dir)
    try:
        platform = storage.read_json("config/platform.json") or {}
    except Exception:
        return True
    skill_mining_cfg = platform.get("skill_mining", {})
    return bool(skill_mining_cfg.get("hook_enabled", True))


# ---------- Hook entry point ----------


@dataclass
class HookResult:
    """Returned by ``SkillMiningHook.run_after_extraction`` for diagnostics."""

    skipped_reason: str | None  # "hook_disabled" / None on success
    new_suggestions_count: int
    error: str | None  # exception message, or None


class SkillMiningHook:
    """Callback hook invoked after F003 extraction completes.

    Both caller paths (``session_manager._trigger_memory_extraction`` and
    ``ingest/pipeline.py``) call ``run_after_extraction(session_id, garage_dir)``
    in a try/except wrapper so hook failure does NOT block archive / import.
    """

    @staticmethod
    def run_after_extraction(
        session_id: str,
        garage_dir: Path,
        *,
        packs_root: Path | None = None,
        threshold: int | None = None,
        expiry_days: int | None = None,
        now: datetime | None = None,
    ) -> HookResult:
        """Run a single pattern-detection pass + write status.

        Honors ``platform.json skill_mining.hook_enabled`` config gate
        (default True). Best-effort: any exception caught and reported via
        ``HookResult.error`` (caller may log).
        """
        if not _hook_enabled_in_platform(garage_dir):
            return HookResult(
                skipped_reason="hook_disabled",
                new_suggestions_count=0,
                error=None,
            )
        try:
            user_cfg = _load_user_config()
            threshold = (
                threshold
                if threshold is not None
                else int(user_cfg.get("threshold", DEFAULT_THRESHOLD))
            )
            expiry_days = (
                expiry_days
                if expiry_days is not None
                else int(user_cfg.get("expiry_days", DEFAULT_EXPIRY_DAYS))
            )
            packs_root = packs_root or (Path(garage_dir).parent / "packs")
            now = now or datetime.now()

            storage = FileStorage(garage_dir)
            ks = KnowledgeStore(storage)
            ei = ExperienceIndex(storage)
            ss = SuggestionStore(garage_dir)

            new = detect_and_write(
                ks, ei, ss, packs_root,
                threshold=threshold,
                expiry_days=expiry_days,
                now=now,
            )
            entries_count = len(ks.list_entries())
            records_count = len(ei.list_records())
            proposed_count = len(ss.list_by_status(SkillSuggestionStatus.PROPOSED))
            _write_last_scan(
                garage_dir,
                entries_count=entries_count,
                records_count=records_count,
                proposed_count=proposed_count,
                timestamp=now,
            )
            # session_id is recorded for future per-session debugging if needed
            _ = session_id
            return HookResult(
                skipped_reason=None,
                new_suggestions_count=len(new),
                error=None,
            )
        except Exception as exc:
            return HookResult(
                skipped_reason=None,
                new_suggestions_count=0,
                error=str(exc),
            )


# ---------- Audit / decay ----------


def run_audit(garage_dir: Path, *, now: datetime | None = None) -> int:
    """Move proposed suggestions whose ``expires_at`` < now into the expired/ subdir.

    Returns the number of expired-this-pass.
    """
    now = now or datetime.now()
    ss = SuggestionStore(garage_dir)
    expired_count = 0
    for s in ss.list_by_status(SkillSuggestionStatus.PROPOSED):
        if s.expires_at < now:
            ss.move_to_status(s.id, SkillSuggestionStatus.EXPIRED)
            expired_count += 1
    return expired_count


# ---------- Status summary (Im-6 r2) ----------


@dataclass
class StatusSummary:
    """Returned by ``compute_status_summary`` for ``garage status`` rendering."""

    entries_count: int
    records_count: int
    proposed_count: int
    expired_count: int
    last_scan: datetime | None  # None if no scan ever
    metadata_line: str
    hint_line: str | None  # None when proposed_count == 0


def compute_status_summary(garage_dir: Path) -> StatusSummary:
    """Compute ``Skill mining: scanned X / Y / Z (last scan: ...)`` line + optional 💡 line.

    Im-6 r2 rule:
    - **Always** emit metadata line (even when proposed = 0)
    - Emit 💡 hint ONLY when proposed > 0 (avoid noise)
    """
    last_scan_data = _read_last_scan(garage_dir)
    if last_scan_data is None:
        # Never scanned; live counts via stores
        try:
            storage = FileStorage(garage_dir)
            entries_count = len(KnowledgeStore(storage).list_entries())
            records_count = len(ExperienceIndex(storage).list_records())
        except Exception:
            entries_count = 0
            records_count = 0
        last_scan = None
    else:
        entries_count = int(last_scan_data.get("entries_count", 0))
        records_count = int(last_scan_data.get("records_count", 0))
        ts = last_scan_data.get("timestamp")
        last_scan = datetime.fromisoformat(ts) if ts else None

    ss = SuggestionStore(garage_dir)
    proposed_count = len(ss.list_by_status(SkillSuggestionStatus.PROPOSED))
    expired_count = len(ss.list_by_status(SkillSuggestionStatus.EXPIRED))

    last_scan_str = last_scan.strftime("%Y-%m-%d %H:%M:%S") if last_scan else "never"
    metadata_line = (
        f"Skill mining: scanned {entries_count} entries / {records_count} records "
        f"/ {proposed_count} proposed (last scan: {last_scan_str})"
    )
    hint_line: str | None = None
    if proposed_count > 0:
        hint_line = (
            f"💡 {proposed_count} proposed / {expired_count} expired skill suggestions "
            f"— run `garage skill suggest` to review"
        )

    return StatusSummary(
        entries_count=entries_count,
        records_count=records_count,
        proposed_count=proposed_count,
        expired_count=expired_count,
        last_scan=last_scan,
        metadata_line=metadata_line,
        hint_line=hint_line,
    )
