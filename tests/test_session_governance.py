import unittest

from core import GateVerdict, SessionStatus, build_session_creation_fixture
from governance import GateType, GovernanceRule, GovernanceRuntime, GovernanceScope, RuntimeContext
from session import BlockedGateError, InvalidSessionTransitionError, SessionAction, SessionController


class SessionGovernanceTests(unittest.TestCase):
    def test_pause_transition_updates_state_when_gate_allows(self) -> None:
        session_fixture = build_session_creation_fixture()
        state = session_fixture["state"]

        controller = SessionController(GovernanceRuntime())
        outcome = controller.transition(
            state,
            action=SessionAction.PAUSE,
            context=RuntimeContext(
                workspace_id="garage",
                session_id=state.session_id,
                pack_id=state.current_pack,
                node_id=state.current_node,
                action=SessionAction.PAUSE,
            ),
        )

        self.assertEqual(outcome.next_state.session_status, SessionStatus.PAUSED)
        self.assertIn("SessionSnapshot", outcome.transition_records)
        self.assertEqual(outcome.gate_evaluation.decision.verdict, GateVerdict.ALLOW)

    def test_invalid_transition_raises_before_state_change(self) -> None:
        session_fixture = build_session_creation_fixture()
        state = session_fixture["state"]

        controller = SessionController(GovernanceRuntime())
        with self.assertRaises(InvalidSessionTransitionError):
            controller.transition(
                state,
                action=SessionAction.CLOSE,
                context=RuntimeContext(
                    workspace_id="garage",
                    session_id=state.session_id,
                    pack_id=state.current_pack,
                    node_id=state.current_node,
                    action=SessionAction.CLOSE,
                ),
            )

    def test_stricter_rule_wins_in_gate_evaluation(self) -> None:
        runtime = GovernanceRuntime(
            rules=(
                GovernanceRule(
                    rule_id="global.allow-pause",
                    scope=GovernanceScope.GLOBAL,
                    gate_type=GateType.TRANSITION,
                    verdict=GateVerdict.ALLOW,
                    rationale="Default global rule allows the pause.",
                ),
                GovernanceRule(
                    rule_id="node.needs-approval",
                    scope=GovernanceScope.NODE,
                    gate_type=GateType.TRANSITION,
                    verdict=GateVerdict.NEEDS_APPROVAL,
                    rationale="This node requires creator approval before pausing.",
                    applies_to=("coding.intake", "pause"),
                    missing=("creator-approval",),
                ),
            )
        )

        evaluation = runtime.evaluate(
            RuntimeContext(
                workspace_id="garage",
                session_id="session.demo",
                pack_id="coding",
                node_id="coding.intake",
                action=SessionAction.PAUSE,
            ),
            GateType.TRANSITION,
        )

        self.assertEqual(evaluation.decision.verdict, GateVerdict.NEEDS_APPROVAL)
        self.assertEqual(evaluation.decision.missing, ("creator-approval",))

    def test_blocked_gate_raises(self) -> None:
        session_fixture = build_session_creation_fixture()
        state = session_fixture["state"]
        runtime = GovernanceRuntime(
            rules=(
                GovernanceRule(
                    rule_id="node.block-pause",
                    scope=GovernanceScope.NODE,
                    gate_type=GateType.TRANSITION,
                    verdict=GateVerdict.BLOCK,
                    rationale="Pause is blocked until evidence is linked.",
                    applies_to=("coding.intake", "pause"),
                ),
            )
        )

        controller = SessionController(runtime)
        with self.assertRaises(BlockedGateError):
            controller.transition(
                state,
                action=SessionAction.PAUSE,
                context=RuntimeContext(
                    workspace_id="garage",
                    session_id=state.session_id,
                    pack_id=state.current_pack,
                    node_id=state.current_node,
                    action=SessionAction.PAUSE,
                ),
            )


if __name__ == "__main__":
    unittest.main()
