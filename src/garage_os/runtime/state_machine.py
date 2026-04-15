"""State machine for managing workflow session state transitions."""

from datetime import datetime
from typing import Optional

from garage_os.types import SessionState, StateTransition


class InvalidStateTransitionError(Exception):
    """Exception raised when an invalid state transition is attempted."""

    def __init__(self, from_state: SessionState, to_state: SessionState):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid transition: {from_state.value} -> {to_state.value}")


class StateMachine:
    """Execution state machine for managing SessionState transitions."""

    # Valid transition table
    VALID_TRANSITIONS: dict[SessionState, set[SessionState]] = {
        SessionState.IDLE: {SessionState.RUNNING, SessionState.ARCHIVED},
        SessionState.RUNNING: {
            SessionState.PAUSED,
            SessionState.COMPLETED,
            SessionState.FAILED,
            SessionState.ARCHIVED,
        },
        SessionState.PAUSED: {SessionState.RUNNING, SessionState.ARCHIVED},
        SessionState.FAILED: {SessionState.RUNNING, SessionState.ARCHIVED},  # retry
        SessionState.COMPLETED: {SessionState.ARCHIVED},
        SessionState.ARCHIVED: set(),  # terminal
    }

    def __init__(self, initial_state: SessionState = SessionState.IDLE):
        """Initialize the state machine with an initial state."""
        self._current_state = initial_state
        self._history: list[StateTransition] = []

    def transition(
        self,
        to_state: SessionState,
        reason: str = "",
        metadata: Optional[dict] = None,
    ) -> StateTransition:
        """Execute a state transition.

        Args:
            to_state: The target state to transition to.
            reason: Optional reason for the transition.
            metadata: Optional metadata dict for the transition.

        Returns:
            The StateTransition record that was created.

        Raises:
            InvalidStateTransitionError: If the transition is not valid.
        """
        if not self.can_transition(to_state):
            raise InvalidStateTransitionError(self._current_state, to_state)

        from_state = self._current_state
        transition_record = StateTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.now(),
            reason=reason,
            metadata=metadata or {},
        )

        self._history.append(transition_record)
        self._current_state = to_state

        return transition_record

    def can_transition(self, to_state: SessionState) -> bool:
        """Check if a transition to the target state is valid.

        Args:
            to_state: The target state to check.

        Returns:
            True if the transition is valid, False otherwise.
        """
        return to_state in self.VALID_TRANSITIONS[self._current_state]

    def get_valid_transitions(self) -> set[SessionState]:
        """Get all valid target states from the current state.

        Returns:
            A set of SessionState values that are valid targets.
        """
        return self.VALID_TRANSITIONS[self._current_state].copy()

    @property
    def current_state(self) -> SessionState:
        """Get the current state."""
        return self._current_state

    @property
    def history(self) -> list[StateTransition]:
        """Get a copy of the transition history."""
        return list(self._history)

    def reset(self, state: SessionState = SessionState.IDLE) -> None:
        """Reset the state machine to a given state and clear history.

        Args:
            state: The state to reset to. Defaults to IDLE.
        """
        self._current_state = state
        self._history.clear()
