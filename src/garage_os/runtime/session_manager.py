"""Session management for Garage Agent OS workflows."""

import hashlib
import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from garage_os.memory import CandidateStore, ExtractionConfig, MemoryExtractionOrchestrator
except ImportError:  # pragma: no cover - memory pipeline may not exist in early stages
    CandidateStore = None
    ExtractionConfig = None
    MemoryExtractionOrchestrator = None

from garage_os.types import (
    SessionMetadata,
    SessionState,
    SessionContext,
    Checkpoint,
    RecoveryResult,
)
from garage_os.storage import FileStorage

logger = logging.getLogger(__name__)


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
            elif key == "context_metadata":
                context = data.setdefault("context", {})
                existing_metadata = context.get("metadata", {})
                if not isinstance(existing_metadata, dict):
                    existing_metadata = {}
                if isinstance(value, dict):
                    existing_metadata.update(value)
                context["metadata"] = existing_metadata
            elif key == "artifacts":
                data["artifacts"] = value

        # Update timestamp
        data["updated_at"] = datetime.now().isoformat()

        # Write back
        checksum = self._storage.write_json(session_path, data)
        data["checksum"] = checksum
        self._storage.write_json(session_path, data)

        return self._deserialize_metadata(data)

    def archive_session(
        self,
        session_id: str,
        reason: str = "session_archived",
        extraction_orchestrator: Optional[object] = None,
    ) -> bool:
        """Archive a session from active to archived storage.

        Args:
            session_id: Session identifier to archive
            reason: Archive reason recorded in ``archive.json``

        Returns:
            True if archived successfully, False otherwise
        """
        # Check if session exists
        session_path = f"sessions/active/{session_id}/session.json"
        data = self._storage.read_json(session_path)

        if data is None:
            return False

        src_path = f"sessions/active/{session_id}"
        archived_dir = f"sessions/archived/{session_id}"
        moved = self._storage.move(src_path, archived_dir)
        if not moved:
            return False

        archive_data = {
            "session_id": session_id,
            "archived_at": datetime.now().isoformat(),
            "reason": reason,
        }
        self._storage.write_json(f"{archived_dir}/archive.json", archive_data)

        # Best-effort memory extraction must never block archive success.
        self._trigger_memory_extraction(
            session_id,
            extraction_orchestrator=extraction_orchestrator,
        )

        return True

    # F004 § 11.4: stable filename for the per-session extraction error file.
    MEMORY_EXTRACTION_ERROR_FILENAME = "memory-extraction-error.json"

    def _trigger_memory_extraction(
        self,
        session_id: str,
        extraction_orchestrator: Optional[object] = None,
    ) -> None:
        """Run archive-time memory extraction in three guarded phases.

        F004 FR-404 / § 10.4 / ADR-404: any failure in orchestrator
        instantiation, enablement check, or extraction itself must
        - never block archive_session (still returns True)
        - persist a machine-readable summary to
          ``sessions/archived/<session_id>/memory-extraction-error.json``
          with a phase tag so downstream readers can locate the breakage
        - keep the original ``logger.warning`` as a stderr safety net so
          that operators reading logs do not lose the context.
        """
        orchestrator = extraction_orchestrator

        # Phase 1: orchestrator instantiation.
        if orchestrator is None:
            if (
                CandidateStore is None
                or ExtractionConfig is None
                or MemoryExtractionOrchestrator is None
            ):
                return
            try:
                orchestrator = MemoryExtractionOrchestrator(
                    self._storage,
                    CandidateStore(self._storage),
                    ExtractionConfig(),
                )
            except Exception as exc:
                self._persist_extraction_error(session_id, "orchestrator_init", exc)
                return

        # Phase 2: enablement check.
        try:
            enabled = orchestrator.is_extraction_enabled()
        except Exception as exc:
            self._persist_extraction_error(session_id, "enablement_check", exc)
            return
        if not enabled:
            return

        archived_session_path = f"sessions/archived/{session_id}/session.json"
        archived_session = self._storage.read_json(archived_session_path)
        if archived_session is None:
            return

        # Phase 3: extraction proper.
        try:
            orchestrator.extract_for_archived_session(archived_session)
        except Exception as exc:
            self._persist_extraction_error(session_id, "extraction", exc)

    def _persist_extraction_error(
        self, session_id: str, phase: str, exc: BaseException
    ) -> None:
        """Persist a single latest-error JSON for the session-side trigger path.

        F004 § 11.4 schema: ``schema_version`` / ``session_id`` / ``phase`` /
        ``error_type`` / ``error_message`` / ``triggered_at``. Each new failure
        for the same session overwrites the previous file (latest-error
        semantics; archive-time extraction only fires once per session).

        ``logger.warning`` is intentionally kept as a stderr-side breadcrumb
        so that operators tailing logs still see the failure even when the
        file write itself succeeds silently.
        """
        error_path = (
            f"sessions/archived/{session_id}/{self.MEMORY_EXTRACTION_ERROR_FILENAME}"
        )
        try:
            self._storage.write_json(
                error_path,
                {
                    "schema_version": "1",
                    "session_id": session_id,
                    "phase": phase,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "triggered_at": datetime.now().isoformat(),
                },
            )
        except Exception:  # pragma: no cover - defensive: never mask the
            # original extraction failure with a write-time failure.
            pass
        logger.warning(
            "Memory extraction failed for archived session %s (phase=%s): %s",
            session_id,
            phase,
            exc,
            exc_info=True,
        )

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

    def archive_expired_sessions(self, timeout_seconds: int) -> list[str]:
        """Archive sessions that have exceeded the timeout period.

        Args:
            timeout_seconds: Timeout threshold in seconds

        Returns:
            List of archived session IDs
        """
        archived_ids: list[str] = []
        now = datetime.now()

        # Get all active sessions
        active_sessions = self.list_active_sessions()

        for session in active_sessions:
            # Calculate time since last update
            time_since_update = (now - session.updated_at).total_seconds()

            # Check if session has expired
            if time_since_update > timeout_seconds:
                session_id = session.session_id

                # Check if session exists
                session_path = f"sessions/active/{session_id}/session.json"
                data = self._storage.read_json(session_path)

                if data is None:
                    continue

                if self.archive_session(session_id, reason="session_timeout"):
                    archived_ids.append(session_id)

        return archived_ids

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
        checkpoint_id = f"cp-{now.strftime('%Y%m%d-%H%M%S-%f')}"

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
        # Add checksum to serialized data for inclusion in file
        serialized["checksum"] = checksum
        self._storage.write_json(checkpoint_path, serialized)

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
        max_seq = self._scan_session_sequence(archived_dir, pattern, max_seq)

        next_seq = max_seq + 1
        return f"session-{today}-{next_seq:03d}"

    def _scan_session_sequence(
        self,
        base_dir: Path,
        pattern: re.Pattern[str],
        current_max: int,
    ) -> int:
        """Scan active/archived directories for the highest sequence number.

        Supports both the current layout ``sessions/<state>/<session_id>/`` and an
        older nested archived layout where session directories may sit one level
        deeper under date buckets.
        """
        max_seq = current_max
        if not base_dir.exists():
            return max_seq

        for child in base_dir.iterdir():
            if not child.is_dir():
                continue

            match = pattern.match(child.name)
            if match:
                max_seq = max(max_seq, int(match.group(1)))
                continue

            for nested in child.iterdir():
                if not nested.is_dir():
                    continue
                match = pattern.match(nested.name)
                if match:
                    max_seq = max(max_seq, int(match.group(1)))

        return max_seq

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

    def recover_session(self, session_id: str) -> Optional[RecoveryResult]:
        """Recover a session using a 5-level fallback strategy.

        Recovery priority:
        1. Valid session.json (checksum verified)
        2. Latest valid checkpoint (if session.json corrupted)
        3. Previous valid checkpoint (if latest checkpoint corrupted)
        4. Artifact-first rebuild (scan artifacts directory)
        5. No data available (return None)

        Args:
            session_id: Session identifier to recover

        Returns:
            RecoveryResult if recovery succeeded, None otherwise
        """
        recovery_log = []

        # Level 1: Try to recover from session.json
        session_path = f"sessions/active/{session_id}/session.json"
        session_data = self._storage.read_json(session_path)

        if session_data is not None:
            # Validate checksum
            stored_checksum = session_data.get("checksum")
            if stored_checksum and self._validate_checksum(session_data, stored_checksum):
                # Checksum valid, recover from session.json
                metadata = self._deserialize_metadata(session_data)
                recovery_log.append("Recovered from valid session.json")
                return RecoveryResult(
                    metadata=metadata,
                    recovery_method="session_json",
                    recovery_log=recovery_log,
                )
            else:
                recovery_log.append("session.json checksum validation failed")
        else:
            recovery_log.append("session.json not found or could not be read")

        # Level 2 & 3: Try to recover from checkpoint
        checkpoint_result = self._find_valid_checkpoint(session_id)
        if checkpoint_result is not None:
            checkpoint_data, is_latest = checkpoint_result
            metadata = self._deserialize_metadata(checkpoint_data)
            method_suffix = " (fallback)" if not is_latest else ""
            recovery_log.append(f"Recovered from checkpoint{method_suffix}")
            return RecoveryResult(
                metadata=metadata,
                recovery_method="checkpoint" if is_latest else "checkpoint_fallback",
                recovery_log=recovery_log,
            )

        # Level 4: Artifact-first rebuild
        metadata = self._rebuild_from_artifacts(session_id)
        if metadata is not None:
            recovery_log.append("Rebuilt from artifacts directory")
            return RecoveryResult(
                metadata=metadata,
                recovery_method="artifact_first",
                recovery_log=recovery_log,
            )

        # Level 5: No data available
        return None

    def _validate_checksum(self, data: dict, expected_checksum: str) -> bool:
        """Validate checksum of data.

        Args:
            data: Data dictionary to validate
            expected_checksum: Expected SHA-256 checksum

        Returns:
            True if checksum matches, False otherwise
        """
        # Create a copy without the checksum field
        # (checksum is computed from data WITHOUT the checksum field)
        data_copy = data.copy()
        data_copy.pop("checksum", None)

        # Serialize the data as JSON (same way as write_json)
        json_str = json.dumps(data_copy, indent=2, ensure_ascii=False)
        computed_checksum = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

        return computed_checksum == expected_checksum

    def _find_valid_checkpoint(self, session_id: str) -> Optional[tuple[dict, bool]]:
        """Find the latest valid checkpoint for a session.

        Args:
            session_id: Session identifier

        Returns:
            Tuple of (session metadata dict reconstructed from checkpoint, is_latest)
            where is_latest indicates if this is the first (newest) checkpoint checked.
            Returns None if no valid checkpoint found.
        """
        checkpoint_dir = f"sessions/active/{session_id}/checkpoints"

        # List all checkpoint files
        checkpoint_files = self._storage.list_files(checkpoint_dir, "*.json")

        if not checkpoint_files:
            return None

        # Sort by filename (newest first based on timestamp in filename)
        checkpoint_files.sort(key=lambda p: p.name, reverse=True)

        is_first_checkpoint = True

        for checkpoint_file in checkpoint_files:
            # Read checkpoint data
            checkpoint_data = self._storage.read_json(
                f"sessions/active/{session_id}/checkpoints/{checkpoint_file.name}"
            )

            if checkpoint_data is None:
                is_first_checkpoint = False
                continue

            # Validate checksum
            stored_checksum = checkpoint_data.get("checksum")
            if stored_checksum and self._validate_checksum(checkpoint_data, stored_checksum):
                # Valid checkpoint found - reconstruct session metadata
                # Try to read session.json even if checksum is invalid
                session_path = f"sessions/active/{session_id}/session.json"
                session_data = self._storage.read_json(session_path)

                # Create a session metadata dict from checkpoint
                if session_data is not None:
                    # Use session data as base (even with invalid checksum)
                    session_data["updated_at"] = checkpoint_data.get("timestamp")
                    return (session_data, is_first_checkpoint)
                else:
                    # No session data at all, create minimal metadata from checkpoint
                    return ({
                        "session_id": session_id,
                        "pack_id": "unknown",
                        "topic": f"Recovered from checkpoint {checkpoint_data.get('checkpoint_id')}",
                        "state": "idle",
                        "current_node_id": checkpoint_data.get("node_id"),
                        "created_at": checkpoint_data.get("timestamp"),
                        "updated_at": checkpoint_data.get("timestamp"),
                        "context": {
                            "pack_id": "unknown",
                            "topic": "Recovered from checkpoint",
                            "graph_variant_id": None,
                            "user_goals": [],
                            "constraints": [],
                            "metadata": {},
                        },
                        "artifacts": [],
                        "host": "claude-code",
                        "host_version": "unknown",
                        "garage_version": "0.1.0",
                    }, is_first_checkpoint)
            else:
                # Checksum invalid, move to next checkpoint
                is_first_checkpoint = False

        return None

    def _rebuild_from_artifacts(self, session_id: str) -> Optional[SessionMetadata]:
        """Rebuild session metadata from artifacts directory.

        Args:
            session_id: Session identifier

        Returns:
            Reconstructed SessionMetadata if artifacts exist, None otherwise
        """
        from garage_os.types import ArtifactReference, ArtifactRole, ArtifactStatus

        artifacts_dir = f"sessions/active/{session_id}/artifacts"

        # Check if artifacts directory exists
        if not self._storage.exists(artifacts_dir):
            return None

        # List artifact files
        artifact_files = self._storage.list_files(artifacts_dir, "*")

        if not artifact_files:
            return None

        # Create artifact references from files
        now = datetime.now()
        artifacts = []
        for artifact_file in artifact_files:
            if artifact_file.is_file():
                artifact_ref = ArtifactReference(
                    artifact_role=ArtifactRole.OTHER,
                    path=artifact_file,
                    status=ArtifactStatus.APPROVED,
                    created_at=now,
                    updated_at=None,
                    checksum=None,
                )
                artifacts.append(artifact_ref)

        # Create minimal session metadata
        context = SessionContext(
            pack_id="unknown",
            topic="Recovered session",
            user_goals=[],
            constraints=[],
        )

        metadata = SessionMetadata(
            session_id=session_id,
            pack_id="unknown",
            topic="Recovered session",
            state=SessionState.IDLE,
            current_node_id=None,
            created_at=now,
            updated_at=now,
            context=context,
            artifacts=artifacts,
        )

        return metadata
