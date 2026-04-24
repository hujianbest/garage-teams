"""Claude Code install adapter.

Implements F007 ADR-D7-3 row 1:

    skill path: .claude/skills/<skill_id>/SKILL.md
    agent path: .claude/agents/<agent_id>.md

F009 ADR-D9-6 + § 2.3 (调研锚点 Anthropic Claude Code 官方文档):

    user-scope skill path: ~/.claude/skills/<skill_id>/SKILL.md (absolute)
    user-scope agent path: ~/.claude/agents/<agent_id>.md (absolute)

Source: OpenSpec ``docs/supported-tools.md`` ``claudeAdapter`` row +
Anthropic Claude Code official skills documentation convention.
"""

from __future__ import annotations

from pathlib import Path


class ClaudeInstallAdapter:
    """HostInstallAdapter for Claude Code.

    Implements the install-time path mapping; runtime invocation is handled
    separately by ``garage_os.adapter.claude_code_adapter.ClaudeCodeAdapter``
    (F001), which is a different concern (see ADR-D7-1).

    F009 (ADR-D9-6) adds optional ``_user`` suffix methods returning absolute
    paths under ``Path.home()``. F007 既有 method 签名严格不变（CON-901）。
    """

    host_id: str = "claude"

    def target_skill_path(self, skill_id: str) -> Path:
        return Path(".claude/skills") / skill_id / "SKILL.md"

    def target_agent_path(self, agent_id: str) -> Path | None:
        return Path(".claude/agents") / f"{agent_id}.md"

    def target_skill_path_user(self, skill_id: str) -> Path:
        """F009 user-scope skill path (absolute, under ~/.claude/skills/)."""
        return Path.home() / ".claude" / "skills" / skill_id / "SKILL.md"

    def target_agent_path_user(self, agent_id: str) -> Path | None:
        """F009 user-scope agent path (absolute, under ~/.claude/agents/)."""
        return Path.home() / ".claude" / "agents" / f"{agent_id}.md"

    def target_context_path(self, name: str) -> Path:
        """F010 (FR-1004 + ADR-D10-2) project-scope context surface path.

        Claude Code auto-loads ``CLAUDE.md`` from the cwd. The ``name`` parameter
        is currently unused for claude (filename is fixed by the host convention);
        retained in the Protocol signature for future multi-context扩展.
        """
        return Path("CLAUDE.md")

    def target_context_path_user(self, name: str) -> Path:
        """F010 user-scope context surface path (absolute, ~/.claude/CLAUDE.md).

        Claude Code 用户级 ``CLAUDE.md`` (auto-loaded for all projects). ``name``
        参数当前 unused (与 project scope 同精神).
        """
        return Path.home() / ".claude" / "CLAUDE.md"

    def render(self, content: str) -> str:
        return content
