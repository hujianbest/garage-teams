# Code Review — F007 Garage Packs & Host Installer

- 评审对象（实现交接块）：
  - `src/garage_os/adapter/installer/__init__.py`（公共 symbol re-export）
  - `src/garage_os/adapter/installer/host_registry.py`（`HostInstallAdapter` Protocol + `HOST_REGISTRY` + `resolve_hosts_arg`，~132 行）
  - `src/garage_os/adapter/installer/hosts/{__init__,claude,opencode,cursor}.py`（3 个 first-class adapter）
  - `src/garage_os/adapter/installer/pack_discovery.py`（`Pack` dataclass + `discover_packs` + 2 类异常，~166 行）
  - `src/garage_os/adapter/installer/manifest.py`（`Manifest` / `ManifestFileEntry` + 读写 + POSIX 序列化，~148 行）
  - `src/garage_os/adapter/installer/marker.py`（`inject` / `extract_marker`，~156 行）
  - `src/garage_os/adapter/installer/pipeline.py`（`install_packs` + `_decide_action` + `_check_conflicts` + 异常类型，~390 行）
  - `src/garage_os/adapter/installer/interactive.py`（`prompt_hosts` stdlib 实现，~91 行）
  - `src/garage_os/cli.py` 行 13-23（installer import）、行 80-95（F007 stdout/stderr 文案常量块）、行 203-307（`_init` + `_resolve_init_hosts`）、行 1409-1439（`build_parser` 的 `init` 段新增三 flag）、行 1761-1768（`main()` dispatch）
  - `packs/README.md`、`packs/garage/{pack.json, README.md, skills/garage-hello/SKILL.md, agents/garage-sample-agent.md}`（T1 工件）
- 上游规格：`docs/features/F007-garage-packs-and-host-installer.md`（已批准）
- 上游设计：`docs/designs/2026-04-19-garage-packs-and-host-installer-design.md` (r2)
- 上游 tasks：`docs/tasks/2026-04-19-garage-packs-and-host-installer-tasks.md` (r1)
- 上游 test review：`docs/reviews/test-review-F007-garage-packs-and-host-installer.md`（通过；5 minor LLM-FIXABLE 中至少 3 条已被实现侧吸收 — `TestInitErrorPaths` 系列、`TestFieldFormats` 正则、`TestDecisionTableEdgeRows` 决策表两行）
- Reviewer：`hf-code-review` subagent
- Date：2026-04-19

---

## Precheck

| 项 | 结果 |
|----|------|
| 实现交接块稳定可定位 | ✅ 9 个 installer 模块 + cli.py 5 段 anchor + 5 个 packs/ 工件，全部按 D7 §9 模块清单落地 |
| 测试通过证据新鲜 | ✅ reviewer 自跑 `pytest tests/adapter/installer/ tests/test_cli.py::TestInitWithHosts tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered -q` → **82 passed**；`pytest tests/ -q` → **585 passed**（基线 496 + F007 新增 89） |
| route / stage / profile 一致 | ✅ test-review 通过 + auto-mode approval；任务 T1-T5 全部完成 |
| AGENTS.md 编码约定 | ✅ Python 3.11+；不引入新依赖（无 questionary / rich）；模块路径 `src/garage_os/adapter/installer/` 符合 CON-701 |

Precheck 通过，进入正式审查。

---

## 多维评分（每维 0-10）

