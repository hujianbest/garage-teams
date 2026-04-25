# F012: Pack Lifecycle 完整化 (uninstall + update + publish + 脱敏导出 + F009 carry-forward)

- 状态: 草稿（待 hf-spec-review）
- 主题: F011 落了 `garage pack install <git-url>` + `garage pack ls`，但用户**卸不掉 / 升不了 / 分享不出**, lifecycle 不完整. F012 补齐: `pack uninstall` + `pack update` + `pack publish` + `knowledge export --anonymize` (与 publish 一起) + F009 carry-forward (VersionManager 注册 host-installer migration 链, 反向操作天然要重审 phase 3)
- 日期: 2026-04-25
- 关联:
  - vision-gap planning artifact `docs/planning/2026-04-25-post-pr30-pr32-next-cycle-plan.md` § 2.3 (F012 锁定 5 部分)
  - F011 — `garage pack install` + `pack ls` (本 cycle 的反向 + publish 路径; 复用 `pack_install.install_pack_from_url` + `list_installed_packs` + `PackInstallSummary` 数据结构)
  - F010 — `garage knowledge add` 等已有的 KnowledgeStore CRUD; 本 cycle export-anonymize 新增 read-only 路径
  - F009 — manifest schema 2 + per-host scope; 本 cycle uninstall 必须按 scope/host 精确清, 否则 manifest 与磁盘漂移
  - F009 finalize approval carry-forward "I-2 VersionManager host-installer migration 链未注册" — 本 cycle 修
  - F010 finalize approval carry-forward (code-review MIN-1..6 + traceability MIN-1) — **不在本 cycle**, 留 polish PR
  - manifesto 信念 B5 "可传承" + Stage 4 生态 + user-pact "你做主"
  - 调研锚点:
    - F011 既有 install: `subprocess.run(["git", "clone", "--depth=1", url, dst])` + `shutil.copytree(... ignore=.git)` (`pack_install.py:88-128`)
    - F011 既有 list: `discover_packs(packs_dir)` + read pack.json `source_url` (`pack_install.py:166-180`)
    - F009 manifest: `ManifestFileEntry(src, dst, host, pack_id, content_hash, scope)` (`manifest.py:78-84`); `Manifest.installed_packs` list 字段
    - F010 sidecar copy: `_sync_skill_sidecars(skill_src_dir, skill_dst_dir)` (`pipeline.py:490`) — uninstall 必须反向清 sidecar
    - F009 既有 publisher: `KnowledgePublisher.publish_candidate(candidate_id, action, confirmation_ref)` — 本 cycle 不动, 仅 read 路径加 export
    - VersionManager: `register_migration(from_major, to_major)` (`platform/version_manager.py:117`) + `_MIGRATION_REGISTRY[(from, to)]` (line 114) — F012-E 注册入口

## 1. 背景与问题陈述

F011 cycle 落了一键拉装 (`garage pack install <git-url>`) + 浏览 (`garage pack ls`), B5 可传承从 2/5 → 3.5/5. 但用户实际跑过几个 pack 后立刻撞到三件事:

1. **卸不掉**: `garage pack uninstall` 不存在. 用户只能手动 `rm -rf packs/<pack-id>/`; 而且如果已经跑过 `garage init --hosts ...`, host 目录 (`.claude/skills/<pack>/...` / `.cursor/rules/...` / `.opencode/...`) 里的副本还得手动清; 还得清 `.garage/config/host-installer.json` 里属于该 pack 的 entry — **三件事不联动 = manifest 与磁盘漂移**, 下一次 `garage init` 行为不可预期
2. **升不了**: `garage pack update` 不存在. F011 install 时 `_ignore_git` 跳过 `.git/` (cli.py 实测), 所以 `cd packs/<pack-id> && git pull` 不可能; 用户被迫 `rm -rf packs/<pack-id>/ && garage pack install <same-url>` (但 F011 install 检测到目录存在直接 abort, 顺序得反着来 + 中间状态不安全)
3. **分享不出**: `garage pack publish` 不存在. 用户写好的 pack 想发到 GitHub/GitLab 让别人 install, 只能手动建 git repo + push — 与 install 命令完全不对称
4. **publish 隐含的隐私需求**: 用户的 `packs/garage/skills/` 可能引用了用户私有信息 (公司名 / 内部 URL / 个人 commit hash). 直接 publish = 隐私泄露. 需要配套 `garage knowledge export --anonymize` (虽然 knowledge != pack, 但同一 publish 心智模型下用户会问"那我的知识库怎么分享出去")
5. **F009 finalize 留了 carry-forward**: VersionManager `_MIGRATION_REGISTRY` 应该注册 host-installer.json 的 1→2 migration (与 F001 platform.json / host-adapter.json 同等待遇), F009 finalize approval 标 "I-2 LLM-FIXABLE", F010 finalize 没动. **F012 反向操作 (uninstall/update) 天然要重审 manifest schema 兼容性 + phase 3 conflict detection, 是顺手补的最佳时机**

