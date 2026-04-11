import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from bootstrap import BootstrapConfig, LaunchMode, SessionApi
from bootstrap.cli import main


class GarageCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_cli_create_prints_launch_summary_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            runtime_home = Path(tmp_dir) / "runtime-home"
            workspace_root = Path(tmp_dir) / "workspace"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "create",
                        "--source-root",
                        str(self.repo_root),
                        "--runtime-home",
                        str(runtime_home),
                        "--workspace-root",
                        str(workspace_root),
                        "--workspace-id",
                        "garage-workspace",
                        "--profile-id",
                        "dogfood",
                        "--problem-kind",
                        "implementation",
                        "--entry-pack",
                        "coding",
                        "--entry-node",
                        "coding.bridge-intake",
                        "--goal",
                        "Land the CLI entry slice.",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["hostAdapterId"], "cli")
            self.assertEqual(payload["profileId"], "dogfood")
            self.assertEqual(payload["workspaceId"], "garage-workspace")
            self.assertTrue(Path(payload["sessionFile"]).exists())

    def test_cli_resume_reuses_existing_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            runtime_home = Path(tmp_dir) / "runtime-home"
            workspace_root = Path(tmp_dir) / "workspace"
            created = SessionApi().create(
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
                    goal="Land the CLI entry slice.",
                )
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "resume",
                        "--source-root",
                        str(self.repo_root),
                        "--runtime-home",
                        str(runtime_home),
                        "--workspace-root",
                        str(workspace_root),
                        "--workspace-id",
                        "garage-workspace",
                        "--profile-id",
                        "dogfood",
                        "--session-id",
                        created.session_state.session_id,
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["sessionId"], created.session_state.session_id)
            self.assertEqual(payload["hostAdapterId"], "cli")


if __name__ == "__main__":
    unittest.main()
