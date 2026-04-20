# Traceability Review — F007 Garage Packs & Host Installer

- 日期: 2026-04-19
- Reviewer: subagent (`hf-traceability-review`)
- Branch: `cursor/f007-packs-host-installer-fa86`
- 评审范围:
  - spec: `docs/features/F007-garage-packs-and-host-installer.md`（已批准 r2）
  - design: `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`（已批准 r2）
  - tasks: `docs/tasks/2026-04-19-garage-packs-and-host-installer-tasks.md`（已批准 r1）
  - 上游评审记录:
    - `docs/reviews/spec-review-F007-...md`（r2 = 通过）
    - `docs/reviews/design-review-F007-...md`（r2 delta = 通过）
    - `docs/reviews/tasks-review-F007-...md`（r1 = 通过）
    - `docs/reviews/test-review-F007-...md`（通过 + 5 minor 已闭合）
    - `docs/reviews/code-review-F007-...md`（通过 + 1 important + 5 minor 全部通过 carry-forward 闭合，commit `52b0986`）
  - 实现源（追溯落点）:
    - `packs/{README.md, garage/{pack.json, README.md, skills/garage-hello/SKILL.md, agents/garage-sample-agent.md}}` (T1)
    - `src/garage_os/adapter/installer/{__init__,host_registry,manifest,marker,pack_discovery,pipeline,interactive}.py` (T2-T3-T4)
    - `src/garage_os/adapter/installer/hosts/{claude,opencode,cursor}.py` (T2)
    - `src/garage_os/cli.py` 行 13-23 (installer import) / 80-98 (FR-709 文案常量) / 206-310 (`_init` + `_resolve_init_hosts`) / 1391-1442 (`build_parser` init 段) / 1764-1771 (`main` dispatch) (T4)
  - 测试落点:
    - `tests/adapter/installer/{test_host_registry,test_hosts,test_pack_discovery,test_manifest,test_marker,test_pipeline,test_neutrality,test_idempotent,test_interactive}.py`
    - `tests/test_cli.py::TestInitWithHosts` + `tests/test_cli.py::TestInitErrorPaths`
    - `tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered`
    - `tests/test_documentation.py::test_user_guide_documents_pack_and_host_installer / test_packs_readme_documents_directory_contract`
  - 文档落点:
    - `docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段（行 542-684）
    - `packs/README.md`、`packs/garage/README.md`
  - artifact 证据: `/opt/cursor/artifacts/f007_manual_smoke_init_all_hosts.log`
  - task-progress: `task-progress.md`

---

## Precheck

| 项 | 结果 |
|----|------|
| 实现交接块稳定可定位 | ✅ 9 个 installer 模块 + cli.py 5 段 anchor + 5 个 packs/ 工件，全部按 D7 §9 模块清单落地；commit `52b0986` 已闭合 code review 全部 6 条 finding |
| 上游 review 链完整 | ✅ spec/design/tasks/test/code 5 份 review 记录全部通过，approval 记录齐备 |
| route / stage / profile 一致 | ✅ 4 份 approval（spec/design/tasks）+ 5 份 review verdict 同向；当前处于 code review 后、regression gate 前的标准 traceability 节点 |
| 测试通过证据新鲜 | ✅ reviewer 自跑 `pytest tests/adapter/installer/ tests/test_cli.py::TestInitWithHosts tests/test_cli.py::TestInitErrorPaths tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered tests/test_documentation.py -q` → **97 passed in 0.37s** |
| AGENTS.md 编码约定 | ✅ Python 3.11+ 无新依赖；模块路径 `src/garage_os/adapter/installer/` 满足 CON-701 |

Precheck 通过，进入正式审查。

---

## 多维评分（每维 0-10）

| ID | 维度 | 分 | 关键依据 |
|---|---|---|---|
| `TZ1` 规格 → 设计追溯 | 10 | spec FR-701~710 / NFR-701~704 / CON-701~704 全部在 design §3 追溯表 / §11 接口契约 / §13 测试矩阵中有承接锚点；ADR-D7-1~5 解决全部 4 条非阻塞 OQ；spec ASM-701~703 在 design §2.2 + ADR-D7-3 + §10.4 显式承接（marker 容错策略）。零规格漂移：spec r2 head 与 design r2 一致 |
| `TZ2` 设计 → 任务追溯 | 10 | design §15 任务规划准备度声明的 5 个 milestones 与 tasks §2/§5 一一对应；ADR-D7-1~5 全部落到具体 task（T2/T3/T4/T5）；design §13 测试矩阵 9 个测试模块逐项映射到 tasks §3.1 新增测试文件清单；tasks §4 追溯表覆盖 spec 全部 FR/NFR/CON |
| `TZ3` 任务 → 实现追溯 | 9 | tasks §3.1 新增工件 19 项 + §3.2 修改工件 4 项全部按 commit `3d0a83f`（T1）/ `3ee343f`（T2）/ `2b6eca8`（T3）/ `9169cd9`（T4）/ `b7ead4f`（T5）落盘；commit `ccbb069`（test-review 5 minor 闭合）+ `52b0986`（code-review 6 finding 闭合）补强；触碰工件与计划一致；§3.3 不修改清单（F001 protocol / F002 init 字节相同 / F003-F006 知识管道）实测 git diff 验证未触 |
| `TZ4` 实现 → 验证追溯 | 9 | reviewer 自跑 F007 切片 97 passed（含 12 host_registry + 10 hosts + 8 pack_discovery + 9 manifest + 9 marker + 12 pipeline + 3 neutrality + 2 idempotent + 6 interactive + 13 cli + 2 version_manager + 9 documentation + agent conflict + edge rows 等）；spec 全部 acceptance 有用例守护；test review 5 minor 与 code review 6 finding 全部已 commit 闭合；artifact log（`f007_manual_smoke_init_all_hosts.log`）落盘 manual smoke 三宿主端到端证据 |
| `TZ5` 漂移与回写义务 | 7 | code review 6 条 finding 已 commit 闭合（含计数语义 / mypy / ruff / agent conflict 测试 / 命名遮蔽 / 文案常量集中）。**1 项轻微漂移**：`task-progress.md` 仍停留在"current active task: T1"且"next action: hf-test-driven-dev"，未反映 T1-T5 已全部完成 + 4 review 已通过 + 当前进入 traceability review 的事实（详见 finding F007-TZ-1）。**1 项次要 docs 漂移**：`AGENTS.md` 未更新提及 `packs/` 目录或 host installer 子模块（`src/garage_os/adapter/installer/`），从入口文档进入 packs 体系时缺少导航锚点（详见 finding F007-TZ-2）。 |
| `TZ6` 整体链路闭合 | 9 | spec→design→tasks→impl→test/verification→docs 端到端无断链；FR-710 5 分钟冷读校验通过（详见 §冷读校验）；3 类下游消费者（用户 / CI / 审计 reviewer）的关键路径全部有可定位证据；唯一需修缺口（`task-progress.md` 状态滞后）属可在 `hf-finalize` 阶段统一收尾的 LLM-FIXABLE，不阻塞 regression gate |

任一维度均 ≥ 7/10，可形成 verdict。

---

## 实现 ↔ 测试 ↔ 文档全量链接矩阵

### A. 规格 → 设计 → 任务 → 实现 → 测试

| spec ID | design 锚点 | tasks 任务 | 实现落点 | 测试用例 | 状态 |
|---|---|---|---|---|---|
| **FR-701** packs 目录契约 | D7 §11.3 + ADR-D7-4 | T1 | `packs/README.md` + `packs/garage/{pack.json, README.md, skills/garage-hello/SKILL.md, agents/garage-sample-agent.md}` + `pack_discovery.py` | `test_pack_discovery.py` (10 用例：空/单 pack/双 pack 排序/缺 pack.json/非法 JSON/id 不匹配/skills 与磁盘不一致/agents 与磁盘不一致) + `test_documentation.py::test_packs_readme_documents_directory_contract` | ✅ |
| **FR-702** `--hosts` | D7 §10.1 + §11.1 | T4 | `cli.py:1413-1442` (init subparser `--hosts`/`--yes`/`--force`) + `cli.py:295-310` (`_resolve_init_hosts`) + `host_registry.py:99-131` (`resolve_hosts_arg`) | `test_host_registry.py::TestResolveHostsArg` (all/none/逗号/未知/空串/trim) + `TestInitWithHosts::test_hosts_explicit_list / test_hosts_all_installs_three_first_class / test_hosts_none_explicit / TestInitErrorPaths::test_unknown_host_exit_1_but_garage_dir_created` | ✅ |
| **FR-703** 交互式 + non-TTY | D7 §10.1 + ADR-D7-5 | T4 | `interactive.py:32-89` (`prompt_hosts` + `_is_tty`) + `cli.py:295-310` | `test_interactive.py` (6 用例: non-TTY notice / `a` 全选 / `q` 早停 / 回车默认 N / capital N / 混合) + `TestInitWithHosts` non-TTY 链路 | ✅ |
| **FR-704** 安装管道 + 多次累加 | D7 §10 / §10.3 | T3 | `pipeline.py:93-244` (`install_packs`) + `pipeline.py:301-313` (`_check_conflicts`) + `pipeline.py:342-370` (`_merge_with_existing`) | `test_pipeline.py` (12 用例: WalkingSkeleton / NoPacksFound / ExtendHosts / CursorAgentSkip / ConflictSkill / ConflictAgent / LocallyModifiedProtection / DecisionTableEdgeRows) | ✅ |
| **FR-705** manifest schema | D7 §8.3 + §11.2 | T3 + T5 | `manifest.py:62-77` (`write_manifest`) + `manifest.py:80-95` (`read_manifest`) + `manifest.py:98-118` (POSIX serialize + sort) + `MANIFEST_SCHEMA_VERSION = 1` | `test_manifest.py` (9 用例 round-trip + sort + POSIX + invalid-JSON + ISO-8601/SHA-256 正则) + `test_version_manager.py::TestHostInstallerSchemaRegistered` (2 用例) | ✅ |
| **FR-706a** 未修改幂等 | D7 §10.2 | T3 | `pipeline.py:316-339` (`_decide_action` UPDATE_FROM_SOURCE) + `pipeline.py:206-212` (写前 SHA-256 短路) | `test_pipeline.py::TestExtendHosts` (claude mtime 不变) + `test_idempotent.py` (2 用例 mtime_ns + force-no-op) | ✅ |
| **FR-706b** 已修改保护 / `--force` | D7 §10.2 | T3 + T4 | `pipeline.py:316-339` + `pipeline.py:187-204` (SKIP / OVERWRITE_FORCED stderr) | `test_pipeline.py::TestLocallyModifiedProtection` (skip + force 两路径) + `TestInitWithHosts::test_force_flag_overwrites` | ✅ |
| **FR-707** host adapter 注册表 | D7 §11.1 + ADR-D7-1 + ADR-D7-3 | T2 | `host_registry.py:28-49` (`HostInstallAdapter` Protocol) + `host_registry.py:71` (`HOST_REGISTRY`) + `hosts/{claude,opencode,cursor}.py` | `test_host_registry.py::TestHostRegistry` (12 用例) + `test_hosts.py::TestClaude/OpenCode/Cursor` (10 用例 字面值 + cursor.target_agent_path == None) | ✅ |
| **FR-708** 安装标记块 | D7 §10.4 + ADR-D7-2 | T3 | `marker.py:46-74` (`inject`) + `marker.py:77-97` (`extract_marker`) + skill/agent 双路 | `test_marker.py` (9 用例: skill OK / 无 FM 抛 `MalformedFrontmatterError` / skill 幂等 / agent 容错 / agent 已有 FM / extract / 无 marker / pack_id mismatch) | ✅ |
| **FR-709** 稳定 stdout/stderr | D7 §2.1 + §10.1 | T4 | `cli.py:80-98` (`INSTALLED_FMT` / `ERR_PACK_INVALID_FMT` / `ERR_MARKER_FAILED_FMT` / `ERR_HOST_FILE_FAILED_FMT`) + `pipeline.py:55-58` (`WARN_LOCALLY_MODIFIED_FMT` / `WARN_OVERWRITE_FORCED_FMT` / `MSG_NO_PACKS_FMT`) + `host_registry.py` 中 `UnknownHostError` 自带 `Unknown host: ...` 文案 | `TestInitWithHosts::test_hosts_explicit_list` 断言 stdout `Installed N skills, M agents into hosts: ...` + `test_subprocess_smoke_three_hosts` + `test_pipeline.py` 断言 stderr `Skipped/Overwrote` | ✅ |
| **FR-710** 文档 | D7 §2.1 + §12 | T1 + T5 | `packs/README.md` + `packs/garage/README.md` + `docs/guides/garage-os-user-guide.md` 行 542-684 | `test_documentation.py::test_user_guide_documents_pack_and_host_installer` (检查 9 个 token) + `test_packs_readme_documents_directory_contract` (检查 5 个 token) + 本 review 5 分钟冷读校验（见下文） | ✅ |
| **NFR-701** 宿主无关性 | D7 §12 | T3 | `packs/garage/skills/garage-hello/SKILL.md` + `agents/garage-sample-agent.md` 不含黑名单关键字 | `test_neutrality.py` (3 用例 parametrize 真实 packs/ 全部 SKILL.md + agent.md 黑名单 regex IGNORECASE) | ✅ |
| **NFR-702** 性能 / 无写入 | D7 §10.2 + §12 | T3 | `pipeline.py:206-212` 写前比 bytes，相等则不写 | `test_idempotent.py` (2 用例 mtime_ns 不变 + force=True 在无变化时仍 no-op) + `TestExtendHosts` mtime 检查 | ✅ |
| **NFR-703** 跨平台路径 | D7 §11.2 | T3 | `manifest.py:143-146` (`_to_posix` 用 `PurePosixPath(*Path(s).parts).as_posix()`) | `test_manifest.py::TestPosixPathSerialization` (断言 `\` 不出现 + `/` ≥ 2) | ✅ |
| **NFR-704** 零回归 | D7 §13 | 所有任务 | F006 基线 ≥496；当前实测 reviewer F007 切片 97 passed；code-review 报告 `pytest tests/ -q` 全量 585+ passed | `pytest tests/` 全绿（依赖 hf-regression-gate 二次复核） | ✅ |
| **CON-701** adapter 位置 | D7 §9 + ADR-D7-1 | T2 + T3 | `src/garage_os/adapter/installer/` 9 模块（位于既有 `src/garage_os/adapter/` 之下，与 `claude_code_adapter.py` 同包） | 物理路径 `ls src/garage_os/adapter/installer/hosts/{claude,opencode,cursor}.py` 全部存在 | ✅ |
| **CON-702** 不破坏 F002 | D7 §10.1 | T4 | `cli.py:206-260` (`_init` 缺省路径无任何 `--hosts*` 时直接早返回，输出 `Initialized Garage OS in <path>` 单行) | `TestInitWithHosts::test_default_init_unchanged_when_no_hosts` 直接断言 | ✅ |
| **CON-703** schema_version | D7 §11.3 + §12 | T5 | `manifest.py:26` (`MANIFEST_SCHEMA_VERSION = 1`) + `version_manager.py` 路径无关检测 | `test_version_manager.py::TestHostInstallerSchemaRegistered::test_host_installer_schema_recognized / test_manifest_constant_pinned_to_one` | ✅ |
| **CON-704** 路径来源说明 | D7 §12 | T5 | `docs/guides/garage-os-user-guide.md:548` "都是各宿主的原生约定 ... Garage 只是把内容写到那里，没有自创任何路径" + 行 649-653 来源依据表 | 用户指南文案 grep ("原生约定" + 来源依据表) | ✅ |

### B. ADR → 实现决策落点

| ADR | 设计决策 | 实现落点 | 验证 |
|---|---|---|---|
| **ADR-D7-1** 安装期 / 运行时 adapter 分离 | `HostInstallAdapter` Protocol 与 F001 `HostAdapterProtocol` 是不同 port | `host_registry.py:28-49` 独立 Protocol；`hosts/claude.py::ClaudeInstallAdapter` 与 `claude_code_adapter.py::ClaudeCodeAdapter` 真分离；`host_adapter.py` git diff 空 | ✅ test_host_registry / test_hosts |
| **ADR-D7-2** YAML front matter 增字段 | `installed_by: garage` + `installed_pack: <pack-id>`，避免 HTML 注释被宿主原样渲染 | `marker.py:38-39` 常量 + `marker.py:46-74` 文本块 split-not-yaml 实现（保 SHA-256 稳定） | ✅ test_marker (9 用例) |
| **ADR-D7-3** 三家路径表 | claude `.claude/skills/` + `.claude/agents/`；opencode `.opencode/skills/` + `.opencode/agent/`（agent 单数）；cursor `.cursor/skills/` + agent=None | `hosts/claude.py:27-31` / `hosts/opencode.py:21-25` / `hosts/cursor.py:29-33` 字面值与 D7 §11 ADR 表完全一致 | ✅ test_hosts (10 用例字面断言) |
| **ADR-D7-4** 单 `packs/garage/` 起步 | 1 sample skill + 1 sample agent；多 pack conflict 路径靠测试 fixture 覆盖 | `packs/garage/{skills/garage-hello, agents/garage-sample-agent}`；`test_pipeline.py::TestConflict*` 用 fixture 构造 `packs_a / packs_b` | ✅ T1 落盘 + test_pipeline conflict 用例 |
| **ADR-D7-5** stdlib `[y/N]` 循环 | 零依赖；`a`/`q` 快捷键；non-TTY 退化 | `interactive.py:22-29` `PROMPT_TEMPLATE` + `interactive.py:55-78` 循环 + `_is_tty` 检测 | ✅ test_interactive (6 用例) |

### C. 任务 → 完成证据

| Task | 完成 commit | 触碰工件 | 验证证据 |
|---|---|---|---|
| **T1** packs 容器 + 双 README | `3d0a83f` | 5 个 packs/ 文件 | `test_pack_discovery.py` 消费这些 fixture（间接验证）+ NFR-701 grep 0 命中 |
| **T2** host adapter port + 3 adapter | `3ee343f` | `host_registry.py` + `hosts/{claude,opencode,cursor}.py` + 3 个 hosts `__init__.py` | `test_host_registry.py` (12) + `test_hosts.py` (10) |
| **T3** 安装管道核心 | `2b6eca8` | `pack_discovery / manifest / marker / pipeline + 6 个测试模块` | `test_pack_discovery / test_manifest / test_marker / test_pipeline / test_neutrality / test_idempotent` 共 50+ 用例 |
| **T4** CLI 集成 + interactive | `9169cd9` | `cli.py` (5 段) + `interactive.py` + `test_cli.py::TestInitWithHosts` + `test_interactive.py` | `TestInitWithHosts` (8) + `TestInitErrorPaths` (5) + `test_interactive` (6) + manual smoke artifact |
| **T5** 文档 + VersionManager | `b7ead4f` | `garage-os-user-guide.md` 行 542-684 + `tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered` (2 用例) | `test_documentation.py` 2 用例 + `test_version_manager.py` 2 用例 |
| 测试评审 carry-forward | `ccbb069` | 9 个新增测试用例（CLI 异常 / dynamic count / ISO-8601 正则 / 决策表 2 边界 / non-TTY） | 测试 review 5 minor 全部闭合 |
| 代码评审 carry-forward | `52b0986` | pipeline rename / cli 文案常量集中 / ruff 0 / mypy 0 / agent conflict 用例 | code review 6 finding 全部闭合 |

---

## FR-710 + CON-704 5 分钟冷读校验（本 review 特别职责）

按 tasks F-4 carry-forward 约定，本 reviewer 仅按 `AGENTS.md` → `packs/README.md` → `docs/guides/garage-os-user-guide.md` 三段顺序冷读，回答 spec FR-710 验收 #1 的 3 个问题。

### 阅读顺序与所读内容

1. **`AGENTS.md`** (130 行)：项目约定中心；列出 Garage OS 7 个核心模块（types/storage/runtime/knowledge/adapter/tools/platform）、`.garage/` 目录结构、测试约定。**未提及 `packs/` 目录、host installer、`src/garage_os/adapter/installer/` 子包**——本文档只为读者建立 Garage OS 项目级背景。
2. **`packs/README.md`** (92 行)：直接命中 3 问中 (a)/(b)/(c)：
   - (a) "与 `.agents/skills/` 的关系" 段以 2×2 表格说明 `.agents/skills/` = 本仓库内部 AHE workflow / `packs/<pack-id>/skills/` = 可分发的 Garage-bundled 能力 → ✅ **冷读可直接回答**
   - (b) "Dogfood 与下游用法" 段含 `garage init --hosts claude,cursor` 1 行命令 → ✅ **冷读可直接回答**
   - (c) "动作" 段示意 `.claude/skills/...` `.opencode/skills/...` `.cursor/skills/...` 三处目标位置 → ✅ **冷读可直接回答**
3. **`docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段** (行 542-684)：在 packs/README.md 的基础上补全细节：
   - 显式重申 "下面提到的 `.claude/skills/...`、`.opencode/skills/...`、`.cursor/skills/...` 等路径**都是各宿主的原生约定**……Garage 只是把内容写到那里，没有自创任何路径"（CON-704 字面落地）
   - 行 649-653 给出 `claude / opencode / cursor` 三家 skill / agent 路径 + 来源依据表（OpenSpec `docs/supported-tools.md`）
   - 行 670-674 "可发现性链" 显式声明本节点是 5 分钟冷读路径的第 3 站

