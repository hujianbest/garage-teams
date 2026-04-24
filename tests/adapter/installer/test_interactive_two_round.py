"""F009 T4: 交互式两轮 scope 选择 (candidate C 三个开关) 测试.

Covers:
- spec FR-903 (交互式两轮)
- design ADR-D9-5 (candidate C: 第二轮 a/u/p 三个开关)
- spec FR-903 验收 #4 (non-TTY 沿用 F007 退化, 不附加 F009-specific 文字)

Fixture pattern (与 F007 既有 test_interactive.py 一致):
- 用 monkeypatch.setattr('builtins.input', ...) 把 input() 接到 fake_in StringIO
- stdin 参数传 fake_in 仅用于控制 isatty()
"""

from __future__ import annotations

import io
from typing import IO

import pytest

from garage_os.adapter.installer.interactive import prompt_scopes_per_host


def _fake_stdin(text: str, *, isatty: bool = True) -> IO[str]:
    """TTY-like StringIO with isatty() control."""
    stream = io.StringIO(text)
    stream.isatty = lambda: isatty  # type: ignore[method-assign]
    return stream


class TestPromptScopesPerHostBatchSwitch:
    """ADR-D9-5 candidate C: 第一轮 a/u/p 批量开关."""

    def test_default_a_returns_all_project_F008_compat(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """空白回车 (default 'a') = all project = F007/F008 行为 (CON-901)."""
        fake_in = _fake_stdin("\n")
        monkeypatch.setattr(
            "builtins.input", lambda prompt="": fake_in.readline().rstrip("\n")
        )
        result = prompt_scopes_per_host(
            ["claude", "cursor"], stdin=fake_in, stderr=io.StringIO()
        )
        assert result == {"claude": "project", "cursor": "project"}

    def test_explicit_a_returns_all_project(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_in = _fake_stdin("a\n")
        monkeypatch.setattr(
            "builtins.input", lambda prompt="": fake_in.readline().rstrip("\n")
        )
        result = prompt_scopes_per_host(
            ["claude", "cursor"], stdin=fake_in, stderr=io.StringIO()
        )
        assert result == {"claude": "project", "cursor": "project"}

    def test_u_returns_all_user(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """'u' 一键全 user."""
        fake_in = _fake_stdin("u\n")
        monkeypatch.setattr(
            "builtins.input", lambda prompt="": fake_in.readline().rstrip("\n")
        )
        result = prompt_scopes_per_host(
            ["claude", "cursor", "opencode"],
            stdin=fake_in,
            stderr=io.StringIO(),
        )
        assert result == {
            "claude": "user",
            "cursor": "user",
            "opencode": "user",
        }


class TestPromptScopesPerHostPerHostSwitch:
    """ADR-D9-5 candidate C: 第一轮选 'p', 第二段逐个 P/u 询问."""

    def test_p_then_per_host_mixed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """p → 然后逐个 host 询问 P/u."""
        # 输入: 'p' (进入 per-host) + 'u' (claude → user) + '' (cursor → P/project default)
        fake_in = _fake_stdin("p\nu\n\n")
        monkeypatch.setattr(
            "builtins.input", lambda prompt="": fake_in.readline().rstrip("\n")
        )
        result = prompt_scopes_per_host(
            ["claude", "cursor"], stdin=fake_in, stderr=io.StringIO()
        )
        assert result == {"claude": "user", "cursor": "project"}

    def test_p_then_all_default_project(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """p → 全部回车 → 全 project (default P 等价 F007/F008 行为)."""
        # 输入: 'p' + '' (claude default P) + '' (cursor default P)
        fake_in = _fake_stdin("p\n\n\n")
        monkeypatch.setattr(
            "builtins.input", lambda prompt="": fake_in.readline().rstrip("\n")
        )
        result = prompt_scopes_per_host(
            ["claude", "cursor"], stdin=fake_in, stderr=io.StringIO()
        )
        assert result == {"claude": "project", "cursor": "project"}

    def test_p_uppercase_u_recognized_as_user(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """'p' 第二段: 'U' (uppercase) → lower() == 'u' → user."""
        fake_in = _fake_stdin("p\nU\n")
        monkeypatch.setattr(
            "builtins.input", lambda prompt="": fake_in.readline().rstrip("\n")
        )
        result = prompt_scopes_per_host(
            ["claude"], stdin=fake_in, stderr=io.StringIO()
        )
        assert result == {"claude": "user"}


class TestPromptScopesPerHostNonTTY:
    """FR-903 验收 #4: non-TTY 退化, 不进入第二轮提示, 不附加 F009 文字."""

    def test_non_tty_returns_all_project(self) -> None:
        stdin = _fake_stdin("", isatty=False)
        stderr = io.StringIO()
        result = prompt_scopes_per_host(
            ["claude", "cursor"], stdin=stdin, stderr=stderr
        )
        # non-TTY: 不进入交互, 全部默认 project (与 F007/F008 一致)
        assert result == {"claude": "project", "cursor": "project"}
        # FR-903 验收 #4: 不附加 F009-specific scope-related 提示文字
        assert "scope" not in stderr.getvalue().lower()


class TestPromptScopesPerHostEmpty:
    """边界: host_ids 为空时."""

    def test_empty_host_ids_returns_empty_dict(self) -> None:
        stdin = _fake_stdin("u\n")
        result = prompt_scopes_per_host([], stdin=stdin, stderr=io.StringIO())
        assert result == {}


class TestPromptScopesPerHostEOF:
    """边界: stream EOF 时."""

    def test_eof_first_round_defaults_all_project(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """第一轮 EOF (空 stream) → 全 project (default 'a' 兼容)."""
        fake_in = _fake_stdin("", isatty=True)
        monkeypatch.setattr(
            "builtins.input",
            lambda prompt="": (_ for _ in ()).throw(EOFError),
        )
        result = prompt_scopes_per_host(
            ["claude"], stdin=fake_in, stderr=io.StringIO()
        )
        assert result == {"claude": "project"}

    def test_eof_per_host_round_defaults_remaining_project(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """选 p 后第二段 EOF → 余下 host 全 project."""
        # claude 输入 'u' → user; cursor EOF → project (default)
        responses = iter(["p", "u"])  # third call → EOFError

        def _input_or_eof(prompt: str = "") -> str:
            try:
                return next(responses)
            except StopIteration:
                raise EOFError() from None

        fake_in = _fake_stdin("", isatty=True)
        monkeypatch.setattr("builtins.input", _input_or_eof)
        result = prompt_scopes_per_host(
            ["claude", "cursor"], stdin=fake_in, stderr=io.StringIO()
        )
        assert result == {"claude": "user", "cursor": "project"}
