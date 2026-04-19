"""Tests for garage_os.adapter.installer.marker (F007 T3 / FR-708 / D7 §10.4).

Marker injection contract:

- ``source_kind="skill"`` requires existing front matter; missing → MalformedFrontmatterError
- ``source_kind="agent"`` tolerates missing front matter; insert minimal one
- Existing ``installed_by`` / ``installed_pack`` fields not duplicated (idempotent re-injection)
- ``extract_marker`` returns dict if present, None otherwise
"""

from __future__ import annotations

import pytest

from garage_os.adapter.installer.marker import (
    MalformedFrontmatterError,
    extract_marker,
    inject,
)


SKILL_SOURCE_OK = """---
name: garage-hello
description: A test skill
---

# Garage Hello

Body line 1.
Body line 2.
"""

SKILL_SOURCE_NO_FRONTMATTER = """# Garage Hello

No front matter, just body.
"""

AGENT_SOURCE_NO_FRONTMATTER = """# Sample Agent

Plain markdown body, no front matter.
"""

AGENT_SOURCE_WITH_FRONTMATTER = """---
agent_role: helper
---

# Sample Agent

Body.
"""


class TestInjectSkill:
    def test_skill_with_frontmatter_injects_marker(self) -> None:
        out = inject(SKILL_SOURCE_OK, "garage", "skill")
        # Front matter remains a single block, with the two new fields appended.
        assert out.startswith("---\n")
        assert "name: garage-hello" in out
        assert "description: A test skill" in out
        assert "installed_by: garage" in out
        assert "installed_pack: garage" in out
        # Body preserved.
        assert "# Garage Hello" in out
        assert "Body line 1." in out

    def test_skill_without_frontmatter_raises(self) -> None:
        with pytest.raises(MalformedFrontmatterError) as exc_info:
            inject(SKILL_SOURCE_NO_FRONTMATTER, "garage", "skill")
        assert "skill" in str(exc_info.value).lower() or "front matter" in str(
            exc_info.value
        ).lower()

    def test_skill_idempotent_reinjection(self) -> None:
        # T3 测试种子关键边界 5: re-injecting an already-marked source is a no-op.
        first = inject(SKILL_SOURCE_OK, "garage", "skill")
        second = inject(first, "garage", "skill")
        assert second == first


class TestInjectAgent:
    def test_agent_with_frontmatter_injects_marker(self) -> None:
        out = inject(AGENT_SOURCE_WITH_FRONTMATTER, "garage", "agent")
        assert "agent_role: helper" in out
        assert "installed_by: garage" in out
        assert "installed_pack: garage" in out

    def test_agent_without_frontmatter_inserts_minimal(self) -> None:
        # D7 §10.4: agent.md without front matter is a legal path.
        out = inject(AGENT_SOURCE_NO_FRONTMATTER, "garage", "agent")
        assert out.startswith("---\n")
        assert "installed_by: garage" in out
        assert "installed_pack: garage" in out
        # Original body fully preserved after the inserted front matter.
        assert "# Sample Agent" in out
        assert "Plain markdown body, no front matter." in out

    def test_agent_idempotent_reinjection(self) -> None:
        first = inject(AGENT_SOURCE_NO_FRONTMATTER, "garage", "agent")
        second = inject(first, "garage", "agent")
        assert second == first


class TestExtractMarker:
    def test_returns_dict_when_marker_present(self) -> None:
        injected = inject(SKILL_SOURCE_OK, "garage", "skill")
        marker = extract_marker(injected)
        assert marker == {"installed_by": "garage", "installed_pack": "garage"}

    def test_returns_none_when_no_frontmatter(self) -> None:
        assert extract_marker(SKILL_SOURCE_NO_FRONTMATTER) is None

    def test_returns_none_when_frontmatter_lacks_marker(self) -> None:
        # Front matter exists but no installed_by/installed_pack fields.
        assert extract_marker(SKILL_SOURCE_OK) is None
