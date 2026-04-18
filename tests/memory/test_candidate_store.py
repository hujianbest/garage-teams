"""Tests for memory candidate storage contracts."""

from datetime import datetime

import pytest

from garage_os.storage.file_storage import FileStorage


@pytest.fixture
def temp_storage(tmp_path):
    """Create a temporary FileStorage instance."""
    return FileStorage(tmp_path)


@pytest.fixture
def candidate_store(temp_storage):
    """Create a CandidateStore instance with temporary storage."""
    from garage_os.memory.candidate_store import CandidateStore

    return CandidateStore(temp_storage)


@pytest.fixture
def sample_batch():
    """Create a sample candidate batch payload."""
    now = datetime.now().isoformat()
    return {
        "batch_id": "batch-001",
        "session_id": "session-001",
        "status": "pending_review",
        "trigger": "session_archived",
        "candidate_ids": ["candidate-001", "candidate-002"],
        "truncated_count": 0,
        "evaluation_summary": "evaluated_with_candidates",
        "created_at": now,
    }


@pytest.fixture
def sample_candidate():
    """Create a sample candidate draft payload."""
    return {
        "schema_version": "1",
        "candidate_id": "candidate-001",
        "candidate_type": "decision",
        "session_id": "session-001",
        "source_artifacts": [
            "docs/designs/2026-04-18-garage-memory-auto-extraction-design.md"
        ],
        "match_reasons": ["repeated_pattern:data-flow"],
        "status": "pending_review",
        "priority_score": 0.92,
        "title": "Use explicit candidate batches",
        "summary": "Store extracted candidates separately from published knowledge.",
        "content": "Candidate body",
    }


class TestCandidateStore:
    """Test candidate storage contract for T1."""

    def test_store_batch_and_candidate_round_trip(
        self,
        candidate_store,
        sample_batch,
        sample_candidate,
    ) -> None:
        """Store and retrieve one batch with two candidates."""
        candidate_store.store_candidate(sample_candidate)
        second_candidate = dict(sample_candidate)
        second_candidate["candidate_id"] = "candidate-002"
        second_candidate["title"] = "Keep confirmation records"
        candidate_store.store_candidate(second_candidate)

        checksum = candidate_store.store_batch(sample_batch)

        assert isinstance(checksum, str)
        assert len(checksum) == 64

        retrieved_batch = candidate_store.retrieve_batch("batch-001")
        assert retrieved_batch is not None
        assert retrieved_batch["candidate_ids"] == ["candidate-001", "candidate-002"]

        retrieved_candidate = candidate_store.retrieve_candidate("candidate-001")
        assert retrieved_candidate is not None
        assert retrieved_candidate["candidate_type"] == "decision"
        assert retrieved_candidate["title"] == "Use explicit candidate batches"

    def test_reject_invalid_candidate_type(
        self,
        candidate_store,
        sample_candidate,
    ) -> None:
        """Candidate type must be one of the four supported values."""
        invalid_candidate = dict(sample_candidate)
        invalid_candidate["candidate_type"] = "note"

        with pytest.raises(ValueError, match="candidate_type"):
            candidate_store.store_candidate(invalid_candidate)

    def test_reject_batch_over_pending_limit(
        self,
        candidate_store,
        sample_batch,
        sample_candidate,
    ) -> None:
        """Pending-review batches must not exceed the limit of five candidates."""
        candidate_ids = []
        for idx in range(6):
            candidate = dict(sample_candidate)
            candidate_id = f"candidate-{idx:03d}"
            candidate["candidate_id"] = candidate_id
            candidate["title"] = f"Candidate {idx}"
            candidate_store.store_candidate(candidate)
            candidate_ids.append(candidate_id)

        oversized_batch = dict(sample_batch)
        oversized_batch["candidate_ids"] = candidate_ids

        with pytest.raises(ValueError, match="at most 5"):
            candidate_store.store_batch(oversized_batch)

    def test_reject_candidate_missing_required_metadata(
        self,
        candidate_store,
        sample_candidate,
    ) -> None:
        """Candidates missing FR-302b mandatory metadata must be rejected before storage."""
        missing_session = {k: v for k, v in sample_candidate.items() if k != "session_id"}
        with pytest.raises(ValueError, match="session_id"):
            candidate_store.store_candidate(missing_session)

        missing_artifacts = dict(sample_candidate)
        missing_artifacts["candidate_id"] = "candidate-002"
        missing_artifacts["source_artifacts"] = []
        with pytest.raises(ValueError, match="source_artifacts"):
            candidate_store.store_candidate(missing_artifacts)

    def test_store_and_retrieve_confirmation_record(
        self,
        candidate_store,
    ) -> None:
        """Confirmation records should round-trip through JSON storage."""
        confirmation = {
            "schema_version": "1",
            "batch_id": "batch-001",
            "resolution": "mixed",
            "actions": [
                {"candidate_id": "candidate-001", "action": "accept"},
                {"candidate_id": "candidate-002", "action": "reject"},
            ],
            "resolved_at": datetime.now().isoformat(),
            "surface": "cli",
            "approver": "user",
        }

        checksum = candidate_store.store_confirmation(confirmation)

        assert isinstance(checksum, str)
        assert len(checksum) == 64

        retrieved = candidate_store.retrieve_confirmation("batch-001")
        assert retrieved is not None
        assert retrieved["resolution"] == "mixed"
        assert len(retrieved["actions"]) == 2