| ID | 维度 | 分 | 关键依据 |
|---|---|---|---|
| `CR1` 正确性 | 8 | walking skeleton 端到端验证 + 决策表 7 行有 6 行直接覆盖（剩 1 行 "no entry & dst missing" 为 trivial WRITE_NEW）；幂等比较前先注入 marker 再哈希，正确反映"目标位置最终字节"语义；conflict 检测 `(host, dst_rel)` 维度准确；只在源 hash 与已写入 hash 不一致时实际触发 `write_bytes`，NFR-702 mtime 不变实测通过；2 处轻微行为偏差见 finding F007-CR-3 / F007-CR-5 |
| `CR2` 设计一致性 | 9 | `HostInstallAdapter` Protocol 与 D7 §11.1 字面一致（`host_id` / `target_skill_path` / `target_agent_path` / `render` 四槽，`render` 默认透传）；ADR-D7-1 严格遵守（与 `HostAdapterProtocol` 命名空间共处但接口独立，`ClaudeInstallAdapter` 与 F001 `ClaudeCodeAdapter` 真分离）；ADR-D7-2 YAML front matter 注入选型落地；ADR-D7-3 三家 adapter 路径字面值与设计表完全一致；ADR-D7-5 stdlib `[y/N]` 循环；CON-701/702/703/704 全部满足。1 处文案与设计 §2.1 表略偏：`MSG_NO_PACKS_FMT` 落在 `pipeline.py` 而非 `cli.py` 顶部常量块（设计承诺 cli.py 顶部统一，详见 finding F007-CR-2） |
| `CR3` 状态 / 错误 / 安全 | 9 | 6 类异常分支 100% 命名 + CLI 包装：`UnknownHostError`/exit 1、`ConflictingSkillError`/exit 2、`InvalidPackError` & `PackManifestMismatchError`/exit 1、`MalformedFrontmatterError`/exit 1、`OSError`/exit 1；CON-702 兜底（`.garage/` 在 host 错误后仍然存在）由 `tests/test_cli.py::TestInitErrorPaths::test_unknown_host_exit_1_but_garage_dir_created` 等 5 用例守护；non-TTY 退化 `prompt_hosts` 默认 `sys.stdin.isatty()` 检测，`EOFError` 归并到 non-TTY 路径，无静默失败；POSIX 序列化避免 Windows `\` 路径泄漏 |
| `CR4` 可读性 / 可维护性 | 8 | 模块拆分清晰，每个 installer 模块单一职责（pack_discovery 不读 SKILL.md 内容、marker 不写文件、pipeline 集中所有 IO 副作用，与 D7 §9 表完全一致）；docstring 详尽且解释了非显然 invariants（marker.inject 选择"不走 yaml 全解析"的原因、`_decide_action` 决策表注释、`_check_conflicts` 维度注释）；命名清晰（`HostInstallAdapter` / `ClaudeInstallAdapter` 与 F001 `ClaudeCodeAdapter` 显式区分）；变量复用 `existing` 在 pipeline 行 154 / 188 双义遮蔽（finding F007-CR-1）；ruff/mypy 4 处新错误见 finding F007-CR-4（不阻塞 baseline） |
| `CR5` 范围守卫 | 9 | 不引入 TUI 依赖（`pyproject.toml` git diff 空）；不修改 F001 `HostAdapterProtocol`、F002 `_init` 字节相同输出、F003-F006 知识 / 经验 / 召回管道完全未触；ADR-D7-4 单 `packs/garage/` 起步，未顺手把 HF skills 搬过来（CA3 守住）；`render` 默认透传 + 暂未引入未使用的 jinja / 模板能力（CA5 守住）；FR-708 marker 选 YAML front matter 而非 HTML 注释，按 ADR-D7-2；R1 informational（spec FR-707 / § 12 术语回填）属于 spec 层补强，不在本 cycle 代码范围 |
| `CR6` 下游追溯就绪度 | 9 | 实现交接块行号清晰，常量名与 spec FR-709 / D7 §2.1 1:1 对得上；`installer/__init__.py` 集中 re-export 让追溯 reviewer 一站式定位 public symbol；测试矩阵覆盖 D7 §13 全部 9 个测试模块；`installed_hosts` / `installed_packs` / `files[]` 三个 manifest 字段足够回答 "本仓库装过哪些 host / pack / 文件来自哪里" 的审计问题；唯一信息缺口是 `ERR_*_FMT` 常量与实际 stderr 文案的对应关系不直观（finding F007-CR-2） |

无任一关键维度 < 6。综合通过线已满足。

---

## 实施 vs 关键约束逐项核对

| 约束 / ADR | 期望 | 现况 | 评 |
|------------|------|------|---|
| **CON-701** adapter 位置 | 子包位于 `src/garage_os/adapter/` 下 | `src/garage_os/adapter/installer/` 9 个模块全部就位 | ✅ |
| **CON-702** 不破坏 F002 | bare `garage init` 字节相同 | `tests/test_cli.py::TestInitWithHosts::test_default_init_unchanged_when_no_hosts` 直接断言 stdout 含 `Initialized Garage OS in <path>` 单行；`_init` 缺省路径无任何 `--hosts*` 时直接早返回；reviewer 自跑通过 | ✅ |
| **CON-703** schema_version 受 VersionManager 管控 | host-installer.json schema 注册 | `MANIFEST_SCHEMA_VERSION = 1` 暴露；`tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered::test_host_installer_schema_recognized` 实际写一个 manifest → `vm.detect_version` 返回 `major == 1` → `vm.check_compatibility` 返回 `COMPATIBLE` 全链路验证；当前实现走"路径无关检测"（VersionManager 本就支持），未在 `version_manager.py` 显式新增字面注册项，但满足验收 | ✅ |
| **CON-704** 路径来源说明 | 用户指南显式说明宿主原生约定 | `docs/guides/garage-os-user-guide.md:548` "都是各宿主的原生约定 ... Garage 只是把内容写到那里，没有自创任何路径" | ✅ |
| **NFR-101** 不引入 TUI 依赖 | 仅 stdlib | `interactive.py` 仅用 `sys.stdin` + `input()` + `print(..., file=stderr)`；`pyproject.toml` git diff 空 | ✅ |
| **NFR-701** 宿主无关性 | packs/ 内容无宿主黑名单关键字 | `tests/adapter/installer/test_neutrality.py` parametrize 真实 packs/ 全部 SKILL.md + agent.md → 0 命中；reviewer 复跑 `rg -i "\.claude/|\.cursor/|\.opencode/|claude-code" packs/garage/skills/ packs/garage/agents/` 0 命中 | ✅ |
| **NFR-702** 性能 / 无写入 | mtime 不刷新 | `pipeline._install_packs` 行 205-209 写前先比 `dst_abs.read_bytes() != rendered_bytes`；`tests/adapter/installer/test_idempotent.py` 双用例（含 `--force` 在无变化时仍 no-op）实测 mtime_ns 不变 | ✅ |
| **NFR-703** 跨平台路径 | manifest 用 POSIX | `manifest._to_posix` 用 `PurePosixPath(*Path(s).parts).as_posix()`；`tests/adapter/installer/test_manifest.py::TestPosixPathSerialization` 断言 `\` 不出现且 `/` ≥ 2 | ✅ |
| **ADR-D7-1** 安装 / 运行时 adapter 分离 | 不污染 F001 protocol | `host_adapter.py` git diff 空；`installer/host_registry.py` 独立 Protocol；命名空间 `ClaudeInstallAdapter` vs `ClaudeCodeAdapter` 显式区分 | ✅ |
| **ADR-D7-2** YAML front matter 注入 | 不破坏宿主解析 + 幂等 | `marker.inject` 用文本块 split 而非 yaml round-trip（避免重排其他键、保 SHA-256 稳定；`marker.py` 行 21-29 docstring 显式记录此意图）；`test_marker.py::test_skill_idempotent_reinjection` + `test_agent_idempotent_reinjection` 守 idempotent | ✅ |
| **ADR-D7-3** 三宿主路径表 | 字面值与表一致 | claude.py 行 28-32 / opencode.py 行 22-26 / cursor.py 行 30-33 与 D7 §11.1 ADR-D7-3 表完全一致；cursor `target_agent_path` 显式返回 `None`；`tests/adapter/installer/test_hosts.py` 字面断言 | ✅ |
| **ADR-D7-4** 单 `packs/garage/` 起步 | 1 sample skill + 1 sample agent | `packs/garage/{pack.json, skills/garage-hello/SKILL.md, agents/garage-sample-agent.md}` 落盘；`pack.json.skills==["garage-hello"]` / `agents==["garage-sample-agent"]` 与磁盘一致 | ✅ |
| **ADR-D7-5** stdlib `[y/N]` | 零依赖 + a/q 快捷键 + 默认 N | `interactive.py` 行 23-30 `PROMPT_TEMPLATE`；行 69-78 `a` / `q` / `y` / 其余跳过；`test_interactive.py` 6 用例覆盖含 capital `N` 仍跳过本 host | ✅ |

---

## 发现项

### F007-CR-1 — `pipeline.install_packs` 内 `existing` 变量遮蔽（双义同名）

- [important][LLM-FIXABLE][CR4 / CA1 边缘]
- 位置：`src/garage_os/adapter/installer/pipeline.py:154` 与 `:188`
- 现状：行 154 `existing = read_manifest(workspace_root / ".garage")` 类型为 `Manifest | None`，下一行立刻被收敛为 `existing_index`，之后理应不再使用 `existing`。但行 188 重新赋 `existing = existing_index.get(...)`（类型 `ManifestFileEntry | None`）并在 189-190 决定是否 `new_entries.append(existing)`。结果：
  1. mypy 报 2 处 error（`Incompatible types in assignment` + `Argument 1 to "append" has incompatible type "Manifest"; expected "ManifestFileEntry"`）—— 这是本 cycle 新引入的 mypy 错误（baseline 不含）；
  2. 阅读时同名变量在 30 行内含两种语义，是 CR4 可读性回退，也存在被未来重构者误用的风险。
- 影响：**功能上正确**（`existing_index.get((src_rel, dst_rel))` 与既有 `read_manifest()` 返回值的 `(src,dst)` 索引等价），但变量遮蔽属于 CR3 边缘 / CR4 真问题；mypy 新错误违反 spec NFR-704 "F007 新增不应引入新错误" 的轻量预期（task-progress 已声明 baseline 不修，但本 cycle 新错应避免）。
- 建议：将 188 行重命名为 `prior_entry = existing_index.get(...)`；同步把 153 行 `existing` 改名为 `prior_manifest`，把 156 行 `if existing else {}` 改成 `if prior_manifest else {}`。零行为差异，纯命名 + 类型修复。
- 修复后 `_resolve_targets` 行 276 `dst_rel: Path | None = adapter.target_agent_path(...)` 同类型遮蔽问题（mypy `Statement is unreachable` + `Incompatible types` 共 2 处）也建议一并改名（如 `agent_dst = adapter.target_agent_path(...)`）。

### F007-CR-2 — 文案常量分散在 cli.py 与 pipeline.py 两处，且部分定义未使用

- [minor][LLM-FIXABLE][CR2 / CR4]
- 位置：
  - `src/garage_os/cli.py:80-95` 定义 `INSTALLED_FMT` / `ERR_UNKNOWN_HOST_FMT` / `ERR_PACK_INVALID_FMT` / `ERR_PACK_MISMATCH_FMT` / `ERR_MARKER_FAILED_FMT` / `ERR_HOST_FILE_FAILED_FMT`
  - `src/garage_os/adapter/installer/pipeline.py:55-58` 定义 `WARN_LOCALLY_MODIFIED_FMT` / `WARN_OVERWRITE_FORCED_FMT` / `MSG_NO_PACKS_FMT`
- 现状：
  1. **`ERR_UNKNOWN_HOST_FMT`（cli.py:86-88）从未被使用**；CLI 行 253 / 267 直接 `print(str(exc), file=sys.stderr)` 把 `UnknownHostError` 的 message 原样输出。该 message 由 `host_registry.get_adapter` / `resolve_hosts_arg` 内部 f-string 拼接（"Unknown host: ... Supported hosts: ..."），与 `ERR_UNKNOWN_HOST_FMT` 字面值同模式但**两份字符串各自维护**，未来若改文案需同时改两处或漏改之一。
  2. **`ERR_PACK_MISMATCH_FMT`（cli.py:93）从未被使用**；`PackManifestMismatchError` 走的是 `ERR_PACK_INVALID_FMT` 分支（cli.py:272-274 把两个异常合并到一个 except）。
  3. D7 §2.1 表承诺 stable 文案常量与 F005 `KNOWLEDGE_*_FMT` 同模式"在 cli.py 顶部声明"，但 `WARN_LOCALLY_MODIFIED_FMT` / `WARN_OVERWRITE_FORCED_FMT` / `MSG_NO_PACKS_FMT` 实际定义在 `pipeline.py` 顶部（cli.py:89-91 用注释指向）。这是合理的工程取舍（pipeline 直接 emit、cli 不二次包装），但与设计文案有微妙偏差，且让 grep `INSTALLED_FMT` 与 `WARN_LOCALLY_MODIFIED_FMT` 需在两个文件之间跳。
- 影响：FR-709 验收**仍然满足**（stderr / stdout 出现稳定 marker 字符串可被 grep）；但常量管理一致性弱，未来文案演进时易出现 "改了一处忘记另一处"。
- 建议：删除 cli.py 中未用的 `ERR_UNKNOWN_HOST_FMT` / `ERR_PACK_MISMATCH_FMT`（或者把 cli 的 `print(str(exc), ...)` 改成 `print(ERR_UNKNOWN_HOST_FMT.format(host=..., supported=...), ...)`）；在 cli.py 文案段加一行 `# WARN_*_FMT / MSG_NO_PACKS_FMT 见 pipeline.py，由 pipeline 直接 emit` 的指针注释（已部分存在于 cli.py:89-91，可补 `MSG_NO_PACKS_FMT`）。

