"""
Knowledge Integration for Garage Agent OS.

Integrates KnowledgeStore and ExperienceIndex to support cross-module
retrieval, manual knowledge extraction, and data consistency maintenance.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.types import (
    KnowledgeType,
    KnowledgeEntry,
    ExperienceRecord,
)


class KnowledgeIntegration:
    """Integration layer between knowledge store and experience index.

    Provides cross-module functionality including:
    - Finding related knowledge based on experience records
    - Extracting knowledge from completed sessions
    - Maintaining data consistency across modules
    """

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        experience_index: ExperienceIndex,
    ):
        """Initialize the integration layer.

        Args:
            knowledge_store: KnowledgeStore instance for knowledge operations
            experience_index: ExperienceIndex instance for experience operations
        """
        self._knowledge_store = knowledge_store
        self._experience_index = experience_index

    def find_related_knowledge(self, experience_id: str) -> List[KnowledgeEntry]:
        """Find knowledge entries related to an experience record.

        Searches for knowledge entries that match the experience record's
        skill IDs, key patterns, domain, and problem domain.

        Matching criteria:
        - Knowledge tags match experience skill_ids
        - Knowledge tags match experience key_patterns
        - Knowledge topic matches experience domain/problem_domain

        Args:
            experience_id: ID of the experience record

        Returns:
            List of related KnowledgeEntry objects (empty list if experience not found)
        """
        # Retrieve the experience record
        experience = self._experience_index.retrieve(experience_id)
        if experience is None:
            return []

        # Build search criteria from experience
        search_tags: List[str] = []

        # Add skill IDs as search tags
        search_tags.extend(experience.skill_ids)

        # Add key patterns as search tags
        search_tags.extend(experience.key_patterns)

        # Add domain and problem domain as search tags
        search_tags.append(experience.domain)
        search_tags.append(experience.problem_domain)

        # Remove duplicates and empty strings
        search_tags = list(set(tag for tag in search_tags if tag))

        # Search for knowledge entries matching any of the tags
        # We use the KnowledgeStore search with tags to find matches
        all_knowledge = self._knowledge_store.list_entries()

        # Filter knowledge entries by relevance
        related = []
        for entry in all_knowledge:
            # Calculate relevance score
            relevance = self._calculate_relevance(entry, experience)
            if relevance > 0:
                related.append(entry)

        # Sort by relevance (descending)
        related.sort(key=lambda e: self._calculate_relevance(e, experience), reverse=True)

        return related

    def extract_from_session(
        self,
        session_id: str,
        experience_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """Extract and store knowledge from a completed session.

        Creates both an experience record and a knowledge entry from the
        provided session data.

        Args:
            session_id: ID of the completed session
            experience_data: Dictionary containing experience and knowledge data

        Returns:
            Dictionary with keys:
                - experience_record_id: ID of the created experience record
                - knowledge_entry_id: ID of the created knowledge entry

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = [
            "task_type",
            "skill_ids",
            "tech_stack",
            "domain",
            "problem_domain",
            "outcome",
            "duration_seconds",
            "complexity",
        ]
        for field in required_fields:
            if field not in experience_data:
                raise ValueError(f"Missing required field: {field}")

        # Generate IDs
        experience_id = str(uuid.uuid4())
        knowledge_id = str(uuid.uuid4())

        # Determine knowledge type (default to SOLUTION)
        knowledge_type_str = experience_data.get("knowledge_type", "solution")
        try:
            knowledge_type = KnowledgeType(knowledge_type_str)
        except ValueError:
            knowledge_type = KnowledgeType.SOLUTION

        # Extract knowledge-specific fields
        if knowledge_type == KnowledgeType.DECISION:
            topic = experience_data.get(
                "decision_topic",
                f"Decision: {experience_data['task_type']}",
            )
            content = experience_data.get(
                "decision_rationale",
                f"Decision made during {experience_data['task_type']}",
            )
        elif knowledge_type == KnowledgeType.PATTERN:
            topic = experience_data.get(
                "pattern_topic",
                f"Pattern: {experience_data['task_type']}",
            )
            content = experience_data.get(
                "pattern_description",
                f"Pattern identified during {experience_data['task_type']}",
            )
        else:  # SOLUTION
            topic = f"Solution: {experience_data['task_type']}"
            content_parts = []
            if experience_data.get("lessons_learned"):
                content_parts.append("## Lessons Learned\n\n")
                content_parts.extend(f"- {lesson}" for lesson in experience_data["lessons_learned"])
            if experience_data.get("recommendations"):
                content_parts.append("\n\n## Recommendations\n\n")
                content_parts.extend(f"- {rec}" for rec in experience_data["recommendations"])
            content = "\n".join(content_parts) if content_parts else f"Solution for {experience_data['task_type']}"

        # Build tags from various sources
        tags = [
            experience_data["domain"],
            experience_data["problem_domain"],
        ]
        tags.extend(experience_data["skill_ids"])
        tags.extend(experience_data.get("key_patterns", []))

        # Create experience record
        now = datetime.now()
        experience = ExperienceRecord(
            record_id=experience_id,
            task_type=experience_data["task_type"],
            skill_ids=experience_data["skill_ids"],
            tech_stack=experience_data["tech_stack"],
            domain=experience_data["domain"],
            problem_domain=experience_data["problem_domain"],
            outcome=experience_data["outcome"],
            duration_seconds=experience_data["duration_seconds"],
            complexity=experience_data["complexity"],
            session_id=session_id,
            artifacts=experience_data.get("artifacts", []),
            key_patterns=experience_data.get("key_patterns", []),
            lessons_learned=experience_data.get("lessons_learned", []),
            pitfalls=experience_data.get("pitfalls", []),
            recommendations=experience_data.get("recommendations", []),
            created_at=now,
            updated_at=now,
        )

        # Create knowledge entry
        knowledge = KnowledgeEntry(
            id=knowledge_id,
            type=knowledge_type,
            topic=topic,
            date=now,
            tags=tags,
            content=content,
            status="active",
            version=1,
            source_session=session_id,
            source_artifact=experience_data.get("artifacts", [None])[0] if experience_data.get("artifacts") else None,
        )

        # Store both records
        self._experience_index.store(experience)
        self._knowledge_store.store(knowledge)
        # F014 ADR-D14-3 Path 4/4: workflow recall cache invalidate
        try:
            from garage_os.workflow_recall.pipeline import WorkflowRecallHook
            WorkflowRecallHook.invalidate(self._experience_index._storage.base_path)
        except Exception:
            pass

        return {
            "experience_record_id": experience_id,
            "knowledge_entry_id": knowledge_id,
        }

    def remove_knowledge_cascade(
        self,
        knowledge_type: KnowledgeType,
        knowledge_id: str,
    ) -> bool:
        """Remove a knowledge entry and update dependent experience records.

        When a knowledge entry is deleted, this method removes references
        to it from experience records' artifacts lists to maintain consistency.

        Args:
            knowledge_type: Type of the knowledge entry
            knowledge_id: ID of the knowledge entry to remove

        Returns:
            True if knowledge was removed, False if it didn't exist
        """
        # Delete the knowledge entry
        deleted = self._knowledge_store.delete(knowledge_type, knowledge_id)

        if not deleted:
            return False

        # Update experience records that reference this knowledge
        all_experiences = self._experience_index.list_records()

        for experience in all_experiences:
            # Check if experience references the deleted knowledge
            if knowledge_id in experience.artifacts:
                # Remove the reference
                updated_artifacts = [aid for aid in experience.artifacts if aid != knowledge_id]

                # Update the experience record
                if len(updated_artifacts) != len(experience.artifacts):
                    experience.artifacts = updated_artifacts
                    self._experience_index.update(experience)

        return True

    def _calculate_relevance(
        self,
        entry: KnowledgeEntry,
        experience: ExperienceRecord,
    ) -> float:
        """Calculate relevance score for a knowledge entry relative to an experience.

        Higher score means more relevant. Score is based on:
        - Tag matches with skills, key patterns, domain
        - Topic/content text matches

        Uses fuzzy matching to handle partial matches (e.g., "data-access" matches "data-access-layer").

        Args:
            entry: KnowledgeEntry to score
            experience: ExperienceRecord to compare against

        Returns:
            Relevance score (0.0 to 1.0+)
        """
        score = 0.0

        # Convert to lowercase for case-insensitive matching
        entry_tags = [tag.lower() for tag in entry.tags]
        entry_text = (entry.topic + " " + entry.content).lower()

        # Build search terms from experience
        search_terms = []
        search_terms.extend([skill.lower() for skill in experience.skill_ids])
        search_terms.extend([pattern.lower() for pattern in experience.key_patterns])
        search_terms.append(experience.domain.lower())
        search_terms.append(experience.problem_domain.lower())

        # Match each search term against entry tags and text
        for term in search_terms:
            # Exact tag match (highest weight)
            if term in entry_tags:
                score += 0.5

            # Partial tag match (e.g., "data-access" matches "data-access-layer")
            for tag in entry_tags:
                if term in tag or tag in term:
                    score += 0.3
                    break  # Only count once per term

            # Text match in topic or content (lower weight)
            if term in entry_text:
                score += 0.15

        return score
