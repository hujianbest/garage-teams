import tempfile
import unittest
from pathlib import Path

from scripts.quick_validate import validate_skill
from scripts.utils import parse_skill_md


class Utf8SkillReadingTests(unittest.TestCase):
    def test_validate_skill_reads_utf8_skill_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_dir = Path(tmp_dir) / "demo-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: demo-skill\n"
                "description: UTF-8 中文描述应当通过校验\n"
                "---\n"
                "\n"
                "# Demo Skill\n",
                encoding="utf-8",
            )

            valid, message = validate_skill(skill_dir)

            self.assertTrue(valid, message)
            self.assertEqual(message, "Skill is valid!")

    def test_parse_skill_md_reads_utf8_skill_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_dir = Path(tmp_dir) / "demo-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: demo-skill\n"
                "description: UTF-8 中文描述应当被正确解析\n"
                "---\n"
                "\n"
                "# Demo Skill\n",
                encoding="utf-8",
            )

            name, description, content = parse_skill_md(skill_dir)

            self.assertEqual(name, "demo-skill")
            self.assertEqual(description, "UTF-8 中文描述应当被正确解析")
            self.assertIn("UTF-8 中文描述应当被正确解析", content)


if __name__ == "__main__":
    unittest.main()