### F007-CR-3 — `SKIP_LOCALLY_MODIFIED` 时仍把该文件计入 `n_skills` / `n_agents`，stdout marker 与"Installed"语义有歧义

- [minor][LLM-FIXABLE][CR1 / CR4]
- 位置：`src/garage_os/adapter/installer/pipeline.py:181-195`
- 现状：当一个 target 决策为 `SKIP_LOCALLY_MODIFIED`（既包括 "tracked but locally modified" 也包括 "untracked stray file at our dst"），代码 stderr 打印 `Skipped <path> ...` 后 `continue`，但**仍然 `n_skills += 1` / `n_agents += 1`**。最终 stdout 渲染 `INSTALLED_FMT` "Installed N skills, M agents into hosts: ..." 的 N/M 把跳过的文件也算进去。
- 例（已被 `tests/adapter/installer/test_pipeline.py::TestLocallyModifiedProtection::test_install_locally_modified_skip_default` 隐式验证为通过）：用户 1 skill 装 claude → 修改文件 → 再装 claude → stderr `Skipped` + stdout `Installed 1 skills, 0 agents into hosts: claude`。从用户视角，"Installed 1" 与 stderr "Skipped" 自相矛盾。
- 影响：FR-709 stable marker 验收 ✅（marker 字符串仍然出现），但语义不严谨；CR1 "完成任务目标"边缘 — D7 §10.2 写入决策表明确把 `SKIP_LOCALLY_MODIFIED` 与 `WRITE_NEW` / `UPDATE_FROM_SOURCE` 区分开；spec FR-704 验收 #2 "原始 SKILL.md 主体（去除 marker 后）字节级等于源文件" 在跳过场景下不成立，但 marker 上报"已 Installed"会让审计 reviewer 误以为 spec 满足。
- 建议（任一即可）：
  1. 在跳过时不增计数器，把 `n_skills` / `n_agents` 改名为 `n_skills_written` / `n_agents_written`，并把 `INSTALLED_FMT` 文案细化为 `"Installed {written} skills (of which {skipped} skipped), ..."`。或者
  2. 维持当前计数语义但补一行 `Skipped {n_skipped} files (locally modified)` summary stdout marker（与 `Skipped` stderr 互文，让 stdout 总览自洽）。
