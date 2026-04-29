"""Artifact-Board synchronization protocol for garage-agent.

This module implements the consistency protocol between the board (in-memory
artifact references) and the actual artifact files on disk. It ensures that
the board reflects the true state of artifact files.

Conflict Resolution Rule: Always trust the actual file content on disk.
If there's a mismatch, the board is updated to match the file.
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from garage_os.storage.front_matter import FrontMatterParser
from garage_os.types import ArtifactReference, ArtifactRole, ArtifactStatus


class SyncAction(Enum):
    """Actions taken during artifact synchronization."""

    BOARD_UPDATED = "board_updated"
    ORPHANED = "orphaned"
    UNTRACKED = "untracked"
    CONSISTENT = "consistent"


@dataclass
class SyncLogEntry:
    """A log entry for artifact synchronization operations."""

    sync_id: str
    timestamp: str
    trigger: str
    artifact_path: str
    board_status: str
    file_status: Optional[str]
    action: str
    resolved_by: str


@dataclass
class SyncResult:
    """Result of an artifact synchronization operation.

    Attributes:
        consistent: List of artifacts that are consistent with disk
        updated: List of artifacts that were updated to match disk
        orphaned: List of artifacts referenced in board but missing on disk
        untracked: List of files on disk not referenced in board
    """

    consistent: List[ArtifactReference] = field(default_factory=list)
    updated: List[ArtifactReference] = field(default_factory=list)
    orphaned: List[ArtifactReference] = field(default_factory=list)
    untracked: List[Path] = field(default_factory=list)


class ArtifactBoardSync:
    """Synchronizes artifact board with actual files on disk.

    This class implements the artifact-board consistency protocol. It compares
    the board's artifact references with the actual files on disk and resolves
    any conflicts by always trusting the file content.

    Conflict Resolution: Always trust the actual file content on disk.
    """

    def __init__(self, root_dir: Path):
        """Initialize the sync manager.

        Args:
            root_dir: Root directory of the workspace (for resolving file paths)
        """
        self.root_dir = root_dir

    def sync(
        self,
        artifacts: List[ArtifactReference],
        trigger: str,
        session_dir: Path,
    ) -> SyncResult:
        """Synchronize artifact board with disk files.

        Compares the board's artifact references with actual files on disk,
        categorizes each artifact, and returns the sync result.

        Args:
            artifacts: List of artifact references from the board
            trigger: What triggered the sync (session_resume, skill_pre_execute,
                     skill_post_execute)
            session_dir: Directory to write sync-log.json

        Returns:
            SyncResult containing categorized artifacts
        """
        result = SyncResult()

        for artifact in artifacts:
            artifact_path = self.root_dir / artifact.path

            # Check if file exists
            if not artifact_path.exists():
                # File referenced in board but missing on disk
                result.orphaned.append(artifact)
                self._log_sync(
                    session_dir=session_dir,
                    trigger=trigger,
                    artifact=artifact,
                    action=SyncAction.ORPHANED,
                )
                continue

            # File exists - compare with board
            try:
                front_matter, _ = FrontMatterParser.parse_file(artifact_path)
                file_status = front_matter.get("status", "draft")
                file_date = front_matter.get("date", "")

                # Calculate hash of file's key fields
                file_hash = self._calculate_file_hash(file_status, file_date)

                # Calculate hash of board's key fields
                board_hash = self._calculate_board_hash(artifact)

                if file_hash == board_hash:
                    # Consistent - no action needed
                    result.consistent.append(artifact)
                    self._log_sync(
                        session_dir=session_dir,
                        trigger=trigger,
                        artifact=artifact,
                        action=SyncAction.CONSISTENT,
                        file_status=file_status,
                    )
                else:
                    # File changed - update board to match file
                    updated_artifact = self._update_artifact_from_file(
                        artifact, front_matter
                    )
                    result.updated.append(updated_artifact)
                    # Log with original artifact to show board state before update
                    self._log_sync(
                        session_dir=session_dir,
                        trigger=trigger,
                        artifact=artifact,
                        action=SyncAction.BOARD_UPDATED,
                        file_status=file_status,
                    )

            except (ValueError, FileNotFoundError):
                # File exists but can't be parsed - treat as inconsistent
                result.orphaned.append(artifact)
                self._log_sync(
                    session_dir=session_dir,
                    trigger=trigger,
                    artifact=artifact,
                    action=SyncAction.ORPHANED,
                )

        # Check for untracked files (files on disk not in board)
        tracked_paths = {str(artifact.path) for artifact in artifacts}
        untracked_files = self._find_untracked_files(tracked_paths)

        for untracked_path in untracked_files:
            result.untracked.append(untracked_path)
            self._log_sync(
                session_dir=session_dir,
                trigger=trigger,
                artifact_path=str(untracked_path),
                action=SyncAction.UNTRACKED,
            )

        return result

    def _calculate_file_hash(self, status: str, date: str) -> str:
        """Calculate hash of file's key fields.

        Args:
            status: Status value from front matter
            date: Date value from front matter

        Returns:
            SHA256 hash of the concatenated values
        """
        content = f"{status}|{date}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _calculate_board_hash(self, artifact: ArtifactReference) -> str:
        """Calculate hash of board's key fields.

        Args:
            artifact: Artifact reference from board

        Returns:
            SHA256 hash of the concatenated values
        """
        status = artifact.status.value if artifact.status else ""
        date_str = ""
        if artifact.updated_at:
            # Format datetime to match ISO format from file
            # Use 'Z' suffix for UTC instead of +00:00
            date_str = artifact.updated_at.isoformat()
            if artifact.updated_at.tzinfo is not None:
                # Has timezone - convert to Z format
                date_str = artifact.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                # No timezone - assume UTC and add Z
                date_str = artifact.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        return self._calculate_file_hash(status, date_str)

    def _update_artifact_from_file(
        self,
        artifact: ArtifactReference,
        front_matter: dict,
    ) -> ArtifactReference:
        """Update artifact reference to match file content.

        Args:
            artifact: Original artifact reference
            front_matter: Parsed front matter from file

        Returns:
            Updated artifact reference
        """
        file_status = front_matter.get("status", "draft")
        file_date_str = front_matter.get("date", "")

        # Map status string to ArtifactStatus enum
        try:
            updated_status = ArtifactStatus(file_status)
        except ValueError:
            updated_status = ArtifactStatus.DRAFT

        # Parse date - keep it simple for hash comparison
        updated_at = artifact.updated_at
        if file_date_str:
            try:
                # Parse with Z suffix handling
                if file_date_str.endswith("Z"):
                    updated_at = datetime.fromisoformat(file_date_str.replace("Z", "+00:00"))
                else:
                    updated_at = datetime.fromisoformat(file_date_str)
            except ValueError:
                pass

        # Create updated artifact
        return ArtifactReference(
            artifact_role=artifact.artifact_role,
            path=artifact.path,
            status=updated_status,
            created_at=artifact.created_at,
            updated_at=updated_at,
            checksum=artifact.checksum,
        )

    def _find_untracked_files(
        self, tracked_paths: set[str]
    ) -> List[Path]:
        """Find artifact files on disk that are not tracked in board.

        Args:
            tracked_paths: Set of paths tracked in board

        Returns:
            List of untracked file paths (relative to root_dir)
        """
        untracked = []

        # Common artifact directories and subdirectories
        docs_dir = self.root_dir / "docs"
        if docs_dir.exists():
            for file_path in docs_dir.rglob("*.md"):
                relative_path = file_path.relative_to(self.root_dir)
                if str(relative_path) not in tracked_paths:
                    untracked.append(relative_path)

        return untracked

    def _log_sync(
        self,
        session_dir: Path,
        trigger: str,
        artifact: Optional[ArtifactReference] = None,
        action: Optional[SyncAction] = None,
        file_status: Optional[str] = None,
        artifact_path: Optional[str] = None,
    ) -> None:
        """Write a sync log entry to sync-log.json.

        Args:
            session_dir: Session directory to write log to
            trigger: What triggered the sync
            artifact: Artifact reference (for BOARD_UPDATED, ORPHANED, CONSISTENT)
            action: Sync action taken
            file_status: Status from file (if applicable)
            artifact_path: Override artifact path (for UNTRACKED)
        """
        sync_id = f"sync-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        timestamp = datetime.now().isoformat()

        # Determine artifact path and board status
        if artifact:
            path_str = str(artifact.path)
            board_status = artifact.status.value if artifact.status else "unknown"
        else:
            path_str = artifact_path or "unknown"
            board_status = "unknown"

        # Determine file status
        if action == SyncAction.UNTRACKED:
            final_file_status = None
        else:
            final_file_status = file_status or board_status

        # Determine action string
        if action:
            action_str = action.value
        else:
            action_str = "consistent"

        log_entry = SyncLogEntry(
            sync_id=sync_id,
            timestamp=timestamp,
            trigger=trigger,
            artifact_path=path_str,
            board_status=board_status,
            file_status=final_file_status,
            action=action_str,
            resolved_by="artifact_first_rule",
        )

        # Write to sync-log.json
        log_file = session_dir / "sync-log.json"
        with open(log_file, "w") as f:
            json.dump(
                {
                    "sync_id": log_entry.sync_id,
                    "timestamp": log_entry.timestamp,
                    "trigger": log_entry.trigger,
                    "artifact_path": log_entry.artifact_path,
                    "board_status": log_entry.board_status,
                    "file_status": log_entry.file_status,
                    "action": log_entry.action,
                    "resolved_by": log_entry.resolved_by,
                },
                f,
                indent=2,
            )