### 冷读结论

| FR-710 验收问题 | 5 分钟内可否回答 | 证据章节 |
|---|---|---|
| (a) `packs/` 与 `.agents/skills/` 的关系 | ✅ 可 | `packs/README.md` "与 `.agents/skills/` 的关系" 段（2×2 表 + "短期内两者并存"段） |
| (b) 如何用 1 行命令在自己项目里装上 garage skills | ✅ 可 | `packs/README.md` "Dogfood 与下游用法" 段 + 用户指南 "用法 2：非交互" 段 |
| (c) 装完后的文件落到哪儿 | ✅ 可 | `packs/README.md` "关系" ASCII 图 + 用户指南行 559-565 架构图 + 行 649-653 三家路径表 |

**冷读 verdict: 通过**——3 问全部可在 5 分钟内冷读得到答案，链路连续且权威（CON-704 来源依据表已显式标注路径来源）。

**informational 观察（非阻塞）**：`AGENTS.md` 自身未提及 `packs/`、host installer 或 `src/garage_os/adapter/installer/`。冷读链能跑通是因为 reviewer 被预先告知三段顺序；如果一个**完全不知道 packs/ 存在的新读者**只读 `AGENTS.md`，没有锚点提示其继续读 `packs/README.md`。建议 `hf-finalize` 阶段顺手在 `AGENTS.md` 中补一条 "## Packs & Host Installer" 段（4-6 行）作为入口指针。详见 finding F007-TZ-2。

