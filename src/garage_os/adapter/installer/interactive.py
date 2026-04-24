"""Interactive host selection prompt for ``garage init`` (no extra deps).

Implements F007 FR-703 + design D7 ADR-D7-5.
F009 (FR-903 + ADR-D9-5 candidate C) adds:

- ``prompt_scopes_per_host``: 第二轮 scope 选择 (a/u/p 三个开关)
  - ``a`` (default): all project (与 F007/F008 行为完全一致, CON-901 兼容)
  - ``u``: all user
  - ``p``: per-host (逐个询问每个 host 的 P/u)
- non-TTY 沿用 F007 退化 (FR-903 验收 #4): **不附加** F009-specific scope 提示文字

Behavior (F007 既有 prompt_hosts, 不变):

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

# F009 ADR-D9-5 candidate C: 第二轮 scope 选择
# 第一段: a/u/p 三个开关 (default a = F007/F008 兼容)
SCOPE_BATCH_PROMPT = (
    "Install selected hosts to:\n"
    "  [a] all project (./.{{host}}/skills/) — F007/F008 default\n"
    "  [u] all user    (~/.{{host}}/skills/)\n"
    "  [p] per-host    — pick scope individually\n"
    "Choice [a/u/p]: "
)
# 第二段 (仅在用户选 'p' 时): 逐个 host 问 P/u
SCOPE_PER_HOST_PROMPT = (
    "Install {host} skills to: [P]roject (./.{{host}}/skills/) "
    "or [u]ser (~/.{{host}}/skills/)? [P/u]: "
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


def prompt_scopes_per_host(
    host_ids: list[str],
    *,
    stdin: IO[str] | None = None,
    stderr: IO[str] | None = None,
) -> dict[str, str]:
    """F009 FR-903 + ADR-D9-5 candidate C: 第二轮 scope 选择.

    在 ``prompt_hosts`` 已选定 host_ids 后, 询问每个 host 的 scope.
    用户体验:

    - 默认 ``a`` (一键回车) = all project = F007/F008 行为完全等价 (CON-901)
    - ``u`` = all user
    - ``p`` = per-host (进入逐个 P/u 询问, 每个默认 P/project)

    non-TTY 场景: 与 F007 ``prompt_hosts`` 退化语义一致, **不**进入第二轮提示;
    上层调用方 (cli._resolve_init_hosts) 已在 prompt_hosts 阶段返回 [] 退化.

    Args:
        host_ids: prompt_hosts 返回的已选定 host id 列表 (sorted).
        stdin / stderr: Streams; default to ``sys.stdin`` / ``sys.stderr``.

    Returns:
        dict[host_id, scope]: 每个 host 对应的 scope ('project' or 'user').
        host_ids 为空时返回空 dict.
    """
    src = stdin if stdin is not None else sys.stdin
    # F009 (FR-903 验收 #4): non-TTY 退化时不向 stderr 打印 F009-specific scope 文字,
    # 完全沿用 F007 prompt_hosts 退化语义; stderr 参数保留是为 future-proof
    # (e.g. 后续 F010 加 user-facing 提示) + 与 prompt_hosts 签名对称.
    _ = stderr  # keep in signature for symmetry with prompt_hosts (F007)

    if not host_ids:
        return {}

    if not _is_tty(src):
        # non-TTY: 不进入第二轮 scope 提示, 全部 host 默认 project
        # (FR-903 验收 #4: non-TTY 沿用 F007 退化语义, 不附加 F009-specific 文字)
        return {h: "project" for h in host_ids}

    # 第一轮: a/u/p 批量开关
    try:
        first_answer = input(SCOPE_BATCH_PROMPT)
    except EOFError:
        return {h: "project" for h in host_ids}
    first_stripped = first_answer.strip().lower()

    if first_stripped == "u":
        return {h: "user" for h in host_ids}
    if first_stripped == "p":
        # 第二段: 逐个询问每个 host
        result: dict[str, str] = {}
        for host in host_ids:
            try:
                ans = input(SCOPE_PER_HOST_PROMPT.format(host=host))
            except EOFError:
                # Stream exhausted: 余下 host 全部 default project
                for remaining in host_ids[host_ids.index(host):]:
                    if remaining not in result:
                        result[remaining] = "project"
                return result
            ans_stripped = ans.strip().lower()
            if ans_stripped == "u":
                result[host] = "user"
            else:
                # 默认 / 'P' / 'p' / 任何其它输入 → project
                result[host] = "project"
        return result

    # 默认 'a' (含空白回车 / 任何其它输入) = all project = F007/F008 行为
    return {h: "project" for h in host_ids}


def _is_tty(stream: IO[str]) -> bool:
    """True if the stream looks like an interactive TTY."""
    isatty = getattr(stream, "isatty", None)
    if isatty is None:
        return False
    try:
        return bool(isatty())
    except (OSError, ValueError):
        return False
