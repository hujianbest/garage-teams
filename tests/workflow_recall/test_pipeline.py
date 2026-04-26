"""F014 T3 tests: WorkflowRecallHook + compute_status_summary + 4 caller hook integration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord
from garage_os.workflow_recall.cache import WorkflowRecallCache
from garage_os.workflow_recall.pipeline import (
    WorkflowRecallHook,
    compute_status_summary,
)


def _setup(tmp_path: Path) -> Path:
    return tmp_path / ".garage"


# T3.1
class TestInvalidateDeletesLastIndexed:
    def test_invalidate_after_writing_last_indexed(self, tmp_path: Path) -> None:
        garage_dir = _setup(tmp_path)
        cache = WorkflowRecallCache(garage_dir)
        cache.write_last_indexed(scanned_count=5, timestamp=datetime(2026, 4, 26))
        assert cache.last_indexed_path.is_file()

        result = WorkflowRecallHook.invalidate(garage_dir)
        assert result.error is None
        assert result.skipped_reason is None
        assert result.invalidated is True
        assert not cache.last_indexed_path.is_file()


# T3.2
class TestInvalidateIdempotent:
    def test_invalidate_when_already_absent(self, tmp_path: Path) -> None:
        garage_dir = _setup(tmp_path)
        # No last-indexed.json exists
        result = WorkflowRecallHook.invalidate(garage_dir)
        assert result.error is None
        assert result.invalidated is False  # nothing was removed; idempotent


# T3.3
class TestFailureNonBlocking:
    def test_invalidate_failure_returns_error(self, tmp_path: Path) -> None:
        garage_dir = _setup(tmp_path)
        with patch("garage_os.workflow_recall.pipeline.WorkflowRecallCache") as mock_cls:
            mock_cls.return_value.invalidate.side_effect = OSError("simulated IO failure")
            result = WorkflowRecallHook.invalidate(garage_dir)
        assert result.error == "simulated IO failure"
        assert result.invalidated is False


# T3.4
class TestComputeStatusZeroRecords:
    def test_zero_records_emits_metadata_line(self, tmp_path: Path) -> None:
        garage_dir = _setup(tmp_path)
        summary = compute_status_summary(garage_dir)
        # Always emits metadata line (Im-6 + RSK-1401)
        assert "Workflow recall: scanned" in summary.metadata_line
        assert summary.scanned_records == 0
        assert summary.advisory_count == 0
        assert summary.stale is True


# T3.5
class TestComputeStatusWithAdvisories:
    def test_with_cache_built(self, tmp_path: Path) -> None:
        garage_dir = _setup(tmp_path)
        cache = WorkflowRecallCache(garage_dir)
        # Fake a built cache with 2 buckets meeting threshold
        cache.write_cache({
            "implement|cli-design": {
                "sequences": [{"skills": ["a"], "count": 5}],
                "total_records": 5,
            },
            "implement|review-verdict": {
                "sequences": [{"skills": ["b"], "count": 4}],
                "total_records": 4,
            },
            "review|*": {
                "sequences": [{"skills": ["c"], "count": 1}],
                "total_records": 1,  # below threshold (3)
            },
        })
        cache.write_last_indexed(scanned_count=10)

        summary = compute_status_summary(garage_dir)
        assert summary.scanned_records == 10
        assert summary.bucket_count == 3
        assert summary.advisory_count == 2  # only buckets ≥ 3 records
        assert summary.stale is False


# T3.6
class TestConfigGateDisabled:
    def test_workflow_recall_enabled_false(self, tmp_path: Path) -> None:
        garage_dir = _setup(tmp_path)
        storage = FileStorage(garage_dir)
        storage.write_json(
            "config/platform.json",
            {"schema_version": 1, "workflow_recall": {"enabled": False}},
        )
        result = WorkflowRecallHook.invalidate(garage_dir)
        assert result.skipped_reason == "hook_disabled"
        assert result.invalidated is False

    def test_status_shows_disabled(self, tmp_path: Path) -> None:
        garage_dir = _setup(tmp_path)
        storage = FileStorage(garage_dir)
        storage.write_json(
            "config/platform.json",
            {"schema_version": 1, "workflow_recall": {"enabled": False}},
        )
        summary = compute_status_summary(garage_dir)
        assert "(disabled" in summary.metadata_line
        assert summary.enabled is False


# T3.7 (integration sentinel)
class TestCallerHookIntegration:
    """Verify the 4 caller hook insertion points actually invalidate cache."""

    def test_experience_add_invalidates_cache(self, tmp_path: Path) -> None:
        """Path 2: cli._experience_add calls invalidate after EI.store."""
        from garage_os.cli import main

        workspace = tmp_path / "ws"
        workspace.mkdir()
        main(["init", "--path", str(workspace), "--yes"])

        cache = WorkflowRecallCache(workspace / ".garage")
        # Pre-write last-indexed so invalidate has something to remove
        cache.write_last_indexed(scanned_count=0)
        assert cache.last_indexed_path.is_file()

        main([
            "experience", "add",
            "--path", str(workspace),
            "--task-type", "review",
            "--skill", "hf-code-review",
            "--domain", "dev",
            "--outcome", "success",
            "--duration", "300",
            "--complexity", "low",
            "--summary", "test invalidation",
        ])
        # Hook should have invalidated last-indexed.json
        assert not cache.last_indexed_path.is_file()