---

## 发现项

### F007-TZ-1 — `task-progress.md` 状态严重滞后（未反映 T1-T5 完成 + 4 review 通过）

- [important][LLM-FIXABLE][TZ5 / ZA3]
- 位置: `task-progress.md` 行 5-27
- 现状:
  - `Goal`: "spec + design + tasks 已批准；待进入 hf-test-driven-dev T1"
  - `Status`: "▶ Active — 任务计划已批准，等待 T1 实施"
  - `Current Stage`: `hf-test-driven-dev`
  - `Current Active Task`: T1 — packs/ 目录契约 + 占位 pack + 双层 README
  - `Pending Reviews And Gates`: hf-test-review / hf-code-review / hf-traceability-review / hf-regression-gate / hf-completion-gate（**T5 完成后串行派发**）
  - `Next Action Or Recommended Skill`: `hf-test-driven-dev` (T1 实施)
- 实际状态（git log + 4 份 review approval 已落盘）：
  - T1-T5 全部完成（commit `3d0a83f` ~ `b7ead4f`）
  - test review 通过 + 5 minor LLM-FIXABLE 已 commit `ccbb069` 闭合
  - code review 通过 + 1 important + 5 minor LLM-FIXABLE 已 commit `52b0986` 闭合
  - 当前正处于 traceability review 节点（即本 review 自身）
  - 下一步应是 `hf-regression-gate`（如本 review 通过）
