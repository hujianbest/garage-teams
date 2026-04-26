"""F013-A T4 tests: SkillMiningHook + audit/decay + status summary."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.skill_mining.pipeline import (
    SkillMiningHook,
    compute_status_summary,
    run_audit,
)
from garage_os.skill_mining.suggestion_store import SuggestionStore
from garage_os.skill_mining.types import SkillSuggestion, SkillSuggestionStatus
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord


def _record(rid: str, session_id: str = "ses-1") -> ExperienceRecord:
    return ExperienceRecord(
        record_id=rid,
        task_type="task",
        skill_ids=[],
        tech_stack=[],
        domain="dev",
        problem_domain="review-verdict",
        outcome="success",
        duration_seconds=60,
        complexity="low",
        session_id=session_id,
        key_patterns=["verdict-format", "5-section"],
    )


def _setup(tmp_path: Path) -> tuple[Path, KnowledgeStore, ExperienceIndex, SuggestionStore]:
    garage_dir = tmp_path / ".garage"
    storage = FileStorage(garage_dir)
    return garage_dir, KnowledgeStore(storage), ExperienceIndex(storage), SuggestionStore(garage_dir)


# T4.pipeline.1
class TestHookRunsAfterExtraction:
    def test_hook_writes_proposal_when_threshold_met(self, tmp_path: Path) -> None:
        garage_dir, ks, ei, ss = _setup(tmp_path)
        for i in range(5):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))
        result = SkillMiningHook.run_after_extraction(
            session_id="ses-test",
            garage_dir=garage_dir,
            packs_root=tmp_path / "packs",
        )
        assert result.error is None
        assert result.skipped_reason is None
        assert result.new_suggestions_count == 1
        # Verify proposal written
        proposed = ss.list_by_status(SkillSuggestionStatus.PROPOSED)
        assert len(proposed) == 1


# T4.pipeline.2
class TestHookIdempotent:
    def test_repeat_session_no_duplicate(self, tmp_path: Path) -> None:
        garage_dir, ks, ei, ss = _setup(tmp_path)
        for i in range(5):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))

        SkillMiningHook.run_after_extraction(
            session_id="ses-test",
            garage_dir=garage_dir,
            packs_root=tmp_path / "packs",
        )
        first_count = len(ss.list_by_status(SkillSuggestionStatus.PROPOSED))

        SkillMiningHook.run_after_extraction(
            session_id="ses-test",
            garage_dir=garage_dir,
            packs_root=tmp_path / "packs",
        )
        second_count = len(ss.list_by_status(SkillSuggestionStatus.PROPOSED))
        assert first_count == second_count == 1


# T4.pipeline.3
class TestHookFailureNonBlocking:
    def test_hook_failure_does_not_raise(self, tmp_path: Path) -> None:
        garage_dir, ks, ei, ss = _setup(tmp_path)
        with patch(
            "garage_os.skill_mining.pipeline.detect_and_write",
            side_effect=RuntimeError("simulated detector failure"),
        ):
            result = SkillMiningHook.run_after_extraction(
                session_id="ses-test",
                garage_dir=garage_dir,
                packs_root=tmp_path / "packs",
            )
        assert result.error == "simulated detector failure"
        assert result.new_suggestions_count == 0


# T4.pipeline.4
class TestAuditDecay:
    def test_audit_marks_expired(self, tmp_path: Path) -> None:
        garage_dir, ks, ei, ss = _setup(tmp_path)
        # Manually create a proposed suggestion 31 days old
        old_time = datetime(2026, 3, 25, 12, 0, 0)
        suggestion = SkillSuggestion(
            id="sg-old-001",
            suggested_name="old-skill",
            suggested_description="x" * 60,
            problem_domain_key="review-verdict",
            tag_bucket=["a"],
            evidence_entries=[],
            evidence_records=["r-1"],
            suggested_pack="garage",
            score=1.0,
            status=SkillSuggestionStatus.PROPOSED,
            created_at=old_time,
            expires_at=old_time + timedelta(days=30),  # 2026-04-24
        )
        ss.write(suggestion)

        # Run audit at a date past expiry
        expired = run_audit(garage_dir, now=datetime(2026, 4, 26, 12, 0, 0))
        assert expired == 1
        # Verify moved to expired/
        assert ss.list_by_status(SkillSuggestionStatus.PROPOSED) == []
        assert len(ss.list_by_status(SkillSuggestionStatus.EXPIRED)) == 1


# T4.pipeline.5
class TestComputeStatusSummary:
    def test_zero_proposed_no_hint_line(self, tmp_path: Path) -> None:
        garage_dir, _, _, _ = _setup(tmp_path)
        summary = compute_status_summary(garage_dir)
        assert summary.proposed_count == 0
        assert summary.hint_line is None  # 💡 only when proposed > 0
        assert "Skill mining: scanned" in summary.metadata_line

    def test_proposed_emits_hint_line(self, tmp_path: Path) -> None:
        garage_dir, ks, ei, ss = _setup(tmp_path)
        for i in range(5):
            ei.store(_record(f"r-{i}", session_id=f"ses-{i}"))
        SkillMiningHook.run_after_extraction(
            session_id="ses-test",
            garage_dir=garage_dir,
            packs_root=tmp_path / "packs",
        )
        summary = compute_status_summary(garage_dir)
        assert summary.proposed_count == 1
        assert summary.hint_line is not None
        assert "💡" in summary.hint_line


# T4.pipeline.6
class TestConfigGateHookEnabled:
    def test_hook_disabled_via_platform_config(self, tmp_path: Path) -> None:
        garage_dir = tmp_path / ".garage"
        storage = FileStorage(garage_dir)
        # Write platform.json with hook_enabled=false
        storage.write_json(
            "config/platform.json",
            {"schema_version": 1, "skill_mining": {"hook_enabled": False}},
        )
        result = SkillMiningHook.run_after_extraction(
            session_id="ses-test",
            garage_dir=garage_dir,
        )
        assert result.skipped_reason == "hook_disabled"
        assert result.new_suggestions_count == 0
