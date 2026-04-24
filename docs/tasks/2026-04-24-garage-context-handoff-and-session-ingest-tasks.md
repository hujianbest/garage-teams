# F010 Task Plan: Garage Context Handoff + Host Session Ingest

- 状态: 草稿（待 hf-tasks-review）
- 关联 spec: `docs/features/F010-garage-context-handoff-and-session-ingest.md` (r2 已批准, `docs/approvals/F010-spec-approval.md`)
- 关联 design: `docs/designs/2026-04-24-garage-context-handoff-and-session-ingest-design.md` (r3 已批准, `docs/approvals/F010-design-approval.md`)
- 日期: 2026-04-24
- 测试基线: 715 passed (search hotfix landed)

## 1. 任务总览 (按 design § 5 7 sub-commit)

| Task | 优先级 (P) | 描述 | Acceptance | Test Design Seeds |
|---|---|---|---|---|
| **T1** | 1 | adapter: 三家 host adapter 加 context surface method | FR-1004 + ADR-D10-2 | adapter 单元测试 |
| **T2** | 2 | sync compiler + render | FR-1007 + ADR-D10-4/5 | top-N + budget + markdown / mdc render 测试 |
| **T3** | 3 | sync manifest + pipeline | FR-1001/2/3 + NFR-1002/3 + ADR-D10-3/6 | 幂等 + user content preservation + 三方 hash 决策 |
| **T4** | 4 | sync CLI + status 段 | FR-1001/8/9 + CON-1001 + ADR-D10-12/13 | e2e CLI + status fallback + --force flag |
| **T5** | 5 | ingest readers + selector | ADR-D10-8/10/11 | reader 单元 + interactive / non-TTY + cursor stub |
| **T6** | 6 | ingest pipeline + CLI | FR-1005/6 + CON-1004 + ADR-D10-7/9 | e2e import → archive → candidate; signal-fill |
| **T7** | 7 | docs + 同步 | FR-1010 | AGENTS.md + user-guide + RELEASE_NOTES F010 段 |

## 2. 任务详情

### T1 — adapter: 三家 host adapter 加 context surface method (P=1)

**目标**: `HostInstallAdapter` Protocol 加 `target_context_path(name) -> Path` + `target_context_path_user(name) -> Path`; 三家 first-class adapter 各实现.

**改动文件**:
- `src/garage_os/adapter/installer/host_registry.py`: Protocol 加 2 method 签名
- `src/garage_os/adapter/installer/hosts/claude.py`: 加 2 method 实现 + `name` 参数文档化为 unused
- `src/garage_os/adapter/installer/hosts/cursor.py`: 加 2 method 实现 + `name` 参数用于 `<name>.mdc` 文件名
- `src/garage_os/adapter/installer/hosts/opencode.py`: 加 2 method 实现 + `name` 参数文档化为 unused

**Acceptance**:
- 三家 adapter 实例化 + 调用 `target_context_path("garage-context")` 返回 design ADR-D10-2 表格中的 path
- 三家 adapter 实例化 + 调用 `target_context_path_user("garage-context")` 返回 absolute path under `Path.home()`
- mypy 通过 (Protocol 方法签名 1:1 一致)
- F009 既有 `target_skill_path` / `target_skill_path_user` / `target_agent_path` / `target_agent_path_user` / `render` 5 method 签名严格不变 (CON-1001)

**Verify**:
```bash
.venv/bin/pytest tests/adapter/installer/test_context_path_three_hosts.py -v
.venv/bin/pytest tests/adapter/installer/ -q  # 既有 F007/F009 测试 0 退绿
.venv/bin/mypy src/garage_os/adapter/installer/
```

**Test Design Seeds**:
- `tests/adapter/installer/test_context_path_three_hosts.py`:
  - `TestProjectScope`: 三家 adapter project scope 路径正确
  - `TestUserScope`: 三家 adapter user scope 路径在 fake_home 下 (monkeypatch Path.home())
  - `TestF009MethodsUnchanged`: F009 既有 `target_skill_path_user` 签名 + 返回值不变 (carry-forward sentinel)

### T2 — sync compiler + render (P=2)

**目标**: 实现 `sync/compiler.py` (top-N + budget) + `sync/render/{markdown,mdc}.py` (Garage 段编译产物).

