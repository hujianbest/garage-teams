# F009: `garage init` 双 Scope 安装 + 交互式 Scope 选择 任务计划

- 状态: 草稿
- 主题: 把已批准 D009 设计拆解为可单任务推进、可冷读、可追溯的工作单元
- 日期: 2026-04-23
- Revision: r1
- 关联规格: `docs/features/F009-garage-init-scope-selection.md`（已批准 r2）
- 关联设计: `docs/designs/2026-04-23-garage-init-scope-selection-design.md`（已批准 r2，11 ADR + 6 task + 9 INV + 11 测试文件）
- 关联批准: `docs/approvals/F009-{spec,design}-approval.md`
- 关联评审: `docs/reviews/{spec,design}-review-F009-garage-init-scope-selection.md`

## 1. 概述

D009 已稳定（11 项 ADR + 6 类提交分组 + 9 条 INV 不变量 + 11 个新增测试文件 + 7 条失败模式）。本任务计划按 D009 § 10.1 6 类提交分组（T1-T6）一一对应 6 个 task，每个 task 含 Acceptance / Files / Verify / 测试设计种子 / 完成条件 + 触发的 INV + 依赖关系。

执行原则：

- **CON-901 + Dogfood 不变性硬门槛**：F007/F008 既有调用形态字节级保留（除 manifest schema migration 例外）；本仓库自身 dogfood SHA-256 与 F008 baseline 一致（INV-F9-1 sentinel test 守门）
- **CON-902 严守**：D7 安装管道 phase 1 + phase 3 算法主体严格不变（design reviewer 可拒红线）；phase 2/4/5 按 enum 允许的最小改动
- **CON-903 严守**：packs/ 内容物 + EXEMPTION_LIST 7 项不动（git diff = 空）
- **CON-904 严守**：manifest 默认不入项目 git
- **零回归保护**：任何 task 不得让 `uv run pytest tests/ -q` 既有 633 用例语义退绿（NFR-902）；carry-forward wording 修复（如 schema_version assertion）允许但需 commit message 显式声明

## 2. 里程碑

| 里程碑 | 包含任务 | 退出标准 | 对应 spec/design 锚点 |
|---|---|---|---|
| **M1 Adapter user scope path** | T1 | 三家 adapter 各加 `target_skill_path_user` + `target_agent_path_user` method；host_registry 加 host_id 不含 `:` assert；2 个新增测试 GREEN | spec FR-904 + ADR-D9-6 + ADR-D9-9 |
| **M2 Pipeline scope 分流** | T2 | `_resolve_targets` phase 2 增 scope 分流；`_Target` 增 scope 字段；`_check_conflicts` 三元组 key + `_decide_action` 5 元组 key；CON-902 phase 1 + phase 3 严格不变；1 个新增测试 GREEN | spec FR-906 + ADR-D9-2 + CON-902 |
| **M3 Manifest schema 1→2 migration** | T3 | `MANIFEST_SCHEMA_VERSION = 2` + `Manifest` dataclass 字段扩展 + `migrate_v1_to_v2` 函数 + `ManifestMigrationError` + `UserHomeNotFoundError` + `VersionManager` 注册；2 个新增测试 GREEN | spec FR-905 + ADR-D9-1/3/4/8/10 + CON-904 |
| **M4 CLI + 交互式 + status 分组** | T4 | init subparser 加 `--scope` flag + per-host override 解析 + 交互式两轮（candidate C 三个开关）+ `_status` 按 scope 分组；4 个新增测试 GREEN + carry-forward 修复 test_cli.py 既有 schema_version assertion | spec FR-901/902/903/908/909 + ADR-D9-5/7 |
| **M5 Sentinel + 集成测试** | T5 | dogfood SHA-256 sentinel + manifest 字段稳定 + user scope 三家宿主集成；3 个新增测试 GREEN | spec NFR-901 Dogfood + ADR-D9-11 + INV-F9-1 |
| **M6 文档同步** | T6 | packs/README.md "Install Scope" 段 + user-guide `--scope` 用法 + AGENTS.md F007/F008/F009 升级 + RELEASE_NOTES F009 占位段 | spec FR-910 |

## 3. 文件 / 工件影响图

### 3.1 新增（不存在 → 存在）

| 工件 | 来自任务 | 类型 |
|---|---|---|
| `tests/adapter/installer/test_adapter_user_scope.py` | T1 | unit (3 adapter user scope path) |
| `tests/adapter/installer/test_host_registry_colon_assert.py` | T1 | unit (ADR-D9-9) |
| `tests/adapter/installer/test_pipeline_scope_routing.py` | T2 | unit (phase 2 + phase 4 + phase 7) |
| `tests/adapter/installer/test_manifest_schema_v2.py` | T3 | unit (FR-905 + ADR-D9-1/3) |
| `tests/adapter/installer/test_manifest_migration_v1_to_v2.py` | T3 | unit (FR-905 migration + ManifestMigrationError) |
| `tests/test_cli.py::TestInitWithScope` | T4 | unit class (FR-901/902/909) |
| `tests/adapter/installer/test_interactive_two_round.py` | T4 | unit (FR-903 + ADR-D9-5 candidate C) |
| `tests/test_cli.py::TestStatusScopeGrouped` | T4 | unit class (FR-908 + ADR-D9-7) |
| `tests/adapter/installer/test_dogfood_invariance_F009.py` | T5 | sentinel (NFR-901 Dogfood + ADR-D9-11) |
| `tests/adapter/installer/test_manifest_v2_dogfood_fields_stable.py` | T5 | sentinel (ADR-D9-11 manifest 字段稳定互补) |
| `tests/adapter/installer/test_full_init_user_scope.py` | T5 | integration (端到端 user scope 三家宿主) |
| `tests/adapter/installer/dogfood_baseline/skill_md_sha256.json` | T5 | static fixture (F008 baseline 30 文件 SHA-256 清单) |
| `RELEASE_NOTES.md` § "F009" 段 | T6 | 占位段（finalize 阶段填实测数据）|

