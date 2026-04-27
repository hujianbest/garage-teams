# F012 Task Plan: Pack Lifecycle 完整化

- 状态: 草稿（待 hf-tasks-review）
- 关联 spec: `docs/features/F012-pack-lifecycle-completion.md` (r2 已批准)
- 关联 design: `docs/designs/2026-04-25-pack-lifecycle-completion-design.md` (r2 已批准)
- 测试基线: 859 passed (post-PR#30+#32 main)

## 1. 任务总览

> **Current Active Task selection rule**: 按 P 升序 (P=1..5 唯一); T2 依赖 T1 helper, 不可并行.

| Task | P | Depends | 描述 | 主要文件 |
|---|---|---|---|---|
| **T1** | 1 | — | uninstall_pack + CLI | `pack_install.py` + `cli.py` + 测试 |
| **T2** | 2 | T1 `_clone_pack_to_tempdir` helper | update_pack + CLI | `pack_install.py` + `cli.py` + 测试 |
| **T3** | 3 | — | publish_pack + sensitive_scan + CLI | `pack_install.py` + `cli.py` + 测试 |
| **T4** | 4 | — | knowledge export --anonymize + CLI | `knowledge/exporter.py` (NEW) + `cli.py` + 测试 |
| **T5** | 5 | — | F009 carry-forward + docs + finalize | `manifest.py` + `version_manager.py` + AGENTS + RELEASE_NOTES + `tests/sync/test_baseline_no_regression.py` (F010 sentinel 沿用) |

## 2. T1 — uninstall_pack + CLI

**改动文件**:
- `src/garage_os/adapter/installer/pack_install.py`: 加 `UninstallSummary` dataclass + `uninstall_pack(workspace_root, pack_id, *, dry_run=False, yes=False, stderr=None) -> UninstallSummary`
  - 三步 transaction (ADR-D12-2): plan / confirm / execute
  - Touch boundary 显式: 仅触碰 packs/<id>/ + .garage/config/host-installer.json + host 目录映射文件; 不读不写 sync-manifest/knowledge/experience/sessions/contracts/platform.json/host-adapter.json
- `src/garage_os/cli.py`: 加 `pack uninstall <pack-id> [--yes] [--dry-run]` subcommand + `_pack_uninstall(workspace_root, pack_id, *, yes, dry_run)`

**Acceptance** (FR-1201..1203):
- `garage pack uninstall <pack-id>` interactive prompt → 'n' → exit 0 + 文件未变
- `garage pack uninstall <pack-id> --yes` → packs/<id>/ + host 目录映射 + host-installer.json files[] + installed_packs[] 全清
- `garage pack uninstall <pack-id> --dry-run` → stdout "DRY RUN" + per-line "would remove <path>" + 文件未变
- `garage pack uninstall nonexistent` → exit 1 + stderr "Pack not installed"
- INV-F12-9: uninstall 后 sync-manifest.json (如存在) 字节级不变

**Test files**:
- `tests/adapter/installer/test_pack_uninstall.py` (新): 7 用例覆盖 happy path + interactive cancel + dry-run + nonexistent + sync-manifest 不动 sentinel + 反向清 sidecar (F010 PR#30 配合) + manifest installed_packs 同步

## 3. T2 — update_pack + CLI (依赖 T1 抽出 helper)

**改动文件**:
- `pack_install.py`: 重构 install_pack_from_url 内部 git clone 抽出 `@contextlib.contextmanager _clone_pack_to_tempdir(url) -> Iterator[Path]` (ADR-D12-3 r2 fix); 加 `UpdateSummary` + `update_pack(workspace_root, pack_id, *, yes=False, preserve_local_edits=False, stderr=None) -> UpdateSummary`
  - 调 `install_packs(workspace_root, packs_root=workspace_root/"packs", hosts=已装, force=True, scopes_per_host=已装)` 反向同步 host (ADR-D12-3 r2 真实签名)
- `cli.py`: 加 `pack update <pack-id> [--yes] [--preserve-local-edits]` subcommand

**Acceptance** (FR-1204..1206):
- `garage pack update <pack-id>` 远端 == 本地 → "Already up to date" + exit 0
- `garage pack update <pack-id> --yes` 远端 != 本地 → 替换 packs/<id>/ + host 目录 SKILL.md hash 更新 + stdout "Updated ... from vX to vY"
- 失败时 (clone fail / 验证 fail) → 滚回 + stderr "Update failed, rolled back to v<old>" + exit 1
- `--preserve-local-edits` + 本地有改 → stderr warn (本 cycle 不真做 merge, F013 D-1211 deferred)
- Interactive cancel: 无 --yes 输 'n' → exit 0 + packs 字节级不变

**Test files**:
- `tests/adapter/installer/test_pack_update.py` (新): 6 用例覆盖 happy path + already-up-to-date + interactive cancel + rollback on failure + --preserve-local-edits warn + host 目录同步 (force=True)

## 4. T3 — publish_pack + sensitive_scan + CLI

**改动文件**:
- `pack_install.py`: 加 `SensitiveMatch` dataclass + `sensitive_scan(pack_dir) -> list[SensitiveMatch]` (按 ADR-D12-4 SENSITIVE_RULES 5 类 + TEXT_EXTENSIONS allowlist) + `PublishSummary` + `publish_pack(workspace_root, pack_id, to_url, *, yes, force, dry_run, no_update_source_url, commit_author, commit_message, stderr) -> PublishSummary`
  - Phase A-E dispatch (ADR-D12-4 r2)
  - `git init -b main` + fallback for older git
  - `_resolve_commit_author(commit_author) -> tuple[str, str]` helper (读 git config + fallback)
- `cli.py`: 加 `pack publish <pack-id> --to <git-url> [--yes] [--force] [--dry-run] [--no-update-source-url] [--commit-author "Name <email>"] [--commit-message <msg>]`

**Acceptance** (FR-1207..1210):
- 9 sub-test 1:1 ↔ FR-1207 r2 9 行 flag 状态表
- File:// publish 端到端: `garage pack publish my-pack --to file:///tmp/remote-bare.git --yes` → `git clone file:///tmp/remote-bare.git` 拿回完整 pack
- Sensitive scan: pack 含 `password=...` 文件 → default abort exit 1; `--force` 跳过 (但仍主 prompt); `--yes --force` 完全 unattended
- `--dry-run` 隐含 yes; sensitive scan 仍跑 (但不 abort)
- Stdout marker: `Published pack '<id>' v<version> to <url>`
- pack.json source_url 写回; `--no-update-source-url` 跳过

**Test files**:
- `tests/adapter/installer/test_sensitive_scan.py` (新): 5 类 SENSITIVE_RULES fixture all hit + binary skip 统计
- `tests/adapter/installer/test_pack_publish.py` (新): 9 sub-test (flag 矩阵) + file:// e2e + force-push 风险检测 + author resolution + commit-author flag

## 5. T4 — knowledge export --anonymize + CLI

**改动文件**:
- `src/garage_os/knowledge/exporter.py` (新): `ExportSummary` + `export_anonymized(workspace_root, *, output_dir=None, dry_run=False, stderr=None) -> ExportSummary` + `ANONYMIZE_RULES` (7 类 per ADR-D12-5 r2) + `load_user_extra_rules() -> list[(name, pattern, replacement)]`
  - Mixed strategy: KnowledgeStore.list_entries 拿 metadata + filesystem read 拿原 markdown bytes
  - tarball 输出 default `~/.garage/exports/knowledge-<ISO ts>.tar.gz`
- `cli.py`: 加 `knowledge export --anonymize [--output <path>] [--dry-run]` subcommand

**Acceptance** (FR-1211..1213):
- `garage knowledge export --anonymize` → `~/.garage/exports/knowledge-<ts>.tar.gz` 创建
- Email / password / api_key / secret / token / sha1_hash / private_key fixture 全部脱敏
- entry id / topic / tags / type / date 字段不动 (front matter 保留, 仅 body 脱敏)
- `--output <workspace>/exports/...` 时 + .gitignore 不含 `exports/` → stderr warn 提醒加 .gitignore
- `--dry-run` 仅 print 命中规则 + entry count 不写 tarball
- 用户 `~/.garage/anonymize-patterns.txt` 加 extra regex 生效

**Test files**:
- `tests/knowledge/test_exporter.py` (新): 7 用例覆盖 7 类 ANONYMIZE_RULES + dry-run + custom output path warn + user extra rules + tarball manifest.json + front matter 不动

## 6. T5 — F009 carry-forward + docs + finalize

**改动文件**:
- `src/garage_os/adapter/installer/manifest.py`: 加 `_migrate_v1_to_v2_dict_form(data: dict) -> dict` (ADR-D12-6 r2 dict-level wrapper) + `@register_migration(1, 2)` decorator
- `src/garage_os/platform/version_manager.py`: `SUPPORTED_VERSIONS: List[int] = [1, 2]` (was [1])
- `AGENTS.md`: 加 "Pack Lifecycle (F012)" 段
- `docs/guides/garage-os-user-guide.md`: 加 pack uninstall/update/publish + knowledge export 用法段
- `RELEASE_NOTES.md`: 加 F012 段
- `docs/manual-smoke/F012-walkthrough.md`: 5 tracks (uninstall + update + publish + sensitive scan + export)
- `docs/approvals/F012-finalize-approval.md`: cycle closeout

**Acceptance** (FR-1214):
- `_MIGRATION_REGISTRY[(1, 2)]` 不为空且指向 `_migrate_v1_to_v2_dict_form`
- `2 in VersionManager.SUPPORTED_VERSIONS` (与 schema 1 并列)
- F009 既有 read_manifest fast-path 字节级不变
- 双源等价测试: `_migrate_v1_to_v2_dict_form(raw_dict)` 与 `read_manifest` 拿到的 Manifest 在 schema_version + files[].scope + 顶层字段层一致 (dst 字段差异由 fast-path workspace_root 拼接造成, ignore)

**Test files**:
- `tests/adapter/installer/test_manifest_migration_registry.py` (新): 4 用例 (registry 含 (1,2) + SUPPORTED_VERSIONS 含 2 + dict wrapper schema 字段 + 双源等价)
- `tests/sync/test_baseline_no_regression.py` (F010 sentinel 沿用): assert >= 859 (post-PR#30+#32 main baseline)

## 7. 测试基线守门

| Task 后 | 期望 | INV |
|---|---|---|
| T1 | ≥ 859 + ~7 | INV-F12-1/2/3/9 |
| T2 | ≥ 866 + ~6 | INV-F12-4 |
| T3 | ≥ 872 + ~9 + ~5 (sensitive_scan) | INV-F12-5/6 |
| T4 | ≥ 886 + ~7 | INV-F12-7 |
| T5 | ≥ 893 + ~4 (manifest registry) | INV-F12-8 + sentinel |

## 8. Carry-forward 守门 (in-cycle)

- F011 既有 install + ls 测试 0 退绿 (CON-1201)
- F009-F011 既有 859 baseline 0 退绿 (CON-1202)
- F010 既有 dogfood SHA-256 sentinel 仍守门 (NFR-1001 沿用)

## 9. Commit 分组 (NFR-904)

每 task 一 commit, 5 commits + manual smoke + finalize approval. 共 7 commit (与 F010 + F011 cycle 节奏一致).

## 10. 评审前自检 ✅ (供 hf-tasks-review)

- [x] 5 task 与 design § 5 ADR-D12-7 1:1 (T1-T5)
- [x] 每 task 含 改动文件 + Acceptance + Test files
- [x] 真实 API 锚点 (install_pack_from_url / install_packs / KnowledgeStore.list_entries / register_migration / _MIGRATION_REGISTRY / migrate_v1_to_v2)
- [x] T1 → T2 helper 依赖显式 (Depends 列)
- [x] CON-1207 守门 (F010 carry-forward 不修)
- [x] 测试基线守门 §7 与 design INV 一致
- [x] sentinel sentinel `tests/sync/test_baseline_no_regression.py` 沿用 (F010 INV-F10-2 + F012 INV-F12-2)
- [x] B5 user-pact 守门 (T1 prompt + T3 prompt + sensitive scan default + T4 opt-in via flag)
- [x] sync-manifest.json + knowledge/experience/sessions touch boundary (T1 ADR-D12-2 r2 F-7)
