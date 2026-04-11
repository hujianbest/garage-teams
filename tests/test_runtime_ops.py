import json
import tempfile
import unittest
from pathlib import Path

from bootstrap import (
    BootstrapConfig,
    GarageLauncher,
    HealthStatus,
    LaunchMode,
    SessionApi,
    compute_install_diagnostics,
    launch_summary_diagnostics,
    recent_ops_events,
)


class RuntimeOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        recent_ops_events(clear=True)
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_launch_emits_ops_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rh = Path(tmp) / "rh"
            ws = Path(tmp) / "ws"
            for sub in ("profiles", "config", "adapters", "cache"):
                (rh / sub).mkdir(parents=True)
            (rh / "profiles" / "p.json").write_text(
                json.dumps({"providerId": "a", "modelId": "m", "adapterId": "ad"}),
                encoding="utf-8",
            )
            (rh / "adapters" / "ad.json").write_text(json.dumps({"providerId": "a"}), encoding="utf-8")
            GarageLauncher().launch(
                BootstrapConfig(
                    launch_mode=LaunchMode.CREATE,
                    source_root=self.repo_root,
                    runtime_home=rh,
                    workspace_root=ws,
                    workspace_id="w",
                    profile_id="p",
                    entry_surface="cli",
                    problem_kind="implementation",
                    entry_pack="coding",
                    entry_node="coding.bridge-intake",
                    goal="ops",
                )
            )
        events = recent_ops_events(clear=True)
        types = {e["event"] for e in events}
        self.assertIn("garage.launch.start", types)
        self.assertIn("garage.launch.complete", types)

    def test_compute_install_diagnostics_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rh = Path(tmp) / "rh"
            ws = Path(tmp) / "ws"
            ws.mkdir()
            for sub in ("profiles", "config", "adapters", "cache"):
                (rh / sub).mkdir(parents=True)
            (rh / "profiles" / "p.json").write_text(
                json.dumps({"providerId": "a", "modelId": "m", "adapterId": "ad"}),
                encoding="utf-8",
            )
            (rh / "adapters" / "ad.json").write_text(json.dumps({"providerId": "a"}), encoding="utf-8")
            diag = compute_install_diagnostics(
                source_root=self.repo_root,
                runtime_home=rh,
                workspace_root=ws,
                workspace_id="w",
                profile_id="p",
                entry_surface="cli",
            )
            self.assertEqual(diag["health"], HealthStatus.HEALTHY.value)
            self.assertTrue(diag["doctorOk"])

    def test_launch_summary_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rh = Path(tmp) / "rh"
            ws = Path(tmp) / "ws"
            for sub in ("profiles", "config", "adapters", "cache"):
                (rh / sub).mkdir(parents=True)
            (rh / "profiles" / "p.json").write_text(
                json.dumps({"providerId": "a", "modelId": "m", "adapterId": "ad"}),
                encoding="utf-8",
            )
            (rh / "adapters" / "ad.json").write_text(json.dumps({"providerId": "a"}), encoding="utf-8")
            result = SessionApi().create(
                BootstrapConfig(
                    launch_mode=LaunchMode.CREATE,
                    source_root=self.repo_root,
                    runtime_home=rh,
                    workspace_root=ws,
                    workspace_id="w",
                    profile_id="p",
                    entry_surface="cli",
                    problem_kind="implementation",
                    entry_pack="coding",
                    entry_node="coding.bridge-intake",
                    goal="ops",
                )
            )
        snap = launch_summary_diagnostics(result)
        self.assertEqual(snap["health"], HealthStatus.HEALTHY.value)
        self.assertEqual(snap["sessionId"], result.session_state.session_id)


if __name__ == "__main__":
    unittest.main()