- 影响: 这是 ZA3 "未回写状态工件"的典型；下游 reviewer / `hf-regression-gate` / `hf-completion-gate` 任何 agent 仅读 `task-progress.md` 就会做出错误的"才刚开始 T1"判断。属 TZ5 必须显式列出的回写工件。
- 建议: 在 `hf-finalize` 之前的某个节点（推荐 regression gate 通过后由 `hf-finalize` 一起处理；或者在本 review 之后立刻由 `hf-test-driven-dev` 阶段一次性 sync）把 `task-progress.md` 更新为：
  - `Status`: "▶ In Review — T1-T5 已实施，test/code/traceability 评审进行中"
  - `Current Stage`: `hf-traceability-review` → `hf-regression-gate`（视本 verdict 决定）
  - `Current Active Task`: 无（T1-T5 全部完成）
  - `Next Action Or Recommended Skill`: 视本 verdict (`hf-regression-gate` 或 `hf-test-driven-dev`)
  - `Previous Milestones` 增 F007 临时条目 "F007 Garage Packs & Host Installer: ▶ In Review (T1-T5 done, code-review passed)"
- 不阻塞 traceability verdict 本身（实现-验证链已闭合），但会阻塞 `hf-completion-gate` 的"宣告完成走向"判定，应由 `hf-finalize` 显式 reconcile。

