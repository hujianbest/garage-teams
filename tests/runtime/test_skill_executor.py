"""Tests for SkillExecutor module."""

from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

import pytest

from garage_os.runtime.skill_executor import (
    SkillExecutor,
    SkillExecutionResult,
    SkillMetadata,
)
from garage_os.runtime.session_manager import SessionManager
from garage_os.runtime.state_machine import StateMachine
from garage_os.runtime.error_handler import ErrorHandler
from garage_os.knowledge.integration import KnowledgeIntegration
from garage_os.types import (
    SessionState,
    ErrorCategory,
    KnowledgeEntry,
    KnowledgeType,
)


class TestExecuteSkillNormalPath:
    """Test skill execution normal path (IDLE -> RUNNING -> COMPLETED)."""

    def test_execute_skill_success_with_artifacts(self):
        """Successful skill execution should transition IDLE -> RUNNING -> COMPLETED."""
        # Setup mocks
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {"output": "test output"},
            "artifacts": [
                {"path": "docs/test.md", "role": "design"},
                {"path": "src/test.py", "role": "code"},
            ],
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        # Create executor
        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        # Execute skill
        result = executor.execute_skill("test-skill", {"param1": "value1"}, session_id="test-session")

        # Verify result
        assert result.success is True
        assert result.skill_name == "test-skill"
        assert result.session_id == "test-session"
        assert result.output is not None
        assert len(result.artifacts) == 2
        assert result.error_entry is None

        # Verify state transitions
        assert len(result.state_transitions) == 2
        assert "idle -> running" in result.state_transitions[0].lower()
        assert "running -> completed" in result.state_transitions[1].lower()

        # Verify final state
        assert state_machine.current_state == SessionState.COMPLETED

    def test_execute_skill_success_without_artifacts(self):
        """Successful skill execution without artifacts should complete correctly."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {"output": "test output"},
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        result = executor.execute_skill("simple-skill", {}, session_id="session-1")

        assert result.success is True
        assert len(result.artifacts) == 0
        assert state_machine.current_state == SessionState.COMPLETED


class TestExecuteSkillWithUserInput:
    """Test skill execution requiring user input (RUNNING -> PAUSED -> RUNNING)."""

    def test_execute_skill_paused_for_user_input(self):
        """Skill requiring user input should transition RUNNING -> PAUSED."""
        host_adapter = Mock()
        # First call raises PermissionError (needs user input)
        host_adapter.invoke_skill.side_effect = PermissionError("User confirmation required")

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        result = executor.execute_skill("confirmation-skill", {}, session_id="paused-session")

        # Verify paused state
        assert result.success is False
        assert result.error_entry is not None
        assert result.error_entry.category == ErrorCategory.USER_INTERVENTION
        assert state_machine.current_state == SessionState.PAUSED

        # Verify state transitions
        assert any("paused" in t.lower() for t in result.state_transitions)

    def test_resume_skill_from_paused(self):
        """Resuming a paused skill should transition PAUSED -> RUNNING -> COMPLETED."""
        host_adapter = Mock()
        # Second call (after resume) succeeds
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {"output": "resumed output"},
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.PAUSED)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        # Store execution context (simulating previous pause)
        executor._execution_contexts["paused-session"] = {
            "skill_name": "confirmation-skill",
            "params": {"original_param": "value"},
            "session_id": "paused-session",
        }

        # Resume with user input
        result = executor.resume_skill("paused-session", {"user_confirmed": True})

        # Verify success
        assert result.success is True
        assert result.skill_name == "confirmation-skill"
        assert state_machine.current_state == SessionState.COMPLETED

        # Verify state transitions
        assert any("running" in t.lower() for t in result.state_transitions)
        assert any("completed" in t.lower() for t in result.state_transitions)

        # Verify execution context was cleaned up
        assert "paused-session" not in executor._execution_contexts


class TestExecuteSkillFailure:
    """Test skill execution failure scenarios (RUNNING -> FAILED)."""

    def test_execute_skill_fatal_error(self):
        """Fatal error during execution should transition RUNNING -> FAILED."""
        host_adapter = Mock()
        host_adapter.invoke_skill.side_effect = ValueError("Invalid input data")

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        result = executor.execute_skill("validation-skill", {"invalid": "data"}, session_id="failed-session")

        # Verify failure
        assert result.success is False
        assert result.error_entry is not None
        assert result.error_entry.category == ErrorCategory.FATAL
        assert state_machine.current_state == SessionState.FAILED

        # Verify error entry details
        assert result.error_entry.error_type == "ValueError"
        assert "Invalid input data" in result.error_entry.message

    def test_execute_skill_error_handler_classification(self):
        """Error Handler should correctly classify different error types."""
        # Test non-retryable errors directly (they don't get upgraded)
        test_cases = [
            (PermissionError("Access denied"), ErrorCategory.USER_INTERVENTION),
            (FileNotFoundError("Missing file"), ErrorCategory.USER_INTERVENTION),
            (ValueError("Invalid data"), ErrorCategory.FATAL),
        ]

        for error, expected_category in test_cases:
            host_adapter = Mock()
            host_adapter.invoke_skill.side_effect = error

            session_manager = Mock(spec=SessionManager)
            state_machine = StateMachine(initial_state=SessionState.IDLE)
            error_handler = ErrorHandler()

            executor = SkillExecutor(
                host_adapter=host_adapter,
                session_manager=session_manager,
                state_machine=state_machine,
                error_handler=error_handler,
            )

            result = executor.execute_skill("test-skill", {}, session_id="test-session")

            assert result.success is False
            assert result.error_entry.category == expected_category

        # Test retryable errors with successful retry
        retryable_test_cases = [
            (ConnectionError("Network error"),),
            (TimeoutError("Timeout"),),
            (OSError("System error"),),
        ]

        for (error,) in retryable_test_cases:
            host_adapter = Mock()
            call_count = [0]

            def flaky_invoke(skill_name, params):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise error
                return {"status": "success", "result": {"output": "success"}}

            host_adapter.invoke_skill = flaky_invoke

            session_manager = Mock(spec=SessionManager)
            state_machine = StateMachine(initial_state=SessionState.IDLE)
            error_handler = ErrorHandler()

            executor = SkillExecutor(
                host_adapter=host_adapter,
                session_manager=session_manager,
                state_machine=state_machine,
                error_handler=error_handler,
            )

            result = executor.execute_skill("test-skill", {}, session_id="test-session")

            # After successful retry, execution should succeed
            assert result.success is True
            assert call_count[0] == 2  # Initial call + 1 retry


class TestExecuteSkillRetry:
    """Test skill execution with retry logic."""

    def test_execute_skill_retryable_error_recovers(self):
        """Retryable error should be retried and eventually succeed."""
        host_adapter = Mock()
        # First call fails, second succeeds
        call_count = [0]

        def flaky_invoke(skill_name, params):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("Connection failed")
            return {"status": "success", "result": {"output": "success after retry"}}

        host_adapter.invoke_skill = flaky_invoke

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        result = executor.execute_skill("flaky-skill", {}, session_id="retry-session")

        # Verify success after retry
        assert result.success is True
        assert call_count[0] == 2  # Called twice (initial + 1 retry)
        assert state_machine.current_state == SessionState.COMPLETED

    def test_execute_skill_retryable_error_exhausted(self):
        """Retryable error should exhaust retries and fail permanently."""
        host_adapter = Mock()
        # Always fails
        host_adapter.invoke_skill.side_effect = ConnectionError("Persistent connection error")

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        result = executor.execute_skill("always-failing-skill", {}, session_id="exhausted-session")

        # Verify failure after exhausting retries
        assert result.success is False
        assert result.error_entry is not None
        # After exhausting retries, error is upgraded to FATAL
        assert result.error_entry.category == ErrorCategory.FATAL
        assert state_machine.current_state == SessionState.FAILED


class TestGetSkillMetadata:
    """Test skill metadata retrieval."""

    def test_get_skill_metadata_with_full_info(self):
        """Should return complete skill metadata when available."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {
                "description": "Test skill for unit testing",
                "parameters": ["param1", "param2", "param3"],
                "required_params": ["param1", "param2"],
                "optional_params": ["param3"],
                "returns": "Dict with execution results",
                "pack_id": "test-pack",
            },
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine()
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        metadata = executor.get_skill_metadata("test-skill")

        # Verify metadata
        assert isinstance(metadata, SkillMetadata)
        assert metadata.name == "test-skill"
        assert metadata.description == "Test skill for unit testing"
        assert len(metadata.parameters) == 3
        assert metadata.required_params == ["param1", "param2"]
        assert metadata.optional_params == ["param3"]
        assert metadata.returns == "Dict with execution results"
        assert metadata.pack_id == "test-pack"

    def test_get_skill_metadata_fallback_to_basic(self):
        """Should return basic metadata when skill doesn't support metadata query."""
        host_adapter = Mock()
        host_adapter.invoke_skill.side_effect = Exception("Metadata not supported")

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine()
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        metadata = executor.get_skill_metadata("unknown-skill")

        # Verify basic metadata
        assert isinstance(metadata, SkillMetadata)
        assert metadata.name == "unknown-skill"
        assert metadata.description == "Skill: unknown-skill"
        assert len(metadata.parameters) == 0