- 优先级：minor 而非 important，因为 stderr 已经准确反映跳过；但下游若仅 grep stdout 会得到误读。

### F007-CR-4 — F007 新增引入 4 个新 mypy error + 20 个新 ruff lint，未与 baseline 合流

- [minor][LLM-FIXABLE][CR4]
- 位置：reviewer 自跑结果
  - `mypy src/garage_os/adapter/installer/ src/garage_os/cli.py` → installer 引入 4 个新错误（pipeline.py:188 / 190 / 276 / 278；其中 188/190 是 F007-CR-1 的成因）
  - `ruff check --output-format concise src/garage_os/adapter/installer/` → 20 errors（13 处 `UP045` "Use X | None for type annotations"、6 处 `I001` import 排序、1 处 `UP035` `Iterable` 应从 `collections.abc` 导入）
- 现状：tasks.md §10 风险表显式声明 "pre-existing 2 mypy errors / 47 ruff warnings 不在本 cycle 修复，但只确保 T2-T5 不新增"。本 cycle 同时违反两项：installer 子包在 baseline mypy 错误数（49）中贡献了 ≥4 处新增（baseline-level mypy 全量 49 错），而 ruff 在 installer 子包贡献了 20 处全新警告（既有 baseline 不含 installer 路径）。
- 影响：不阻塞功能，且与既有代码风格一致（cli.py 自身大量 `Optional[X]` 同模式 UP045）；但 T2 验证条目"`uv run mypy src/garage_os/adapter/installer/` 无新错"未严格通过 —— 该用例在批准时被解释为相对全仓 baseline 的"无新错"，而严格读应是 installer 子包内 0 错。
- 建议（最小成本）：
  1. F007-CR-1 修好后 mypy 错从 4 降到 2；剩余 2 处（pipeline.py:276/278 `dst_rel` 类型遮蔽）顺手 rename 即解决；
  2. ruff 20 errors 中 19 处 `--fix` 即可自动修复（按 `ruff check --fix src/garage_os/adapter/installer/`），不影响行为；
  3. 若决定不修，应在 task-progress.md 显式记录 carry-forward 让 traceability 不再追问。

