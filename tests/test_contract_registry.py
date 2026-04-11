import json
import tempfile
import unittest
from pathlib import Path

from registry import RegistryLoadError, build_registry


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class ContractRegistryTests(unittest.TestCase):
    def test_build_registry_loads_reference_pack_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            pack_root = Path(tmp_dir) / "packs" / "coding"
            contracts_root = pack_root / "contracts"

            _write_json(
                contracts_root / "manifest.json",
                {
                    "packId": "coding",
                    "packVersion": "0.1.0",
                    "contractVersion": "v1alpha1",
                    "entryNodeRefs": ["coding.intake"],
                    "roleRefs": ["coding.implementer"],
                    "nodeRefs": ["coding.intake"],
                    "supportedArtifactRoles": ["spec-brief"],
                },
            )
            _write_json(
                contracts_root / "roles" / "implementer.json",
                {
                    "roleId": "coding.implementer",
                    "packId": "coding",
                    "contractVersion": "v1alpha1",
                    "responsibility": "Implement the current coding task.",
                    "readableArtifactRoles": ["spec-brief"],
                    "writableArtifactRoles": ["spec-brief"],
                    "triggerableNodes": ["coding.intake"],
                    "handoffScope": ["in-pack", "cross-pack"],
                },
            )
            _write_json(
                contracts_root / "nodes" / "intake.json",
                {
                    "nodeId": "coding.intake",
                    "packId": "coding",
                    "contractVersion": "v1alpha1",
                    "intent": "Start the coding session.",
                    "inputArtifactRoles": ["spec-brief"],
                    "outputArtifactRoles": ["spec-brief"],
                    "allowedTransitions": ["coding.intake"],
                    "humanConfirmationRequired": False,
                    "parallelizable": False,
                },
            )
            _write_json(
                contracts_root / "artifacts" / "spec-brief.json",
                {
                    "artifactRole": "spec-brief",
                    "contractVersion": "v1alpha1",
                    "primaryFormat": "markdown",
                    "authorityRule": "latest-wins",
                    "readWriteSemantics": "authoritative-current-slot",
                },
            )
            _write_json(
                contracts_root / "evidence" / "verification.json",
                {
                    "evidenceType": "verification",
                    "contractVersion": "v1alpha1",
                    "sourcePointer": "evidence/verification.md",
                    "relatedSession": "session.demo",
                    "relatedNode": "coding.intake",
                    "relatedArtifacts": ["spec-brief"],
                    "outcome": "passed",
                    "lineageLinks": ["artifact->evidence"],
                },
            )

            registry = build_registry([pack_root])

            self.assertIn("coding", registry.packs)
            self.assertIn("coding.implementer", registry.roles)
            self.assertIn("coding.intake", registry.nodes)
            self.assertIn("spec-brief", registry.artifacts)
            self.assertIn("verification", registry.evidence)

    def test_build_registry_rejects_missing_manifest_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            pack_root = Path(tmp_dir) / "packs" / "product-insights"
            contracts_root = pack_root / "contracts"

            _write_json(
                contracts_root / "manifest.json",
                {
                    "packId": "product-insights",
                    "packVersion": "0.1.0",
                    "contractVersion": "v1alpha1",
                    "entryNodeRefs": ["product-insights.entry"],
                    "roleRefs": ["product-insights.researcher"],
                    "nodeRefs": ["product-insights.entry"],
                    "supportedArtifactRoles": ["concept-brief"],
                },
            )
            _write_json(
                contracts_root / "roles" / "researcher.json",
                {
                    "roleId": "product-insights.researcher",
                    "packId": "product-insights",
                    "contractVersion": "v1alpha1",
                    "responsibility": "Research product opportunities.",
                    "readableArtifactRoles": ["concept-brief"],
                    "writableArtifactRoles": ["concept-brief"],
                    "triggerableNodes": ["product-insights.entry"],
                    "handoffScope": ["in-pack"],
                },
            )

            with self.assertRaises(RegistryLoadError):
                build_registry([pack_root])


if __name__ == "__main__":
    unittest.main()