class TestListSkills:
    """Test listing available skills."""

    def test_list_skills_all(self):
        """Should return list of all available skills."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": [
                "skill-1",
                "skill-2",
                "skill-3",
            ],
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine()
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        skills = executor.list_skills()

        # Verify skills list
        assert isinstance(skills, list)
        assert len(skills) == 3
        assert "skill-1" in skills
        assert "skill-2" in skills
        assert "skill-3" in skills

    def test_list_skills_filtered_by_pack(self):
        """Should return skills filtered by pack_id."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": ["pack1-skill-1", "pack1-skill-2"],
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine()
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        skills = executor.list_skills(pack_id="pack1")

        # Verify filtered skills
        assert len(skills) == 2
        assert all(skill.startswith("pack1-") for skill in skills)

    def test_list_skills_fallback_to_empty(self):
        """Should return empty list when listing fails."""
        host_adapter = Mock()
        host_adapter.invoke_skill.side_effect = Exception("List not supported")

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine()
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        skills = executor.list_skills()

        # Verify empty list
        assert isinstance(skills, list)
        assert len(skills) == 0


class TestKnowledgeIntegration:
    """Test knowledge base integration during skill execution."""

    def test_execute_skill_queries_related_knowledge(self):
        """Skill execution should query related knowledge entries."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {"output": "test output"},
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        # Mock knowledge integration
        knowledge_integration = Mock(spec=KnowledgeIntegration)
        mock_knowledge_store = Mock()
        mock_entry = KnowledgeEntry(
            id="k1",
            type=KnowledgeType.SOLUTION,
            topic="Test skill solution",
            date=datetime.now(),
            tags=["test-skill", "testing"],
            content="Solution content",
        )
        mock_knowledge_store.list_entries.return_value = [mock_entry]
        knowledge_integration._knowledge_store = mock_knowledge_store

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
            knowledge_integration=knowledge_integration,
        )

        result = executor.execute_skill("test-skill", {}, session_id="test-session")

        # Verify knowledge was queried
        assert result.success is True
        assert len(result.related_knowledge) > 0
        assert result.related_knowledge[0].id == "k1"
        assert "test-skill" in result.related_knowledge[0].tags

    def test_execute_skill_without_knowledge_integration(self):
        """Skill execution should work without knowledge integration."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {"output": "test output"},
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        # Create executor without knowledge integration
        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
            knowledge_integration=None,
        )

        result = executor.execute_skill("test-skill", {}, session_id="test-session")

        # Verify execution succeeds without knowledge
        assert result.success is True
        assert len(result.related_knowledge) == 0

    def test_execute_skill_uses_recommendation_service_when_available(self):
        """Skill execution should surface recommendations built from richer context."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {"output": "test output"},
        }
        host_adapter.get_repository_state.return_value = {"branch": "main", "dirty": False}

        session_manager = Mock(spec=SessionManager)
        session_manager.restore_session.return_value = Mock(
            topic="F003 design",
            context=Mock(metadata={"problem_domain": "memory_pipeline"}),
        )
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        recommendation_service = Mock()
        recommendation_service.recommend.return_value = [
            {
                "entry_id": "decision-1",
                "match_reasons": ["skill:hf-design"],
            }
        ]

        result = executor.execute_skill(
            "hf-design",
            {"domain": "garage_os"},
            session_id="test-session",
            recommendation_service=recommendation_service,
        )

        assert result.success is True
        assert result.recommendations == [
            {
                "entry_id": "decision-1",
                "match_reasons": ["skill:hf-design"],
            }
        ]
        recommendation_service.recommend.assert_called_once()


class TestSkillExecutorEdgeCases:
    """Test edge cases and error handling."""

    def test_resume_skill_invalid_session(self):
        """Resume with invalid session should return error result."""
        host_adapter = Mock()
        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.PAUSED)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        result = executor.resume_skill("non-existent-session", {"input": "value"})

        # Verify error result
        assert result.success is False
        assert result.error_entry is not None
        assert result.error_entry.category == ErrorCategory.FATAL

    def test_execute_skill_with_empty_params(self):
        """Skill execution with empty params should work correctly."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {"output": "no params needed"},
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        result = executor.execute_skill("no-params-skill")

        assert result.success is True
        assert state_machine.current_state == SessionState.COMPLETED

    def test_execute_skill_preserves_session_id(self):
        """Session ID should be preserved in execution result."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {"output": "test"},
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        result = executor.execute_skill("test-skill", {}, session_id="custom-session-123")

        assert result.session_id == "custom-session-123"

    def test_execute_skill_with_output_files(self):
        """Artifacts should be extracted from output_files field."""
        host_adapter = Mock()
        host_adapter.invoke_skill.return_value = {
            "status": "success",
            "result": {
                "output": "files generated",
                "output_files": ["/path/to/file1.md", "/path/to/file2.py"],
            },
        }

        session_manager = Mock(spec=SessionManager)
        state_machine = StateMachine(initial_state=SessionState.IDLE)
        error_handler = ErrorHandler()

        executor = SkillExecutor(
            host_adapter=host_adapter,
            session_manager=session_manager,
            state_machine=state_machine,
            error_handler=error_handler,
        )

        result = executor.execute_skill("file-generator-skill", {}, session_id="test-session")

        assert result.success is True
        assert len(result.artifacts) == 2
        assert "/path/to/file1.md" in result.artifacts
