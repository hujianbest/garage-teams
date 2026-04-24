# Release Notes

本文件按 feature cycle 倒序记录 Garage OS 的用户可见变化。每个条目对应一次 `hf-finalize` 关闭的 workflow cycle。

---

## F010 — Context Handoff (`garage sync`) + Host Session Ingest (`garage session import`)

- 状态: ✅ 完成 (closed by hf-finalize 2026-04-24)
- Workflow Profile: `full`
- Execution Mode: `auto`
- Branch / PR: `cursor/f010-context-handoff-and-session-import-bf33` / TBD
- 关联文档:
  - 规格 `docs/features/F010-garage-context-handoff-and-session-ingest.md` (r2 已批准)
  - 设计 `docs/designs/2026-04-24-garage-context-handoff-and-session-ingest-design.md` (r3 已批准)
  - 任务计划 `docs/tasks/2026-04-24-garage-context-handoff-and-session-ingest-tasks.md` (r2 已批准)
  - 完整 review 链路: `docs/reviews/{spec(r1+r2),design(r1+r2+r3),tasks(r1+r2)}-review-F010-...md`
  - 三份 approval: `docs/approvals/F010-{spec,design,tasks}-approval.md`

### 用户可见变化

- **新增 `garage sync` 子命令**: 把 `.garage/knowledge/` + `.garage/experience/` 编译到三家 host 原生 context surface (`CLAUDE.md` / `.cursor/rules/garage-context.mdc` / `.opencode/AGENTS.md`)
  - 复用 F009 双 scope (`--scope project|user`) + per-host override (`--hosts claude:user,cursor:project`)
  - top-12 knowledge (4 per kind: decision/solution/pattern) + top-5 experience, 16KB budget
  - 三方 hash 决策: 用户改了 marker 之间内容 → SKIP_LOCALLY_MODIFIED + stderr warn; `--force` 强制覆写
  - 第二次 sync 内容相同 → mtime 不刷新 (NFR-1002 守门)
- **新增 `garage session import --from <host>` 子命令**: 读宿主 conversation history → 转 Garage SessionState → 触发 F003 自动提取链
  - 三家 host history reader: claude-code (~/.claude/conversations/) + opencode (~/.local/share/opencode/sessions/) + cursor (deferred D-1010, NotImplementedError stub)
  - alias: `claude` → `claude-code` 自动解析
  - default: TTY interactive (列出 ≤ 30 条对话 + 用户选); `--all` 显式 batch
  - 不绕过 F003 candidate 审批 (CON-1004 + B5 user-pact); 用户用 `garage memory review --action accept` 入库 (复用 F003/F004 既有链)
- **新增 `garage status` sync 段**: ADR-D10-12 在 F009 packs 段后追加 `Last synced (per host):` 段; sync-manifest.json 不存在时段省略 (CON-1001 字节级守门)
- **三家 first-class adapter Protocol 字段扩展**: 加 `target_context_path(name)` + `target_context_path_user(name)` (与 F009 `_user` 后缀模式对齐)
- **F003-F006 dataclass 0 改动 (CON-1002)**: ingest 利用既有 `SessionContext.metadata: Dict[str, Any]` 字段携带 `imported_from` provenance + `tags` + `problem_domain` signal-fill (ADR-D10-7), 命中 `_build_signals` 强 signal 识别规则; F003-F006 既有 318 个测试 0 退绿
- **零下游用户行为变化 (CON-1001)**: F009 既有 `garage init` / `garage status` 在 sync-manifest 不存在时输出字节级一致

### 数据与契约影响

- **新增 `.garage/config/sync-manifest.json` (schema_version=1)**:
  - `synced_at` + `sources` (knowledge_count / experience_count / knowledge_kinds / size_bytes / size_budget_bytes) + `targets[]`
  - `targets[].path`: absolute POSIX (per `Path(...).resolve(strict=False).as_posix()`)
  - `targets[].action`: WRITE_NEW / UPDATE_FROM_SOURCE / SKIP_LOCALLY_MODIFIED / OVERWRITE_FORCED / UNCHANGED
  - 与 F009 `host-installer.json` 完全独立 (CON-1005 + INV-F10-6 守门)
- **`HostInstallAdapter` Protocol 字段扩展同一类**: 加 `target_context_path` + `target_context_path_user` method; F007/F009 既有 5 method 签名严格不变 (CON-1006 + CON-1001)
- **新增 `SyncManifestMigrationError`**: JSON 损坏 / unsupported schema 时抛, 旧文件不被覆盖 (F009 CON-904 sync-side mirror)
- **新增 modules**:
  - `src/garage_os/sync/` (compiler / manifest / pipeline / render/{markdown, mdc})
  - `src/garage_os/ingest/` (host_readers/{claude_code, opencode, cursor} + selector + pipeline + types)
