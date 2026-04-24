"""F010 ingest types: ConversationSummary + ConversationContent + HostHistoryReader Protocol.

Implements ADR-D10-8 (per-host reader Protocol) + ADR-D10-9 (signal-fill helpers
on ConversationContent).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@dataclass
class ConversationSummary:
    """Summary of a host conversation, returned by HostHistoryReader.list_conversations.

    Sorted by mtime DESC (newest first); ≤ 30 entries per ADR-D10-8.
    """

    conversation_id: str
    topic: str
    mtime: datetime
    message_count: int


@dataclass
class ConversationContent:
    """Full conversation payload, returned by HostHistoryReader.read_conversation.

    Provides three helper methods used by ingest pipeline (ADR-D10-9 r2 signal-fill):
    - ``topic_or_summary()``: one-line topic for SessionMetadata.topic
    - ``first_user_message_excerpt()``: ≤ 100 chars for problem_domain signal (#2 priority 0.72)
    - ``derived_tags()``: ≤ 3 keywords for tags signal (#1 priority 0.62)
    """

    conversation_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def topic_or_summary(self) -> str:
        """Return a one-line topic. Fallback to first user msg or conv_id."""
        if "topic" in self.raw:
            return str(self.raw["topic"])[:200]
        msg = self.first_user_message_excerpt(max_chars=200)
        return msg or f"Conversation {self.conversation_id[:8]}"

    def first_user_message_excerpt(self, max_chars: int = 100) -> str:
        """Return first user message content, truncated to max_chars.

        Used for ``metadata.problem_domain`` strong signal (priority 0.72).
        """
        for msg in self.messages:
            role = msg.get("role") or msg.get("type")
            content = msg.get("content") or msg.get("text") or ""
            if isinstance(content, list):
                # Some hosts use list-of-blocks format
                content = " ".join(
                    block.get("text", "") for block in content if isinstance(block, dict)
                )
            if role in ("user", "human"):
                text = str(content).strip()
                if text:
                    return text[:max_chars]
        return ""

    def derived_tags(self) -> list[str]:
        """Return ≤ 3 derived keyword tags.

        Used for ``metadata.tags`` strong signal (priority 0.62). Heuristic:
        extract noteworthy keywords from topic / messages. Quality not enforced —
        F003 candidate review is the trust boundary (CON-1004).
        """
        topic = self.topic_or_summary().lower()
        # Naive tokenization: split on whitespace, take first 3 alpha tokens > 3 chars
        tokens = [t.strip(".,!?:;") for t in topic.split()]
        keywords = [t for t in tokens if t.isalpha() and len(t) > 3][:3]
        return keywords


@runtime_checkable
class HostHistoryReader(Protocol):
    """Protocol for per-host conversation history readers.

    Each first-class host implements this Protocol with two methods:
    - ``list_conversations()``: return mtime-sorted summaries (newest first, ≤ 30)
    - ``read_conversation(conversation_id)``: load full conversation; raises
      ``FileNotFoundError`` / ``json.JSONDecodeError`` on errors

    F010 ADR-D10-10: cursor reader is a stub (raises ``NotImplementedError``)
    deferred to D-1010.
    """

    host_id: str

    def list_conversations(self) -> list[ConversationSummary]: ...
    def read_conversation(self, conversation_id: str) -> ConversationContent: ...