**改动文件**:
- `src/garage_os/sync/__init__.py`: package init + export
- `src/garage_os/sync/compiler.py`: `compile_garage_section(workspace_root) -> CompiledSection` + 常量 (KNOWLEDGE_TOP_N=12, EXPERIENCE_TOP_M=5, SIZE_BUDGET_BYTES=16384)
- `src/garage_os/sync/render/__init__.py`
- `src/garage_os/sync/render/markdown.py`: `render_garage_section(compiled, host) -> str` (4 sections + footer)
- `src/garage_os/sync/render/mdc.py`: `render_mdc_with_front_matter(body) -> str` (cursor `.mdc` 加 alwaysApply: true front matter)

**Acceptance**:
- `compile_garage_section` 复用 `KnowledgeStore.list_entries(type=)` + `ExperienceIndex.list_records()`
- ranking: decision (4) > solution (4) > pattern (4) > experience (5), 同 kind 内按 mtime 倒序
- 编译产物 size ≤ 16384 bytes; 超 budget 时按 ranking 截断 + stderr warn `Truncated N entries due to size budget`
- 单 entry 截到 ≤ 200 char
- 没有 entry 的 kind 段省略 (e.g. 0 patterns → 不输出 `### Recent Patterns` 段)
- footer 含 `_Synced at <ISO> by garage sync (N knowledge + M experience, X B / Y B budget)_`

**Verify**:
```bash
.venv/bin/pytest tests/sync/test_compiler.py tests/sync/test_render_markdown.py tests/sync/test_render_mdc.py -v
```

**Test Design Seeds**:
- `tests/sync/test_compiler.py`:
  - `TestTopN`: 12 + 5 + budget 默认值生效
  - `TestSizeBudgetEnforced` (INV-F10-3): 大库 (50 entries) + 强制 budget=512 → 截断 N 个 entries + stderr warn
  - `TestEmptyKindOmitted`: 0 patterns 时 `### Recent Patterns` 段不出现
  - `TestRanking`: decision > solution > pattern > experience 顺序
- `tests/sync/test_render_markdown.py`:
  - `TestMarkerWrapping`: 输出含 `<!-- garage:context-begin -->` + `<!-- garage:context-end -->`
  - `TestEntryTruncated200Char`: 单 entry > 200 char 被截
  - `TestFooterContent`: footer 含 timestamp + counts + budget
- `tests/sync/test_render_mdc.py`:
  - `TestFrontMatterAlwaysApply`: cursor mdc 含 `alwaysApply: true` YAML front matter
  - `TestMarkdownNoFrontMatter`: claude/opencode 不含 front matter (sentinel 守门)

### T3 — sync manifest + pipeline (P=3)

**目标**: 实现 `sync/manifest.py` (sync-manifest.json schema 1) + `sync/pipeline.py` (写入 + 幂等 + 三方 hash 决策).

**改动文件**:
- `src/garage_os/sync/manifest.py`: `SyncManifest` / `SyncTargetEntry` / `SyncSources` dataclass + `read_sync_manifest()` / `write_sync_manifest()` (与 F007/F009 manifest 函数同模式; 独立 module 避免命名冲突)
- `src/garage_os/sync/pipeline.py`: `sync_hosts(workspace_root, hosts, scopes_per_host, force=False, ...) -> SyncSummary` + 三方 hash 决策 + WriteAction enum (复用 F007 既有)

**Acceptance**:
- `write_sync_manifest()` 始终写 `schema_version=1`; 输出按 spec § 5.1 A4 schema (含 sources + targets[] absolute POSIX path)
- `read_sync_manifest()` 返回 SyncManifest 或 None (文件不存在时); JSON 损坏时抛 ManifestMigrationError 不写文件 (与 F009 CON-904 同精神)
- pipeline 三方 hash 决策 (ADR-D10-3 决策表):
  - disk_marker_hash == prior_synced_hash AND fresh != prior → UPDATE_FROM_SOURCE 覆写
  - disk_marker_hash == prior_synced_hash AND fresh == prior → 跳过 (mtime 不刷新, NFR-1002)
  - disk_marker_hash != prior_synced_hash → SKIP_LOCALLY_MODIFIED + stderr warn (除非 force=True)
- pipeline 默认创建文件 (WRITE_NEW): 写入 host context surface, 文件不存在时新建 + parent dir mkdir
- 用户在 marker 之外手写内容字节级保留 (NFR-1003 + INV-F10-5)

