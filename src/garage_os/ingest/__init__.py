"""F010 ingest package: garage session import (pull) — host conversation history → SessionState.

Implements F010 spec FR-1005/1006 + design ADR-D10-7/8/9/10/11.

Public API:
- ``HostHistoryReader`` Protocol + per-host implementations
- ``HOST_READERS`` registry + ``HOST_ID_ALIASES``
- ``import_conversations(...)``: ingest pipeline (creates Garage SessionMetadata,
  triggers F003 archive_session + extract_for_archived_session_id)
- ``prompt_select(...)``: TTY interactive selector
"""

from garage_os.ingest.host_readers import (
    HOST_ID_ALIASES,
    HOST_READERS,
    resolve_host_id,
)
from garage_os.ingest.pipeline import ImportSummary, import_conversations
from garage_os.ingest.selector import prompt_select
from garage_os.ingest.types import (
    ConversationContent,
    ConversationSummary,
    HostHistoryReader,
)

__all__ = [
    "ConversationContent",
    "ConversationSummary",
    "HostHistoryReader",
    "HOST_ID_ALIASES",
    "HOST_READERS",
    "ImportSummary",
    "import_conversations",
    "prompt_select",
    "resolve_host_id",
]
