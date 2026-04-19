"""Interactive host selection prompt for ``garage init`` (no extra deps).

Implements F007 FR-703 + design D7 ADR-D7-5.

Behavior:

- TTY: ask for each host with ``Install Garage packs into <host>? [y/N]:``
- ``a`` shortcut: install all remaining + previously selected hosts
- ``n`` shortcut: install no further hosts (return current selection)
- empty / ``N`` / unrecognized: skip that host
- non-TTY (``stdin.isatty() == False``): emit a single stderr notice and
  return ``[]`` immediately (matches CI / scripted ``garage init`` behavior)

Stdlib-only by design (NFR-101 forbids new TUI deps).
"""

from __future__ import annotations

import sys
from typing import IO

PROMPT_TEMPLATE = (
    "Install Garage packs into {host}? "
    "[y/N, or 'a' = yes-to-all-remaining, 'q' = stop-here]: "
)
NON_INTERACTIVE_NOTICE = (
    "non-interactive shell detected; install no hosts "
    "(pass --hosts <list> to override)"
)


def prompt_hosts(
    available_hosts: list[str],
    *,
    stdin: IO[str] | None = None,
    stderr: IO[str] | None = None,
) -> list[str]:
    """Ask the user which hosts to install Garage packs into.

    Args:
        available_hosts: Pre-sorted list of host ids from
            ``host_registry.list_host_ids()``.
        stdin / stderr: Streams; default to ``sys.stdin`` / ``sys.stderr``.

    Returns:
        Sorted list of selected host ids (subset of ``available_hosts``).
    """
    src = stdin if stdin is not None else sys.stdin
    err = stderr if stderr is not None else sys.stderr

    if not _is_tty(src):
        print(NON_INTERACTIVE_NOTICE, file=err)
        return []

    selected: set[str] = set()
    remaining = list(available_hosts)
    while remaining:
        host = remaining.pop(0)
        try:
            answer = input(PROMPT_TEMPLATE.format(host=host))
        except EOFError:
            # Stream exhausted; treat the same as non-interactive.
            print(NON_INTERACTIVE_NOTICE, file=err)
            break
        answer_stripped = answer.strip()
        # Shortcuts use exact lowercase letters so 'N' (capital) keeps the
        # plain "no, skip this host" meaning expected from the [y/N] prompt.
        if answer_stripped == "a":
            selected.add(host)
            selected.update(remaining)
            break
        if answer_stripped == "q":
            # Stop asking; keep prior selections, don't add this one.
            break
        if answer_stripped.lower() == "y":
            selected.add(host)
        # Empty / "N" / "n" / unrecognized → skip this host only, continue.
    return sorted(selected)


def _is_tty(stream: IO[str]) -> bool:
    """True if the stream looks like an interactive TTY."""
    isatty = getattr(stream, "isatty", None)
    if isatty is None:
        return False
    try:
        return bool(isatty())
    except (OSError, ValueError):
        return False
