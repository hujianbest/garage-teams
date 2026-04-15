"""Tests for StateMachine module."""

import pytest

from garage_os.runtime.state_machine import (
    StateMachine,
    InvalidStateTransitionError,
)
from garage_os.types import SessionState


class TestInitialState:
    """Test initial state setup."""

    def test_initial_state(self):
        """Initial state should be IDLE by default."""
        sm = StateMachine()
        assert sm.current_state == SessionState.IDLE

    def test_custom_initial_state(self):
        """State machine can be initialized with a custom state."""
        sm = StateMachine(initial_state=SessionState.RUNNING)
        assert sm.current_state == SessionState.RUNNING


class TestValidTransitions:
    """Test valid state transitions."""

    def test_valid_transition_idle_to_running(self):
        """idle -> running should succeed."""
        sm = StateMachine()
        transition = sm.transition(SessionState.RUNNING, "Starting execution")
        assert sm.current_state == SessionState.RUNNING
        assert transition.from_state == SessionState.IDLE
        assert transition.to_state == SessionState.RUNNING
        assert transition.reason == "Starting execution"

    def test_valid_transition_running_to_paused(self):
        """running -> paused should succeed."""
        sm = StateMachine(SessionState.RUNNING)
        transition = sm.transition(SessionState.PAUSED, "User paused")
        assert sm.current_state == SessionState.PAUSED
        assert transition.to_state == SessionState.PAUSED

    def test_valid_transition_paused_to_running(self):
        """paused -> running (resume) should succeed."""
        sm = StateMachine(SessionState.PAUSED)
        transition = sm.transition(SessionState.RUNNING, "Resuming")
        assert sm.current_state == SessionState.RUNNING
        assert transition.to_state == SessionState.RUNNING

    def test_valid_transition_running_to_completed(self):
        """running -> completed should succeed."""
        sm = StateMachine(SessionState.RUNNING)
        transition = sm.transition(SessionState.COMPLETED, "Finished successfully")
        assert sm.current_state == SessionState.COMPLETED
        assert transition.to_state == SessionState.COMPLETED

    def test_valid_transition_running_to_failed(self):
        """running -> failed should succeed."""
        sm = StateMachine(SessionState.RUNNING)
        transition = sm.transition(SessionState.FAILED, "Error occurred")
        assert sm.current_state == SessionState.FAILED
        assert transition.to_state == SessionState.FAILED

    def test_valid_transition_failed_to_running(self):
        """failed -> running (retry) should succeed."""
        sm = StateMachine(SessionState.FAILED)
        transition = sm.transition(SessionState.RUNNING, "Retrying")
        assert sm.current_state == SessionState.RUNNING
        assert transition.to_state == SessionState.RUNNING

    def test_valid_transition_any_to_archived_from_idle(self):
        """idle -> archived should succeed."""
        sm = StateMachine(SessionState.IDLE)
        sm.transition(SessionState.ARCHIVED)
        assert sm.current_state == SessionState.ARCHIVED

    def test_valid_transition_any_to_archived_from_running(self):
        """running -> archived should succeed."""
        sm = StateMachine(SessionState.RUNNING)
        sm.transition(SessionState.ARCHIVED)
        assert sm.current_state == SessionState.ARCHIVED

    def test_valid_transition_any_to_archived_from_paused(self):
        """paused -> archived should succeed."""
        sm = StateMachine(SessionState.PAUSED)
        sm.transition(SessionState.ARCHIVED)
        assert sm.current_state == SessionState.ARCHIVED

    def test_valid_transition_any_to_archived_from_failed(self):
        """failed -> archived should succeed."""
        sm = StateMachine(SessionState.FAILED)
        sm.transition(SessionState.ARCHIVED)
        assert sm.current_state == SessionState.ARCHIVED

    def test_valid_transition_any_to_archived_from_completed(self):
        """completed -> archived should succeed."""
        sm = StateMachine(SessionState.COMPLETED)
        sm.transition(SessionState.ARCHIVED)
        assert sm.current_state == SessionState.ARCHIVED


