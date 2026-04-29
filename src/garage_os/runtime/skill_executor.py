"""Skill Executor for garage-agent.

This module implements the SkillExecutor class, which is responsible for
executing AHE workflow skills, managing execution context, integrating
knowledge base queries, and coordinating state transitions.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Dict

from garage_os.adapter.host_adapter import HostAdapterProtocol
from garage_os.memory.recommendation_service import (
    RecommendationContextBuilder,
    RecommendationService,
)
from garage_os.runtime.session_manager import SessionManager
from garage_os.runtime.state_machine import StateMachine
from garage_os.runtime.error_handler import ErrorHandler, ErrorLogEntry
from garage_os.knowledge.integration import KnowledgeIntegration
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.storage.file_storage import FileStorage
from garage_os.types import (
    SessionState,
    SessionMetadata,
    ErrorCategory,
    KnowledgeEntry,
)

logger = logging.getLogger(__name__)


@dataclass
class SkillExecutionResult:
    """Result of a skill execution.

    Attributes:
        success: Whether the execution succeeded
        skill_name: Name of the executed skill
        session_id: Session identifier
        output: Output from skill execution (if successful)
        error_entry: Error log entry (if failed)
        artifacts: List of artifacts produced (if any)
        state_transitions: List of state transitions during execution
        related_knowledge: Related knowledge entries queried (if any)
    """

    success: bool
    skill_name: str
    session_id: str
    output: Optional[Dict[str, Any]] = None
    error_entry: Optional[ErrorLogEntry] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    state_transitions: List[str] = field(default_factory=list)
    related_knowledge: List[KnowledgeEntry] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SkillMetadata:
    """Metadata about a skill.

    Attributes:
        name: Skill name
        description: Skill description
        parameters: List of parameter names
        required_params: List of required parameter names
        optional_params: List of optional parameter names
        returns: Description of return value
        pack_id: Pack identifier
    """

    name: str
    description: str
    parameters: List[str] = field(default_factory=list)
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    returns: str = ""
    pack_id: str = ""


class SkillExecutor:
    """Execute AHE workflow skills with state management and error handling.

    The SkillExecutor is responsible for:
    - Executing skills through the host adapter
    - Managing session state transitions
    - Handling errors with classification and retry logic
    - Integrating knowledge base queries during execution
    - Managing skill pause/resume for user input scenarios
    """

    def __init__(
        self,
        host_adapter: HostAdapterProtocol,
        session_manager: SessionManager,
        state_machine: StateMachine,
        error_handler: ErrorHandler,
        knowledge_integration: Optional[KnowledgeIntegration] = None,
        recommendation_service: Optional[RecommendationService] = None,
    ):
        """Initialize the SkillExecutor.

        Args:
            host_adapter: Host adapter for invoking skills
            session_manager: Session manager for session operations
            state_machine: State machine for managing state transitions
            error_handler: Error handler for error classification and retry
            knowledge_integration: Optional knowledge integration for queries
        """
        self._host_adapter = host_adapter
        self._session_manager = session_manager
        self._state_machine = state_machine
        self._error_handler = error_handler
        self._knowledge_integration = knowledge_integration
        self._recommendation_service = recommendation_service

        # Track execution context for resume operations
        self._execution_contexts: Dict[str, Dict[str, Any]] = {}
        self._recommendation_context_builder = RecommendationContextBuilder()

    def execute_skill(
        self,
        skill_name: str,
        params: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        recommendation_service: Optional[RecommendationService] = None,
    ) -> SkillExecutionResult:
        """Execute a skill and manage state transitions.

        This method:
        1. Transitions state from IDLE to RUNNING
        2. Queries related knowledge (if integration available)
        3. Executes the skill via host adapter with retry logic
        4. Handles errors and classifies them
        5. Transitions to COMPLETED, FAILED, or PAUSED based on outcome
        6. Records artifacts produced by the skill

        Args:
            skill_name: Name of the skill to execute
            params: Optional parameters for the skill
            session_id: Optional session identifier (uses current if None)

        Returns:
            SkillExecutionResult containing execution outcome
        """
        params = params or {}
        state_transitions: List[str] = []
        related_knowledge: List[KnowledgeEntry] = []
        recommendations: List[Dict[str, Any]] = []

        try:
            # Step 1: Transition to RUNNING
            transition = self._state_machine.transition(
                SessionState.RUNNING,
                reason=f"Executing skill: {skill_name}",
                metadata={"skill_name": skill_name, "params": params},
            )
            state_transitions.append(f"{transition.from_state.value} -> {transition.to_state.value}")

            # Step 2: Query related knowledge if available
            if self._knowledge_integration:
                # For knowledge lookup, we use the skill_name as a search term
                # In a full implementation, this would use experience records
                all_knowledge = self._knowledge_integration._knowledge_store.list_entries()
                # Filter knowledge entries matching the skill name
                related_knowledge = [
                    entry for entry in all_knowledge
                    if skill_name.lower() in entry.topic.lower() or
                       any(skill_name.lower() in tag.lower() for tag in entry.tags)
                ]

            session_topic, session_metadata = self._get_session_context(session_id)
            session_metadata = dict(session_metadata)
            session_metadata = self._merge_recommendation_metadata(session_metadata, params)
            self._persist_session_runtime_context(session_id, SessionState.RUNNING, session_metadata)

            # Step 2.5: Query recommendations if available
            recommendation_service = recommendation_service or self._build_recommendation_service()
            if recommendation_service is not None and self._recommendation_service_enabled(
                recommendation_service
            ):
                repo_state = self._safe_get_repository_state()
                recommendation_context = self._recommendation_context_builder.build(
                    skill_name=skill_name,
                    params=params,
                    session_topic=session_topic,
                    session_metadata=session_metadata,
                    repo_state=repo_state,
                    artifact_paths=[],
                )
                recommendations = recommendation_service.recommend(recommendation_context)

            # Step 3: Execute skill with retry logic
            def execute_operation():
                return self._host_adapter.invoke_skill(skill_name, params)

            result, error_entry = self._error_handler.execute_with_retry(
                execute_operation,
                session_id=session_id,
                context={"skill_name": skill_name, "params": params},
            )

            # Step 4: Handle error if execution failed
            if error_entry is not None:
                # Check if this is a USER_INTERVENTION error (needs user input)
                if error_entry.category == ErrorCategory.USER_INTERVENTION:
                    # Transition to PAUSED
                    transition = self._state_machine.transition(
                        SessionState.PAUSED,
                        reason="Waiting for user input",
                        metadata={"skill_name": skill_name, "error": error_entry.message},
                    )
                    state_transitions.append(f"{transition.from_state.value} -> {transition.to_state.value}")

                    # Store execution context for resume
                    self._execution_contexts[session_id or "default"] = {
                        "skill_name": skill_name,
                        "params": params,
                        "session_id": session_id,
                    }

                    return SkillExecutionResult(
                        success=False,
                        skill_name=skill_name,
                        session_id=session_id or "unknown",
                        error_entry=error_entry,
                        state_transitions=state_transitions,
                        related_knowledge=related_knowledge,
                    recommendations=recommendations,
                    )

                # For other errors, transition to FAILED
                transition = self._state_machine.transition(
                    SessionState.FAILED,
                    reason=f"Skill execution failed: {error_entry.message}",
                    metadata={"skill_name": skill_name, "error_category": error_entry.category.value},
                )
                state_transitions.append(f"{transition.from_state.value} -> {transition.to_state.value}")

                return SkillExecutionResult(
                    success=False,
                    skill_name=skill_name,
                    session_id=session_id or "unknown",
                    error_entry=error_entry,
                    state_transitions=state_transitions,
                    related_knowledge=related_knowledge,
                    recommendations=recommendations,
                )

            # Step 5: Extract artifacts from result if present
            artifacts = []
            if isinstance(result, dict):
                # Check if result contains artifacts at top level
                if "artifacts" in result:
                    artifacts = result["artifacts"]
                # Check in result field if present
                elif "result" in result and isinstance(result["result"], dict):
                    inner_result = result["result"]
                    if "artifacts" in inner_result:
                        artifacts = inner_result["artifacts"]
                    # Check for common artifact fields
                    elif "output_files" in inner_result:
                        artifacts = inner_result["output_files"]
                    elif "files" in inner_result:
                        artifacts = inner_result["files"]
                # Check for common artifact fields at top level
                elif "output_files" in result:
                    artifacts = result["output_files"]
                elif "files" in result:
                    artifacts = result["files"]

            self._persist_session_artifacts(session_id, artifacts)
            self._persist_session_runtime_context(
                session_id,
                SessionState.COMPLETED,
                session_metadata,
            )

            # Step 6: Transition to COMPLETED
            transition = self._state_machine.transition(
                SessionState.COMPLETED,
                reason=f"Skill execution completed: {skill_name}",
                metadata={"skill_name": skill_name},
            )
            state_transitions.append(f"{transition.from_state.value} -> {transition.to_state.value}")

            return SkillExecutionResult(
                success=True,
                skill_name=skill_name,
                session_id=session_id or "unknown",
                output=result,
                artifacts=artifacts if isinstance(artifacts, list) else [],
                state_transitions=state_transitions,
                related_knowledge=related_knowledge,
                recommendations=recommendations,
            )

        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error during skill execution: {e}", exc_info=True)
            category = self._error_handler.classify_error(e)
            error_entry = self._error_handler.log_error(e, category, session_id, {"skill_name": skill_name})

            # Try to transition to FAILED if possible
            try:
                transition = self._state_machine.transition(
                    SessionState.FAILED,
                    reason=f"Unexpected error: {str(e)}",
                    metadata={"skill_name": skill_name, "error_category": category.value},
                )
                state_transitions.append(f"{transition.from_state.value} -> {transition.to_state.value}")
            except Exception:
                # State transition failed, keep current state
                pass

            return SkillExecutionResult(
                success=False,
                skill_name=skill_name,
                session_id=session_id or "unknown",
                error_entry=error_entry,
                state_transitions=state_transitions,
                related_knowledge=related_knowledge,
                recommendations=recommendations,
            )

    def resume_skill(
        self,
        session_id: str,
        user_input: Dict[str, Any],
    ) -> SkillExecutionResult:
        """Resume a paused skill execution with user input.

        This method:
        1. Retrieves the execution context for the paused session
        2. Transitions state from PAUSED to RUNNING
        3. Merges user input with original parameters
        4. Re-executes the skill with updated parameters
        5. Transitions to COMPLETED or FAILED based on outcome

        Args:
            session_id: Session identifier to resume
            user_input: User input to provide to the paused skill

        Returns:
            SkillExecutionResult containing execution outcome
        """
        state_transitions: List[str] = []
        context = None  # Initialize to avoid UnboundLocalError

        try:
            # Step 1: Retrieve execution context
            context = self._execution_contexts.get(session_id)
            if context is None:
                # Log the error and return error result
                category = self._error_handler.classify_error(
                    ValueError(f"No paused execution context found for session: {session_id}")
                )
                error_entry = self._error_handler.log_error(
                    ValueError(f"No paused execution context found for session: {session_id}"),
                    category,
                    session_id,
                    {"resumed": True},
                )
                return SkillExecutionResult(
                    success=False,
                    skill_name="unknown",
                    session_id=session_id,
                    error_entry=error_entry,
                    state_transitions=state_transitions,
                )

            skill_name = context["skill_name"]
            original_params = context.get("params", {})

            # Step 2: Transition from PAUSED to RUNNING
            transition = self._state_machine.transition(
                SessionState.RUNNING,
                reason="Resuming execution with user input",
                metadata={"skill_name": skill_name, "session_id": session_id},
            )
            state_transitions.append(f"{transition.from_state.value} -> {transition.to_state.value}")

            # Step 3: Merge user input with original parameters
            updated_params = {**original_params, **user_input}

            # Step 4: Re-execute the skill with updated parameters
            def execute_operation():
                return self._host_adapter.invoke_skill(skill_name, updated_params)

            result, error_entry = self._error_handler.execute_with_retry(
                execute_operation,
                session_id=session_id,
                context={"skill_name": skill_name, "params": updated_params, "resumed": True},
            )

            # Step 5: Handle error if execution failed
            if error_entry is not None:
                transition = self._state_machine.transition(
                    SessionState.FAILED,
                    reason=f"Resume execution failed: {error_entry.message}",
                    metadata={"skill_name": skill_name, "error_category": error_entry.category.value},
                )
                state_transitions.append(f"{transition.from_state.value} -> {transition.to_state.value}")

                # Clean up execution context
                self._execution_contexts.pop(session_id, None)

                return SkillExecutionResult(
                    success=False,
                    skill_name=skill_name,
                    session_id=session_id,
                    error_entry=error_entry,
                    state_transitions=state_transitions,
                )

            # Step 6: Extract artifacts from result if present
            artifacts = []
            if isinstance(result, dict):
                # Check if result contains artifacts at top level
                if "artifacts" in result:
                    artifacts = result["artifacts"]
                # Check in result field if present
                elif "result" in result and isinstance(result["result"], dict):
                    inner_result = result["result"]
                    if "artifacts" in inner_result:
                        artifacts = inner_result["artifacts"]
                    # Check for common artifact fields
                    elif "output_files" in inner_result:
                        artifacts = inner_result["output_files"]
                    elif "files" in inner_result:
                        artifacts = inner_result["files"]
                # Check for common artifact fields at top level
                elif "output_files" in result:
                    artifacts = result["output_files"]
                elif "files" in result:
                    artifacts = result["files"]

            # Step 7: Transition to COMPLETED
            transition = self._state_machine.transition(
                SessionState.COMPLETED,
                reason=f"Skill execution completed after resume: {skill_name}",
                metadata={"skill_name": skill_name},
            )
            state_transitions.append(f"{transition.from_state.value} -> {transition.to_state.value}")

            # Clean up execution context
            self._execution_contexts.pop(session_id, None)

            return SkillExecutionResult(
                success=True,
                skill_name=skill_name,
                session_id=session_id,
                output=result,
                artifacts=artifacts if isinstance(artifacts, list) else [],
                state_transitions=state_transitions,
                recommendations=[],
            )

        except Exception as e:
            logger.error(f"Unexpected error during skill resume: {e}", exc_info=True)
            category = self._error_handler.classify_error(e)
            error_entry = self._error_handler.log_error(e, category, session_id, {"resumed": True})

            # Try to transition to FAILED if possible
            try:
                transition = self._state_machine.transition(
                    SessionState.FAILED,
                    reason=f"Resume failed: {str(e)}",
                    metadata={"error_category": category.value},
                )
                state_transitions.append(f"{transition.from_state.value} -> {transition.to_state.value}")
            except Exception:
                pass

            # Clean up execution context
            self._execution_contexts.pop(session_id, None)

            return SkillExecutionResult(
                success=False,
                skill_name=context.get("skill_name", "unknown") if 'context' in locals() else "unknown",
                session_id=session_id,
                error_entry=error_entry,
                state_transitions=state_transitions,
                recommendations=[],
            )

    def _build_recommendation_service(self) -> RecommendationService | None:
        """Build a recommendation service when knowledge stores are available."""
        if self._recommendation_service is not None:
            return self._recommendation_service

        if self._knowledge_integration is not None:
            knowledge_store = getattr(self._knowledge_integration, "_knowledge_store", None)
            experience_index = getattr(self._knowledge_integration, "_experience_index", None)
            if knowledge_store is not None and experience_index is not None:
                return RecommendationService(knowledge_store, experience_index)
            return None

        if self._session_manager is not None and hasattr(self._session_manager, "_storage"):
            storage = getattr(self._session_manager, "_storage")
            if isinstance(storage, FileStorage):
                return RecommendationService(
                    KnowledgeStore(storage),
                    ExperienceIndex(storage),
                )

        return None

    def _recommendation_service_enabled(
        self,
        recommendation_service: RecommendationService,
    ) -> bool:
        """Return whether the provided recommendation service should run."""
        enabled_checker = getattr(recommendation_service, "is_enabled", None)
        if callable(enabled_checker):
            return bool(enabled_checker())
        return True

    def _get_session_context(
        self,
        session_id: Optional[str],
    ) -> tuple[str | None, dict[str, Any]]:
        """Fetch session topic/metadata when session information is available."""
        if not session_id or self._session_manager is None:
            return None, {}
        session = self._session_manager.restore_session(session_id)
        if session is None:
            return None, {}
        topic = getattr(session, "topic", None)
        context = getattr(session, "context", None)
        metadata = getattr(context, "metadata", {}) if context is not None else {}
        if isinstance(metadata, dict):
            return topic, dict(metadata)
        return topic, {}

    def _safe_get_repository_state(self) -> dict[str, Any]:
        """Best-effort repository state fetch for recommendation context."""
        try:
            return self._host_adapter.get_repository_state()
        except Exception:
            return {}

    def _merge_recommendation_metadata(
        self,
        existing_metadata: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge recommendation-relevant params into session metadata."""
        merged = dict(existing_metadata)
        if params.get("problem_domain"):
            merged["problem_domain"] = params["problem_domain"]
        if params.get("domain"):
            merged["domain"] = params["domain"]
        tags = params.get("tags")
        if isinstance(tags, list):
            merged["tags"] = tags
        return merged

    def _persist_session_runtime_context(
        self,
        session_id: Optional[str],
        state: SessionState,
        metadata: dict[str, Any],
    ) -> None:
        """Best-effort writeback of runtime state/metadata to session.json."""
        if not session_id or self._session_manager is None:
            return
        try:
            self._session_manager.update_session(
                session_id,
                state=state,
                context_metadata=metadata,
            )
        except Exception:
            logger.debug("Failed to persist session runtime context", exc_info=True)

    def _persist_session_artifacts(
        self,
        session_id: Optional[str],
        artifacts: list[Any],
    ) -> None:
        """Best-effort writeback of artifact paths to session.json."""
        if not session_id or self._session_manager is None or not artifacts:
            return
        artifact_payloads: list[dict[str, Any]] = []
        for artifact in artifacts:
            if isinstance(artifact, str):
                artifact_payloads.append({"path": artifact, "status": "produced"})
            elif isinstance(artifact, dict):
                artifact_payloads.append(artifact)
        try:
            self._session_manager.update_session(
                session_id,
                artifacts=artifact_payloads,
            )
        except Exception:
            logger.debug("Failed to persist session artifacts", exc_info=True)

    def get_skill_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
        """Get metadata about a skill.

        In Phase 1, this is a simplified implementation that returns
        basic metadata. In a full implementation, this would parse
        the SKILL.md file to extract detailed metadata.

        Args:
            skill_name: Name of the skill

        Returns:
            SkillMetadata if skill exists, None otherwise
        """
        try:
            # Try to invoke the skill with a special metadata query
            # This is a Phase 1 simplification - in production, we would
            # parse the SKILL.md file directly
            result = self._host_adapter.invoke_skill(
                skill_name,
                {"__metadata_query": True},
            )

            # If the skill supports metadata queries, return detailed info
            if isinstance(result, dict) and result.get("status") == "success":
                metadata_result = result.get("result", {})
                return SkillMetadata(
                    name=skill_name,
                    description=metadata_result.get("description", f"Skill: {skill_name}"),
                    parameters=metadata_result.get("parameters", []),
                    required_params=metadata_result.get("required_params", []),
                    optional_params=metadata_result.get("optional_params", []),
                    returns=metadata_result.get("returns", ""),
                    pack_id=metadata_result.get("pack_id", ""),
                )

        except Exception:
            # If metadata query fails, return basic metadata
            pass

        # Return basic metadata
        return SkillMetadata(
            name=skill_name,
            description=f"Skill: {skill_name}",
            parameters=[],
            required_params=[],
            optional_params=[],
            returns="",
            pack_id="",
        )

    def list_skills(self, pack_id: Optional[str] = None) -> List[str]:
        """List available skills, optionally filtered by pack.

        In Phase 1, this is a simplified implementation. In a full
        implementation, this would scan the skills directory to
        discover all available skills.

        Args:
            pack_id: Optional pack identifier to filter by

        Returns:
            List of skill names
        """
        try:
            # Try to invoke a special list-skills operation
            result = self._host_adapter.invoke_skill(
                "__list_skills__",
                {"pack_id": pack_id},
            )

            if isinstance(result, dict) and result.get("status") == "success":
                skills = result.get("result", [])
                if isinstance(skills, list):
                    return skills

        except Exception:
            pass

        # Return empty list if listing fails
        return []
