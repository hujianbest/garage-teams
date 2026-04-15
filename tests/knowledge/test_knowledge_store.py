"""
Tests for KnowledgeStore implementation.
"""

import pytest
from datetime import datetime
from pathlib import Path

from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.storage.file_storage import FileStorage
from garage_os.types import KnowledgeType, KnowledgeEntry


@pytest.fixture
def temp_storage(tmp_path):
    """Create a temporary FileStorage instance."""
    return FileStorage(tmp_path)


@pytest.fixture
def knowledge_store(temp_storage):
    """Create a KnowledgeStore instance with temporary storage."""
    return KnowledgeStore(temp_storage)


@pytest.fixture
def sample_decision():
    """Create a sample decision knowledge entry."""
    return KnowledgeEntry(
        id="decision-001",
        type=KnowledgeType.DECISION,
        topic="Use SQLAlchemy for ORM",
        date=datetime.now(),
        tags=["database", "orm", "sqlalchemy"],
        content="# Decision\n\nWe decided to use SQLAlchemy for the ORM layer.",
        status="active",
        version=1,
        related_decisions=[],
        related_tasks=["T1"],
        source_session="session-123",
    )


@pytest.fixture
def sample_pattern():
    """Create a sample pattern knowledge entry."""
    return KnowledgeEntry(
        id="pattern-001",
        type=KnowledgeType.PATTERN,
        topic="Repository Pattern",
        date=datetime.now(),
        tags=["architecture", "design-pattern"],
        content="# Repository Pattern\n\nSeparate data access logic from business logic.",
        status="active",
        version=1,
    )


@pytest.fixture
def sample_solution():
    """Create a sample solution knowledge entry."""
    return KnowledgeEntry(
        id="solution-001",
        type=KnowledgeType.SOLUTION,
        topic="Authentication Flow",
        date=datetime.now(),
        tags=["security", "auth"],
        content="# Authentication Flow\n\nImplement JWT-based authentication.",
        status="active",
        version=1,
    )


def test_store_decision(knowledge_store, sample_decision):
    """Test storing a decision type entry."""
    checksum = knowledge_store.store(sample_decision)

    # Verify checksum is returned
    assert checksum is not None
    assert len(checksum) == 64  # SHA-256 hex length

    # Verify file exists in correct directory
    file_path = knowledge_store._storage.base_path / "knowledge/decisions/decision-decision-001.md"
    assert file_path.exists()

    # Verify file content has front matter
    content = file_path.read_text()
    assert "---" in content
    assert "Use SQLAlchemy for ORM" in content


def test_store_pattern(knowledge_store, sample_pattern):
    """Test storing a pattern type entry."""
    checksum = knowledge_store.store(sample_pattern)

    # Verify checksum is returned
    assert checksum is not None

    # Verify file exists in correct directory
    file_path = knowledge_store._storage.base_path / "knowledge/patterns/pattern-pattern-001.md"
    assert file_path.exists()


def test_store_solution(knowledge_store, sample_solution):
    """Test storing a solution type entry."""
    checksum = knowledge_store.store(sample_solution)

    # Verify checksum is returned
    assert checksum is not None

    # Verify file exists in correct directory
    file_path = knowledge_store._storage.base_path / "knowledge/solutions/solution-solution-001.md"
    assert file_path.exists()


def test_retrieve(knowledge_store, sample_decision):
    """Test retrieving a stored knowledge entry."""
    # Store the entry
    knowledge_store.store(sample_decision)

    # Retrieve it
    retrieved = knowledge_store.retrieve(KnowledgeType.DECISION, "decision-001")

    # Verify content
    assert retrieved is not None
    assert retrieved.id == "decision-001"
    assert retrieved.type == KnowledgeType.DECISION
    assert retrieved.topic == "Use SQLAlchemy for ORM"
    assert retrieved.tags == ["database", "orm", "sqlalchemy"]
    assert "SQLAlchemy" in retrieved.content
    assert retrieved.status == "active"
    assert retrieved.version == 1
    assert retrieved.source_session == "session-123"


def test_retrieve_nonexistent(knowledge_store):
    """Test retrieving a non-existent entry returns None."""
    result = knowledge_store.retrieve(KnowledgeType.DECISION, "nonexistent")
    assert result is None


def test_search_by_tags(knowledge_store, sample_decision, sample_pattern):
    """Test searching entries by tags."""
    # Store entries
    knowledge_store.store(sample_decision)
    knowledge_store.store(sample_pattern)

    # Search by tag
    results = knowledge_store.search(tags=["database"])

    # Verify results
    assert len(results) == 1
    assert results[0].id == "decision-001"
    assert "database" in results[0].tags


def test_search_by_type(knowledge_store, sample_decision, sample_pattern):
    """Test searching entries by type."""
    # Store entries
    knowledge_store.store(sample_decision)
    knowledge_store.store(sample_pattern)

    # Search by type
    results = knowledge_store.search(knowledge_type=KnowledgeType.PATTERN)

    # Verify results
    assert len(results) == 1
    assert results[0].type == KnowledgeType.PATTERN
    assert results[0].id == "pattern-001"


