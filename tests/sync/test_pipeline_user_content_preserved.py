"""F010 T3: NFR-1003 + INV-F10-5: marker 之外用户内容字节级保留."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import pytest

from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.storage.file_storage import FileStorage
from garage_os.sync.pipeline import sync_hosts
from garage_os.types import KnowledgeEntry, KnowledgeType


def _seed_decision(workspace_root: Path, content: str = "body") -> None:
    storage = FileStorage(workspace_root / ".garage")
    store = KnowledgeStore(storage)
    store.store(
        KnowledgeEntry(
            id=f"d-{hashlib.md5(content.encode()).hexdigest()[:8]}",
            type=KnowledgeType.DECISION,
            topic="test",
            date=datetime(2026, 4, 24),
            tags=[],
            content=content,
        )
    )


class TestUserContentPreserved:
    def test_user_text_above_marker_preserved(self, tmp_path: Path) -> None:
        _seed_decision(tmp_path, content="initial")
        # First sync creates CLAUDE.md with marker block
        sync_hosts(tmp_path, ["claude"])

        # User adds prose ABOVE marker block
        claude_md = tmp_path / "CLAUDE.md"
        original = claude_md.read_text(encoding="utf-8")
        with_user_prose = "# My Project Notes\n\nSome user notes here.\n\n" + original
        claude_md.write_text(with_user_prose, encoding="utf-8")
        user_content_hash = hashlib.sha256(b"# My Project Notes\n\nSome user notes here.\n\n").hexdigest()

        # Knowledge changes → trigger UPDATE
        _seed_decision(tmp_path, content="updated content")
        sync_hosts(tmp_path, ["claude"])

        # User content above marker preserved byte-for-byte
        new_full = claude_md.read_text(encoding="utf-8")
        assert new_full.startswith("# My Project Notes\n\nSome user notes here.\n\n")
        # And the marker block content was updated
        assert "updated content" in new_full

    def test_user_text_below_marker_preserved(self, tmp_path: Path) -> None:
        _seed_decision(tmp_path, content="initial")
        sync_hosts(tmp_path, ["claude"])
        claude_md = tmp_path / "CLAUDE.md"

        # User appends content BELOW marker block
        original = claude_md.read_text(encoding="utf-8")
        with_user_below = original + "\n\n## My Footer\n\nUser footer notes\n"
        claude_md.write_text(with_user_below, encoding="utf-8")

        # Trigger UPDATE
        _seed_decision(tmp_path, content="updated")
        sync_hosts(tmp_path, ["claude"])

        new_full = claude_md.read_text(encoding="utf-8")
        # User footer preserved
        assert new_full.endswith("## My Footer\n\nUser footer notes\n")
        assert "updated" in new_full
