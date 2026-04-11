import unittest

from bridge import (
    AcceptanceVerdict,
    build_reference_bridge_walkthrough_fixture,
    routing_for_verdict,
)
from core import SessionStatus
from session import SessionAction


class BridgeWorkflowTests(unittest.TestCase):
    def test_verdict_routes_align_with_session_lifecycle(self) -> None:
        expected = {
            AcceptanceVerdict.ACCEPTED: (SessionAction.RESUME, SessionStatus.ACTIVE, False),
            AcceptanceVerdict.ACCEPTED_WITH_GAPS: (
                SessionAction.RESUME,
                SessionStatus.ACTIVE,
                False,
            ),
            AcceptanceVerdict.NEEDS_CLARIFICATION: (
                SessionAction.ENTER_REVIEW_HOLD,
                SessionStatus.REVIEW_HOLD,
                True,
            ),
            AcceptanceVerdict.REJECTED_RETURN_UPSTREAM: (
                SessionAction.ENTER_REWORK,
                SessionStatus.REWORK,
                True,
            ),
        }

        for verdict, expectation in expected.items():
            route = routing_for_verdict(verdict)
            self.assertEqual(
                (route.session_action, route.next_status, route.needs_rework_request),
                expectation,
            )

    def test_clarification_path_creates_rework_request_and_review_hold(self) -> None:
        walkthrough = build_reference_bridge_walkthrough_fixture()
        clarification = walkthrough.clarification_path

        self.assertEqual(clarification.verdict, AcceptanceVerdict.NEEDS_CLARIFICATION)
        self.assertEqual(clarification.next_state.session_status, SessionStatus.REVIEW_HOLD)
        self.assertIsNotNone(clarification.rework_request)
        assert clarification.rework_request is not None
        self.assertIn("clarify scope boundary", clarification.rework_request.missing_items)
        self.assertEqual(clarification.handoff_record.acceptance, "needs-clarification")

    def test_walkthrough_keeps_bridge_acceptance_and_closeout_traceable(self) -> None:
        walkthrough = build_reference_bridge_walkthrough_fixture()
        accepted = walkthrough.accepted_path

        self.assertEqual(accepted.verdict, AcceptanceVerdict.ACCEPTED_WITH_GAPS)
        self.assertEqual(accepted.next_state.session_status, SessionStatus.ACTIVE)
        self.assertIsNone(accepted.rework_request)
        self.assertEqual(accepted.acceptance_evidence.evidence_type, "bridge-lineage")
        self.assertEqual(
            accepted.lineage_links[-1].target_ref.object_id,
            accepted.acceptance_evidence.evidence_id,
        )
        self.assertEqual(
            walkthrough.closeout_lineage.source_ref.object_id,
            walkthrough.bridge_surface.bridge_artifact.artifact_id,
        )
        self.assertEqual(walkthrough.closeout_evidence.evidence_type, "closeout-record")


if __name__ == "__main__":
    unittest.main()
