"""F016 T1 tests: STYLE template loader + 3 packaged templates."""

from __future__ import annotations

from pathlib import Path

from garage_os.memory_activation.templates import (
    SUPPORTED_LANGUAGES,
    parse_style_template,
    template_path,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKS_ROOT = REPO_ROOT / "packs"


# T1.1
class TestSupportedLanguages:
    def test_supported_langs(self) -> None:
        assert SUPPORTED_LANGUAGES == ("python", "typescript", "markdown")


# T1.2
class TestTemplatePath:
    def test_constructs_path(self, tmp_path: Path) -> None:
        path = template_path(tmp_path, "python")
        assert path == tmp_path / "garage" / "templates" / "style-templates" / "python.md"


# T1.3 — packaged templates exist + parse
class TestPackagedTemplates:
    def test_python_template_parses(self) -> None:
        path = template_path(PACKS_ROOT, "python")
        assert path.is_file(), "F016 T1: packs/garage/templates/style-templates/python.md missing"
        entries = parse_style_template(path)
        assert len(entries) >= 5, f"python template should have ≥ 5 entries, got {len(entries)}"
        # Validate kebab-case topic format
        for topic, content in entries:
            assert topic.replace("-", "").replace("_", "").isalnum(), f"topic '{topic}' is not kebab-case"
            assert len(content) > 10, f"content '{content}' is too short"

    def test_typescript_template_parses(self) -> None:
        path = template_path(PACKS_ROOT, "typescript")
        assert path.is_file()
        entries = parse_style_template(path)
        assert len(entries) >= 5

    def test_markdown_template_parses(self) -> None:
        path = template_path(PACKS_ROOT, "markdown")
        assert path.is_file()
        entries = parse_style_template(path)
        assert len(entries) >= 5


# T1.4 — parse_style_template edge cases
class TestParseEdges:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert parse_style_template(tmp_path / "nonexistent.md") == []

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.md"
        path.write_text("", encoding="utf-8")
        assert parse_style_template(path) == []

    def test_no_matching_lines_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "no-style.md"
        path.write_text("# Title\n\nJust prose, no style entries.\n", encoding="utf-8")
        assert parse_style_template(path) == []

    def test_skips_unparseable_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "mixed.md"
        path.write_text(
            "# Title\n\n"
            "Some prose\n\n"
            "- valid-topic: This is the content.\n"
            "  not a topic line\n"
            "- another-topic: More content here.\n",
            encoding="utf-8",
        )
        entries = parse_style_template(path)
        assert len(entries) == 2
        assert entries[0] == ("valid-topic", "This is the content.")
        assert entries[1] == ("another-topic", "More content here.")

    def test_handles_backtick_topics(self, tmp_path: Path) -> None:
        path = tmp_path / "backtick.md"
        path.write_text("- `prefer-x`: Use X over Y.\n", encoding="utf-8")
        entries = parse_style_template(path)
        assert entries == [("prefer-x", "Use X over Y.")]
