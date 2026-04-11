from pathlib import Path
import tempfile
import unittest

from foundation import (
    RuntimeHomeBinding,
    RuntimeTopology,
    SourceRootBinding,
    TopologyBindingError,
    WorkspaceBinding,
    WorkspaceMode,
)


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
        self.assertEqual(binding.mode, WorkspaceMode.EXTERNAL)

    def test_source_root_binding_exposes_authoring_surfaces(self) -> None:
        repo_root = Path("d:/Garage")

        source_root = SourceRootBinding.from_root(repo_root)

        self.assertEqual(source_root.root, repo_root.resolve())
        self.assertEqual(source_root.docs_root, repo_root.resolve() / "docs")
        self.assertEqual(source_root.packs_root, repo_root.resolve() / "packs")
        self.assertEqual(source_root.agent_skills_root, repo_root.resolve() / ".agents" / "skills")
        self.assertEqual(source_root.src_root, repo_root.resolve() / "src")
        self.assertEqual(source_root.tests_root, repo_root.resolve() / "tests")

    def test_runtime_home_binding_keeps_profiles_and_cache_outside_workspace_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            runtime_home = RuntimeHomeBinding.from_root(Path(tmp_dir) / "runtime-home")

            self.assertTrue(str(runtime_home.profiles_root).endswith("profiles"))
            self.assertTrue(str(runtime_home.config_root).endswith("config"))
            self.assertTrue(str(runtime_home.cache_root).endswith("cache"))
            self.assertTrue(str(runtime_home.adapters_root).endswith("adapters"))

    def test_source_coupled_topology_keeps_workspace_and_runtime_home_distinct(self) -> None:
        repo_root = Path("d:/Garage")
        with tempfile.TemporaryDirectory() as tmp_dir:
            topology = RuntimeTopology.source_coupled(
                source_root=repo_root,
                runtime_home=Path(tmp_dir) / "runtime-home",
                workspace_id="garage-dogfood",
            )

            self.assertEqual(topology.workspace.mode, WorkspaceMode.SOURCE_COUPLED)
            self.assertEqual(topology.source_root.root, topology.workspace.root)
            self.assertNotEqual(topology.runtime_home.root, topology.workspace.root)

    def test_runtime_home_cannot_live_inside_workspace_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir) / "workspace"
            workspace = WorkspaceBinding.from_root("garage-test", workspace_root)
            topology = RuntimeTopology(
                source_root=SourceRootBinding.from_root(Path("d:/Garage")),
                runtime_home=RuntimeHomeBinding.from_root(workspace.garage_root / "runtime-home"),
                workspace=workspace,
            )

            with self.assertRaises(TopologyBindingError):
                topology.validated()


if __name__ == "__main__":
    unittest.main()
