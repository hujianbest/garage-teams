"""Unit tests for the three first-class HostInstallAdapter implementations.

F007 T2 — covers ADR-D7-3 path-pattern decisions:

| host    | skill path                            | agent path                          |
|---------|---------------------------------------|-------------------------------------|
| claude  | .claude/skills/<id>/SKILL.md          | .claude/agents/<id>.md              |
| opencode| .opencode/skills/<id>/SKILL.md        | .opencode/agent/<id>.md             |
| cursor  | .cursor/skills/<id>/SKILL.md          | None (no native agent surface)      |
"""

from __future__ import annotations

from pathlib import Path

from garage_os.adapter.installer.hosts.claude import ClaudeInstallAdapter
from garage_os.adapter.installer.hosts.cursor import CursorInstallAdapter
from garage_os.adapter.installer.hosts.opencode import OpenCodeInstallAdapter


class TestClaudeInstallAdapter:
    def test_host_id(self) -> None:
        assert ClaudeInstallAdapter().host_id == "claude"

    def test_target_skill_path(self) -> None:
        adapter = ClaudeInstallAdapter()
        assert adapter.target_skill_path("garage-hello") == Path(
            ".claude/skills/garage-hello/SKILL.md"
        )

    def test_target_agent_path(self) -> None:
        adapter = ClaudeInstallAdapter()
        assert adapter.target_agent_path("sample") == Path(".claude/agents/sample.md")

    def test_render_default_passthrough(self) -> None:
        adapter = ClaudeInstallAdapter()
        assert adapter.render("hello\nworld\n") == "hello\nworld\n"


class TestOpenCodeInstallAdapter:
    def test_host_id(self) -> None:
        assert OpenCodeInstallAdapter().host_id == "opencode"

    def test_target_skill_path(self) -> None:
        adapter = OpenCodeInstallAdapter()
        assert adapter.target_skill_path("garage-hello") == Path(
            ".opencode/skills/garage-hello/SKILL.md"
        )

    def test_target_agent_path(self) -> None:
        # ADR-D7-3 表第 2 行：opencode agent 目录为单数 "agent/"。
        adapter = OpenCodeInstallAdapter()
        assert adapter.target_agent_path("sample") == Path(".opencode/agent/sample.md")


class TestCursorInstallAdapter:
    def test_host_id(self) -> None:
        assert CursorInstallAdapter().host_id == "cursor"

    def test_target_skill_path(self) -> None:
        adapter = CursorInstallAdapter()
        assert adapter.target_skill_path("garage-hello") == Path(
            ".cursor/skills/garage-hello/SKILL.md"
        )

    def test_target_agent_path_returns_none(self) -> None:
        # ADR-D7-3: Cursor 当前无原生 agent surface。
        adapter = CursorInstallAdapter()
        assert adapter.target_agent_path("sample") is None
