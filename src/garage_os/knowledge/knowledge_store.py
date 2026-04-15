"""
Knowledge Store for Garage Agent OS.

Stores knowledge entries as markdown files with YAML front matter.
Directory structure:
- .garage/knowledge/decisions/    <- DECISION type entries
- .garage/knowledge/patterns/     <- PATTERN type entries
- .garage/knowledge/solutions/    <- SOLUTION type entries
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List

from garage_os.storage.file_storage import FileStorage
from garage_os.storage.front_matter import FrontMatterParser
from garage_os.types import KnowledgeType, KnowledgeEntry


class KnowledgeStore:
    """Store and retrieve knowledge entries as markdown files."""

    # Directory mappings for each knowledge type
    TYPE_DIRECTORIES = {
        KnowledgeType.DECISION: "knowledge/decisions",
        KnowledgeType.PATTERN: "knowledge/patterns",
        KnowledgeType.SOLUTION: "knowledge/solutions",
    }

    def __init__(self, storage: FileStorage):
        """Initialize knowledge store with file storage backend.

        Args:
            storage: FileStorage instance for file operations
        """
        self._storage = storage

    def store(self, entry: KnowledgeEntry) -> str:
        """Store a knowledge entry as a markdown file.

        Args:
            entry: KnowledgeEntry to store

        Returns:
            SHA-256 checksum of the written content

        Raises:
            ValueError: If entry type is invalid
        """
        directory = self._get_directory_for_type(entry.type)
        self._storage.ensure_dir(directory)

        # Build filename: <type>-<id>.md
        filename = f"{entry.type.value}-{entry.id}.md"
        filepath = f"{directory}/{filename}"

        # Convert entry to front matter + content
        front_matter = self._entry_to_front_matter(entry)
        content = entry.content

        # Render markdown with front matter and write atomically
        markdown_content = FrontMatterParser.render(front_matter, content)
        return self._storage.write_text(filepath, markdown_content)

    def retrieve(self, knowledge_type: KnowledgeType, entry_id: str) -> Optional[KnowledgeEntry]:
        """Retrieve a knowledge entry by type and ID.

        Args:
            knowledge_type: Type of knowledge entry
            entry_id: Unique identifier for the entry

        Returns:
            KnowledgeEntry if found, None otherwise
        """
        directory = self._get_directory_for_type(knowledge_type)
        filename = f"{knowledge_type.value}-{entry_id}.md"
        filepath = f"{directory}/{filename}"

        content = self._storage.read_text(filepath)
        if content is None:
            return None

        try:
            front_matter, body = FrontMatterParser.parse(content)
            return self._front_matter_to_entry(front_matter, body)
        except ValueError:
            # File exists but has invalid front matter
            return None

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        knowledge_type: Optional[KnowledgeType] = None,
    ) -> List[KnowledgeEntry]:
        """Search knowledge entries by query, tags, and/or type.

        Args:
            query: Optional text query to search in content/topic
            tags: Optional list of tags to filter by (AND logic)
            knowledge_type: Optional type filter

        Returns:
            List of matching KnowledgeEntry objects
        """
        entries = []

        # Determine which directories to search
        if knowledge_type:
            directories = [self._get_directory_for_type(knowledge_type)]
        else:
            directories = list(self.TYPE_DIRECTORIES.values())

        # Collect all entries from relevant directories
        for directory in directories:
            files = self._storage.list_files(directory, "*.md")
            for file_path in files:
                # Read and parse each file
                try:
                    content = self._storage.read_text(str(file_path.relative_to(self._storage.base_path)))
                    if content is None:
                        continue

                    front_matter, body = FrontMatterParser.parse(content)
                    entry = self._front_matter_to_entry(front_matter, body)

                    # Apply filters
                    if query and not self._matches_query(entry, query):
                        continue
                    if tags and not self._matches_tags(entry, tags):
                        continue

                    entries.append(entry)
                except (ValueError, OSError):
                    # Skip invalid/unreadable files
                    continue

        return entries

    def update(self, entry: KnowledgeEntry) -> str:
        """Update an existing knowledge entry.

        Args:
            entry: KnowledgeEntry with updated data

        Returns:
            SHA-256 checksum of the updated content

        Raises:
            ValueError: If entry type is invalid
        """
        # Increment version and update timestamp
        entry.version += 1

        # Store the updated entry (will overwrite existing file)
        return self.store(entry)

    def delete(self, knowledge_type: KnowledgeType, entry_id: str) -> bool:
        """Delete a knowledge entry.

        Args:
            knowledge_type: Type of knowledge entry
            entry_id: Unique identifier for the entry

        Returns:
            True if entry was deleted, False if it didn't exist
        """
        directory = self._get_directory_for_type(knowledge_type)
        filename = f"{knowledge_type.value}-{entry_id}.md"
        filepath = f"{directory}/{filename}"

        return self._storage.delete(filepath)

    def list_entries(self, knowledge_type: Optional[KnowledgeType] = None) -> List[KnowledgeEntry]:
        """List all knowledge entries, optionally filtered by type.

        Args:
            knowledge_type: Optional type filter

        Returns:
            List of all matching KnowledgeEntry objects
        """
        return self.search(query=None, tags=None, knowledge_type=knowledge_type)

    def _get_directory_for_type(self, knowledge_type: KnowledgeType) -> str:
        """Get directory path for a knowledge type.

        Args:
            knowledge_type: Type of knowledge entry

        Returns:
            Directory path relative to storage base

        Raises:
            ValueError: If type is not valid
        """
        if knowledge_type not in self.TYPE_DIRECTORIES:
            raise ValueError(f"Unknown knowledge type: {knowledge_type}")
        return self.TYPE_DIRECTORIES[knowledge_type]

    def _entry_to_front_matter(self, entry: KnowledgeEntry) -> dict:
        """Convert a KnowledgeEntry to front matter dictionary.

        Args:
            entry: KnowledgeEntry to convert

        Returns:
            Dictionary suitable for YAML front matter
        """
        return {
            "id": entry.id,
            "type": entry.type.value,
            "topic": entry.topic,
            "date": entry.date.isoformat(),
            "tags": entry.tags,
            "status": entry.status,
            "version": entry.version,
            "related_decisions": entry.related_decisions,
            "related_tasks": entry.related_tasks,
            "source_session": entry.source_session,
            "source_artifact": entry.source_artifact,
        }

    def _front_matter_to_entry(self, fm: dict, content: str) -> KnowledgeEntry:
        """Convert front matter + content to KnowledgeEntry.

        Args:
            fm: Front matter dictionary
            content: Markdown body content

        Returns:
            KnowledgeEntry object

        Raises:
            ValueError: If front matter is invalid
        """
        # Parse date from ISO format string
        date_str = fm.get("date")
        if isinstance(date_str, str):
            date = datetime.fromisoformat(date_str)
        elif isinstance(date_str, datetime):
            date = date_str
        else:
            date = datetime.now()

        # Parse knowledge type
        type_str = fm.get("type", "solution")
        try:
            knowledge_type = KnowledgeType(type_str)
        except ValueError:
            knowledge_type = KnowledgeType.SOLUTION

        return KnowledgeEntry(
            id=fm.get("id", "unknown"),
            type=knowledge_type,
            topic=fm.get("topic", ""),
            date=date,
            tags=fm.get("tags", []),
            content=content,
            status=fm.get("status", "active"),
            version=fm.get("version", 1),
            related_decisions=fm.get("related_decisions", []),
            related_tasks=fm.get("related_tasks", []),
            source_session=fm.get("source_session"),
            source_artifact=fm.get("source_artifact"),
            front_matter=fm,  # Store original front matter
        )

    def _matches_query(self, entry: KnowledgeEntry, query: str) -> bool:
        """Check if entry matches text query.

        Args:
            entry: KnowledgeEntry to check
            query: Query string

        Returns:
            True if entry matches query
        """
        query_lower = query.lower()
        return (
            query_lower in entry.topic.lower()
            or query_lower in entry.content.lower()
            or any(query_lower in tag.lower() for tag in entry.tags)
        )

    def _matches_tags(self, entry: KnowledgeEntry, tags: List[str]) -> bool:
        """Check if entry contains all specified tags.

        Args:
            entry: KnowledgeEntry to check
            tags: List of tags to match (AND logic)

        Returns:
            True if entry has all tags
        """
        entry_tags_lower = {tag.lower() for tag in entry.tags}
        return all(tag.lower() in entry_tags_lower for tag in tags)