**Verify**:
```bash
.venv/bin/pytest tests/sync/test_manifest.py tests/sync/test_manifest_isolation.py tests/sync/test_pipeline_idempotent.py tests/sync/test_pipeline_user_content_preserved.py tests/sync/test_pipeline_force.py -v
```

**Test Design Seeds**:
- `tests/sync/test_manifest.py`: schema 1 round-trip + 字段完整性
- `tests/sync/test_manifest_isolation.py` (INV-F10-6): sync-manifest.json 与 host-installer.json 完全独立 (写一个不影响另一个)
- `tests/sync/test_pipeline_idempotent.py` (INV-F10-4 + NFR-1002): 第二次 sync 内容相同 → mtime 不刷新
- `tests/sync/test_pipeline_user_content_preserved.py` (INV-F10-5 + NFR-1003): marker 之外用户手写内容 SHA-256 不变
- `tests/sync/test_pipeline_force.py`: SKIP_LOCALLY_MODIFIED 默认行为 + `--force` 强制覆写
- `tests/sync/test_pipeline_three_way_hash.py`: 三方 hash 决策表三种状态 (与 ADR-D10-3 1:1)

### T4 — sync CLI + status 段 (P=4)

**目标**: cli.py 加 `garage sync` 子命令 + `garage status` sync 段 (ADR-D10-12 + ADR-D10-13).

**改动文件**:
- `src/garage_os/cli.py`:
  - imports: + `sync.pipeline.sync_hosts` + `sync.manifest.read_sync_manifest`
  - 加 `sync_parser` subcommand: `--hosts <list>` (复用 F009 解析) + `--scope <project|user>` + `--force` (与 init --force 同精神, ADR-D10-13)
  - 加 `_sync(garage_root, hosts_arg, scope, force)` 函数: 调 `sync_hosts(...)` + 打印 stdout marker (FR-1008)
  - 加 `_print_sync_status(garage_dir, stdout)` helper (ADR-D10-12): early return if sync-manifest.json 不存在 (CON-1001 字节级守门)
  - `_status` 末尾追加 `_print_sync_status(...)` 调用 (在 F009 packs 段之后)

**Acceptance**:
- `garage sync --hosts claude` 干净下游项目 → `<cwd>/CLAUDE.md` 出现 Garage 段 + `.garage/config/sync-manifest.json` 写入 + stdout 含 `Synced N knowledge entries + M experience records into hosts: claude`
- `garage sync --hosts claude --scope user` (HOME=fake_home) → `~/.claude/CLAUDE.md` 装到, cwd 不创建
- `garage sync --hosts claude:user,cursor:project` (per-host override) → claude 走 user, cursor 走 project
- `garage sync --hosts claude --force` 用户改了 marker 段也强制覆写
- `garage status` 加段: sync-manifest 存在 → 含 `Last synced (per host):` 段; 不存在 → status 输出与 F009 baseline 字节级一致 (CON-1001 守门)
- F007/F009 既有 `garage init` 行为字节级不变 (CON-1001)

**Verify**:
```bash
.venv/bin/pytest tests/test_cli.py::TestSyncCommand tests/test_cli.py::TestStatusSyncSegment -v
.venv/bin/pytest tests/ -q  # 715 baseline + T1+T2+T3 增量, 0 退绿
```

**Test Design Seeds**:
- `tests/test_cli.py::TestSyncCommand`: 7 用例
  - `test_sync_hosts_claude_project_default`
  - `test_sync_hosts_claude_scope_user` (fake_home)
  - `test_sync_per_host_override` (claude:user,cursor:project)
  - `test_sync_force_overrides_skip_locally_modified`
  - `test_sync_stdout_marker_grep_compat` (FR-1008 grep `^Synced [0-9]+ knowledge entries \+ [0-9]+ experience records into hosts:`)
  - `test_sync_no_knowledge_no_section` (空 .garage/knowledge/ 时 sync 仍 OK + 段 emit "No Garage knowledge yet" 或 minimal)
  - `test_sync_manifest_migration_error_exit_1` (sync-manifest.json 损坏 → exit 1)
