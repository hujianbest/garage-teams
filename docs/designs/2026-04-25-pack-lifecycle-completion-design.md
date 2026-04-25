# F012 Design: Pack Lifecycle 完整化

- 状态: 草稿 r2 (回应 design-review-F012-r1; 待 r2 hf-design-review)
- 关联 spec: `docs/features/F012-pack-lifecycle-completion.md` (r2 已批准, `docs/approvals/F012-spec-approval.md`)
- 日期: 2026-04-25

## 0. 设计目标

把 F012 spec 14 FR + 4 NFR + 7 CON + 4 ASM + 6 HYP + 4 BLK 翻译成可拆 task 的代码层结构. 5 子部分都是单领域改动.

**ADR Status 默认**: Accepted r1; r2 修订的 ADR (D12-2/3/4/6/7) 显式标 "Status: Accepted r2".

- **A** uninstall: `pack_install.py` 加 `uninstall_pack(workspace_root, pack_id)` + CLI subcommand
- **B** update: 同 module 加 `update_pack(workspace_root, pack_id)`, 复用 install 内部 helper
- **C** publish: 同 module 加 `publish_pack(workspace_root, pack_id, to_url, ...)` + sensitive_scan helper
- **D** knowledge export: 新 module `src/garage_os/knowledge/exporter.py` + `garage knowledge export --anonymize` CLI
- **E** F009 carry-forward: `manifest.py` 加 `@register_migration(1, 2)` decorator + VersionManager.SUPPORTED_VERSIONS 同步加 2

## 1. 架构概览

```
src/garage_os/
├── adapter/installer/
│   ├── pack_install.py (ext)
│   │   + uninstall_pack(workspace_root, pack_id, *, dry_run, yes, stderr) -> UninstallSummary
│   │   + update_pack(workspace_root, pack_id, *, yes, preserve_local_edits, stderr) -> UpdateSummary
│   │   + publish_pack(workspace_root, pack_id, to_url, *, yes, force, dry_run,
│   │                  no_update_source_url, commit_author, commit_message, stderr) -> PublishSummary
│   │   + sensitive_scan(pack_dir) -> list[SensitiveMatch]   (helper for publish)
│   └── manifest.py (ext)
│       + @register_migration(1, 2) on migrate_v1_to_v2
│
├── knowledge/
│   └── exporter.py (NEW)
│       + export_anonymized(workspace_root, *, output_dir, dry_run, stderr) -> ExportSummary
│       + ANONYMIZE_RULES: list[(name, pattern, replacement)]
│       + load_user_extra_rules() -> list[(name, pattern, replacement)]   (~/.garage/anonymize-patterns.txt)
│
├── platform/version_manager.py (ext)
│   + SUPPORTED_VERSIONS: List[int] = [1, 2]   (was [1])
│
└── cli.py (ext)
    + pack uninstall <pack-id> [--yes] [--dry-run]
    + pack update <pack-id> [--yes] [--preserve-local-edits]
    + pack publish <pack-id> --to <git-url> [--yes] [--force] [--dry-run]
                              [--no-update-source-url] [--commit-author "Name <email>"]
                              [--commit-message <msg>]
    + knowledge export --anonymize [--output <path>] [--dry-run]
```

依赖方向 (无环):
```
pack_install (ext) → manifest (ext) ← VersionManager
                  ↘ host_registry / hosts/* (既有, 不动)
exporter (NEW) → KnowledgeStore (既有, 不动)
cli (ext) → 上述全部
```

## 2. ADRs

### ADR-D12-1: 5 子部分共用同一 module 还是分开?

**Decision**: F012-A/B/C 三者都在 `pack_install.py` 同 module (与 F011 既有 `install_pack_from_url` + `list_installed_packs` 并列), 复用 PackInstallSummary 数据结构 pattern (UninstallSummary / UpdateSummary / PublishSummary). F012-D 在 `knowledge/exporter.py` (与 KnowledgeStore 同包, 自然位置). F012-E 在 manifest.py 顶部加一行 decorator + VersionManager.SUPPORTED_VERSIONS 加常数.

