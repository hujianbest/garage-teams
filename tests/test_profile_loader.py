import json
import tempfile
import unittest
from pathlib import Path

from bootstrap import (
    BootstrapConfig,
    GarageLauncher,
    LaunchMode,
    RuntimeProfileResolutionError,
    load_runtime_profile,
)
from foundation import RuntimeHomeBinding


class RuntimeProfileLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_loader_reads_runtime_home_authority_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            runtime_home_root = Path(tmp_dir) / "runtime-home"
            self._write_json(
                runtime_home_root / "profiles" / "dogfood.json",
                {
                    "providerId": "provider.dogfood",
                    "modelId": "model.dogfood",
                    "adapterId": "adapter.dogfood",
                    "capabilities": ["workspace.read"],
                },
            )
            self._write_json(
                runtime_home_root / "config" / "providers.json",
                {
                    "defaults": {
                        "providerId": "provider.default",
                        "modelId": "model.default",
                        "adapterId": "adapter.default",
                        "capabilities": ["workspace.write"],
                    }
                },
            )
            self._write_json(
                runtime_home_root / "adapters" / "adapter.dogfood.json",
                {
                    "providerId": "provider.dogfood",
                    "modelId": "model.dogfood",
                    "transport": "cli",
                },
            )

            profile = load_runtime_profile(
                RuntimeHomeBinding.from_root(runtime_home_root),
                profile_id="dogfood",
                runtime_capabilities=("workspace.write",),
                provider_hints={"temperature": "low"},
            )

            self.assertEqual(profile.provider_id, "provider.dogfood")
            self.assertEqual(profile.model_id, "model.dogfood")
            self.assertEqual(profile.adapter_id, "adapter.dogfood")
            self.assertEqual(profile.provider_hints["temperature"], "low")
            self.assertEqual(profile.adapter_settings["transport"], "cli")
            self.assertEqual(profile.capabilities, ("workspace.write", "workspace.read"))
            self.assertEqual(len(profile.authority_sources), 3)

    def test_loader_rejects_host_authority_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            runtime_home_root = Path(tmp_dir) / "runtime-home"
            self._write_json(
                runtime_home_root / "profiles" / "dogfood.json",
                {"providerId": "provider.dogfood"},
            )

            with self.assertRaises(RuntimeProfileResolutionError):
                load_runtime_profile(
                    RuntimeHomeBinding.from_root(runtime_home_root),
                    profile_id="dogfood",
                    provider_hints={"providerId": "provider.host"},
                )

    def test_launcher_uses_runtime_home_profile_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            runtime_home_root = Path(tmp_dir) / "runtime-home"
            workspace_root = Path(tmp_dir) / "workspace"
            self._write_json(
                runtime_home_root / "profiles" / "dogfood.json",
                {
                    "providerId": "provider.dogfood",
                    "modelId": "model.dogfood",
                    "adapterId": "adapter.dogfood",
                },
            )
            self._write_json(
                runtime_home_root / "adapters" / "adapter.dogfood.json",
                {"providerId": "provider.dogfood", "transport": "local"},
            )

            result = GarageLauncher().launch(
                BootstrapConfig(
                    launch_mode=LaunchMode.CREATE,
                    source_root=self.repo_root,
                    runtime_home=runtime_home_root,
                    workspace_root=workspace_root,
                    workspace_id="garage-workspace",
                    profile_id="dogfood",
                    entry_surface="cli",
                    problem_kind="implementation",
                    entry_pack="coding",
                    entry_node="coding.bridge-intake",
                    goal="Resolve runtime-home authority before execution.",
                    provider_hints={"temperature": "low"},
                )
            )

            self.assertEqual(result.services.profile.provider_id, "provider.dogfood")
            self.assertEqual(result.services.profile.model_id, "model.dogfood")
            self.assertEqual(result.services.profile.adapter_id, "adapter.dogfood")
            self.assertEqual(result.services.profile.provider_hints["temperature"], "low")
            self.assertEqual(result.services.profile.adapter_settings["transport"], "local")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
