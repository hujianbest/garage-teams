import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bootstrap.install_layout import (
    RUNTIME_HOME_SCHEMA_VERSION,
    default_runtime_home_path,
    resolve_runtime_home,
    resolve_source_root,
    resolve_workspace_root,
)


class InstallLayoutTests(unittest.TestCase):
    def test_runtime_home_schema_constant(self) -> None:
        self.assertEqual(RUNTIME_HOME_SCHEMA_VERSION, "1")

    def test_resolve_runtime_home_explicit_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            explicit = base / "rh"
            explicit.mkdir()
            env_dir = base / "from_env"
            env_dir.mkdir()
            with mock.patch.dict(os.environ, {"GARAGE_RUNTIME_HOME": str(env_dir)}, clear=False):
                got = resolve_runtime_home(explicit)
            self.assertEqual(got, explicit.resolve())

    def test_resolve_runtime_home_env_second(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_home = Path(tmp) / "env-rh"
            env_home.mkdir()
            with mock.patch.dict(os.environ, {"GARAGE_RUNTIME_HOME": str(env_home)}):
                got = resolve_runtime_home(None)
            self.assertEqual(got, env_home.resolve())

    def test_default_runtime_home_windows(self) -> None:
        import bootstrap.install_layout as il

        with mock.patch.object(il.sys, "platform", "win32"):
            with mock.patch.dict(os.environ, {"LOCALAPPDATA": r"C:\Users\me\AppData\Local"}, clear=False):
                p = default_runtime_home_path()
        self.assertTrue(str(p).replace("\\", "/").endswith("Garage/runtime-home"))

    def test_default_runtime_home_posix(self) -> None:
        import bootstrap.install_layout as il

        with mock.patch.object(il.sys, "platform", "linux"):
            with mock.patch.dict(os.environ, {}, clear=True):
                with mock.patch("pathlib.Path.home", return_value=Path("/home/u")):
                    p = default_runtime_home_path()
        expect = Path("/home/u/.local/state/garage/runtime-home")
        self.assertEqual(p, expect.resolve())

    def test_resolve_workspace_root_defaults_to_cwd(self) -> None:
        import bootstrap.install_layout as il

        with mock.patch.object(il.Path, "cwd", return_value=Path("/tmp/ws")):
            self.assertEqual(resolve_workspace_root(None), Path("/tmp/ws").resolve())

    def test_resolve_source_root_env(self) -> None:
        import bootstrap.install_layout as il

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "srcroot"
            src.mkdir()
            with mock.patch.dict(os.environ, {"GARAGE_SOURCE_ROOT": str(src)}):
                with mock.patch.object(il.Path, "cwd", return_value=Path("/tmp/other")):
                    self.assertEqual(resolve_source_root(None), src.resolve())


if __name__ == "__main__":
    unittest.main()
