"""F010 SM-1002 round-trip e2e: import → archive → candidate → sync → host context.

Closes test-review-F010-r1 IMP-1 + traceability-review-F010-r1 MIN-2.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from garage_os.ingest.host_readers.claude_code import ClaudeCodeHistoryReader
from garage_os.ingest.pipeline import import_conversations
from garage_os.sync.pipeline import sync_hosts

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "claude_code"


class TestE2EImportThenSync:
    """SM-1002: import 1 conversation → candidate review → sync to host context.

    Note: This e2e exercises the full feedback loop without going through
    `garage memory review --action accept` (which requires user input). Instead,
    it manually publishes one candidate via KnowledgePublisher to simulate user
    approval, then verifies the resulting knowledge appears in the next sync.
    """

    def test_import_then_publish_then_sync_appears_in_host_context(
        self, tmp_path: Path
    ) -> None:
        from garage_os.knowledge.experience_index import ExperienceIndex
        from garage_os.knowledge.knowledge_store import KnowledgeStore
        from garage_os.memory.candidate_store import CandidateStore
        from garage_os.memory.publisher import KnowledgePublisher
        from garage_os.storage.file_storage import FileStorage

        # Step 1: import a conversation (uses fixture)
        reader = ClaudeCodeHistoryReader(history_dir=FIXTURE_DIR, stderr=io.StringIO())
        import_summary = import_conversations(
            tmp_path,
            "claude-code",
            ["conversation-001"],
            reader=reader,
            stderr=io.StringIO(),
        )
        assert import_summary.imported == 1
        assert import_summary.batch_id is not None

        # Step 2: publish 1 candidate via KnowledgePublisher (simulate user accept via memory review)
        storage = FileStorage(tmp_path / ".garage")
        candidate_store = CandidateStore(storage)
        knowledge_store = KnowledgeStore(storage)
        experience_index = ExperienceIndex(storage)
        publisher = KnowledgePublisher(candidate_store, knowledge_store, experience_index)

        batch = candidate_store.retrieve_batch(import_summary.batch_id)
        assert batch is not None and batch["candidate_ids"]
        first_candidate_id = batch["candidate_ids"][0]
        confirmation_ref = f".garage/memory/candidates/confirmations/{import_summary.batch_id}.json"

        publish_result = publisher.publish_candidate(
            candidate_id=first_candidate_id,
            action="accept",
            confirmation_ref=confirmation_ref,
        )
        # Verify candidate published (publisher returns published_id + action)
        assert publish_result.get("action") == "accept"
        assert publish_result.get("published_id") is not None

        # Step 3: garage sync — newly published candidate should appear in CLAUDE.md
        # (Publisher may produce KnowledgeEntry OR ExperienceRecord depending on
        # candidate type heuristics; both are valid SM-1002 round-trip outcomes.)
        sync_summary = sync_hosts(tmp_path, ["claude"])
        total_synced = sync_summary.knowledge_count + sync_summary.experience_count
        assert total_synced > 0, (
            "SM-1002 e2e: after publishing imported candidate, sync should pick up "
            "either a knowledge entry or an experience record. "
            f"sync_summary={sync_summary}"
        )

        # Step 4: verify CLAUDE.md content
        claude_md = tmp_path / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text(encoding="utf-8")
        # Garage marker block present
        assert "## Garage Knowledge Context" in content
        assert "<!-- garage:context-begin -->" in content
        assert "<!-- garage:context-end -->" in content
        # At least one Recent ... section emitted (knowledge OR experience)
        assert "Recent " in content
