"""F010 T5: Cursor history reader DEFERRED stub tests.

Covers ADR-D10-10 + INV-F10-9 + CON-1007.
"""

from __future__ import annotations

import pytest

from garage_os.ingest.host_readers import HOST_READERS
from garage_os.ingest.host_readers.cursor import (
    DEFERRED_MESSAGE,
    CursorHistoryReader,
)


class TestCursorDeferred:
    def test_list_raises_not_implemented(self) -> None:
        reader = CursorHistoryReader()
        with pytest.raises(NotImplementedError) as exc_info:
            reader.list_conversations()
        assert "deferred" in str(exc_info.value).lower()
        assert "D-1010" in str(exc_info.value)

    def test_read_raises_not_implemented(self) -> None:
        reader = CursorHistoryReader()
        with pytest.raises(NotImplementedError):
            reader.read_conversation("any-id")

    def test_in_registry(self) -> None:
        """ADR-D10-10: cursor stays in registry (HOST_READERS three齐) but errors at use time."""
        assert "cursor" in HOST_READERS
        assert HOST_READERS["cursor"] is CursorHistoryReader

    def test_deferred_message_links_upstream(self) -> None:
        assert "cursor.sh" in DEFERRED_MESSAGE