**Consequences**:
- (+) 单一职责: pack lifecycle 共一处, knowledge export 与 KnowledgeStore 同包
- (+) 复用 PackInstallError exception type 跨 install/uninstall/update/publish (统一 CLI catch)
- (-) `pack_install.py` 行数从 ~190 → ~600 (5x); 但仍 < 800, 接受 trade-off

### ADR-D12-2: uninstall 反向清磁盘的算法 (FR-1201 + CON-1203 atomic, r2 fix per design-review F-7)

**Status**: Accepted r2

**Decision**: 三步 transaction (类似 F009 manifest atomic write):
1. **Plan phase** (read-only): 从 `host-installer.json files[]` 过滤 `pack_id == <pack-id>` 的所有 entry, 列出每个 entry 的 `dst` 文件 + 反向推导 sidecar 子目录 (`references/ assets/ evals/ scripts/` 在 `dst.parent` 下) + 空的 host 父目录候选
2. **Confirm phase** (interactive 或 dry-run): 显示 plan 详情, prompt or print
3. **Execute phase** (commit): 按 plan 删文件 → 删 sidecar → 删空 host 父目录 → 删 `packs/<pack-id>/` → 重写 host-installer.json (drop entries + drop installed_packs[])
4. 任一步骤失败 → 回滚 (磁盘备份在 temp dir, 失败时 swap 回; manifest 备份在内存, 失败时不写回)

**Touch boundary** (r2 F-7 fix, CON-1205 + HYP-1206 + INV-F12-9 显式 guard):
- 本 transaction 只触碰:
  - `<workspace>/packs/<pack-id>/` (本 pack 整树)
  - `<workspace>/.garage/config/host-installer.json` (drop entries + installed_packs[])
  - 各 host 目录映射文件 (按 `host-installer.json files[]` 反向枚举, 不展开模糊 glob)
- **不读不写**:
  - `.garage/config/sync-manifest.json` (F010 sync, CON-1205)
  - `.garage/knowledge/**` (F003-F006 KnowledgeStore, 含 STYLE 维度)
  - `.garage/experience/**` (F003 ExperienceIndex)
  - `.garage/sessions/**` (F010 ingest archived sessions)
  - `.garage/contracts/**` / `.garage/config/platform.json` / `host-adapter.json` (F001 platform contracts)

**Consequences**:
- (+) atomic: 无半完成状态
- (+) dry-run 复用 plan phase, 不进 execute
- (+) 显式 touch boundary 让 implementer 不滑出 (F-7 fix; CON-1205 + HYP-1206 + INV-F12-9 三层守门)
- (-) 备份 packs/<pack-id>/ 到 temp dir 增加 IO; 但与 update 一致 + 安全优先

### ADR-D12-3: update 算法 — 复用 install 内部 helper (r2 fix per design-review F-2 + F-5)

**Status**: Accepted r2

**Decision**: `update_pack` 内部:
1. read `packs/<pack-id>/pack.json.source_url`
2. shallow clone 到 temp dir. **抽出 helper 为 `@contextmanager` 形式** (F-2 fix: `Path` 返回值与 `tempfile.TemporaryDirectory` 寿命冲突):
   ```python
   @contextlib.contextmanager
   def _clone_pack_to_tempdir(git_url: str) -> Iterator[Path]:
       """Shallow-clone a pack URL to a temp dir, yield clone path, auto-cleanup on exit."""
       with tempfile.TemporaryDirectory(prefix="garage-pack-clone-") as tmpdir:
           clone_dst = Path(tmpdir) / "clone"
           subprocess.run(["git", "clone", "--depth=1", git_url, str(clone_dst)],
                          check=True, capture_output=True, text=True)
           yield clone_dst
   ```
   调用方:
   ```python
   with _clone_pack_to_tempdir(source_url) as clone_dst:
       new_pack_json = json.loads((clone_dst / "pack.json").read_text())
       # ... compare + replace
   ```