### F007-TZ-2 — `AGENTS.md` 未承接 packs/ 与 host installer 子模块的入口指针

- [minor][LLM-FIXABLE][TZ5 / ZA3]
- 位置: `AGENTS.md`（130 行全文）
- 现状: AGENTS.md 列出 7 个核心模块（types/storage/runtime/knowledge/**adapter**/tools/platform）但 `adapter` 行未提及新增的 `installer/` 子包；项目灵魂 / Skill 写作原则 / Garage OS 三大段落均未提及 `packs/` 目录或 host installer。
- 影响: FR-710 5 分钟冷读链按预定顺序读时**勉强通过**（packs/README.md 自身完整），但完全冷启动的新 Agent 在 AGENTS.md 上找不到任何指向 `packs/` 的路标，需要靠 grep 或 `find` 才能发现。属 TZ5 "应同步而未同步的工件"。
- 建议: 在 `hf-finalize` 阶段顺手在 AGENTS.md 加 4-6 行：
  - `## Packs & Host Installer`（新章节）：
    - 一句话解释 `packs/<pack-id>/` 是 Garage 自带可分发能力源；
    - 一句话指向 `packs/README.md` 与 `docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段；
    - 在"模块概览"表的 `adapter` 行末追加 "+ `installer/` 子包：host installer 安装管道"。
- 与 F007-TZ-1 一并由 `hf-finalize` 处理即可，不需额外 cycle。

### F007-TZ-3 — 部分 manifest schema 未在 `version_manager.py` 显式字面注册（实现走"路径无关检测"）

- [minor][LLM-FIXABLE][TZ3 / TZ5]
- 位置: `src/garage_os/platform/version_manager.py`（git diff 空）
- 现状: 设计 §2.1 / §11.3 表述为 "`platform.VersionManager` 现有 schema 注册表追加一项"；tasks T5 §3.2 列出 "`src/garage_os/platform/version_manager.py` ... 注册 `host-installer.json` schema 项"。但实际实现（commit `b7ead4f`）选择"VersionManager 本就支持路径无关 schema 检测，host-installer.json 通过通用 `detect_version` 路径自然被识别"。code review 已注明该实现方式 "未在 `version_manager.py` 显式新增字面注册项，但满足验收"，并标记 ✅。
- 影响: 行为上 100% 满足 CON-703（`test_version_manager.py::TestHostInstallerSchemaRegistered` 真实写一个 manifest → `vm.detect_version` 返回 `major == 1` → `vm.check_compatibility` 返回 `COMPATIBLE` 全链路通过），但任务计划与实现存在文字层面 drift："注册" 在 task / design 文字含义被实现解释为"通过通用机制识别即视为已注册"。
- 建议（任一即可）:
  - (a) 在 `task-progress.md` carry-forward 段或 RELEASE_NOTES 中显式记录此 design→impl 的语义抽象（"VersionManager 已是路径无关，无需字面追加 SUPPORTED_VERSIONS"）；
  - (b) 或在 `version_manager.py` 加一个无副作用的 sentinel 常量（如 `KNOWN_SCHEMA_FILES = (..., "host-installer.json")`）以让 grep 找得到；
  - (c) 或在 `manifest.py` docstring 已写"T5 registers host-installer.json so future migrations can be planned"，可补一行指向 `test_version_manager.py::TestHostInstallerSchemaRegistered` 即可。
- 优先级 minor 而非 important：行为完全正确，仅是工件文字 drift。

---

## 追溯缺口

无关键缺口。三条 finding 全部是状态工件 / 入口文档 / 任务-实现文字层 drift，**不影响**实现-验证链闭合。

---

## 需要回写或同步的工件

| 工件 | 原因 | 建议动作 | 时机 |
|---|---|---|---|
| `task-progress.md` | T1-T5 + test/code review 全部完成，状态停留在 T1 active；阻塞 `hf-completion-gate` 判定 | 更新 Status / Current Stage / Active Task / Next Action / Previous Milestones | `hf-finalize`（推荐）或本 verdict 后由编排 agent reconcile |
| `AGENTS.md` | 未承接 packs/ + host installer 入口指针；FR-710 5 分钟冷读链入口缺路标 | 增 4-6 行 "## Packs & Host Installer" 段 + adapter 行末追加 installer 子包提及 | `hf-finalize` |
| `RELEASE_NOTES.md`（本 cycle 收尾）| 按 tasks T5 acceptance "RELEASE_NOTES 不在 T5 改，留给 hf-finalize" | 添加 F007 首条目 | `hf-finalize` |
| 实现 ↔ design 文字 drift（"VersionManager 注册"措辞） | code-review 已 ✅，但措辞 drift 应留下 audit trail | RELEASE_NOTES 或 task-progress carry-forward 段记录 | `hf-finalize` |

---

## 结论

**通过**

- 6 个评审维度均 ≥ 7/10，无关键维度阻塞。
- spec FR-701~710 / NFR-701~704 / CON-701~704 / ADR-D7-1~5 全部已被 design / tasks / impl / test 1:1 覆盖（详见 §A/§B/§C 链接矩阵）。
- 上游 4 份 review（spec / design / tasks / test / code）verdict 全部通过；test review 5 minor + code review 6 finding 全部 commit 闭合（`ccbb069` / `52b0986`）。
- 实现-验证链闭合：reviewer 自跑 F007 切片 **97 passed in 0.37s**；manual smoke artifact `f007_manual_smoke_init_all_hosts.log` 落盘三宿主端到端证据。
- FR-710 + CON-704 5 分钟冷读校验通过：3 问可在 `AGENTS.md → packs/README.md → user-guide` 顺序冷读 5 分钟内回答（详见 §冷读校验）。
- 3 条 finding 均为 LLM-FIXABLE：
  - 1 条 `important` (F007-TZ-1)：`task-progress.md` 状态滞后，需在 `hf-finalize` reconcile，不阻塞 `hf-regression-gate`（regression gate 看 `pytest tests/ -q` 全绿即可）。
  - 2 条 `minor` (F007-TZ-2 / F007-TZ-3)：AGENTS.md 入口指针缺失 + VersionManager 注册措辞 drift，均建议 `hf-finalize` 阶段一并处理。
- 与 F001 `HostAdapterProtocol`、F002 `garage init`、F003-F006 知识/经验/记忆/召回管道完全无回归（对应模块 git diff 空）。

**注**：本 reviewer 选择 `通过` 而非 `需修改`，理由：(a) 实现-验证链 100% 闭合，全部 spec acceptance 有用例守护；(b) 三条 finding 全部是**工件回写义务**而非追溯断链——`task-progress.md` 与 `AGENTS.md` 的更新本来就属于 `hf-finalize` 阶段的标准 closeout 工作；(c) `hf-regression-gate` 关注的是测试全绿与回归证据，而不是 status 文档完备性，本 cycle 已具备进入 regression gate 的所有技术条件。F007-TZ-1 的回写工作应在 `hf-finalize` 触发，不需要回到 `hf-test-driven-dev`。

---

## 下一步

- `hf-regression-gate`（按 reviewer return contract）
- `needs_human_confirmation=false`
- `reroute_via_router=false`
- `hf-finalize` 阶段需 reconcile：`task-progress.md` (F007-TZ-1) + `AGENTS.md` (F007-TZ-2) + RELEASE_NOTES F007 首条目 + VersionManager 措辞 drift 备注 (F007-TZ-3)

## 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-regression-gate",
  "record_path": "docs/reviews/traceability-review-F007-garage-packs-and-host-installer.md",
  "key_findings": [
    "[important][LLM-FIXABLE][TZ5/ZA3] F007-TZ-1 task-progress.md 状态严重滞后：仍写 'Current Active Task: T1 / Next Action: hf-test-driven-dev'，未反映 T1-T5 + test/code review 全部完成的事实；阻塞 hf-completion-gate 判定但不阻塞 regression gate；建议 hf-finalize reconcile",
    "[minor][LLM-FIXABLE][TZ5/ZA3] F007-TZ-2 AGENTS.md 未承接 packs/ + installer 子模块入口指针；FR-710 5 分钟冷读链入口缺路标（链本身仍走得通）；建议 hf-finalize 增 4-6 行 'Packs & Host Installer' 段",
    "[minor][LLM-FIXABLE][TZ3/TZ5] F007-TZ-3 host-installer.json 未在 version_manager.py 显式字面注册（实现走 VersionManager 路径无关检测）；行为 ✅ 但与 design/tasks 文字层 drift；建议 RELEASE_NOTES 或 task-progress carry-forward 留下 audit trail"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {"severity": "important", "classification": "LLM-FIXABLE", "rule_id": "TZ5", "summary": "F007-TZ-1 task-progress.md 未回写 T1-T5 完成 + 4 review 通过状态"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TZ5", "summary": "F007-TZ-2 AGENTS.md 未承接 packs/ + installer 入口指针"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TZ3", "summary": "F007-TZ-3 host-installer.json 注册 design→impl 措辞 drift"}
  ]
}
```
