"""F012-C T3 tests: sensitive_scan helper (5 SENSITIVE_RULES + binary skip)."""

from __future__ import annotations

from pathlib import Path

from garage_os.adapter.installer.pack_install import (
    SENSITIVE_RULES,
    TEXT_EXTENSIONS,
    sensitive_scan,
)


class TestSensitiveRules:
    def test_5_rules_present(self) -> None:
        rule_names = [r[0] for r in SENSITIVE_RULES]
        assert sorted(rule_names) == ["api_key", "password", "private_key", "secret", "token"]

    def test_text_extensions_includes_common(self) -> None:
        for ext in (".md", ".py", ".json", ".yaml", ".env", ".gitignore"):
            assert ext in TEXT_EXTENSIONS


class TestSensitiveScanFiveCategories:
    """5 类 SENSITIVE_RULES fixture all hit (SM-1204 + INV-F12-5)."""

    def test_password_match(self, tmp_path: Path) -> None:
        (tmp_path / "config.env").write_text("password=abc123\n", encoding="utf-8")
        matches, skipped = sensitive_scan(tmp_path)
        assert any(m.rule == "password" for m in matches)
        assert skipped == 0

    def test_api_key_match(self, tmp_path: Path) -> None:
        (tmp_path / "settings.yaml").write_text("api_key: sk-12345\n", encoding="utf-8")
        matches, _ = sensitive_scan(tmp_path)
        assert any(m.rule == "api_key" for m in matches)

    def test_secret_match(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text('{"secret": "s3cret-val"}\n', encoding="utf-8")
        matches, _ = sensitive_scan(tmp_path)
        assert any(m.rule == "secret" for m in matches)

    def test_token_match(self, tmp_path: Path) -> None:
        (tmp_path / "auth.txt").write_text("token = abcdef123\n", encoding="utf-8")
        matches, _ = sensitive_scan(tmp_path)
        assert any(m.rule == "token" for m in matches)

    def test_private_key_match(self, tmp_path: Path) -> None:
        (tmp_path / "key.txt").write_text(
            "-----BEGIN RSA PRIVATE KEY-----\nMIIEvQ...\n-----END RSA PRIVATE KEY-----\n",
            encoding="utf-8",
        )
        matches, _ = sensitive_scan(tmp_path)
        assert any(m.rule == "private_key" for m in matches)


class TestSensitiveScanBinarySkip:
    def test_binary_extension_skipped(self, tmp_path: Path) -> None:
        # .png is not in TEXT_EXTENSIONS
        (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n password=should-not-trigger \r\n")
        matches, skipped = sensitive_scan(tmp_path)
        # .png skipped → password regex inside binary not detected
        assert skipped == 1
        assert not any(m.rule == "password" for m in matches)

    def test_clean_pack_no_matches(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text("# Hello\n\nNo secrets here.\n", encoding="utf-8")
        matches, skipped = sensitive_scan(tmp_path)
        assert matches == []
        assert skipped == 0


class TestSensitiveScanIgnoreGit:
    def test_git_dir_skipped(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("[user]\n  password=should-not-trigger\n")
        (tmp_path / "README.md").write_text("# Clean\n", encoding="utf-8")
        matches, _ = sensitive_scan(tmp_path)
        assert matches == []
