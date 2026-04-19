# F007: Garage Packs 与宿主安装器 任务计划

- 状态: 草稿
- 主题: 把已批准 D7 设计拆解为可单任务推进、可冷读、可追溯的工作单元
- 日期: 2026-04-19
- 关联规格: `docs/features/F007-garage-packs-and-host-installer.md`（已批准）
- 关联设计: `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`（已批准 r2）
- 关联批准: `docs/approvals/F007-spec-approval.md`、`docs/approvals/F007-design-approval.md`

## 1. 概述

D7 设计已稳定（5 个 ADR + 模块拆分 + 接口契约 + 测试矩阵 + 失败模式）。本任务计划按 D7 §15 给出的初始拆解（T1-T5）细化每个任务的 Acceptance / Files / Verify / 测试设计种子 / 完成条件，并补依赖图、活跃任务选择规则、队列投影。

执行原则：

- **TDD 优先**：每个代码任务都先写 fail-first 测试 → 确认失败 → 最小实现 → verify green。
- **零回归保护**：任何任务不得让 `uv run pytest tests/ -q` 已有用例退绿。
- **接口契约不漂移**：D7 §11 已锁定 `HostInstallAdapter` Protocol、`Manifest` schema、`pack.json` 字段、`marker.inject(content, pack_id, source_kind)` 签名；任务实现必须按字面契约落地，不得自行调整。
- **路径契约**：D7 §9 锁定模块位置 `src/garage_os/adapter/installer/`；测试位置 `tests/adapter/installer/`；任何偏离需回到 `hf-design`。

## 2. 里程碑

| 里程碑 | 包含任务 | 退出标准 | 对应 spec/design 锚点 |
|---|---|---|---|
| **M1 packs 容器** | T1 | `packs/garage/` 占位 pack 落盘；`packs/README.md` + `packs/garage/README.md` 可冷读；`pack.json` 含 `skills[]` / `agents[]`；空 `garage-hello` SKILL.md + 1 个 sample agent | spec FR-701 / FR-710；design §11.3 |
| **M2 host adapter port** | T2 | `HostInstallAdapter` Protocol + 3 个 first-class adapter 落盘；注册表可枚举；`resolve_hosts_arg` 支持 `all` / `none` / 列表 | spec FR-707；design §9 / §11.1 / ADR-D7-1 / ADR-D7-3 |
| **M3 安装管道核心** | T3 | `install_packs` 端到端可运行；manifest 读写 + content_hash + extend mode + `--force` + 同名 pack 冲突全部覆盖；marker 注入按 source_kind 分两路 | spec FR-704 / FR-705 / FR-706a / FR-706b / FR-708；design §10 / ADR-D7-2 / ADR-D7-4 |
| **M4 CLI 集成 + 交互** | T4 | `garage init --hosts ... --yes --force` 可端到端调用；非交互 / TTY 交互 / non-TTY 退化 / unknown host 退出码 1 / 缺省 init 字节相同 | spec FR-702 / FR-703 / FR-709 / CON-702；design §10.1 / ADR-D7-5 |
| **M5 文档收尾 + VersionManager 注册** | T5 | `docs/guides/garage-os-user-guide.md` 增 "Pack & Host Installer" 段；CON-703 schema 注册；R2 风险（Cursor 老版本）在用户指南显式提示 | spec FR-710 / CON-703 / CON-704；design §12 / R2 风险 |

## 3. 文件 / 工件影响图

### 3.1 新增（不存在 → 存在）

