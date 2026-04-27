"""Install manifest persistence: ``.garage/config/host-installer.json``.

Implements F007 FR-705 + design D7 §8.3 / §11.2 / NFR-703 / CON-703.
F009 (FR-905 + ADR-D9-1/3/8/10 + CON-904) extends to schema 2 with:

- ``files[].dst`` 改为 absolute POSIX path (含用户 home 部分)
- ``files[].scope`` 字段 (``"project"`` / ``"user"``)
- F007 既有 schema 1 manifest 自动 migration 到 schema 2 (T3 实施)
- ``ManifestMigrationError``: JSON 损坏 / 字段缺失时抛, 且**旧 manifest 不被覆盖**
  (FR-905 验收 #4 + CON-904 安全语义硬门槛)
- ``UserHomeNotFoundError``: ``Path.home()`` 抛 RuntimeError 时由 pipeline 捕获后 raise

The manifest is the **idempotency credential** for ``garage init`` re-runs:
each entry records (src, dst, host, pack_id, scope, content_hash) so the pipeline
can decide whether a target file is "still Garage-owned" (hash matches),
"locally modified" (hash differs), or "newly added by user" (no entry).

Stability invariants for clean ``git diff``:

- ``installed_hosts`` and ``installed_packs`` are written ASCII-sorted
- ``files[]`` is written sorted by (src, dst, host, scope)
- All path strings serialize as POSIX forward slashes regardless of OS
- ``schema_version`` field 由 VersionManager 管控 (CON-703 + CON-904)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

# F009: schema 升级到 2. F007 既有 schema 1 manifest 由 read_manifest 自动 migrate.
MANIFEST_SCHEMA_VERSION = 2
MANIFEST_FILENAME = "host-installer.json"
CONFIG_SUBDIR = "config"


class ManifestMigrationError(ValueError):
    """F009 ADR-D9-8: Raised when manifest migration fails (JSON 损坏 / 字段缺失).

    安全语义硬门槛 (FR-905 验收 #4 + CON-904): 抛出此异常时, **旧 manifest 文件
    字节级不被覆盖** — 由 read_manifest 在抛异常前 NOT 写入新内容来保证.
    pipeline / CLI 层 catch 后 → exit 1 + stderr 含 'Manifest migration failed: ...'.
    """


class UserHomeNotFoundError(RuntimeError):
    """F009 ADR-D9-10: Raised when ``Path.home()`` cannot resolve user home directory.

    由 pipeline._resolve_targets 在 user scope 分流时, catch ``Path.home()``
    抛的 ``RuntimeError`` 后 raise. CLI 层 catch → exit 1 + stderr 含
    'Cannot determine user home directory: ...'.

    与 ManifestMigrationError 处理对称 (ADR-D9-8 + ADR-D9-10), 都映射 exit 1
    (沿用 F007 退出码语义稳定性).
    """


@dataclass
class ManifestFileEntry:
    """One file installed by Garage into a host directory.

    F007 schema 1 fields:
        src: project-relative POSIX path to the source under ``packs/``
        dst: project-relative POSIX path to the installed file
        host: host id (e.g. ``"claude"``)
        pack_id: pack id this file came from
        content_hash: SHA-256 hex of the bytes actually written to ``dst``
                      (i.e. after marker injection, not the raw source)

    F009 schema 2 changes (CON-901: F007 既有类名保留, 字段扩展同一类, 不引入新类):
        dst: 改为 **absolute** POSIX path (含 home 部分 for user scope; 含 cwd
             for project scope) — 与 F007 schema 1 的 project-relative 形式不同
        scope: 新增 ``"project"`` | ``"user"`` 字段, 默认 ``"project"`` (向后兼容)
    """

    src: str
    dst: str  # F009: schema 2 = absolute POSIX; schema 1 = project-relative POSIX
    host: str
    pack_id: str
    content_hash: str
    # F009 ADR-D9-1: scope 字段, 默认 'project' 兼容 schema 1 entry (migration 路径)
    scope: str = "project"


@dataclass
class Manifest:
    """Top-level structure persisted to ``.garage/config/host-installer.json``."""

    schema_version: int
    installed_hosts: list[str]
    installed_packs: list[str]
    installed_at: str  # ISO-8601
    files: list[ManifestFileEntry] = field(default_factory=list)


def write_manifest(garage_dir: Path, manifest: Manifest) -> Path:
    """Persist ``manifest`` to ``garage_dir/config/host-installer.json``.

    F009: 始终写入当前 ``MANIFEST_SCHEMA_VERSION`` (即 2). 调用方传入的
    manifest.schema_version 字段被覆盖, 确保所有 fresh write 都是最新 schema.

    Returns the file path written. Sorts list-valued fields and converts
    paths to POSIX form for cross-platform stability (NFR-703).
    """
    config_dir = garage_dir / CONFIG_SUBDIR
    config_dir.mkdir(parents=True, exist_ok=True)
    target = config_dir / MANIFEST_FILENAME

    payload = _to_serializable(manifest)
    target.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def read_manifest(garage_dir: Path) -> Manifest | None:
    """Load manifest from ``garage_dir/config/host-installer.json``, or None.

    Returns None if the file does not exist (i.e. first-time install).

    F009 (FR-905 + CON-904 安全语义):
    - schema_version=1 → 自动 migrate 到 schema_version=2 (内存中, 不立即覆盖磁盘);
      调用方在 install_packs 完成后 write_manifest 时才会写入 schema 2 内容
    - JSON 损坏 / 字段缺失 → 抛 ``ManifestMigrationError``, **旧文件字节级不被覆盖**
      (本函数不做任何写操作, 只 raise)

    Args:
        garage_dir: 通常 ``workspace_root / ".garage"``

    Raises:
        ManifestMigrationError: when JSON parse fails or required fields are missing.
    """
    target = garage_dir / CONFIG_SUBDIR / MANIFEST_FILENAME
    if not target.is_file():
        return None
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        # F009 安全语义: 抛 ManifestMigrationError 不写文件, 旧 manifest 字节级保留
        raise ManifestMigrationError(
            f"Failed to parse manifest at {target}: {exc}"
        ) from exc

    schema_version = int(raw.get("schema_version", MANIFEST_SCHEMA_VERSION))

    if schema_version == 1:
        # F009 ADR-D9-1/3: schema 1 → 2 migration
        # 旧 entry 默认 scope = "project"; dst 仍是 project-relative (由
        # pipeline.install_packs 写入新 manifest 时再转 absolute, 由 ADR-D9-2
        # phase 5 内部 ManifestSerializer 完成).
        try:
            return _from_dict_v1_migrate(raw, garage_dir)
        except (KeyError, TypeError, ValueError) as exc:
            raise ManifestMigrationError(
                f"Failed to migrate schema 1 manifest at {target}: {exc}"
            ) from exc

    if schema_version == 2:
        try:
            return _from_dict_v2(raw)
        except (KeyError, TypeError, ValueError) as exc:
            raise ManifestMigrationError(
                f"Failed to parse schema 2 manifest at {target}: {exc}"
            ) from exc

    raise ManifestMigrationError(
        f"Unsupported manifest schema_version={schema_version} in {target}; "
        f"supported: 1 (auto-migrated) or 2"
    )


def migrate_v1_to_v2(prior_v1: Manifest, workspace_root: Path) -> Manifest:
    """F009 FR-905 + ADR-D9-3: migrate a schema 1 Manifest to schema 2 in-memory.

    每条 entry: ``scope = "project"`` + ``dst = (workspace_root / dst_rel).as_posix()``.
    ``schema_version`` 字段 1 → 2; 其它顶层字段 (installed_hosts / installed_packs /
    installed_at) 保持不变.

    Args:
        prior_v1: schema 1 Manifest (from read_manifest with auto-detect)
        workspace_root: 用于把 project-relative dst 转 absolute

    Returns:
        schema 2 Manifest (字段扩展同一类 ManifestFileEntry, 不引入新类)
    """
    new_files: list[ManifestFileEntry] = []
    for e in prior_v1.files:
        # schema 1 dst 是 project-relative POSIX; schema 2 改为 absolute POSIX
        old_dst = e.dst
        if PurePosixPath(old_dst).is_absolute():
            # 防御性: 若已是 absolute (异常 schema 1 数据), 保留
            new_dst = old_dst
        else:
            new_dst = (workspace_root / old_dst).as_posix()
        new_files.append(
            ManifestFileEntry(
                src=e.src,
                dst=new_dst,
                host=e.host,
                pack_id=e.pack_id,
                content_hash=e.content_hash,
                scope="project",  # F009 schema 1 entry 默认 project (F007/F008 行为)
            )
        )
    return Manifest(
        schema_version=2,
        installed_hosts=prior_v1.installed_hosts,
        installed_packs=prior_v1.installed_packs,
        installed_at=prior_v1.installed_at,
        files=new_files,
    )


def _to_serializable(manifest: Manifest) -> dict[str, Any]:
    """Convert Manifest to JSON-serializable dict with stability invariants.

    F009: 始终写 schema_version=2 (覆盖调用方传入值, 确保 fresh write 是最新 schema).
    """
    files_sorted = sorted(
        manifest.files, key=lambda e: (e.src, e.dst, e.host, e.scope)
    )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,  # F009: 始终写 2
        "installed_hosts": sorted(manifest.installed_hosts),
        "installed_packs": sorted(manifest.installed_packs),
        "installed_at": manifest.installed_at,
        "files": [
            {
                "src": _to_posix(e.src),
                "dst": _to_posix(e.dst),
                "host": e.host,
                "pack_id": e.pack_id,
                "scope": e.scope,
                "content_hash": e.content_hash,
            }
            for e in files_sorted
        ],
    }


def _from_dict_v1_migrate(raw: dict[str, Any], garage_dir: Path) -> Manifest:
    """Read schema 1 raw dict + auto-migrate to schema 2 in-memory.

    workspace_root 由 garage_dir.parent 推导 (garage_dir = workspace_root/.garage).
    """
    # 先按 schema 1 解析 (无 scope 字段)
    schema_v1_files = sorted(
        [
            ManifestFileEntry(
                src=str(f["src"]),
                dst=str(f["dst"]),
                host=str(f["host"]),
                pack_id=str(f["pack_id"]),
                content_hash=str(f["content_hash"]),
                scope="project",  # 默认 (F007/F008 行为)
            )
            for f in raw.get("files", [])
        ],
        key=lambda e: (e.src, e.dst),
    )
    v1 = Manifest(
        schema_version=1,
        installed_hosts=sorted(raw.get("installed_hosts", [])),
        installed_packs=sorted(raw.get("installed_packs", [])),
        installed_at=str(raw.get("installed_at", "")),
        files=schema_v1_files,
    )
    # 然后 migrate v1 → v2 (dst project-relative → absolute)
    return migrate_v1_to_v2(v1, garage_dir.parent)


def _from_dict_v2(raw: dict[str, Any]) -> Manifest:
    """Read schema 2 raw dict (no migration needed)."""
    files = sorted(
        [
            ManifestFileEntry(
                src=str(f["src"]),
                dst=str(f["dst"]),
                host=str(f["host"]),
                pack_id=str(f["pack_id"]),
                content_hash=str(f["content_hash"]),
                # F009 schema 2: scope 字段必须存在
                scope=str(f.get("scope", "project")),
            )
            for f in raw.get("files", [])
        ],
        key=lambda e: (e.src, e.dst, e.host, e.scope),
    )
    return Manifest(
        schema_version=2,
        installed_hosts=sorted(raw.get("installed_hosts", [])),
        installed_packs=sorted(raw.get("installed_packs", [])),
        installed_at=str(raw.get("installed_at", "")),
        files=files,
    )


def _to_posix(path_str: str) -> str:
    """Convert any OS-native path string to POSIX form (forward slashes)."""
    # PurePosixPath cannot accept '\' on its own, so normalize first.
    return PurePosixPath(*Path(path_str).parts).as_posix()


# ============================================================
# F012-E (FR-1214 + ADR-D12-6 r2): VersionManager registration
# ============================================================
#
# F009 finalize approval carry-forward I-2: register host-installer schema 1→2
# migration in VersionManager._MIGRATION_REGISTRY (parallel to F001 platform.json /
# host-adapter.json registrations).
#
# ADR-D12-6 r2 (scheme C, dict-level equivalent): wrapper signature compatible
# with VersionManager.migrate() single-arg call convention (`migrator(data)`,
# version_manager.py:323). The dataclass-form `migrate_v1_to_v2(prior_v1: Manifest,
# workspace_root: Path)` requires workspace_root which VersionManager.migrate() does
# not provide; this dict-level wrapper performs equivalent schema field transformations
# (schema_version 1 → 2 + add `scope: "project"` default to each file entry) but
# does NOT touch the `dst` field (that conversion remains in `read_manifest` fast-path
# which has workspace_root context).
from garage_os.platform.version_manager import register_migration


@register_migration(1, 2)
def _migrate_v1_to_v2_dict_form(data: dict[str, Any]) -> dict[str, Any]:
    """F012-E (ADR-D12-6 r2 scheme C): dict-level v1→v2 migration for VersionManager registry.

    Compatible with ``VersionManager.migrate()`` single-arg call (line 323).
    Equivalent semantics with ``migrate_v1_to_v2(Manifest, workspace_root)`` for
    schema_version + files[].scope; ``dst`` field is left as-is here (read_manifest
    fast-path is the canonical absolute-dst conversion path with workspace_root context).
    """
    out = dict(data)
    out["schema_version"] = 2
    out["files"] = [
        {**f, "scope": f.get("scope", "project")} for f in out.get("files", [])
    ]
    return out
