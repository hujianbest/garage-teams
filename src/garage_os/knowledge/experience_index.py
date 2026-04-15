"""
Experience Index for Garage Agent OS.

Stores experience records as JSON files with a central index.
Directory structure:
- .garage/experience/records/<record_id>.json    <- Individual records
- .garage/knowledge/.metadata/index.json         <- Central index
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from garage_os.storage.file_storage import FileStorage
from garage_os.types import ExperienceRecord


class ExperienceIndex:
    """Store and index execution experience records."""

    # Paths for records and index
    RECORDS_DIR = "experience/records"
    INDEX_PATH = "knowledge/.metadata/index.json"

    def __init__(self, storage: FileStorage):
        """Initialize experience index with file storage backend.

        Args:
            storage: FileStorage instance for file operations
        """
        self._storage = storage
        self._ensure_directories()

    def store(self, record: ExperienceRecord) -> str:
        """Store an experience record and update the index.

        Args:
            record: ExperienceRecord to store

        Returns:
            SHA-256 checksum of the written content
        """
        # Ensure records directory exists
        self._storage.ensure_dir(self.RECORDS_DIR)

        # Build filepath for the record
        filename = f"{record.record_id}.json"
        filepath = f"{self.RECORDS_DIR}/{filename}"

        # Convert record to dict and write as JSON
        record_dict = self._record_to_dict(record)
        checksum = self._storage.write_json(filepath, record_dict)

        # Update the central index
        self._update_index(record)

        return checksum

    def retrieve(self, record_id: str) -> Optional[ExperienceRecord]:
        """Retrieve an experience record by ID.

        Args:
            record_id: Unique identifier for the record

        Returns:
            ExperienceRecord if found, None otherwise
        """
        filename = f"{record_id}.json"
        filepath = f"{self.RECORDS_DIR}/{filename}"

        data = self._storage.read_json(filepath)
        if data is None:
            return None

        return self._dict_to_record(data)

    def search(
        self,
        task_type: Optional[str] = None,
        skill_ids: Optional[List[str]] = None,
        domain: Optional[str] = None,
        key_patterns: Optional[List[str]] = None,
    ) -> List[ExperienceRecord]:
        """Search experience records by various dimensions.

        Args:
            task_type: Optional task type filter
            skill_ids: Optional list of skill IDs to filter by (OR logic)
            domain: Optional domain filter
            key_patterns: Optional list of key patterns to filter by (AND logic)

        Returns:
            List of matching ExperienceRecord objects
        """
        records = []

        # List all record files
        files = self._storage.list_files(self.RECORDS_DIR, "*.json")

        for file_path in files:
            # Read each record
            rel_path = str(file_path.relative_to(self._storage.base_path))
            data = self._storage.read_json(rel_path)

            if data is None:
                continue

            record = self._dict_to_record(data)

            # Apply filters
            if task_type and record.task_type != task_type:
                continue
            if domain and record.domain != domain:
                continue
            if skill_ids and not self._matches_skill_ids(record, skill_ids):
                continue
            if key_patterns and not self._matches_key_patterns(record, key_patterns):
                continue

            records.append(record)

        return records

    def update(self, record: ExperienceRecord) -> str:
        """Update an existing experience record.

        Args:
            record: ExperienceRecord with updated data

        Returns:
            SHA-256 checksum of the updated content
        """
        # Update timestamp
        record.updated_at = datetime.now()

        # Store the updated record
        return self.store(record)

    def delete(self, record_id: str) -> bool:
        """Delete an experience record and remove from index.

        Args:
            record_id: Unique identifier for the record

        Returns:
            True if record was deleted, False if it didn't exist
        """
        filename = f"{record_id}.json"
        filepath = f"{self.RECORDS_DIR}/{filename}"

        # Delete the record file
        deleted = self._storage.delete(filepath)

        # Remove from index if record existed
        if deleted:
            self._remove_from_index(record_id)

        return deleted

    def list_records(self) -> List[ExperienceRecord]:
        """List all experience records.

        Returns:
            List of all ExperienceRecord objects
        """
        records = []

        # List all record files
        files = self._storage.list_files(self.RECORDS_DIR, "*.json")

        for file_path in files:
            # Read each record
            rel_path = str(file_path.relative_to(self._storage.base_path))
            data = self._storage.read_json(rel_path)

            if data is None:
                continue

            records.append(self._dict_to_record(data))

        return records

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self._storage.ensure_dir(self.RECORDS_DIR)
        self._storage.ensure_dir("knowledge/.metadata")

    def _update_index(self, record: ExperienceRecord) -> None:
        """Update the central index with a new/updated record.

        Args:
            record: ExperienceRecord to add to index
        """
        # Read existing index
        index = self._load_index()

        # Add or update entry for this record
        index[record.record_id] = {
            "task_type": record.task_type,
            "domain": record.domain,
            "skill_ids": record.skill_ids,
            "key_patterns": record.key_patterns,
            "outcome": record.outcome,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

        # Write updated index
        self._storage.write_json(self.INDEX_PATH, index)

    def _remove_from_index(self, record_id: str) -> None:
        """Remove a record from the central index.

        Args:
            record_id: ID of record to remove
        """
        # Read existing index
        index = self._load_index()

        # Remove entry if it exists
        if record_id in index:
            del index[record_id]

            # Write updated index
            self._storage.write_json(self.INDEX_PATH, index)

    def _load_index(self) -> Dict[str, Any]:
        """Load the central index.

        Returns:
            Index dictionary, or empty dict if index doesn't exist
        """
        index = self._storage.read_json(self.INDEX_PATH)
        return index if index is not None else {}

    def _record_to_dict(self, record: ExperienceRecord) -> dict:
        """Convert an ExperienceRecord to a dictionary.

        Args:
            record: ExperienceRecord to convert

        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            "record_id": record.record_id,
            "task_type": record.task_type,
            "skill_ids": record.skill_ids,
            "tech_stack": record.tech_stack,
            "domain": record.domain,
            "problem_domain": record.problem_domain,
            "outcome": record.outcome,
            "duration_seconds": record.duration_seconds,
            "complexity": record.complexity,
            "session_id": record.session_id,
            "artifacts": record.artifacts,
            "key_patterns": record.key_patterns,
            "lessons_learned": record.lessons_learned,
            "pitfalls": record.pitfalls,
            "recommendations": record.recommendations,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

    def _dict_to_record(self, data: dict) -> ExperienceRecord:
        """Convert a dictionary to an ExperienceRecord.

        Args:
            data: Dictionary from JSON file

        Returns:
            ExperienceRecord object

        Raises:
            ValueError: If required fields are missing
        """
        # Parse datetime fields
        created_at = self._parse_datetime(data.get("created_at"))
        updated_at = self._parse_datetime(data.get("updated_at"))

        return ExperienceRecord(
            record_id=data["record_id"],
            task_type=data["task_type"],
            skill_ids=data.get("skill_ids", []),
            tech_stack=data.get("tech_stack", []),
            domain=data["domain"],
            problem_domain=data["problem_domain"],
            outcome=data["outcome"],
            duration_seconds=data["duration_seconds"],
            complexity=data.get("complexity", "medium"),
            session_id=data["session_id"],
            artifacts=data.get("artifacts", []),
            key_patterns=data.get("key_patterns", []),
            lessons_learned=data.get("lessons_learned", []),
            pitfalls=data.get("pitfalls", []),
            recommendations=data.get("recommendations", []),
            created_at=created_at,
            updated_at=updated_at,
        )

    def _parse_datetime(self, value: Any) -> datetime:
        """Parse a datetime from various formats.

        Args:
            value: Datetime value (ISO string or datetime object)

        Returns:
            datetime object
        """
        if isinstance(value, datetime):
            return value
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.now()
        else:
            return datetime.now()

    def _matches_skill_ids(self, record: ExperienceRecord, skill_ids: List[str]) -> bool:
        """Check if record matches any of the specified skill IDs.

        Args:
            record: ExperienceRecord to check
            skill_ids: List of skill IDs (OR logic)

        Returns:
            True if record has at least one of the skill IDs
        """
        return any(skill_id in record.skill_ids for skill_id in skill_ids)

    def _matches_key_patterns(self, record: ExperienceRecord, key_patterns: List[str]) -> bool:
        """Check if record contains all specified key patterns.

        Args:
            record: ExperienceRecord to check
            key_patterns: List of key patterns to match (AND logic)

        Returns:
            True if record has all key patterns
        """
        record_patterns_lower = {p.lower() for p in record.key_patterns}
        return all(pattern.lower() in record_patterns_lower for pattern in key_patterns)
