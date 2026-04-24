"""F010 T3: sync pipeline idempotency tests.

Covers INV-F10-4 + NFR-1002: 第二次 sync 内容相同时 mtime 不刷新.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import pytest

from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.storage.file_storage import FileStorage
from garage_os.sync.pipeline import sync_hosts
from garage_os.types import KnowledgeEntry, KnowledgeType


def _seed_one_decision(workspace_root: Path) -> None:
    storage = FileStorage(workspace_root / ".garage")
    store = KnowledgeStore(storage)
    store.store(
        KnowledgeEntry(
            id="d-001",
            type=KnowledgeType.DECISION,
            topic="test",
            date=datetime(2026, 4, 24),
            tags=[],
            content="content",
        )
    )


class TestIdempotency:
    def test_second_sync_no_mtime_change(self, tmp_path: Path) -> None:
        _seed_one_decision(tmp_path)

        # First sync
        sync_hosts(tmp_path, ["claude"])
        claude_md = tmp_path / "CLAUDE.md"
        first_mtime = claude_md.stat().st_mtime
        first_bytes = claude_md.read_bytes()

        time.sleep(0.05)  # ensure mtime would diff if rewritten

        # Second sync (no change in knowledge base)
        sync_hosts(tmp_path, ["claude"])
        second_mtime = claude_md.stat().st_mtime
        second_bytes = claude_md.read_bytes()

        # Bytes identical
        assert first_bytes == second_bytes
        # mtime unchanged (UNCHANGED action skips disk write entirely)
        assert first_mtime == second_mtime

    def test_knowledge_change_triggers_update(self, tmp_path: Path) -> None:
        _seed_one_decision(tmp_path)
        sync_hosts(tmp_path, ["claude"])
        first_bytes = (tmp_path / "CLAUDE.md").read_bytes()

        # Add new entry → triggers UPDATE_FROM_SOURCE
        storage = FileStorage(tmp_path / ".garage")
        store = KnowledgeStore(storage)
        store.store(
            KnowledgeEntry(
                id="d-002",
                type=KnowledgeType.DECISION,
                topic="another",
                date=datetime(2026, 4, 25),
                tags=[],
                content="more content",
            )
        )

        sync_hosts(tmp_path, ["claude"])
        second_bytes = (tmp_path / "CLAUDE.md").read_bytes()

        # Marker block content updated
        assert first_bytes != second_bytes
        assert b"another" in second_bytes