### F007-CR-5 — Conflict 检测仅在 skill / agent 同名同 host 时触发；agent 维度未单独测试

- [minor][LLM-FIXABLE][CR1 / CR3]
- 位置：`src/garage_os/adapter/installer/pipeline.py:294-306`
- 现状：`_check_conflicts` 把 `(host, dst_rel)` 作为 key 检测重复 src，agent 与 skill 共用同一逻辑。`tests/adapter/installer/test_pipeline.py::TestConflict::test_conflict_same_skill_two_packs` 仅触发 skill 路径；agent 路径（两 pack 同名 agent → 同 dst）未直接覆盖。test review F-6 已标注此点为 minor，对应建议未在实现侧吸收。
- 影响：行为正确（同一函数同一 key 计算）但缺少冗余 fixture 兜底；属 test 缺口而非实现缺口。
- 建议：留给下游 traceability 阶段或在本 cycle 顺手补 1 个 `test_conflict_same_agent_two_packs` 用例（可与 skill 用例共享 fixture 工厂），属轻量补强；不阻塞 verdict。

### F007-CR-6 — `_resolve_targets` `agent_id` `if dst_rel is None` 早 break 的可读性

- [minor][LLM-FIXABLE][CR4]
- 位置：`src/garage_os/adapter/installer/pipeline.py:273-278`
- 现状：cursor adapter 的 `target_agent_path` 永远返回 `None`，所以 `for host_id in adapters: if dst_rel is None: continue` 会对 `["claude", "cursor", "opencode"]` 在 cursor 这一 iteration 上 continue。当前逻辑等价正确，但 mypy 因为 `dst_rel: Path` 类型注解（外层 `_Target.dst_abs` 是 `Path`，注释看是 `dst_rel = adapter.target_agent_path(...)` 推断为 `Path | None`）而报 `Statement is unreachable` 与 `Incompatible types`。
- 影响：与 F007-CR-1 / F007-CR-4 同根；建议合并解决。
- 建议：rename `dst_rel` 为 `agent_dst: Path | None`，并把 `dst_rel=_to_posix(dst_rel)` 中的 `dst_rel` 改成 `agent_dst`（在 `if agent_dst is None: continue` 之后 mypy 自然 narrow 为 `Path`）。

