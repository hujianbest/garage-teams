"""Tests for check_retrospective_readiness.py."""

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "scripts")
)

from check_retrospective_readiness import check_readiness


def test_directory_with_md_files(tmp_path):
    """Directory exists with .md files -> ready=True, count=N."""
    retro_dir = tmp_path / "retrospectives"
    retro_dir.mkdir()
    (retro_dir / "sprint-1.md").write_text("# Sprint 1\n")
    (retro_dir / "sprint-2.md").write_text("# Sprint 2\n")

    result = check_readiness(str(retro_dir))

    assert result["ready"] is True
    assert result["record_count"] == 2
    assert len(result["record_paths"]) == 2
    assert result["issues"] == []


def test_directory_exists_but_empty(tmp_path):
    """Directory exists but has no .md files -> ready=False."""
    retro_dir = tmp_path / "retrospectives"
    retro_dir.mkdir()

    result = check_readiness(str(retro_dir))

    assert result["ready"] is False
    assert result["record_count"] == 0
    assert result["record_paths"] == []
    assert len(result["issues"]) > 0


def test_directory_does_not_exist(tmp_path):
    """Directory does not exist -> ready=False."""
    retro_dir = tmp_path / "nonexistent"

    result = check_readiness(str(retro_dir))

    assert result["ready"] is False
    assert result["record_count"] == 0
    assert result["record_paths"] == []
    assert any("does not exist" in issue for issue in result["issues"])


def test_reported_subdirectory_excluded(tmp_path):
    """Files in reported/ subdirectory are excluded from count."""
    retro_dir = tmp_path / "retrospectives"
    retro_dir.mkdir()
    reported = retro_dir / "reported"
    reported.mkdir()

    (retro_dir / "sprint-1.md").write_text("# Sprint 1\n")
    (reported / "sprint-old.md").write_text("# Old Sprint\n")

    result = check_readiness(str(retro_dir))

    assert result["ready"] is True
    assert result["record_count"] == 1
    assert len(result["record_paths"]) == 1
    # Ensure the reported subdirectory file is not included
    for p in result["record_paths"]:
        assert os.path.join("reported", "") not in p


def test_non_md_files_excluded(tmp_path):
    """Non-.md files are excluded from count."""
    retro_dir = tmp_path / "retrospectives"
    retro_dir.mkdir()
    (retro_dir / "notes.txt").write_text("some notes")
    (retro_dir / "data.json").write_text("{}")
    (retro_dir / "image.png").write_bytes(b"\x89PNG")

    result = check_readiness(str(retro_dir))

    assert result["ready"] is False
    assert result["record_count"] == 0
    assert result["record_paths"] == []