### 3.2 修改（既存 → 改动）

| 工件 | 来自任务 | 修改范围 |
|---|---|---|
| `src/garage_os/adapter/installer/host_registry.py` | T1 | (1) 加 `host_id` 不含 `:` import-time assert (2) `HostInstallAdapter` Protocol docstring 加约束声明 (3) `resolve_hosts_arg` 改造：返回 `list[tuple[str, str \| None]]` 而非 `list[str]`，每个 host token 解析为 `(host_id, scope_override?)` 二元组 |
| `src/garage_os/adapter/installer/hosts/claude.py` | T1 | 加 `target_skill_path_user(skill_id) -> Path` + `target_agent_path_user(agent_id) -> Path \| None`，返回 `~/.claude/skills/<id>/SKILL.md` + `~/.claude/agents/<id>.md` |
| `src/garage_os/adapter/installer/hosts/opencode.py` | T1 | 同上 + `~/.config/opencode/skills/<id>/SKILL.md` + `~/.config/opencode/agent/<id>.md` |
| `src/garage_os/adapter/installer/hosts/cursor.py` | T1 | 同上 + `~/.cursor/skills/<id>/SKILL.md`；`target_agent_path_user` 返回 `None`（与 project scope 一致） |
| `src/garage_os/adapter/installer/pipeline.py` | T2 | (1) `_Target` dataclass 增 `scope: Literal["project", "user"]` 字段 (2) `_resolve_targets` phase 2 内按 target.scope 选 base path：`base = workspace_root if scope == "project" else Path.home()` (3) `_check_conflicts` 比对 key 改为 `(host, scope, dst_abs)` 三元组 (4) `_decide_action` 比对 key 改为 `(src, dst_abs, host, pack_id, scope)` 5 元组 (5) `install_packs()` 函数签名扩展接受 `scopes_per_host: dict[str, str] \| None` optional 参数（缺省 None 等价 F007/F008 全 project）— phase 1 + phase 3 算法主体字节级不变（INV-F9-2 守门） |
| `src/garage_os/adapter/installer/manifest.py` | T3 | (1) `MANIFEST_SCHEMA_VERSION = 2`（F007 是 1）(2) **不引入新 dataclass `ManifestFileEntryV2`**：直接给既有 `ManifestFileEntry` 字段扩展（`dst: str` 改为 absolute POSIX + 新增 `scope: Literal["project", "user"]` 字段）；F007 既有 `ManifestFileEntry` 类名保留（避免双类并存）；schema 区分由顶层 `Manifest.schema_version` 字段 + `migrate_v1_to_v2` 函数承担 (3) 新增 `migrate_v1_to_v2(prior: Manifest, workspace_root: Path) -> Manifest` 函数 (4) 新增 `ManifestMigrationError(ValueError)` (5) `read_manifest` 自动 detect schema_version=1 → 调用 migrate；migration 失败时**不覆盖**旧 manifest（FR-905 验收 #4 + CON-904 安全语义） (6) `write_manifest` 始终写 schema_version=2 |
| `src/garage_os/adapter/installer/__init__.py` | T1 + T3 | export 新增类型（`ManifestMigrationError` / `UserHomeNotFoundError` / 等） |
| `src/garage_os/platform/version_manager.py` | T3 | 注册 host-installer migration 链 (1 → 2) |
| `src/garage_os/adapter/installer/interactive.py` | T4 | 新增 `prompt_scopes_per_host(host_ids: list[str], *, stdin, stderr) -> dict[str, str]` 函数：candidate C 三个开关（先问 a/u/p，选 p 才进入逐个 P/u 提示）|
| `src/garage_os/cli.py` | T4 | (1) `build_parser()` 给 init subparser 加 `--scope` flag（`choices=["project", "user"]`，`default="project"`）(2) `_init()` 接收 `scope` 参数 + 传给 `_resolve_init_hosts` (3) `_resolve_init_hosts` 改造：接收 `hosts_arg: str | None` + `scope: str` + `yes: bool`，返回 `dict[str, str]`（host → scope 映射）(4) 调用 `install_packs(scopes_per_host=...)` (5) `_status` 按 scope 分组打印（ADR-D9-7 nested bullets）|
| `tests/test_cli.py` | T4 | (1) carry-forward fixture 兼容：grep 实测 `tests/test_cli.py` 含 5 处 `"schema_version": "1"` fixture 输入字符串（line 457/505/563/640/703）— 这些是 fixture 模拟旧 manifest，T3 加 read_manifest 自动 migration 后仍能读为 schema_version=1 → 自动迁移到 schema 2，旧 fixture **不必修改**；如有任何 init 相关测试 fail 则 wording 同步放宽（commit message 显式声明）(2) 新增 `TestInitWithScope` + `TestStatusScopeGrouped` 两个 test class |
| `tests/adapter/installer/test_manifest.py` | T3（carry-forward 真实目标）| grep 实测 6 处 `schema_version=1` (line 55/77/100/121/154/171) + 1 处 `assert MANIFEST_SCHEMA_VERSION == 1` (line 47) — T3 实施后 wording 必须同步修复：(a) `MANIFEST_SCHEMA_VERSION == 1` → `MANIFEST_SCHEMA_VERSION == 2`（反映 F009 升级）(b) 6 处 `schema_version=1` fixture 输入保留（测试 v1 manifest 行为，确保 migration 测试有 v1 fixture 输入）；新增 v2 fixture 用于测试 v2 read/write；既有 6 个测试函数语义保留但 assertion 适度更新（与 NFR-901 carry-forward wording 修复同精神，commit message 显式声明）|
| `tests/adapter/installer/test_host_registry.py` | T1（in-cycle API 演化同步）| `resolve_hosts_arg` 返回类型从 `list[str]` 改为 `list[tuple[str, str | None]]`，既有测试 assert 同步更新（与 T1 commit 同 commit 落地，与 F008 carry-forward wording 修复同精神）|
| `packs/README.md` | T6 | 增 "Install Scope" 段 |
| `docs/guides/garage-os-user-guide.md` | T6 | "Pack & Host Installer" 段加 `--scope` 用法 + 交互式两轮示例 + user scope 端到端样板 |
| `AGENTS.md` | T6 | § "Packs & Host Installer (F007/F008)" → "(F007/F008/F009)" + 新增 "Install Scope" 子段 |
| `RELEASE_NOTES.md` | T6 | 新增 F009 段（占位结构）|

