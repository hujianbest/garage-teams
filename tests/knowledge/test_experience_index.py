"""
Tests for ExperienceIndex implementation.
"""

import pytest
from datetime import datetime
from pathlib import Path

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord


@pytest.fixture
def temp_storage(tmp_path):
    """Create a temporary FileStorage instance."""
    return FileStorage(tmp_path)


@pytest.fixture
def experience_index(temp_storage):
    """Create an ExperienceIndex instance with temporary storage."""
    return ExperienceIndex(temp_storage)


@pytest.fixture
def sample_record():
    """Create a sample experience record."""
    now = datetime.now()
    return ExperienceRecord(
        record_id="exp-001",
        task_type="code_generation",
        skill_ids=["python", "fastapi"],
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        domain="backend",
        problem_domain="api-development",
        outcome="success",
        duration_seconds=1800,
        complexity="medium",
        session_id="session-123",
        artifacts=["artifact-1", "artifact-2"],
        key_patterns=["layered-architecture", "dependency-injection"],
        lessons_learned=["Use async endpoints for better performance"],
        pitfalls=["Forgot to handle database connection pool"],
        recommendations=["Add connection pooling configuration"],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_record_2():
    """Create another sample experience record for testing searches."""
    now = datetime.now()
    return ExperienceRecord(
        record_id="exp-002",
        task_type="refactoring",
        skill_ids=["python", "testing"],
        tech_stack=["Python", "pytest"],
        domain="testing",
        problem_domain="unit-tests",
        outcome="success",
        duration_seconds=2400,
        complexity="low",
        session_id="session-456",
        key_patterns=["test-driven-development"],
        lessons_learned=["Write tests before implementation"],
        created_at=now,
        updated_at=now,
    )


def test_store_record(experience_index, sample_record):
    """Test storing an experience record."""
    checksum = experience_index.store(sample_record)

    # Verify checksum is returned
    assert checksum is not None
    assert len(checksum) == 64  # SHA-256 hex length

    # Verify file exists in correct location
    file_path = experience_index._storage.base_path / "experience/records/exp-001.json"
    assert file_path.exists()

    # Verify file content is valid JSON
    import json
    with file_path.open("r") as f:
        data = json.load(f)
    assert data["record_id"] == "exp-001"
    assert data["task_type"] == "code_generation"


def test_retrieve_record(experience_index, sample_record):
    """Test retrieving a stored experience record."""
    # Store the record
    experience_index.store(sample_record)

    # Retrieve it
    retrieved = experience_index.retrieve("exp-001")

    # Verify content
    assert retrieved is not None
    assert retrieved.record_id == "exp-001"
    assert retrieved.task_type == "code_generation"
    assert retrieved.skill_ids == ["python", "fastapi"]
    assert retrieved.tech_stack == ["Python", "FastAPI", "PostgreSQL"]
    assert retrieved.domain == "backend"
    assert retrieved.outcome == "success"
    assert retrieved.duration_seconds == 1800
    assert retrieved.complexity == "medium"
    assert retrieved.session_id == "session-123"
    assert retrieved.key_patterns == ["layered-architecture", "dependency-injection"]
    assert len(retrieved.lessons_learned) == 1
    assert len(retrieved.pitfalls) == 1
    assert len(retrieved.recommendations) == 1


def test_retrieve_nonexistent(experience_index):
    """Test retrieving a non-existent record returns None."""
    result = experience_index.retrieve("nonexistent")
    assert result is None


def test_search_by_task_type(experience_index, sample_record, sample_record_2):
    """Test searching records by task type."""
    # Store records
    experience_index.store(sample_record)
    experience_index.store(sample_record_2)

    # Search by task type
    results = experience_index.search(task_type="code_generation")

    # Verify results
    assert len(results) == 1
    assert results[0].record_id == "exp-001"
    assert results[0].task_type == "code_generation"


def test_search_by_domain(experience_index, sample_record, sample_record_2):
    """Test searching records by domain."""
    # Store records
    experience_index.store(sample_record)
    experience_index.store(sample_record_2)

    # Search by domain
    results = experience_index.search(domain="testing")

    # Verify results
    assert len(results) == 1
    assert results[0].record_id == "exp-002"
    assert results[0].domain == "testing"


def test_search_by_skill_ids(experience_index, sample_record, sample_record_2):
    """Test searching records by skill IDs."""
    # Store records
    experience_index.store(sample_record)
    experience_index.store(sample_record_2)

    # Search by skill ID (OR logic)
    results = experience_index.search(skill_ids=["fastapi"])

    # Verify results
    assert len(results) == 1
    assert results[0].record_id == "exp-001"
    assert "fastapi" in results[0].skill_ids


def test_search_by_skill_ids_multiple(experience_index, sample_record, sample_record_2):
    """Test searching records with multiple skill IDs (OR logic)."""
    # Store records
    experience_index.store(sample_record)
    experience_index.store(sample_record_2)

    # Both records have "python" skill
    results = experience_index.search(skill_ids=["python"])

    # Verify both records returned
    assert len(results) == 2
    record_ids = {r.record_id for r in results}
    assert record_ids == {"exp-001", "exp-002"}


def test_search_by_key_patterns(experience_index, sample_record, sample_record_2):
    """Test searching records by key patterns (AND logic)."""
    # Store records
    experience_index.store(sample_record)
    experience_index.store(sample_record_2)

    # Search by key pattern
    results = experience_index.search(key_patterns=["test-driven-development"])

    # Verify results
    assert len(results) == 1
    assert results[0].record_id == "exp-002"
    assert "test-driven-development" in results[0].key_patterns


def test_search_by_key_patterns_multiple(experience_index, sample_record):
    """Test searching with multiple key patterns (AND logic)."""
    # Store record
    experience_index.store(sample_record)

    # Search by multiple patterns (both must match)
    results = experience_index.search(
        key_patterns=["layered-architecture", "dependency-injection"]
    )

    # Verify results
    assert len(results) == 1
    assert results[0].record_id == "exp-001"


def test_search_by_key_patterns_no_match(experience_index, sample_record):
    """Test searching with key patterns that don't match returns empty list."""
    # Store record
    experience_index.store(sample_record)

    # Search by non-existent pattern
    results = experience_index.search(key_patterns=["nonexistent-pattern"])

    # Verify no results
    assert len(results) == 0


def test_search_combined_filters(experience_index, sample_record, sample_record_2):
    """Test searching with multiple filters combined."""
    # Store records
    experience_index.store(sample_record)
    experience_index.store(sample_record_2)

    # Search with multiple filters (AND logic)
    results = experience_index.search(
        task_type="code_generation",
        domain="backend",
        skill_ids=["python"],
    )

    # Verify only matching record returned
    assert len(results) == 1
    assert results[0].record_id == "exp-001"


def test_update_record(experience_index, sample_record):
    """Test updating a record updates the timestamp."""
    # Store original record
    original_time = sample_record.updated_at
    experience_index.store(sample_record)

    # Modify and update
    import time
    time.sleep(0.01)  # Small delay to ensure timestamp differs
    sample_record.outcome = "partial_success"
    checksum = experience_index.update(sample_record)

    # Verify checksum returned
    assert checksum is not None

    # Retrieve and verify timestamp updated
    retrieved = experience_index.retrieve("exp-001")
    assert retrieved.outcome == "partial_success"
    assert retrieved.updated_at > original_time


def test_delete_record(experience_index, sample_record):
    """Test deleting a record removes file and updates index."""
    # Store record
    experience_index.store(sample_record)

    # Verify file and index entry exist
    file_path = experience_index._storage.base_path / "experience/records/exp-001.json"
    assert file_path.exists()

    index = experience_index._load_index()
    assert "exp-001" in index

    # Delete record
    result = experience_index.delete("exp-001")

    # Verify deletion succeeded
    assert result is True
    assert not file_path.exists()

    # Verify removed from index
    index = experience_index._load_index()
    assert "exp-001" not in index


def test_delete_nonexistent(experience_index):
    """Test deleting a non-existent record returns False."""
    result = experience_index.delete("nonexistent")
    assert result is False


def test_list_records(experience_index, sample_record, sample_record_2):
    """Test listing all experience records."""
    # Store records
    experience_index.store(sample_record)
    experience_index.store(sample_record_2)

    # List all records
    all_records = experience_index.list_records()

    # Verify all records returned
    assert len(all_records) == 2
    record_ids = {r.record_id for r in all_records}
    assert record_ids == {"exp-001", "exp-002"}


def test_index_updated(experience_index, sample_record):
    """Test that the central index is updated when storing a record."""
    # Store record
    experience_index.store(sample_record)

    # Load index
    index = experience_index._load_index()

    # Verify record is in index
    assert "exp-001" in index
    assert index["exp-001"]["task_type"] == "code_generation"
    assert index["exp-001"]["domain"] == "backend"
    assert index["exp-001"]["skill_ids"] == ["python", "fastapi"]
    assert index["exp-001"]["outcome"] == "success"


def test_index_updated_on_delete(experience_index, sample_record):
    """Test that the central index is updated when deleting a record."""
    # Store record
    experience_index.store(sample_record)

    # Verify in index
    index = experience_index._load_index()
    assert "exp-001" in index

    # Delete record
    experience_index.delete("exp-001")

    # Verify removed from index
    index = experience_index._load_index()
    assert "exp-001" not in index


def test_record_to_dict_conversion(experience_index, sample_record):
    """Test internal record to dict conversion."""
    data = experience_index._record_to_dict(sample_record)

    # Verify all fields are included
    assert data["record_id"] == "exp-001"
    assert data["task_type"] == "code_generation"
    assert data["skill_ids"] == ["python", "fastapi"]
    assert data["tech_stack"] == ["Python", "FastAPI", "PostgreSQL"]
    assert data["domain"] == "backend"
    assert data["outcome"] == "success"
    assert data["duration_seconds"] == 1800
    assert data["complexity"] == "medium"
    assert data["session_id"] == "session-123"


def test_dict_to_record_conversion(experience_index):
    """Test internal dict to record conversion."""
    data = {
        "record_id": "test-001",
        "task_type": "testing",
        "skill_ids": ["pytest"],
        "tech_stack": ["Python"],
        "domain": "testing",
        "problem_domain": "unit-tests",
        "outcome": "success",
        "duration_seconds": 600,
        "complexity": "low",
        "session_id": "session-789",
        "artifacts": ["artifact-1"],
        "key_patterns": ["tdd"],
        "lessons_learned": ["Test first"],
        "pitfalls": ["None"],
        "recommendations": ["Add more tests"],
        "created_at": "2026-04-16T12:00:00",
        "updated_at": "2026-04-16T12:30:00",
    }

    record = experience_index._dict_to_record(data)

    # Verify conversion
    assert record.record_id == "test-001"
    assert record.task_type == "testing"
    assert record.skill_ids == ["pytest"]
    assert record.domain == "testing"
    assert record.outcome == "success"
    assert record.duration_seconds == 600


def test_matches_skill_ids(experience_index, sample_record):
    """Test skill ID matching logic (OR logic)."""
    # Single match
    assert experience_index._matches_skill_ids(sample_record, ["python"])
    assert experience_index._matches_skill_ids(sample_record, ["fastapi"])
    assert not experience_index._matches_skill_ids(sample_record, ["rust"])

    # Multiple skill IDs (OR logic - match any)
    assert experience_index._matches_skill_ids(sample_record, ["python", "rust"])
    assert experience_index._matches_skill_ids(sample_record, ["rust", "fastapi"])


def test_matches_key_patterns(experience_index, sample_record):
    """Test key pattern matching logic (AND logic)."""
    # Single pattern
    assert experience_index._matches_key_patterns(sample_record, ["layered-architecture"])
    assert not experience_index._matches_key_patterns(sample_record, ["nonexistent"])

    # Multiple patterns (AND logic - match all)
    assert experience_index._matches_key_patterns(
        sample_record, ["layered-architecture", "dependency-injection"]
    )
    assert not experience_index._matches_key_patterns(
        sample_record, ["layered-architecture", "nonexistent"]
    )


def test_parse_datetime(experience_index):
    """Test datetime parsing from various formats."""
    # ISO string
    dt = experience_index._parse_datetime("2026-04-16T12:00:00")
    assert isinstance(dt, datetime)
    assert dt.year == 2026

    # Datetime object
    now = datetime.now()
    assert experience_index._parse_datetime(now) == now

    # Invalid string returns current datetime
    invalid_dt = experience_index._parse_datetime("invalid")
    assert isinstance(invalid_dt, datetime)