def test_search_by_query(knowledge_store, sample_decision, sample_pattern):
    """Test searching entries by text query."""
    # Store entries
    knowledge_store.store(sample_decision)
    knowledge_store.store(sample_pattern)

    # Search by query in topic
    results = knowledge_store.search(query="Repository")

    # Verify results
    assert len(results) == 1
    assert results[0].id == "pattern-001"
    assert "Repository" in results[0].topic


def test_update(knowledge_store, sample_decision):
    """Test updating a knowledge entry increments version."""
    # Store original entry
    knowledge_store.store(sample_decision)

    # Update with new content
    sample_decision.content = "# Updated Decision\n\nNew content here."
    sample_decision.version = 1  # Will be incremented to 2

    checksum = knowledge_store.update(sample_decision)

    # Verify checksum returned
    assert checksum is not None

    # Retrieve and verify version incremented
    retrieved = knowledge_store.retrieve(KnowledgeType.DECISION, "decision-001")
    assert retrieved.version == 2
    assert "New content here" in retrieved.content


def test_delete(knowledge_store, sample_decision):
    """Test deleting a knowledge entry."""
    # Store entry
    knowledge_store.store(sample_decision)

    # Verify file exists
    file_path = knowledge_store._storage.base_path / "knowledge/decisions/decision-decision-001.md"
    assert file_path.exists()

    # Delete entry
    result = knowledge_store.delete(KnowledgeType.DECISION, "decision-001")

    # Verify deletion succeeded
    assert result is True
    assert not file_path.exists()


def test_delete_nonexistent(knowledge_store):
    """Test deleting a non-existent entry returns False."""
    result = knowledge_store.delete(KnowledgeType.DECISION, "nonexistent")
    assert result is False


def test_list_entries(knowledge_store, sample_decision, sample_pattern, sample_solution):
    """Test listing all knowledge entries."""
    # Store entries
    knowledge_store.store(sample_decision)
    knowledge_store.store(sample_pattern)
    knowledge_store.store(sample_solution)

    # List all entries
    all_entries = knowledge_store.list_entries()

    # Verify all entries are returned
    assert len(all_entries) == 3
    entry_ids = {e.id for e in all_entries}
    assert entry_ids == {"decision-001", "pattern-001", "solution-001"}


def test_list_entries_by_type(knowledge_store, sample_decision, sample_pattern):
    """Test listing entries filtered by type."""
    # Store entries
    knowledge_store.store(sample_decision)
    knowledge_store.store(sample_pattern)

    # List only decisions
    decisions = knowledge_store.list_entries(knowledge_type=KnowledgeType.DECISION)

    # Verify only decisions returned
    assert len(decisions) == 1
    assert decisions[0].type == KnowledgeType.DECISION


def test_invalid_type_raises_error(knowledge_store):
    """Test that invalid type raises appropriate error."""
    entry = KnowledgeEntry(
        id="test-001",
        type=KnowledgeType.DECISION,
        topic="Test",
        date=datetime.now(),
        tags=[],
        content="Test content",
    )

    # This should work fine
    knowledge_store.store(entry)

    # Verify we can retrieve it
    retrieved = knowledge_store.retrieve(KnowledgeType.DECISION, "test-001")
    assert retrieved is not None


def test_entry_to_front_matter_conversion(knowledge_store, sample_decision):
    """Test internal entry to front matter conversion."""
    fm = knowledge_store._entry_to_front_matter(sample_decision)

    # Verify all fields are included
    assert fm["id"] == "decision-001"
    assert fm["type"] == "decision"
    assert fm["topic"] == "Use SQLAlchemy for ORM"
    assert fm["tags"] == ["database", "orm", "sqlalchemy"]
    assert fm["status"] == "active"
    assert fm["version"] == 1
    assert fm["source_session"] == "session-123"


def test_front_matter_to_entry_conversion(knowledge_store):
    """Test internal front matter to entry conversion."""
    fm = {
        "id": "test-001",
        "type": "solution",
        "topic": "Test Topic",
        "date": "2026-04-16T12:00:00",
        "tags": ["test", "sample"],
        "status": "active",
        "version": 2,
        "related_decisions": ["d1"],
        "related_tasks": ["t1"],
    }
    body = "# Test Content\n\nThis is test content."

    entry = knowledge_store._front_matter_to_entry(fm, body)

    # Verify conversion
    assert entry.id == "test-001"
    assert entry.type == KnowledgeType.SOLUTION
    assert entry.topic == "Test Topic"
    assert entry.tags == ["test", "sample"]
    assert entry.status == "active"
    assert entry.version == 2
    assert entry.content == body
    assert entry.related_decisions == ["d1"]
    assert entry.related_tasks == ["t1"]