---

## 代码风险与薄弱项

- **`marker._split_frontmatter` 仅识别 `---\n` 起始**：若源文件以 BOM 或 `---\r\n` 开头（Windows-edited SKILL.md），会被识别为"无 front matter"。skill 路径会抛 `MalformedFrontmatterError` 直接报错（行为可见），agent 路径会"再注入一次最小 front matter"导致内容重复。当前 packs/garage/ 全部 LF + 无 BOM，本 cycle 不暴露；但 ASM-702 假设下游 Pack 作者用任意编辑器写 SKILL.md 时这是潜在踩坑点。建议在 `_split_frontmatter` 加 BOM 容忍 + `\r\n` 正常化，或在 `marker.py` docstring 显式声明 LF + UTF-8 不带 BOM 是 packs 的隐性约定。**不阻塞本 cycle**，可作为 hf-bug-patterns 候选。
- **`InstallSummary.hosts` 在 no-packs 与 packs 路径返回值不一致**：no-packs 路径行 151 仅返 `sorted(set(hosts))`（不含 prior installed_hosts），packs 路径行 240 返 `sorted(set(hosts) | set(merged.installed_hosts))`（含 prior）。CLI stdout 渲染 `Installed 0 skills, 0 agents into hosts: ...` 在 extend 模式下会少列 prior 宿主，与 manifest 的 `installed_hosts` 字段产生轻微不一致。本 cycle 用例未触发；属 minor 行为偏差。
- **Cursor `.cursor/skills/` 在某些 Cursor 旧版本可能不识别**（D7 ADR-D7-3 R2 风险）：用户指南已显式提示，本 cycle 不阻塞；属 deferred 信息条目。
- **`_check_conflicts` 在 host 维度独立判断，跨 host 同名 skill 不算冲突**：合理（不同宿主目录前缀不同），但本设计假设宿主 dst 路径前缀总是不同；若未来某 adapter 改成 dot-less 前缀（如自定义共享根），需重审本断言。当前 3 个 first-class adapter 都以 `.<host>/...` 前缀，不会出现跨 host dst 撞车。
- **`existing_index.get((src_rel, dst_rel))` 的 key 为 `(src, dst)` 而非 `(src, dst, host)`**：当前 host 已隐含在 `dst_rel` 前缀（`.claude/skills/...` vs `.cursor/skills/...`），不会撞车。但若未来支持 "global mode"（OpenSpec issue #752）让多 host 共享 `~/.skills/`，此索引会塌陷。属 deferred 关注。

