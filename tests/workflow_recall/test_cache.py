"""F014 T1 tests: WorkflowRecallCache CRUD + atomic write + invalidate + bucket key format."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from garage_os.workflow_recall.cache import (
    CACHE_FILE_NAME,
    LAST_INDEXED_FILE_NAME,
    NULL_SLOT,
    WORKFLOW_RECALL_DIR_NAME,
    WorkflowRecallCache,
    _bucket_key,
)


# T1.1
class TestLoadMissing:
    def test_cache_load_returns_none_when_missing(self, tmp_path: Path) -> None:
        cache = WorkflowRecallCache(tmp_path / ".garage")
        assert cache.load_cache() is None
        assert cache.load_last_indexed() is None


# T1.2
class TestAtomicWrite:
    def test_cache_write_atomic_no_partial_on_failure(self, tmp_path: Path) -> None:
        cache = WorkflowRecallCache(tmp_path / ".garage")
        target = cache.cache_path

        with patch("garage_os.workflow_recall.cache.os.replace") as mock_replace:
            mock_replace.side_effect = OSError("simulated atomic rename failure")
            with pytest.raises(OSError):
                cache.write_cache({"k|v": {"sequences": []}})

        # Target file should not exist (atomic semantics)
        assert not target.exists()


# T1.3
class TestRoundTrip:
    def test_cache_round_trip(self, tmp_path: Path) -> None:
        cache = WorkflowRecallCache(tmp_path / ".garage")
        original = {
            "implement|cli-design": {
                "sequences": [
                    {"skills": ["hf-specify", "hf-design"], "count": 5,
                     "avg_duration_seconds": 3580.0,
                     "top_lessons": [["lesson-a", 5]]},
                ],
                "total_records": 5,
            },
            "review|*": {"sequences": [], "total_records": 0},
        }
        cache.write_cache(original)
        loaded = cache.load_cache()
        assert loaded == original


# T1.4
class TestInvalidateDeletesLastIndexed:
    def test_invalidate_deletes_last_indexed(self, tmp_path: Path) -> None:
        cache = WorkflowRecallCache(tmp_path / ".garage")
        cache.write_last_indexed(scanned_count=10, timestamp=datetime(2026, 4, 26))
        assert cache.last_indexed_path.is_file()

        result = cache.invalidate()
        assert result is True
        assert not cache.last_indexed_path.is_file()

    def test_invalidate_idempotent_when_already_absent(self, tmp_path: Path) -> None:
        cache = WorkflowRecallCache(tmp_path / ".garage")
        # No last-indexed.json exists
        result = cache.invalidate()
        assert result is False  # nothing was removed


# T1.5
class TestStaleSemantics:
    def test_load_returns_stale_when_last_indexed_missing(self, tmp_path: Path) -> None:
        cache = WorkflowRecallCache(tmp_path / ".garage")
        # No data at all → stale
        assert cache.is_stale() is True

        # Cache exists but last-indexed missing → still stale
        cache.write_cache({"k|v": {}})
        assert cache.is_stale() is True

        # Both present → not stale
        cache.write_last_indexed(scanned_count=5)
        assert cache.is_stale() is False

        # last-indexed deleted (invalidate) → stale
        cache.invalidate()
        assert cache.is_stale() is True


# T1.6
class TestBucketKeyFormat:
    def test_bucket_key_with_both_args(self) -> None:
        assert _bucket_key("implement", "cli-design") == "implement|cli-design"

    def test_bucket_key_with_none_task_type(self) -> None:
        assert _bucket_key(None, "cli-design") == f"{NULL_SLOT}|cli-design"

    def test_bucket_key_with_none_problem_domain(self) -> None:
        assert _bucket_key("implement", None) == f"implement|{NULL_SLOT}"

    def test_bucket_key_with_both_none(self) -> None:
        assert _bucket_key(None, None) == f"{NULL_SLOT}|{NULL_SLOT}"


# T1.7
class TestLazyMkdir:
    def test_mkdir_on_first_write(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        cache = WorkflowRecallCache(garage_dir)
        # Before write: no workflow-recall dir
        assert not (garage_dir / WORKFLOW_RECALL_DIR_NAME).exists()

        cache.write_cache({"k|v": {}})
        assert (garage_dir / WORKFLOW_RECALL_DIR_NAME).is_dir()
        assert (garage_dir / WORKFLOW_RECALL_DIR_NAME / CACHE_FILE_NAME).is_file()


# T1.8
class TestCorruptedJson:
    def test_load_corrupted_cache_returns_none(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        cache = WorkflowRecallCache(garage_dir)
        cache._ensure_dir()
        cache.cache_path.write_text("{invalid json", encoding="utf-8")

        # Corrupted → treat as missing (force rebuild)
        assert cache.load_cache() is None

    def test_load_corrupted_last_indexed_returns_none(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        cache = WorkflowRecallCache(garage_dir)
        cache._ensure_dir()
        cache.last_indexed_path.write_text("not valid", encoding="utf-8")

        assert cache.load_last_indexed() is None


# T1.9 (bonus): file naming sentinel
class TestFileNames:
    def test_filenames_match_constants(self, tmp_path: Path) -> None:
        cache = WorkflowRecallCache(tmp_path / ".garage")
        assert cache.cache_path.name == CACHE_FILE_NAME
        assert cache.last_indexed_path.name == LAST_INDEXED_FILE_NAME
        assert cache.cache_path.parent.name == WORKFLOW_RECALL_DIR_NAME