| 工件 | 来自任务 | 类型 |
|---|---|---|
| `packs/README.md` | T1 | 文档 |
| `packs/garage/pack.json` | T1 | 配置（schema_version=1） |
| `packs/garage/README.md` | T1 | 文档 |
| `packs/garage/skills/garage-hello/SKILL.md` | T1 | skill 源文件 |
| `packs/garage/agents/garage-sample-agent.md` | T1 | agent 源文件 |
| `src/garage_os/adapter/installer/__init__.py` | T2 | 包入口 + public symbol |
| `src/garage_os/adapter/installer/host_registry.py` | T2 | Protocol + 注册表 + `resolve_hosts_arg` |
| `src/garage_os/adapter/installer/hosts/__init__.py` | T2 | 包入口（空） |
| `src/garage_os/adapter/installer/hosts/claude.py` | T2 | adapter |
| `src/garage_os/adapter/installer/hosts/opencode.py` | T2 | adapter |
| `src/garage_os/adapter/installer/hosts/cursor.py` | T2 | adapter |
| `src/garage_os/adapter/installer/pack_discovery.py` | T3 | discover + Pack dataclass |
| `src/garage_os/adapter/installer/manifest.py` | T3 | Manifest + read/write + `MANIFEST_SCHEMA_VERSION` |
| `src/garage_os/adapter/installer/marker.py` | T3 | `inject(content, pack_id, source_kind)` + `extract_marker` |
| `src/garage_os/adapter/installer/pipeline.py` | T3 | `install_packs` + `_decide_action` + `InstallSummary` + 异常类型 |
| `src/garage_os/adapter/installer/interactive.py` | T4 | `prompt_hosts(registry, *, stdin, stderr)` |
| `tests/adapter/installer/__init__.py` | T2 | 测试包入口 |
| `tests/adapter/installer/test_host_registry.py` | T2 | unit |
| `tests/adapter/installer/test_hosts.py` | T2 | unit |
| `tests/adapter/installer/test_pack_discovery.py` | T3 | unit |
| `tests/adapter/installer/test_manifest.py` | T3 | unit |
| `tests/adapter/installer/test_marker.py` | T3 | unit |
| `tests/adapter/installer/test_pipeline.py` | T3 | unit + e2e walking skeleton |
| `tests/adapter/installer/test_neutrality.py` | T3 | NFR-701 grep |
| `tests/adapter/installer/test_idempotent.py` | T3 | NFR-702 mtime |
| `tests/adapter/installer/test_interactive.py` | T4 | unit |
| `docs/guides/garage-os-user-guide.md` 新段落 | T5 | 用户文档（可能需先创建该文件） |

### 3.2 修改（既存 → 改动）

| 工件 | 来自任务 | 修改范围 |
|---|---|---|
| `src/garage_os/cli.py` | T4 | 新增 stdout/stderr 常量块；`build_parser()` 给 `init` subparser 加 `--hosts` / `--yes` / `--force`；`_init()` 末尾追加安装调用；新增 `_resolve_init_hosts` helper |
| `src/garage_os/platform/version_manager.py` | T5 | 注册 `host-installer.json` schema 项（向后兼容追加，不改公共方法签名） |
| `tests/test_cli.py` | T4 | 新增 `TestInitWithHosts` class 覆盖 CLI 集成 |
| `tests/platform/test_version_manager.py` | T5 | 新增 1 个 host-installer.json 注册项检查用例 |

### 3.3 不修改（声明性兜底）

`src/garage_os/adapter/host_adapter.py` / `claude_code_adapter.py` / `storage/` / `runtime/` / `knowledge/` / `memory/` / `tools/` / `types/` 全部不改（与 D7 §2 / spec NFR-704 一致）。

## 4. 需求与设计追溯

| spec ID | design 锚点 | 任务 | 验证用例 |
|---|---|---|---|
| FR-701 packs 契约 | D7 §11.3 | T1 | `test_pack_discovery.py` |
| FR-702 `--hosts` | D7 §10.1 + §11.1 | T4 | `tests/test_cli.py::TestInitWithHosts::test_hosts_explicit_list` |
| FR-703 交互式 + non-TTY 退化 | D7 §10.1 + ADR-D7-5 | T4 | `test_interactive.py` |
| FR-704 安装管道 + 多次累加 | D7 §10.2 + §10.3 | T3 | `test_pipeline.py::test_write_new` / `test_extend_hosts` / `test_conflict_exit_2` |
| FR-705 manifest schema | D7 §8.3 + §11.2 | T3 + T5 | `test_manifest.py::test_round_trip` + `test_version_manager.py::test_host_installer_registered` |
| FR-706a 未修改幂等 | D7 §10.2 | T3 | `test_pipeline.py::test_unmodified_idempotent` + `test_idempotent.py` |
| FR-706b 已修改保护 / `--force` | D7 §10.2 | T3 | `test_pipeline.py::test_locally_modified_skip` / `test_force_overwrite` |
| FR-707 host adapter 注册表 | D7 §11.1 + ADR-D7-1 | T2 | `test_host_registry.py` + `test_hosts.py` |
| FR-708 标记块 | D7 §10.4 + ADR-D7-2 | T3 | `test_marker.py::test_skill_inject` / `test_agent_no_frontmatter_tolerant` / `test_skill_malformed_raises` |
| FR-709 stdout/stderr 常量 | D7 §2.1 + §10.1 | T4 | `tests/test_cli.py::TestInitWithHosts::test_stable_marker` |
| FR-710 文档 | D7 §2.1 | T1 + T5 | 人工 review（review 阶段） |
| NFR-701 宿主无关 | D7 §12 | T3 | `test_neutrality.py` |
| NFR-702 性能 / 无写入 | D7 §10.2 + §12 | T3 | `test_idempotent.py` |
| NFR-703 跨平台路径 | D7 §11.2 | T3 | `test_manifest.py::test_posix_serialization` |
| NFR-704 零回归 | D7 §13 | 所有任务 | `uv run pytest tests/ -q` 整体 ≥496 |
| CON-701 adapter 位置 | D7 §9 | T2 + T3 | 物理路径 `src/garage_os/adapter/installer/` 存在即可 |
| CON-702 不破坏 F002 | D7 §10.1 | T4 | `tests/test_cli.py::TestInitWithHosts::test_default_init_unchanged` |
| CON-703 schema_version 注册 | D7 §11.3 | T5 | `tests/platform/test_version_manager.py` |
| CON-704 路径来源说明 | D7 §12 | T5 | 人工 review |

