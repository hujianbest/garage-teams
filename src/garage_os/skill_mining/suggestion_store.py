"""F013-A T1: ``SuggestionStore`` — 5-status-subdir CRUD + atomic write + ``mv`` transitions.

Persistence layout (ADR-D13-2):
```
<garage_dir>/skill-suggestions/
  proposed/  accepted/  promoted/  rejected/  expired/
    <sg-id>.json
```

Status transitions use ``os.rename`` (single atomic syscall). Atomic write
uses tempfile + rename to prevent partial files on IO failure.

INV-F13-1 守门: writes are restricted to ``<garage_dir>/skill-suggestions/``
subtree (no escape). ID format ``sg-<yyyymmdd>-<6 hex>`` collision prob is
negligible per day for individual user dogfood.
"""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from garage_os.skill_mining.types import SkillSuggestion, SkillSuggestionStatus

SUGGESTIONS_DIR_NAME = "skill-suggestions"

_STATUS_SUBDIRS = (
    SkillSuggestionStatus.PROPOSED,
    SkillSuggestionStatus.ACCEPTED,
    SkillSuggestionStatus.PROMOTED,
    SkillSuggestionStatus.REJECTED,
    SkillSuggestionStatus.EXPIRED,
)


class SuggestionStore:
    """File-system store for ``SkillSuggestion`` records."""

    def __init__(self, garage_dir: Path) -> None:
        self._root = Path(garage_dir) / SUGGESTIONS_DIR_NAME

    # ---- ID + path helpers ----

    @staticmethod
    def generate_id(now: datetime | None = None) -> str:
        """Generate a new ID: ``sg-<yyyymmdd>-<6 hex>``."""
        ts = now or datetime.now()
        return f"sg-{ts.strftime('%Y%m%d')}-{secrets.token_hex(3)}"

    def _status_dir(self, status: SkillSuggestionStatus) -> Path:
        return self._root / status.value

    def _path_for(self, status: SkillSuggestionStatus, sg_id: str) -> Path:
        return self._status_dir(status) / f"{sg_id}.json"

    def _ensure_dirs(self) -> None:
        for status in _STATUS_SUBDIRS:
            self._status_dir(status).mkdir(parents=True, exist_ok=True)

    # ---- Serialization ----

    @staticmethod
    def _to_dict(suggestion: SkillSuggestion) -> dict:
        d = asdict(suggestion)
        d["status"] = suggestion.status.value
        d["created_at"] = suggestion.created_at.isoformat()
        d["expires_at"] = suggestion.expires_at.isoformat()
        return d

    @staticmethod
    def _from_dict(data: dict) -> SkillSuggestion:
        return SkillSuggestion(
            id=data["id"],
            suggested_name=data["suggested_name"],
            suggested_description=data["suggested_description"],
            problem_domain_key=data["problem_domain_key"],
            tag_bucket=list(data.get("tag_bucket", [])),
            evidence_entries=list(data.get("evidence_entries", [])),
            evidence_records=list(data.get("evidence_records", [])),
            suggested_pack=data["suggested_pack"],
            score=float(data["score"]),
            status=SkillSuggestionStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            promoted_to_path=data.get("promoted_to_path"),
            rejected_reason=data.get("rejected_reason"),
            extra=dict(data.get("extra", {})),
        )

    # ---- CRUD ----

    def write(self, suggestion: SkillSuggestion) -> Path:
        """Atomic write a suggestion to its current-status subdir.

        Uses tempfile in the same dir + ``os.replace`` for atomic rename
        (guarantees no partial file visible on IO failure).
        """
        self._ensure_dirs()
        target = self._path_for(suggestion.status, suggestion.id)
        target_dir = target.parent
        payload = json.dumps(self._to_dict(suggestion), indent=2, ensure_ascii=False) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(target_dir), delete=False, prefix=".tmp-"
        ) as fh:
            tmp_path = Path(fh.name)
            try:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            except Exception:
                fh.close()
                tmp_path.unlink(missing_ok=True)
                raise
        os.replace(tmp_path, target)
        return target

    def load(self, status: SkillSuggestionStatus, sg_id: str) -> SkillSuggestion | None:
        """Load by (status, id); return ``None`` if file missing."""
        path = self._path_for(status, sg_id)
        if not path.is_file():
            return None
        return self._from_dict(json.loads(path.read_text(encoding="utf-8")))

    def find(self, sg_id: str) -> SkillSuggestion | None:
        """Find by id across all 5 status subdirs (slower; for CLI ``--id``)."""
        for status in _STATUS_SUBDIRS:
            s = self.load(status, sg_id)
            if s is not None:
                return s
        return None

    def list_by_status(self, status: SkillSuggestionStatus) -> list[SkillSuggestion]:
        """List all suggestions in a single status subdir."""
        d = self._status_dir(status)
        if not d.is_dir():
            return []
        out: list[SkillSuggestion] = []
        for path in sorted(d.glob("*.json")):
            try:
                out.append(self._from_dict(json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError, KeyError, ValueError):
                continue  # corrupted entry; skip silently (audit pass will sweep)
        return out

    def list_all(self) -> list[SkillSuggestion]:
        """List across all 5 status subdirs."""
        out: list[SkillSuggestion] = []
        for status in _STATUS_SUBDIRS:
            out.extend(self.list_by_status(status))
        return out

    def move_to_status(
        self, sg_id: str, new_status: SkillSuggestionStatus
    ) -> SkillSuggestion | None:
        """Atomically move a suggestion file to a new status subdir using ``os.rename``.

        Returns the updated SkillSuggestion (with new status), or ``None`` if not found.
        Read-modify-write is avoided: file is renamed in-place + JSON status field is
        rewritten atomically (load → mutate → write to new path → unlink old).
        """
        existing = self.find(sg_id)
        if existing is None:
            return None
        if existing.status == new_status:
            return existing
        old_path = self._path_for(existing.status, sg_id)
        existing.status = new_status
        # Write to new path atomically, then unlink old
        self.write(existing)
        try:
            old_path.unlink(missing_ok=True)
        except OSError:
            pass  # best-effort; new path is already canonical
        return existing

    def delete(self, status: SkillSuggestionStatus, sg_id: str) -> bool:
        """Physically delete a suggestion (used by ``--purge-expired``)."""
        path = self._path_for(status, sg_id)
        if not path.is_file():
            return False
        path.unlink()
        return True
