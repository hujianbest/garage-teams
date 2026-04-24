"""OpenCode install adapter.

Implements F007 ADR-D7-3 row 2:

    skill path: .opencode/skills/<skill_id>/SKILL.md
    agent path: .opencode/agent/<agent_id>.md

F009 ADR-D9-6 + § 2.3 (调研锚点 OpenCode PR #6174):

    user-scope skill path: ~/.config/opencode/skills/<skill_id>/SKILL.md (XDG default)
    user-scope agent path: ~/.config/opencode/agent/<agent_id>.md

Note: OpenCode historically pluralizes ``skills/`` but uses singular
``agent/`` for its agent surface. F009 选择 XDG 默认路径
(`~/.config/opencode/`) 作为 user scope；dotfiles 风格 `~/.opencode/skills/`
留给 deferred backlog (spec § 5)。Source: OpenSpec
``docs/supported-tools.md`` ``opencodeAdapter`` row + OpenCode PR #6174
确认 XDG 与 dotfiles 风格皆支持。
"""

from __future__ import annotations

from pathlib import Path


class OpenCodeInstallAdapter:
    """HostInstallAdapter for OpenCode.

    F009 (ADR-D9-6) adds optional ``_user`` suffix methods returning absolute
    paths under ``Path.home()``. F007 既有 method 签名严格不变（CON-901）。
    """

    host_id: str = "opencode"

    def target_skill_path(self, skill_id: str) -> Path:
        return Path(".opencode/skills") / skill_id / "SKILL.md"

    def target_agent_path(self, agent_id: str) -> Path | None:
        return Path(".opencode/agent") / f"{agent_id}.md"

    def target_skill_path_user(self, skill_id: str) -> Path:
        """F009 user-scope skill path (XDG default ~/.config/opencode/skills/)."""
        return Path.home() / ".config" / "opencode" / "skills" / skill_id / "SKILL.md"

    def target_agent_path_user(self, agent_id: str) -> Path | None:
        """F009 user-scope agent path (XDG default ~/.config/opencode/agent/)."""
        return Path.home() / ".config" / "opencode" / "agent" / f"{agent_id}.md"

    def target_context_path(self, name: str) -> Path:
        """F010 (FR-1004 + ADR-D10-2) project-scope context surface path.

        OpenCode auto-loads ``.opencode/AGENTS.md``. The ``name`` parameter is
        currently unused for opencode (filename is fixed by the host convention).
        """
        return Path(".opencode/AGENTS.md")

    def target_context_path_user(self, name: str) -> Path:
        """F010 user-scope context surface path (XDG default ~/.config/opencode/AGENTS.md)."""
        return Path.home() / ".config" / "opencode" / "AGENTS.md"

    def render(self, content: str) -> str:
        return content
