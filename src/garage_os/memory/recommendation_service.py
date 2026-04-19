"""Recommendation services for Garage memory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.types import KnowledgeEntry


@dataclass
class RecommendationContextBuilder:
    """Build richer recommendation context from runtime inputs."""

    def build(
        self,
        skill_name: str,
        params: dict[str, Any] | None = None,
        session_topic: str | None = None,
        session_metadata: dict[str, Any] | None = None,
        repo_state: dict[str, Any] | None = None,
        artifact_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build a recommendation context with graceful degradation."""
        params = params or {}
        session_metadata = session_metadata or {}
        repo_state = repo_state or {}
        tags = list(params.get("tags", []))
        if not isinstance(tags, list):
            tags = []

        return {
            "skill_name": skill_name,
            "domain": params.get("domain"),
            "problem_domain": params.get("problem_domain") or session_metadata.get("problem_domain"),
            "tags": tags,
            "session_topic": session_topic,
            "artifact_paths": artifact_paths or [],
            "repo_state": repo_state,
        }

    def build_from_query(
        self,
        query: str,
        tags: list[str] | None = None,
        domain: str | None = None,
    ) -> dict[str, Any]:
        """Build a context from a user `garage recommend` query (F006 FR-601).

        Non-breaking complement to :py:meth:`build`. The original ``build``
        signature, behavior, and call sites (`garage run` flow, F003 / F004
        skill-execution path) are intentionally unchanged (see F006 CON-602 /
        CON-605).

        Maps the query string into a context dict shaped identically to what
        :py:meth:`RecommendationService.recommend` already consumes:

        - ``query`` is split on whitespace into tokens; tokens become the
          ``tags`` field (where the existing ``recommend()`` scoring already
          checks tag membership).
        - ``skill_name`` is set to ``tokens[0]`` (or empty string when the
          query is blank) so the existing tag/skill scoring path also fires.
        - ``--tag`` overrides from the CLI are appended to the tag list.
        - ``--domain`` populates ``domain``.
        - ``session_topic`` carries the raw query for later display / debugging.

        ``problem_domain`` is intentionally left None — the user is querying
        ad-hoc, not from inside an active session.
        """
        tokens = [t for t in (query or "").split() if t]
        merged_tags: list[str] = list(tokens)
        if tags:
            merged_tags.extend(tags)
        return {
            "skill_name": tokens[0] if tokens else "",
            "domain": domain,
            "problem_domain": None,
            "tags": merged_tags,
            "session_topic": query,
            "artifact_paths": [],
            "repo_state": {},
        }


class RecommendationService:
    """Return ranked published knowledge / experience recommendations."""

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        experience_index: ExperienceIndex,
        enabled: bool = True,
    ) -> None:
        self._knowledge_store = knowledge_store
        self._experience_index = experience_index
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """Return whether recommendation queries should run."""
        return self._enabled

    def recommend(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Recommend published entries based on heuristics."""
        skill_name = (context.get("skill_name") or "").lower()
        domain = (context.get("domain") or "").lower()
        problem_domain = (context.get("problem_domain") or "").lower()
        tags = [str(tag).lower() for tag in context.get("tags", [])]

        candidates = self._knowledge_store.list_entries()
        results: list[dict[str, Any]] = []
        for entry in candidates:
            score = 0.0
            reasons: list[str] = []
            entry_tags = [tag.lower() for tag in entry.tags]
            entry_text = f"{entry.topic} {entry.content}".lower()

            if skill_name and skill_name in entry_tags:
                score += 1.0
                reasons.append(f"skill:{skill_name}")
            elif skill_name and skill_name in entry_text:
                score += 0.5
                reasons.append(f"skill-text:{skill_name}")

            if domain and domain in entry_tags:
                score += 0.8
                reasons.append(f"domain:{domain}")
            if problem_domain and problem_domain in entry_tags:
                score += 0.8
                reasons.append(f"problem_domain:{problem_domain}")

            for tag in tags:
                if tag in entry_tags:
                    score += 0.6
                    reasons.append(f"tag:{tag}")

            if score <= 0:
                continue
            results.append(
                {
                    "entry_id": entry.id,
                    "entry_type": entry.type.value,
                    "title": entry.topic,
                    "score": score,
                    "match_reasons": reasons,
                    "source_session": entry.source_session,
                }
            )

        if results:
            if not domain and not problem_domain and not tags:
                for item in results:
                    if "skill_name_only" not in item["match_reasons"]:
                        item["match_reasons"].append("skill_name_only")
            results.sort(key=lambda item: item["score"], reverse=True)
            return results

        if skill_name:
            fallback = [
                entry for entry in candidates
                if skill_name in entry.topic.lower() or skill_name in [tag.lower() for tag in entry.tags]
            ]
            if fallback:
                return [
                    {
                        "entry_id": entry.id,
                        "entry_type": entry.type.value,
                        "title": entry.topic,
                        "score": 0.1,
                        "match_reasons": ["skill_name_only"],
                        "source_session": entry.source_session,
                    }
                    for entry in fallback
                ]

        return []