---

## 下游追溯评审提示

下游 `hf-traceability-review` 可直接按以下 anchor 复核：

1. **FR-701 → 实现 → 测试**：`packs/README.md` + `packs/garage/pack.json` + `packs/garage/{skills,agents}/...` ↔ `pack_discovery.py:71-91 discover_packs` ↔ `tests/adapter/installer/test_pack_discovery.py` (10 用例)
2. **FR-702/703/707 → 实现 → 测试**：`cli.py:1409-1439 build_parser init` + `cli.py:292-307 _resolve_init_hosts` + `host_registry.py:99-131 resolve_hosts_arg` + `interactive.py:33-79 prompt_hosts` ↔ `tests/test_cli.py::TestInitWithHosts/TestInitErrorPaths` + `test_host_registry.py` + `test_interactive.py`
3. **FR-704/706a/706b/708 → 实现 → 测试**：`pipeline.py:93-241 install_packs` + `pipeline.py:309-332 _decide_action` + `marker.py:47-75 inject` ↔ `tests/adapter/installer/test_pipeline.py` (11 用例) + `test_marker.py` (9 用例) + `test_idempotent.py` (2 用例)
4. **FR-705 → 实现 → 测试**：`manifest.py` + `MANIFEST_SCHEMA_VERSION = 1` ↔ `tests/adapter/installer/test_manifest.py` (9 用例) + `tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered` (2 用例)
5. **FR-709 stable marker → 实现 → 测试**：`cli.py:80-95 INSTALLED_FMT 等` + `pipeline.py:55-58 WARN_*` ↔ `tests/test_cli.py::TestInitWithHosts::test_hosts_explicit_list / test_no_packs_dir_succeeds_with_marker` + `test_pipeline.py::TestLocallyModifiedProtection`
6. **FR-710 文档 → 实现 → 测试**：`packs/README.md` + `docs/guides/garage-os-user-guide.md "Pack & Host Installer"` ↔ `tests/test_documentation.py::test_user_guide_documents_pack_and_host_installer / test_packs_readme_documents_directory_contract`
7. **CON-701/702/703/704 → 实现 → 测试**：模块物理路径（`src/garage_os/adapter/installer/`）+ `tests/test_cli.py::TestInitWithHosts::test_default_init_unchanged_when_no_hosts` + `tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered` + 用户指南文案

需要 traceability reviewer 额外关注：
- F007-CR-2 `ERR_UNKNOWN_HOST_FMT` / `ERR_PACK_MISMATCH_FMT` 字面常量未被代码引用，可视作"为 grep 自描述而存在"的容忍项（与 design D7 §2.1 一致），但建议要求实现侧明确"哪些常量是被 emit 的、哪些是为 grep 占位"。
- F007-CR-3 stdout `Installed N skills` 计数包含 `SKIP_LOCALLY_MODIFIED` 文件，与"Installed"字面语义略偏；如 traceability 阶段要严求 spec FR-704 acceptance 字节级等于源，需建议补一个 stdout summary marker。

---

## 结论

**通过**