### 3.3 不修改（声明性兜底）

`src/garage_os/{types,storage,runtime,knowledge,adapter/host_adapter.py,adapter/claude_code_adapter.py,tools}/` 全部不动；F001-F008 既有 ≥ 633 测试 0 改写（除 T4 carry-forward wording 修复）；packs/ 内容物 + ADR-D8-9 EXEMPTION_LIST 7 项 0 改动（CON-903）。

## 4. 需求与设计追溯

| spec ID | design 锚点 | 任务 | 验证用例 |
|---|---|---|---|
| FR-901 `--scope` flag | ADR-D9-7 | T4 | `TestInitWithScope::test_scope_flag` |
| FR-902 per-host override | ADR-D9-9 | T1 + T4 | `test_host_registry_colon_assert` + `TestInitWithScope::test_per_host_override` |
| FR-903 交互式两轮 | ADR-D9-5 | T4 | `test_interactive_two_round` |
| FR-904 user scope path | ADR-D9-6 + § 2.3 | T1 | `test_adapter_user_scope` |
| FR-905 manifest schema migration | ADR-D9-1/3/8 | T3 | `test_manifest_schema_v2` + `test_manifest_migration_v1_to_v2` |
| FR-906 pipeline scope 分流 | ADR-D9-2 + CON-902 | T2 | `test_pipeline_scope_routing` |
| FR-907 跨 scope 冲突 | ADR-D9-2 | T2 | `test_pipeline_scope_routing::test_cross_scope_no_conflict` |
| FR-908 status 分组 | ADR-D9-7 | T4 | `TestStatusScopeGrouped` |
| FR-909 stdout 派生 | ADR-D9-7 | T4 | `TestInitWithScope::test_stdout_marker_F007_compat` |
| FR-910 文档 | — | T6 | 人工 review |
| NFR-901 字节级 + Dogfood | ADR-D9-11 | T5 | `test_dogfood_invariance_F009` + `test_manifest_v2_dogfood_fields_stable` |
| NFR-902 测试基线 | § 13 | 全 PR | `pytest tests/ -q` ≥ 633 + 新增 |
| NFR-903 跨平台 | — | T1 + T2 | `Path.home()` + `Path.as_posix()` |
| NFR-904 git diff 可审计 | § 10.1 | 全 PR | 6 commit 分组 |
| CON-901 兼容 F002/F007/F008 | NFR-901 | 全 PR | INV-F9-1 sentinel + carry-forward |
| CON-902 phase 1 + phase 3 严格 | ADR-D9-2 | T2 | `git diff` 人工 + design-review |
| CON-903 packs + EXEMPTION_LIST | — | 全 PR | git diff = 空 |
| CON-904 manifest 不入 git | — | T3 | `.gitignore` 已含排除 |
| § 4.2 F009 边界（按 spec § 4.2 8 条逐条 enum）| | | |
| ↳ "F007 安装管道核心算法不变" | CON-902 + ADR-D9-2 | T2 | `inspect.getsource(_check_conflicts)` 比对 main 分支字节级一致 + design-review 人工 |
| ↳ "manifest schema migration 单向" | CON-904 + ADR-D9-1/3 | T3 | `test_manifest_migration_v1_to_v2::test_no_v2_to_v1_reverse` |
| ↳ "Path.home() stdlib 标准" | NFR-903 + ADR-D9-10 | T1 + T3 | `test_adapter_user_scope::test_path_home_used` + `test_user_home_not_found_error` |
| ↳ "OpenCode XDG 默认" | ADR-D9-6 + § 2.3 | T1 | `test_adapter_user_scope::test_opencode_xdg_default` |
| ↳ "不动 HostInstallAdapter Protocol 既有 method" | ADR-D9-6 | T1 | `test_adapter_user_scope::test_F007_methods_unchanged` (inspect.getsource) |
| ↳ "不动 packs/ 内容物" | CON-903 | 全 PR | `git diff main..HEAD -- packs/` 输出空 |
| ↳ "不动 F008 ADR-D8-9 EXEMPTION_LIST" | CON-903 | 全 PR | `git diff main..HEAD -- tests/adapter/installer/test_neutrality_exemption_list.py` 输出空 |
| ↳ "dogfood 不受影响" | NFR-901 + ADR-D9-11 | T5 | `test_dogfood_invariance_F009::test_dogfood_skill_md_sha256_match` |
| ↳ "scope 不引入新优先级语义" | spec § 4.2 + ADR-D9-1 | 全 PR | 设计上不实施任何 scope 优先级解析（Garage 不替宿主决定）|

## 5. 任务拆解

### T1. Adapter user scope path + host_id 命名约束

