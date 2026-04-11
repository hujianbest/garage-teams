import unittest

from continuity import ForbiddenPromotionPathError, GrowthEngine, GrowthTarget, MemoryEntry
from core import EvidenceRecord, ObjectRef


class GrowthEngineTests(unittest.TestCase):
    def test_evidence_becomes_candidate_then_growth_proposal(self) -> None:
        engine = GrowthEngine()
        evidence = EvidenceRecord(
            evidence_id="evidence.verify.demo",
            evidence_type="verification",
            session_ref=ObjectRef(kind="session-state", object_id="session.demo"),
            node_ref=ObjectRef(kind="node", object_id="coding.verify"),
            artifact_refs=(ObjectRef(kind="artifact", object_id="artifact.runtime.skeleton"),),
            outcome_or_verdict="passed",
            source_pointer="evidence/verification.md",
        )

        candidate = engine.candidate_from_evidence(
            workspace_id="garage",
            candidate_id="candidate.runtime.memory",
            target=GrowthTarget.MEMORY,
            summary="Remember the repository prefers src layout for runtime code.",
            rationale="This preference was confirmed during runtime scaffolding.",
            evidence=evidence,
        )
        proposal = engine.draft_proposal(
            proposal_id="proposal.runtime.memory",
            candidate=candidate,
            risk_level="low",
            suggested_governance_actions=("review", "approval"),
        )
        decision, applied = engine.apply_decision(
            decision_id="decision.runtime.memory",
            proposal=proposal,
            accepted=True,
            rationale="The preference is stable and workspace-relevant.",
        )

        self.assertEqual(candidate.source_evidence_refs[0].object_id, evidence.evidence_id)
        self.assertEqual(proposal.target, GrowthTarget.MEMORY)
        self.assertTrue(decision.accepted)
        self.assertIsInstance(applied, MemoryEntry)
        self.assertEqual(applied.source_proposal_ref.object_id, proposal.proposal_id)

    def test_forbidden_session_promotion_raises(self) -> None:
        engine = GrowthEngine()

        with self.assertRaises(ForbiddenPromotionPathError):
            engine.forbid_session_promotion()


if __name__ == "__main__":
    unittest.main()