- **CLI 新增**: `garage sync` (--hosts + --scope + --force) + `garage session import` (--from + --all)
- **零依赖变更**: `pyproject.toml` + `uv.lock` git diff main..HEAD = 0
- **新增 12+ 测试文件 + 4 fixture JSON**:
  - `tests/sync/`: test_baseline_no_regression (INV-F10-2 sentinel) / test_compiler / test_manifest / test_render_{markdown,mdc} / test_pipeline_{idempotent, user_content_preserved, three_way_hash}
  - `tests/ingest/`: test_host_readers_registry / test_{claude_code, opencode, cursor_deferred}_reader / test_selector / test_pipeline_candidate_path / fixtures/{claude_code, opencode}/*.json
  - `tests/adapter/installer/`: test_context_path_three_hosts (T1)
  - `tests/test_cli.py`: TestSyncCommand (7) + TestStatusSyncSegment (2) + TestSessionImportCommand (5)

### 验证证据

- `pytest tests/ -q` → **825 passed** (+110 from F009 baseline 715, 0 regressions; +1 e2e import-then-sync added in finalize closing test-review IMP-1)
- `git diff main..HEAD -- src/garage_os/` → 仅 `sync/` + `ingest/` 新增 + `adapter/installer/host_registry.py` + `adapter/installer/hosts/*.py` + `cli.py` 改动
- `git diff main..HEAD -- pyproject.toml uv.lock` → 空 (零依赖变更)
- INV-F10-1..10 全部通过 (design § 4.1)
- **Manual smoke walkthrough** → 4 tracks 全绿 (dogfood / project / user / mixed-ingest), 完整记录 `docs/manual-smoke/F010-walkthrough.md`
- **完整质量链** → 全部通过:
  - `hf-spec-review` r2: APPROVED (12/12 r1 findings closed)
  - `hf-design-review` r3: PASS (r1 13 + r2 4 → r3 0 finding)
  - `hf-tasks-review` r2: PASS (r1 6 → r2 0 finding)
  - `hf-test-review` r1: PASS_WITH_FINDINGS (0 critical / 1 important / 6 minor / 4 nit)
  - `hf-code-review` r1: CHANGES_REQUESTED → PASS (IMP-1 + IMP-2 in-cycle fix)
  - `hf-traceability-review` r1: PASS_WITH_FINDINGS (0 critical / 0 important / 3 minor / 2 nit)
  - `hf-regression-gate` r1: PASS
  - `hf-completion-gate` r1: COMPLETE — Ready to finalize
  - `hf-finalize`: ✅ closed 2026-04-24

### 5 项实测占位字段 (hf-finalize 已填)

| 字段 | 实测 |
|---|---|
| `manual_smoke_wall_clock` | ~0.1s per command (NFR-1004 ≤ 5s; ~50× headroom) |
| `pytest_total_count` | 825 passed (+110 from F009 baseline 715) |
| `candidate_count_per_test` | 4 candidate items + 1 batch per fixture conversation (manual smoke Track 4) |
| `commit_count_per_group` | 11 commits (T1-T7 各 1 + manual smoke 1 + post-code-review fix 1 + ruff StrEnum 1 + finalize) |
| `release_notes_quality_chain` | ✅ 完整 (9 review/gate/finalize verdict 文档全部生成) |

### 已知限制 / 后续工作

- **D-1010 cursor history reader**: HYP-1005 Low confidence, 当前 stub; 等 Cursor history schema 稳定后落地
- **D-1011 sync file-watcher (F012-D 候选)**: 当前 sync 是显式触发, 无自动监听
- **D-1013 top-N + budget 配置化**: 当前默认 12+5+16KB 不可配置
- **F011 候选 (本 cycle 不夹带)**: KnowledgeEntry 加 style 维度 + 2 production agent + `garage pack install <git-url>`

---

## F009 — `garage init` 双 Scope 安装（project / user）+ 交互式 Scope 选择

- 状态: ✅ 完成 (closed by hf-finalize 2026-04-23)
- Workflow Profile: `full`
- Execution Mode: `auto`
- Branch / PR: `cursor/f009-init-scope-selection-bf33` / [#24](https://github.com/hujianbest/garage-agent/pull/24)
- 关联文档:
  - 规格 `docs/features/F009-garage-init-scope-selection.md`（已批准 r2，10 FR + 4 NFR + 4 CON + 4 ASM）
  - 设计 `docs/designs/2026-04-23-garage-init-scope-selection-design.md`（已批准 r2，11 ADR + 6 task + 9 INV + 11 测试文件）
  - 任务计划 `docs/tasks/2026-04-23-garage-init-scope-selection-tasks.md`（已批准 r3，6 task）
  - 完整 review 链路：`docs/reviews/{spec(r1+r2),design(r1+r2),tasks(r1+r2+r3)}-review-F009-...md`
  - 三份 approval：`docs/approvals/F009-{spec,design,tasks}-approval.md`

### 用户可见变化

- **新增 `--scope <project|user>` flag**（默认 `project`，CON-901 严守 F007/F008 字节级兼容）：让 solo creator 选择装到当前项目还是用户家目录
- **per-host scope override 语法**：`garage init --hosts claude:user,cursor:project` 让每个 host 独立指定 scope，覆盖全局 `--scope` 默认
- **交互式两轮（candidate C 三个开关）**：TTY 下 `garage init` 第一轮选宿主（F007 行为不变），第二轮 `[a]` all project (default 一键回车，F007/F008 兼容) / `[u]` all user / `[p]` per-host 逐个询问
- **三家 first-class adapter 各加 user scope path 解析**：
  - Claude Code: `~/.claude/skills/<id>/SKILL.md` + `~/.claude/agents/<id>.md`（Anthropic 官方）
  - OpenCode: `~/.config/opencode/skills/<id>/SKILL.md` + `~/.config/opencode/agent/<id>.md`（XDG default；dotfiles `~/.opencode/` 留 deferred）
  - Cursor: `~/.cursor/skills/<id>/SKILL.md`（无 agent surface，与 project scope 一致）
- **`garage status` 按 scope 分组**展示 installed packs：`Installed packs (project scope):` / `Installed packs (user scope):` 段，每段按 host 子分组 + 类型计数
- **stdout marker 派生**（FR-909 F007 grep 兼容硬约束）：F007 既有 `Installed N skills, M agents into hosts: <list>` 字面**字节级不变**；多 scope 时另起一行附加 `(N user-scope hosts, M project-scope hosts)` 段，下游脚本 `grep -E '^Installed [0-9]+ skills, [0-9]+ agents into hosts:'` 仍恰好命中 1 次
- **零下游用户行为变化（F007/F008 兼容）**：`garage init`、`garage init --hosts <list>`、`garage init --hosts all`、`garage init --hosts none`、`garage init --yes`、`garage init --hosts claude --force` 等 F007/F008 既有调用形态的 stdout / stderr / 退出码 / `.garage/` 目录创建 / `<cwd>/.{host}/skills/` 落盘行为字节级一致（除 manifest schema 1→2 自动 migration 例外，由 `VersionManager` 透明承接）
- **本仓库自身 dogfood 路径不受影响**（NFR-901 Dogfood 不变性硬门槛）：`garage init --hosts cursor,claude` 仍默认 project scope，落盘文件 SHA-256 与 F008 baseline 字节级一致（由 `test_dogfood_invariance_F009.py` sentinel 守门）

### 数据与契约影响

- **Manifest schema 1 → 2 升级**（FR-905 + ADR-D9-1/3）：
  - `files[].dst` 改为 absolute POSIX path（含 cwd 或 user home）
  - 新增 `files[].scope` 字段（`"project"` / `"user"`）
  - F007/F008 既有 schema 1 manifest 由 `read_manifest` 自动 migrate（旧 entry 默认 scope=project + dst project-relative 转 absolute）
  - 安全语义硬门槛（FR-905 #4 + CON-904）：JSON 损坏 / 字段缺失时抛 `ManifestMigrationError`，旧 manifest 字节级 + mtime 严格保留
  - 跨用户立场：manifest 默认不入项目 git（`.gitignore` 已排除），`files[].dst` absolute path 不追求跨用户可移植
- **HostInstallAdapter Protocol 字段扩展**（ADR-D9-6）：
  - 新增 optional `target_skill_path_user(skill_id) -> Path` + `target_agent_path_user(agent_id) -> Path | None` method（绝对路径返回值）
  - F007 既有 `target_skill_path` / `target_agent_path` / `render` method 签名严格不变（CON-901）
  - host_id 命名约束：MUST NOT contain literal `:`（ADR-D9-9 用作 `--hosts <host>:<scope>` 分隔符），由 `host_registry._build_registry()` import-time assert 守门
- **新增错误类型**:
  - `ManifestMigrationError(ValueError)` (ADR-D9-8): manifest migration 失败 → CLI exit 1
  - `UserHomeNotFoundError(RuntimeError)` (ADR-D9-10): `Path.home()` 抛 RuntimeError → CLI exit 1
  - `UnknownScopeError(ValueError)` (新增): scope 值非法 → CLI exit 1（`--hosts claude:bad` 或 `--scope unknown`，注：argparse choices 实施 `--scope` 时是 SystemExit(2)）
- **CLI 新增**:
  - `--scope <project|user>` flag（argparse choices，default 'project'）
  - `--hosts <host>:<scope>,...` 语法（`resolve_hosts_arg` 返回 `list[tuple[str, str | None]]`）
  - `cli._resolve_init_hosts` 返回二元组 `(hosts: list[str], scopes_per_host: dict[str, str])`
- **零依赖变更**：`pyproject.toml` + `uv.lock` 在本 cycle `git diff main..HEAD` 为空（NFR-803 子项）
- **CON-902 严守**：D7 安装管道 `pipeline._check_conflicts` (phase 3) + `discover_packs` (phase 1) 算法主体字节级保持原状；phase 2 (_resolve_targets) + phase 4 (decide_action 5 元组) + phase 5 (manifest schema 升至 2) 按 enum 允许的最小改动
- **新增 11 个测试文件**:
  - `tests/adapter/installer/test_adapter_user_scope.py`（FR-904 + ADR-D9-6 + Path.home() 守门，15 用例）
  - `tests/adapter/installer/test_host_registry_colon_assert.py`（ADR-D9-9 双层守门，3 用例）
  - `tests/adapter/installer/test_pipeline_scope_routing.py`（FR-906 + ADR-D9-2 + CON-902 INV-F9-2，10 用例）
  - `tests/adapter/installer/test_manifest_schema_v2.py`（FR-905 + ADR-D9-1/3，10 用例）
  - `tests/adapter/installer/test_manifest_migration_v1_to_v2.py`（FR-905 + ADR-D9-8 + 安全语义硬门槛，11 用例）
  - `tests/adapter/installer/test_interactive_two_round.py`（FR-903 + ADR-D9-5 candidate C，10 用例）
  - `tests/test_cli.py::TestInitWithScope`（FR-901/902/909，7 用例）
  - `tests/test_cli.py::TestStatusScopeGrouped`（FR-908 + ADR-D9-7，2 用例）
  - `tests/adapter/installer/test_dogfood_invariance_F009.py`（NFR-901 + ADR-D9-11 sentinel，2 用例）
  - `tests/adapter/installer/test_manifest_v2_dogfood_fields_stable.py`（ADR-D9-11 字段稳定独立守门，4 用例）
  - `tests/adapter/installer/test_full_init_user_scope.py`（端到端 user scope 三家宿主，4 用例）
- **新增 baseline fixture**: `tests/adapter/installer/dogfood_baseline/skill_md_sha256.json`（59 文件 SHA-256，hf-test-driven-dev executor 在 T5 fixture 内首跑生成，候选 A）
- **测试基线扩展**：F008 baseline 633 → F009 实施完成 **708 passed**（+75 增量；含 11 个新增测试文件 + carry-forward wording 修复 + 既有 test_neutrality.py 等自动 parametrize 拾取的兼容性测试）
- **Carry-forward wording 修复**（in-cycle，与 F008 carry-forward 同精神）：
  - `tests/adapter/installer/test_host_registry.py`：`resolve_hosts_arg` 返回类型 `list[str]` → `list[tuple[str, str | None]]` 同步更新（T1）
  - `tests/adapter/installer/test_manifest.py`：`MANIFEST_SCHEMA_VERSION == 1` → `== 2`；test fixture schema_version=1 → 2 (T3)
  - `tests/platform/test_version_manager.py`：`test_manifest_constant_pinned_to_one` → `pinned_to_two` (T3)
  - `tests/test_cli.py`：顶部 `import pytest` 加（T4 新增 TestInitWithScope 用 pytest.raises）

### 验证证据

- `pytest tests/ -q` → **713 passed** (+80 from F008 baseline 633, 0 regressions)
- `git diff main..HEAD -- src/garage_os/` → 仅 `adapter/installer/{host_registry,pipeline,manifest,interactive}.py` + `hosts/{claude,opencode,cursor}.py` + `cli.py` + `__init__.py` 改动；其它模块零改动
- `git diff main..HEAD -- pyproject.toml uv.lock` → 空（零依赖变更）
- INV-F9-1..9 全部通过（详见 design § 11.1）；INV-F9-1 dogfood SHA-256 由 sentinel test 自动守门
- **Manual smoke walkthrough** → 4 tracks 全绿（dogfood + project + user + mixed），完整记录见 `docs/manual-smoke/F009-walkthrough.md`
- **完整质量链** → 全部通过：
  - `hf-test-review` r1: APPROVE_WITH_FINDINGS (0 critical / 2 important / 10 minor)
  - `hf-code-review` r1: APPROVE_WITH_FINDINGS (0 critical / 4 important / 5 minor; I-3+I-4 in-cycle fix)
  - `hf-traceability-review` r1: APPROVE_WITH_FINDINGS (0 critical / 3 important / 5 minor)
  - `hf-regression-gate` r1: PASS
  - `hf-completion-gate` r1: COMPLETE — Ready to finalize
  - `hf-finalize`: ✅ closed 2026-04-23

### 实测占位字段（已填）

| 字段 | 实测值 |
|---|---|
| `manual_smoke_wall_clock` | 0.11s (`garage init --hosts all --scope user`) << 5s NFR-803 上限 |
| `pytest_total_count` | 713 passed (+80 from F008 baseline 633, 0 regressions) |
| `installed_packs_from_manifest` | dogfood: 58 skills + 1 agent (29 skill × 2 host + 1 agent claude only); --hosts all: 87 skills + 2 agents (29 × 3 + 2 hosts with agents); --hosts all --scope user: 同 87 skills + 2 agents 但装到 fake_home |
| `commit_count_per_group` | 8 commits (T1-T6 各 1 + manual smoke 1 + post-code-review 1) |
| `release_notes_quality_chain` | ✅ 完整: 6 个 review/gate 文档全部生成 + finalize-approval 显式记录 carry-forward |

### 已知限制 / 后续工作

- **F010 候选 — `garage uninstall --scope <scope>`**：与 F009 正交（先做装两端再做反向）
- **F010 候选 — `garage update --scope <scope>`**：同上
- **F010 候选 — D7 管道扩展为递归 `references/` 子目录**（F008 deferred）：与 F009 正交，独立 cycle
- **单独候选 — Enterprise scope**（Anthropic 官方有）：solo creator 用不到，需要时单独 spec 化
- **单独候选 — Plugin scope**：同上
- **单独子选项候选 — OpenCode dotfiles 风格 `~/.opencode/skills/`**：XDG default 已覆盖 90%+ 用户；少数 dotfiles 偏好用户可在 D10+ 加 `--scope user-dotfiles` 子选项
- **不做 — 跨 scope 同名 skill 自动 dedupe / 优先级解析**：Garage 不替宿主决定加载优先级（manifesto "你做主"）
- **不做 — `~/.garage/config/host-installer.json` 全局 manifest**：与 workspace-first 信念冲突；每次 init 仍只写一份 cwd manifest

---

## F008 — Garage Coding Pack 与 Writing Pack（把 .agents/skills/ 物化为可分发 packs，兑现 manifesto "几秒变成你的 Agent" 承诺）

- 状态: ✅ 已完成（2026-04-23）
- Workflow Profile: `full`
- Execution Mode: `auto`
- Branch / PR: `cursor/f008-coding-pack-and-writing-pack-bf33` / [#22](https://github.com/hujianbest/garage-agent/pull/22)
- 关联文档:
  - 规格 `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准 r2 + design/tasks 阶段反向同步 wording）
  - 设计 `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（已批准 r2，含 9 项 ADR + 9 sub-commit + 9 INV + 5 测试文件）
  - 任务计划 `docs/tasks/2026-04-22-garage-coding-pack-and-writing-pack-tasks.md`（已批准 r4，9 个 task）
  - 完整 review 链路：`docs/reviews/{spec(r1+r2),design(r1+r2),tasks(r1+r2+r3+r4),test,code,traceability}-review-F008-...md`
  - 三份 approval：`docs/approvals/F008-{spec,design,tasks}-approval.md`
  - regression-gate `docs/verification/F008-regression-gate.md`
  - completion-gate `docs/verification/F008-completion-gate.md`
  - workflow closeout `docs/verification/F008-finalize-closeout-pack.md`

### 用户可见变化

- **新建 `packs/coding/`**（22 skill + 11 family-level 共享资产）：HarnessFlow 工程工作流 family pack 物化落地，把 21 hf-* + 1 using-hf-workflow 完整搬到 packs/coding/skills/，外加 4 个 family-level shared docs (packs/coding/skills/docs/) + 5 个 templates (packs/coding/skills/templates/) + 2 个 principles (packs/coding/principles/)，让下游用户挂载后直接获得完整 SDD + 闸 TDD 工程工作流能力
- **新建 `packs/writing/`**（4 skill + 1 family-level prompts）：内容创作 family pack 物化落地，含 blog-writing（含发布前定稿 12 条规律）+ humanizer-zh（去 AI 痕迹）+ hv-analysis（横纵分析法深度研究）+ khazix-writer（卡兹克公众号风格）+ family-level prompts/横纵分析法.md，外加上游 LICENSE 保留
- **`packs/garage/` 扩容到 3 skill** + version 0.1.0 → 0.2.0：从单一 garage-hello 占位 sample 扩到 getting-started 三件套（+ find-skills 发现新 skill 的 meta-skill + writing-skills 写新 skill 的 SOP），garage-sample-agent.md 保留（验证 agent surface 在多 pack 下仍工作）
- **总计**：3 个 pack × **29 个 skill** × 3 个宿主 = `garage init --hosts all` 物化 87 个 skill 文件 + 1 个 agent 文件（agent 仅装到 claude / opencode；cursor 无 agent surface）
- **`docs/principles/skill-anatomy.md` drift 收敛**：项目早期 AHE → HF 重命名后未同步的 70 字节 drift 已收敛，根级与 packs/coding/principles/ 字节相等，由 sentinel test `tests/adapter/installer/test_skill_anatomy_drift.py` 守门
- **`.agents/skills/` 整目录删除**：F008 ADR-D8-2 候选 C，本仓库自身 IDE 加载入口转向 dogfood 安装产物（`.cursor/skills/` + `.claude/skills/` 已在 `.gitignore` 排除）。首次 clone 贡献者需跑 `garage init --hosts cursor,claude` 激活 IDE skill 加载
- **AGENTS.md 局部刷新**：§ Packs & Host Installer 段加 packs/{garage,coding,writing}/ 三行 + "本仓库自身 IDE 加载入口" onboarding 段
- **packs/README.md "当前 packs" 表更新**：F007 后只有 garage 1 行 → F008 后 garage + coding + writing 3 行
- **零下游用户行为变化**：`garage init --hosts <list>` 接口完全不变；只是装到的内容物从 1 sample skill 变为 29 真实可用 skill

### 数据与契约影响

- **零 schema 变更**：`pack.json` schema 仍 6 字段（schema_version=1 / pack_id / version / description / skills[] / agents[]），不引入新字段
- **零 host adapter 注册表变更**：仍 claude / opencode / cursor 三项
- **零 D7 安装管道代码变更**：CON-801 严守，`git diff main..HEAD -- src/garage_os/` = 空（INV-5 守门）
- **零依赖变更**：`pyproject.toml` + `uv.lock` 无变化（NFR-803 守门）
- **新增 EXEMPTION_LIST 常量**（`tests/adapter/installer/test_neutrality_exemption_list.py`）：F008 ADR-D8-9 文件级豁免清单，7 项 meta/教学/README 文件保留宿主特定字面值（与 SKILL.md/agent.md 强约束分层），三层同步守门（spec NFR-801 详细说明 + design ADR-D8-9 + 测试 EXEMPTION_LIST）
- **CON-803 字节级 1:1 例外 #2**（宿主中性化最小替换）：T2 (hv-analysis SKILL.md L55) + T3 (writing-skills SKILL.md L12) 各 1 处，每处 ≤ 3 行 diff（量化守门），把上游 SKILL.md 内宿主特定路径作为 example 的字面值替换为宿主无关表达
- **新增 5 个测试文件**（`tests/adapter/installer/`）：
  - `test_skill_anatomy_drift.py` — sentinel: drift 收敛硬门槛 (T1c)
  - `test_full_packs_install.py` — INV-1 总 29 skill + INV-2 family-asset 单点 + FR-806 三家宿主全装 + INV-4 字节级 + NFR-803 ≤ 5s (T4c)
  - `test_packs_garage_extended.py` — FR-803 packs/garage/ 扩容 + ADR-D8-5 agents 保留 + ADR-D8-6 version bump (T4c)
  - `test_dogfood_layout.py` — INV-6 .agents/skills/ 移除 + INV-8 .gitignore + AGENTS.md 多个结构性 invariant (T4c)
  - `test_neutrality_exemption_list.py` — ADR-D8-9 双层守门 (T4c)
- **测试基线扩展**：F007 baseline 586 → F008 实施完成 633 passed（+22 test_neutrality.py 新增 SKILL.md parametrize + +18 个新测试用例 + +7 个 packs/{garage,writing}/skills/<id>/SKILL.md 增量），0 改写、0 退绿（NFR-802 严格守门）
- **F007 carry-forward 修复**：`tests/test_cli.py:3042` 的 hard-coded `installed_packs == ["garage"]` 改为 `"garage" in installed_packs`，与 `test_subprocess_smoke_three_hosts:3144` regex-on-marker 同精神（防止 packs 扩容后 F007 测试退绿）

### 验证证据

- `pytest tests/ -q` → **633 passed in ~26.4s**（F007 baseline 586 → +47 增量, 0 改写、0 退绿；NFR-802 严格守门）
- `git diff main..HEAD -- src/garage_os/` → 空（CON-801 严守，INV-5 验证）
- `git diff main..HEAD -- pyproject.toml uv.lock` → 空（零依赖变更，NFR-803 子项）
- INV-1..9 全部通过（详见 design § 11.1）；INV-7（IDE 加载链）由 manual smoke walkthrough 验证
- **Manual smoke walkthrough**（双轨 dogfood + tmp）：
  - **Garage 仓库自身 dogfood**（`/opt/cursor/artifacts/f008_dogfood_init.log`）：`garage init --hosts cursor,claude` → `Installed 58 skills, 1 agents into hosts: claude, cursor` (58 = 29 × 2 hosts; 1 agent = garage-sample-agent → claude only)
  - **干净下游环境**（`/opt/cursor/artifacts/f008_smoke_first.log`，`/tmp/f008-smoke/`）：`garage init --hosts all` → `Installed 87 skills, 2 agents into hosts: claude, cursor, opencode` (87 = 29 × 3 hosts; 2 agents = 1 agent × 2 hosts claude+opencode；cursor 无 agent surface)
  - **`Installed N skills` marker N 派生验证**：N == sum(三 pack.json.skills[]) == 22 (coding) + 3 (garage) + 4 (writing) = 29，与 `garage init --hosts <list>` 实测 `N × len(hosts)` 完全一致 ✓
  - **manifest excerpt**（`/opt/cursor/artifacts/f008_smoke_manifest_excerpt.json`）：schema_version=1, installed_packs=["coding","garage","writing"], files=89 (87+2), 每条 entry 含 src/dst/host/pack_id/content_hash
  - **目录树**（`/opt/cursor/artifacts/f008_smoke_claude_tree.txt`）：29 skill 全部落到 .claude/skills/
- **NFR-803 wall-clock**（双轨）：
  - 自动化口径：`test_full_packs_install::test_install_packs_under_5_seconds_NFR803` 实测 < **100ms** （远低于 5s 上限，50× margin）
  - **manual smoke 口径**：第一次 `time garage init --hosts all` 实测 **0m0.120s**；第二次幂等 **0m0.107s**（远低于 NFR-803 5s + NFR-702 2s 双重上限）
- **NFR-702 mtime stability 严格幂等**：第二次运行 `.claude/skills/hf-specify/SKILL.md` mtime = 1776952954 与首次完全相等 ✓
- **完整质量链**（按 cycle 进度倒序）：
  - hf-spec-review r1 (`需修改`, 4 important + 3 minor 全 LLM-FIXABLE) → r2 `通过`
  - hf-spec auto-mode approval (`docs/approvals/F008-spec-approval.md`)
  - hf-design-review r1 (`需修改`, 1 USER-INPUT 收敛 + 3 important + 4 minor LLM-FIXABLE) → r2 `通过`（reviewer 收回 USER-INPUT 标记）
  - hf-design auto-mode approval (`docs/approvals/F008-design-approval.md`)
  - hf-tasks-review r1 (`需修改`, 1 critical + 2 important + 6 minor + 3 缺失) → r2 (1 critical 升级到 ADR-D8-9 + 2 minor) → r3 (1 important + 3 minor wording 残留) → r4 `通过`
  - hf-tasks auto-mode approval (`docs/approvals/F008-tasks-approval.md`)
  - hf-test-review `通过` (4 minor LLM-FIXABLE 不阻塞，6 维均分 7.67/10)
  - hf-code-review `通过` (5 minor LLM-FIXABLE 不阻塞，6 维均分 9.00/10)
  - hf-traceability-review `通过` (5 minor LLM-FIXABLE 全 carry-forward 不阻塞，6 维均分 8.83/10)
  - hf-regression-gate `通过` (`docs/verification/F008-regression-gate.md`，全套 7 项 fresh evidence + 1 wording 漂移自洽修复)
  - hf-completion-gate `通过` (`docs/verification/F008-completion-gate.md`，9/9 task 落地 + 9 success criteria + 6 红线 + 9 INV 全部 ✓ + 无剩余 task)
  - hf-finalize workflow closeout (`docs/verification/F008-finalize-closeout-pack.md`)
- **9 sub-commit 分组**（NFR-804 git diff 可审计）：
  - T1a `4f92b05 f008(coding/skills): packs/coding/ 22 skill cp -r 字节级搬迁`
  - T1b `1a86212 f008(coding/family-asset): 11 个 family-level 资产 + pack.json + README`
  - T1c `fa3d3fc f008(coding/drift-sync): 反向同步根级 skill-anatomy.md + sentinel test`
  - T2 `f0f2c05 f008(writing): packs/writing/ 4 skill + LICENSE + family-level prompts/ + 宿主中性化替换`
  - T3 `b81664a f008(garage): +find-skills +writing-skills, 0.1.0→0.2.0 + 宿主中性化替换`
  - T4a `5a95b45 f008(layout/remove-agents): 删 .agents/skills/, dogfood 产物入 .gitignore`
  - T4b `907bbfb f008(layout/agents-md): AGENTS.md Packs 段刷新 + 首次 clone 贡献者 onboarding`
  - T4c `57a1efd f008(layout/tests): 4 集成测试 + EXEMPTION_LIST 扩展`
  - T5 `6aa7587 f008(docs): packs/README + user-guide + RELEASE_NOTES F008 占位段`
  - 加 `3002215`（task-progress 同步）+ `0119b50`（三 review record + regression-gate）+ `572689f`（completion-gate + 测试 wording 修复）= 共 12 个 cycle commit

### 已知限制 / 后续工作

- **F009 候选 — D7 安装管道扩展为递归 references/ 子目录**：design ADR-D8-4 选定"文档级提示"路径，下游用户在 Claude Code 加载 hf-* skill 时看到的 `references/spec-template.md` 引用是文档级提示（指向 Garage 仓库 git checkout 的 packs/ 路径），不在 .claude/skills/ 下复制。D9 cycle 可扩展 D7 管道递归子目录闭合此体验差距
- **F009 候选 — `garage uninstall --hosts <list>` + `garage update --hosts <list>`**：F007 显式 deferred 的安装逆向操作 + 拉新流程，sentinel manifest 已为这两条留好 entry point
- **`packs/product-insights/`**：F001 CON-002 提及但仓库当前无任何 product discovery skill 内容物；待真实内容物到位后再开 cycle
- **首次 clone 贡献者 IDE 加载链空窗**（ADR-D8-2 候选 C 已知 trade-off）：必须先跑 `garage init --hosts cursor,claude` 激活 dogfood 产物才能在 IDE 内加载 hf-* skill；AGENTS.md `## Packs & Host Installer (F007/F008) > 本仓库自身 IDE 加载入口` 段已说明
- **NFR-801 文件级豁免清单 7 项**（design ADR-D8-9）：humanizer-zh/README.md + writing-skills/anthropic-best-practices.md + writing-skills/examples/CLAUDE_MD_TESTING.md + packs/writing/README.md + packs/README.md + packs/garage/README.md + packs/coding/README.md 含 `.claude/skills/` 等字面值作为 meta/教学/README 安装样板；SKILL.md/agent.md 仍受 NFR-801 强约束。任何后续新增同类豁免必须三层同步：spec NFR-801 详细说明 + design ADR-D8-9 + tests/adapter/installer/test_neutrality_exemption_list.py 的 EXEMPTION_LIST 常量

---

## F007 — Garage Packs 与宿主安装器（让 garage init 把内置 skills/agents 安装到 Claude Code / OpenCode / Cursor）

- 状态: ✅ 已完成（2026-04-19）
- Workflow Profile: `coding`
- Execution Mode: `auto-mode`
- Branch / PR: `cursor/f007-packs-host-installer-fa86` / [#18](https://github.com/hujianbest/garage-agent/pull/18)
- 关联文档:
  - 规格 `docs/features/F007-garage-packs-and-host-installer.md`
  - 设计 `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`（r2）
  - 任务计划 `docs/tasks/2026-04-19-garage-packs-and-host-installer-tasks.md`
  - completion gate `docs/verification/F007-completion-gate.md`
  - regression gate `docs/verification/F007-regression-gate.md`
  - 完整 review 链路：`docs/reviews/{spec(r1+r2),design(r1+r2),tasks,test,code,traceability}-review-F007-*.md`
  - finalize closeout `docs/verification/F007-finalize-closeout-pack.md`

### 用户可见变化

- **新建 `packs/` 目录契约**（兑现 F001 `CON-002` 的 `packs/coding/skills/` 约束）：仓库根新建 `packs/<pack-id>/` 目录树，含 `pack.json`（`schema_version`/`pack_id`/`version`/`description`/`skills[]`/`agents[]`）、`README.md`、`skills/<id>/SKILL.md`、`agents/<id>.md`。本 cycle 落 1 个占位 pack `packs/garage/`（含 1 sample skill `garage-hello` + 1 sample agent `garage-sample-agent`），验证容器与端到端管道；`.agents/skills/` 30 个 HF skills 的实际搬迁延后到 F008+。
- **`garage init` 加 `--hosts <list>` / `--yes` / `--force` 三个 flag**，把 `packs/` 内容物化到 cwd 下的宿主原生目录：
  - `garage init --hosts all` → 装到三个 first-class 宿主 `claude` / `opencode` / `cursor`
  - `garage init --hosts claude,cursor` → 仅指定宿主
  - `garage init --hosts none` / `garage init --yes` → 跳过宿主安装（仅 .garage/ 创建，等价 F002 行为）
  - 不带任何 flag + TTY → 交互式 `[y/N/a=yes-to-all/q=stop]` 询问
  - 不带任何 flag + non-TTY → 退化为 `--hosts none` + stderr 提示
- **三家宿主路径映射**（来源：OpenSpec `docs/supported-tools.md` + 各家官方文档）：
  - Claude Code: `.claude/skills/<name>/SKILL.md` + `.claude/agents/<name>.md`
  - OpenCode: `.opencode/skills/<name>/SKILL.md` + `.opencode/agent/<name>.md`（注意 agent 单数）
  - Cursor: `.cursor/skills/<name>/SKILL.md`（无原生 agent surface，自动跳过）
- **YAML front matter 注入安装标记**（ADR-D7-2）：每个被安装的 SKILL.md / agent.md 在 front matter 中追加 `installed_by: garage` + `installed_pack: <pack-id>`；agent.md 无 front matter 时自动插入最小 front matter（容错路径）。注入幂等：再次安装不会重复堆叠字段。
- **Extend Mode + 幂等再运行**（FR-706a + FR-706b）：再次 `garage init` 自动比对 SHA-256：
  - 未被本地修改的目标文件 → 按当前 packs 源覆盖更新（NFR-702: mtime 不刷新，无字节变化）
  - **已被本地修改的目标文件 → 默认跳过 + stderr `Skipped <path> (locally modified, pass --force to overwrite)`；只有 `--force` 才覆盖**
  - 新增宿主 → 既有宿主目录零变更，仅追加新宿主；`installed_hosts` 累加
- **安装清单 `.garage/config/host-installer.json`**（schema_version=1，受 VersionManager 管控）：每次成功安装写入 `installed_hosts[]` / `installed_packs[]` / `files[]`；每个 file entry 含 `(src, dst, host, pack_id, content_hash)`，让任何 Agent 仅凭该文件就能回答 "本仓库装过哪些 host、哪些 pack、哪些文件来自 Garage" 三个问题。
- **退出码三段式**：0 = 成功（含「无 packs，仅创建 .garage/」）；1 = 输入错误 / pack.json 非法 / SKILL.md 缺 front matter / OS IO 错误；2 = 同名 skill 跨 pack 冲突。
- **同名 skill 跨 pack 冲突保护**（FR-704 #4）：当未来 F008 把 HF skills 搬到 `packs/coding/` 后又有 pack 复用同名，安装管道会以退出码 2 + stderr 列出冲突 source/dest 而非静默覆盖。

### 数据与契约影响

- **零 schema 变更于既有 contracts**：`HostAdapterProtocol` (F001) / `KnowledgeStore` (F003) / `ExperienceIndex` / `SessionManager` 全部不动。
- **新增 schema**：`.garage/config/host-installer.json` `schema_version=1`，由 `VersionManager` 通过 `detect_version` path-based 自动识别（不需要显式 register API），`MANIFEST_SCHEMA_VERSION` 常量在 `src/garage_os/adapter/installer/manifest.py` 顶部 + `test_version_manager.py::test_manifest_constant_pinned_to_one` sentinel 测试守护未来 schema bump 必须是显式行为。
- **新增子包**：`src/garage_os/adapter/installer/`（11 个源文件 + 9 个测试模块），与 F001 `claude_code_adapter.py` 同包但接口独立（`HostInstallAdapter` Protocol vs `HostAdapterProtocol`，参见 ADR-D7-1）。
- **零依赖变更**：`pyproject.toml` 在本 cycle `git diff main..HEAD` 为空。NFR-101 显式禁止新增 TUI 依赖，交互 prompt 用 stdlib `input()` 实现。
- **新增 CLI 模块顶层常量**（`src/garage_os/cli.py`）：4 个 stdout/stderr marker (`INSTALLED_FMT` / `ERR_PACK_INVALID_FMT` / `ERR_MARKER_FAILED_FMT` / `ERR_HOST_FILE_FAILED_FMT`) + 与 `host_registry` (UnknownHostError message) / `pipeline` (`WARN_LOCALLY_MODIFIED_FMT` / `WARN_OVERWRITE_FORCED_FMT` / `MSG_NO_PACKS_FMT`) 的 ownership 边界已在 docstring 显式标注。
- **新增 documentation contracts**：
  - `packs/README.md`、`packs/<pack-id>/README.md`（双层 README 强制）
  - `docs/guides/garage-os-user-guide.md` 增 "Pack & Host Installer" 段
  - `AGENTS.md` 增 `## Packs & Host Installer` 入口指针段 + 模块表 `adapter` 行更新

### 验证证据

- `pytest tests/ -q` → **586 passed in ~26s**（F006 baseline 496 → +90 个 F007 新增测试，零回归）
  - T2 22 + T3 47 + T4 14 + T5 4 + 测试评审 carry-forward 5 + 代码评审 carry-forward 2
- `mypy src/garage_os/adapter/installer/` → 0 errors（11 source files）
- `mypy src/garage_os/cli.py` → 1 error pre-existing on main (`_memory_review` line 562 / line 667 post-F007)，**F007 引入 0 new mypy errors**（用 `git checkout main` 验证）
- `ruff check src/garage_os/adapter/installer/ tests/adapter/installer/` → 0 errors（35 fixable + 2 carry-forward `noqa` / 单行 import 已闭合）
- E2E manual smoke：在 `/tmp/f007-smoke/` 跑 `garage init --hosts all` → 三宿主目录全部生成 + manifest 正确 + 第二次运行 mtime 不变（NFR-702 实证；evidence 在 `/opt/cursor/artifacts/f007_manual_smoke_init_all_hosts.log`）
- 完整质量链：spec-review r1（需修改）→ r2（通过）→ design-review r1（需修改）→ r2（通过）→ tasks-review（通过 5 minor carry-forward 闭合）→ test-review（通过 5 minor carry-forward 闭合，9 个新增用例）→ code-review（通过 1 important + 5 minor carry-forward 闭合）→ traceability-review（通过 3 项 hf-finalize 闭合）→ regression-gate（通过）→ completion-gate（通过）→ finalize（workflow closeout）

### 已知限制 / 后续工作

- **F008 候选 — 把 `.agents/skills/` 30 个 HF skills 搬迁到 `packs/coding/skills/`**：F007 已把容器、注册表、安装管道、conflict 检测、测试矩阵全部铺好；搬迁本身是机械动作，不需要 spec/design 改动。
- **F008 候选 — `garage uninstall --hosts <list>` + `garage update --hosts <list>`**：F007 显式 deferred 的安装逆向操作 + 拉新流程。manifest schema 已为这两条留好 entry point（`files[].content_hash` 可识别 Garage-owned 文件 → uninstall；`schema_version` 可标识 packs 版本 → update）。
- **单独候选 — 全局安装到 `~/.claude/skills/...`**（OpenSpec issue #752 模式）：solo creator 跨多客户仓库的需求；与 Garage workspace-first 信念有 trade-off，应单独 spec 化。
- **F008+ 候选 — 新增宿主**（Codex / Gemini CLI / Windsurf / Copilot 等）：F007 已确立 first-class adapter 注册模式；新增宿主成本 = 1 个 adapter 子模块 + `HOST_REGISTRY` 字面表 1 行 + 1 套测试；spec / design 改动最小。
- **Cursor `.cursor/skills/` 在某些用户的 Cursor 版本可能不识别**：本 cycle 选用是因为 OpenSpec 已验证可行 + 与 Anthropic SKILL.md 同构 + 不污染 always-loaded `.cursor/rules/`；若用户反馈不识别可在 F008+ 增 `.cursor/rules/` fallback。
- **Pre-existing baseline mypy + ruff 警告**：1 个 `_memory_review` 历史 mypy error（F004 vintage）+ ~47 个 ruff stylistic warnings（F002/F003/F004 vintage）— 全部超出 F007 范围，由独立 cycle 治理。F007 新引入的代码已 0 mypy + 0 ruff error。
- **未做 live host-tool runtime 检验**：F007 是文件系统级安装（spec § 4.2 明确 boundary）；用户在 Claude Code / OpenCode / Cursor 真正"加载并调用"安装的 SKILL.md 的端到端体验不在本 cycle 验证范围。

---

## F006 — Garage Recall & Knowledge Graph（主动召回 + 知识图最小可用形态）

- 状态: ✅ 已完成（2026-04-19）
- Workflow Profile: `standard`
- Execution Mode: `auto`
- Branch / PR: `cursor/f006-recommend-and-link-177b` / [#17](https://github.com/hujianbest/garage-agent/pull/17)
- 关联文档:
  - 规格 `docs/features/F006-garage-recall-and-knowledge-graph.md`
  - 设计 `docs/designs/2026-04-19-garage-recall-and-knowledge-graph-design.md`（r1 inline-fixed）
  - 任务计划 `docs/tasks/2026-04-19-garage-recall-and-knowledge-graph-tasks.md`
  - completion gate `docs/verification/F006-completion-gate.md`
  - regression gate `docs/verification/F006-regression-gate.md`
  - 完整 review 链路：`docs/reviews/{spec(r1+r2),design,tasks,test,code,traceability}-review-F006-recall-and-knowledge-graph*.md`
  - finalize closeout `docs/verification/F006-finalize-closeout-pack.md`

### 用户可见变化

- **新增 3 个 CLI 子命令**让用户主动召回积累的知识、把孤立 entry 连成图：
  - `garage recommend <query>` — **mixed knowledge + experience** 召回；按 score 降序排序，带 `match_reasons` 解释命中理由；支持 `--tag` (可重复) / `--domain` / `--top` 过滤；零结果时给明确兜底文案
  - `garage knowledge link --from --to [--kind related-decision|related-task]` — 写 `KnowledgeEntry.related_decisions` / `related_tasks` 字段（这两字段从 F001 起就存在，本 cycle 第一次接通到用户面）；幂等（重复 link 不重复追加但 stdout 显式 "Already linked"）
  - `garage knowledge graph --id` — 1 跳邻居视图（`Outgoing edges:` 来自 entry 字段，`Incoming edges:` 全库扫描"哪些其他 entry 把我列为 related"）
- **F003 RecommendationService 投入回报率扩大**：F003 已经做的 ranking + match_reasons 算法此前只在 `garage run <skill>` 流程内被动触发。F006 让同一逻辑在更高频、纯本地、无 Claude Code 依赖的 `garage recommend <query>` 入口上服务用户，解锁 manifesto "记得你上个月的架构决策" 承诺。
- **`cli:` 命名空间扩展到 link 路径**：`garage knowledge link` 写入 entry 时强制 `source_artifact = "cli:knowledge-link"`，与 F005 已有的 `cli:knowledge-add` / `cli:knowledge-edit` / `cli:experience-add` 同命名空间。`grep "cli:knowledge-link" .garage/knowledge/` 可一键筛选所有手工建图动作。
- **v1.1 `version+=1` 不变量延伸**：CLI `link` 走 `KnowledgeStore.update()` 路径，每次 link（含重复 link）都触发 version 递增，与 F004 v1.1 + F005 edit 路径一致。

### 数据与契约影响

- **零 schema 变更**：`KnowledgeEntry.related_decisions: List[str]` / `related_tasks: List[str]` / `ExperienceRecord` 全部 dataclass 字段不变（CON-602）。
- **零依赖变更**：`pyproject.toml` 在本 cycle `git diff main..HEAD` 为空（NFR-602 ✓）。
- **零 `RecommendationService.recommend()` 算法变化**：F003 `garage run` 路径行为完全不变（CON-605）；测试 `test_recommendation_service_recommend_byte_level_unchanged` 通过 `inspect.getsource` 断言 5 个关键 score weight token 未被改动。
- **新增 `RecommendationContextBuilder.build_from_query(query, tags, domain)` 方法**（non-breaking 增量）：把 query 字符串映射为 `RecommendationService.recommend()` 已有契约形状的 context dict；既有 `build()` 一字未改。
- **CLI 内独立 experience scorer**（`_recommend_experience` helper）：不进 `RecommendationService`，由 cli.py 承担 experience 半边召回；保留 `garage run` 路径行为不变。这是 spec round-1 USER-INPUT path B 裁决的结果（详见 `docs/approvals/F006-spec-approval.md`）。
- **新增 CLI 模块顶层常量**（`src/garage_os/cli.py`）：
  - 6 个 stdout/stderr 常量：`RECOMMEND_NO_RESULTS_FMT` / `KNOWLEDGE_LINKED_FMT` / `KNOWLEDGE_LINK_ALREADY_FMT` / `ERR_LINK_FROM_AMBIGUOUS_FMT` / `KNOWLEDGE_GRAPH_NODE_FMT` + 3 个 graph 段标题字符串
  - 1 个 source-marker 常量：`CLI_SOURCE_KNOWLEDGE_LINK = "cli:knowledge-link"`
- **新增顶级 sub-parser** `garage recommend`（跨 knowledge + experience 域，挂顶级是有意决定，详见 design ADR-601）+ 2 个二级 sub-parsers `knowledge link` / `knowledge graph`。

### 验证证据

- `pytest tests/ -q` → **496 passed in ~26s**（F005 baseline 451 → +45 个 F006 新增测试，零回归）
- F006 触动模块 mypy 持平 baseline（无新引入错误；2 个 pre-existing baseline errors 与 F006 无因果）
- E2E walkthrough：在干净 `.garage/` 内完成 `add ×3 → experience add → recommend (mixed score sorted) → link ×3 → graph (out + in edges) → recommend (top filter) → recommend (zero result) → status` 全链路（详见 `/opt/cursor/artifacts/f006_cli_walkthrough.log`）
- 完整质量链：spec-review r1（需修改 USER-INPUT）→ r2（通过）→ design-review（通过 3 minor inline-fixed）→ tasks-review（通过 5 minor; 3 absorbed downstream）→ test-review（通过 3 minor; supplementary tests added）→ code-review（通过 3 minor; CR-1/CR-2 inline-fixed）→ traceability-review（通过 3 minor）→ regression-gate（通过）→ completion-gate（通过）

### 已知限制 / 后续工作

- **Stage 3 进入信号尚未达标**：F006 把召回 pull 入口与图衬底都铺好了，但 `growth-strategy.md` 的 "知识库条目 >100" + "识别到 5+ 可复用模式" 信号**仍依赖用户使用频率**。下一个 cycle 是否启动 Stage 3 由 `hf-workflow-router` 在新会话独立判断。
- **`_recommend_experience` 多次累加 vs 单次累加语义微差（code review CR-3 minor）**：tech / pattern / lesson 规则可对同一 record 重复加分；task_type 规则带 break。spec FR-602 措辞已允许此读法；建议下一 cycle 在真实使用数据上观察 score 分布后决定是否对齐。
- **§ 5 deferred backlog（spec 显式不在本 cycle）**：`garage knowledge unlink` / 多跳 graph (`graph --depth 2`) / experience link / 跨类型 link / 图导出 (GraphViz/Mermaid/JSON) / `recommend --format json` / `recommend --include knowledge-only|experience-only` / embedding-based 相似度 / 自动建议链接 — 全部由后续 cycle 独立立项。
- **Pre-existing baseline mypy + ruff 警告**：2 个 F004 历史 mypy errors + cli.py / recommendation_service.py 共 47 个 ruff stylistic warnings（含 1 个 unused import on `recommendation_service.py:10`）— 全部超出 F006 范围，由独立 cycle 治理。F006 新引入的 ruff 增量（4 项 UP045）与现有代码风格一致，未引入新行为问题。

---

## F005 — Garage Knowledge Authoring CLI（让 Stage 2 飞轮能从终端起转）

- 状态: ✅ 已完成（2026-04-19）
- Workflow Profile: `standard`
- Execution Mode: `auto`
- Branch / PR: `cursor/f005-knowledge-add-cli-177b` / [#16](https://github.com/hujianbest/garage-agent/pull/16)
- 关联文档:
  - 规格 `docs/features/F005-garage-knowledge-authoring-cli.md`
  - 设计 `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md`（r1 inline-fixed）
  - 任务计划 `docs/tasks/2026-04-19-garage-knowledge-authoring-cli-tasks.md`（r1 inline-fixed）
  - completion gate `docs/verification/F005-completion-gate.md`
  - regression gate `docs/verification/F005-regression-gate.md`
  - 完整 review 链路：`docs/reviews/{spec,design,tasks,test,code,traceability}-review-F005-knowledge-authoring-cli.md`
  - finalize closeout `docs/verification/F005-finalize-closeout-pack.md`

### 用户可见变化

- **新增 7 个 CLI 子命令**让用户在不依赖 session 归档与候选提取的前提下从终端直接 CRUD 知识与经验：
  - `garage knowledge add --type {decision|pattern|solution} --topic ... --content ...`（或 `--from-file`）
  - `garage knowledge edit --type ... --id ... [--topic|--content|--from-file|--tags|--status]`（自动 v1.1 `version+=1`）
  - `garage knowledge show --type ... --id ...`（人类可读 front matter + body）
  - `garage knowledge delete --type ... --id ...`
  - `garage experience add --task-type ... --skill ... --domain ... --outcome ... --duration ... --complexity ... --summary ...`
  - `garage experience show --id ...`（JSON pretty-print）
  - `garage experience delete --id ...`（同时清理 `.garage/knowledge/.metadata/index.json` 中的引用）
- **`cli:` 命名空间来源标记**让自动路径与手工路径产出物在持久层可被冷读区分（FR-509 + ADR-503）：
  - `garage knowledge add` → front matter `source_artifact: cli:knowledge-add`
  - `garage knowledge edit` → 覆盖为 `source_artifact: cli:knowledge-edit`，**不**触动 publisher 路径写入的 `published_from_candidate` 等元数据
  - `garage experience add` → `record.artifacts[0] = "cli:experience-add"`
  - 命令行中 `grep -l "cli:" .garage/knowledge/**/*.md` 即可一键筛选手工添加路径产出物
- **时间敏感的 ID 自动生成**（FR-508 + ADR-502）：未传 `--id` 时按 `<type>-<YYYYMMDD>-<6 hex>` 生成，hash 输入含秒级时间戳。同一秒重复 add 同 topic+content 会被拒绝（`Entry with id '<id>' already exists`），不会原地覆盖现有 entry。
- **CRUD 闭环对称**：同一 `(type, id)` 可被 `add → show → edit → show → delete → show` 全链路操作；前 5 步退出码 0，最后一步退出码 1。
- **稳定 stdout 标识符常量**（NFR-504 + F004 § 11.5 同模式）：所有 success / failure 文案由模块顶层 `KNOWLEDGE_*_FMT` / `EXPERIENCE_*_FMT` / `ERR_*` 常量产出，便于 Agent 调用方做 stdout 解析。
- **零配置可用**：在全新仓库内 `garage init && garage knowledge add ...` 一行就能成功写入 entry，不需要 platform.json 改动、不需要 Claude Code 在线、不需要先有 session。

### 数据与契约影响

- **零 schema 变更**：`KnowledgeEntry` / `ExperienceRecord` / `KnowledgeStore` / `ExperienceIndex` 公开 API 一字未改（CON-502 / CON-503）。
- **零依赖变更**：`pyproject.toml` 在本 cycle `git diff main..HEAD` 为空（NFR-502 ✓）；新增 CLI 路径仅依赖 stdlib + `garage_os.*`。
- **新增 CLI surface 模块常量**（`src/garage_os/cli.py`）：
  - 7 个成功/失败 stdout 常量：`KNOWLEDGE_ADDED_FMT` / `KNOWLEDGE_EDITED_FMT` / `KNOWLEDGE_DELETED_FMT` / `KNOWLEDGE_NOT_FOUND_FMT` / `KNOWLEDGE_ALREADY_EXISTS_FMT` / `EXPERIENCE_ADDED_FMT` / `EXPERIENCE_DELETED_FMT` / `EXPERIENCE_NOT_FOUND_FMT` / `EXPERIENCE_ALREADY_EXISTS_FMT` / `EXPERIENCE_READ_ERR_FMT`
  - 5 个 stderr 常量：`ERR_NO_GARAGE` / `ERR_CONTENT_AND_FILE_MUTEX` / `ERR_ADD_REQUIRES_CONTENT` / `ERR_FILE_NOT_FOUND_FMT` / `ERR_EDIT_REQUIRES_FIELD`
  - 3 个 source-marker 常量：`CLI_SOURCE_KNOWLEDGE_ADD` / `CLI_SOURCE_KNOWLEDGE_EDIT` / `CLI_SOURCE_EXPERIENCE_ADD`
- **新增 `experience` 二级父 subparser** + `add` / `show` / `delete` 三个子命令；不引入新顶级命令（CON-501）。

### 验证证据

- `pytest tests/ -q` → **451 passed in ~25s**（F004 baseline 414 → +37 个 F005 新增测试，零回归）
- F005 触动模块 mypy 持平 baseline（无新引入错误）
- E2E walkthrough：在干净 `.garage/` 内完成 `add → list → show → edit → show → experience add → experience show → experience delete → status` 全链路，全部 exit 0（详见 `/opt/cursor/artifacts/f005_cli_walkthrough.log`）
- 完整质量链：spec-review r1（需修改）→ r2（通过）→ design-review（通过 4 minor inline-fixed）→ tasks-review（通过 3 minor; F-1 inline-fixed）→ test-review（通过 5 minor; TT3/TT4 supplementary tests added）→ code-review（通过 5 minor; CR-2/CR-4 inline-fixed）→ traceability-review（通过 2 minor）→ regression-gate（通过）→ completion-gate（通过）

### 已知限制 / 后续工作

- **Stage 2 → Stage 3 触发信号尚未达标**：`docs/soul/growth-strategy.md` 的 Stage 3 进入信号包括 "知识库条目 >100"。F005 把"添加"路径从必须经 session 归档触发，修到了"终端 1 行命令即可"，但**实际的 100 条条目仍依赖用户使用频率**。下一个 cycle 是否启动 Stage 3 由 `hf-workflow-router` 在新会话独立判断。
- **`_experience_show` 与 design §3 traceability 文字不严格一致（traceability TZ5 minor）**：handler docstring 已就地说明绕过 `ExperienceIndex.retrieve()` 直接读盘的理由（forward-compat with on-disk schema additions）；design 文档未回流。
- **CON-501 / CON-502 / NFR-502 间接证据（traceability TZ4 minor）**：`pyproject.toml` 空 diff 是机器证据，但 CON-501/502 目前由 code review 人工确认；可在后续 cycle 加契约测试。
- **§ 5 deferred backlog（spec 显式不在本 cycle）**：批量导入 / `experience edit` / `garage knowledge link` / TUI wizard / `garage knowledge export` / `--format json` for show / `source_session` 自动绑定 — 全部由后续 cycle 独立立项。
- **Pre-existing baseline mypy + ruff 警告**：23 个 F002/F003 历史 mypy errors + cli.py 25 个 ruff stylistic warnings + F004 line 541 mypy error — 全部超出 F005 范围，由独立 cycle 治理。F005 新引入的 ruff 增量（21 项 UP045/UP012）与 cli.py 既有代码风格保持一致，未引入新行为问题。

---

## F004 — Garage Memory v1.1（发布身份解耦与确认语义收敛）

- 状态: ✅ 已完成（2026-04-19）
- Workflow Profile: `full`
- Execution Mode: `auto`
- Branch / PR: `cursor/f004-memory-polish-1bde` / [#15](https://github.com/hujianbest/garage-agent/pull/15)
- 关联文档:
  - 规格 `docs/features/F004-garage-memory-v1-1-publication-identity-and-confirmation-semantics.md`
  - 设计 `docs/designs/2026-04-19-garage-memory-v1-1-design.md`（r1）
  - 任务计划 `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md`
  - completion gate `docs/verification/F004-completion-gate.md`
  - regression gate `docs/verification/F004-regression-gate.md`
  - 完整 review 链路：`docs/reviews/{spec,design,tasks,test,code,traceability}-review-F004-memory-v1-1.md`

### 用户可见变化

- **重复发布走 update 链（FR-401）**：同一 candidate 被多次 `accept` / `edit_accept` 时，系统现在会沿用 `KnowledgeStore.update()` 的 `version+=1` 路径，git 历史可读出完整版本链。F003 v1 行为下重复发布会原地覆盖文件且不递增 version，现已修复。
- **Publisher 入口校验前置（FR-402）**：`KnowledgePublisher.publish_candidate(...)` 在入口立即校验 `conflict_strategy`，不再依赖冲突分支命中；调用方误传无效值会立即收到 `ValueError("Allowed: ['abandon', 'coexist', 'supersede']")`。
- **CLI abandon 双路径语义化（FR-403）**：`garage memory review --action=abandon`（主动放弃）与 `--action=accept --strategy=abandon`（因冲突放弃）现在在 confirmation 持久产物 + stdout 文案 + 用户文档 3 个面均可独立识别：
  - `--action=abandon` → confirmation `resolution=abandon` + `conflict_strategy=null` + stdout `"Candidate '...' abandoned without publication attempt"`
  - `--action=accept --strategy=abandon` 命中冲突 → confirmation `resolution=accept` + `conflict_strategy=abandon` + stdout `"Candidate '...' abandoned due to conflict with published knowledge"`
  - `--action=accept --strategy=abandon` 不命中冲突 → 退化为正常 accept publish（与 v1 一致）
  - 详细差异说明见 `docs/guides/garage-os-user-guide.md` 新增的 "Memory review — abandon paths" 段
- **Session memory-extraction-error.json 文件级证据（FR-404）**：`SessionManager._trigger_memory_extraction` 在 archive-time 触发链路任意 phase（`orchestrator_init` / `enablement_check` / `extraction`）失败时，都会在 `.garage/sessions/archived/<session_id>/memory-extraction-error.json` 写入可机器读取的 schema-v1 错误摘要（含 `phase` / `error_type` / `error_message` / `triggered_at`）。session 归档结果保持 `archive_session()=True`；orchestrator 内部 batch-level 错误（`evaluation_summary=extraction_failed`）按 F003 行为继续写入，session 错误文件不重复 batch 信息。
- **F003 KnowledgeStore extra-key 持久化修复**：`KnowledgeStore._entry_to_front_matter()` 之前只持久化 14 个 dataclass 字段，`entry.front_matter` 中的 extra keys（如 publisher 写入的 `supersedes`）从未 make it to disk。本 cycle 按 design § 9 escape hatch 修复：reserved keys 从 dataclass 重建，extras 在末尾合并，兼容 F003 v1 已发布数据。

### 数据与契约影响

- **新增 publisher helper class** `PublicationIdentityGenerator`（`src/garage_os/memory/publisher.py`）：含 `derive_knowledge_id(candidate_id, knowledge_type)` / `derive_experience_id(candidate_id)` 两个纯函数。v1.1 默认实现 = candidate_id 透传，**不破坏 F003 v1 已发布数据**。
- **新增 publisher carry-over contract** `PRESERVED_FRONT_MATTER_KEYS = ("supersedes", "related_decisions")`：在重复发布的 update 路径上自动 carry-over，避免 v1 supersede 链丢失。
- **新增运行时文件**：`.garage/sessions/archived/<session_id>/memory-extraction-error.json`（仅在失败时存在；schema_version=1；旧 session 目录无该文件可正常读取）。
- **CLI surface 新增模块常量**：`MEMORY_REVIEW_ABANDONED_NO_PUB` / `MEMORY_REVIEW_ABANDONED_CONFLICT`（`src/garage_os/cli.py`）。
- **`KnowledgeEntry` / `ExperienceRecord` / `MemoryCandidate` dataclass 字段不变**；`platform.json` schema 不变。

### 验证证据

- `pytest tests/ -q` → **414 passed in ~25s**（F003 baseline 384 → +30 个 F004 新增测试，零回归）
- F004 focused 子集 → `147 passed in ~1s`
- F004 触动文件 mypy 持平 baseline（无新引入错误）
- 完整质量链：spec-review（通过）→ design-review（需修改 → r1 1:1 闭合）→ tasks-review（通过）→ test-review（通过 +2 supplementary tests）→ code-review（通过 +2 docstring 补强）→ traceability-review（通过）→ regression-gate（通过）→ completion-gate（通过）

### 已知限制 / 后续工作

- **Trace 矩阵措辞补强（traceability review TZ5 minor）**：design § 3 / § 9 trace 矩阵未显式登记 KnowledgeStore extra-key 修复（已在 design § 9 escape hatch + 实现交接块 + code-review §5.2 + test-review §4.5A 共 4 处文档化，仅 trace 矩阵措辞机会）。
- **T5 implementation handoff RED 段仅 narrative**（test review TT5 minor）：lint-only 测试，已接受现状。
- **`scripts/benchmark.py` 不补 publisher 专项基准**（ASM-403 已裁决）：当前 `pytest tests/memory/ -q` wall-clock 已能反映回归；如未来用户大量重复发布出现 git diff 噪声升级，可独立立项。
- **CLI `--action=abandon` 仍写 confirmation**：与 design § 10.3 + ADR-403 一致；如要 revisit "abandon 不写 confirmation" 应走 `hf-increment`。
- **Pre-existing baseline mypy 错误**：23 个 F002/F003 历史 mypy 错误超出 F004 范围，由后续 cycle 单独治理。

---

## F003 — Garage Memory（自动知识提取与经验推荐）

- 状态: ✅ 已完成（2026-04-18）
- Workflow Profile: `full`
- Branch / PR: `cursor/f003-quality-chain-3d5f` / [#13](https://github.com/hujianbest/garage-agent/pull/13)
- 关联文档:
  - 规格 `docs/features/F003-garage-memory-auto-extraction.md`
  - 设计 `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
  - 任务计划 `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`
  - completion gate `docs/verification/F003-completion-gate.md`
  - 完整 review 链路：`docs/reviews/{spec,design,tasks,test,code,traceability}-review-F003-*.md`

