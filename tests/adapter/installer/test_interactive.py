"""Tests for garage_os.adapter.installer.interactive (F007 T4 / FR-703 / ADR-D7-5)."""

from __future__ import annotations

import io
from typing import IO

import pytest

from garage_os.adapter.installer.interactive import (
    NON_INTERACTIVE_NOTICE,
    prompt_hosts,
)


class _FakeTTY(io.StringIO):
    """StringIO that lies about being a TTY for input() simulation."""

    def isatty(self) -> bool:  # type: ignore[override]
        return True


def _fake_stdin(text: str) -> IO[str]:
    s = _FakeTTY(text)
    return s


def _non_tty_stdin(text: str = "") -> IO[str]:
    return io.StringIO(text)


class TestNonInteractive:
    def test_non_tty_returns_empty_with_notice(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # io.StringIO.isatty() → False by default.
        result = prompt_hosts(["claude", "cursor"], stdin=_non_tty_stdin())
        captured = capsys.readouterr()
        assert result == []
        assert NON_INTERACTIVE_NOTICE in captured.err


class TestSelectionShortcuts:
    def test_a_shortcut_selects_remaining_plus_already_chosen(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Answer 'y' for first, 'a' for second → all three selected.
        # input() reads from sys.stdin; we monkeypatch it to a TTY-like StringIO.
        fake_in = _fake_stdin("y\na\n")
        monkeypatch.setattr("builtins.input", lambda prompt="": fake_in.readline().rstrip("\n"))
        result = prompt_hosts(["claude", "cursor", "opencode"], stdin=fake_in)
        assert result == ["claude", "cursor", "opencode"]

    def test_q_shortcut_stops_with_prior_selection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # 'y' then 'q' → only the first one (stop without asking the rest).
        fake_in = _fake_stdin("y\nq\n")
        monkeypatch.setattr("builtins.input", lambda prompt="": fake_in.readline().rstrip("\n"))
        result = prompt_hosts(["claude", "cursor", "opencode"], stdin=fake_in)
        assert result == ["claude"]

    def test_capital_N_means_skip_only_this_host(  # noqa: N802 — test name intentionally uses capital N as the literal user input under test
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Capital 'N' is the prompt's default-no, NOT a shortcut: keep asking.
        fake_in = _fake_stdin("N\nN\ny\n")
        monkeypatch.setattr("builtins.input", lambda prompt="": fake_in.readline().rstrip("\n"))
        result = prompt_hosts(["claude", "cursor", "opencode"], stdin=fake_in)
        assert result == ["opencode"]

    def test_default_no_for_each_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_in = _fake_stdin("\n\n\n")
        monkeypatch.setattr("builtins.input", lambda prompt="": fake_in.readline().rstrip("\n"))
        result = prompt_hosts(["claude", "cursor", "opencode"], stdin=fake_in)
        assert result == []

    def test_explicit_y_skip_y_picks_two(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 'y' / '' / 'y' → claude + opencode (cursor skipped via empty/default-N)
        fake_in = _fake_stdin("y\n\ny\n")
        monkeypatch.setattr("builtins.input", lambda prompt="": fake_in.readline().rstrip("\n"))
        result = prompt_hosts(["claude", "cursor", "opencode"], stdin=fake_in)
        assert result == ["claude", "opencode"]