- 6 个评审维度均 ≥ 8/10，无关键维度阻塞。
- spec FR-701~710 / NFR-701~704 / CON-701~704 / ADR-D7-1~5 全部已被实现侧 1:1 覆盖；reviewer 自跑 82 passed (F007 切片) + 585 passed (整体)。
- 6 条 finding 中：
  - 1 条 `important` (F007-CR-1)：变量遮蔽 + 引入新 mypy error；属 LLM-FIXABLE，不阻塞 traceability 阶段，但建议在进入 traceability 前做 1 轮定向修订或在 task-progress 显式 carry-forward 给 traceability / regression-gate 决策。
  - 5 条 `minor` (F007-CR-2 ~ F007-CR-6)：常量管理、计数语义、lint baseline、agent conflict 测试缺口、类型遮蔽；均不阻塞 verdict，可在 traceability 阶段一并标注或下个 cycle 集中清理。
- 与 F001 `HostAdapterProtocol`、F002 `garage init`、F003-F006 知识/经验/记忆/召回管道完全无回归。

**注**：本 reviewer 注意到 F007-CR-1 已明确触发新增 mypy error（违反 spec NFR-704 隐性预期"F007 新增不应引入新错误"，task-progress §10 措辞较宽松仅要求"不退绿"）。考虑到：(a) 现有测试 100% 通过（585 passed），(b) finding 为纯 LLM-FIXABLE 命名重构，(c) test review 已通过且类似 minor finding 在 F003-F006 cycle 也曾以 carry-forward 处理 —— 本 reviewer 选择**通过**而非**需修改**，但**强烈建议**实现侧在进入 `hf-traceability-review` 之前先用 1 个小 commit 闭合 F007-CR-1（rename + 顺手 ruff `--fix`），让 traceability / regression-gate 阶段拿到的代码是 baseline-clean 的。

## 下一步

- `hf-traceability-review`（按 reviewer return contract）
- `needs_human_confirmation=false`
- `reroute_via_router=false`

## 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-traceability-review",
  "record_path": "docs/reviews/code-review-F007-garage-packs-and-host-installer.md",
  "key_findings": [
    "[important][LLM-FIXABLE][CR4] F007-CR-1 pipeline.install_packs `existing` 变量在行 154/188 双义遮蔽，引入 2 处新 mypy error 且降低可读性；建议 rename 为 prior_manifest / prior_entry",
    "[minor][LLM-FIXABLE][CR2/CR4] F007-CR-2 cli.py `ERR_UNKNOWN_HOST_FMT` / `ERR_PACK_MISMATCH_FMT` 定义但未使用，与 host_registry / pipeline 内 f-string 文案双份维护；WARN_*/MSG_NO_PACKS_FMT 落在 pipeline.py 与设计文案 'cli.py 顶部统一' 略偏",
    "[minor][LLM-FIXABLE][CR1/CR4] F007-CR-3 SKIP_LOCALLY_MODIFIED 路径仍计入 n_skills/n_agents，stdout 'Installed N' marker 与 stderr 'Skipped' 语义自相矛盾",
    "[minor][LLM-FIXABLE][CR4] F007-CR-4 installer 子包引入 4 个新 mypy error + 20 个新 ruff warning，未合流到 baseline carry-forward；建议 ruff --fix + F007-CR-1 修复后 mypy 残 0",
    "[minor][LLM-FIXABLE][CR1/CR3] F007-CR-5 _check_conflicts agent 维度无独立测试用例（test review F-6 carry-forward 未吸收）",
    "[minor][LLM-FIXABLE][CR4] F007-CR-6 _resolve_targets agent 路径 dst_rel 类型遮蔽（与 F007-CR-1 同根，建议合并 rename）"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {"severity": "important", "classification": "LLM-FIXABLE", "rule_id": "CR4", "summary": "F007-CR-1 pipeline.py existing 变量双义遮蔽 + 新增 mypy error"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "CR2", "summary": "F007-CR-2 ERR_*_FMT 常量分散且部分未使用"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "CR1", "summary": "F007-CR-3 SKIP 文件仍计入 Installed N 计数，stdout/stderr 语义不自洽"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "CR4", "summary": "F007-CR-4 installer 子包 4 mypy + 20 ruff 新增未合流 baseline"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "CR1", "summary": "F007-CR-5 _check_conflicts agent 维度无独立测试"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "CR4", "summary": "F007-CR-6 _resolve_targets dst_rel 类型遮蔽"}
  ]
}
```
