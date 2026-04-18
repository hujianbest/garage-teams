"""Storage layer for memory candidate batches, drafts, and confirmation records."""

from __future__ import annotations

from typing import Any

from garage_os.storage.file_storage import FileStorage
from garage_os.storage.front_matter import FrontMatterParser

from garage_os.memory.types import ALLOWED_CANDIDATE_TYPES


class CandidateStore:
    """Persist candidate batches, candidate drafts, and confirmation records."""

    BATCHES_DIR = "memory/candidates/batches"
    ITEMS_DIR = "memory/candidates/items"
    CONFIRMATIONS_DIR = "memory/confirmations"
    MAX_PENDING_CANDIDATES = 5

    def __init__(self, storage: FileStorage) -> None:
        self._storage = storage
        self._ensure_directories()

    def store_batch(self, batch: dict[str, Any]) -> str:
        """Store a candidate batch as JSON after validating queue constraints."""
        candidate_ids = batch.get("candidate_ids", [])
        status = batch.get("status")
        if status == "pending_review" and len(candidate_ids) > self.MAX_PENDING_CANDIDATES:
            raise ValueError("pending_review batches may contain at most 5 candidates")

        batch_id = batch["batch_id"]
        return self._storage.write_json(f"{self.BATCHES_DIR}/{batch_id}.json", batch)

    def retrieve_batch(self, batch_id: str) -> dict[str, Any] | None:
        """Retrieve a stored batch by ID."""
        return self._storage.read_json(f"{self.BATCHES_DIR}/{batch_id}.json")

    def store_candidate(self, candidate: dict[str, Any]) -> str:
        """Store a candidate draft as markdown with YAML front matter."""
        candidate_type = candidate.get("candidate_type")
        if candidate_type not in ALLOWED_CANDIDATE_TYPES:
            raise ValueError("candidate_type must be one of the supported values")

        candidate_id = candidate["candidate_id"]
        content = candidate.get("content", "")
        front_matter = {k: v for k, v in candidate.items() if k != "content"}
        rendered = FrontMatterParser.render(front_matter, content)
        return self._storage.write_text(f"{self.ITEMS_DIR}/{candidate_id}.md", rendered)

    def retrieve_candidate(self, candidate_id: str) -> dict[str, Any] | None:
        """Retrieve a stored candidate draft by ID."""
        content = self._storage.read_text(f"{self.ITEMS_DIR}/{candidate_id}.md")
        if content is None:
            return None

        front_matter, body = FrontMatterParser.parse(content)
        front_matter["content"] = body
        return front_matter

    def list_candidates_by_status(self, status: str) -> list[dict[str, Any]]:
        """List all candidate drafts matching a status."""
        candidates: list[dict[str, Any]] = []
        for path in self._storage.list_files(self.ITEMS_DIR, "*.md"):
            content = self._storage.read_text(f"{self.ITEMS_DIR}/{path.name}")
            if content is None:
                continue
            front_matter, body = FrontMatterParser.parse(content)
            if front_matter.get("status") != status:
                continue
            front_matter["content"] = body
            candidates.append(front_matter)
        return candidates

    def update_candidate(self, candidate_id: str, updates: dict[str, Any]) -> str:
        """Update a stored candidate draft."""
        existing = self.retrieve_candidate(candidate_id)
        if existing is None:
            raise FileNotFoundError(f"Candidate not found: {candidate_id}")
        existing.update(updates)
        return self.store_candidate(existing)

    def store_confirmation(self, confirmation: dict[str, Any]) -> str:
        """Store a confirmation record as JSON."""
        batch_id = confirmation["batch_id"]
        return self._storage.write_json(
            f"{self.CONFIRMATIONS_DIR}/{batch_id}.json",
            confirmation,
        )

    def retrieve_confirmation(self, batch_id: str) -> dict[str, Any] | None:
        """Retrieve a confirmation record by batch ID."""
        return self._storage.read_json(f"{self.CONFIRMATIONS_DIR}/{batch_id}.json")

    def _ensure_directories(self) -> None:
        """Create the required memory directories."""
        self._storage.ensure_dir(self.BATCHES_DIR)
        self._storage.ensure_dir(self.ITEMS_DIR)
        self._storage.ensure_dir(self.CONFIRMATIONS_DIR)
