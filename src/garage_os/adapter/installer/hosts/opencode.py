"""OpenCode install adapter.

Implements F007 ADR-D7-3 row 2:

    skill path: .opencode/skills/<skill_id>/SKILL.md
    agent path: .opencode/agent/<agent_id>.md

Note: OpenCode historically pluralizes ``skills/`` but uses singular
``agent/`` for its agent surface. Source: OpenSpec ``docs/supported-tools.md``
``opencodeAdapter`` row.
"""

from __future__ import annotations

from pathlib import Path


class OpenCodeInstallAdapter:
    host_id: str = "opencode"

    def target_skill_path(self, skill_id: str) -> Path:
        return Path(".opencode/skills") / skill_id / "SKILL.md"

    def target_agent_path(self, agent_id: str) -> Path | None:
        return Path(".opencode/agent") / f"{agent_id}.md"

    def render(self, content: str) -> str:
        return content
