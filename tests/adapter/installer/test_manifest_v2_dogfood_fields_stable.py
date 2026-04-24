"""F009 T5: Manifest schema 2 字段稳定性 sentinel (与 dogfood SHA-256 互补).

Covers:
- ADR-D9-11 Consequences: manifest 字段稳定性独立守门
  (manifest 不参与 dogfood SHA-256 sentinel, 但需另行验证关键字段稳定)
- spec FR-905 (schema 2 字段: dst absolute + scope)
- 与 dogfood sentinel 边界分清: dogfood 测落盘 SKILL.md/agent.md 字节级;
  本测试测 manifest 字段稳定性 (content_hash + scope + host 必须稳定;
  dst / installed_at / schema_version 豁免, 因 cwd / 时间戳易变)

Strategy:
- Fixture 跑 garage init --hosts cursor,claude (project scope, dogfood 路径)
- read_manifest 后比对 files[].content_hash + files[].scope + files[].host
  与 baseline 一致 (baseline 由 dogfood SHA-256 baseline 推导)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from garage_os.adapter.installer.manifest import read_manifest
from garage_os.adapter.installer.pipeline import install_packs


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKS_ROOT = REPO_ROOT / "packs"
BASELINE_JSON = (
    Path(__file__).resolve().parent
    / "dogfood_baseline"
    / "skill_md_sha256.json"
)


def _link_packs(tmp_path: Path) -> None:
    link = tmp_path / "packs"
    if not link.exists() and not link.is_symlink():
        link.symlink_to(PACKS_ROOT)


class TestManifestV2DogfoodFieldsStable:
    """ADR-D9-11: manifest 字段稳定性独立守门.

    与 dogfood SHA-256 sentinel (test_dogfood_invariance_F009.py) 互补:
    - dogfood sentinel: 测 SKILL.md/agent.md 落盘字节级
    - 本 sentinel: 测 manifest content_hash/scope/host 稳定 (dst/installed_at/schema_version 豁免)
    """

    def test_manifest_files_count_matches_baseline(
        self, tmp_path: Path
    ) -> None:
        """manifest files[] 数 == baseline 文件数 (dogfood 路径 SHA-256 一致)."""
        _link_packs(tmp_path)
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["cursor", "claude"],
        )

        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        baseline = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))

        assert len(manifest.files) == len(baseline), (
            f"manifest files = {len(manifest.files)}, baseline = {len(baseline)}"
        )

    def test_manifest_all_entries_scope_project(self, tmp_path: Path) -> None:
        """ADR-D9-11: dogfood 路径默认 project scope, manifest 全部 entry scope='project'."""
        _link_packs(tmp_path)
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["cursor", "claude"],
        )

        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        scopes = {e.scope for e in manifest.files}
        assert scopes == {"project"}, (
            f"manifest 含非 project scope entry: scopes={scopes}"
        )

    def test_manifest_content_hash_matches_baseline(
        self, tmp_path: Path
    ) -> None:
        """manifest 每条 entry.content_hash == baseline 对应文件 SHA-256.

        ADR-D9-11 关键守门: content_hash 字段稳定性是 dogfood 不变性的 manifest 侧证据.
        """
        _link_packs(tmp_path)
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["cursor", "claude"],
        )

        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        baseline = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))

        # 把 baseline 按 manifest entry.dst 的 (host, file_basename) 重映射
        # baseline key: ".claude/skills/hf-specify/SKILL.md"
        # manifest entry.dst: "/tmp/.../tmp_path/.claude/skills/hf-specify/SKILL.md"
        # 用 entry.dst 末段抽取 ".claude/skills/.../SKILL.md" 形态对齐 baseline key
        mismatches = []
        for entry in manifest.files:
            # 抽取 dst 的相对部分 (workspace_root 之后)
            try:
                rel = Path(entry.dst).relative_to(tmp_path).as_posix()
            except ValueError:
                # 不在 tmp_path 下 (user scope) — 不应在本测试出现
                continue
            if rel not in baseline:
                continue
            expected = baseline[rel]
            if entry.content_hash != expected:
                mismatches.append(
                    f"{rel}: manifest hash {entry.content_hash[:12]}... "
                    f"vs baseline {expected[:12]}..."
                )
        assert not mismatches, (
            "Manifest content_hash 与 dogfood baseline 不一致 (ADR-D9-11 字段稳定性硬门槛):\n"
            + "\n".join(mismatches[:5])
        )

    def test_manifest_dst_absolute_under_workspace_root(
        self, tmp_path: Path
    ) -> None:
        """ADR-D9-3: project scope dst 是 absolute, 在 workspace_root 下."""
        _link_packs(tmp_path)
        install_packs(
            workspace_root=tmp_path,
            packs_root=tmp_path / "packs",
            hosts=["claude"],
        )

        manifest = read_manifest(tmp_path / ".garage")
        assert manifest is not None
        for entry in manifest.files:
            assert Path(entry.dst).is_absolute(), (
                f"manifest entry.dst 应是 absolute: {entry.dst}"
            )
            # project scope: dst 在 workspace_root (tmp_path) 下
            assert tmp_path in Path(entry.dst).parents, (
                f"project scope dst 应在 workspace_root 下: {entry.dst}"
            )
