"""Cursor conversation history reader — DEFERRED stub (F010 ADR-D10-10 + CON-1007).

Cursor's conversation history file path is not stably documented at F010 time
(HYP-1005 Low confidence). Per ADR-D10-10 + CON-1007, this reader is a stub:
both methods raise ``NotImplementedError`` with deferred message + upstream link.

When Cursor history schema stabilizes, replace this stub with a real reader
(D-1010 candidate).
"""

from __future__ import annotations

from garage_os.ingest.types import ConversationContent, ConversationSummary

DEFERRED_MESSAGE = (
    "Cursor history reader is deferred to F010 D-1010 per CON-1007. "
    "Cursor conversation history path was not stabilized at F010 design time. "
    "Track upstream: https://cursor.sh/docs/cli"
)


class CursorHistoryReader:
    """Stub HostHistoryReader for Cursor (D-1010 deferred)."""

    host_id: str = "cursor"

    def __init__(self, *args: object, **kwargs: object) -> None:
        # Accept any constructor args for parity with concrete readers; ignore.
        pass

    def list_conversations(self) -> list[ConversationSummary]:
        raise NotImplementedError(DEFERRED_MESSAGE)

    def read_conversation(self, conversation_id: str) -> ConversationContent:
        raise NotImplementedError(DEFERRED_MESSAGE)
