"""F010 ingest host_readers registry + alias resolution.

Implements ADR-D10-11 (HOST_READERS registry independent from HOST_REGISTRY +
HOST_ID_ALIASES bridge for user-friendly aliases).

Note: install host_id ('claude' / 'opencode' / 'cursor') and ingest host_id
('claude-code' / 'opencode' / 'cursor') are deliberately distinct because they
target different surfaces (skill vs conversation history). HOST_ID_ALIASES
lets users write either form via ``garage session import --from <id>``.
"""

from __future__ import annotations

from garage_os.ingest.host_readers.claude_code import ClaudeCodeHistoryReader
from garage_os.ingest.host_readers.cursor import CursorHistoryReader
from garage_os.ingest.host_readers.opencode import OpenCodeHistoryReader
from garage_os.ingest.types import HostHistoryReader

# Canonical ingest host_id → reader class
HOST_READERS: dict[str, type[HostHistoryReader]] = {
    "claude-code": ClaudeCodeHistoryReader,
    "opencode": OpenCodeHistoryReader,
    "cursor": CursorHistoryReader,
}

# F010 ADR-D10-11: alias map (CLI input → canonical ingest host_id)
HOST_ID_ALIASES: dict[str, str] = {
    "claude": "claude-code",       # F007/F009 install host_id ↔ F010 ingest
    "claude-code": "claude-code",
    "cursor": "cursor",
    "opencode": "opencode",
}


def resolve_host_id(user_input: str) -> str:
    """Resolve a user-provided host id (CLI --from value) to canonical ingest host_id.

    Raises:
        ValueError: when ``user_input`` is not in HOST_ID_ALIASES.
    """
    canonical = HOST_ID_ALIASES.get(user_input.strip().lower())
    if canonical is None:
        supported = ", ".join(sorted(HOST_ID_ALIASES))
        raise ValueError(
            f"Unknown host: '{user_input}'. Supported: {supported} "
            "(cursor is deferred to F010 D-1010 per CON-1007)"
        )
    return canonical


__all__ = [
    "HOST_ID_ALIASES",
    "HOST_READERS",
    "resolve_host_id",
]