- **目标**: 三家 first-class adapter（claude/opencode/cursor）各加 `target_skill_path_user` + `target_agent_path_user` optional method（绝对路径返回值）；`host_registry.py` 加 host_id 不含 `:` import-time assert + Protocol docstring 约束声明 + `resolve_hosts_arg` 改造接收二元组。
- **Acceptance**:
  - `ClaudeInstallAdapter().target_skill_path_user("hf-specify") == Path.home() / ".claude/skills/hf-specify/SKILL.md"`
  - `ClaudeInstallAdapter().target_agent_path_user("garage-sample-agent") == Path.home() / ".claude/agents/garage-sample-agent.md"`
  - `OpenCodeInstallAdapter().target_skill_path_user("hf-specify") == Path.home() / ".config/opencode/skills/hf-specify/SKILL.md"`
  - `OpenCodeInstallAdapter().target_agent_path_user("garage-sample-agent") == Path.home() / ".config/opencode/agent/garage-sample-agent.md"`
  - `CursorInstallAdapter().target_skill_path_user("hf-specify") == Path.home() / ".cursor/skills/hf-specify/SKILL.md"`
  - `CursorInstallAdapter().target_agent_path_user("garage-sample-agent") is None`（无 agent surface）
  - `host_registry._build_registry()` 在 import 时 `assert all(":" not in host_id for host_id in HOST_REGISTRY)` 通过
  - `resolve_hosts_arg("claude:user,cursor")` 返回 `[("claude", "user"), ("cursor", None)]`（None 表示用 `--scope` 全局默认）
  - `resolve_hosts_arg("claude:bad")` 抛 `UnknownScopeError`（与 `UnknownHostError` 对称的新类型）
  - 既有 F007 `target_skill_path` / `target_agent_path` / `render` method 签名零变更（INV-F9-2 间接守门）
- **依赖**: 无（M1 起点）
- **Ready When**: 当前分支已就位
- **初始队列状态**: ready
- **Selection Priority**: 1
- **Files / 触碰工件**:
  - 修改 `src/garage_os/adapter/installer/host_registry.py`
  - 修改 `src/garage_os/adapter/installer/hosts/{claude,opencode,cursor}.py`
  - 修改 `src/garage_os/adapter/installer/__init__.py`（export `UnknownScopeError`）
  - 新增 `tests/adapter/installer/test_adapter_user_scope.py`
  - 新增 `tests/adapter/installer/test_host_registry_colon_assert.py`
- **测试设计种子**:
  - 主行为：`ClaudeInstallAdapter().target_skill_path_user("hf-specify")` 返回 absolute Path 含 `Path.home()`
  - 关键边界：cursor `target_agent_path_user` 返回 None；opencode 用 XDG `~/.config/opencode/`
  - fail-first 适用点：先写 `test_adapter_user_scope.py` 跑 RED → 实现 method → GREEN
  - host_id assert: `test_host_registry_colon_assert::test_no_host_contains_colon` 验证当前 3 家通过；`test_assert_fires_on_violation` 用 monkeypatch 注入虚假 adapter 验证 assert 触发
- **Verify**:
  - `.venv/bin/pytest tests/adapter/installer/test_adapter_user_scope.py -v` GREEN
  - `.venv/bin/pytest tests/adapter/installer/test_host_registry_colon_assert.py -v` GREEN
  - `.venv/bin/pytest tests/ -q` 整体 ≥ 633 + 新增（T1 增量预期 ≥ 6）
  - `git diff main..HEAD -- src/garage_os/adapter/installer/hosts/{claude,opencode,cursor}.py | grep -E '^[+-]' | grep -v '^[+-][+-][+-]' | wc -l` 应有改动（新增 method）
  - 既有 30 个 installer 测试 0 退绿
- **预期证据**: PR commit `f009(adapter): 三家 first-class adapter 加 user scope path + host_id 命名约束`
- **完成条件**: 6 个 method 实现 + 2 个测试文件 GREEN + 既有测试 0 退绿 + commit 落地

### T2. Pipeline scope 分流（CON-902 严守）

- **目标**: `pipeline._resolve_targets` phase 2 内按 target.scope 选 base path；`_Target` dataclass 增 `scope` 字段；`_check_conflicts` 三元组 key + `_decide_action` 5 元组 key；`install_packs()` 函数签名扩展 optional `scopes_per_host` 参数（缺省 None 兼容 F007）；CON-902 phase 1 + phase 3 算法主体字节级严格不变。
- **Acceptance**:
  - `_Target` dataclass 增 `scope: Literal["project", "user"]` 字段
  - `install_packs(workspace, packs, hosts, scopes_per_host=None)` 函数签名扩展；`scopes_per_host=None` 等价 F007/F008 全 project（CON-901）
  - `install_packs(workspace, packs, ["claude", "cursor"], scopes_per_host={"claude": "user", "cursor": "project"})` 把 claude 装到 `Path.home() / .claude/skills/`，cursor 装到 `workspace / .cursor/skills/`
  - `_check_conflicts` 比对 key 改为 `(host, scope, dst_abs)` 三元组：跨 scope 同 dst（如 `claude:user` + `claude:project`）不视为冲突
  - `_decide_action` 比对 key 改为 5 元组（含 scope）
  - **CON-902 严守**：`git diff main..HEAD -- src/garage_os/adapter/installer/pipeline.py` 检查 phase 1 (`discover_packs` 调用部分) + phase 3 (`_check_conflicts` 主体) 算法主体字节级不变（仅 type signatures 因 _Target 增 scope 字段而扩展）
  - 既有 F007/F008 既有调用形态（不传 `scopes_per_host`）行为字节级不变（除 manifest schema migration 例外，由 T3 实施）
- **依赖**: T1（adapter user scope path 已实现）
- **Ready When**: T1 完成
- **初始队列状态**: pending
- **Selection Priority**: 2
- **Files / 触碰工件**:
  - 修改 `src/garage_os/adapter/installer/pipeline.py`
  - 新增 `tests/adapter/installer/test_pipeline_scope_routing.py`
- **测试设计种子**:
  - 主行为：fixture 跑 `install_packs(scopes_per_host={"claude": "user"})` + monkeypatch `Path.home()` 到 tmp_path 子目录，验证落盘到正确位置
  - 关键边界：(a) `scopes_per_host=None` 等价 F007 行为 (b) 跨 scope 不冲突 (c) phase 1 + phase 3 字节级不变（用 `inspect.getsource` 提取函数文本对比）
  - fail-first 适用点：先写 fail-first 测试 → 实现分流 → GREEN
