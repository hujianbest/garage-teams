"""Tests for SessionManager."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from garage_os.runtime.session_manager import SessionManager
from garage_os.storage import FileStorage
from garage_os.types import SessionState


@pytest.fixture
def storage(tmp_path: Path):
    """Create a FileStorage instance for testing."""
    return FileStorage(tmp_path)


@pytest.fixture
def session_manager(storage: FileStorage):
    """Create a SessionManager instance for testing."""
    return SessionManager(storage)


def test_create_session(session_manager: SessionManager, tmp_path: Path):
    """Test creating a new session."""
    metadata = session_manager.create_session(
        pack_id="test-pack",
        topic="Test topic",
        user_goals=["goal1", "goal2"],
        constraints=["constraint1"],
    )

    # Check session ID format
    assert metadata.session_id.startswith("session-")
    assert metadata.pack_id == "test-pack"
    assert metadata.topic == "Test topic"
    assert metadata.state == SessionState.IDLE
    assert metadata.current_node_id is None

    # Check context
    assert metadata.context.pack_id == "test-pack"
    assert metadata.context.topic == "Test topic"
    assert metadata.context.user_goals == ["goal1", "goal2"]
    assert metadata.context.constraints == ["constraint1"]

    # Check session.json exists
    session_file = tmp_path / "sessions" / "active" / metadata.session_id / "session.json"
    assert session_file.exists()

    # Check session.json format
    data = json.loads(session_file.read_text())
    assert data["session_id"] == metadata.session_id
    assert data["pack_id"] == "test-pack"
    assert data["topic"] == "Test topic"
    assert data["state"] == "idle"
    assert data["current_node_id"] is None
    assert "created_at" in data
    assert "updated_at" in data
    assert "checksum" in data


def test_create_session_increments_id(session_manager: SessionManager, tmp_path: Path):
    """Test that consecutive session IDs increment."""
    session1 = session_manager.create_session("pack-1", "topic-1")
    session2 = session_manager.create_session("pack-2", "topic-2")
    session3 = session_manager.create_session("pack-3", "topic-3")

    # Extract sequence numbers
    import re

    pattern = re.compile(r"session-(\d+)-(\d+)")
    match1 = pattern.match(session1.session_id)
    match2 = pattern.match(session2.session_id)
    match3 = pattern.match(session3.session_id)

    assert match1 and match2 and match3

    # Same date part
    date1, seq1 = match1.group(1), int(match1.group(2))
    date2, seq2 = match2.group(1), int(match2.group(2))
    date3, seq3 = match3.group(1), int(match3.group(2))

    assert date1 == date2 == date3
    assert seq1 == 1
    assert seq2 == 2
    assert seq3 == 3


def test_create_session_increments_after_archive(
    session_manager: SessionManager, tmp_path: Path
):
    """Archived sessions should still count toward the next session sequence."""
    session1 = session_manager.create_session("pack-1", "topic-1")
    archived = session_manager.archive_session(session1.session_id)

    assert archived is True

    session2 = session_manager.create_session("pack-2", "topic-2")

    assert session2.session_id.endswith("-002")


def test_restore_session(session_manager: SessionManager):
    """Test restoring an existing session."""
    # Create a session
    created = session_manager.create_session(
        pack_id="test-pack",
        topic="Test topic",
        user_goals=["goal1"],
        constraints=["constraint1"],
    )

    # Restore the session
    restored = session_manager.restore_session(created.session_id)

    assert restored is not None
    assert restored.session_id == created.session_id
    assert restored.pack_id == created.pack_id
    assert restored.topic == created.topic
    assert restored.state == created.state
    assert restored.current_node_id == created.current_node_id
    assert restored.context.pack_id == created.context.pack_id
    assert restored.context.topic == created.context.topic
    assert restored.context.user_goals == created.context.user_goals
    assert restored.context.constraints == created.context.constraints


def test_restore_nonexistent(session_manager: SessionManager):
    """Test restoring a nonexistent session returns None."""
    restored = session_manager.restore_session("session-doesnotexist-001")
    assert restored is None


def test_update_session_state(session_manager: SessionManager, tmp_path: Path):
    """Test updating session state."""
    metadata = session_manager.create_session("test-pack", "Test topic")
    session_file = (
        tmp_path / "sessions" / "active" / metadata.session_id / "session.json"
    )

    # Update state
    updated = session_manager.update_session(
        metadata.session_id, state=SessionState.RUNNING
    )

    assert updated is not None
    assert updated.state == SessionState.RUNNING

    # Verify file was updated
    data = json.loads(session_file.read_text())
    assert data["state"] == "running"


def test_update_session_node(session_manager: SessionManager, tmp_path: Path):
    """Test updating current node ID."""
    metadata = session_manager.create_session("test-pack", "Test topic")
    session_file = (
        tmp_path / "sessions" / "active" / metadata.session_id / "session.json"
    )

    # Update node
    updated = session_manager.update_session(
        metadata.session_id, current_node_id="node-123"
    )

    assert updated is not None
    assert updated.current_node_id == "node-123"

    # Verify file was updated
    data = json.loads(session_file.read_text())
    assert data["current_node_id"] == "node-123"


def test_archive_session(session_manager: SessionManager, tmp_path: Path):
    """Test archiving a session."""
    metadata = session_manager.create_session("test-pack", "Test topic")
    session_id = metadata.session_id

    active_dir = tmp_path / "sessions" / "active" / session_id
    archived_dir = tmp_path / "sessions" / "archived" / session_id

    # Archive
    result = session_manager.archive_session(session_id)

    assert result is True

    # Active session should be removed
    assert not active_dir.exists()

    # Archived session should exist
    assert archived_dir.exists()
    assert (archived_dir / "session.json").exists()
    assert (archived_dir / "archive.json").exists()

    # Check archive.json format
    archive_data = json.loads((archived_dir / "archive.json").read_text())
    assert archive_data["session_id"] == session_id
    assert "archived_at" in archive_data
    assert archive_data["reason"] == "session_archived"


def test_archive_session_creates_memory_batch_when_enabled(
    session_manager: SessionManager,
    tmp_path: Path,
):
    """Archiving a completed session should trigger memory extraction when enabled."""
    metadata = session_manager.create_session("test-pack", "Memory topic")
    session_id = metadata.session_id
    session_manager.update_session(
        session_id,
        current_node_id="node-123",
    )

    platform_config = tmp_path / "config" / "platform.json"
    platform_config.parent.mkdir(parents=True, exist_ok=True)
    platform_config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "memory": {
                    "extraction_enabled": True,
                    "recommendation_enabled": False,
                },
            }
        ),
        encoding="utf-8",
    )

    active_session_file = tmp_path / "sessions" / "active" / session_id / "session.json"
    data = json.loads(active_session_file.read_text(encoding="utf-8"))
    data["context"]["metadata"] = {
        "problem_domain": "memory_pipeline",
        "tags": ["workspace-first"],
    }
    data["artifacts"] = [
        {
            "path": "docs/designs/2026-04-18-garage-memory-auto-extraction-design.md",
            "status": "approved",
        }
    ]
    active_session_file.write_text(json.dumps(data), encoding="utf-8")

    result = session_manager.archive_session(session_id)

    assert result is True
    batch_files = list((tmp_path / "memory" / "candidates" / "batches").glob("*.json"))
    assert len(batch_files) == 1
    batch_data = json.loads(batch_files[0].read_text(encoding="utf-8"))
    assert batch_data["evaluation_summary"] == "evaluated_with_candidates"


def test_archive_session_ignores_memory_errors(
    session_manager: SessionManager,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Memory extraction failures should not block archive_session."""
    metadata = session_manager.create_session("test-pack", "Error topic")
    session_id = metadata.session_id

    platform_config = tmp_path / "config" / "platform.json"
    platform_config.parent.mkdir(parents=True, exist_ok=True)
    platform_config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "memory": {
                    "extraction_enabled": True,
                    "recommendation_enabled": False,
                },
            }
        ),
        encoding="utf-8",
    )

    def _boom(*args, **kwargs):
        raise RuntimeError("memory exploded")

    monkeypatch.setattr(
        "garage_os.runtime.session_manager.MemoryExtractionOrchestrator.extract_for_archived_session",
        _boom,
    )

    result = session_manager.archive_session(session_id)

    assert result is True
    archived_dir = tmp_path / "sessions" / "archived" / session_id
    assert archived_dir.exists()


