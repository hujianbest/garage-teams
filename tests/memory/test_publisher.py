"""Tests for publishing reviewed memory candidates."""

from datetime import datetime

import pytest

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
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
def knowledge_store(temp_storage):
    """Create a KnowledgeStore instance with temporary storage."""
    return KnowledgeStore(temp_storage)


@pytest.fixture
def experience_index(temp_storage):
    """Create an ExperienceIndex instance with temporary storage."""
    return ExperienceIndex(temp_storage)


@pytest.fixture
def publisher(candidate_store, knowledge_store, experience_index):
    """Create a publisher instance."""
    from garage_os.memory.publisher import KnowledgePublisher

    return KnowledgePublisher(
        candidate_store=candidate_store,
        knowledge_store=knowledge_store,
        experience_index=experience_index,
    )


@pytest.fixture
def confirmation_record():
    """Create a sample confirmation record."""
    return {
        "schema_version": "1",
        "batch_id": "batch-001",
        "resolution": "mixed",
        "actions": [
            {
                "candidate_id": "candidate-001",
                "action": "accept",
            }
        ],
        "resolved_at": datetime.now().isoformat(),
        "surface": "cli",
        "approver": "user",
    }


@pytest.fixture
def decision_candidate():
    """Create a decision candidate draft."""
    return {
        "schema_version": "1",
        "candidate_id": "candidate-001",
        "candidate_type": "decision",
        "session_id": "session-001",
        "source_artifacts": ["docs/designs/example.md"],
        "source_evidence_anchors": [
            {"kind": "artifact_excerpt", "ref": "docs/designs/example.md#decision"}
        ],
        "match_reasons": ["repeated_pattern:data-flow"],
        "status": "pending_review",
        "priority_score": 0.91,
        "title": "Use candidate batches",
        "summary": "Store candidates before publication.",
        "content": "Decision body",
        "tags": ["memory", "batching"],
    }


@pytest.fixture
def experience_summary_candidate():
    """Create an experience summary candidate draft."""
    return {
        "schema_version": "1",
        "candidate_id": "candidate-002",
        "candidate_type": "experience_summary",
        "session_id": "session-001",
        "source_artifacts": ["docs/designs/example.md"],
        "source_evidence_anchors": [
            {"kind": "session_metadata", "ref": "sessions/archived/session-001/session.json"}
        ],
        "match_reasons": ["skill_match:hf-design"],
        "status": "pending_review",
        "priority_score": 0.88,
        "title": "Experience summary",
        "summary": "Summarize the workflow experience.",
        "content": "Experience content",
        "task_type": "memory_pipeline",
        "skill_ids": ["hf-design"],
        "tech_stack": ["Python"],
        "domain": "garage_os",
        "problem_domain": "memory_pipeline",
        "outcome": "success",
        "duration_seconds": 120,
        "complexity": "medium",
        "recommendations": ["Keep candidate layers explicit"],
    }