- `tests/test_cli.py::TestStatusSyncSegment`: 3 用例
  - `test_status_no_sync_manifest_no_segment` (CON-1001 fallback)
  - `test_status_with_sync_manifest_shows_segment` (含 `Last synced (per host):` + 各 host 行)
  - `test_status_baseline_no_regression_when_sync_disabled` (与 F009 baseline 字节级一致 sentinel)

### T5 — ingest readers + selector (P=5)

**目标**: 实现 `ingest/host_readers/{claude_code,opencode,cursor}.py` + `ingest/selector.py`.

**改动文件**:
- `src/garage_os/ingest/__init__.py`: package init
- `src/garage_os/ingest/host_readers/__init__.py`: HOST_READERS registry + HOST_ID_ALIASES (ADR-D10-11)
- `src/garage_os/ingest/host_readers/claude_code.py`: `ClaudeCodeHistoryReader`
- `src/garage_os/ingest/host_readers/opencode.py`: `OpenCodeHistoryReader`
- `src/garage_os/ingest/host_readers/cursor.py`: `CursorHistoryReader` stub (ADR-D10-10, NotImplementedError)
- `src/garage_os/ingest/types.py`: `ConversationSummary` + `ConversationContent` dataclass + `HostHistoryReader` Protocol
- `src/garage_os/ingest/selector.py`: `prompt_select(summaries) -> list[str]` (TTY interactive); non-TTY 返回 [] + stderr notice

**Acceptance**:
- `HostHistoryReader` Protocol 含 `host_id: str` + `list_conversations() -> list[ConversationSummary]` + `read_conversation(id) -> ConversationContent`
- claude_code reader 读 `Path.home() / ".claude/conversations/*.json"` (mtime 倒序 ≤ 30); 单文件损坏不阻塞 list (skip + stderr)
- opencode reader 读 `Path.home() / ".local/share/opencode/sessions/*.json"` (XDG default)
- cursor reader 抛 `NotImplementedError("Cursor history reader is deferred to F010 D-1010 per CON-1007. Track upstream: https://cursor.sh/docs/cli")`
- HOST_READERS registry 三家齐全 (cursor 入 registry 但 instantiate 时报 NotImplementedError)
- HOST_ID_ALIASES: `claude` → `claude-code` 别名生效
- selector.prompt_select TTY: 显示 ≤ 30 条对话 (mtime, message_count, topic), 用户输入数字选, 输入 q/Ctrl-C/EOF 返回 []
- selector non-TTY: stderr `non-interactive shell detected; use --all to batch import` + 返回 []

**Verify**:
```bash
.venv/bin/pytest tests/ingest/test_host_readers_registry.py tests/ingest/test_claude_code_reader.py tests/ingest/test_opencode_reader.py tests/ingest/test_cursor_deferred.py tests/ingest/test_selector.py -v
```

**Test Design Seeds**:
- `tests/ingest/test_host_readers_registry.py` (ADR-D10-11 + INV-F10-10):
  - HOST_READERS 含 claude-code/opencode/cursor 三 key
  - HOST_ID_ALIASES claude→claude-code 生效
- `tests/ingest/test_claude_code_reader.py`:
  - 用 fixture `tests/ingest/fixtures/claude_code/<id>.json` 读 conversation
  - mtime 倒序 ≤ 30
  - 单文件损坏 skip + stderr
- `tests/ingest/test_opencode_reader.py`: 同上 (fixture `tests/ingest/fixtures/opencode/<id>.json`)
- `tests/ingest/test_cursor_deferred.py` (ADR-D10-10 + INV-F10-9):
  - `CursorHistoryReader().list_conversations()` 抛 NotImplementedError + msg 含 "deferred"
  - registry 仍含 cursor entry (与 install 三家齐)
- `tests/ingest/test_selector.py`: TTY 模拟 (与 F007 既有 prompt_hosts 测试同 monkeypatch builtins.input 模式)

### T6 — ingest pipeline + CLI (P=6)

**目标**: 实现 `ingest/pipeline.py` (signal-fill + bypass extraction_enabled gate) + cli.py `garage session import`.

**改动文件**:
- `src/garage_os/ingest/pipeline.py`: `import_conversations(workspace_root, host, conversation_ids, *, session_manager, storage, stderr) -> ImportSummary` (按 ADR-D10-9 r2 实施代码)
- `src/garage_os/cli.py`:
  - imports: + ingest 相关
  - 加 `session_parser` subcommand + `import` 子子命令: `--from <host>` (alias 解析) + `--all` 显式 batch
  - 加 `_session_import(garage_root, host, all_flag)` 函数: alias 解析 + reader.list_conversations + selector.prompt_select / --all → import_conversations + 打印 stdout `Imported N conversations from <host> (M skipped, batch-id: <id>)`

