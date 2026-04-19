"""Tests for Garage OS CLI."""

import json
from pathlib import Path
from typing import Optional
from unittest.mock import patch, MagicMock

from garage_os.cli import main
from garage_os.storage.file_storage import FileStorage


class TestInitCreatesStructure:
    """Test that 'garage init' creates the expected directory structure."""

    EXPECTED_SUBDIRS = [
        "config/tools",
        "contracts",
        "knowledge/.metadata",
        "knowledge/decisions",
        "knowledge/patterns",
        "knowledge/solutions",
        "experience/records",
        "sessions/active",
        "sessions/archived",
    ]

    def test_init_creates_structure(self, tmp_path: Path) -> None:
        """init should create all expected sub-directories under .garage/."""
        main(["init", "--path", str(tmp_path)])

        garage_dir = tmp_path / ".garage"
        assert garage_dir.is_dir()

        for subdir in self.EXPECTED_SUBDIRS:
            assert (garage_dir / subdir).is_dir(), f"Missing .garage/{subdir}"

        # README should also exist
        assert (garage_dir / "README.md").is_file()


class TestInitIdempotent:
    """Test that running init twice does not raise."""

    def test_init_idempotent(self, tmp_path: Path) -> None:
        """Running init twice should succeed without errors."""
        main(["init", "--path", str(tmp_path)])
        # Second init should not raise
        main(["init", "--path", str(tmp_path)])

        garage_dir = tmp_path / ".garage"
        assert garage_dir.is_dir()