def test_archive_nonexistent(session_manager: SessionManager):
    """Test archiving a nonexistent session returns False."""
    result = session_manager.archive_session("session-doesnotexist-001")
    assert result is False


def test_list_active_sessions(session_manager: SessionManager):
    """Test listing all active sessions."""
    # Create multiple sessions
    session1 = session_manager.create_session("pack-1", "Topic 1")
    session2 = session_manager.create_session("pack-2", "Topic 2")
    session3 = session_manager.create_session("pack-3", "Topic 3")

    # List active sessions
    sessions = session_manager.list_active_sessions()

    assert len(sessions) == 3
    session_ids = {s.session_id for s in sessions}
    assert session_ids == {session1.session_id, session2.session_id, session3.session_id}


def test_create_checkpoint(session_manager: SessionManager, tmp_path: Path):
    """Test creating a checkpoint."""
    metadata = session_manager.create_session("test-pack", "Test topic")

    state_snapshot = {"counter": 42, "status": "ok", "data": [1, 2, 3]}
    checkpoint = session_manager.create_checkpoint(
        metadata.session_id, "node-abc", state_snapshot
    )

    # Check checkpoint object
    assert checkpoint.checkpoint_id.startswith("cp-")
    assert checkpoint.node_id == "node-abc"
    assert checkpoint.state_snapshot == state_snapshot
    assert checkpoint.checksum is not None

    # Check checkpoint file exists
    checkpoint_file = (
        tmp_path
        / "sessions"
        / "active"
        / metadata.session_id
        / "checkpoints"
        / f"{checkpoint.checkpoint_id}.json"
    )
    assert checkpoint_file.exists()

    # Check checkpoint file content
    data = json.loads(checkpoint_file.read_text())
    assert data["checkpoint_id"] == checkpoint.checkpoint_id
    assert data["node_id"] == "node-abc"
    assert data["state_snapshot"] == state_snapshot
    assert "timestamp" in data


