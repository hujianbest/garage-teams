"""Session lifecycle orchestration with governance gating."""

from __future__ import annotations

from dataclasses import dataclass

from core.records import GateDecision, GateVerdict, SessionState
from governance.runtime import GateEvaluation, GateType, GovernanceRuntime, RuntimeContext
from session.lifecycle import SessionAction, apply_action, describe_transition


class BlockedGateError(RuntimeError):
    """Raised when governance prevents a lifecycle action from proceeding."""

    def __init__(self, decision: GateDecision) -> None:
        self.decision = decision
        super().__init__(
            f"Gate blocked action {decision.action_ref.object_id!r} with verdict {decision.verdict.value!r}."
        )


@dataclass(slots=True, frozen=True)
class TransitionOutcome:
    next_state: SessionState
    transition_records: tuple[str, ...]
    evidence_events: tuple[str, ...]
    gate_evaluation: GateEvaluation


class SessionController:
    """Apply lifecycle actions only after governance allows them."""

    def __init__(self, governance: GovernanceRuntime) -> None:
        self._governance = governance

    def transition(
        self,
        state: SessionState,
        *,
        action: SessionAction,
        context: RuntimeContext,
        gate_type: GateType = GateType.TRANSITION,
        summary: str | None = None,
    ) -> TransitionOutcome:
        transition = describe_transition(state, action)
        evaluation = self._governance.evaluate(context, gate_type)
        if evaluation.decision.verdict != GateVerdict.ALLOW:
            raise BlockedGateError(evaluation.decision)
        next_state = apply_action(state, action, summary=summary)
        return TransitionOutcome(
            next_state=next_state,
            transition_records=transition.required_record_types,
            evidence_events=transition.required_evidence_events,
            gate_evaluation=evaluation,
        )
