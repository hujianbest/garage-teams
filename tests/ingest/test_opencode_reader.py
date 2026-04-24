"""F010 T5: OpenCodeHistoryReader tests."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from garage_os.ingest.host_readers.opencode import OpenCodeHistoryReader

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "opencode"


class TestListConversations:
    def test_list_returns_summaries(self) -> None:
        reader = OpenCodeHistoryReader(history_dir=FIXTURE_DIR, stderr=io.StringIO())
        summaries = reader.list_conversations()
        assert len(summaries) == 1
        assert summaries[0].conversation_id == "session-001"

    def test_corrupted_session_skipped(self) -> None:
        stderr = io.StringIO()
        reader = OpenCodeHistoryReader(history_dir=FIXTURE_DIR, stderr=stderr)
        reader.list_conversations()
        assert "Skipped unreadable opencode session" in stderr.getvalue()

    def test_missing_dir_returns_empty(self, tmp_path: Path) -> None:
        reader = OpenCodeHistoryReader(history_dir=tmp_path / "missing")
        assert reader.list_conversations() == []


class TestReadConversation:
    def test_read_valid(self) -> None:
        reader = OpenCodeHistoryReader(history_dir=FIXTURE_DIR)
        content = reader.read_conversation("session-001")
        assert content.conversation_id == "session-001"
        assert len(content.messages) == 2

    def test_read_missing_raises(self) -> None:
        reader = OpenCodeHistoryReader(history_dir=FIXTURE_DIR)
        with pytest.raises(FileNotFoundError):
            reader.read_conversation("nonexistent-session")
