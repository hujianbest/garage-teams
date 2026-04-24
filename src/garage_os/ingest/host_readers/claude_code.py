"""Claude Code conversation history reader (F010 ADR-D10-8).

Reads ``~/.claude/conversations/*.json`` (NDJSON-style per Anthropic CLI doc).

Failure modes (handled per FR-1005 negative path acceptance):
- Missing directory → list_conversations returns []
- Single corrupted JSON file → skipped + stderr warn during list_conversations
- Single not-found conversation_id → read_conversation raises FileNotFoundError
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import IO

from garage_os.ingest.types import ConversationContent, ConversationSummary


class ClaudeCodeHistoryReader:
    """HostHistoryReader for Claude Code conversations under ~/.claude/conversations/."""

    host_id: str = "claude-code"

    def __init__(
        self,
        *,
        history_dir: Path | None = None,
        stderr: IO[str] | None = None,
        max_entries: int = 30,
    ) -> None:
        self._history_dir = history_dir or (Path.home() / ".claude" / "conversations")
        self._stderr = stderr if stderr is not None else sys.stderr
        self._max_entries = max_entries

    def list_conversations(self) -> list[ConversationSummary]:
        if not self._history_dir.is_dir():
            return []

        all_files = sorted(self._history_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        summaries: list[ConversationSummary] = []
        for fpath in all_files[: self._max_entries]:
            try:
                raw = json.loads(fpath.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(
                    f"Skipped unreadable conversation: {fpath.name} ({exc})",
                    file=self._stderr,
                )
                continue
            conv_id = fpath.stem  # file name without .json extension
            topic = self._extract_topic(raw)
            messages = raw.get("messages", []) if isinstance(raw, dict) else []
            mtime = datetime.fromtimestamp(fpath.stat().st_mtime)
            summaries.append(
                ConversationSummary(
                    conversation_id=conv_id,
                    topic=topic,
                    mtime=mtime,
                    message_count=len(messages),
                )
            )
        return summaries

    def read_conversation(self, conversation_id: str) -> ConversationContent:
        fpath = self._history_dir / f"{conversation_id}.json"
        if not fpath.is_file():
            raise FileNotFoundError(
                f"Claude Code conversation not found: {fpath}"
            )
        raw = json.loads(fpath.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(
                f"Invalid Claude Code conversation schema: expected JSON object, got {type(raw).__name__}"
            )
        messages = raw.get("messages", [])
        return ConversationContent(
            conversation_id=conversation_id,
            messages=list(messages) if isinstance(messages, list) else [],
            raw=raw,
        )

    @staticmethod
    def _extract_topic(raw: object) -> str:
        """Extract a one-line topic. Try 'topic' / 'title' / first user message."""
        if isinstance(raw, dict):
            for key in ("topic", "title", "summary"):
                v = raw.get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()[:200]
            messages = raw.get("messages", [])
            if isinstance(messages, list):
                for msg in messages:
                    if isinstance(msg, dict) and msg.get("role") in ("user", "human"):
                        content = msg.get("content") or ""
                        if isinstance(content, str) and content.strip():
                            return content.strip()[:200]
        return "(untitled conversation)"