### 用户可见变化

- **新增 memory 子模块** (`src/garage_os/memory/`)：候选层与正式发布层解耦，提供四类候选（decision / pattern / solution / experience_summary）的存储、提取、确认、发布与冲突探测能力。
- **session 归档自动触发候选提取**：`SessionManager.archive_session()` 在归档完成后自动调用 `MemoryExtractionOrchestrator`。提取失败不阻塞 session 归档，错误以 `evaluation_summary=extraction_failed` batch 写入 `.garage/memory/candidates/batches/`，可冷读。
- **CLI canonical surface — `garage memory review`**：
  - `garage memory review <batch-id>` 查看候选批次摘要
  - `--action accept|edit_accept|reject|batch_reject|defer|abandon|show-conflicts`
  - `--strategy coexist|supersede|abandon` 处理与已发布知识的冲突；`accept` / `edit_accept` 命中相似条目时**强制要求** `--strategy`，不再静默写 supersede（FR-304）
- **`garage run` 主动推荐**：当 `recommendation_enabled=true` 时，每次 `garage run <skill>` 在执行前展示一次推荐摘要（含 `match_reasons`），仅消费正式发布态。
- **正式知识与经验记录扩展**：`KnowledgeEntry` / `ExperienceRecord` 新增 `source_evidence_anchor(s)`、`confirmation_ref`、`published_from_candidate` 等可追溯字段（设计 §11.4）。
- **Feature flag 双开关**：`platform.json` 新增 `memory.extraction_enabled` 与 `memory.recommendation_enabled`，默认两者均为 `false`，关闭时现有 `garage` 主链不回归。

