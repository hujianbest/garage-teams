"""Session lifecycle actions, transitions, and record requirements."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from core.records import SessionState, SessionStatus


class SessionAction(StrEnum):
    CREATE = "create"
    RESUME = "resume"
    PAUSE = "pause"
    HANDOFF = "handoff"
    ENTER_REVIEW_HOLD = "enter-review-hold"
    ENTER_REWORK = "enter-rework"
    START_CLOSEOUT = "start-closeout"
    MARK_ARCHIVE_READY = "mark-archive-ready"
    CLOSE = "close"


class InvalidSessionTransitionError(ValueError):
    """Raised when a lifecycle action is not allowed from the current state."""


@dataclass(slots=True, frozen=True)
class TransitionDefinition:
    from_status: SessionStatus
    action: SessionAction
    to_status: SessionStatus
    required_record_types: tuple[str, ...]
    required_evidence_events: tuple[str, ...] = ()


_TRANSITIONS: dict[SessionStatus, dict[SessionAction, TransitionDefinition]] = {
    SessionStatus.DRAFT: {
        SessionAction.CREATE: TransitionDefinition(
            from_status=SessionStatus.DRAFT,
            action=SessionAction.CREATE,
            to_status=SessionStatus.ACTIVE,
            required_record_types=("SessionIntent", "SessionState"),
        ),
    },
    SessionStatus.ACTIVE: {
        SessionAction.PAUSE: TransitionDefinition(
            from_status=SessionStatus.ACTIVE,
            action=SessionAction.PAUSE,
            to_status=SessionStatus.PAUSED,
            required_record_types=("SessionSnapshot",),
            required_evidence_events=("pause-checkpoint",),
        ),
        SessionAction.HANDOFF: TransitionDefinition(
            from_status=SessionStatus.ACTIVE,
            action=SessionAction.HANDOFF,
            to_status=SessionStatus.HANDOFF_PENDING,
            required_record_types=("SessionSnapshot", "HandoffRecord", "GateDecision"),
            required_evidence_events=("handoff-brief",),
        ),
        SessionAction.ENTER_REVIEW_HOLD: TransitionDefinition(
            from_status=SessionStatus.ACTIVE,
            action=SessionAction.ENTER_REVIEW_HOLD,
            to_status=SessionStatus.REVIEW_HOLD,
            required_record_types=("GateDecision",),
            required_evidence_events=("review-request",),
        ),
        SessionAction.START_CLOSEOUT: TransitionDefinition(
            from_status=SessionStatus.ACTIVE,
            action=SessionAction.START_CLOSEOUT,
            to_status=SessionStatus.CLOSEOUT,
            required_record_types=("SessionSnapshot", "GateDecision"),
            required_evidence_events=("closeout-summary",),
        ),
    },
    SessionStatus.PAUSED: {
        SessionAction.RESUME: TransitionDefinition(
            from_status=SessionStatus.PAUSED,
            action=SessionAction.RESUME,
            to_status=SessionStatus.ACTIVE,
            required_record_types=("SessionState",),
        ),
    },
    SessionStatus.HANDOFF_PENDING: {
        SessionAction.RESUME: TransitionDefinition(
            from_status=SessionStatus.HANDOFF_PENDING,
            action=SessionAction.RESUME,
            to_status=SessionStatus.ACTIVE,
            required_record_types=("SessionState", "HandoffRecord"),
            required_evidence_events=("handoff-acceptance",),
        ),
        SessionAction.ENTER_REVIEW_HOLD: TransitionDefinition(
            from_status=SessionStatus.HANDOFF_PENDING,
            action=SessionAction.ENTER_REVIEW_HOLD,
            to_status=SessionStatus.REVIEW_HOLD,
            required_record_types=("HandoffRecord", "GateDecision"),
            required_evidence_events=("handoff-clarification",),
        ),
        SessionAction.ENTER_REWORK: TransitionDefinition(
            from_status=SessionStatus.HANDOFF_PENDING,
            action=SessionAction.ENTER_REWORK,
            to_status=SessionStatus.REWORK,
            required_record_types=("HandoffRecord", "GateDecision"),
            required_evidence_events=("handoff-rework",),
        ),
    },
    SessionStatus.REVIEW_HOLD: {
        SessionAction.RESUME: TransitionDefinition(
            from_status=SessionStatus.REVIEW_HOLD,
            action=SessionAction.RESUME,
            to_status=SessionStatus.ACTIVE,
            required_record_types=("GateDecision",),
            required_evidence_events=("review-pass",),
        ),
        SessionAction.ENTER_REWORK: TransitionDefinition(
            from_status=SessionStatus.REVIEW_HOLD,
            action=SessionAction.ENTER_REWORK,
            to_status=SessionStatus.REWORK,
            required_record_types=("GateDecision",),
            required_evidence_events=("review-rework",),
        ),
    },
    SessionStatus.REWORK: {
        SessionAction.RESUME: TransitionDefinition(
            from_status=SessionStatus.REWORK,
            action=SessionAction.RESUME,
            to_status=SessionStatus.ACTIVE,
            required_record_types=("SessionState", "GateDecision"),
            required_evidence_events=("rework-restart",),
        ),
    },
    SessionStatus.CLOSEOUT: {
        SessionAction.MARK_ARCHIVE_READY: TransitionDefinition(
            from_status=SessionStatus.CLOSEOUT,
            action=SessionAction.MARK_ARCHIVE_READY,
            to_status=SessionStatus.ARCHIVE_READY,
            required_record_types=("SessionSnapshot", "GateDecision", "LineageLink"),
            required_evidence_events=("archive-readiness",),
        ),
    },
    SessionStatus.ARCHIVE_READY: {
        SessionAction.CLOSE: TransitionDefinition(
            from_status=SessionStatus.ARCHIVE_READY,
            action=SessionAction.CLOSE,
            to_status=SessionStatus.CLOSED,
            required_record_types=("SessionSnapshot", "LineageLink"),
            required_evidence_events=("session-closeout",),
        ),
    },
}


def describe_transition(
    status_or_state: SessionStatus | SessionState,
    action: SessionAction,
) -> TransitionDefinition:
    status = status_or_state.session_status if isinstance(status_or_state, SessionState) else status_or_state
    try:
        return _TRANSITIONS[status][action]
    except KeyError as exc:
        raise InvalidSessionTransitionError(
            f"Action {action.value!r} is not allowed from status {status.value!r}."
        ) from exc


def required_record_types_for_action(
    status_or_state: SessionStatus | SessionState,
    action: SessionAction,
) -> tuple[str, ...]:
    return describe_transition(status_or_state, action).required_record_types


def apply_action(
    state: SessionState,
    action: SessionAction,
    *,
    summary: str | None = None,
) -> SessionState:
    transition = describe_transition(state, action)
    return replace(
        state,
        session_status=transition.to_status,
        summary=summary or state.summary,
    )
