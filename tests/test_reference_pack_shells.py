import unittest
from pathlib import Path

from continuity import GrowthTarget
from packs import load_pack_continuity_map
from registry import build_registry


class ReferencePackShellTests(unittest.TestCase):
    def test_registry_discovers_repo_reference_pack_shells(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        registry = build_registry(
            [
                repo_root / "packs" / "product-insights",
                repo_root / "packs" / "coding",
            ]
        )

        self.assertIn("product-insights", registry.packs)
        self.assertIn("coding", registry.packs)
        self.assertIn("product-insights.researcher", registry.roles)
        self.assertIn("product-insights.opportunity", registry.nodes)
        self.assertIn("product-insights.bridge-ready", registry.nodes)
        self.assertIn("coding.specifier", registry.roles)
        self.assertIn("coding.bridge-intake", registry.nodes)
        self.assertIn("coding.closeout", registry.nodes)
        self.assertIn("insight-pack", registry.artifacts)
        self.assertIn("review-record", registry.artifacts)
        self.assertIn("review-evidence", registry.evidence)
        self.assertIn("closeout-record", registry.evidence)
        self.assertIn("spec-bridge", registry.artifacts)

    def test_pack_continuity_maps_load(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        product_continuity_map = load_pack_continuity_map(
            repo_root / "packs" / "product-insights"
        )
        coding_continuity_map = load_pack_continuity_map(repo_root / "packs" / "coding")

        self.assertEqual(product_continuity_map.pack_id, "product-insights")
        self.assertEqual(len(product_continuity_map.candidate_families), 3)
        self.assertEqual(
            product_continuity_map.candidate_families[0].target,
            GrowthTarget.MEMORY,
        )
        self.assertIn("temporary-framing", product_continuity_map.blocked_patterns)

        self.assertEqual(coding_continuity_map.pack_id, "coding")
        self.assertEqual(len(coding_continuity_map.candidate_families), 3)
        self.assertEqual(
            coding_continuity_map.candidate_families[1].target,
            GrowthTarget.SKILL,
        )
        self.assertIn("temporary-workaround", coding_continuity_map.blocked_patterns)


if __name__ == "__main__":
    unittest.main()
