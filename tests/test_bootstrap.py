import tempfile
import unittest
from pathlib import Path

from bootstrap import BootstrapConfig, BootstrapError, GarageLauncher, LaunchMode
from core import SessionStatus
from session import SessionAction
from session.lifecycle import apply_action


class BootstrapLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.launcher = GarageLauncher()

    def test_launcher_create_builds_runtime_services_and_persists_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir) / "workspace"
            runtime_home = Path(tmp_dir) / "runtime-home"
            result = self.launcher.launch(
                BootstrapConfig(
                    launch_mode=LaunchMode.CREATE,
                    source_root=self.repo_root,
                    runtime_home=runtime_home,
                    workspace_root=workspace_root,
                    workspace_id="garage-workspace",
                    profile_id="dogfood",
                    entry_surface="cli",
                    problem_kind="implementation",
                    entry_pack="coding",
                    entry_node="coding.bridge-intake",
                    goal="Land the bootstrap slice.",
                )
            )

            self.assertEqual(result.services.host.adapter_id, "cli")
            self.assertEqual(result.session_state.session_status, SessionStatus.ACTIVE)
            self.assertTrue(result.session_route.file_path.exists())
            self.assertIsNotNone(result.services.execution_runtime)
            self.assertIn("coding", result.services.registry.packs)
            self.assertIn("product-insights", result.services.registry.packs)

    def test_launcher_resume_restores_session_from_workspace_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir) / "workspace"
            runtime_home = Path(tmp_dir) / "runtime-home"
            created = self.launcher.launch(
                BootstrapConfig(
                    launch_mode=LaunchMode.CREATE,
                    source_root=self.repo_root,
                    runtime_home=runtime_home,
                    workspace_root=workspace_root,
                    workspace_id="garage-workspace",
                    profile_id="dogfood",
                    entry_surface="cli",
                    problem_kind="implementation",
                    entry_pack="coding",
                    entry_node="coding.bridge-intake",
                    goal="Land the bootstrap slice.",
                )
            )
            paused_state = apply_action(
                created.session_state,
                SessionAction.PAUSE,
                summary="Paused between host entry surfaces.",
            )
            created.services.surfaces.write_session_state(paused_state)

            resumed = self.launcher.launch(
                BootstrapConfig(
                    launch_mode=LaunchMode.RESUME,
                    source_root=self.repo_root,
                    runtime_home=runtime_home,
                    workspace_root=workspace_root,
                    workspace_id="garage-workspace",
                    profile_id="dogfood",
                    entry_surface="ide",
                    session_id=paused_state.session_id,
                )
            )

            self.assertEqual(resumed.session_state.session_status, SessionStatus.ACTIVE)
            self.assertEqual(resumed.session_state.session_id, paused_state.session_id)
            self.assertEqual(resumed.services.host.adapter_id, "ide")

    def test_launcher_attach_reuses_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir) / "workspace"
            runtime_home = Path(tmp_dir) / "runtime-home"
            created = self.launcher.launch(
                BootstrapConfig(
                    launch_mode=LaunchMode.CREATE,
                    source_root=self.repo_root,
                    runtime_home=runtime_home,
                    workspace_root=workspace_root,
                    workspace_id="garage-workspace",
                    profile_id="dogfood",
                    entry_surface="cli",
                    problem_kind="implementation",
                    entry_pack="coding",
                    entry_node="coding.bridge-intake",
                    goal="Land the bootstrap slice.",
                )
            )

            attached = self.launcher.launch(
                BootstrapConfig(
                    launch_mode=LaunchMode.ATTACH,
                    source_root=self.repo_root,
                    runtime_home=runtime_home,
                    workspace_root=workspace_root,
                    workspace_id="garage-workspace",
                    profile_id="dogfood",
                    entry_surface="chat",
                    session_id=created.session_state.session_id,
                )
            )

            self.assertEqual(attached.session_state.session_id, created.session_state.session_id)
            self.assertEqual(attached.session_state.session_status, SessionStatus.ACTIVE)
            self.assertEqual(attached.services.host.adapter_id, "chat")

    def test_launcher_requires_workspace_root(self) -> None:
        with self.assertRaises(BootstrapError):
            self.launcher.launch(
                BootstrapConfig(
                    launch_mode=LaunchMode.CREATE,
                    source_root=self.repo_root,
                    runtime_home=self.repo_root / ".runtime-home",
                    problem_kind="implementation",
                    entry_pack="coding",
                    entry_node="coding.bridge-intake",
                    goal="Land the bootstrap slice.",
                )
            )


if __name__ == "__main__":
    unittest.main()