- **Verify**:
  - `.venv/bin/pytest tests/adapter/installer/test_pipeline_scope_routing.py -v` GREEN
  - `.venv/bin/pytest tests/ -q` 整体 ≥ 633 + 新增（T2 增量预期 ≥ 5）
  - 既有 `tests/adapter/installer/test_pipeline.py` 0 退绿（CON-901 + CON-902 双重守门）
  - 人工检查 `pipeline.py` `_check_conflicts` 函数主体（除 type signature）字节级与 main 分支一致
- **预期证据**: PR commit `f009(pipeline): phase 2 scope 分流 + phase 4 5 元组比对 (CON-902 严守)`
- **完成条件**: pipeline 改造完成 + INV-F9-2 守门通过 + 1 个测试 GREEN + commit 落地

### T3. Manifest schema 1→2 migration

- **目标**: `MANIFEST_SCHEMA_VERSION = 2` + 既有 `ManifestFileEntry` dataclass **字段扩展**（不引入新类，参见 § 3.2 改动范围）+ `migrate_v1_to_v2(prior, workspace_root)` 函数 + `ManifestMigrationError` + `UserHomeNotFoundError` + `VersionManager` 注册 host-installer migration 链；`read_manifest` 自动 detect schema_version=1 → 调 migrate；migration 失败时**不覆盖**旧 manifest（FR-905 验收 #4 + CON-904 安全语义硬门槛）；`write_manifest` 始终写 schema_version=2。
- **Acceptance**:
  - `MANIFEST_SCHEMA_VERSION` 常量从 1 升到 2
  - **既有 `ManifestFileEntry` 类名保留 + 字段扩展**（与 § 3.2 修改范围段一致；不引入新 `ManifestFileEntryV2` 类）：`src: str / dst: str (absolute POSIX) / host: str / pack_id: str / scope: Literal["project", "user"] / content_hash: str`
  - `migrate_v1_to_v2(prior_v1, workspace_root)`：每条 entry `scope = "project"` + `dst = (workspace_root / dst_relative).as_posix()`；schema_version 1 → 2；其它字段保持
  - `ManifestMigrationError(ValueError)`：JSON 损坏或字段缺失时抛
  - `UserHomeNotFoundError(RuntimeError)`：`Path.home()` 抛 RuntimeError 时 catch + raise（ADR-D9-10）
  - `read_manifest` 检测 schema_version=1 自动 migrate；`write_manifest` 始终写 schema_version=2
  - **(安全语义硬门槛, FR-905 验收 #4 + CON-904)** Migration 失败时旧 manifest 文件**字节级不被覆盖**：测试 `test_manifest_migration_v1_to_v2::test_corrupted_manifest_not_overwritten` 守门 — fixture 写一个损坏 JSON 到 host-installer.json，调用 `read_manifest` 抛 ManifestMigrationError 后，`stat` 文件 mtime + 内容 SHA-256 与 fixture 写入时完全一致
  - `VersionManager` host-installer migration 链注册（与 F007 既有 platform.json / host-adapter.json 同等待遇）
  - F008 既有 manifest schema 1 自动迁移成功 + 旧 entry 默认 `scope: "project"` + dst 转 absolute
- **依赖**: T2（pipeline 改造完成，需要 _Target.scope 写入 manifest）
- **Ready When**: T2 完成
- **初始队列状态**: pending
- **Selection Priority**: 3
- **Files / 触碰工件**:
  - 修改 `src/garage_os/adapter/installer/manifest.py`（核心改动）
  - 修改 `src/garage_os/adapter/installer/__init__.py`（export 新错误类型）
  - 修改 `src/garage_os/platform/version_manager.py`（注册 migration 链）
  - 新增 `tests/adapter/installer/test_manifest_schema_v2.py`
  - 新增 `tests/adapter/installer/test_manifest_migration_v1_to_v2.py`
  - **carry-forward (in-cycle wording 修复)**: 修改 `tests/adapter/installer/test_manifest.py`（grep 实测含 6 处 `schema_version=1` line 55/77/100/121/154/171 + 1 处 `assert MANIFEST_SCHEMA_VERSION == 1` line 47；T3 实施时把 line 47 assert 改为 `assert MANIFEST_SCHEMA_VERSION == 2`，6 处 `schema_version=1` fixture 输入保留以测 v1 → v2 migration 路径，新增 v2 fixture 与测试覆盖；commit message 显式声明 carry-forward）
- **测试设计种子**:
  - 主行为：`migrate_v1_to_v2` 函数对 F008 schema 1 fixture 输入 → 返回 schema 2 输出 + 字段正确
  - 关键边界：(a) JSON 损坏抛 ManifestMigrationError + **旧 manifest 不被覆盖**（FR-905 验收 #4 安全语义硬门槛，由 `test_corrupted_manifest_not_overwritten` 测试守门）(b) `Path.home()` RuntimeError → UserHomeNotFoundError (c) `read_manifest` 对 schema_version=2 直接读不 migrate (d) `write_manifest` 始终写 schema_version=2
  - fail-first 适用点：先写 RED 测试（特别是 `test_corrupted_manifest_not_overwritten`：先写 + 跑应 RED → 实现 read_manifest 错误处理路径不覆盖文件 → GREEN）→ 实现 migration → GREEN
- **Verify**:
  - `.venv/bin/pytest tests/adapter/installer/test_manifest_schema_v2.py -v` GREEN
  - `.venv/bin/pytest tests/adapter/installer/test_manifest_migration_v1_to_v2.py -v` GREEN（**含 `test_corrupted_manifest_not_overwritten` 安全语义守门**）
  - `.venv/bin/pytest tests/adapter/installer/test_manifest.py -v` GREEN（含 carry-forward wording 修复后；既有 6 处 schema_version=1 fixture 输入保留 + line 47 assert 改为 == 2 + 新增 v2 测试覆盖）
  - `.venv/bin/pytest tests/ -q` 整体 ≥ 633 + 新增（T3 增量预期 ≥ 6）
  - **既有 `tests/test_cli.py` 中 5 处 fixture 输入 `"schema_version": "1"` (line 457/505/563/640/703) 不必修改**：T3 加 read_manifest 自动 migration 后，旧 fixture 仍能被读为 schema_version=1 → 自动迁移到 schema 2，行为透明（design-review-F009 r1 important #2 + tasks-review-F009 r1 important #2 显式分清 carry-forward 真实目标在 test_manifest.py 而非 test_cli.py）
- **预期证据**: PR commit `f009(manifest): schema 1 → 2 migration + ManifestMigrationError + UserHomeNotFoundError + VersionManager 注册 + carry-forward test_manifest.py wording 修复`
- **完成条件**: 两个错误类型 + migration 函数 + read/write_manifest 改造 + 2 个新增测试 GREEN + 既有 test_manifest.py carry-forward 修复后 GREEN + 安全语义硬门槛测试 GREEN + commit 落地

### T4. CLI + 交互式 + status 分组

- **目标**: `cli.py` init subparser 加 `--scope` flag + `_init` 接收 scope 参数 + `_resolve_init_hosts` 改造 + `interactive.prompt_scopes_per_host` (candidate C) + `_status` 按 scope 分组；test_cli.py 既有 init 相关测试 carry-forward wording 修复 + 新增 `TestInitWithScope` + `TestStatusScopeGrouped` 两个 test class + 新增 `test_interactive_two_round.py`。
- **Acceptance**:
  - `garage init --hosts claude --scope user` 退出码 0 + SKILL.md 落到 `~/.claude/skills/`（fixture-isolated）
  - `garage init --hosts claude:user,cursor:project` per-host override 正确分流
  - `garage init --hosts claude:bad` 退出码 1 + stderr 含 `Unknown scope: bad in 'claude:bad'`
  - TTY 下 `garage init` 进入两轮交互（candidate C 三个开关 a/u/p）
  - non-TTY 沿用 F007 FR-703 退化（`--hosts none` + stderr 提示，不附加 F009 scope 提示，FR-903 验收 #4）
  - `garage status` 按 scope 分组打印（ADR-D9-7 nested bullets 格式）
  - F007 既有 stdout marker `Installed N skills, M agents into hosts: <list>` 字面不变；多 scope 时另起一行附加（FR-909）
  - `grep -cE '^Installed [0-9]+ skills, [0-9]+ agents into hosts:'` stdout 命中 == 1（F007 grep 兼容）
  - 既有 `test_cli.py::TestInitWithHosts` 100% 通过（CON-901）；**注意**: tasks-review-F009 r1 important #2 已实测 grep 确认 test_cli.py 5 处 `"schema_version": "1"` (line 457/505/563/640/703) 是 fixture 输入字符串而非 assertion，T3 加 read_manifest 自动 migration 后旧 fixture 透明兼容，**T4 不需要修改 test_cli.py 中 schema_version 相关 fixture**；如 T4 实施时跑 既有 init 相关测试有 fail，则按需 wording 同步放宽（commit message 显式声明）
- **依赖**: T3（manifest schema 2 已实现）
- **Ready When**: T3 完成
- **初始队列状态**: pending
- **Selection Priority**: 4
- **Files / 触碰工件**:
  - 修改 `src/garage_os/cli.py`（init subparser + `_init` + `_resolve_init_hosts` + `_status`）
  - 修改 `src/garage_os/adapter/installer/interactive.py`（新增 `prompt_scopes_per_host`）
  - 修改 `tests/test_cli.py`（carry-forward + 新增 `TestInitWithScope` + `TestStatusScopeGrouped`）
  - 新增 `tests/adapter/installer/test_interactive_two_round.py`
- **测试设计种子**:
  - 主行为：`TestInitWithScope::test_scope_user_explicit` fixture monkeypatch `Path.home()` 到 tmp_path/home，跑 `garage init --hosts claude --scope user`，验证 `tmp_path/home/.claude/skills/` 存在
  - 关键边界：(a) per-host override 解析正确 (b) F007 grep 兼容 (c) candidate C a 一键回车默认 = F007 行为 (d) non-TTY 退化不附加 F009 scope 文字
  - fail-first 适用点：先写 RED 测试 → 实现 CLI flag + 交互式 → GREEN
- **Verify**:
  - `.venv/bin/pytest tests/test_cli.py -v` GREEN（含既有 init 相关 + 新增 TestInitWithScope + TestStatusScopeGrouped）
  - `.venv/bin/pytest tests/adapter/installer/test_interactive_two_round.py -v` GREEN
  - `.venv/bin/pytest tests/ -q` 整体 ≥ 633 + 新增（T4 增量预期 ≥ 10）
  - 人工检查 stdout marker grep 兼容（FR-909 验收）
- **预期证据**: PR commit `f009(cli): --scope flag + per-host override + 交互式两轮 + status scope 分组`
- **完成条件**: CLI + interactive + status 改造完成 + 4 个测试 / class GREEN + carry-forward 显式声明 + commit 落地

### T5. Sentinel + 集成测试 (NFR-901 Dogfood + ADR-D9-11)

- **目标**: 落地 `test_dogfood_invariance_F009.py` SHA-256 sentinel + `test_manifest_v2_dogfood_fields_stable.py` 字段稳定 + `test_full_init_user_scope.py` 端到端集成 + `dogfood_baseline/skill_md_sha256.json` 静态 fixture（含 F008 baseline 30 文件 SHA-256 清单）。
- **Acceptance**:
  - `test_dogfood_invariance_F009::test_dogfood_skill_md_sha256_match`：fixture 在 tmp_path 内 `cp -r packs/` → `garage init --hosts cursor,claude`（无 scope，默认 project，dogfood 路径），比对 .{host}/skills/<id>/SKILL.md + .claude/agents/garage-sample-agent.md 的 SHA-256 与 `dogfood_baseline/skill_md_sha256.json` 一致
  - `test_manifest_v2_dogfood_fields_stable::test_manifest_fields_stable`：同上 fixture，read_manifest 后比对 `files[].content_hash` + `files[].scope == "project"` + `files[].host` 字段稳定
  - `test_full_init_user_scope::test_install_three_hosts_user_scope`：fixture monkeypatch `Path.home()` 到 tmp_path/home，跑 `garage init --hosts all --scope user`，验证三家宿主目录全部存在 + manifest schema 2 含 `scope: "user"` entry 87+ 条；**enum 三家 user scope 落盘路径**（ADR-D9-6 + § 2.3 调研锚点）：
    - `tmp_path/home/.claude/skills/<id>/SKILL.md` × 29 + `tmp_path/home/.claude/agents/<id>.md` × 1
    - `tmp_path/home/.config/opencode/skills/<id>/SKILL.md` × 29 + `tmp_path/home/.config/opencode/agent/<id>.md` × 1（**XDG default**，不走 dotfiles `~/.opencode/skills/` 路径，spec § 11 阻塞性问题已选定）
    - `tmp_path/home/.cursor/skills/<id>/SKILL.md` × 29（无 agent surface，与 F007 一致）
  - `dogfood_baseline/skill_md_sha256.json` 是 T5 commit 落地的静态 fixture（不依赖 cycle 内任何 commit 之间的环境差异）
- **依赖**: T4（CLI 完成才能跑 garage init 端到端）
- **Ready When**: T4 完成
- **初始队列状态**: pending
- **Selection Priority**: 5
- **Files / 触碰工件**:
  - 新增 `tests/adapter/installer/test_dogfood_invariance_F009.py`
  - 新增 `tests/adapter/installer/test_manifest_v2_dogfood_fields_stable.py`
  - 新增 `tests/adapter/installer/test_full_init_user_scope.py`
  - 新增 `tests/adapter/installer/dogfood_baseline/skill_md_sha256.json`（静态 fixture）
- **测试设计种子**:
  - 主行为：dogfood sentinel 比对 SHA-256 一致；user scope 集成跑端到端三家宿主全装
  - 关键边界：(a) baseline JSON **录制方式选定**（design-review-F009 r1 important #3 + tasks-review-F009 r1 important #3 显式收敛）：候选 A — 由 hf-test-driven-dev executor 在 T5 实施时**首跑** install_packs 后 read SHA-256 写入静态 fixture JSON（人工 review 后 commit）；候选 B — 用 F008 cycle 末实测 SHA-256 静态副本（需要 git revert 到 F008 closeout commit `bafbd1c` 重跑 dogfood）；选定 **候选 A** 理由：F009 实施期 marker injection 逻辑无变化（CON-902 phase 2 仅改 base path 选择），首跑 SHA-256 即等价 F008 baseline；候选 B 需要历史 commit 重跑增加复杂度；**关键约束**：T5 commit 中 baseline JSON 由 hf-test-driven-dev executor 在 fixture 内首跑 garage init 后 read SHA-256 写入，并由人工 review SHA-256 数值合理性（参考 packs/ 内容物 + F007 marker injection 规则） (b) test_full_init_user_scope 用 monkeypatch `Path.home()` 隔离 (c) dogfood sentinel 不测 manifest（ADR-D9-11）
  - fail-first 适用点：sentinel 先 commit 一个能 RED 的 baseline（故意错误 SHA-256）→ 跑 RED → 修正 baseline → GREEN（演示 sentinel 真有守门能力）
- **Verify**:
  - `.venv/bin/pytest tests/adapter/installer/test_dogfood_invariance_F009.py -v` GREEN
  - `.venv/bin/pytest tests/adapter/installer/test_manifest_v2_dogfood_fields_stable.py -v` GREEN
  - `.venv/bin/pytest tests/adapter/installer/test_full_init_user_scope.py -v` GREEN
  - `.venv/bin/pytest tests/ -q` 整体 ≥ 633 + 新增（T5 增量预期 ≥ 6）
- **预期证据**: PR commit `f009(tests): Dogfood 不变性 sentinel + manifest 字段稳定 + user scope 全装集成测试 + baseline fixture`
- **完成条件**: 3 个测试 GREEN + baseline JSON 落地 + commit 落地

### T6. 文档同步

- **目标**: `packs/README.md` 增 "Install Scope" 段；`docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段加 `--scope` 用法 + 交互式两轮示例；`AGENTS.md` § "Packs & Host Installer (F007/F008)" 升级到 F007/F008/F009 + 新增 "Install Scope" 子段；`RELEASE_NOTES.md` 新增 F009 段（占位结构 + 5 项 TBD 占位字段，hf-finalize 阶段填实测）。
- **Acceptance**:
  - `grep -E 'Install Scope' packs/README.md` 命中
  - `grep -E '\\-\\-scope' docs/guides/garage-os-user-guide.md` 命中
  - `grep -E 'Packs & Host Installer \\(F007/F008/F009\\)' AGENTS.md` 命中
  - `grep -E '^## F009' RELEASE_NOTES.md` 命中
  - 5 项占位字段 enum 在 RELEASE_NOTES F009 段（manual_smoke_wall_clock / pytest_total_count / installed_packs_from_manifest / commit_count_per_group / release_notes_quality_chain）
  - 任意新 Agent / 新用户从 AGENTS.md 出发，5 分钟内能回答 (a) project/user scope 区别 (b) 怎么选 (c) per-host override 怎么写 三个问题
- **依赖**: T1 + T2 + T3 + T4 + T5 全部完成（文档反映最终状态）
- **Ready When**: 所有前序 task 完成
- **初始队列状态**: pending
- **Selection Priority**: 6
- **Files / 触碰工件**:
  - 修改 `packs/README.md`
  - 修改 `docs/guides/garage-os-user-guide.md`
  - 修改 `AGENTS.md`
  - 修改 `RELEASE_NOTES.md`（新增 F009 段，占位）
- **测试设计种子**:
  - 主行为：4 处 grep 命中
  - 关键边界：F008 段不被破坏（grep `^## F008` 仍命中）；packs/README.md "当前 packs" 表保持
  - fail-first 适用点：N/A（文档级 task；review 阶段人工 review）
- **Verify**: 上述 grep 全部命中 + 人工 review
- **预期证据**: PR commit `f009(docs): packs/README + user-guide + AGENTS.md + RELEASE_NOTES F009 占位段`
- **完成条件**: 4 文档全部更新 + commit 落地

## 6. 依赖与关键路径

```
T1 ──→ T2 ──→ T3 ──→ T4 ──→ T5 ──→ T6
```

**关键路径**: 6 跳串行；调度按 P 升序（router 不并发）。

**关键约束**:
- T2 依赖 T1 (adapter user scope method 已实现)
- T3 依赖 T2 (pipeline phase 2/4 已扩展，需要 _Target.scope 写入 manifest)
- T4 依赖 T3 (manifest schema 2 已可读写)
- T5 依赖 T4 (CLI 完成才能跑 garage init 端到端)
- T6 必须在所有 T1-T5 完成之后

## 7. 完成定义与验证策略

cycle 完成定义：

1. T1-T6 全部 commit 落地
2. INV-F9-1..9 全部通过（详见 design § 11.1）
3. spec § 4.2 + NFR-901 + CON-902 + CON-904 多重约束全部通过
4. `pytest tests/ -q` ≥ 633 + 25（实际预期 ≥ 30；详见 design § 13）
5. `git diff main..HEAD -- src/garage_os/{types,storage,runtime,knowledge,tools}/ packs/ tests/adapter/installer/test_neutrality_exemption_list.py` 输出空（CON-903 守门）
6. `git diff main..HEAD -- pyproject.toml uv.lock` 输出空（零依赖变更）
7. End-to-end smoke 在 PR walkthrough 提供证据（dogfood + tmp 双轨）

验证顺序（hf-test-driven-dev 阶段执行）：
- 每个 task commit 后跑该 task 的 Verify 命令 + INV 守门
- 全 PR 跑 `pytest tests/ -q` + `mypy src/`（如适用）
- T5 完成后跑 manual smoke walkthrough（dogfood + user scope 两轨）

## 8. 当前活跃任务选择规则

按依赖图 DFS + Priority 升序串行：

1. T1 是绝对起点（P=1，无依赖）
2. T1 完成 → T2 ready
3. T2 完成 → T3 ready
4. T3 完成 → T4 ready
5. T4 完成 → T5 ready
6. T5 完成 → T6 ready

router 在每个 task 完成后按上述规则重选下一 task。

## 9. 任务队列投影视图

```
[T1] adapter        ready    P=1
[T2] pipeline       pending  P=2  ← T1
[T3] manifest       pending  P=3  ← T2
[T4] cli            pending  P=4  ← T3
[T5] tests          pending  P=5  ← T4
[T6] docs           pending  P=6  ← T5
```

## 10. 风险与顺序说明

| 风险 | 缓解 | 锚点 |
|---|---|---|
| T1 测试 fixture 不隔离 `Path.home()` 污染真实 ~/ | 全部 user scope 测试用 `tmp_path` + monkeypatch `Path.home()` 隔离（INV-F9-8）| design § 14 F4 |
| T2 phase 1 + phase 3 算法主体被意外修改 | INV-F9-2 守门 + design-review 时人工检查 + 加自动化检测脚本（如 `inspect.getsource` 比对）| design § 14 + CON-902 |
| T3 既有 test_manifest.py 真实 carry-forward 目标（grep 实测 6 处 `schema_version=1` line 55/77/100/121/154/171 + 1 处 `assert MANIFEST_SCHEMA_VERSION == 1` line 47）| T3 commit 内同步修复：line 47 assert 改为 `== 2`；6 处 `schema_version=1` fixture 输入保留以测 v1 → v2 migration 路径；commit message 显式声明 carry-forward | design § 14 F7 + tasks-review-F009 r1 important #2 |
| T4 既有 test_cli.py 中 `"schema_version": "1"` 是 fixture 输入字符串而非 assertion（grep 实测 line 457/505/563/640/703） | T3 加 read_manifest 自动 migration 后透明兼容，**T4 不需要修改 test_cli.py 中 schema_version 相关 fixture**；如 T4 实施时跑既有 init 相关测试有 fail 才按需 wording 放宽（commit message 显式声明）| design § 14 F7 + tasks-review-F009 r1 important #2 |
| T5 baseline JSON 录制方式偏差 | tasks-review-F009 r1 important #3 收敛：选定**候选 A**（hf-test-driven-dev executor 在 T5 fixture 内首跑 install_packs 后 read SHA-256 写入静态 JSON + 人工 review 数值合理性，参考 packs/ 内容物 + F007 marker injection 规则）；候选 B（git revert 到 F008 closeout commit `bafbd1c` 重跑）因增加复杂度被 reject；未来如发现偏差视为 sentinel 失败 | design § 18 #1 + tasks-review-F009 r1 important #3 |
| T5 dogfood sentinel 在贡献者 cwd 不同时假性 RED | sentinel 仅测 SKILL.md + agent.md 字节级（manifest 不参与，ADR-D9-11） | design ADR-D9-11 |
| T6 RELEASE_NOTES F009 段 5 项 TBD 在实施期是占位，finalize 阶段填 | T6 acceptance 写明占位段 + 5 项 enum；hf-finalize 阶段（hf-finalize）补实测数据 | design § 18 #3 |