class TestKnowledgePublisher:
    """Tests for publishing accepted candidates."""

    def test_detect_conflicts_returns_supersede_for_similar_knowledge(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """Similar published knowledge should produce a supersede suggestion."""
        candidate_store.store_candidate(decision_candidate)
        published = publisher._to_knowledge_entry(  # noqa: SLF001 - test helper use
            decision_candidate,
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )
        knowledge_store.store(published)

        conflict = publisher.detect_conflicts("candidate-001")

        assert conflict["strategy"] == "supersede"
        assert published.id in conflict["similar_entries"]

    def test_publish_decision_candidate_with_traceability(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        confirmation_record,
        knowledge_store,
    ) -> None:
        """Accepted decision candidates should become knowledge entries with traceability."""
        candidate_store.store_candidate(decision_candidate)
        candidate_store.store_confirmation(confirmation_record)

        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        knowledge = knowledge_store.retrieve(result["knowledge_type"], result["published_id"])
        assert knowledge is not None
        assert knowledge.front_matter["confirmation_ref"] == ".garage/memory/confirmations/batch-001.json"
        assert knowledge.front_matter["published_from_candidate"] == "candidate-001"
        assert knowledge.front_matter["source_evidence_anchor"]["kind"] == "artifact_excerpt"

    def test_publish_experience_summary_candidate_to_experience_record(
        self,
        publisher,
        candidate_store,
        experience_summary_candidate,
        confirmation_record,
        experience_index,
    ) -> None:
        """Accepted experience summary candidates should publish into experience records."""
        candidate_store.store_candidate(experience_summary_candidate)
        confirmation_record["actions"][0]["candidate_id"] = "candidate-002"
        candidate_store.store_confirmation(confirmation_record)

        result = publisher.publish_candidate(
            candidate_id="candidate-002",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        record = experience_index.retrieve(result["published_id"])
        assert record is not None
        assert record.confirmation_ref == ".garage/memory/confirmations/batch-001.json"
        assert record.published_from_candidate == "candidate-002"
        assert record.source_evidence_anchors[0]["kind"] == "session_metadata"

    def test_edit_accept_uses_edited_content(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        confirmation_record,
        knowledge_store,
    ) -> None:
        """edit_accept should publish the edited payload and preserve confirmation link."""
        candidate_store.store_candidate(decision_candidate)
        candidate_store.store_confirmation(confirmation_record)

        edited = {
            "title": "Edited title",
            "summary": "Edited summary",
            "content": "Edited decision body",
            "tags": ["memory", "edited"],
        }
        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="edit_accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
            edited_fields=edited,
        )

        knowledge = knowledge_store.retrieve(result["knowledge_type"], result["published_id"])
        assert knowledge is not None
        assert knowledge.topic == "Edited title"
        assert knowledge.content == "Edited decision body"
        assert knowledge.tags == ["memory", "edited"]
        assert knowledge.front_matter["confirmation_ref"] == ".garage/memory/confirmations/batch-001.json"

    def test_publish_supersede_records_relation_to_existing_entries(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        confirmation_record,
        knowledge_store,
    ) -> None:
        """Accepting a candidate that supersedes existing knowledge should record the relation (T6 acceptance)."""
        candidate_store.store_candidate(decision_candidate)
        candidate_store.store_confirmation(confirmation_record)

        existing_entry = publisher._to_knowledge_entry(  # noqa: SLF001 - test helper use
            {**decision_candidate, "candidate_id": "existing-001"},
            confirmation_ref="prior",
        )
        existing_entry.id = "existing-001"
        knowledge_store.store(existing_entry)

        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="accept",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        assert result["published_id"] is not None
        published = knowledge_store.retrieve(result["knowledge_type"], result["published_id"])
        assert published is not None
        assert "existing-001" in published.related_decisions

    def test_publish_abandon_skips_publication(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """abandon must skip publication regardless of candidate type (T6 acceptance)."""
        candidate_store.store_candidate(decision_candidate)

        result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="abandon",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        assert result["published_id"] is None
        assert knowledge_store.list_entries() == []

    def test_publish_abandon_skips_experience_summary(
        self,
        publisher,
        candidate_store,
        experience_summary_candidate,
        experience_index,
    ) -> None:
        """abandon must skip experience publication too."""
        candidate_store.store_candidate(experience_summary_candidate)

        result = publisher.publish_candidate(
            candidate_id="candidate-002",
            action="abandon",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        assert result["published_id"] is None
        assert experience_index.list_records() == []

    def test_reject_or_defer_does_not_publish(
        self,
        publisher,
        candidate_store,
        decision_candidate,
        knowledge_store,
    ) -> None:
        """Reject/defer actions must not publish formal data."""
        candidate_store.store_candidate(decision_candidate)

        reject_result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="reject",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )
        defer_result = publisher.publish_candidate(
            candidate_id="candidate-001",
            action="defer",
            confirmation_ref=".garage/memory/confirmations/batch-001.json",
        )

        assert reject_result["published_id"] is None
        assert defer_result["published_id"] is None
        assert knowledge_store.list_entries() == []
