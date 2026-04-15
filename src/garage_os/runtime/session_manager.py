"""Session management for Garage Agent OS workflows."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from garage_os.types import (
    SessionMetadata,
    SessionState,
    SessionContext,
    Checkpoint,
)
from garage_os.storage import FileStorage


class SessionManager:
    """Manage workflow session lifecycle including creation, restoration, updates, and archiving."""

    def __init__(self, storage: FileStorage):
        """Initialize session manager with storage backend.

        Args:
            storage: File storage backend for persistence
        """
        self._storage = storage

    def create_session(
        self,
        pack_id: str,
        topic: str,
        user_goals: Optional[list[str]] = None,
        constraints: Optional[list[str]] = None,
    ) -> SessionMetadata:
        """Create a new workflow session.

        Args:
            pack_id: Identifier of the pack being executed
            topic: Topic or description of the workflow
            user_goals: Optional list of user-defined goals
            constraints: Optional list of constraints for the session

        Returns:
            Created session metadata
        """
        session_id = self._generate_session_id()

        now = datetime.now()
        context = SessionContext(
            pack_id=pack_id,
            topic=topic,
            user_goals=user_goals or [],
            constraints=constraints or [],
        )

        metadata = SessionMetadata(
            session_id=session_id,
            pack_id=pack_id,
            topic=topic,
            state=SessionState.IDLE,
            current_node_id=None,
            created_at=now,
            updated_at=now,
            context=context,
        )

        # Write session.json
        session_path = f"sessions/active/{session_id}/session.json"
        serialized = self._serialize_metadata(metadata)
        checksum = self._storage.write_json(session_path, serialized)
        # Add checksum to serialized data for inclusion in file
        serialized["checksum"] = checksum
        self._storage.write_json(session_path, serialized)

        return metadata

    def restore_session(self, session_id: str) -> Optional[SessionMetadata]:
        """Restore a session from storage.

        Args:
            session_id: Session identifier to restore

        Returns:
            Session metadata if found, None otherwise
        """
        session_path = f"sessions/active/{session_id}/session.json"
        data = self._storage.read_json(session_path)

        if data is None:
            return None

        return self._deserialize_metadata(data)

    def update_session(self, session_id: str, **kwargs) -> Optional[SessionMetadata]:
        """Update session fields.

        Args:
            session_id: Session identifier to update
            **kwargs: Fields to update (e.g., state, current_node_id)

        Returns:
            Updated session metadata, or None if session not found
        """
        # Load existing metadata
        session_path = f"sessions/active/{session_id}/session.json"
        data = self._storage.read_json(session_path)

        if data is None:
            return None

        # Update fields
        for key, value in kwargs.items():
            if key == "state":
                if isinstance(value, SessionState):
                    data["state"] = value.value
                else:
                    data["state"] = value
            elif key == "current_node_id":
                data["current_node_id"] = value
            elif key in ("pack_id", "topic"):
                data[key] = value

        # Update timestamp
        data["updated_at"] = datetime.now().isoformat()

        # Write back
        checksum = self._storage.write_json(session_path, data)
        data["checksum"] = checksum
        self._storage.write_json(session_path, data)

        return self._deserialize_metadata(data)

    def archive_session(self, session_id: str) -> bool:
        """Archive a session from active to archived storage.

        Args:
            session_id: Session identifier to archive

        Returns:
            True if archived successfully, False otherwise
        """
        # Check if session exists
        session_path = f"sessions/active/{session_id}/session.json"
        data = self._storage.read_json(session_path)

        if data is None:
            return False

        # Create archive.json with archive metadata
        now = datetime.now()
        archive_data = {
            "session_id": session_id,
            "archived_at": now.isoformat(),
            "reason": "session_archived",
        }

        # Ensure archived directory exists
        archived_dir = f"sessions/archived/{session_id}"
        self._storage.ensure_dir(archived_dir)

        # Write archive.json
        self._storage.write_json(f"{archived_dir}/archive.json", archive_data)

        # Move session directory
        src_path = f"sessions/active/{session_id}"
        dst_path = f"sessions/archived/{session_id}/session.json"
        self._storage.ensure_dir(f"sessions/archived/{session_id}")

        # Read the session data first
        session_data = self._storage.read_json(f"sessions/active/{session_id}/session.json")

        # Write to new location
        self._storage.write_json(dst_path, session_data)

        # Remove old directory
        old_session_dir = self._storage._get_full_path(f"sessions/active/{session_id}")
        if old_session_dir.exists():
            for item in old_session_dir.iterdir():
                item.unlink()
            old_session_dir.rmdir()

        return True

    def list_active_sessions(self) -> list[SessionMetadata]:
        """List all active sessions.

        Returns:
            List of active session metadata
        """
        sessions: list[SessionMetadata] = []

        # List all directories in sessions/active/
        active_dir = self._storage._get_full_path("sessions/active")
        if not active_dir.exists():
            return sessions

        for session_dir in active_dir.iterdir():
            if not session_dir.is_dir():
                continue

            session_id = session_dir.name
            metadata = self.restore_session(session_id)
            if metadata is not None:
                sessions.append(metadata)

        return sessions

    def create_checkpoint(
        self, session_id: str, node_id: str, state_snapshot: dict
    ) -> Checkpoint:
        """Create a checkpoint for a session at a specific node.

        Args:
            session_id: Session identifier
            node_id: Current workflow node ID
            state_snapshot: Snapshot of execution state

        Returns:
            Created checkpoint
        """
        now = datetime.now()
        checkpoint_id = f"cp-{now.strftime('%Y%m%d-%H%M%S')}"

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            node_id=node_id,
            timestamp=now,
            state_snapshot=state_snapshot,
        )

        # Write checkpoint file
        checkpoint_path = (
            f"sessions/active/{session_id}/checkpoints/{checkpoint_id}.json"
        )
        serialized = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "node_id": checkpoint.node_id,
            "timestamp": checkpoint.timestamp.isoformat(),
            "state_snapshot": checkpoint.state_snapshot,
        }
        checksum = self._storage.write_json(checkpoint_path, serialized)

        checkpoint.checksum = checksum
        return checkpoint

    def _generate_session_id(self) -> str:
        """Generate a unique session ID.

        Returns:
            Session ID in format: session-YYYYMMDD-NNN
        """
        today = datetime.now().strftime("%Y%m%d")

        # Find existing sessions for today to determine next sequence number
        pattern = re.compile(rf"^session-{today}-(\d+)$")
        max_seq = 0

        active_dir = self._storage._get_full_path("sessions/active")
        if active_dir.exists():
            for session_dir in active_dir.iterdir():
                match = pattern.match(session_dir.name)
                if match:
                    seq = int(match.group(1))
                    max_seq = max(max_seq, seq)

        # Also check archived sessions
        archived_dir = self._storage._get_full_path(f"sessions/archived")
        if archived_dir.exists():
            for date_dir in archived_dir.iterdir():
                if date_dir.is_dir():
                    for session_dir in date_dir.iterdir():
                        match = pattern.match(session_dir.name)
                        if match:
                            seq = int(match.group(1))
                            max_seq = max(max_seq, seq)

        next_seq = max_seq + 1
        return f"session-{today}-{next_seq:03d}"

    def _serialize_metadata(self, metadata: SessionMetadata) -> dict:
        """Serialize session metadata to JSON-compatible dict.

        Args:
            metadata: Session metadata to serialize

        Returns:
            JSON-serializable dictionary
        """
        serialized = {
            "session_id": metadata.session_id,
            "pack_id": metadata.pack_id,
            "topic": metadata.topic,
            "state": metadata.state.value,
            "current_node_id": metadata.current_node_id,
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
            "context": {
                "pack_id": metadata.context.pack_id,
                "topic": metadata.context.topic,
                "graph_variant_id": metadata.context.graph_variant_id,
                "user_goals": metadata.context.user_goals,
                "constraints": metadata.context.constraints,
                "metadata": metadata.context.metadata,
            },
            "artifacts": [],
            "host": metadata.host,
            "host_version": metadata.host_version,
            "garage_version": metadata.garage_version,
        }
        return serialized

    def _deserialize_metadata(self, data: dict) -> SessionMetadata:
        """Deserialize dict to session metadata.

        Args:
            data: Dictionary to deserialize

        Returns:
            Session metadata object
        """
        context_data = data.get("context", {})
        context = SessionContext(
            pack_id=context_data.get("pack_id", data.get("pack_id", "")),
            topic=context_data.get("topic", data.get("topic", "")),
            graph_variant_id=context_data.get("graph_variant_id"),
            user_goals=context_data.get("user_goals", []),
            constraints=context_data.get("constraints", []),
            metadata=context_data.get("metadata", {}),
        )

        return SessionMetadata(
            session_id=data["session_id"],
            pack_id=data["pack_id"],
            topic=data["topic"],
            state=SessionState(data["state"]),
            current_node_id=data.get("current_node_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            context=context,
            artifacts=[],
            host=data.get("host", "claude-code"),
            host_version=data.get("host_version", "unknown"),
            garage_version=data.get("garage_version", "0.1.0"),
        )
