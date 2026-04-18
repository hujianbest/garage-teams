"""Tests for Garage OS CLI."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from garage_os.cli import main


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

