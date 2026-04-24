"""F010 T5: prompt_select tests."""

from __future__ import annotations

import io
from datetime import datetime
from typing import IO

import pytest

from garage_os.ingest.selector import (
    NON_INTERACTIVE_NOTICE,
    prompt_select,
)
from garage_os.ingest.types import ConversationSummary


def _fake_stdin(text: str, *, isatty: bool = True) -> IO[str]:
    s = io.StringIO(text)
    s.isatty = lambda: isatty  # type: ignore[method-assign]
    return s


def _summaries() -> list[ConversationSummary]:
    return [
        ConversationSummary(
            conversation_id="conv-001",
            topic="Topic A",
            mtime=datetime(2026, 4, 24, 10),
            message_count=3,
        ),
        ConversationSummary(
            conversation_id="conv-002",
            topic="Topic B",
            mtime=datetime(2026, 4, 23, 9),
            message_count=5,
        ),
    ]


class TestSelectorTTY:
    def test_select_indices(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _fake_stdin("1,2\n")
        monkeypatch.setattr("builtins.input", lambda prompt="": fake.readline().rstrip("\n"))
        result = prompt_select(
            _summaries(), stdin=fake, stderr=io.StringIO(), stdout=io.StringIO()
        )
        assert result == ["conv-001", "conv-002"]

    def test_select_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _fake_stdin("all\n")
        monkeypatch.setattr("builtins.input", lambda prompt="": fake.readline().rstrip("\n"))
        result = prompt_select(_summaries(), stdin=fake, stderr=io.StringIO(), stdout=io.StringIO())
        assert result == ["conv-001", "conv-002"]

    def test_quit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _fake_stdin("q\n")
        monkeypatch.setattr("builtins.input", lambda prompt="": fake.readline().rstrip("\n"))
        result = prompt_select(_summaries(), stdin=fake, stderr=io.StringIO(), stdout=io.StringIO())
        assert result == []

    def test_eof_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _eof(prompt: str = "") -> str:
            raise EOFError()
        monkeypatch.setattr("builtins.input", _eof)
        result = prompt_select(_summaries(), stdin=_fake_stdin(""), stderr=io.StringIO(), stdout=io.StringIO())
        assert result == []

    def test_invalid_index_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _fake_stdin("99,abc,1\n")
        monkeypatch.setattr("builtins.input", lambda prompt="": fake.readline().rstrip("\n"))
        stderr = io.StringIO()
        result = prompt_select(_summaries(), stdin=fake, stderr=stderr, stdout=io.StringIO())
        assert result == ["conv-001"]
        assert "out of range" in stderr.getvalue() or "Invalid selection" in stderr.getvalue()


class TestSelectorNonTTY:
    def test_returns_empty_with_notice(self) -> None:
        stderr = io.StringIO()
        result = prompt_select(
            _summaries(),
            stdin=_fake_stdin("", isatty=False),
            stderr=stderr,
            stdout=io.StringIO(),
        )
        assert result == []
        assert NON_INTERACTIVE_NOTICE in stderr.getvalue()


class TestSelectorEmpty:
    def test_no_summaries_returns_empty(self) -> None:
        stderr = io.StringIO()
        result = prompt_select([], stdin=_fake_stdin("", isatty=True), stderr=stderr, stdout=io.StringIO())
        assert result == []
        assert "No conversations available" in stderr.getvalue()