3. 比对 version (read both pack.json)
4. 同 → no-op + stdout "Already up to date"
5. 不同 → prompt or yes → 备份当前 `packs/<pack-id>/` 到 temp → 替换 → **调 F007 既有 `install_packs` 反向同步 host 目录** (F-5 fix: 真实签名 + force=True):
   ```python
   from garage_os.adapter.installer.pipeline import install_packs
   from garage_os.adapter.installer.manifest import read_manifest
   
   prior = read_manifest(workspace_root / ".garage")
   already_installed_hosts = list(prior.installed_hosts) if prior else []
   already_installed_scopes = {entry.host: entry.scope for entry in (prior.files if prior else [])}
   
   install_packs(
       workspace_root,
       packs_root=workspace_root / "packs",       # F-5 fix: required positional
       hosts=already_installed_hosts,
       force=True,                                 # F-5 fix: 必须覆盖既有 host 文件
       scopes_per_host=already_installed_scopes,   # 保持 F009 per-host scope
   )
   ```
   - **`force=True`**: update 必须覆盖之前 install 时写入的 host 文件; 否则会撞 F007 SKIP_LOCALLY_MODIFIED 路径 (因为 host 文件已存在), update 后 host 字节级老旧, FR-1204 acceptance 不满足
6. 失败时 swap 回备份 (atomic 同 ADR-D12-2)