## 5. 任务拆解

### T1 — packs/ 目录契约 + 占位 pack + 双层 README

- **目标**：在仓库中物化 `packs/` 目录契约，让 T2/T3/T4 后续任务有可消费的源。
- **Acceptance**：
  - `packs/README.md` 解释 `packs/` 目录契约（pack.json schema、skills/agents 子目录约定、与 host 安装的关系）。
  - `packs/garage/pack.json` 字段完整：`schema_version=1`、`pack_id="garage"`、`version`、`description`、`skills=["garage-hello"]`、`agents=["garage-sample-agent"]`。
  - `packs/garage/README.md` 介绍占位 pack 的用途、列出包含的 skill/agent。
  - `packs/garage/skills/garage-hello/SKILL.md` 是合法 SKILL.md（含 `name: garage-hello` + `description: ...` front matter，正文是占位欢迎语；遵循 `docs/principles/skill-anatomy.md`）。
  - `packs/garage/agents/garage-sample-agent.md` 是合法 markdown，含可选 front matter（用于测 marker 容错路径）。
  - `packs/garage/skills/garage-hello/SKILL.md` **不**含任何宿主特定术语（`.claude/` / `.cursor/` / `.opencode/` / `claude-code` 等黑名单关键字）。
- **依赖**：无（首任务）。
- **Ready When**：cycle 启动即 ready。
- **初始队列状态**：`active`。
- **Selection Priority**：1（首任务）。
- **Files / 触碰工件**：见 §3.1 packs/* 5 项。
- **测试设计种子**：人工 review + 后续 T3 `test_pack_discovery.py` 会消费这些工件作为 fixture（read 验证）。
- **Verify**：
  - `cat packs/garage/pack.json | python -m json.tool` 不抛错
  - `head -5 packs/garage/skills/garage-hello/SKILL.md` 显示 yaml front matter
  - `rg -n "\.claude/|\.cursor/|\.opencode/|claude-code" packs/` 0 命中（NFR-701 预演）
- **预期证据**：5 个新文件落盘可被 git 追踪。
- **完成条件**：所有 Acceptance 条目可 `ls` / `cat` 验证。

### T2 — host adapter port + 3 个 first-class adapter

- **目标**：把 D7 §11.1 的 `HostInstallAdapter` Protocol 与 ADR-D7-3 三家 adapter 落地，让 T3 安装管道能拿到目标路径计算能力。
- **Acceptance**：
  - `src/garage_os/adapter/installer/host_registry.py` 暴露 `HostInstallAdapter` Protocol（含 `host_id`、`target_skill_path`、`target_agent_path`、`render` 四个槽，`render` 默认透传）；`HOST_REGISTRY: dict[str, HostInstallAdapter]` 字面声明 `claude` / `opencode` / `cursor` 三项；`get_adapter(host_id)` / `list_host_ids()` / `resolve_hosts_arg(arg, registry)` 公开 helper 可调用。
  - `resolve_hosts_arg` 行为：`"all"` → 注册表全集稳定排序；`"none"` → 空列表；`"a,b"` → 逐项校验后排序；任意未知 ID → 抛 `UnknownHostError`。
  - 三个 adapter（在 `hosts/{claude,opencode,cursor}.py`）的字面值与 D7 ADR-D7-3 表完全一致；`cursor.target_agent_path("any")` 返回 `None`。
- **依赖**：无（与 T1 无强依赖；可与 T1 并行，但 §8 选择规则将 T1 排在前确保单线推进）。
- **Ready When**：T1 完成（保持单线推进，避免 review 时双任务交叉）。
- **初始队列状态**：`pending`。
- **Selection Priority**：2。
- **Files / 触碰工件**：见 §3.1 `installer/host_registry.py` + `hosts/*` 5 项 + `tests/adapter/installer/test_host_registry.py`、`test_hosts.py`、`__init__.py`。
- **测试设计种子（fail-first）**：
  - 主行为：`HOST_REGISTRY` 含 `claude` / `opencode` / `cursor` 3 个 key；`list_host_ids()` 返回 `["claude", "cursor", "opencode"]`（ASCII 排序）。
  - 关键边界：`resolve_hosts_arg("notarealtool")` 抛 `UnknownHostError` 且 message 含已支持列表；`resolve_hosts_arg("none")` 返回 `[]`。
  - fail-first 点：先写 `test_get_adapter_returns_claude_install_adapter`，断言 `HOST_REGISTRY["claude"].target_skill_path("foo") == Path(".claude/skills/foo/SKILL.md")` —— 在没有任何 adapter 实现前必须红。
- **Verify**：
  - `uv run pytest tests/adapter/installer/test_host_registry.py tests/adapter/installer/test_hosts.py -q`（绿）
  - `uv run mypy src/garage_os/adapter/installer/`（无新错；既有 baseline mypy 错误不算 T2 引入）
- **预期证据**：新增 ~10-12 用例全绿；既有 ≥496 pytest 用例不退绿。
- **完成条件**：所有 Acceptance + Verify。

### T3 — 安装管道核心（discover / manifest / marker / pipeline + 测试矩阵）

- **目标**：实现 D7 §10 的端到端安装管道，让 `install_packs(workspace_root, packs_root, hosts)` 可独立运行（暂不接 CLI）。
- **Acceptance**：
  - `pack_discovery.discover_packs(packs_root)` 返回 `list[Pack]`：空目录 → `[]`；含 `packs/garage/` → 1 个 `Pack` 含 1 skill + 1 agent；`pack.json` 缺失或非法 JSON → `InvalidPackError`；`pack.json.skills[]` 与磁盘扫描不一致 → `PackManifestMismatchError`。
  - `manifest.Manifest` dataclass + `read_manifest(garage_dir)` / `write_manifest(garage_dir, manifest)` round-trip 字节稳定（`installed_hosts` / `installed_packs` ASCII 排序、`files[]` 按 `(src,dst)` 字典序、`installed_at` ISO-8601、`content_hash` 是 SHA-256 hex）。`MANIFEST_SCHEMA_VERSION = 1` 暴露。
  - `marker.inject(content, pack_id, source_kind)` 按 D7 §10.4：`source_kind="skill"` 强制源含 front matter（否则 `MalformedFrontmatterError`）→ 注入 `installed_by: garage` + `installed_pack: <pack-id>` 两字段；`source_kind="agent"` 容错：源无 front matter 时插入最小 front matter，源已有 front matter 时同 skill 路径注入。`extract_marker(content)` 返回 dict 或 `None`。
  - `pipeline.install_packs(workspace_root, packs_root, hosts, *, force=False)` 端到端走通：discover → resolve targets → `_decide_action` 按 D7 §10.2 写入决策表 → 调用 adapter `target_*_path` → marker.inject → 写文件 → 写 manifest。返回 `InstallSummary(n_skills, n_agents, hosts)`。
  - 同名 skill 跨 pack（fixture 临时构造 `packs_a/skills/foo` + `packs_b/skills/foo`）→ `ConflictingSkillError`。
  - NFR-702：未修改幂等场景下，目标文件 `mtime` 不被刷新（在源 hash 与已写入 hash 相等时短路 `write_text`）。
  - NFR-701：`tests/adapter/installer/test_neutrality.py` grep `packs/` 黑名单关键字 0 命中。
- **依赖**：T2（消费 `HOST_REGISTRY` / adapter 计算目标路径）。
- **Ready When**：T2 完成。
- **初始队列状态**：`pending`。
- **Selection Priority**：3。
- **Files / 触碰工件**：见 §3.1 `installer/{pack_discovery,manifest,marker,pipeline}.py` + 6 个测试文件。
- **测试设计种子（fail-first）**：
  - 主行为（walking skeleton）：`test_install_packs_writes_skill_and_manifest`：临时仓库写 1 pack + 1 skill → 调 `install_packs(tmp, tmp/"packs", ["claude"])` → 断言 `(tmp/".claude/skills/garage-hello/SKILL.md").exists()` 且包含 `installed_by: garage` + manifest.files 含 1 entry，content_hash 等于实际写入内容的 SHA-256。
  - 关键边界 1：`test_install_locally_modified_skip_default`：先装 → 用户改文件 → 二次装 → 文件不变 + stderr 含 `Skipped`。
  - 关键边界 2：`test_install_force_overwrites_locally_modified`：同上场景 + `force=True` → 文件被覆盖 + stderr 含 `Overwrote`。
  - 关键边界 3：`test_extend_hosts_no_touch_existing`：先装 claude → 二次装 cursor → `.claude/` 文件 mtime 不变；`installed_hosts` 累加为 `["claude", "cursor"]`。
  - 关键边界 4：`test_conflict_same_skill_two_packs`：fixture 构造 `packs_a` + `packs_b` 同名 `foo` → 抛 `ConflictingSkillError`。
  - fail-first 点：先写 walking skeleton，必红，再实现 discover/marker/pipeline 各模块直至绿。
- **Verify**：
  - `uv run pytest tests/adapter/installer/ -q`（全绿，预计 22-28 个新用例）
  - `uv run pytest tests/ -q`（整体 ≥496+T3 新增 不退绿）
- **预期证据**：T3 新增用例全绿；installer 子包文件落盘；NFR-701 grep 0 命中。
- **完成条件**：所有 Acceptance + Verify。

### T4 — CLI 集成（`--hosts` / `--yes` / `--force` + 交互式 + 文案常量）

- **目标**：把 T2/T3 通过 `garage init` 暴露给最终用户，覆盖 spec FR-702/703/709/CON-702 全部 acceptance。
- **Acceptance**：
  - `cli.py` 顶部新增稳定文案常量：`INSTALLED_FMT`、`ERR_UNKNOWN_HOST_FMT`、`WARN_LOCALLY_MODIFIED_FMT`、`WARN_OVERWRITE_FORCED_FMT`、`MSG_NON_INTERACTIVE_NO_HOSTS`、`MSG_NO_PACKS`（与 F005 `KNOWLEDGE_*_FMT` 同模式，见 `cli.py:31-46`）。
  - `build_parser()` 给 `init` subparser 加 `--hosts <list>`、`--yes`、`--force` 三个 flag（`--hosts` 接受 `all` / `none` / 逗号列表）。
  - `_init(garage_root, *, hosts_arg=None, yes=False, force=False, stdin=None, stderr=None)` 按 D7 §10.1 编排：先创建 `.garage/`（既有 F002 行为字节相同保留）→ `_resolve_init_hosts` 解析 → 若空集 早返回 → 调 `install_packs` → 打印稳定 marker。
  - `_resolve_init_hosts` 行为表（与 D7 §10.1 一致）：显式 `--hosts` 走 `resolve_hosts_arg`；`--yes` 无 `--hosts` → 等价 `none`；都没有 + TTY → `interactive.prompt_hosts`；都没有 + non-TTY → 写 stderr 提示 + 返回 `[]`。
  - `interactive.prompt_hosts(registry, *, stdin, stderr)` 按 ADR-D7-5：每个宿主问 `Install Garage packs into <host-id>? [y/N]:`，回车默认 N；额外支持 `a` / `n` 快捷键跳过剩余；non-TTY 直接返回 `[]` + stderr 提示。
  - `cli.main()` 的 `init` 分支把 argparse 结果翻给 `_init`；任何 `UnknownHostError` 被捕获并以退出码 1 + stderr `ERR_UNKNOWN_HOST_FMT` 退出，**`.garage/` 已创建不回滚**（CON-702 兼容）；`ConflictingSkillError` → 退出码 2；`OSError` / `MalformedFrontmatterError` → 退出码 1。
- **依赖**：T2 + T3。
- **Ready When**：T2 + T3 完成。
- **初始队列状态**：`pending`。
- **Selection Priority**：4。
- **Files / 触碰工件**：见 §3.2 `cli.py` + `installer/interactive.py` + `tests/test_cli.py` + `tests/adapter/installer/test_interactive.py`。
- **测试设计种子（fail-first）**：
  - 主行为：`TestInitWithHosts::test_hosts_explicit_list`：`main(["init", "--hosts", "claude", "--path", str(tmp_path)])` → 退出码 0；`.claude/skills/garage-hello/SKILL.md` 存在；stdout 含 `INSTALLED_FMT.format(...)` 渲染结果。
  - 关键边界 1：`test_unknown_host_exits_1_but_garage_dir_created`：`--hosts notarealtool` → 退出码 1 + `.garage/` 仍存在 + stderr 含 `Unknown host: notarealtool`。
  - 关键边界 2：`test_default_init_unchanged_byte_equal`：无任何新参数 + non-TTY → stdout 与既有 F002 一致（`Initialized Garage OS in <path>` 单行）；不在 `.claude/` 等目录写任何文件（CON-702 关键证据）。
  - 关键边界 3：`test_yes_no_hosts_equals_none`：`--yes` 无 `--hosts` → 跳过交互 + 不装任何 host。
  - fail-first 点：先写 `test_hosts_explicit_list` 期望 stdout 含 marker，必红，再扩展 `_init` 直至绿。
- **Verify**：
  - `uv run pytest tests/test_cli.py::TestInitWithHosts tests/adapter/installer/test_interactive.py -q`（全绿）
  - `uv run pytest tests/ -q`（整体不退绿）
  - **manual smoke**（hf-test-driven-dev 阶段执行）：在 `/tmp/f007-smoke/` 临时目录跑 `garage init --hosts all`，确认 `.claude/skills/garage-hello/SKILL.md`、`.cursor/skills/garage-hello/SKILL.md`、`.opencode/skills/garage-hello/SKILL.md` 三处文件落盘 + manifest 写入。
- **预期证据**：CLI 新增用例全绿；manual smoke 三宿主目录截图/文件树。
- **完成条件**：所有 Acceptance + Verify。

### T5 — 文档收尾 + VersionManager schema 注册

- **目标**：把 spec FR-710 / CON-703 / CON-704 关掉，让 cycle 进入 review/gate 阶段无 documentation gap。
- **Acceptance**：
  - `docs/guides/garage-os-user-guide.md` 增 "Pack & Host Installer" 段（若该文件不存在则创建）：包含交互/非交互/extend 三种用法 + 三宿主目录映射表 + 显式说明 `.claude/skills/...` 等是宿主原生约定（CON-704）+ R2 风险提示（Cursor 老版本可能不识别 `.cursor/skills/`）。
  - `src/garage_os/platform/version_manager.py` 注册 `host-installer.json` schema 项（schema_version=1），向后兼容追加；不改既有公开方法签名。
  - `tests/platform/test_version_manager.py` 增 1 个用例：`test_host_installer_registered`，断言 VersionManager 能识别该 schema。
  - `RELEASE_NOTES.md` **不**在 T5 改（留给 hf-finalize closeout 阶段统一更新首条目）。
- **依赖**：T1 + T2 + T3 + T4（文档需要引用所有已完成的能力）。
- **Ready When**：T1-T4 完成。
- **初始队列状态**：`pending`。
- **Selection Priority**：5。
- **Files / 触碰工件**：见 §3.2 `docs/guides/garage-os-user-guide.md` + `version_manager.py` + `tests/platform/test_version_manager.py`。
- **测试设计种子**：
  - 主行为：`test_host_installer_registered`：构造 VersionManager → 调 `check_compatibility("host-installer.json", current_version=1)` → 返回 `COMPATIBLE`。
  - fail-first 点：先写 test 期望注册项存在，必红，再注册。
- **Verify**：
  - `uv run pytest tests/platform/test_version_manager.py -q`（绿，含新增用例）
  - `uv run pytest tests/ -q`（整体不退绿）
  - 人工 review `docs/guides/garage-os-user-guide.md` 新段落覆盖 FR-710 验收 #1（5 分钟内回答 3 个问题）
- **预期证据**：用户指南新段落 + version_manager 注册 + 1 新测试。
- **完成条件**：所有 Acceptance + Verify。

## 6. 依赖与关键路径

```
T1 (packs/) ────► T2 (host_registry + adapters)
                       │
                       ▼
                  T3 (pipeline + manifest + marker)
                       │
                       ▼
                  T4 (CLI 集成 + interactive)
                       │
                       ▼
                  T5 (文档 + VersionManager 注册)
```

关键路径：T1 → T2 → T3 → T4 → T5（线性，无并行机会）。

设计上 T1 与 T2 在功能上独立可并行，但本计划选择**严格线性**，理由：(a) 单 cycle / solo creator 没有并行收益；(b) 让 review/gate 阶段每次只看一个任务的 diff；(c) 避免 T1 缺失时 T2 测试无 fixture 可用。

## 7. 完成定义与验证策略

- **任务完成（per task）**：所有 Acceptance + Verify 通过；该任务相关测试全绿；既有 ≥496 用例不退绿；diff 已提交并推送。
- **里程碑完成**：里程碑包含的所有任务完成；里程碑退出标准（§2 表）通过冷读校验。
- **cycle 完成（gate 阶段）**：
  - `hf-test-driven-dev` 完成后派发 `hf-test-review`、`hf-code-review`、`hf-traceability-review`；
  - 三 review 全通过后入 `hf-regression-gate`：`uv run pytest tests/ -q` 全绿 + traceability evidence bundle；
  - 入 `hf-completion-gate` 判定走向；
  - 入 `hf-finalize` 写 closeout pack + RELEASE_NOTES 首条目更新为 F007 + task-progress 收尾。

## 8. 当前活跃任务选择规则

- **初始 active task**：T1。
- **任务完成后选择规则**：取所有 `pending` 中 `Selection Priority` 最小且 `Ready When` 全部满足的任务作为下一个 active；本计划线性结构下即按 T1 → T2 → T3 → T4 → T5。
- **若任意任务被 `hf-test-review` / `hf-code-review` / `hf-traceability-review` 打回**：该任务回到 `active`，前置任务 evidence 不重做；review 闭合后回流到原计划下一任务。
- **手动 override**：若用户显式指定其它任务，遵循用户指令并在 task-progress.md 记录原因。

## 9. 任务队列投影视图

| Task | Status | Priority | Ready | Owner | Notes |
|---|---|---|---|---|---|
| T1 | active | 1 | yes | cursor cloud agent (auto) | 首任务 |
| T2 | pending | 2 | T1 完成后 | cursor cloud agent (auto) | |
| T3 | pending | 3 | T2 完成后 | cursor cloud agent (auto) | walking skeleton 在此任务 |
| T4 | pending | 4 | T3 完成后 | cursor cloud agent (auto) | manual smoke 在此任务 |
| T5 | pending | 5 | T4 完成后 | cursor cloud agent (auto) | |

队列源：本文件 §5 + §6；不维护额外 board JSON。

## 10. 风险与顺序说明

| 风险 | 触发任务 | 缓解 |
|---|---|---|
| Cursor 实际版本不识别 `.cursor/skills/` | T2 / T4 manual smoke | 用户指南 R2 风险段；本 cycle 仍按 ADR-D7-3 选择 `.cursor/skills/` |
| `_init()` 现有签名扩展可能影响既有调用方 | T4 | `_init()` 所有新参数都有默认值；`cli.main()` 与既有 `tests/test_cli.py` 是唯一调用方，已纳入 §3.2 修改清单 |
| pytest baseline 数字偏差（实际可能 >496） | 所有任务 | 验证以 "整体不退绿" 而非 "等于 496" 判定，对齐 spec NFR-704 措辞 |
| pre-existing 2 mypy errors / 47 ruff warnings（F002-F004 历史） | 所有任务 | 不在本 cycle 修复（task-progress 既有 deferred 项）；只确保 T2-T5 不新增 mypy/ruff 错误 |
| YAML front matter 注入对 SKILL.md 的兼容性 | T3 marker 实现 | T3 测试矩阵已含 `test_skill_inject` / `test_skill_malformed_raises` / `test_agent_no_frontmatter_tolerant`，覆盖 D7 §10.4 全部分支 |
| 同名 skill 冲突路径在本 cycle 无生产 fixture | T3 | T3 测试用临时构造 `packs_a/packs_b` 覆盖（D7 §13 已注明） |

