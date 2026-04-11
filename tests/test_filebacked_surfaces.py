import tempfile
import unittest
from pathlib import Path

from core import ArtifactDescriptor, AuthorityMarker, EvidenceRecord, ObjectRef
from foundation import WorkspaceBinding
from surfaces import FileBackedSurfaceManager


class FileBackedSurfaceTests(unittest.TestCase):
    def test_artifact_and_evidence_materialize_to_canonical_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = WorkspaceBinding.from_root("garage-test", Path(tmp_dir))
            manager = FileBackedSurfaceManager(workspace)
            descriptor = ArtifactDescriptor(
                artifact_id="design--session-routing--a42",
                intent_ref=ObjectRef(kind="artifact-intent", object_id="artifact-intent.demo"),
                artifact_role="design-brief",
                pack_id="coding",
                primary_format="markdown",
                locator="artifacts/coding/design-brief/design--session-routing--a42.md",
            )
            authority = AuthorityMarker(
                artifact_ref=ObjectRef(kind="artifact", object_id=descriptor.artifact_id),
                is_authoritative=True,
            )
            route = manager.write_artifact(
                descriptor,
                body="Artifact routing design body.",
                authority=authority,
            )

            self.assertTrue(route.file_path.exists())
            self.assertTrue(route.sidecar_path.exists())
            self.assertIn(str(workspace.artifacts_root), str(route.file_path))
            self.assertIn(str(workspace.garage_root), str(route.sidecar_path))

            evidence = EvidenceRecord(
                evidence_id="verification--design-a42--e17",
                evidence_type="verification",
                session_ref=ObjectRef(kind="session-state", object_id="session.demo"),
                node_ref=ObjectRef(kind="node", object_id="coding.verify"),
                artifact_refs=(ObjectRef(kind="artifact", object_id=descriptor.artifact_id),),
                outcome_or_verdict="passed",
                source_pointer="tests/verification.md",
            )
            evidence_route = manager.emit_evidence(
                pack_id="coding",
                record=evidence,
                summary="Verification passed for the design brief.",
            )

            self.assertTrue(evidence_route.file_path.exists())
            self.assertTrue(evidence_route.sidecar_path.exists())
            self.assertIn(str(workspace.evidence_root), str(evidence_route.file_path))

    def test_supersede_and_archive_keep_history_separate_from_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = WorkspaceBinding.from_root("garage-test", Path(tmp_dir))
            manager = FileBackedSurfaceManager(workspace)
            descriptor = ArtifactDescriptor(
                artifact_id="design--session-routing--a42",
                intent_ref=ObjectRef(kind="artifact-intent", object_id="artifact-intent.demo"),
                artifact_role="design-brief",
                pack_id="coding",
                primary_format="markdown",
                locator="artifacts/coding/design-brief/design--session-routing--a42.md",
            )
            authority = AuthorityMarker(
                artifact_ref=ObjectRef(kind="artifact", object_id=descriptor.artifact_id),
                is_authoritative=True,
            )
            route = manager.write_artifact(
                descriptor,
                body="Current authoritative version.",
                authority=authority,
            )

            archived_route = manager.archive_artifact(
                descriptor=descriptor,
                authority=authority,
                route=route,
            )
            old_authority, new_authority, lineage = manager.supersede_artifact(
                current_authority=authority,
                superseding_descriptor=ArtifactDescriptor(
                    artifact_id="design--session-routing--a43",
                    intent_ref=descriptor.intent_ref,
                    artifact_role=descriptor.artifact_role,
                    pack_id=descriptor.pack_id,
                    primary_format=descriptor.primary_format,
                    locator="artifacts/coding/design-brief/design--session-routing--a43.md",
                ),
                link_id="lineage.supersede.demo",
            )

            self.assertTrue(archived_route.file_path.exists())
            self.assertFalse(old_authority.is_authoritative)
            self.assertTrue(new_authority.is_authoritative)
            self.assertEqual(lineage.source_ref.object_id, descriptor.artifact_id)
            self.assertEqual(lineage.target_ref.object_id, "design--session-routing--a43")


if __name__ == "__main__":
    unittest.main()