### 真实摩擦量化

- F011 落地后, 用户在本仓库 dogfood 装的第三方 pack 数: 0 (因为没法卸, 用户不敢装)
- packs/coding 从 v0.2.0 → v0.3.0 (PR #32) 走的是 reverse-sync 手动 commit 而非 `garage pack update` (该路径不存在)
- magazine-web-ppt skill 从 op7418/guizang-ppt-skill 进 packs/writing/ 走的是手 cp + 改 pack.json (PR #30) — 完全没用 F011 install 路径

→ **F012 的核心承诺**: install ↔ uninstall 对称, install ↔ update 对称, install ↔ publish 对称 + 配套脱敏

## 2. 目标与成功标准

### 2.1 范围

A. **`garage pack uninstall <pack-id>`** (FR-1201..1203):
- 删 `packs/<pack-id>/` 整树
- 反向清 host 目录: 对每个曾装入的 host (从 host-installer.json `files[]` 查), 删该 pack 贡献的所有 skill 目录 + agent 文件 + sidecar 子目录 (references/ assets/ evals/ scripts/)
- 同步更新 `.garage/config/host-installer.json` `installed_packs[]` + `files[]` (drop 该 pack 的所有 entry); manifest 行级 atomic write
- `--dry-run` flag (干跑, 仅打印将删的文件清单, 不实际操作)
- B5 user-pact 守门: 默认要求确认 (TTY interactive `[y/N]`); `--yes` 显式 opt-in 无需确认

B. **`garage pack update <pack-id>`** (FR-1204..1206):
- 从 pack.json `source_url` 重新 shallow clone 到 temp dir
- 比对版本号: 若新 version 与本地一致 → no-op + stdout marker; 若不同 → 提示 + 用户确认 → 替换 packs/<pack-id>/ + 重跑 `garage init --hosts <已装 host>` 反向自动同步 host 目录
- 用户的 pack.json 里手改的字段 (e.g. local note) 默认覆盖; `--preserve-local-edits` flag 走 3-way merge stub (本 cycle 仅警告, 不真实 merge)
- 失败时 (clone failed / version 解析失败 / 验证失败) 滚回原 packs/<pack-id>/

C. **`garage pack publish <pack-id> --to <git-url>`** (FR-1207..1210):
- 从 `packs/<pack-id>/` 创建临时 git repo + initial commit + push 到 `--to <git-url>` (用户先在 GitHub/GitLab 创好空 repo)
- 默认 commit message `Publish <pack-id> v<version> from Garage`
- pack.json `source_url` 字段 update 为 `--to <git-url>` (push 成功后写回; 用户下次 `garage pack ls` 即看到 source 切到 publish 后的 URL)
- 隐私自检: publish 前扫 packs/<pack-id>/ 文件, 若命中常见敏感词 (e.g. `password=` / `api_key` / `BEGIN RSA PRIVATE KEY` / 用户名相关 path 段) → stderr warn + 默认中止 (`--force` 显式 opt-in)
- `--dry-run` flag (仅创建 temp git repo, 不真实 push)

D. **`garage knowledge export --anonymize`** (FR-1211..1213):
- 把 `.garage/knowledge/{decisions,patterns,solutions,style}/*.md` 里的内容**脱敏**导出到 `<workspace>/exports/knowledge-<timestamp>.tar.gz`
- 脱敏规则: 替换公司名 / email / 常见私密 token (regex 列表硬编码 + user 可加 `~/.garage/anonymize-patterns.txt` extra rules); 知识 entry `id` / `topic` / `tags` 保留; `content` 走脱敏
- `--dry-run` flag (打印将脱敏的 entry 数 + 命中规则数, 不写文件)
- B5 user-pact 守门: 显式 opt-in (用户主动跑 `--anonymize`); 不自动跑

E. **F012-E (Should)** F009 carry-forward — VersionManager 注册 host-installer migration 链 (FR-1214):
- `manifest.py` 模块加载时注册 `@register_migration(1, 2)` 包装既有 `migrate_v1_to_v2` 函数
- 不破坏 F009 既有 read_manifest 自动 detect + migrate 行为 (保持 fast-path)
- VersionManager.SUPPORTED_VERSIONS 同步加 2

### 2.2 成功标准

1. **F011 既有 install + ls 行为字节级不变 (CON-1201)**: 既有 859 测试 0 退绿; F011 stdout marker 字面不变
2. **F009 既有 init/sync/status/session import 行为字节级不变 (CON-1202)**: F010+F011 既有 859 baseline 全绿
3. **uninstall 端到端可演示**: `garage pack install file:///tmp/test-pack` → `garage init --hosts claude` → `garage pack uninstall test-pack --yes` → `packs/test-pack/` 不存在 + `.claude/skills/<test-pack 的 skills>/` 不存在 + `.garage/config/host-installer.json` 内对应 entry 全清
4. **update 端到端可演示**: 修改远端 pack 版本 → `garage pack update test-pack` 提示版本变化 → 用户确认 → `packs/test-pack/pack.json.version` 更新 + host 目录同步
5. **publish 端到端可演示**: 在干净 file:// remote 上 `garage pack publish my-pack --to file:///tmp/remote-bare.git` 后, `git clone file:///tmp/remote-bare.git /tmp/clone-back` 能拿到完整 pack 内容
6. **publish 隐私自检可演示**: `packs/<pack>/` 含 `password=...` 文件时, 默认 publish abort + stderr warn; `--force` 强制 publish
7. **knowledge export --anonymize 可演示**: `.garage/knowledge/decisions/foo.md` 含 `email: alice@bigco.com` → export 后 tarball 内对应 entry 该字段被替换为 `email: <REDACTED>`
8. **VersionManager F012-E 注册可演示**: `from garage_os.adapter.installer.manifest import _ ; from garage_os.platform.version_manager import _MIGRATION_REGISTRY` 后, `(1, 2)` key 在注册表中 (与 F001 platform.json 同精神)
9. **测试基线**: 859 → ≥ 859 + 增量, 0 退绿
10. **NFR-1204 (CLI safety)**: uninstall + publish 默认 prompt 确认, 错误时滚回; 无 force flag 时不破坏现状
11. **manual smoke 6 tracks 全绿**: install (F011 既有 verify) + uninstall + update + publish + publish-with-anonymize + dogfood not affected

### 2.3 与既有 cycle 的边界

- **F011 既有**: `install_pack_from_url` + `list_installed_packs` + `PackInstallSummary` 数据结构 + `PackInstallError` exception type — 全部直接复用, F012 加 `uninstall_pack(workspace_root, pack_id)` + `update_pack(workspace_root, pack_id)` + `publish_pack(workspace_root, pack_id, to_url)` 三个并列 function 在同一 module
- **F010 sync**: 完全不动. F012-A uninstall 不影响 sync-manifest.json (pack 与 sync context 解耦); 删 pack 后下次 sync 时 compiler 自然不见该 pack 的 STYLE/decision entries (因为 knowledge entries 是用户独立的, 不是 pack 的; 事实上 pack 不贡献 knowledge entries)
- **F009 init**: 完全不动. F012-A uninstall 复用 host-installer.json 已有 schema 2 (含 scope/host/pack_id), 不需要 schema 升级
- **F003-F006 KnowledgeStore + ExperienceIndex**: F012-D `knowledge export --anonymize` 是 read-only 路径 (调 `KnowledgeStore.list_entries` + 脱敏 in memory + tarball 输出), 0 改动 F003-F006 内核

## 3. Success Metrics

| Metric ID | Outcome | Threshold | Measurement | Non-goal |
|---|---|---|---|---|
| **SM-1201** | pack lifecycle install ↔ uninstall 对称 | install + init → uninstall 后 packs/ + host 目录 + manifest 三处全清 | manual smoke Track 2 + 自动 e2e test | 不衡量删除速度 |
| **SM-1202** | pack lifecycle install ↔ update 对称 | update 比对版本 + 替换 + 重新 init 同步 host | manual smoke Track 3 + 自动 e2e test | 不衡量 git pull 网络 |
| **SM-1203** | pack lifecycle install ↔ publish 对称 | publish 后远端 git clone 能拿回完整 pack | manual smoke Track 4 (file:// remote) | 不衡量真 GitHub push (留给用户实测) |
| **SM-1204** | publish 隐私自检守门 | sensitive token 命中时默认 abort | TestPublishSensitive (regex 库覆盖率 ≥ 5 类) | 不追求 100% 召回 (用户自管 + B5) |
| **SM-1205** | F009 carry-forward 闭环 | `_MIGRATION_REGISTRY[(1, 2)]` 含 host-installer migration | 单元测试 import-time 验证 | - |
| **SM-1206** | 0 regression | 859 → ≥ 859 + 增量 | pytest | - |

**Non-goal Metrics**:
- 不追求 publish 自动 GitHub auth (用户自管 git credentials)
- 不追求 update 真实 3-way merge (`--preserve-local-edits` 仅 stub + warn)
- 不追求脱敏规则 100% 召回 (regex + 用户 extra rules 兜底, B5 "你做主")

## 4. Key Hypotheses

| HYP ID | Statement | Type | Confidence | Validation | Blocking? |
|---|---|---|---|---|---|
| **HYP-1201** | uninstall 通过 `host-installer.json files[]` 查到该 pack 的所有 entry → 反向删 host 目录 + sidecar 不会误删别 pack 文件 | F | High | 自动 e2e test (TestUninstallE2E) + manual smoke Track 2 | Yes |
| **HYP-1202** | update 通过 source_url 重新 clone 行为可复用 F011 install 内部步骤 (subprocess git + 验证 + 替换) | F | High | 复用 F011 install_pack_from_url 内部 helper | Yes |
| **HYP-1203** | publish push to file:// bare git URL 可工作 (用 `git init --bare` 创 remote, `git push --set-upstream`) | F | High | manual smoke Track 4 + 单元测试 (subprocess git push file://) | Yes |
| **HYP-1204** | 脱敏 regex 列表对常见敏感词 (email / password / api_key / token / RSA private key) 召回率 ≥ 80% | V | Medium | TestAnonymize 5 类敏感词 fixture + 命中率统计 | No (用户兜底) |
| **HYP-1205** | F009 既有 read_manifest 自动 migrate 与 VersionManager.register_migration(1, 2) 协调可行 (二者都 write 1 → 2 但语义一致) | F | High | 单元测试 import 双源一致性 | Yes |
| **HYP-1206** | uninstall 不影响 F010 sync-manifest.json (pack 与 sync 是独立 namespace) | F | High | 自动 e2e (uninstall 后 sync-manifest unchanged) | Yes |

> **Blocking 规则**: HYP-1201..1203 + HYP-1205/1206 manual smoke 必须验证. HYP-1204 (脱敏召回率) 不卡 cycle 通过 (B5 "你做主" 兜底).

## 5. 范围内 / 外 / Deferred

### 5.1 范围内 (Must)

- F012-A `garage pack uninstall <pack-id>` (5 sub-FR)
- F012-B `garage pack update <pack-id>` (3 sub-FR)
- F012-C `garage pack publish <pack-id> --to <git-url>` (4 sub-FR, 含 sensitive scan)
- F012-D `garage knowledge export --anonymize` (3 sub-FR)
- F012-E F009 carry-forward (1 FR, Should)

### 5.2 范围外

- 不做 GitHub OAuth 自动认证 (用户自管 git credentials)
- 不做真实 3-way merge (--preserve-local-edits 仅 warn)
- 不做 pack signature / 安全审核 (F011 D-3, deferred to F013+ when 第三方 pack 流入足够多)
- 不做 monorepo (多 pack from 同 URL) (F011 D-2)
- 不做 pack info / pack search (planning § 2.2 add candidates, deferred)
- 不做 F010 code-review carry-forward MIN-1..6 (留 polish PR)
- 不做 HOST_REGISTRY plugin / sync watch / Memory push (4-24 P2 三项)

### 5.3 Deferred Backlog (F013+)

- D-1210: GitHub OAuth + GitLab token auto-detect
- D-1211: 真实 3-way merge for `pack update --preserve-local-edits`
- D-1212: pack signature (F011 D-3)
- D-1213: monorepo (F011 D-2)
- D-1214: pack info / pack search (planning § 2.2 add candidates)
- D-1215: knowledge export 反向 import (--unanonymize / restore from tarball)
- D-1216: publish 时自动跑 hf-doc-freshness-gate skill (PR #32 提供 evaluator pattern)

## 6. 功能需求 (FR)

### FR-1201 — `garage pack uninstall <pack-id>` 命令

- 优先级: Must
- 来源: § 1 + SM-1201
- Statement (EARS, Event-driven): When 用户执行 `garage pack uninstall <pack-id>` (默认 interactive prompt; `--yes` 跳过 prompt; `--dry-run` 仅 print), the system SHALL:
  1. 验证 `packs/<pack-id>/` 存在 (否则 stderr exit 1 with "Pack not installed")
  2. 从 `.garage/config/host-installer.json` `files[]` 查该 pack 贡献的所有 entry (按 `pack_id` field 过滤)
  3. 反向删 host 目录: 每个 entry 的 `dst` 文件 + skill 父目录 (含 sidecar references/ assets/ evals/ scripts/) + 空的 host 父目录
  4. 删 `packs/<pack-id>/` 整树
  5. 更新 host-installer.json: drop 该 pack 的所有 entry; 同步 `installed_packs[]` (drop pack_id); atomic write
- Acceptance (BDD):
  ```
  Given packs/test-pack 已装 + garage init --hosts claude 后 .claude/skills/<...>/ + .garage/config/host-installer.json 含 entry
  When 用户跑 garage pack uninstall test-pack --yes
  Then packs/test-pack/ 不存在
  And .claude/skills/<test-pack 的 skills>/ 都不存在
  And .claude/agents/<test-pack 的 agents>.md 都不存在 (如有)
  And host-installer.json files[] 不再含 pack_id == "test-pack" 的 entry
  And host-installer.json installed_packs[] 不再含 "test-pack"
  And exit code = 0 + stdout "Uninstalled pack 'test-pack' from N hosts"
  ```

### FR-1202 — uninstall TTY interactive 确认

- 优先级: Must (B5 user-pact)
- Statement (Event-driven): When 用户跑 `garage pack uninstall <pack-id>` 不带 `--yes`, the system SHALL print 影响摘要 (将删的文件数 + 受影响 host) + prompt `[y/N]`; 用户输入非 y/Y 时 abort exit 0 + 不改任何文件
- Acceptance:
  ```
  Given pack 已装 + TTY stdin
  When 用户跑 garage pack uninstall test-pack (无 --yes)
  Then stdout 列出 "Will remove: N files from M hosts. Continue? [y/N]:"
  And 用户输入 'n' / 回车 / EOF → exit 0 + 文件未变
  And 用户输入 'y' → 走 FR-1201 流程
  ```

### FR-1203 — uninstall `--dry-run` 干跑

- 优先级: Must
- Statement: When 用户加 `--dry-run`, the system SHALL print 完整将删清单 (per-file path) + exit 0 + 不改任何文件
- Acceptance:
  ```
  Given pack 已装
  When 用户跑 garage pack uninstall test-pack --dry-run
  Then stdout 含 "DRY RUN" prefix + per-line "would remove <path>" 列表
  And packs/test-pack/ 仍存在 + host 目录仍含 SKILL.md
  And exit code = 0
  ```

### FR-1204 — `garage pack update <pack-id>` 命令

- 优先级: Must
- 来源: § 1 + SM-1202
- Statement (Event-driven): When 用户跑 `garage pack update <pack-id>`, the system SHALL:
  1. 读 `packs/<pack-id>/pack.json` 拿 `source_url` (无 source_url → exit 1 with "Pack has no source_url; was it installed via 'pack install'?")
  2. shallow clone 到 temp dir (复用 F011 install pattern)
  3. 比对 version: 若 remote == local → stdout "Already up to date" + exit 0
  4. 若不同, default interactive prompt 显示 old → new + diff 提示 + `[y/N]` (与 FR-1202 同精神; `--yes` 跳过)
  5. 替换 `packs/<pack-id>/` 内容 (atomic: temp dir → 备份 → swap → 删备份)
  6. 重跑 `install_packs(workspace_root, packs_root, hosts=已装 host list)` 反向同步 host 目录 (host-installer.json 自动 update entries; F009 manifest 既有逻辑承接)
- Acceptance:
  ```
  Given packs/test-pack v0.1.0 已装 + remote source_url 现 v0.2.0
  When 用户跑 garage pack update test-pack --yes
  Then packs/test-pack/pack.json.version == "0.2.0"
  And host 目录的 SKILL.md 已重新装 (manifest content_hash 更新)
  And stdout "Updated pack 'test-pack' from v0.1.0 to v0.2.0"
  And exit code = 0
  ```

### FR-1205 — update 失败滚回

- 优先级: Must
- Statement: When `pack update` 任一步骤失败 (clone failed / version 解析失败 / 验证失败 / 替换失败), the system SHALL 回滚 `packs/<pack-id>/` 到原版本 + stderr 报错 + exit 1; host-installer.json 不被改
- Acceptance:
  ```
  Given pack 已装 + source_url 临时变成 invalid
  When 用户跑 garage pack update test-pack
  Then packs/test-pack/ 字节级与 update 前一致
  And exit code = 1
  And stderr 含 "Update failed, rolled back to v<old>"
  ```

### FR-1206 — update `--preserve-local-edits` (本 cycle 仅 warn)

- 优先级: Must
- Statement: When 用户加 `--preserve-local-edits` 且本地 pack 有未推送的本地 commit / 改动, the system SHALL stderr warn "Local edits detected; proceeding with overwrite (true 3-way merge deferred to F013 D-1211)" + 仍按 FR-1204 流程; 不实际做 3-way merge
- Acceptance: 检测靠 simple file content compare (clone 后比 packs/<pack-id>/pack.json 与 cloned pack.json 是否相同, 不相同 = 本地有改动); warn 后仍 overwrite

### FR-1207 — `garage pack publish <pack-id> --to <git-url>` 命令

- 优先级: Must
- 来源: § 1 + SM-1203
- Statement (Event-driven): When 用户跑 `garage pack publish <pack-id> --to <git-url>` (`--dry-run` 仅 build temp git不 push; `--force` 跳过 sensitive 检查; `--yes` 跳过 prompt), the system SHALL:
  1. 验证 `packs/<pack-id>/` 存在
  2. 跑 sensitive scan (FR-1208); 命中且无 `--force` → abort exit 1
  3. interactive prompt 显示 "Will publish <pack-id> v<version> to <to-url>. Continue? [y/N]:" (无 `--yes` 时); 用户取消 → exit 0
  4. 创 temp git repo: `git init` + `git add .` + `git -c user.email=garage-publish@local -c user.name=Garage commit -m "Publish <pack-id> v<version> from Garage"` + `git remote add origin <to-url>` + `git push --force origin main` (用 --force 因初始 publish 通常空 remote; 后续 publish 改用普通 push)
  5. 写回 `packs/<pack-id>/pack.json.source_url = <to-url>` (push 成功后)
- Acceptance:
  ```
  Given packs/my-pack v0.1.0 已装 (无 sensitive)
  When 用户跑 garage pack publish my-pack --to file:///tmp/remote-bare.git --yes
  Then file:///tmp/remote-bare.git 内可被 git clone
  And clone 后内容含 packs/my-pack/ 全部文件 (除 .git/)
  And packs/my-pack/pack.json.source_url == "file:///tmp/remote-bare.git"
  And stdout "Published pack 'my-pack' v0.1.0 to file:///tmp/remote-bare.git"
  And exit code = 0
  ```

### FR-1208 — publish 隐私自检 (sensitive scan)

- 优先级: Must
- 来源: § 2.2 #6 + SM-1204
- Statement (Ubiquitous): The system SHALL 在 `pack publish` 默认行为下扫 `packs/<pack-id>/**/*` 文件文本内容; 若命中以下任一 regex → abort exit 1 + stderr 列出命中文件 + 行号 + 命中规则名:
  - `password\s*[:=]\s*\S+`
  - `api[_-]?key\s*[:=]\s*\S+`
  - `secret\s*[:=]\s*\S+`
  - `token\s*[:=]\s*\S+` (case-insensitive)
  - `-----BEGIN (RSA|OPENSSH|PRIVATE KEY)-----`
- 用户加 `--force` 跳过本检查 (B5 "你做主" 兜底)
- Acceptance:
  ```
  Given packs/my-pack/ 内含文件 secret.txt 含 "password=abc123"
  When 用户跑 garage pack publish my-pack --to <url> --yes
  Then stderr 含 "Sensitive content detected: secret.txt:1 (password regex)"
  And exit code = 1
  And remote 未被 push

  When 用户加 --force
  Then 仍正常 publish (B5 用户决策)
  ```

### FR-1209 — publish `--dry-run`

- 优先级: Must
- Statement: With `--dry-run`, the system SHALL 创 temp git repo + 跑 sensitive scan + 显示 git log 但**不** push to remote + 不改 source_url
- Acceptance: 测试 verify temp dir 创建后被清 + remote 不存在新 commit

### FR-1210 — publish stdout marker

- 优先级: Should
- Statement: stdout 含 `Published pack '<pack-id>' v<version> to <url>` 单行 marker (与 F011 install marker family 一致, grep-friendly)

### FR-1211 — `garage knowledge export --anonymize` 命令

- 优先级: Must
- 来源: § 1 + SM-1204
- Statement (Event-driven): When 用户跑 `garage knowledge export --anonymize [--output <path>] [--dry-run]`, the system SHALL:
  1. 读 `.garage/knowledge/{decisions, patterns, solutions, style}/*.md`, 拿全部 KnowledgeEntry
  2. 对每个 entry 走脱敏规则 (FR-1212), 替换敏感词为 `<REDACTED>`
  3. tarball 输出到 `<output>/knowledge-<ISO timestamp>.tar.gz` (default `<workspace>/exports/`)
  4. `--dry-run` 时仅 print 命中规则统计 + entry count
- Acceptance:
  ```
  Given .garage/knowledge/decisions/foo.md 含 "Discussed with alice@bigco.com" + "use api_key=xyz"
  When 用户跑 garage knowledge export --anonymize --output /tmp/export
  Then /tmp/export/knowledge-<ts>.tar.gz 存在
  And tarball 解压后 foo.md 含 "Discussed with <REDACTED>" + "use api_key=<REDACTED>"
  And entry id / topic / tags 字段未被改
  And exit code = 0 + stdout "Exported N entries (M sensitive matches redacted)"
  ```

### FR-1212 — 脱敏规则集 (regex 列表)

- 优先级: Must
- Statement (Ubiquitous): The system SHALL 默认走以下 regex 替换:
  - email: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` → `<REDACTED>`
  - password / api_key / secret / token (同 FR-1208 模式)
  - SHA-1 commit hash: `\b[a-f0-9]{40}\b` → `<REDACTED:sha1>`
  - `-----BEGIN ... PRIVATE KEY-----` 整段 (multiline)
- 用户可在 `~/.garage/anonymize-patterns.txt` 加 extra regex (一行一条; 缺失 OK; 注释行 `#` 开头)
- Acceptance: TestAnonymizeRules 5 类 fixture (email / password / sha1 / privkey / user 自定义) 全部命中

### FR-1213 — knowledge export `--dry-run`

- 优先级: Should
- 同 FR-1209 精神, 仅 print 统计不写 tarball

### FR-1214 — F009 carry-forward: VersionManager 注册 host-installer migration

- 优先级: Should
- 来源: F009 finalize approval I-2 carry-forward
- Statement (Ubiquitous): The system SHALL 在 `manifest.py` 模块加载时通过 `@register_migration(1, 2)` decorator 把既有 `migrate_v1_to_v2` 函数注册到 `_MIGRATION_REGISTRY`; F009 既有 `read_manifest` fast-path 不动 (双源一致, 二者都 write 1 → 2)
- Acceptance:
  ```
  Given F012 实施完成
  When import garage_os.adapter.installer.manifest + garage_os.platform.version_manager
  Then _MIGRATION_REGISTRY[(1, 2)] 不为空且指向 manifest.migrate_v1_to_v2 (或等价 wrapper)
  And F009 既有 718+ manifest 测试 0 退绿 (双源一致守门)
  ```

## 7. 非功能需求 (NFR)

### NFR-1201 — F011 既有 install + ls 字节级不变

- 优先级: Must
- 质量维度 (ISO 25010): Compatibility + Reliability
- QAS:
  - Stimulus: F012 实施完成的 cycle commit
  - Stimulus Source: F011 既有 `garage pack install` / `garage pack ls` 调用
  - Environment: 任意干净 workspace
  - Response: stdout / stderr / exit code / packs 物化 / pack.json source_url 写入 行为字节级与 F011 baseline 一致
  - Response Measure: 既有 11 F011 测试 100% 通过
- Acceptance: pytest 既有 tests/adapter/installer/test_pack_install.py + tests/test_cli.py::TestPackInstallCommand + TestPackLsCommand 全绿

### NFR-1202 — F009 init / F010 sync+ingest / F011 install 行为字节级不变

- 优先级: Must
- QAS:
  - Stimulus: F012 实施
  - Response: 既有 859 baseline 0 退绿
  - Response Measure: pytest tests/ -q 全绿; CON-1001 (F010) + CON-901 (F009) 沿用精神
- Acceptance: 全套测试

### NFR-1203 — uninstall + update + publish 性能 ≤ 5s typical

- 优先级: Should
- 与 F009/F010/F011 perf budget 一致

### NFR-1204 — uninstall + publish 默认 prompt 确认 (CLI safety)

- 优先级: Must
- QAS:
  - Stimulus: 用户跑 uninstall / publish 不带 --yes
  - Response: TTY interactive prompt 显示 + 等输入 + 用户拒绝时不改任何文件
  - Response Measure: TestUninstallNeedConfirm + TestPublishNeedConfirm pass
- Acceptance: 已在 FR-1202 + FR-1207 spec 出

## 8. 约束 (CON)

### CON-1201 — F011 既有 install + ls 字节级兼容
- 沿用 F011 CON-1101 精神; F012 仅 add 子命令 (uninstall/update/publish/info-eq)

### CON-1202 — F003-F006 + F009 + F010 + F011 既有内核 0 改动
- F012-D `knowledge export --anonymize` 是 read-only (调既有 KnowledgeStore.list_entries 等 public API)
- F012-A uninstall 走既有 host-installer.json schema 2 + sidecar copy (F010 PR #30) 既有 helper

### CON-1203 — uninstall 必须保证 manifest ↔ 磁盘一致
- 任一步骤失败 → 滚回到 uninstall 前状态 (磁盘 + manifest); 不允许半完成

### CON-1204 — publish 默认 sensitive scan; --force opt-in
- 与 user-pact "你做主" + "透明可审计" 同精神; 用户必须 explicit acknowledge 风险

### CON-1205 — pack uninstall 不影响 F010 sync-manifest.json
- pack 与 sync context 解耦; uninstall 不动 .garage/config/sync-manifest.json

### CON-1206 — F012 不引入新依赖
- 沿用 F011 CON-1104; subprocess git + shutil + json + tarfile 都是 stdlib; 0 新 pyproject.toml 改动

### CON-1207 — F012 不修 F010 carry-forward (留 polish PR)
- F010 finalize approval 列出的 code-review MIN-1..6 + traceability MIN-1 不在本 cycle 范围

## 9. 假设 (ASM)

- ASM-1201: 用户机器有 git (与 F011 ASM-1101 同)
- ASM-1202: pack.json `source_url` 字段在 install 时正确写入 (F011 FR-1108 提供); uninstall 不依赖 source_url, update + publish 依赖 source_url 存在
- ASM-1203: 用户提供的 publish `--to <git-url>` 是空的或者 fast-forward 兼容的; publish 的初始 push 用 `--force` 处理空 remote, 后续 update push 走普通 push
- ASM-1204: 脱敏 regex 列表对常见敏感词召回 ≥ 80% (HYP-1204); 用户自管补充

## 10. INVEST + Phase 0 自检

- [x] 14 FR 全部 ID + Priority + Source + EARS + BDD
- [x] 4 NFR 全部 ISO 25010 + QAS 五要素 + Response Measure
- [x] 7 CON 全部 ID + Source
- [x] 4 ASM 全部 ID
- [x] 6 HYP 全部 Type + Confidence + Validation + Blocking 标注
- [x] 6 SM 含 Non-goal Metrics
- [x] 范围内 / 外 / Deferred 显式
- [x] FR/NFR INVEST: Independent (5 子部分各自闭环), Negotiable (脱敏 regex 列表可改), Valuable (B5 闭环 + Stage 4 启动), Small (each FR 1-3 文件改动), Testable (BDD)
- [x] 真实 API name 锚点 (避免 F010 r1 critical typo): `install_pack_from_url` / `list_installed_packs` / `PackInstallSummary` / `PackInstallError` (F011 既有) / `KnowledgeStore.list_entries` (F003 既有) / `register_migration(from, to)` + `_MIGRATION_REGISTRY` (`platform/version_manager.py:114, 117`) + `migrate_v1_to_v2` (`manifest.py`)
- [x] 复用 F011 既有 PackInstall API + F009 manifest schema 2 + F010 sidecar copy helper
- [x] B5 user-pact "你做主": uninstall + publish 默认 prompt + --yes opt-in; sensitive scan 默认守门 + --force opt-in; export --anonymize 显式 opt-in
- [x] 不夹带 F013+ 内容 (D-1210..1216 显式 deferred)

## 11. 阻塞性开放问题

### BLK-1201 — uninstall 时 host 目录里的 sidecar (references/ assets/) 是否一并删?
- spec FR-1201 #3 答: **是**, 与 F010 sidecar copy (PR #30) 反向对称; 不删 sidecar 会留垃圾文件
- 不阻塞 spec 通过

### BLK-1202 — update 替换 packs/<pack-id>/ 时怎么 atomic?
- spec FR-1204 #5 给框架 (atomic: temp dir → 备份 → swap → 删备份); 具体实现细节由 design ADR 决定
- 不阻塞 spec 通过

### BLK-1203 — publish 的 git push 用 force 还是 fast-forward?
- spec FR-1207 #4 答: **初始 publish 用 `--force`** (空 remote 通常需要); 后续 update push 用普通 push
- 不阻塞 spec 通过 (design 阶段决定 detect 初始 vs 后续的细节)

### BLK-1204 — knowledge export tarball 是否含 `.garage/experience/`?
- spec FR-1211 答: **不含**, 仅 `.garage/knowledge/`. experience records 含 session_id + 实际 outcome, 脱敏更难; 留 deferred D-1215 (反向 import + experience)
- 不阻塞 spec 通过

## 12. 评审前自检 ✅ (供 hf-spec-review)

- [x] 14 FR 全部锚 spec 行号 + 真实 API name (F011 PackInstall / F009 manifest / F010 sidecar / F003 KnowledgeStore / VersionManager register_migration)
- [x] 4 NFR 全部 ISO 25010 + QAS
- [x] 7 CON 守门 (F011/F010/F009/F003-F006 既有 0 改动 + manifest ↔ 磁盘一致 + sensitive scan default + 零依赖 + 不夹 F010 carry-forward)
- [x] B5 user-pact 显式 (uninstall + publish prompt + sensitive scan + anonymize opt-in)
- [x] HYP-1201..1206 Blocking 5/6 (HYP-1204 脱敏召回 Non-blocking, 用户兜底)
- [x] § 5.3 Deferred backlog 7 项 (D-1210..1216) 显式
- [x] 不夹 F010 carry-forward (CON-1207)
- [x] 不夹 F011 D-2 (monorepo) / D-3 (signature) / 4-24 P2 (HOST_REGISTRY plugin / sync watch / Memory push)
- [x] 复用既有 PackInstallError + 复用 F011 install pattern
- [x] BLK-1201..1204 显式回答 (1=是, 2/3 by design ADR, 4=不含)
