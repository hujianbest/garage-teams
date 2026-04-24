"""Cursor install adapter.

Implements F007 ADR-D7-3 row 3:

    skill path: .cursor/skills/<skill_id>/SKILL.md
    agent path: None (Cursor has no native agent surface)

F009 ADR-D9-6 + § 2.3 (调研锚点 Cursor 官方文档):

    user-scope skill path: ~/.cursor/skills/<skill_id>/SKILL.md (absolute)
    user-scope agent path: None (与 project scope 一致, cursor 无 agent surface)

ADR-D7-3 chose ``.cursor/skills/`` over ``.cursor/rules/*.mdc`` because:

- SKILL.md format is identical to Anthropic's, so source files can be
  installed without transformation.
- ``.cursor/rules/*.mdc`` are always-loaded context; bundling 30+ HF skills
  there would saturate context.
- OpenSpec already validates ``.cursor/skills/openspec-*/SKILL.md`` works
  (``docs/supported-tools.md`` ``cursorAdapter`` row).

Older Cursor versions may not recognize ``.cursor/skills/``; this is
documented in the user guide R2 risk section.
"""

from __future__ import annotations

from pathlib import Path


class CursorInstallAdapter:
    """HostInstallAdapter for Cursor.

    F009 (ADR-D9-6) adds optional ``_user`` suffix methods returning absolute
    paths under ``Path.home()``. F007 既有 method 签名严格不变（CON-901）。
    Cursor 在 user scope 下也无 agent surface（与 project scope 一致）。
    """

    host_id: str = "cursor"

    def target_skill_path(self, skill_id: str) -> Path:
        return Path(".cursor/skills") / skill_id / "SKILL.md"

    def target_agent_path(self, agent_id: str) -> Path | None:
        return None

    def target_skill_path_user(self, skill_id: str) -> Path:
        """F009 user-scope skill path (absolute, under ~/.cursor/skills/)."""
        return Path.home() / ".cursor" / "skills" / skill_id / "SKILL.md"

    def target_agent_path_user(self, agent_id: str) -> Path | None:
        """F009 user-scope agent path: None (cursor 无 agent surface, 与 project scope 一致)."""
        return None

    def target_context_path(self, name: str) -> Path:
        """F010 (FR-1004 + ADR-D10-2) project-scope context surface path.

        Cursor auto-loads ``.cursor/rules/<name>.mdc`` files with ``alwaysApply: true``
        front matter. Default ``name="garage-context"`` 时, 装到 ``.cursor/rules/garage-context.mdc``.
        """
        return Path(".cursor/rules") / f"{name}.mdc"

    def target_context_path_user(self, name: str) -> Path:
        """F010 user-scope context surface path (absolute, ~/.cursor/rules/<name>.mdc)."""
        return Path.home() / ".cursor" / "rules" / f"{name}.mdc"

    def render(self, content: str) -> str:
        return content
