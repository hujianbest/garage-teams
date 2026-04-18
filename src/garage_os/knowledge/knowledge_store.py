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
from typing import Optional, List, Set

from garage_os.storage.file_storage import FileStorage
from garage_os.storage.front_matter import FrontMatterParser
from garage_os.types import KnowledgeType, KnowledgeEntry


class KnowledgeStore:
    """Store and retrieve knowledge entries as markdown files.

    Uses a lazy in-memory index with secondary indexes for fast searches.
    The primary index maps file paths to entries. Secondary indexes provide
    O(1) lookups for type and tag filtering, reducing search from O(N) to
    O(K) where K is the number of matching entries.
    """

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
        # Primary index: {file_rel_path: KnowledgeEntry}
        self._index: dict[str, KnowledgeEntry] = {}
        # Secondary index: type directory -> set of file paths
        self._type_index: dict[str, set[str]] = {}
        # Secondary index: tag.lower() -> set of file paths
        self._tag_index: dict[str, set[str]] = {}
        # Pre-computed lowercase values: {file_rel_path: (topic_lower, content_lower, tags_lower_set)}
        self._lower_cache: dict[str, tuple[str, str, frozenset[str]]] = {}
        self._index_dirty: bool = True

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
        checksum = self._storage.write_text(filepath, markdown_content)

        # Incremental index update
        if not self._index_dirty:
            self._add_to_index(filepath, entry)

        return checksum

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

        Uses in-memory secondary indexes for O(1) type/tag filtering.
        Text queries scan only the candidate set from type/tag filters.

        Args:
            query: Optional text query to search in content/topic
            tags: Optional list of tags to filter by (AND logic)
            knowledge_type: Optional type filter

        Returns:
            List of matching KnowledgeEntry objects
        """
        self._ensure_index()

        # Start with all file paths, then narrow down using indexes
        candidates: Optional[set[str]] = None

        # Type filter: O(1) via _type_index
        if knowledge_type:
            dir_name = self._get_directory_for_type(knowledge_type)
            type_matches = self._type_index.get(dir_name, set())
            candidates = set(type_matches)
        else:
            # No type filter — candidates are all indexed paths
            pass

        # Tag filter: O(1) via _tag_index, intersect for AND logic
        if tags:
            for tag in tags:
                tag_matches = self._tag_index.get(tag.lower(), set())
                if candidates is not None:
                    candidates = candidates & tag_matches
                else:
                    if candidates is None:
                        candidates = set(tag_matches)
                    else:
                        candidates = candidates & tag_matches

        # If no filters at all, all entries are candidates
        if candidates is None:
            candidates = set(self._index.keys())

        # Text query: scan remaining candidates (O(K) where K = |candidates|)
        if query:
            query_lower = query.lower()
            results = []
            for fp in candidates:
                entry = self._index.get(fp)
                if entry is None:
                    continue
                lower_data = self._lower_cache.get(fp)
                if lower_data is None:
                    continue
                topic_lower, content_lower, tags_lower = lower_data
                if (query_lower in topic_lower
                        or query_lower in content_lower
                        or any(query_lower in t for t in tags_lower)):
                    results.append(entry)
            return results

        # No text query — return entries for all candidates
        return [self._index[fp] for fp in candidates if fp in self._index]

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

        # Remove old entry from index before storing updated version
        directory = self._get_directory_for_type(entry.type)
        filename = f"{entry.type.value}-{entry.id}.md"
        filepath = f"{directory}/{filename}"
        if not self._index_dirty:
            self._remove_from_index(filepath)

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

        result = self._storage.delete(filepath)

        # Incremental index update — remove entry from indexes
        if result:
            self._remove_from_index(filepath)

        return result

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

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def _ensure_index(self) -> None:
        """Rebuild the in-memory index if it is dirty."""
        if not self._index_dirty:
            return
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Load all knowledge entries from disk into the in-memory index."""
        new_index: dict[str, KnowledgeEntry] = {}
        new_type_index: dict[str, set[str]] = {}
        new_tag_index: dict[str, set[str]] = {}
        new_lower_cache: dict[str, tuple[str, str, frozenset[str]]] = {}

        for directory in self.TYPE_DIRECTORIES.values():
            type_paths: set[str] = set()
            files = self._storage.list_files(directory, "*.md")
            for file_path in files:
                try:
                    rel = str(file_path.relative_to(self._storage.base_path))
                    content = self._storage.read_text(rel)
                    if content is None:
                        continue
                    front_matter, body = FrontMatterParser.parse(content)
                    entry = self._front_matter_to_entry(front_matter, body)
                    new_index[rel] = entry
                    type_paths.add(rel)

                    # Build lowercase cache
                    new_lower_cache[rel] = (
                        entry.topic.lower(),
                        entry.content.lower(),
                        frozenset(t.lower() for t in entry.tags),
                    )

                    # Build tag index
                    for tag in entry.tags:
                        tag_lower = tag.lower()
                        if tag_lower not in new_tag_index:
                            new_tag_index[tag_lower] = set()
                        new_tag_index[tag_lower].add(rel)
                except (ValueError, OSError):
                    continue

            new_type_index[directory] = type_paths

        self._index = new_index
        self._type_index = new_type_index
        self._tag_index = new_tag_index
        self._lower_cache = new_lower_cache
        self._index_dirty = False

    def _add_to_index(self, filepath: str, entry: KnowledgeEntry) -> None:
        """Add a single entry to all indexes (incremental update after store)."""
        self._index[filepath] = entry

        # Type index
        dir_name = filepath.rsplit("/", 1)[0] if "/" in filepath else ""
        if dir_name not in self._type_index:
            self._type_index[dir_name] = set()
        self._type_index[dir_name].add(filepath)

        # Tag index
        for tag in entry.tags:
            tag_lower = tag.lower()
            if tag_lower not in self._tag_index:
                self._tag_index[tag_lower] = set()
            self._tag_index[tag_lower].add(filepath)

        # Lowercase cache
        self._lower_cache[filepath] = (
            entry.topic.lower(),
            entry.content.lower(),
            frozenset(t.lower() for t in entry.tags),
        )

    def _remove_from_index(self, filepath: str) -> None:
        """Remove a single entry from all indexes (incremental after delete/update)."""
        entry = self._index.pop(filepath, None)
        if entry is None:
            return

        # Type index
        dir_name = filepath.rsplit("/", 1)[0] if "/" in filepath else ""
        if dir_name in self._type_index:
            self._type_index[dir_name].discard(filepath)

        # Tag index
        for tag in entry.tags:
            tag_lower = tag.lower()
            if tag_lower in self._tag_index:
                self._tag_index[tag_lower].discard(filepath)
                if not self._tag_index[tag_lower]:
                    del self._tag_index[tag_lower]

        # Lowercase cache
        self._lower_cache.pop(filepath, None)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

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
            "source_evidence_anchor": entry.source_evidence_anchor,
            "confirmation_ref": entry.confirmation_ref,
            "published_from_candidate": entry.published_from_candidate,
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
            source_evidence_anchor=fm.get("source_evidence_anchor"),
            confirmation_ref=fm.get("confirmation_ref"),
            published_from_candidate=fm.get("published_from_candidate"),
            front_matter=fm,  # Store original front matter
        )
