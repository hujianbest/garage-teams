"""
Unit tests for core type definitions.

These tests validate the data structures and enums used across garage-agent.
"""

import pytest
from datetime import datetime
from pathlib import Path
from garage_os.types import (
    SessionState,
    ArtifactRole,
    ArtifactStatus,
    ArtifactReference,
    SessionContext,
    SessionMetadata,
    KnowledgeType,
    KnowledgeEntry,
    ExperienceRecord,
)


class TestSessionState:
    """Test SessionState enum."""

    def test_all_states_defined(self):
        """Verify all expected session states are defined."""
        expected_states = {
            SessionState.IDLE: "idle",
            SessionState.RUNNING: "running",
            SessionState.PAUSED: "paused",
            SessionState.COMPLETED: "completed",
            SessionState.FAILED: "failed",
            SessionState.ARCHIVED: "archived",
        }
        for state, value in expected_states.items():
            assert state.value == value


class TestArtifactRole:
    """Test ArtifactRole enum."""

    def test_all_roles_defined(self):
        """Verify all expected artifact roles are defined."""
        expected_roles = {
            ArtifactRole.SPEC: "spec",
            ArtifactRole.DESIGN: "design",
            ArtifactRole.TASKS: "tasks",
            ArtifactRole.CODE: "code",
            ArtifactRole.REVIEW: "review",
            ArtifactRole.OTHER: "other",
        }
        for role, value in expected_roles.items():
            assert role.value == value


class TestArtifactReference:
    """Test ArtifactReference dataclass."""

    def test_create_artifact_reference(self):
        """Test creating an artifact reference."""
        ref = ArtifactReference(
            artifact_role=ArtifactRole.DESIGN,
            path=Path("docs/designs/test.md"),
            status=ArtifactStatus.DRAFT,
            created_at=datetime.now(),
        )
        assert ref.artifact_role == ArtifactRole.DESIGN
        assert ref.path == Path("docs/designs/test.md")
        assert ref.status == ArtifactStatus.DRAFT
        assert ref.checksum is None


class TestSessionContext:
    """Test SessionContext dataclass."""

    def test_create_session_context(self):
        """Test creating a session context."""
        context = SessionContext(
            pack_id="ahe-coding",
            topic="Test workflow",
            user_goals=["Goal 1", "Goal 2"],
            constraints=["Constraint 1"],
        )
        assert context.pack_id == "ahe-coding"
        assert context.topic == "Test workflow"
        assert len(context.user_goals) == 2
        assert len(context.constraints) == 1


class TestSessionMetadata:
    """Test SessionMetadata dataclass."""

    def test_create_session_metadata(self):
        """Test creating session metadata."""
        metadata = SessionMetadata(
            session_id="session-20260416-001",
            pack_id="ahe-coding",
            topic="Test workflow",
            state=SessionState.IDLE,
            current_node_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            context=SessionContext(
                pack_id="ahe-coding",
                topic="Test workflow",
            ),
        )
        assert metadata.session_id == "session-20260416-001"
        assert metadata.state == SessionState.IDLE
        assert metadata.host == "claude-code"


class TestKnowledgeEntry:
    """Test KnowledgeEntry dataclass."""

    def test_create_knowledge_entry(self):
        """Test creating a knowledge entry."""
        entry = KnowledgeEntry(
            id="decision-001",
            type=KnowledgeType.DECISION,
            topic="Test decision",
            date=datetime.now(),
            tags=["architecture", "storage"],
            content="Decision content here",
        )
        assert entry.id == "decision-001"
        assert entry.type == KnowledgeType.DECISION
        assert len(entry.tags) == 2
        assert entry.status == "active"


class TestExperienceRecord:
    """Test ExperienceRecord dataclass."""

    def test_create_experience_record(self):
        """Test creating an experience record."""
        record = ExperienceRecord(
            record_id="task-001",
            task_type="feature_implementation",
            skill_ids=["ahe-specify", "ahe-design"],
            tech_stack=["Python", "YAML"],
            domain="system_design",
            problem_domain="agent_os",
            outcome="success",
            duration_seconds=3600,
            complexity="medium",
            session_id="session-20260416-001",
            key_patterns=["pattern1", "pattern2"],
            lessons_learned=["Lesson 1"],
        )
        assert record.record_id == "task-001"
        assert record.outcome == "success"
        assert len(record.key_patterns) == 2
        assert len(record.lessons_learned) == 1
