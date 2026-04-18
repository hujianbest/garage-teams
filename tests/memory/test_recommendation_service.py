"""Tests for recommendation service and context builder."""

from datetime import datetime

from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.memory.recommendation_service import (
    RecommendationContextBuilder,
    RecommendationService,
)
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord, KnowledgeEntry, KnowledgeType


def test_recommendations_include_match_reasons(tmp_path) -> None:
    """Rich context should return ranked recommendations with reasons."""
    storage = FileStorage(tmp_path)
    knowledge_store = KnowledgeStore(storage)
    experience_index = ExperienceIndex(storage)

    knowledge_store.store(
        KnowledgeEntry(
            id="decision-001",
            type=KnowledgeType.DECISION,
            topic="Workspace-first memory storage",
            date=datetime.now(),
            tags=["hf-design", "memory_pipeline", "workspace-first"],
            content="Keep candidates in workspace files.",
        )
    )

    service = RecommendationService(knowledge_store, experience_index)
    results = service.recommend(
        {
            "skill_name": "hf-design",
            "domain": "garage_os",
            "problem_domain": "memory_pipeline",
            "tags": ["workspace-first"],
            "artifact_paths": [],
        }
    )

    assert len(results) == 1
    assert results[0]["entry_id"] == "decision-001"
    assert results[0]["match_reasons"]


def test_skill_name_only_degrades_reason(tmp_path) -> None:
    """Sparse context should still work with explicit downgrade reason."""
    storage = FileStorage(tmp_path)
    knowledge_store = KnowledgeStore(storage)
    experience_index = ExperienceIndex(storage)

    knowledge_store.store(
        KnowledgeEntry(
            id="pattern-001",
            type=KnowledgeType.PATTERN,
            topic="Pattern for hf-design",
            date=datetime.now(),
            tags=["hf-design"],
            content="Use ADRs before tasks.",
        )
    )

    service = RecommendationService(knowledge_store, experience_index)
    results = service.recommend({"skill_name": "hf-design"})

    assert len(results) == 1
    assert "skill_name_only" in results[0]["match_reasons"]


def test_context_builder_uses_session_and_repo_metadata() -> None:
    """Builder should pull richer context from params/session/repo metadata."""
    builder = RecommendationContextBuilder()
    context = builder.build(
        skill_name="garage-memory",
        params={"domain": "garage_os", "tags": ["candidate-review"]},
        session_topic="F003",
        session_metadata={"problem_domain": "memory_pipeline"},
        repo_state={"branch": "main", "dirty": False},
        artifact_paths=["docs/features/F003-garage-memory-auto-extraction.md"],
    )

    assert context["skill_name"] == "garage-memory"
    assert context["domain"] == "garage_os"
    assert context["problem_domain"] == "memory_pipeline"
    assert "candidate-review" in context["tags"]
    assert context["artifact_paths"]