def test_session_json_format(session_manager: SessionManager, tmp_path: Path):
    """Test that session.json contains all required fields."""
    metadata = session_manager.create_session(
        pack_id="test-pack",
        topic="Test topic",
        user_goals=["goal1"],
        constraints=["constraint1"],
    )

    session_file = (
        tmp_path / "sessions" / "active" / metadata.session_id / "session.json"
    )
    data = json.loads(session_file.read_text())

    # Required top-level fields
    assert "session_id" in data
    assert "pack_id" in data
    assert "topic" in data
    assert "state" in data
    assert "current_node_id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "context" in data
    assert "artifacts" in data
    assert "host" in data
    assert "host_version" in data
    assert "garage_version" in data

    # Required context fields
    context = data["context"]
    assert "pack_id" in context
    assert "topic" in context
    assert "graph_variant_id" in context
    assert "user_goals" in context
    assert "constraints" in context
    assert "metadata" in context


def test_session_checksum(session_manager: SessionManager, tmp_path: Path):
    """Test that session.json contains a checksum field."""
    metadata = session_manager.create_session("test-pack", "Test topic")

    session_file = (
        tmp_path / "sessions" / "active" / metadata.session_id / "session.json"
    )
    content = session_file.read_text()
    data = json.loads(content)

    # Checksum exists in the data
    assert "checksum" in data
    assert isinstance(data["checksum"], str)
    assert len(data["checksum"]) == 64  # SHA-256 hex length


def test_archive_expired_sessions(session_manager: SessionManager, tmp_path: Path):
    """Test archiving sessions that have exceeded the timeout period."""
    from datetime import timedelta

    # Create a session
    metadata = session_manager.create_session("test-pack", "Test topic")
    session_id = metadata.session_id

    active_dir = tmp_path / "sessions" / "active" / session_id
    archived_dir = tmp_path / "sessions" / "archived" / session_id

    # Manually set updated_at to be older than timeout
    session_file = active_dir / "session.json"
    data = json.loads(session_file.read_text())
    expired_time = datetime.now() - timedelta(seconds=7201)
    data["updated_at"] = expired_time.isoformat()
    session_file.write_text(json.dumps(data))

    # Archive expired sessions with 7200 second timeout
    archived_ids = session_manager.archive_expired_sessions(7200)

    # Verify the session was archived
    assert session_id in archived_ids
    assert not active_dir.exists()
    assert archived_dir.exists()
    assert (archived_dir / "session.json").exists()
    assert (archived_dir / "archive.json").exists()

    # Verify archive reason
    archive_data = json.loads((archived_dir / "archive.json").read_text())
    assert archive_data["reason"] == "session_timeout"


def test_archive_expired_sessions_keeps_active(
    session_manager: SessionManager, tmp_path: Path
):
    """Test that only expired sessions are archived, active ones remain."""
    from datetime import timedelta

    # Create two sessions
    session1 = session_manager.create_session("pack-1", "Topic 1")
    session2 = session_manager.create_session("pack-2", "Topic 2")

    # Make session1 expired
    session1_file = tmp_path / "sessions" / "active" / session1.session_id / "session.json"
    data1 = json.loads(session1_file.read_text())
    expired_time = datetime.now() - timedelta(seconds=7201)
    data1["updated_at"] = expired_time.isoformat()
    session1_file.write_text(json.dumps(data1))

    # Keep session2 active (recent update)
    session2_file = tmp_path / "sessions" / "active" / session2.session_id / "session.json"
    data2 = json.loads(session2_file.read_text())
    recent_time = datetime.now() - timedelta(seconds=1000)
    data2["updated_at"] = recent_time.isoformat()
    session2_file.write_text(json.dumps(data2))

    # Archive expired sessions
    archived_ids = session_manager.archive_expired_sessions(7200)

    # Verify only session1 was archived
    assert session1.session_id in archived_ids
    assert session2.session_id not in archived_ids

    # Verify session1 is archived
    assert not (tmp_path / "sessions" / "active" / session1.session_id).exists()
    assert (tmp_path / "sessions" / "archived" / session1.session_id).exists()

    # Verify session2 is still active
    assert (tmp_path / "sessions" / "active" / session2.session_id).exists()
    assert not (tmp_path / "sessions" / "archived" / session2.session_id).exists()


def test_archive_expired_sessions_no_expired(session_manager: SessionManager):
    """Test that archiving works correctly when no sessions are expired."""
    # Create multiple sessions
    session1 = session_manager.create_session("pack-1", "Topic 1")
    session2 = session_manager.create_session("pack-2", "Topic 2")

    # Archive with a very long timeout (no sessions should be expired)
    archived_ids = session_manager.archive_expired_sessions(999999)

    # Verify no sessions were archived
    assert len(archived_ids) == 0

    # Verify all sessions are still active
    active_sessions = session_manager.list_active_sessions()
    active_ids = {s.session_id for s in active_sessions}
    assert active_ids == {session1.session_id, session2.session_id}
