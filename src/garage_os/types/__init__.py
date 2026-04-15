"""
Core type definitions for Garage Agent OS.

This module defines the primary data structures used across the runtime,
including sessions, artifacts, knowledge entries, and experience records.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path


class SessionState(Enum):
    """Possible states of a workflow session."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ArtifactRole(Enum):
    """Roles that artifacts can play in a workflow."""

    SPEC = "spec"
    DESIGN = "design"
    TASKS = "tasks"
    CODE = "code"
    REVIEW = "review"
    OTHER = "other"


class ArtifactStatus(Enum):
    """Status of an artifact in its lifecycle."""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ARCHIVED = "archived"


@dataclass
class ArtifactReference:
    """Reference to an artifact produced or consumed by a workflow node."""

    artifact_role: ArtifactRole
    path: Path
    status: ArtifactStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    checksum: Optional[str] = None


@dataclass
class SessionContext:
    """Context information for a workflow session."""

    pack_id: str
    topic: str
    graph_variant_id: Optional[str] = None
    user_goals: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMetadata:
    """Metadata about a workflow session."""

    session_id: str
    pack_id: str
    topic: str
    state: SessionState
    current_node_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    context: SessionContext
    artifacts: List[ArtifactReference] = field(default_factory=list)
    host: str = "claude-code"
    host_version: str = "unknown"
    garage_version: str = "0.1.0"


class KnowledgeType(Enum):
    """Types of knowledge entries."""

    DECISION = "decision"
    PATTERN = "pattern"
    SOLUTION = "solution"


@dataclass
class KnowledgeEntry:
    """A knowledge entry stored in the knowledge base."""

    id: str
    type: KnowledgeType
    topic: str
    date: datetime
    tags: List[str]
    content: str
    status: str = "active"
    version: int = 1
    related_decisions: List[str] = field(default_factory=list)
    related_tasks: List[str] = field(default_factory=list)
    source_session: Optional[str] = None
    source_artifact: Optional[str] = None
    front_matter: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperienceRecord:
    """A record of execution experience for future reference."""

    record_id: str
    task_type: str
    skill_ids: List[str]
    tech_stack: List[str]
    domain: str
    problem_domain: str
    outcome: str
    duration_seconds: int
    complexity: str
    session_id: str
    artifacts: List[str] = field(default_factory=list)
    key_patterns: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    pitfalls: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class ErrorCategory(Enum):
    """Categories of errors that can occur during execution."""

    RETRYABLE = "retryable"
    USER_INTERVENTION = "user_intervention"
    FATAL = "fatal"
    IGNORABLE = "ignorable"


@dataclass
class StateTransition:
    """Record of a state transition in a workflow session."""

    from_state: SessionState
    to_state: SessionState
    timestamp: datetime
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Checkpoint:
    """A checkpoint representing a snapshot of execution state."""

    checkpoint_id: str
    node_id: str
    timestamp: datetime
    state_snapshot: Dict[str, Any]
    checksum: Optional[str] = None


@dataclass
class RecoveryResult:
    """Result of a session recovery operation."""

    metadata: SessionMetadata
    recovery_method: str
    recovery_log: List[str] = field(default_factory=list)


@dataclass
class SyncLogEntry:
    """A log entry for artifact synchronization operations."""

    artifact_path: Path
    board_status: str
    file_exists: bool
    checksum_match: Optional[bool]
    timestamp: datetime
    resolution: Optional[str] = None


__all__ = [
    "SessionState",
    "ArtifactRole",
    "ArtifactStatus",
    "ArtifactReference",
    "SessionContext",
    "SessionMetadata",
    "KnowledgeType",
    "KnowledgeEntry",
    "ExperienceRecord",
    "ErrorCategory",
    "StateTransition",
    "Checkpoint",
    "RecoveryResult",
    "SyncLogEntry",
]