**Acceptance**:
- `garage session import --from claude-code` 干净 fixture (`tests/ingest/fixtures/claude_code/<id>.json`) → SessionMetadata 创建 + provenance 在 `SessionContext.metadata.imported_from = "claude-code:<id>"`
- ingest 灌入 metadata.tags + metadata.problem_domain (signal-fill 守门, ADR-D10-7 + ADR-D10-9 r2)
- archive_session() trigger → orchestrator.extract_for_archived_session_id() 主动调 → candidate 入 `.garage/memory/candidates/items/` + batch 入 `.garage/memory/candidates/batches/`
- 单 conversation 损坏 skip + stderr; batch partial success exit 0
- `--from cursor` → exit 1 + stderr `Cursor history import is not yet implemented (deferred to F010 D-1010, see docs).`
- `--from claude` (alias) → 等价 `--from claude-code`
- 不传 `--all` 且 stdin 非 TTY → stderr `non-interactive shell detected; use --all to batch import` + exit 0
- F003-F006 测试 baseline 0 退绿 (CON-1002 + INV-F10-8)

**Verify**:
```bash
.venv/bin/pytest tests/ingest/test_pipeline_candidate_path.py tests/ingest/test_pipeline_partial_failure.py tests/ingest/test_session_provenance_via_metadata.py tests/ingest/test_e2e_import_then_sync.py tests/test_cli.py::TestSessionImportCommand -v
.venv/bin/pytest tests/ -q  # 715 baseline + 全部 T1-T6 增量, 0 退绿
```

**Test Design Seeds**:
- `tests/ingest/test_pipeline_candidate_path.py` (INV-F10-7):
  - import 1 fixture conversation → archive_session 触发 → extract_for_archived_session_id 调用 → candidate items + batch 落盘
  - 验证 candidate JSON 含 signals[] (含 metadata.tags + problem_domain 来源)
- `tests/ingest/test_pipeline_partial_failure.py` (FR-1006 partial):
  - 5 fixture conversations, 1 损坏 → 4 imported + 1 skipped + summary.batch_id 非 None + stderr warn
- `tests/ingest/test_session_provenance_via_metadata.py` (INV-F10-8):
  - SessionContext.metadata.imported_from 字段 = "claude-code:<id>" (ADR-D10-7 验证)
  - F003-F006 既有 SessionMetadata dataclass 字段 0 改动 (carry-forward sentinel: 既有 384 测试不退绿)
- `tests/ingest/test_e2e_import_then_sync.py` (SM-1002 + manual smoke Track 4 等价):
  - import → archive → 自动 candidate → 用户 `garage memory review --action accept` → publisher 入 .garage/knowledge/ → garage sync → host context surface 出现新知识
- `tests/test_cli.py::TestSessionImportCommand`: 6 用例
  - happy path + cursor deferred + claude alias + --all batch + non-TTY 退化 + interactive cancel ('q')

### T7 — docs + 同步 (P=7)

**目标**: AGENTS.md + user-guide + RELEASE_NOTES F010 段 (FR-1010).

**改动文件**:
- `AGENTS.md`: 加 "Memory Sync (F010)" 段 (在 "Packs & Host Installer (F007/F008/F009)" 之后, 与 "本仓库自身 IDE 加载入口" 之前). 内容含:
  - sync + ingest 简介
  - 三家 host context surface 路径表
  - HOST_ID_ALIASES 说明
  - SessionContext.metadata 三个 F010 占用 key (`imported_from` / `tags` / `problem_domain`)
  - 5 min cold-read 链
- `docs/guides/garage-os-user-guide.md`: 加 "Sync & Session Import" 段 (在 "Pack & Host Installer" 之后):
  - `garage sync` 端到端用法 (3 种使用方式)
  - `garage session import` 端到端用法 (interactive + --all)
  - 三家 host context surface 路径表
  - cursor history deferred 说明
  - candidate review 链 (`garage memory review`) 引导
  - 已知限制 + F011+ 候选
