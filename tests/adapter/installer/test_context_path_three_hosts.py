"""F010 T1: 三家 host adapter context surface 路径测试.

Covers:
- spec FR-1004 (三家 host context adapter)
- design ADR-D10-2 (HostInstallAdapter Protocol 字段扩展, 复用 F009 _user 后缀模式)

Fixture isolation (与 F009 user scope 测试同模式):
- monkeypatch Path.home() → tmp_path 隔离, 不污染真实 ~/
"""

from __future__ import annotations

from pathlib import Path

import pytest

from garage_os.adapter.installer.host_registry import (
    HOST_REGISTRY,
    HostInstallAdapter,
    get_adapter,
)


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake = tmp_path / "fake-home"
    fake.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake))
    return fake


class TestProjectScope:
    """FR-1004 + ADR-D10-2: 三家 adapter project scope 路径正确."""

    def test_claude_project_path(self) -> None:
        adapter = get_adapter("claude")
        assert adapter.target_context_path("garage-context") == Path("CLAUDE.md")

    def test_cursor_project_path(self) -> None:
        adapter = get_adapter("cursor")
        assert adapter.target_context_path("garage-context") == Path(
            ".cursor/rules/garage-context.mdc"
        )

    def test_opencode_project_path(self) -> None:
        adapter = get_adapter("opencode")
        assert adapter.target_context_path("garage-context") == Path(
            ".opencode/AGENTS.md"
        )

    def test_cursor_name_param_used(self) -> None:
        """ADR-D10-2: cursor 用 name 参数生成 <name>.mdc."""
        adapter = get_adapter("cursor")
        assert adapter.target_context_path("custom-name") == Path(
            ".cursor/rules/custom-name.mdc"
        )


class TestUserScope:
    """FR-1004 + ADR-D10-2: 三家 adapter user scope 路径在 fake_home 下."""

    def test_claude_user_path(self, fake_home: Path) -> None:
        adapter = get_adapter("claude")
        assert adapter.target_context_path_user("garage-context") == (
            fake_home / ".claude" / "CLAUDE.md"
        )

    def test_cursor_user_path(self, fake_home: Path) -> None:
        adapter = get_adapter("cursor")
        assert adapter.target_context_path_user("garage-context") == (
            fake_home / ".cursor" / "rules" / "garage-context.mdc"
        )

    def test_opencode_user_path_xdg_default(self, fake_home: Path) -> None:
        """ADR-D10-2 + F009 ASM: OpenCode 走 XDG default ~/.config/opencode/."""
        adapter = get_adapter("opencode")
        assert adapter.target_context_path_user("garage-context") == (
            fake_home / ".config" / "opencode" / "AGENTS.md"
        )


class TestProtocolCompliance:
    """ADR-D10-2: HostInstallAdapter Protocol 字段扩展同一类, 三家都满足."""

    def test_three_hosts_implement_protocol(self) -> None:
        """三家 first-class adapter 都符合 HostInstallAdapter Protocol (含 F010 加的 method)."""
        for host_id, adapter in HOST_REGISTRY.items():
            assert isinstance(adapter, HostInstallAdapter), (
                f"{host_id} adapter does not satisfy HostInstallAdapter Protocol "
                "(missing target_context_path or target_context_path_user)"
            )

    def test_target_context_path_returns_path(self) -> None:
        """target_context_path 返回 Path 对象 (mypy + runtime 双守门)."""
        for host_id in HOST_REGISTRY:
            adapter = get_adapter(host_id)
            result = adapter.target_context_path("garage-context")
            assert isinstance(result, Path)


class TestF009MethodsUnchanged:
    """CON-1001: F009 既有 method 签名 + 返回值不变 (carry-forward sentinel)."""

    def test_target_skill_path_user_unchanged(self, fake_home: Path) -> None:
        """F009 既有 target_skill_path_user 字节级行为不变."""
        claude = get_adapter("claude")
        assert claude.target_skill_path_user("garage-hello") == (
            fake_home / ".claude" / "skills" / "garage-hello" / "SKILL.md"
        )

    def test_target_agent_path_unchanged(self) -> None:
        """F007 既有 target_agent_path: cursor 仍返回 None."""
        cursor = get_adapter("cursor")
        assert cursor.target_agent_path("any") is None
