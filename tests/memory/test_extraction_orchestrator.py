"""Tests for memory extraction orchestration."""

from datetime import datetime

import pytest

from garage_os.memory.candidate_store import CandidateStore
from garage_os.storage.file_storage import FileStorage


@pytest.fixture
def temp_storage(tmp_path):
    """Create a temporary FileStorage instance."""
    return FileStorage(tmp_path)


@pytest.fixture
def candidate_store(temp_storage):
    """Create a CandidateStore instance with temporary storage."""
    return CandidateStore(temp_storage)


@pytest.fixture
def archived_session_payload():
    """Create a minimal archived session payload."""
    now = datetime.now().isoformat()
    return {
        "session_id": "session-001",
        "pack_id": "hf-design",
        "topic": "F003 design",
        "state": "completed",
        "current_node_id": None,
        "created_at": now,
        "updated_at": now,
        "context": {
            "pack_id": "hf-design",
            "topic": "F003 design",
            "graph_variant_id": None,
            "user_goals": [],
            "constraints": [],
            "metadata": {"problem_domain": "memory-pipeline", "tags": ["workspace-first"]},
        },
        "artifacts": [
            {
                "path": "docs/designs/2026-04-18-garage-memory-auto-extraction-design.md",
                "status": "approved",
            }
        ],
        "host": "claude-code",
        "host_version": "unknown",
        "garage_version": "0.1.0",
    }


class TestExtractionOrchestrator:
    """Test T2/T3 extraction orchestration."""

    def test_extract_generates_candidate_batch(
        self,
        temp_storage,
        candidate_store,
        archived_session_payload,
    ) -> None:
        """Valid evidence should produce a batch with at least one candidate."""
        from garage_os.memory.extraction_orchestrator import (
            ExtractionConfig,
            MemoryExtractionOrchestrator,
        )

        orchestrator = MemoryExtractionOrchestrator(temp_storage, candidate_store, ExtractionConfig())

        summary = orchestrator.extract_for_archived_session(archived_session_payload)

        assert summary["evaluation_summary"] == "evaluated_with_candidates"
        assert summary["batch_id"].startswith("batch-")
        stored_batch = candidate_store.retrieve_batch(summary["batch_id"])
        assert stored_batch is not None
        assert len(stored_batch["candidate_ids"]) >= 1

    def test_extract_records_no_evidence(self, temp_storage, candidate_store) -> None:
        """Missing evidence should produce a no_evidence batch."""
        from garage_os.memory.extraction_orchestrator import (
            ExtractionConfig,
            MemoryExtractionOrchestrator,
        )

        orchestrator = MemoryExtractionOrchestrator(temp_storage, candidate_store, ExtractionConfig())

        summary = orchestrator.extract_for_archived_session(
            {
                "session_id": "session-002",
                "pack_id": "hf-design",
                "topic": "Empty session",
                "context": {"metadata": {}},
                "artifacts": [],
            }
        )

        assert summary["evaluation_summary"] == "no_evidence"
        stored_batch = candidate_store.retrieve_batch(summary["batch_id"])
        assert stored_batch is not None
        assert stored_batch["candidate_ids"] == []

    def test_extract_records_evaluated_no_candidate(
        self,
        temp_storage,
        candidate_store,
        archived_session_payload,
    ) -> None:
        """Explicitly filtered candidates should produce evaluated_no_candidate."""
        from garage_os.memory.extraction_orchestrator import (
            ExtractionConfig,
            MemoryExtractionOrchestrator,
        )

        config = ExtractionConfig(min_priority_score=0.99)
        orchestrator = MemoryExtractionOrchestrator(temp_storage, candidate_store, config)

        summary = orchestrator.extract_for_archived_session(archived_session_payload)

        assert summary["evaluation_summary"] == "evaluated_no_candidate"
        stored_batch = candidate_store.retrieve_batch(summary["batch_id"])
        assert stored_batch is not None
        assert stored_batch["candidate_ids"] == []
