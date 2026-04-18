"""Conflict detection for publishing memory candidates."""

from __future__ import annotations

from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.types import KnowledgeEntry


class ConflictDetector:
    """Detect similar published knowledge before a candidate is promoted."""

    def __init__(self, knowledge_store: KnowledgeStore) -> None:
        self._knowledge_store = knowledge_store

    def detect(self, title: str, tags: list[str]) -> dict[str, object]:
        """Return a simple publication strategy recommendation."""
        entries = self._knowledge_store.list_entries()
        title_lower = title.lower()
        tag_set = {tag.lower() for tag in tags}

        similar: list[KnowledgeEntry] = []
        for entry in entries:
            entry_tags = {tag.lower() for tag in entry.tags}
            if title_lower in entry.topic.lower() or tag_set.intersection(entry_tags):
                similar.append(entry)

        if not similar:
            return {"strategy": "coexist", "similar_entries": []}

        return {
            "strategy": "supersede",
            "similar_entries": [entry.id for entry in similar],
        }
