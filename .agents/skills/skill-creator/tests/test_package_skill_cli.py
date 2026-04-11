import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PackageSkillCliTests(unittest.TestCase):
    def test_package_skill_cli_succeeds_with_default_windows_encoding(self):
        repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            skill_dir = tmp_path / "demo-skill"
            out_dir = tmp_path / "dist"
            skill_dir.mkdir()
            out_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: demo-skill\n"
                "description: Package this skill on Windows\n"
                "---\n"
                "\n"
                "# Demo Skill\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, "-m", "scripts.package_skill", str(skill_dir), str(out_dir)],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((out_dir / "demo-skill.skill").exists())


if __name__ == "__main__":
    unittest.main()
