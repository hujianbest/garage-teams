"""F014 T1: ``WorkflowRecallCache`` — single-file JSON CRUD + atomic write.

Persistence layout (ADR-D14-2):
```
<garage_dir>/workflow-recall/
  cache.json          # { "{tt}|{pd}": {sequences: [...], total_records: int} }
  last-indexed.json   # { last_indexed_at: ISO ts, scanned_count: int }
```

Cache invalidation: ``invalidate()`` deletes ``last-indexed.json`` (lazy);
next ``read()`` triggers full recompute (Im-5 r2: no incremental scan,
deferred to D-1410 in F015+).

INV-F14-2 守门: writes restricted to ``<garage_dir>/workflow-recall/``
subtree (no escape).
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

WORKFLOW_RECALL_DIR_NAME = "workflow-recall"
CACHE_FILE_NAME = "cache.json"
LAST_INDEXED_FILE_NAME = "last-indexed.json"

NULL_SLOT = "*"
"""Used in cache key when task_type or problem_domain is None."""


def _bucket_key(task_type: str | None, problem_domain: str | None) -> str:
    """Format a cache key as ``{tt}|{pd}`` (with ``*`` for None)."""
    tt = task_type if task_type is not None else NULL_SLOT
    pd = problem_domain if problem_domain is not None else NULL_SLOT
    return f"{tt}|{pd}"


class WorkflowRecallCache:
    """Single-file JSON cache for ranked workflow sequences."""

    def __init__(self, garage_dir: Path) -> None:
        self._root = Path(garage_dir) / WORKFLOW_RECALL_DIR_NAME

    @property
    def cache_path(self) -> Path:
        return self._root / CACHE_FILE_NAME

    @property
    def last_indexed_path(self) -> Path:
        return self._root / LAST_INDEXED_FILE_NAME

    # ---- IO helpers ----

    def _ensure_dir(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)

    def _atomic_write(self, target: Path, payload: str) -> None:
        """Write atomically: tempfile + os.replace (single-syscall rename)."""
        target_dir = target.parent
        target_dir.mkdir(parents=True, exist_ok=True)
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

    # ---- Cache CRUD ----

    def load_cache(self) -> dict | None:
        """Return parsed cache dict, or None if missing / corrupted."""
        if not self.cache_path.is_file():
            return None
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None  # treat corrupted as missing; force rebuild

    def write_cache(self, payload: dict) -> Path:
        """Atomic write the full cache dict."""
        self._ensure_dir()
        text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        self._atomic_write(self.cache_path, text)
        return self.cache_path

    # ---- last-indexed CRUD ----

    def load_last_indexed(self) -> dict | None:
        """Return last-indexed metadata, or None if missing / corrupted."""
        if not self.last_indexed_path.is_file():
            return None
        try:
            return json.loads(self.last_indexed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def write_last_indexed(self, *, scanned_count: int, timestamp: datetime | None = None) -> Path:
        ts = timestamp or datetime.now()
        payload = {
            "last_indexed_at": ts.isoformat(),
            "scanned_count": int(scanned_count),
        }
        self._ensure_dir()
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        self._atomic_write(self.last_indexed_path, text)
        return self.last_indexed_path

    # ---- Invalidation ----

    def invalidate(self) -> bool:
        """Lazy invalidation: delete last-indexed.json (cache.json kept until next read).

        Returns True if a file was actually removed; False if already absent
        (idempotent — safe to call multiple times from caller hooks).
        """
        if not self.last_indexed_path.is_file():
            return False
        self.last_indexed_path.unlink()
        return True

    def is_stale(self) -> bool:
        """Return True if cache should be rebuilt (last-indexed.json missing or cache.json missing)."""
        return self.load_last_indexed() is None or not self.cache_path.is_file()
