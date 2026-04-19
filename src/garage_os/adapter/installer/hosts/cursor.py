"""Cursor install adapter.

Implements F007 ADR-D7-3 row 3:

    skill path: .cursor/skills/<skill_id>/SKILL.md
    agent path: None (Cursor has no native agent surface)

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
    host_id: str = "cursor"

    def target_skill_path(self, skill_id: str) -> Path:
        return Path(".cursor/skills") / skill_id / "SKILL.md"

    def target_agent_path(self, agent_id: str) -> Path | None:
        return None

    def render(self, content: str) -> str:
        return content
