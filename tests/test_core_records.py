import unittest

from core import (
    APPEND_ONLY_RECORD_TYPES,
    CURRENT_SLOT_RECORD_TYPES,
    ArtifactDescriptor,
    ArtifactIntent,
    PolicySet,
    SessionIntent,
    build_evidence_lineage_fixture,
    build_gate_decision_fixture,
    build_handoff_fixture,
    build_session_creation_fixture,
    write_semantics_for,
)
from core.records import WriteSemantics


class CoreRecordTests(unittest.TestCase):
    def test_write_semantics_match_record_layers(self) -> None:
        for record_type in CURRENT_SLOT_RECORD_TYPES:
            self.assertEqual(write_semantics_for(record_type), WriteSemantics.CURRENT_SLOT)

        for record_type in APPEND_ONLY_RECORD_TYPES:
            self.assertEqual(write_semantics_for(record_type), WriteSemantics.APPEND_ONLY)

        for record_type in (SessionIntent, ArtifactIntent, ArtifactDescriptor, PolicySet):
            self.assertEqual(write_semantics_for(record_type), WriteSemantics.IMMUTABLE)

    def test_fixtures_keep_minimum_lineage_links(self) -> None:
        session_fixture = build_session_creation_fixture()
        handoff_fixture = build_handoff_fixture()
        gate_fixture = build_gate_decision_fixture()
        evidence_fixture = build_evidence_lineage_fixture()

        self.assertIn("state", session_fixture)
        self.assertIn("handoff", handoff_fixture)
        self.assertIn("decision", gate_fixture)
        self.assertEqual(
            evidence_fixture["evidence"].lineage_link_refs[0].object_id,
            evidence_fixture["lineage"].link_id,
        )


if __name__ == "__main__":
    unittest.main()