**Consequences**:
- (+) 复用 F011 install_pack_from_url 内部 git clone 逻辑 (重构为 contextmanager helper)
- (+) 复用 F007 install_packs 的 host 目录同步, 自动走既有 sidecar copy (PR #30 F010-E)
- (+) F011 install 函数对外契约 (`install_pack_from_url(workspace_root, git_url, *, stderr) -> PackInstallSummary`) **不变** (仅内部抽出 helper, CON-1202 守门保留 — 仅 F011 内部 refactor, 既有测试 0 退绿)
- (-) update 默认 `force=True` 会绕过 F009 SKIP_LOCALLY_MODIFIED protection — 但语义正确 (用户显式 update 意图); 测试 e2e 校验 host 文件 hash 已更新

### ADR-D12-4: publish 算法 + sensitive scan + git push --force 风险检测

**Status**: Accepted r2 (design-review-r1 F-4 + F-6 + F-8 fix)

**Decision**:
1. **Sensitive scan** (FR-1208 + ADR-D12-1 helper): 用 `sensitive_scan(pack_dir) -> list[SensitiveMatch]`. 实现:
   ```python
   SENSITIVE_RULES = [
       ("password", re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE)),
       ("api_key", re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.IGNORECASE)),
       ("secret", re.compile(r"secret\s*[:=]\s*\S+", re.IGNORECASE)),
       ("token", re.compile(r"token\s*[:=]\s*\S+", re.IGNORECASE)),
       ("private_key", re.compile(r"-----BEGIN (RSA|OPENSSH|PRIVATE) KEY-----")),
   ]
   TEXT_EXTENSIONS = frozenset({".md", ".py", ".txt", ".json", ".yaml", ".yml", ".toml",
                                ".sh", ".js", ".ts", ".ini", ".cfg", ".conf", ".env",
                                ".lock", ".gitignore"})
   ```
   仅扫 ext 在 allowlist 的文件; 其它跳过 + 计入 skipped_count.

2. **Force push 风险检测** (FR-1207 step 3):
   ```python
   result = subprocess.run(["git", "ls-remote", to_url], capture_output=True, text=True)
   remote_has_refs = bool(result.stdout.strip())
   if remote_has_refs and not yes:
       # 显示 remote head + 必须二次 prompt
       print(f"Remote {to_url} has existing refs:\n{result.stdout}\nReally overwrite? [y/N]:")
   ```

3. **Git author 决议** (F-8 fix: 与 spec FR-1207 fallback wording 对齐):
   ```python
   def _resolve_commit_author(commit_author: str | None) -> tuple[str, str]:
       """Returns (name, email). Fallback "Garage <garage-publish@local>" matches spec FR-1207 step 5."""
       if commit_author:
           # parse "Name <email>" format
           ...
       try:
           name = subprocess.run(["git", "config", "user.name"], ...).stdout.strip()
           email = subprocess.run(["git", "config", "user.email"], ...).stdout.strip()
           if name and email: return (name, email)
       except subprocess.CalledProcessError: pass
       return ("Garage", "garage-publish@local")  # rendered as "Garage <garage-publish@local>"
   ```

4. **Publish steps** (FR-1207 step 5, F-6 fix: 显式 default branch):
   ```bash
   git init -b main          # F-6 fix: git ≥ 2.28 显式 initial branch; older fallback: git init && git symbolic-ref HEAD refs/heads/main
   git add .
   git -c user.email=<email> -c user.name=<name> commit -m "<msg>"
   git remote add origin <to-url>
   git push --force origin main
   ```

5. **Flag matrix dispatch** (FR-1207 r2 9 行表代码化, F-4 fix):
   ```python
   def publish_pack(workspace_root, pack_id, to_url, *, yes=False, force=False, dry_run=False, ...):
       # Phase A: sensitive scan
       matches = sensitive_scan(packs_root / pack_id)
       if matches and not force:
           # 默认 / --yes 命中 (--yes 不绕 sensitive)
           print_matches_to_stderr(matches)
           return exit_1
       # --force 命中: 仅绕 sensitive scan, 不绕主 prompt; matches 仍 print summary
       
       # Phase B: remote check
       remote_has_refs = bool(subprocess.run(["git", "ls-remote", to_url], ...).stdout.strip())
       
       # Phase C: 主 prompt (--dry-run 隐含 yes; 主 publish 不 prompt)
       effective_yes = yes or dry_run
       if not effective_yes:
           if remote_has_refs:
               # F-2 fix: 二次确认 force-push 风险
               print(f"WARNING: remote {to_url} has existing refs; force push will OVERWRITE", file=stderr)
           if not prompt_confirm("Continue?"):
               return exit_0
       
       # Phase D: actual publish (or dry-run)
       with tempfile.TemporaryDirectory() as tmpdir:
           # ... git init -b main, add, commit (with resolved author), remote add, push
           if dry_run:
               return exit_0  # don't push
           subprocess.run(["git", "push", "--force", "origin", "main"], cwd=tmpdir, check=True)
       
       # Phase E: writeback source_url (unless --no-update-source-url)
       if not no_update_source_url and not dry_run:
           pack_json["source_url"] = to_url
           write_pack_json(...)
   ```

**Consequences**:
- (+) sensitive scan 模块化, 测试 fixture 5 类敏感词 ↔ 5 类 SENSITIVE_RULES 1:1
- (+) git ls-remote 检测 + 主 prompt 二次确认 force-push 风险, 实施 FR-1207 step 3 (B5 user-pact)
- (+) git author 决议支持 user-pact "你做主" + 配置友好
- (+) 9 行 flag 状态表完全代码化为 dispatch 流; T3 implementer 不需猜
- (+) `git init -b main` 解决旧 git 默认 master 问题 (F-6)

### ADR-D12-5: knowledge export 脱敏 + KnowledgeStore mixed strategy

**Decision** (FR-1211 + Mi-5 fix):
1. **Metadata pass**: `KnowledgeStore.list_entries()` 拿全部 KnowledgeEntry → tarball 内 `manifest.json` (entry id / topic / tags / type / date 索引)
2. **Content pass**: 用 entry id 推 file path `.garage/knowledge/<kind-dir>/<id>.md` → filesystem read raw bytes → split front matter + body → 仅对 body 走脱敏 (front matter 字段 id/topic/tags/date 是 meta 不动) → write tarball 内 `<kind>/<id>.md`
3. **Anonymize rules** (r2 fix per design-review F-3: 加 secret + token, 与 SENSITIVE_RULES 1:1 对齐):
   ```python
   ANONYMIZE_RULES = [
       ("email", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "<REDACTED>"),
       ("password", re.compile(r"(?P<key>password\s*[:=]\s*)\S+", re.IGNORECASE), r"\g<key><REDACTED>"),
       ("api_key", re.compile(r"(?P<key>api[_-]?key\s*[:=]\s*)\S+", re.IGNORECASE), r"\g<key><REDACTED>"),
       ("secret", re.compile(r"(?P<key>secret\s*[:=]\s*)\S+", re.IGNORECASE), r"\g<key><REDACTED>"),     # F-3
       ("token", re.compile(r"(?P<key>token\s*[:=]\s*)\S+", re.IGNORECASE), r"\g<key><REDACTED>"),       # F-3
       ("sha1_hash", re.compile(r"\b[a-f0-9]{40}\b"), "<REDACTED:sha1>"),
       ("private_key", re.compile(r"-----BEGIN (RSA|OPENSSH|PRIVATE) KEY-----.*?-----END \1 KEY-----", re.DOTALL), "-----REDACTED-----"),
   ]
   # 7 类规则 (与 ADR-D12-4 SENSITIVE_RULES 5 类基础 + 2 类专属 anonymize: email + sha1_hash)
   # SM-1204 + INV-F12-7 wording 同步: "5 类基础 (FR-1208 与 anonymize 共享) + 2 类 anonymize 专属 = 7 类全部命中 fixture"
   ```
   `load_user_extra_rules()` 读 `~/.garage/anonymize-patterns.txt` (一行一条 regex, `#` 注释), append 到 ANONYMIZE_RULES.
4. **Output**: `<output>/knowledge-<ISO ts>.tar.gz` (default `~/.garage/exports/`)

**Consequences**:
- (+) Mixed strategy 让 metadata 走 KnowledgeStore (类型安全), body 走 filesystem (字节级保留 markdown 结构)
- (+) ANONYMIZE_RULES 5 类与 SENSITIVE_RULES 5 类 1:1 (FR-1212 + FR-1208 同 schema, 易测)
- (+) tarball 内含 manifest.json 让接收方能 list 内容不必解 tarball

### ADR-D12-6: F009 carry-forward — 注册策略 (r2 fix per design-review F-1)

**Status**: Accepted r2 (design-review-r1 critical F-1 fix)

**Context**: r1 wrote wrapper signature `(data, target_version) -> dict` but real `VersionManager.migrate()` calls `migrator(data)` (single arg, version_manager.py:323), and real `migrate_v1_to_v2(prior_v1: Manifest, workspace_root: Path) -> Manifest` needs workspace_root which wrapper has no access to. r1 wrapper not callable in practice → SM-1205 acceptance (`_MIGRATION_REGISTRY[(1, 2)]` filled) would be 名义满足 but functionally fake (F010 r1 typo recurrence type).

**Decision (r2, scheme C — dict-level equivalent implementation)**:
- 在 `manifest.py` 模块顶部加:
  ```python
  from garage_os.platform.version_manager import register_migration
  
  @register_migration(1, 2)
  def _migrate_v1_to_v2_dict_form(data: dict) -> dict:
      """Dict-level equivalent of migrate_v1_to_v2.
      
      Compatible with VersionManager.migrate() single-arg call convention
      (version_manager.py:323 `migrated = migrator(data)`).
      
      Equivalent semantics with the dataclass-form `migrate_v1_to_v2(Manifest, workspace_root)`:
      both transform schema 1 → 2 by adding `scope: "project"` default to each
      file entry + setting top-level `schema_version = 2`. The dict form does
      NOT touch `dst` field (dataclass form converts dst project-relative → absolute
      using workspace_root, but dict-level migration is workspace-agnostic so dst
      stays as-is — read_manifest fast-path is the canonical absolute-dst conversion;
      dict-level path is for VersionManager.migrate() registry coverage + future
      use cases that don't have workspace_root context).
      """
      out = dict(data)
      out["schema_version"] = 2
      out["files"] = [
          {**f, "scope": f.get("scope", "project")} for f in out.get("files", [])
      ]
      return out
  ```
- 同时改 `VersionManager.SUPPORTED_VERSIONS = [1, 2]` (line 146)
- F009 既有 `read_manifest` 内部分支 (auto-detect schema 1 → migrate) 不动 — 仍走 fast-path (`migrate_v1_to_v2` dataclass form, 含 workspace_root 信息), 是 absolute-dst 的 canonical 路径
- **双源等价测试**: 单元测试同时 (a) 调 `read_manifest` fast-path 拿一个 schema 2 Manifest, (b) 调 `_migrate_v1_to_v2_dict_form(raw_dict)` 拿 dict, 比较二者 `schema_version` + `files[].scope` 默认值 + `installed_hosts/installed_packs/installed_at` 完全一致 (dst 字段差异由 fast-path workspace_root 拼接造成, 测试 ignore dst)

**Consequences**:
- (+) `_MIGRATION_REGISTRY[(1, 2)]` 真实 callable + 通过 `VersionManager.migrate()` 调用约定 (单 arg)
- (+) F009 既有 read_manifest 行为字节级不变 (CON-1202); fast-path 仍是 dst 的权威路径
- (+) 双源等价 schema 字段层验证 (单元测试守门)
- (-) dict-level migration 不动 dst 字段是有意妥协 (workspace_root 只能从外部 inject, 但 VersionManager.migrate() 不传 context); 这是符合 dict-only API 边界的合理 trade-off; ADR docstring + Consequences 显式说明

**Alternatives Considered**:
- 方案 A (wrapper 用 contextvar 注入 workspace_root): 拒, contextvar 增加状态魔法, 调试难
- 方案 B (改 VersionManager.migrate() 加 **kwargs): 拒, 破 CON-1202 (F009 既有 0 改动)
- 方案 C (本 ADR 选): dict-level 等价, scope 简单, 符合 VersionManager API 契约

### ADR-D12-7: 5 子部分串行 commit (T1-T5, r2 加 Depends 列)

**Status**: Accepted r2

**Decision**: 5 sub-commit, 单线递进, P=1..5 唯一无冲突 (与 F010 T1-T7 + F011 T1-T5 同 cycle 结构):

| Task | P | Depends | 描述 |
|---|---|---|---|
| T1 | 1 | — | F012-A uninstall (pack_install + cli + tests) |
| T2 | 2 | **T1's `_clone_pack_to_tempdir` helper** (F-9 fix: 显式依赖) | F012-B update (复用 helper + cli + tests) |
| T3 | 3 | — | F012-C publish + sensitive_scan (pack_install + cli + tests) |
| T4 | 4 | — | F012-D knowledge export --anonymize (新 module + cli + tests) |
| T5 | 5 | — | F012-E F009 carry-forward (manifest + version_manager + tests) + docs sync + finalize |

**Consequences**:
- (+) 每 task 单文件域 + 单测试文件; auto mode 可每 task 独立 verify + commit
- (+) 串行依赖只 1 处 (T2 → T1 helper); T3-T5 互不依赖
- (+) Depends 列让 reviewer 能看到 P 顺序背后的真实依赖 (F-9 fix; auto-mode 调度时不会误以为 T2 可与 T1 并行)

## 3. 测试矩阵

### INV
- INV-F12-1: F011 既有 install + ls 行为字节级不变 (CON-1201; 测既有测试 0 退绿)
- INV-F12-2: F009/F010/F011 baseline 859 → ≥ 859 + 增量 (CON-1202)
- INV-F12-3: uninstall 反向清干净 (HYP-1201 + SM-1201)
- INV-F12-4: update atomic + 滚回 (HYP-1202 + FR-1205)
- INV-F12-5: publish 隐私自检 5 类 (FR-1208 + SM-1204)
- INV-F12-6: publish push to file:// remote 可工作 (HYP-1203 + SM-1203)
- INV-F12-7: anonymize 5 类规则 (HYP-1204 + SM-1204)
- INV-F12-8: VersionManager 注册 (1, 2) (FR-1214 + HYP-1205 + SM-1205)
- INV-F12-9: uninstall 不动 sync-manifest.json (HYP-1206 + CON-1205)

### 测试文件
- `tests/adapter/installer/test_pack_uninstall.py` (T1)
- `tests/adapter/installer/test_pack_update.py` (T2)
- `tests/adapter/installer/test_pack_publish.py` + `test_sensitive_scan.py` (T3)
- `tests/knowledge/test_exporter.py` (T4)
- `tests/adapter/installer/test_manifest_migration_registry.py` (T5)
- `tests/test_cli.py::TestPackUninstallCommand` / `TestPackUpdateCommand` / `TestPackPublishCommand` / `TestKnowledgeExportCommand` (T1-T4)

## 4. Commit 分组 (T1-T5)

按 NFR-904 commit 可审计:

| Task | P | 描述 |
|---|---|---|
| **T1** | 1 | A: uninstall_pack + CLI + tests |
| **T2** | 2 | B: update_pack (refactor _clone_pack_to_tempdir helper) + CLI + tests |
| **T3** | 3 | C: publish_pack + sensitive_scan helper + CLI + tests |
| **T4** | 4 | D: knowledge/exporter.py + CLI + tests |
| **T5** | 5 | E: F009 carry-forward (manifest + version_manager) + docs sync + RELEASE_NOTES + finalize |

## 5. 风险 + 缓解

| 风险 | 严重度 | 缓解 |
|---|---|---|
| HYP-1203 (file:// publish) 在 git 旧版本不工作 | 中 | manual smoke Track 4 实测; failed 时降级 deferred |
| HYP-1204 脱敏召回不足 | 低 | B5 user 自管 ~/.garage/anonymize-patterns.txt; SM-1204 仅追求 5 类 fixture 命中 |
| _migrate_v1_to_v2_for_registry wrapper 与 read_manifest fast-path 双源不一致 | 中 | 单元测试同时调两路径, assert 同结果 |
| update 失败时备份恢复失败 (二次失败) | 中 | tempdir 备份 + atomic swap; 即使二次失败 stderr 显式告知用户手动干预路径 |

## 6. 评审前自检 (供 hf-design-review r2)

- [x] 7 个 ADR 全部含 Status / Context / Decision / Consequences (r2 F-10 fix: ADR-D12-2/3/6/7 显式标 Status: Accepted r2)
- [x] 架构图 (5 子部分模块图)
- [x] 9 个 INV 与 spec FR/NFR/CON 一一对应
- [x] 测试文件按 task 拆 + enum
- [x] 5 sub-commit 分组 (T1-T5) + Depends 列 (r2 F-9)
- [x] 风险表 + 缓解
- [x] 复用 F011 PackInstall pattern + F007 install_packs + F009 manifest migration + F003 KnowledgeStore (CON-1202 守门)
- [x] CON-1207 不修 F010 carry-forward (FR-1214 仅修 F009 carry-forward)
- [x] 真实 API name 锚点持续 (8/8 from spec r2 review)
- [x] **r2 回修结果** (回应 design-review-F012-r1 全部 10 finding):
  - F-1 critical ✓ ADR-D12-6 改 dict-level 等价实现 (`_migrate_v1_to_v2_dict_form(data: dict) -> dict`), 与 VersionManager.migrate() 单 arg 调用约定兼容; read_manifest fast-path 仍保 dst absolute canonical 路径; 双源等价测试 schema 字段层
  - F-2 important ✓ ADR-D12-3 helper 改 `@contextmanager` (`_clone_pack_to_tempdir(url) -> Iterator[Path]`)
  - F-3 important ✓ ADR-D12-5 ANONYMIZE_RULES 加 secret + token (5 → 7 类, 与 SENSITIVE_RULES 1:1)
  - F-4 important ✓ ADR-D12-4 加 publish_pack flag matrix dispatch 伪代码 (Phase A 不绕 sensitive / Phase C --dry-run 隐含 yes / 9 行表全代码化)
  - F-5 important ✓ ADR-D12-3 step 5 加 `install_packs(workspace_root, packs_root=workspace_root/"packs", hosts, force=True, scopes_per_host)` 真实签名
  - F-6 important ✓ ADR-D12-4 publish step 4 加 `git init -b main` 显式 + fallback for older git
  - F-7 important ✓ ADR-D12-2 加 Touch boundary 段, 显式 enum 不读不写: sync-manifest.json / knowledge / experience / sessions / contracts / platform.json / host-adapter.json
  - F-8 minor ✓ ADR-D12-4 git author fallback wording 与 spec FR-1207 step 5 对齐 (`Garage <garage-publish@local>`)
  - F-9 minor ✓ ADR-D12-7 加 Depends 列
  - F-10 nit ✓ ADR-D12-2/3/6/7 加 Status 字段 (D12-1/4/5 仍 implicit, 在 § 0 顶部声明 "所有 ADR 默认 Status: Accepted r1, r2 修订的标 r2")
