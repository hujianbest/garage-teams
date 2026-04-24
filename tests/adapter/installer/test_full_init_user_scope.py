"""F009 T5: end-to-end user scope 三家宿主全装集成测试.

Covers:
- spec FR-806 等价 (端到端三家宿主全装) + FR-901 + FR-904 + ADR-D9-2/6
- task plan T5 § 5 acceptance: 三家 user scope 落盘路径 (含 OpenCode XDG default 守门)
- INV-F9-1 (CON-901 + Dogfood SHA-256 一致 间接) / INV-F9-7 (manifest schema 2)
- INV-F9-8 (user scope 测试 fixture-isolated, 不污染真实 ~/)

Strategy:
- Fixture monkeypatch Path.home() → tmp_path/fake-home, 隔离真实 ~/
- 跑 garage init --hosts all --scope user
- 验证三家宿主目录全部存在 + manifest schema 2 含 scope='user' entry
"""

from __future__ import annotations

from pathlib import Path

import pytest

from garage_os.adapter.installer.manifest import read_manifest
from garage_os.adapter.installer.pipeline import install_packs


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKS_ROOT = REPO_ROOT / "packs"


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """INV-F9-8: monkeypatch Path.home() 隔离真实 ~/."""
    fake = tmp_path / "fake-home"
    fake.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake))
    return fake


def _link_packs(tmp_path: Path) -> None:
    link = tmp_path / "packs"
    if not link.exists() and not link.is_symlink():
        link.symlink_to(PACKS_ROOT)


class TestFullInitUserScopeThreeHosts:
    """端到端 garage init --hosts all --scope user, 三家宿主全装."""

    def test_install_three_hosts_user_scope_all_paths(
        self, tmp_path: Path, fake_home: Path
    ) -> None:
        """三家宿主 user scope 落盘路径全部正确 (FR-904 + ADR-D9-6 + § 2.3 调研锚点)."""
        _link_packs(tmp_path)

        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude", "cursor", "opencode"],
            scopes_per_host={"claude": "user", "cursor": "user", "opencode": "user"},
        )

        # claude user: ~/.claude/skills/<id>/SKILL.md + ~/.claude/agents/<id>.md
        assert (fake_home / ".claude/skills/garage-hello/SKILL.md").exists()
        assert (fake_home / ".claude/agents/garage-sample-agent.md").exists()

        # opencode user: ~/.config/opencode/skills/<id>/SKILL.md (XDG default!)
        # + ~/.config/opencode/agent/<id>.md
        assert (fake_home / ".config/opencode/skills/garage-hello/SKILL.md").exists()
        assert (
            fake_home / ".config/opencode/agent/garage-sample-agent.md"
        ).exists()

        # cursor user: ~/.cursor/skills/<id>/SKILL.md (无 agent surface)
        assert (fake_home / ".cursor/skills/garage-hello/SKILL.md").exists()
        # cursor 无 agent
        assert not (fake_home / ".cursor/agents").exists()
        assert not (fake_home / ".cursor/agent").exists()

        # CON-901: 不创建 cwd/.{host}/skills/
        assert not (tmp_path / ".claude").exists()
        assert not (tmp_path / ".cursor").exists()
        assert not (tmp_path / ".opencode").exists()

    def test_opencode_xdg_default_not_dotfiles_style(
        self, tmp_path: Path, fake_home: Path
    ) -> None:
        """ADR-D9-6 + spec § 11 阻塞性问题选定: OpenCode 走 XDG default ~/.config/opencode/,
        不走 dotfiles 风格 ~/.opencode/ (deferred 到 F010+)."""
        _link_packs(tmp_path)

        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["opencode"],
            scopes_per_host={"opencode": "user"},
        )

        # XDG default 路径
        assert (fake_home / ".config/opencode/skills/garage-hello/SKILL.md").exists()
        # dotfiles 风格不创建 (deferred)
        assert not (fake_home / ".opencode").exists()

    def test_manifest_schema_v2_user_scope_entries(
        self, tmp_path: Path, fake_home: Path
    ) -> None:
        """INV-F9-7: manifest 含 scope='user' entry, dst absolute 在 fake_home 下."""
        _link_packs(tmp_path)

        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            scopes_per_host={"claude": "user"},
        )

        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        assert manifest.schema_version == 2

        # 全部 entry scope='user'
        scopes = {e.scope for e in manifest.files}
        assert scopes == {"user"}

        # dst 是 absolute, 在 fake_home 下
        for entry in manifest.files:
            assert Path(entry.dst).is_absolute()
            assert fake_home in Path(entry.dst).parents

    def test_mixed_scope_per_host(
        self, tmp_path: Path, fake_home: Path
    ) -> None:
        """混合 scope: claude:user + cursor:project + opencode:user 正确分流."""
        _link_packs(tmp_path)

        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude", "cursor", "opencode"],
            scopes_per_host={
                "claude": "user",
                "cursor": "project",
                "opencode": "user",
            },
        )

        # claude user → fake_home/.claude/
        assert (fake_home / ".claude/skills/garage-hello/SKILL.md").exists()
        # cursor project → tmp_path/.cursor/
        assert (tmp_path / ".cursor/skills/garage-hello/SKILL.md").exists()
        # opencode user → fake_home/.config/opencode/
        assert (fake_home / ".config/opencode/skills/garage-hello/SKILL.md").exists()

        # 反向: claude / opencode 不在 cwd, cursor 不在 fake_home
        assert not (tmp_path / ".claude").exists()
        assert not (tmp_path / ".opencode").exists()
        assert not (fake_home / ".cursor").exists()

        # manifest 含两类 scope entry
        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        scopes = {e.scope for e in manifest.files}
        assert scopes == {"user", "project"}