- `RELEASE_NOTES.md`: 加 F010 段 (按 F009 同等结构):
  - 状态 / Workflow Profile / Branch / PR
  - 用户可见变化
  - 数据与契约影响 (sync-manifest.json schema 1 + Protocol 加 method + ingest 入口)
  - 验证证据 (5 项 TBD: manual_smoke_wall_clock / pytest_total_count / candidate_count_per_test / commit_count / release_notes_quality_chain)
  - 已知限制 + carry-forward
- `packs/README.md`: **不修改** (FR-1010 第 4 项, F010 不影响 packs)

**Acceptance**:
- 4 grep 通过:
  - `grep 'Memory Sync (F010)' AGENTS.md` ✓
  - `grep 'Sync & Session Import' docs/guides/garage-os-user-guide.md` ✓
  - `grep '^## F010' RELEASE_NOTES.md` ✓
  - `git diff main..HEAD -- packs/README.md` 输出空 (FR-1010 守门)
- 5 项 TBD 占位字段 enum (FR-1010 + spec § 12 自检对齐)
- cold-read 链 5 分钟内可达

**Verify**: 手动 grep + cold-read 自检

## 3. 测试基线守门

| 任务后基线 | 期望 |
|---|---|
| T1 完成 | ≥ 715 + ~5 个 T1 测试 (INV-F10-2 守门) |
| T2 完成 | ≥ 720 + ~10 个 T2 测试 |
| T3 完成 | ≥ 730 + ~12 个 T3 测试 |
| T4 完成 | ≥ 742 + ~10 个 T4 测试 |
| T5 完成 | ≥ 752 + ~10 个 T5 测试 |
| T6 完成 | ≥ 762 + ~12 个 T6 测试 |
| T7 完成 | ≥ 774 (与 T6 一致, T7 不增测试用例) |

NFR-1004 perf: T6 manual smoke wall_clock ≤ 5s (50 entries + 30 conversations)

## 4. Carry-forward 修复 (in-cycle 同步)

T1-T6 实施期间可能触发的既有测试 carry-forward:
- F009 既有 `tests/adapter/installer/test_*.py`: 因 Protocol 加 method, mypy 可能报 incomplete implementation. 修法: F009 既有 mock adapter 同步加 stub method (与 F009 T1 carry-forward 同精神)
- F009 既有 `tests/test_cli.py::TestStatusXxx`: 因 status 加 sync 段, 既有 status 测试若硬编码全文 fixture 需 carry-forward (但应只在 sync-manifest 存在时受影响, CON-1001 fallback 保护无 manifest 路径)

## 5. 提交分组 (NFR-904 commit 可审计)

每个 task 一个 commit, 共 7 commits. commit message 模板:

```
f010(<scope>): <T-id> <one-liner>

T<N> 实施 (按 task plan § 2):
- <改动文件 1>
- <改动文件 2>
- <新增测试文件>

Acceptance 验证:
- <每条 acceptance 一个 ✓>

测试基线: <prior> → <current> passed (+<delta> 增量, 0 退绿)
git diff main..HEAD -- pyproject.toml uv.lock = 0
INV-F10-<x> 守门 ✓

下一步: T<N+1>
```

## 6. 评审前自检 ✅ (供 hf-tasks-review)

- [x] 7 task 与 design § 5 7 sub-commit 1:1 对应
- [x] 每 task 含 Acceptance + Verify + Test Design Seeds
- [x] T1-T6 acceptance 直接锚定 spec FR/NFR/CON + design ADR/INV
- [x] T7 acceptance 锚定 FR-1010 + 4 grep + 5 TBD 占位字段
- [x] 测试基线守门 (§ 3) 与 design INV-F10-2 sentinel 一致
- [x] Carry-forward 修复段 (§ 4) 显式列出潜在 F009 既有测试影响
- [x] 提交分组 (§ 5) 与 NFR-904 一致
- [x] 复用 F007/F009 既有 host adapter pattern + WriteAction enum (T1 + T3)
- [x] CON-1002 守门: F003-F006 既有 dataclass + 算法 0 改动 (T6 ingest 走既有 public API)
- [x] CON-1004 守门: B5 user-pact 显式 (T6 不绕过 candidate review)
- [x] 真实 API name 锚点 (T6: `archive_session(reason=)` + `update_session(context_metadata=)` + `extract_for_archived_session_id`)