class TestStatusShowsStats:
    """Test that 'garage status' displays statistics when data exists."""

    def test_status_shows_stats(self, tmp_path: Path, capsys) -> None:
        """status should show session count, knowledge count, and recent experience."""
        # First init
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"

        # Create active and archived sessions using the runtime layout
        active_session_dir = garage_dir / "sessions" / "active" / "session-001"
        active_session_dir.mkdir(parents=True)
        (active_session_dir / "session.json").write_text(
            json.dumps({"session_id": "session-001"}), encoding="utf-8"
        )
        archived_session_dir = garage_dir / "sessions" / "archived" / "session-002"
        archived_session_dir.mkdir(parents=True)
        (archived_session_dir / "session.json").write_text(
            json.dumps({"session_id": "session-002"}), encoding="utf-8"
        )

        # Create a knowledge entry
        knowledge_decisions = garage_dir / "knowledge" / "decisions"
        (knowledge_decisions / "decision-001.md").write_text(
            "---\ntitle: test\n---\nbody", encoding="utf-8"
        )

        # Create an experience record
        experience_records = garage_dir / "experience" / "records"
        (experience_records / "exp-001.json").write_text(
            json.dumps({"id": "exp-001", "timestamp": "2025-01-15T10:00:00"}),
            encoding="utf-8",
        )

        main(["status", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert "Sessions: 2" in captured.out
        assert "active: 1" in captured.out
        assert "archived: 1" in captured.out
        assert "Knowledge entries: 1" in captured.out
        assert "Experience records: 1" in captured.out
        assert "2025-01-15T10:00:00" in captured.out


class TestStatusEmpty:
    """Test that 'garage status' shows 'No data' for empty repos."""

    def test_status_empty(self, tmp_path: Path, capsys) -> None:
        """status on empty .garage/ should print 'No data'."""
        main(["init", "--path", str(tmp_path)])
        main(["status", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert "No data" in captured.out

    def test_status_no_garage_dir(self, tmp_path: Path, capsys) -> None:
        """status without .garage/ should say directory not found."""
        main(["status", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert "No .garage/ directory found" in captured.out


class TestNoArgsShowsHelp:
    """Test that running CLI with no arguments shows help."""

    def test_no_args_shows_help(self, capsys) -> None:
        """Calling main([]) should print help text."""
        # Patch _find_garage_root so we don't depend on the real FS
        with patch("garage_os.cli._find_garage_root", return_value=Path.cwd()):
            main([])

        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "garage" in captured.out.lower()


class TestUnknownCommandShowsHelp:
    """Test that an unknown command shows help."""

    def test_unknown_command_shows_help(self, capsys) -> None:
        """An unrecognized sub-command should cause argparse to error / show help."""
        # argparse will raise SystemExit for unknown commands when using subparsers
        # Since we pass None to command, let's test the fallback behavior
        # argparse handles unknown commands by printing help and exiting with code 2
        import pytest

        with pytest.raises(SystemExit) as exc_info:
            main(["nonexistent"])

        # argparse exits with code 2 for unrecognized arguments
        assert exc_info.value.code == 2


class TestRunCommand:
    """Test that 'garage run' invokes skills and records experience."""

    def test_run_success(self, tmp_path: Path, capsys) -> None:
        """run should invoke skill, archive a completed session, and record experience."""
        from garage_os.types import SessionState

        # First init
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"

        # Mock ClaudeCodeAdapter.invoke_skill to return success
        mock_result = {"output": "Skill output", "exit_code": 0, "success": True}
        with patch("garage_os.cli.ClaudeCodeAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.invoke_skill.return_value = mock_result
            MockAdapter.return_value = mock_adapter

            result = main(["run", "test-skill", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert result == 0
        assert "Skill 'test-skill' completed successfully" in captured.out
        assert "Experience recorded:" in captured.out
        assert "Session archived:" in captured.out

        # Check session moved to archived and was updated to completed
        assert list((garage_dir / "sessions" / "active").iterdir()) == []
        sessions = list((garage_dir / "sessions" / "archived").iterdir())
        assert len(sessions) == 1
        session_file = sessions[0] / "session.json"
        session_data = json.loads(session_file.read_text(encoding="utf-8"))
        assert session_data["state"] == SessionState.COMPLETED.value
        assert session_data["pack_id"] == "test-skill"

        # Check experience record was created
        experience_records = list((garage_dir / "experience" / "records").glob("*.json"))
        assert len(experience_records) == 1
        exp_data = json.loads(experience_records[0].read_text(encoding="utf-8"))
        assert exp_data["outcome"] == "success"
        assert exp_data["skill_ids"] == ["test-skill"]
        assert exp_data["session_id"] == session_data["session_id"]

    def test_run_failure(self, tmp_path: Path, capsys) -> None:
        """run should archive failed sessions and record failed experience."""
        from garage_os.types import SessionState

        # First init
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"

        # Mock ClaudeCodeAdapter.invoke_skill to return failure
        mock_result = {"output": "Error occurred", "exit_code": 1, "success": False}
        with patch("garage_os.cli.ClaudeCodeAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.invoke_skill.return_value = mock_result
            MockAdapter.return_value = mock_adapter

            result = main(["run", "failing-skill", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert result == 1
        assert "Skill 'failing-skill' failed" in captured.out
        assert "Experience recorded:" in captured.out
        assert "Session archived:" in captured.out

        # Check session moved to archived and was updated to failed
        assert list((garage_dir / "sessions" / "active").iterdir()) == []
        sessions = list((garage_dir / "sessions" / "archived").iterdir())
        assert len(sessions) == 1
        session_file = sessions[0] / "session.json"
        session_data = json.loads(session_file.read_text(encoding="utf-8"))
        assert session_data["state"] == SessionState.FAILED.value

        # Check experience record was created with failure outcome
        experience_records = list((garage_dir / "experience" / "records").glob("*.json"))
        assert len(experience_records) == 1
        exp_data = json.loads(experience_records[0].read_text(encoding="utf-8"))
        assert exp_data["outcome"] == "failure"

    def test_run_creates_session(self, tmp_path: Path) -> None:
        """run should create and archive a new session for each invocation."""
        # First init
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"

        # Mock ClaudeCodeAdapter
        with patch("garage_os.cli.ClaudeCodeAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.invoke_skill.return_value = {
                "output": "",
                "exit_code": 0,
                "success": True,
            }
            MockAdapter.return_value = mock_adapter

            # Run two skills
            main(["run", "skill1", "--path", str(tmp_path)])
            main(["run", "skill2", "--path", str(tmp_path)])

        # Check two archived sessions were created
        assert list((garage_dir / "sessions" / "active").iterdir()) == []
        sessions = list((garage_dir / "sessions" / "archived").iterdir())
        assert len(sessions) == 2

    def test_run_returns_nonzero_on_exception(self, tmp_path: Path, capsys) -> None:
        """run should return non-zero when the adapter raises an exception."""
        main(["init", "--path", str(tmp_path)])

        with patch("garage_os.cli.ClaudeCodeAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.invoke_skill.side_effect = Exception("boom")
            MockAdapter.return_value = mock_adapter

            result = main(["run", "broken-skill", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert result == 1
        assert "Error running skill 'broken-skill': boom" in captured.out

    def test_run_passes_timeout_to_adapter(self, tmp_path: Path) -> None:
        """run should pass the requested timeout through to ClaudeCodeAdapter."""
        main(["init", "--path", str(tmp_path)])

        with patch("garage_os.cli.ClaudeCodeAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.invoke_skill.return_value = {
                "output": "",
                "exit_code": 0,
                "success": True,
            }
            MockAdapter.return_value = mock_adapter

            result = main(
                ["run", "timed-skill", "--timeout", "17", "--path", str(tmp_path)]
            )

        assert result == 0
        MockAdapter.assert_called_once_with(tmp_path, timeout=17)

    def test_run_skips_recommendation_when_disabled(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """run must NOT print recommendations when the feature flag is off (T4 acceptance)."""
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"
        platform_json = garage_dir / "config" / "platform.json"
        config = json.loads(platform_json.read_text(encoding="utf-8"))
        assert config["memory"]["recommendation_enabled"] is False

        decision_path = garage_dir / "knowledge" / "decisions" / "decision-disabled.md"
        decision_path.write_text(
            """---
id: decision-disabled
type: decision
topic: Recommendation for disabled-skill
date: 2026-04-18T10:00:00
tags: [disabled-skill, workspace-first]
status: active
version: 1
---

Should not be surfaced when recommendation is disabled.
""",
            encoding="utf-8",
        )

        with patch("garage_os.cli.ClaudeCodeAdapter") as MockAdapter, \
            patch("garage_os.cli.RecommendationService") as MockRecommendationService:
            mock_adapter = MagicMock()
            mock_adapter.invoke_skill.return_value = {
                "output": "",
                "exit_code": 0,
                "success": True,
            }
            MockAdapter.return_value = mock_adapter

            result = main(["run", "disabled-skill", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert result == 0
        assert "Recommendations:" not in captured.out
        MockRecommendationService.assert_not_called()

    def test_run_shows_recommendation_summary_when_enabled(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """run should print a recommendation summary before execution when enabled."""
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"
        platform_json = garage_dir / "config" / "platform.json"
        config = json.loads(platform_json.read_text(encoding="utf-8"))
        config["memory"]["recommendation_enabled"] = True
        platform_json.write_text(json.dumps(config), encoding="utf-8")

        decision_path = garage_dir / "knowledge" / "decisions" / "decision-memory.md"
        decision_path.write_text(
            """---
id: decision-memory
type: decision
topic: Recommendation for timed-skill
date: 2026-04-18T10:00:00
tags: [timed-skill, workspace-first]
status: active
version: 1
---

Use workspace-first memory recommendations.
""",
            encoding="utf-8",
        )

        with patch("garage_os.cli.ClaudeCodeAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.invoke_skill.return_value = {
                "output": "",
                "exit_code": 0,
                "success": True,
            }
            MockAdapter.return_value = mock_adapter

            result = main(["run", "timed-skill", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert result == 0
        assert "Recommendations:" in captured.out
        assert "Recommendation for timed-skill" in captured.out


class TestExperienceRecording:
    """Test that experience is automatically recorded after skill execution."""

    def test_experience_recorded_on_success(self, tmp_path: Path) -> None:
        """Successful skill execution should create experience record with success outcome."""
        # First init
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"

        # Mock ClaudeCodeAdapter
        with patch("garage_os.cli.ClaudeCodeAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.invoke_skill.return_value = {
                "output": "Success",
                "exit_code": 0,
                "success": True,
            }
            MockAdapter.return_value = mock_adapter

            main(["run", "test-skill", "--path", str(tmp_path)])

        # Check experience record
        experience_records = list((garage_dir / "experience" / "records").glob("*.json"))
        assert len(experience_records) == 1
        exp_data = json.loads(experience_records[0].read_text(encoding="utf-8"))

        # Verify fields
        assert exp_data["outcome"] == "success"
        assert exp_data["task_type"] == "skill_execution"
        assert exp_data["skill_ids"] == ["test-skill"]
        assert exp_data["problem_domain"] == "test-skill"
        assert "duration_seconds" in exp_data
        assert "session_id" in exp_data
        assert "created_at" in exp_data
        assert "updated_at" in exp_data

    def test_experience_recorded_on_failure(self, tmp_path: Path) -> None:
        """Failed skill execution should create experience record with failure outcome."""
        # First init
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"

        # Mock ClaudeCodeAdapter to raise exception
        with patch("garage_os.cli.ClaudeCodeAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.invoke_skill.side_effect = Exception("Skill failed")
            MockAdapter.return_value = mock_adapter

            main(["run", "failing-skill", "--path", str(tmp_path)])

        # Check experience record was created even on exception
        experience_records = list((garage_dir / "experience" / "records").glob("*.json"))
        assert len(experience_records) == 1
        exp_data = json.loads(experience_records[0].read_text(encoding="utf-8"))

        # Verify failure outcome
        assert exp_data["outcome"] == "failure"
        assert exp_data["skill_ids"] == ["failing-skill"]


class TestMemoryReviewCommand:
    """Test CLI memory review command."""

    def test_memory_review_shows_batch_summary(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """memory review should show candidate batch summary."""
        from garage_os.memory.candidate_store import CandidateStore

        main(["init", "--path", str(tmp_path)])
        storage = FileStorage(tmp_path / ".garage")
        candidate_store = CandidateStore(storage)
        candidate_store.store_candidate(
            {
                "schema_version": "1",
                "candidate_id": "candidate-001",
                "candidate_type": "decision",
                "session_id": "session-001",
                "source_artifacts": ["docs/designs/example.md"],
                "match_reasons": ["artifact:docs/designs/example.md"],
                "status": "pending_review",
                "priority_score": 0.9,
                "title": "Use candidate batches",
                "summary": "Summary",
                "content": "Body",
            }
        )
        candidate_store.store_batch(
            {
                "batch_id": "batch-001",
                "session_id": "session-001",
                "status": "pending_review",
                "trigger": "session_archived",
                "candidate_ids": ["candidate-001"],
                "truncated_count": 0,
                "evaluation_summary": "evaluated_with_candidates",
                "created_at": "2026-04-18T10:00:00",
                "metadata": {},
            }
        )

        result = main(["memory", "review", "batch-001", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert result == 0
        assert "Candidate Batch: batch-001" in captured.out
        assert "Use candidate batches" in captured.out

    def test_memory_review_batch_reject_updates_candidates(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """batch_reject should reject every candidate in the batch."""
        from garage_os.memory.candidate_store import CandidateStore

        main(["init", "--path", str(tmp_path)])
        storage = FileStorage(tmp_path / ".garage")
        candidate_store = CandidateStore(storage)
        for candidate_id in ["candidate-001", "candidate-002"]:
            candidate_store.store_candidate(
                {
                    "schema_version": "1",
                    "candidate_id": candidate_id,
                    "candidate_type": "decision",
                    "session_id": "session-001",
                    "source_artifacts": ["docs/designs/example.md"],
                    "match_reasons": ["artifact:docs/designs/example.md"],
                    "status": "pending_review",
                    "priority_score": 0.9,
                    "title": f"Title {candidate_id}",
                    "summary": "Summary",
                    "content": "Body",
                }
            )
        candidate_store.store_batch(
            {
                "batch_id": "batch-001",
                "session_id": "session-001",
                "status": "pending_review",
                "trigger": "session_archived",
                "candidate_ids": ["candidate-001", "candidate-002"],
                "truncated_count": 0,
                "evaluation_summary": "evaluated_with_candidates",
                "created_at": "2026-04-18T10:00:00",
                "metadata": {},
            }
        )

        result = main(
            [
                "memory",
                "review",
                "batch-001",
                "--action",
                "batch_reject",
                "--path",
                str(tmp_path),
            ]
        )

        captured = capsys.readouterr()
        assert result == 0
        assert "Applied action 'batch_reject'" in captured.out
        assert candidate_store.retrieve_candidate("candidate-001")["status"] == "rejected"
        assert candidate_store.retrieve_candidate("candidate-002")["status"] == "rejected"

    def test_memory_review_defer_marks_batch_pending_later(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """defer should keep the batch available for later review."""
        from garage_os.memory.candidate_store import CandidateStore

        main(["init", "--path", str(tmp_path)])
        storage = FileStorage(tmp_path / ".garage")
        candidate_store = CandidateStore(storage)
        candidate_store.store_candidate(
            {
                "schema_version": "1",
                "candidate_id": "candidate-001",
                "candidate_type": "decision",
                "session_id": "session-001",
                "source_artifacts": ["docs/designs/example.md"],
                "match_reasons": ["artifact:docs/designs/example.md"],
                "status": "pending_review",
                "priority_score": 0.9,
                "title": "Keep later",
                "summary": "Summary",
                "content": "Body",
            }
        )
        candidate_store.store_batch(
            {
                "batch_id": "batch-001",
                "session_id": "session-001",
                "status": "pending_review",
                "trigger": "session_archived",
                "candidate_ids": ["candidate-001"],
                "truncated_count": 0,
                "evaluation_summary": "evaluated_with_candidates",
                "created_at": "2026-04-18T10:00:00",
                "metadata": {},
            }
        )

        result = main(
            [
                "memory",
                "review",
                "batch-001",
                "--action",
                "defer",
                "--path",
                str(tmp_path),
            ]
        )

        captured = capsys.readouterr()
        assert result == 0
        assert "Applied action 'defer'" in captured.out
        assert candidate_store.retrieve_batch("batch-001")["status"] == "deferred"


    def test_memory_review_accept_requires_strategy_when_conflict_exists(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """accept must surface the FR-304 strategy choice when a similar entry exists."""
        from garage_os.memory.candidate_store import CandidateStore

        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"
        decisions_dir = garage_dir / "knowledge" / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)
        (decisions_dir / "decision-existing.md").write_text(
            """---
id: existing
type: decision
topic: Use candidate batches
date: 2026-04-18T10:00:00
tags: [memory]
status: active
version: 1
---

Existing decision body.
""",
            encoding="utf-8",
        )

        storage = FileStorage(garage_dir)
        candidate_store = CandidateStore(storage)
        candidate_store.store_candidate(
            {
                "schema_version": "1",
                "candidate_id": "candidate-001",
                "candidate_type": "decision",
                "session_id": "session-001",
                "source_artifacts": ["docs/designs/example.md"],
                "source_evidence_anchors": [
                    {"kind": "artifact_excerpt", "ref": "docs/designs/example.md#decision"}
                ],
                "match_reasons": ["artifact:docs/designs/example.md"],
                "status": "pending_review",
                "priority_score": 0.9,
                "title": "Use candidate batches",
                "summary": "Summary",
                "content": "Body",
                "tags": ["memory"],
            }
        )
        candidate_store.store_batch(
            {
                "batch_id": "batch-001",
                "session_id": "session-001",
                "status": "pending_review",
                "trigger": "session_archived",
                "candidate_ids": ["candidate-001"],
                "truncated_count": 0,
                "evaluation_summary": "evaluated_with_candidates",
                "created_at": "2026-04-18T10:00:00",
                "metadata": {},
            }
        )

        result = main(
            [
                "memory",
                "review",
                "batch-001",
                "--action",
                "accept",
                "--candidate-id",
                "candidate-001",
                "--path",
                str(tmp_path),
            ]
        )

        captured = capsys.readouterr()
        assert result == 1
        assert "--strategy" in captured.out

    def test_memory_review_abandon_skips_publication(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """abandon must be a first-class CLI action that skips publication (FR-304)."""
        from garage_os.memory.candidate_store import CandidateStore

        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"
        storage = FileStorage(garage_dir)
        candidate_store = CandidateStore(storage)
        candidate_store.store_candidate(
            {
                "schema_version": "1",
                "candidate_id": "candidate-001",
                "candidate_type": "decision",
                "session_id": "session-001",
                "source_artifacts": ["docs/designs/example.md"],
                "source_evidence_anchors": [
                    {"kind": "artifact_excerpt", "ref": "docs/designs/example.md#decision"}
                ],
                "match_reasons": ["artifact:docs/designs/example.md"],
                "status": "pending_review",
                "priority_score": 0.9,
                "title": "Abandon-able candidate",
                "summary": "Summary",
                "content": "Body",
            }
        )
        candidate_store.store_batch(
            {
                "batch_id": "batch-001",
                "session_id": "session-001",
                "status": "pending_review",
                "trigger": "session_archived",
                "candidate_ids": ["candidate-001"],
                "truncated_count": 0,
                "evaluation_summary": "evaluated_with_candidates",
                "created_at": "2026-04-18T10:00:00",
                "metadata": {},
            }
        )

        result = main(
            [
                "memory",
                "review",
                "batch-001",
                "--action",
                "abandon",
                "--candidate-id",
                "candidate-001",
                "--path",
                str(tmp_path),
            ]
        )

        captured = capsys.readouterr()
        assert result == 0
        assert "abandon" in captured.out.lower()
        assert candidate_store.retrieve_candidate("candidate-001")["status"] == "abandoned"
        published = list((garage_dir / "knowledge" / "decisions").glob("*.md"))
        assert published == []


class TestMemoryReviewAbandonDualPaths:
    """F004 T3: CLI abandon dual-path differentiation (FR-403a + FR-403b + ADR-403).

    Locks differentiation between:
    - ``--action=abandon``                       -> intentionally drop candidate
    - ``--action=accept --strategy=abandon``     -> abandon because of conflict
    """

    def _seed_candidate(
        self,
        tmp_path: Path,
        candidate_id: str = "candidate-001",
        title: str = "Dual-path abandon candidate",
        tags: Optional[list[str]] = None,
    ):
        from garage_os.memory.candidate_store import CandidateStore

        garage_dir = tmp_path / ".garage"
        storage = FileStorage(garage_dir)
        candidate_store = CandidateStore(storage)
        candidate_store.store_candidate(
            {
                "schema_version": "1",
                "candidate_id": candidate_id,
                "candidate_type": "decision",
                "session_id": "session-001",
                "source_artifacts": ["docs/designs/example.md"],
                "source_evidence_anchors": [
                    {"kind": "artifact_excerpt", "ref": "docs/designs/example.md#decision"}
                ],
                "match_reasons": ["artifact:docs/designs/example.md"],
                "status": "pending_review",
                "priority_score": 0.9,
                "title": title,
                "summary": "Summary",
                "content": "Body",
                "tags": tags or ["memory", "abandon"],
            }
        )
        candidate_store.store_batch(
            {
                "batch_id": "batch-001",
                "session_id": "session-001",
                "status": "pending_review",
                "trigger": "session_archived",
                "candidate_ids": [candidate_id],
                "truncated_count": 0,
                "evaluation_summary": "evaluated_with_candidates",
                "created_at": "2026-04-18T10:00:00",
                "metadata": {},
            }
        )
        return candidate_store, garage_dir, storage

    def _seed_existing_published_entry_with_same_title(
        self,
        garage_dir: Path,
        title: str,
        tags: list[str],
    ) -> str:
        """Plant a v1-published KnowledgeEntry with a different id but same
        title/tags so ConflictDetector surfaces it as a real similar entry
        (and is not stripped by F004 self-conflict short-circuit)."""
        from datetime import datetime
        from garage_os.knowledge.knowledge_store import KnowledgeStore
        from garage_os.types import KnowledgeEntry, KnowledgeType

        storage = FileStorage(garage_dir)
        knowledge_store = KnowledgeStore(storage)
        existing_id = "existing-conflict-target"
        knowledge_store.store(
            KnowledgeEntry(
                id=existing_id,
                type=KnowledgeType.DECISION,
                topic=title,
                date=datetime.now(),
                tags=list(tags),
                content="Pre-existing entry to force a real conflict.",
            )
        )
        return existing_id

    def test_memory_review_abandon_writes_resolution_abandon_with_null_strategy(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """--action=abandon path -> confirmation resolution=abandon, conflict_strategy=null (FR-403a verify 1)."""
        main(["init", "--path", str(tmp_path)])
        candidate_store, garage_dir, _ = self._seed_candidate(tmp_path)

        result = main(
            [
                "memory",
                "review",
                "batch-001",
                "--action",
                "abandon",
                "--candidate-id",
                "candidate-001",
                "--path",
                str(tmp_path),
            ]
        )
        assert result == 0
        confirmation = candidate_store.retrieve_confirmation("batch-001")
        assert confirmation is not None
        assert confirmation["resolution"] == "abandon"
        assert confirmation.get("conflict_strategy") in (None,)

    def test_memory_review_accept_with_strategy_abandon_writes_resolution_accept(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """--action=accept --strategy=abandon + real conflict -> resolution=accept,
        conflict_strategy=abandon (FR-403a verify 2)."""
        main(["init", "--path", str(tmp_path)])
        candidate_store, garage_dir, _ = self._seed_candidate(tmp_path)
        self._seed_existing_published_entry_with_same_title(
            garage_dir,
            title="Dual-path abandon candidate",
            tags=["memory", "abandon"],
        )

        result = main(
            [
                "memory",
                "review",
                "batch-001",
                "--action",
                "accept",
                "--candidate-id",
                "candidate-001",
                "--strategy",
                "abandon",
                "--path",
                str(tmp_path),
            ]
        )
        assert result == 0
        confirmation = candidate_store.retrieve_confirmation("batch-001")
        assert confirmation is not None
        assert confirmation["resolution"] == "accept"
        assert confirmation.get("conflict_strategy") == "abandon"
        assert (
            candidate_store.retrieve_candidate("candidate-001")["status"] == "abandoned"
        )

    def test_memory_review_accept_with_abandon_strategy_no_conflict_falls_through_to_publish(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """--action=accept --strategy=abandon + no conflict -> normal publish (FR-403a verify 3)."""
        main(["init", "--path", str(tmp_path)])
        candidate_store, garage_dir, _ = self._seed_candidate(tmp_path)

        result = main(
            [
                "memory",
                "review",
                "batch-001",
                "--action",
                "accept",
                "--candidate-id",
                "candidate-001",
                "--strategy",
                "abandon",
                "--path",
                str(tmp_path),
            ]
        )
        assert result == 0
        confirmation = candidate_store.retrieve_confirmation("batch-001")
        assert confirmation is not None
        assert confirmation["resolution"] == "accept"
        # Strategy was passed but no conflict matched -> behavior matches v1 normal accept.
        assert (
            candidate_store.retrieve_candidate("candidate-001")["status"] == "published"
        )

    def test_memory_review_abandon_outputs_no_pub_marker(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """--action=abandon stdout must contain ABANDONED_NO_PUB marker (FR-403b verify 1)."""
        from garage_os.cli import MEMORY_REVIEW_ABANDONED_NO_PUB

        main(["init", "--path", str(tmp_path)])
        self._seed_candidate(tmp_path)

        main(
            [
                "memory",
                "review",
                "batch-001",
                "--action",
                "abandon",
                "--candidate-id",
                "candidate-001",
                "--path",
                str(tmp_path),
            ]
        )

        captured = capsys.readouterr()
        expected = MEMORY_REVIEW_ABANDONED_NO_PUB.format(cid="candidate-001")
        assert expected in captured.out, (
            f"expected stdout to contain '{expected}'; got: {captured.out}"
        )

    def test_memory_review_conflict_abandon_outputs_conflict_marker(
        self,
        tmp_path: Path,
        capsys,
    ) -> None:
        """--action=accept --strategy=abandon + real conflict stdout must contain ABANDONED_CONFLICT marker
        (FR-403b verify 2)."""
        from garage_os.cli import MEMORY_REVIEW_ABANDONED_CONFLICT

        main(["init", "--path", str(tmp_path)])
        _, garage_dir, _ = self._seed_candidate(tmp_path)
        self._seed_existing_published_entry_with_same_title(
            garage_dir,
            title="Dual-path abandon candidate",
            tags=["memory", "abandon"],
        )

        main(
            [
                "memory",
                "review",
                "batch-001",
                "--action",
                "accept",
                "--candidate-id",
                "candidate-001",
                "--strategy",
                "abandon",
                "--path",
                str(tmp_path),
            ]
        )

        captured = capsys.readouterr()
        expected = MEMORY_REVIEW_ABANDONED_CONFLICT.format(cid="candidate-001")
        assert expected in captured.out, (
            f"expected stdout to contain '{expected}'; got: {captured.out}"
        )

    def test_memory_review_two_abandon_markers_do_not_overlap(self) -> None:
        """The two stdout markers must be independently grep-able (FR-403b verify 3)."""
        from garage_os.cli import (
            MEMORY_REVIEW_ABANDONED_CONFLICT,
            MEMORY_REVIEW_ABANDONED_NO_PUB,
        )

        no_pub = MEMORY_REVIEW_ABANDONED_NO_PUB.format(cid="x")
        conflict = MEMORY_REVIEW_ABANDONED_CONFLICT.format(cid="x")
        # Neither rendered marker should be a substring of the other.
        assert no_pub not in conflict
        assert conflict not in no_pub


class TestKnowledgeCommand:
    """Test knowledge search and list commands."""

    def test_knowledge_search(self, tmp_path: Path, capsys) -> None:
        """knowledge search should find matching entries."""
        # First init
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"

        # Create a knowledge entry
        knowledge_decisions = garage_dir / "knowledge" / "decisions"
        knowledge_decisions.mkdir(parents=True, exist_ok=True)
        (knowledge_decisions / "decision-001.md").write_text(
            """---
id: decision-001
type: decision
topic: Use REST API
date: 2025-01-15T10:00:00
tags: [api, rest]
status: active
version: 1
---

Decided to use REST API for this service.
""",
            encoding="utf-8",
        )

        # Search for the entry
        main(["knowledge", "search", "REST", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert "Found 1 knowledge entry" in captured.out
        assert "[DECISION] Use REST API" in captured.out
        assert "ID: decision-001" in captured.out
        assert "Tags: api, rest" in captured.out

    def test_knowledge_list(self, tmp_path: Path, capsys) -> None:
        """knowledge list should show all entries."""
        # First init
        main(["init", "--path", str(tmp_path)])
        garage_dir = tmp_path / ".garage"

        # Create multiple knowledge entries
        knowledge_decisions = garage_dir / "knowledge" / "decisions"
        knowledge_patterns = garage_dir / "knowledge" / "patterns"

        knowledge_decisions.mkdir(parents=True, exist_ok=True)
        knowledge_patterns.mkdir(parents=True, exist_ok=True)

        (knowledge_decisions / "decision-001.md").write_text(
            """---
id: decision-001
type: decision
topic: Use TypeScript
date: 2025-01-15T10:00:00
tags: [typescript]
status: active
version: 1
---

Decided to use TypeScript.
""",
            encoding="utf-8",
        )

        (knowledge_patterns / "pattern-001.md").write_text(
            """---
id: pattern-001
type: pattern
topic: Repository Pattern
date: 2025-01-16T10:00:00
tags: [design-pattern]
status: active
version: 1
---

Repository pattern implementation.
""",
            encoding="utf-8",
        )

        # List all entries
        main(["knowledge", "list", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert "Total 2 knowledge entry" in captured.out
        assert "[DECISION] Use TypeScript" in captured.out
        assert "[PATTERN] Repository Pattern" in captured.out

    def test_knowledge_empty(self, tmp_path: Path, capsys) -> None:
        """knowledge commands should show 'No knowledge entries' when empty."""
        # First init
        main(["init", "--path", str(tmp_path)])

        # List when empty
        main(["knowledge", "list", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert "No knowledge entries" in captured.out

        # Search when empty
        main(["knowledge", "search", "test", "--path", str(tmp_path)])

        captured = capsys.readouterr()
        assert "No knowledge entries" in captured.out