### 数据与契约影响

- 新增运行时目录：
  - `.garage/memory/candidates/batches/`（batch JSON）
  - `.garage/memory/candidates/items/`（candidate markdown + YAML front matter）
  - `.garage/memory/confirmations/`（confirmation JSON）
- 新增 `.garage/config/platform.json` 字段：`memory.extraction_enabled`、`memory.recommendation_enabled`（默认全 `false`，向后兼容）。
- `KnowledgeStore` / `ExperienceIndex` 接受额外可选字段；旧 entry 在缺字段时仍可读，未做强制迁移。

### 验证证据

- `pytest tests/ -q` → `384 passed in ~24s`（基线 369 → 376 → 384，每轮回流 fresh evidence，零回归）
- F003 任务范围聚焦验证 → `145 passed in ~16s`
- 完整质量链：test-review r1（需修改）→ test-review r2（通过）→ test-review r3 增量（通过）→ code-review r1（需修改）→ code-review r2（通过）→ traceability-review（通过，6 维度 ≥7/10）→ regression-gate（通过）→ completion-gate（通过）

### 已知限制 / 后续工作

- **延后接受（USER-INPUT）**：`KnowledgePublisher` 当前用 `candidate_id` 直接作为 `KnowledgeEntry.id`。同一候选重复 `accept` / `edit_accept` 会原地覆盖前一次发布，不触发 `KnowledgeStore.update()` 的版本递增链路。spec / design §11.4 未硬要求"必须解耦"，此项在 `code-review r1 finding 5` → `code-review r2` → `traceability-review TZ5` → `completion-gate` 中均**显式延后**，建议下一个 cycle 作为独立 task 推进（带版本后缀或独立 ID）。
- **延后处理（LLM-FIXABLE，行为变更类）**：
  - `KnowledgePublisher.publish_candidate` 仅在 `similar_entries` 非空时校验 `VALID_CONFLICT_STRATEGIES`，建议在入口处提前校验
  - CLI `--action=abandon` 与 `--action=accept --strategy=abandon` 语义重叠，待产品侧确认是否需要差异化
  - `SessionManager._trigger_memory_extraction` 仍用 `logger.warning` 兜底（FR-307 文件级证据由 orchestrator batch 文件承担），如需 session 侧双写可独立任务推进
- 本轮 finalize 已顺手清理：移除 `extraction_orchestrator.py:68` 已 stale 的 `# pragma: no cover` 注释；为 `.garage/config/platform.json` 补 `memory` 块；为 T2-T9 testDesignApproval 治理路径写 merge note (`docs/approvals/F003-T2-T9-test-design-merge-note.md`)。

---

## Previous Cycles

- **F002 — Garage Live**：✅ 已完成（CLI + 真实 Claude Code 集成，436 测试通过）
- **F001 — Garage Agent OS Phase 1**：✅ 已完成（T1-T22，416 测试通过）
