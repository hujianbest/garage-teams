"""F010 T5: ClaudeCodeHistoryReader tests."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from garage_os.ingest.host_readers.claude_code import ClaudeCodeHistoryReader

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "claude_code"


class TestListConversations:
    def test_list_returns_summaries(self) -> None:
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR, stderr=io.StringIO())
        summaries = reader.list_conversations()
        # 1 valid + 1 corrupted (skipped) = 1
        assert len(summaries) == 1
        assert summaries[0].conversation_id == "conversation-001"
        assert "F010 design" in summaries[0].topic
        assert summaries[0].message_count == 4

    def test_corrupted_json_skipped_with_stderr_warn(self) -> None:
        stderr = io.StringIO()
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR, stderr=stderr)
        reader.list_conversations()
        assert "Skipped unreadable conversation" in stderr.getvalue()
        assert "conversation-002-broken" in stderr.getvalue()

    def test_missing_dir_returns_empty(self, tmp_path: Path) -> None:
        reader = ClaudeCodeHistoryReader(history_dir=tmp_path / "nonexistent")
        assert reader.list_conversations() == []

    def test_max_entries_limits(self) -> None:
        reader = ClaudeCodeHistoryReader(
            history_dir=FIXTURE_DIR, stderr=io.StringIO(), max_entries=0
        )
        assert reader.list_conversations() == []


class TestReadConversation:
    def test_read_valid(self) -> None:
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR)
        content = reader.read_conversation("conversation-001")
        assert content.conversation_id == "conversation-001"
        assert len(content.messages) == 4

    def test_read_missing_raises(self) -> None:
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR)
        with pytest.raises(FileNotFoundError):
            reader.read_conversation("nonexistent")

    def test_read_corrupted_raises(self) -> None:
        import json
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR)
        with pytest.raises(json.JSONDecodeError):
            reader.read_conversation("conversation-002-broken")


class TestConversationContentHelpers:
    """ADR-D10-9 r2 signal-fill helpers."""

    def test_topic_or_summary(self) -> None:
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR)
        content = reader.read_conversation("conversation-001")
        assert "F010 design" in content.topic_or_summary()

    def test_first_user_message_excerpt(self) -> None:
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR)
        content = reader.read_conversation("conversation-001")
        excerpt = content.first_user_message_excerpt(max_chars=80)
        assert "budget" in excerpt or "garage sync" in excerpt
        assert len(excerpt) <= 80

    def test_derived_tags_returns_keywords(self) -> None:
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR)
        content = reader.read_conversation("conversation-001")
        tags = content.derived_tags()
        assert isinstance(tags, list)
        assert len(tags) <= 3
