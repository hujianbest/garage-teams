from pathlib import Path
import unittest

from foundation import WorkspaceBinding


class WorkspaceBindingTests(unittest.TestCase):
    def test_from_root_builds_workspace_first_surfaces(self) -> None:
        root = Path("d:/Garage")

        binding = WorkspaceBinding.from_root("garage-main", root)

        self.assertEqual(binding.workspace_id, "garage-main")
        self.assertEqual(binding.root, root.resolve())
        self.assertEqual(binding.artifacts_root, root.resolve() / "artifacts")
        self.assertEqual(binding.evidence_root, root.resolve() / "evidence")
        self.assertEqual(binding.sessions_root, root.resolve() / "sessions")
        self.assertEqual(binding.archives_root, root.resolve() / "archives")
        self.assertEqual(binding.garage_root, root.resolve() / ".garage")


if __name__ == "__main__":
    unittest.main()
