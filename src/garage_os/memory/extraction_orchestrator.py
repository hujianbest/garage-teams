"""Evidence-driven candidate extraction for Garage memory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from garage_os.memory.candidate_store import CandidateStore
from garage_os.storage.file_storage import FileStorage


def load_memory_config(storage: FileStorage) -> dict[str, bool]:
    """Load memory feature flags from platform config."""
    config = storage.read_json("config/platform.json") or {}
    memory = config.get("memory", {})
    return {
        "extraction_enabled": bool(memory.get("extraction_enabled", False)),
        "recommendation_enabled": bool(memory.get("recommendation_enabled", False)),
    }


@dataclass
class ExtractionConfig:
    """Configuration for archive-time candidate extraction."""

    min_priority_score: float = 0.5


class MemoryExtractionOrchestrator:
    """Generate candidate batches from archived session evidence."""

    def __init__(
        self,
        storage: FileStorage,
        candidate_store: CandidateStore,
        config: ExtractionConfig | None = None,
    ) -> None:
        self._storage = storage
        self._candidate_store = candidate_store
        self._config = config or ExtractionConfig()

    def extract_for_archived_session(
        self,
        archived_session: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a candidate batch for an archived session."""
        session_id = archived_session["session_id"]
        batch_id = self._build_batch_id(session_id)

        signals = self._build_signals(archived_session)
        if not signals:
            summary = self._build_summary(
                batch_id=batch_id,
                session_id=session_id,
                evaluation_summary="no_evidence",
                candidate_ids=[],
                truncated_count=0,
                metadata={"reason": "no_evidence"},
            )
            self._candidate_store.store_batch(summary)
            return summary

        try:
            candidates, truncated_count = self._generate_candidates(
                archived_session, signals
            )
        except Exception as exc:
            summary = self._build_summary(
                batch_id=batch_id,
                session_id=session_id,
                evaluation_summary="extraction_failed",
                candidate_ids=[],
                truncated_count=0,
                metadata={
                    "reason": "extraction_failed",
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )
            self._candidate_store.store_batch(summary)
            return summary
        if not candidates:
            summary = self._build_summary(
                batch_id=batch_id,
                session_id=session_id,
                evaluation_summary="evaluated_no_candidate",
                candidate_ids=[],
                truncated_count=0,
                metadata={"reason": "filtered_below_threshold"},
            )
            self._candidate_store.store_batch(summary)
            return summary

        stored_candidate_ids: list[str] = []
        for candidate in candidates:
            self._candidate_store.store_candidate(candidate)
            stored_candidate_ids.append(candidate["candidate_id"])

        summary = self._build_summary(
            batch_id=batch_id,
            session_id=session_id,
            evaluation_summary="evaluated_with_candidates",
            candidate_ids=stored_candidate_ids,
            truncated_count=truncated_count,
            metadata={"reason": "candidates_generated"},
        )
        self._candidate_store.store_batch(summary)
        return summary

    def is_extraction_enabled(self) -> bool:
        """Return whether extraction is enabled."""
        return load_memory_config(self._storage)["extraction_enabled"]

    def extract_for_archived_session_id(self, session_id: str) -> dict[str, Any]:
        """Load an archived session from disk and extract candidates for it."""
        archived = self._storage.read_json(f"sessions/archived/{session_id}/session.json")
        if archived is None:
            raise ValueError(f"Archived session not found: {session_id}")
        return self.extract_for_archived_session(archived)

    def _build_signals(self, archived_session: dict[str, Any]) -> list[dict[str, Any]]:
        """Build evidence signals from archived session payload."""
        signals: list[dict[str, Any]] = []
        context = archived_session.get("context", {})
        metadata = context.get("metadata", {})
        tags = metadata.get("tags", [])
        if isinstance(tags, list) and tags:
            signals.append(
                {
                    "kind": "metadata_tags",
                    "value": tags,
                    "priority_score": 0.62,
                }
            )

        problem_domain = metadata.get("problem_domain")
        if isinstance(problem_domain, str) and problem_domain:
            signals.append(
                {
                    "kind": "problem_domain",
                    "value": problem_domain,
                    "priority_score": 0.72,
                }
            )

        for artifact in archived_session.get("artifacts", []):
            path = artifact.get("path")
            if path:
                signals.append(
                    {
                        "kind": "artifact",
                        "value": path,
                        "priority_score": 0.81,
                    }
                )

        # Only use weaker session metadata as supplemental signals once at least
        # one stronger evidence source exists. This preserves the explicit
        # "no_evidence" branch for empty sessions while still helping real
        # archived sessions produce candidates.
        if signals:
            pack_id = archived_session.get("pack_id")
            if isinstance(pack_id, str) and pack_id:
                signals.append(
                    {
                        "kind": "pack_id",
                        "value": pack_id,
                        "priority_score": 0.58,
                    }
                )

            topic = archived_session.get("topic")
            if isinstance(topic, str) and topic:
                signals.append(
                    {
                        "kind": "topic",
                        "value": topic,
                        "priority_score": 0.56,
                    }
                )

            current_node_id = archived_session.get("current_node_id")
            if isinstance(current_node_id, str) and current_node_id:
                signals.append(
                    {
                        "kind": "current_node",
                        "value": current_node_id,
                        "priority_score": 0.57,
                    }
                )

        return signals

    def _generate_candidates(
        self,
        archived_session: dict[str, Any],
        signals: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], int]:
        """Generate candidate drafts from extracted signals."""
        session_id = archived_session["session_id"]
        topic = archived_session.get("topic", "Memory candidate")
        source_artifacts = [
            artifact.get("path")
            for artifact in archived_session.get("artifacts", [])
            if artifact.get("path")
        ]
        context = archived_session.get("context", {})
        metadata = context.get("metadata", {})
        candidate_tags: list[str] = []
        for raw_tag in metadata.get("tags", []):
            if isinstance(raw_tag, str) and raw_tag:
                candidate_tags.append(raw_tag)
        for tag in (
            archived_session.get("pack_id"),
            metadata.get("domain"),
            metadata.get("problem_domain"),
        ):
            if isinstance(tag, str) and tag:
                candidate_tags.append(tag)
        candidate_tags = list(dict.fromkeys(candidate_tags))
        problem_domain = (
            metadata.get("problem_domain")
            if isinstance(metadata.get("problem_domain"), str)
            else None
        )
        domain = (
            metadata.get("domain") if isinstance(metadata.get("domain"), str) else None
        )
        pack_id = archived_session.get("pack_id")
        if not isinstance(pack_id, str):
            pack_id = None
        generated: list[dict[str, Any]] = []
        for index, signal in enumerate(signals):
            priority_score = float(signal["priority_score"])
            if priority_score < self._config.min_priority_score:
                continue

            candidate_type = "decision"
            if signal["kind"] == "metadata_tags":
                candidate_type = "pattern"
            elif signal["kind"] == "problem_domain":
                candidate_type = "experience_summary"

            anchor = self._build_anchor(signal, session_id)
            candidate = {
                "schema_version": "1",
                "candidate_id": f"candidate-{session_id}-{index + 1:02d}",
                "candidate_type": candidate_type,
                "session_id": session_id,
                "source_artifacts": source_artifacts or [str(signal["value"])],
                "source_evidence_anchors": [anchor],
                "match_reasons": [f"{signal['kind']}:{signal['value']}"],
                "status": "pending_review",
                "priority_score": priority_score,
                "title": f"{topic} / {signal['kind']}",
                "summary": f"Candidate generated from {signal['kind']}",
                "content": f"Derived from {signal['kind']}: {signal['value']}",
                "tags": candidate_tags,
            }
            if candidate_type == "experience_summary":
                candidate.update(
                    {
                        "task_type": pack_id or "skill_execution",
                        "skill_ids": [pack_id] if pack_id else [],
                        "tech_stack": [],
                        "domain": domain or "general",
                        "problem_domain": problem_domain or pack_id or "unknown",
                        "outcome": "success",
                        "duration_seconds": 0,
                        "complexity": "medium",
                        "recommendations": [],
                    }
                )
            generated.append(candidate)

        generated.sort(key=lambda item: item["priority_score"], reverse=True)
        truncated_count = max(
            0, len(generated) - CandidateStore.MAX_PENDING_CANDIDATES
        )
        return generated[: CandidateStore.MAX_PENDING_CANDIDATES], truncated_count

    def _build_anchor(
        self, signal: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """Build a self-describing source_evidence_anchor for a signal."""
        kind = signal["kind"]
        value = signal["value"]
        if kind == "artifact":
            return {"kind": "artifact_excerpt", "ref": str(value)}
        if kind == "metadata_tags":
            return {
                "kind": "session_metadata",
                "ref": f"sessions/archived/{session_id}/session.json#tags",
                "value": list(value) if isinstance(value, list) else [str(value)],
            }
        if kind == "problem_domain":
            return {
                "kind": "session_metadata",
                "ref": f"sessions/archived/{session_id}/session.json#problem_domain",
                "value": str(value),
            }
        return {
            "kind": "session_metadata",
            "ref": f"sessions/archived/{session_id}/session.json#{kind}",
            "value": str(value),
        }

    def _build_summary(
        self,
        *,
        batch_id: str,
        session_id: str,
        evaluation_summary: str,
        candidate_ids: list[str],
        truncated_count: int,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "batch_id": batch_id,
            "session_id": session_id,
            "status": "pending_review",
            "trigger": "session_archived",
            "candidate_ids": candidate_ids,
            "truncated_count": truncated_count,
            "evaluation_summary": evaluation_summary,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata,
        }

    def _build_batch_id(self, session_id: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"batch-{timestamp}-{session_id}"
