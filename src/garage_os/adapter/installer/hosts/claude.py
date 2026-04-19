"""Claude Code install adapter.

Implements F007 ADR-D7-3 row 1:

    skill path: .claude/skills/<skill_id>/SKILL.md
    agent path: .claude/agents/<agent_id>.md

Source: OpenSpec ``docs/supported-tools.md`` ``claudeAdapter`` row +
Anthropic Claude Code official skills documentation convention.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class ClaudeInstallAdapter:
    """HostInstallAdapter for Claude Code.

    Implements the install-time path mapping; runtime invocation is handled
    separately by ``garage_os.adapter.claude_code_adapter.ClaudeCodeAdapter``
    (F001), which is a different concern (see ADR-D7-1).
    """

    host_id: str = "claude"

    def target_skill_path(self, skill_id: str) -> Path:
        return Path(".claude/skills") / skill_id / "SKILL.md"

    def target_agent_path(self, agent_id: str) -> Optional[Path]:
        return Path(".claude/agents") / f"{agent_id}.md"

    def render(self, content: str) -> str:
        return content
