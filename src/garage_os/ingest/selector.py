"""F010 interactive conversation selector (FR-1006 + ADR-D10-9 r2).

Implements TTY interactive prompt for `garage session import` (no `--all`).
non-TTY退化: 返回 [] + stderr notice (与 F009 prompt_hosts 同精神).
"""

from __future__ import annotations

import sys
from typing import IO

from garage_os.ingest.types import ConversationSummary

NON_INTERACTIVE_NOTICE = (
    "non-interactive shell detected; use --all to batch import"
)
PROMPT_TEMPLATE = (
    "Select conversations to import (e.g. '1,3,5' or 'all' or 'q' to quit): "
)


def prompt_select(
    summaries: list[ConversationSummary],
    *,
    stdin: IO[str] | None = None,
    stderr: IO[str] | None = None,
    stdout: IO[str] | None = None,
) -> list[str]:
    """Interactive selection of conversation_ids from summaries.

    Returns:
        list of selected conversation_ids (empty when user cancels / EOF / non-TTY)
    """
    src = stdin if stdin is not None else sys.stdin
    err = stderr if stderr is not None else sys.stderr
    out = stdout if stdout is not None else sys.stdout

    if not _is_tty(src):
        print(NON_INTERACTIVE_NOTICE, file=err)
        return []

    if not summaries:
        print("No conversations available.", file=err)
        return []

    # Print numbered list
    print("Available conversations (most recent first):", file=out)
    for i, s in enumerate(summaries, 1):
        topic_short = s.topic[:60] + "…" if len(s.topic) > 60 else s.topic
        print(
            f"  {i:2d}. [{s.mtime.strftime('%Y-%m-%d')}] "
            f"{topic_short} ({s.message_count} msgs, {s.conversation_id[:8]})",
            file=out,
        )

    try:
        answer = input(PROMPT_TEMPLATE)
    except EOFError:
        print(NON_INTERACTIVE_NOTICE, file=err)
        return []

    answer_stripped = answer.strip().lower()
    if answer_stripped in ("q", "quit", ""):
        return []
    if answer_stripped == "all":
        return [s.conversation_id for s in summaries]

    # Parse comma-separated indices
    selected: list[str] = []
    for token in answer_stripped.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            idx = int(token)
        except ValueError:
            print(f"Invalid selection: '{token}', skipping", file=err)
            continue
        if 1 <= idx <= len(summaries):
            selected.append(summaries[idx - 1].conversation_id)
        else:
            print(f"Selection out of range: {idx}", file=err)
    return selected


def _is_tty(stream: IO[str]) -> bool:
    isatty = getattr(stream, "isatty", None)
    if isatty is None:
        return False
    try:
        return bool(isatty())
    except (OSError, ValueError):
        return False
