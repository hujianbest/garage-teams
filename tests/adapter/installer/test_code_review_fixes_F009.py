"""F009 code-review (r1) 修复测试: I-3 (UserHomeNotFoundError 死路径) + I-4 (extend mode 跨 scope).

Covers:
- code-review-F009-r1 I-3: UserHomeNotFoundError 在 Path.home() 抛 RuntimeError 时被真正 raise
- code-review-F009-r1 I-4: _merge_with_existing 跨 scope 不漂移 (manifest 与磁盘一致)

Sister tests for code-review fixes confirmed during cycle.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from garage_os.adapter.installer.manifest import (
    UserHomeNotFoundError,
    read_manifest,
)
from garage_os.adapter.installer.pipeline import install_packs


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKS_ROOT = REPO_ROOT / "packs"


def _link_packs(tmp_path: Path) -> None:
    link = tmp_path / "packs"
    if not link.exists() and not link.is_symlink():
        link.symlink_to(PACKS_ROOT)


class TestI3_UserHomeNotFoundErrorRealRaise:
    """code-review-F009-r1 I-3: 真正接通 UserHomeNotFoundError.

    现状 (修复前): Path.home() 在 adapter / pipeline 多处直接调用, 无 try/except;
    UserHomeNotFoundError 类型存在但永远不会被 raise → CLI catch 路径死代码.

    修复 (T-postcr): 在 _resolve_targets user scope 分支前 try/except 包裹 Path.home();
    在 adapter.target_skill_path_user / target_agent_path_user 调用处 try/except 包裹.
    """

    def test_user_scope_with_path_home_runtime_error_raises_user_home_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ADR-D9-10: Path.home() 抛 RuntimeError 时 user scope install 抛 UserHomeNotFoundError."""
        _link_packs(tmp_path)

        # monkeypatch Path.home() 抛 RuntimeError (模拟 $HOME 未设置场景)
        def _broken_home(cls):
            raise RuntimeError("Could not determine home directory.")

        monkeypatch.setattr(Path, "home", classmethod(_broken_home))

        # user scope install 应抛 UserHomeNotFoundError (而非 Python 默认 RuntimeError traceback)
        with pytest.raises(UserHomeNotFoundError) as exc_info:
            install_packs(
                workspace_root=tmp_path,
                packs_root=tmp_path / "packs",
                hosts=["claude"],
                scopes_per_host={"claude": "user"},
            )
        # 错误消息应保留原始 RuntimeError 信息
        assert "Could not determine home directory" in str(exc_info.value)

    def test_project_scope_unaffected_by_path_home_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CON-901: project scope install 即使 Path.home() 失败也不应受影响 (因为不需要 home)."""
        _link_packs(tmp_path)

        def _broken_home(cls):
            raise RuntimeError("Could not determine home directory.")

        monkeypatch.setattr(Path, "home", classmethod(_broken_home))

        # project scope 不调用 Path.home(), 应正常完成
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            scopes_per_host={"claude": "project"},
        )
        # 落盘文件存在
        assert (tmp_path / ".claude/skills/garage-hello/SKILL.md").exists()


class TestI4_MergeExistingCrossScopeNoDrift:
    """code-review-F009-r1 I-4: _merge_with_existing 跨 scope key 升级.

    现状 (修复前): drop key 是 'host' 单维; 用户先 user scope claude, 再 project scope claude
    时, 第二次 init 的 _merge_with_existing 会 drop 所有 prior user scope claude entry
    → manifest 丢失 user scope 安装记录, 但磁盘文件还在.

    修复 (T-postcr): drop key 升级为 (host, scope) 二元 host-scope key.
    """

    def test_install_user_then_project_same_host_keeps_user_in_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """同 host 先装 user 再装 project, manifest 应保留 user scope 记录."""
        fake_home = tmp_path / "fake-home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
        _link_packs(tmp_path)

        # Step 1: install claude:user
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            scopes_per_host={"claude": "user"},
        )
        manifest_after_step1 = read_manifest(tmp_path / ".garage")
        assert manifest_after_step1 is not None
        user_entries_count = sum(
            1 for e in manifest_after_step1.files
            if e.host == "claude" and e.scope == "user"
        )
        assert user_entries_count > 0

        # Step 2: install claude:project (extend mode 同 host 不同 scope)
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            scopes_per_host={"claude": "project"},
        )
        manifest_after_step2 = read_manifest(tmp_path / ".garage")
        assert manifest_after_step2 is not None

        # I-4 修复后期望: manifest 同时含 user + project scope claude entry
        user_entries = [
            e for e in manifest_after_step2.files
            if e.host == "claude" and e.scope == "user"
        ]
        project_entries = [
            e for e in manifest_after_step2.files
            if e.host == "claude" and e.scope == "project"
        ]
        assert user_entries, (
            "I-4 修复期望: 同 host 不同 scope 二次 init 后, manifest 应保留 user scope 记录; "
            "实际 manifest 只剩 project entry, 与磁盘漂移 (~/.claude/skills/ 文件还在)"
        )
        assert project_entries, "Step 2 project install 应在 manifest 留下 project entry"

        # 磁盘对应文件都还在
        assert (fake_home / ".claude/skills/garage-hello/SKILL.md").exists()
        assert (tmp_path / ".claude/skills/garage-hello/SKILL.md").exists()

    def test_install_project_then_user_same_host_keeps_project_in_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """对称: 先 project 再 user, manifest 应保留 project scope 记录."""
        fake_home = tmp_path / "fake-home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
        _link_packs(tmp_path)

        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            scopes_per_host={"claude": "project"},
        )
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            scopes_per_host={"claude": "user"},
        )

        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None

        scopes_for_claude = {
            e.scope for e in manifest.files if e.host == "claude"
        }
        assert scopes_for_claude == {"user", "project"}, (
            f"manifest claude scopes={scopes_for_claude}, 期望 {{user, project}}"
        )

    def test_idempotent_same_scope_re_install_no_change(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """同 host 同 scope 二次 install 是幂等的 (manifest entries 数不变)."""
        fake_home = tmp_path / "fake-home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))
        _link_packs(tmp_path)

        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            scopes_per_host={"claude": "user"},
        )
        manifest1 = read_manifest(tmp_path / ".garage")
        assert manifest1 is not None
        count1 = len(manifest1.files)

        # 二次 install (同 scope) 应幂等
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
            scopes_per_host={"claude": "user"},
        )
        manifest2 = read_manifest(tmp_path / ".garage")
        assert manifest2 is not None
        count2 = len(manifest2.files)

        assert count1 == count2, (
            f"幂等再装: count1={count1}, count2={count2}; should be equal"
        )
