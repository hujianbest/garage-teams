"""F010 T6: ingest pipeline → archive_session → F003 candidate path test.

Covers INV-F10-7 + ADR-D10-7 + ADR-D10-9 r2.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from garage_os.ingest.host_readers.claude_code import ClaudeCodeHistoryReader
from garage_os.ingest.pipeline import import_conversations

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "claude_code"


class TestIngestCandidatePath:
    """ADR-D10-7 + INV-F10-7: import → archive → candidate入 .garage/memory/candidates/items/."""

    def test_import_creates_session_and_candidate(
        self, tmp_path: Path
    ) -> None:
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR, stderr=io.StringIO())
        summary = import_conversations(
            tmp_path,
            "claude-code",
            ["conversation-001"],
            reader=reader,
        )
        # Session imported
        assert summary.imported == 1
        assert summary.skipped == 0
        # Archived session created (F003 既有路径)
        archived_dir = tmp_path / ".garage" / "sessions" / "archived"
        assert archived_dir.is_dir()
        sessions = list(archived_dir.iterdir())
        assert len(sessions) == 1
        # Candidate items + batches under .garage/memory/candidates/ (F003/F004 既有路径, INV-F10-7)
        candidates_items = tmp_path / ".garage" / "memory" / "candidates" / "items"
        candidates_batches = tmp_path / ".garage" / "memory" / "candidates" / "batches"
        # At least one must exist (depending on ExtractionOrchestrator outcome)
        # ADR-D10-9 r2 signal-fill: tags + problem_domain hit strong signals → batch
        # generated even if items count is 0 (would be no_evidence batch otherwise)
        assert candidates_batches.is_dir()
        assert summary.batch_id is not None

    def test_import_partial_failure_continues(self, tmp_path: Path) -> None:
        """FR-1006 negative path: 1 broken + 1 valid → partial success."""
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR, stderr=io.StringIO())
        summary = import_conversations(
            tmp_path,
            "claude-code",
            ["conversation-001", "conversation-002-broken"],
            reader=reader,
            stderr=io.StringIO(),
        )
        assert summary.imported == 1
        assert summary.skipped == 1


class TestSessionProvenanceViaMetadata:
    """ADR-D10-7 + INV-F10-8: SessionContext.metadata.imported_from set correctly.

    CON-1002 守门: F003-F006 dataclass 0 改动 (利用既有 metadata dict).
    """

    def test_imported_from_in_session_metadata(self, tmp_path: Path) -> None:
        import json

        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR, stderr=io.StringIO())
        import_conversations(
            tmp_path,
            "claude-code",
            ["conversation-001"],
            reader=reader,
        )

        # Inspect archived session.json
        archived_dir = tmp_path / ".garage" / "sessions" / "archived"
        session_dirs = list(archived_dir.iterdir())
        assert len(session_dirs) == 1
        session_json = session_dirs[0] / "session.json"
        data = json.loads(session_json.read_text(encoding="utf-8"))
        # SessionContext.metadata.imported_from = "claude-code:<conversation_id>"
        ctx_meta = data.get("context", {}).get("metadata", {})
        assert ctx_meta.get("imported_from") == "claude-code:conversation-001"
        # ADR-D10-9 r2 signal-fill: tags + problem_domain present
        assert "tags" in ctx_meta
        assert isinstance(ctx_meta["tags"], list)
        assert "ingested" in ctx_meta["tags"]
        assert "problem_domain" in ctx_meta
