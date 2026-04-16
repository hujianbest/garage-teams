"""Tests for Garage OS CLI."""

import json
from pathlib import Path
from unittest.mock import patch

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

        # Create some session files
        sessions_active = garage_dir / "sessions" / "active"
        (sessions_active / "session-001.json").write_text(
            json.dumps({"id": "001"}), encoding="utf-8"
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
        assert "Sessions: 1" in captured.out
        assert "active: 1" in captured.out
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