class TestInvalidTransitions:
    """Test invalid state transitions raise exceptions."""

    def test_invalid_transition_idle_to_completed(self):
        """idle -> completed should raise InvalidStateTransitionError."""
        sm = StateMachine()
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            sm.transition(SessionState.COMPLETED)
        assert exc_info.value.from_state == SessionState.IDLE
        assert exc_info.value.to_state == SessionState.COMPLETED
        assert sm.current_state == SessionState.IDLE  # State unchanged

    def test_invalid_transition_paused_to_completed(self):
        """paused -> completed should raise InvalidStateTransitionError."""
        sm = StateMachine(SessionState.PAUSED)
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            sm.transition(SessionState.COMPLETED)
        assert exc_info.value.from_state == SessionState.PAUSED
        assert exc_info.value.to_state == SessionState.COMPLETED

    def test_invalid_transition_completed_to_running(self):
        """completed -> running should raise InvalidStateTransitionError."""
        sm = StateMachine(SessionState.COMPLETED)
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            sm.transition(SessionState.RUNNING)
        assert exc_info.value.from_state == SessionState.COMPLETED
        assert exc_info.value.to_state == SessionState.RUNNING

    def test_invalid_transition_archived_to_running(self):
        """archived -> running should raise InvalidStateTransitionError."""
        sm = StateMachine(SessionState.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            sm.transition(SessionState.RUNNING)
        assert exc_info.value.from_state == SessionState.ARCHIVED
        assert exc_info.value.to_state == SessionState.RUNNING

    def test_invalid_transition_archived_to_idle(self):
        """archived -> idle should raise InvalidStateTransitionError."""
        sm = StateMachine(SessionState.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            sm.transition(SessionState.IDLE)
        assert exc_info.value.from_state == SessionState.ARCHIVED
        assert exc_info.value.to_state == SessionState.IDLE

    def test_invalid_transition_archived_to_paused(self):
        """archived -> paused should raise InvalidStateTransitionError."""
        sm = StateMachine(SessionState.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            sm.transition(SessionState.PAUSED)
        assert exc_info.value.from_state == SessionState.ARCHIVED
        assert exc_info.value.to_state == SessionState.PAUSED


class TestHistory:
    """Test transition history recording."""

    def test_history_records_transitions(self):
        """Each transition should record timestamp and reason."""
        sm = StateMachine()
        sm.transition(SessionState.RUNNING, "Start")
        sm.transition(SessionState.PAUSED, "Pause")
        sm.transition(SessionState.RUNNING, "Resume")

        history = sm.history
        assert len(history) == 3

        assert history[0].from_state == SessionState.IDLE
        assert history[0].to_state == SessionState.RUNNING
        assert history[0].reason == "Start"
        assert history[0].timestamp is not None

        assert history[1].from_state == SessionState.RUNNING
        assert history[1].to_state == SessionState.PAUSED
        assert history[1].reason == "Pause"

        assert history[2].from_state == SessionState.PAUSED
        assert history[2].to_state == SessionState.RUNNING
        assert history[2].reason == "Resume"

    def test_multiple_transitions(self):
        """Multiple transitions should maintain complete history."""
        sm = StateMachine()
        states = [
            SessionState.RUNNING,
            SessionState.PAUSED,
            SessionState.RUNNING,
            SessionState.FAILED,
            SessionState.RUNNING,
            SessionState.COMPLETED,
            SessionState.ARCHIVED,
        ]

        for i, state in enumerate(states):
            sm.transition(state, f"Transition {i+1}")

        assert len(sm.history) == len(states)
        assert sm.current_state == SessionState.ARCHIVED

        # Verify each transition in order
        for i, (transition, expected_to_state) in enumerate(zip(sm.history, states)):
            assert transition.to_state == expected_to_state

    def test_history_with_metadata(self):
        """Transitions should store optional metadata."""
        sm = StateMachine()
        sm.transition(SessionState.RUNNING)  # First go to RUNNING
        metadata = {"error_code": 500, "retry_count": 3}
        sm.transition(SessionState.FAILED, "Server error", metadata=metadata)

        assert sm.history[1].metadata == metadata

    def test_history_returns_copy(self):
        """History property should return a copy, not the internal list."""
        sm = StateMachine()
        sm.transition(SessionState.RUNNING)

        history1 = sm.history
        history2 = sm.history
        assert history1 is not history2  # Different objects
        assert history1 == history2  # Same content


class TestQueryMethods:
    """Test state machine query methods."""

    def test_can_transition_true(self):
        """can_transition should return True for valid transitions."""
        sm = StateMachine()
        assert sm.can_transition(SessionState.RUNNING) is True
        assert sm.can_transition(SessionState.ARCHIVED) is True

    def test_can_transition_false(self):
        """can_transition should return False for invalid transitions."""
        sm = StateMachine()
        assert sm.can_transition(SessionState.COMPLETED) is False
        assert sm.can_transition(SessionState.PAUSED) is False

    def test_get_valid_transitions_from_idle(self):
        """get_valid_transitions should return correct set for IDLE."""
        sm = StateMachine()
        valid = sm.get_valid_transitions()
        assert valid == {SessionState.RUNNING, SessionState.ARCHIVED}

    def test_get_valid_transitions_from_running(self):
        """get_valid_transitions should return correct set for RUNNING."""
        sm = StateMachine(SessionState.RUNNING)
        valid = sm.get_valid_transitions()
        assert valid == {
            SessionState.PAUSED,
            SessionState.COMPLETED,
            SessionState.FAILED,
            SessionState.ARCHIVED,
        }

    def test_get_valid_transitions_from_archived(self):
        """get_valid_transitions should return empty set for ARCHIVED."""
        sm = StateMachine(SessionState.ARCHIVED)
        valid = sm.get_valid_transitions()
        assert valid == set()

    def test_get_valid_transitions_returns_copy(self):
        """get_valid_transitions should return a copy, not internal set."""
        sm = StateMachine()
        valid1 = sm.get_valid_transitions()
        valid2 = sm.get_valid_transitions()
        assert valid1 is not valid2  # Different objects
        assert valid1 == valid2  # Same content


class TestReset:
    """Test state machine reset functionality."""

    def test_reset_to_default(self):
        """Reset without arguments should return to IDLE and clear history."""
        sm = StateMachine()
        sm.transition(SessionState.RUNNING)
        sm.transition(SessionState.PAUSED)

        sm.reset()

        assert sm.current_state == SessionState.IDLE
        assert len(sm.history) == 0

    def test_reset_to_custom_state(self):
        """Reset to a custom state should work."""
        sm = StateMachine()
        sm.transition(SessionState.RUNNING)
        sm.transition(SessionState.FAILED)

        sm.reset(state=SessionState.RUNNING)

        assert sm.current_state == SessionState.RUNNING
        assert len(sm.history) == 0

    def test_reset_preserves_valid_transitions(self):
        """After reset, transition table should still be valid."""
        sm = StateMachine()
        sm.transition(SessionState.RUNNING)
        sm.reset()

        # Should still be able to transition from IDLE
        assert sm.can_transition(SessionState.RUNNING) is True
        sm.transition(SessionState.RUNNING)
        assert sm.current_state == SessionState.RUNNING
