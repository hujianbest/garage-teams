# D009: `garage init` 双 Scope 安装 + 交互式 Scope 选择 设计

- 状态: 草稿
- 日期: 2026-04-23
- Revision: r1
- 关联规格: `docs/features/F009-garage-init-scope-selection.md`（已批准 r2，见 `docs/approvals/F009-spec-approval.md`）
- 关联评审: `docs/reviews/spec-review-F009-garage-init-scope-selection.md`（r1 需修改 → r2 通过）
- 关联前序设计: `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`（D7）+ `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（D8）— 本 cycle 严守 D7 算法骨架不动 + D8 packs 内容物不动
- 关联前序代码: `src/garage_os/adapter/installer/{pack_discovery,pipeline,manifest,host_registry}.py` + `hosts/{claude,opencode,cursor}.py` + `src/garage_os/cli.py`（init 子命令）+ `src/garage_os/platform/version_manager.py`

## 1. 概述

D009 把 spec 7 个 FR 拆成 6 类工程动作（与 NFR-904 六类提交分组对齐）：

1. **Adapter user scope 路径解析**：3 家 first-class adapter 各加 `target_skill_path_user` / `target_agent_path_user` optional method（绝对路径返回值）
2. **Pipeline scope 分流**：`_resolve_targets` phase 2 内按 target.scope 选 base path（project = workspace_root，user = `Path.home()`）；其它 phase 算法骨架严格不动（CON-902 硬约束）
3. **Manifest schema 1 → 2 migration**：VersionManager 接管自动 migration；`files[].dst` absolute path + 新增 `files[].scope` 字段
4. **CLI 接口扩展**：新增 `--scope` flag + per-host override 语法 + 交互式两轮 scope 选择（含 design 选定的 UX 候选）
5. **`garage status` scope 分组**：按 `installed_packs[].scope` 分组展示
6. **文档同步**：`packs/README.md` + `docs/guides/garage-os-user-guide.md` + `AGENTS.md` + `RELEASE_NOTES.md`

D009 **零修改 packs/ 内容物**（CON-903），**严守 D7 phase 1 + phase 3 算法主体不变**（CON-902 design reviewer 可拒红线），**严守 dogfood SHA-256 字节级与 F008 baseline 一致**（NFR-901 验收 "Dogfood 不变性硬门槛"）。

## 2. 设计驱动因素

### 2.1 来自规格的核心驱动力（FR）

| FR | 设计承接要点 |
|---|---|
| FR-901 `--scope` flag | `cli.py:build_parser()` 给 init subparser 加 `--scope <choices>`（choices=`["project", "user"]`，default=`"project"`）；`_init()` 接收 `scope` 参数传给 `_resolve_init_hosts` |
| FR-902 per-host override 语法 | `host_registry.resolve_hosts_arg()` 改造：把单 host token 解析为 `(host_id, scope_override?)` 二元组；返回 `list[tuple[str, str | None]]` 而非 F007 既有 `list[str]`；`scope_override=None` 表示用 `--scope` 全局默认 |
| FR-903 交互式两轮 scope 选择（含 ADR-D9-5 选定） | `interactive.py` 新增 `prompt_scopes_per_host(host_ids, *, stdin, stderr) -> dict[str, str]`：在 F007 既有 `prompt_hosts` 后 chain；按 ADR-D9-5 选定的 candidate C 三选一开关（all P / all u / per-host） |
| FR-904 user scope 路径解析（3 adapter）| `hosts/{claude,opencode,cursor}.py` 各加 `target_skill_path_user(skill_id) -> Path`（absolute）+ `target_agent_path_user(agent_id) -> Path \| None`（claude/opencode 返回 absolute，cursor 返回 None）；具体 path 由 ADR-D9-6 method 命名 + ADR-D9-4 absolute path 形态确定 |
| FR-905 manifest schema 1 → 2 migration | `manifest.py` 新增 `MANIFEST_SCHEMA_VERSION = 2` + `Manifest` dataclass 增 `files[].dst` absolute + `files[].scope` 字段 + 新增 `migrate_v1_to_v2(prior: Manifest) -> Manifest` 函数；`platform/version_manager.py` 注册 host-installer migration 链 |
| FR-906 pipeline scope 分流（CON-902 严守）| `pipeline._resolve_targets` 内按 target.scope 选 base path：`base = workspace_root if scope == "project" else Path.home()`；`_Target` dataclass 增 `scope: Literal["project", "user"]` 字段 |
| FR-907 跨 scope 冲突 | `pipeline._check_conflicts` 比对 key 改为 `(host, scope, dst_abs)` 三元组（同 scope 内冲突保留 F007 行为，跨 scope 不视作冲突，自然由 key 不同实现）|
| FR-908 garage status scope 分组 | `cli.py:_status` 读 manifest 后按 `files[].scope` 分组打印 |
| FR-909 stdout marker 派生（不破坏 F007 grep） | `pipeline.install_packs` summary 段在多 scope 时另起一行附加 scope 分布；F007 marker `Installed N skills, M agents into hosts: <list>` 那一行不变 |
| FR-910 文档同步 | `packs/README.md` + `docs/guides/garage-os-user-guide.md` + `AGENTS.md` + `RELEASE_NOTES.md` 由 hf-tasks T?(docs) 阶段统一更新 |

### 2.2 来自规格的非功能驱动力（NFR / CON）

| 驱动 | 设计承接 |
|---|---|
| NFR-901 字节级一致 + Dogfood 不变性硬门槛 | (a) F007/F008 既有调用形态默认 scope project，行为字节级保留（`--scope project` 等价无 flag）(b) Dogfood 不变性由 hf-tasks 阶段加 sentinel test 守门：`tests/adapter/installer/test_dogfood_invariance_F009.py` 在 fixture 临时目录跑 `garage init --hosts cursor,claude` 后比对落盘 SKILL.md/agent.md SHA-256 与 F008 dogfood baseline 一致 |
| NFR-902 测试基线零回归 + 增量 ≥ 25 | 详见 §13 测试矩阵：8 个新增测试文件 + 既有测试 0 退绿 + carry-forward wording 修复（schema_version assertion） |
| NFR-903 跨平台路径稳定性 | 用 `Path.home()` + `Path.as_posix()`（F007 NFR-703 同精神）；Windows `Path.home()` 默认解析 `%USERPROFILE%` |
| NFR-904 git diff 可审计 | 6 类提交分组：`f009(adapter)` / `f009(pipeline)` / `f009(manifest)` / `f009(cli)` / `f009(tests)` / `f009(docs)`，详见 §10.1 |
| CON-901 不破坏 F002/F007/F008 | 默认 scope project + manifest schema migration 自动透明；test_cli.py 既有 init 测试如有 schema_version assertion 需 carry-forward 放宽（与 F008 carry-forward 同精神） |
| CON-902 D7 算法骨架不动（phase 1 + phase 3 严格不变 + phase 2/4/5 enum 允许的最小改动） | 详见 ADR-D9-2 与 §10.2 决策表 |
| CON-903 复用 F007 pack.json schema + F008 EXEMPTION_LIST | 不动；`pack.json` schema 6 字段、`EXEMPTION_LIST` 7 项均不变 |
| CON-904 manifest schema 1 → 2 migration 单向 + 跨用户立场 | 详见 ADR-D9-1 / ADR-D9-3 / ADR-D9-4 |

### 2.3 关键 host scope path 调研结果（spec § 1 调研锚点对应）

按 spec § 1 enum 的 3 家宿主官方文档：

| Host | Project skill path | User skill path | Project agent path | User agent path |
|---|---|---|---|---|
| **claude** | `.claude/skills/<id>/SKILL.md` | `~/.claude/skills/<id>/SKILL.md` | `.claude/agents/<id>.md` | `~/.claude/agents/<id>.md` |
| **opencode** | `.opencode/skills/<id>/SKILL.md` | `~/.config/opencode/skills/<id>/SKILL.md` (XDG) | `.opencode/agent/<id>.md` | `~/.config/opencode/agent/<id>.md` |
| **cursor** | `.cursor/skills/<id>/SKILL.md` | `~/.cursor/skills/<id>/SKILL.md` | (None) | (None) |

**OpenCode XDG vs dotfiles**：spec § 11 阻塞性问题列了三选一，spec 默认选 XDG（OpenCode 历史默认）。design 沿用此选择，dotfiles 风格 `~/.opencode/skills/` 留给 deferred backlog（ADR-D9-? 不引入子选项）。

## 3. 需求覆盖与追溯

| spec 条款 | 覆盖位置 |
|---|---|
| FR-901 `--scope` flag | §11 模块 `cli.py` + ADR-D9-7 stdout 多 scope 段 + §10 工作流 step 4 |
| FR-902 per-host override 语法 | §11 模块 `host_registry.resolve_hosts_arg` + ADR-D9-9 host_id 命名约束 |
| FR-903 交互式两轮 scope 选择 | §11 模块 `interactive.prompt_scopes_per_host` + ADR-D9-5 UX 候选 C |
| FR-904 user scope 路径解析（3 adapter）| §11 模块 `hosts/{claude,opencode,cursor}.py` 各加 `_user` 后缀 method + ADR-D9-6 method 命名 |
| FR-905 manifest schema 1 → 2 migration | §11 模块 `manifest.py` + `version_manager.py` + ADR-D9-1 字段命名 + ADR-D9-3 absolute path 序列化 + ADR-D9-4 是否带 `~/` 前缀 + ADR-D9-8 ManifestMigrationError 类型 |
| FR-906 pipeline scope 分流 | §11 模块 `pipeline._resolve_targets` + CON-902 严守 |
| FR-907 跨 scope 冲突 | §11 模块 `pipeline._check_conflicts` 三元组 key |
| FR-908 garage status scope 分组 | §11 模块 `cli._status` + ADR-D9-7 输出格式 |
| FR-909 stdout marker 派生 | §11 模块 `pipeline.install_packs` summary 段 + ADR-D9-7 |
| FR-910 文档同步 | §11 模块 `docs/` + hf-tasks T?(docs) 阶段 |
| NFR-901 字节级 + Dogfood 不变性 | §13 sentinel test + §11 dogfood SHA-256 baseline |
| NFR-902 测试基线 + 增量 ≥ 25 | §13 8 个新增测试文件 |
| NFR-903 跨平台路径 | `Path.home()` + `Path.as_posix()` |
| NFR-904 git diff 可审计 | §10.1 6 类提交分组 |
| CON-901..904 | 全 ADR 集合 + §11 INV 不变量 |

## 4. 架构模式选择

D009 不引入新代码模块，是**对 F007/F008 现有模块的最小扩展**：

- **核心模式**：Strategy Pattern（按 target.scope 选 base path）+ Schema Versioning（VersionManager 接管 manifest migration）
- **次级模式**：Optional Protocol Methods（adapter 新增 `_user` 后缀 method 而不破坏 F007 既有 method 签名，参考 ADR-D9-6）
- **不引入**：新代码模块、新依赖、新数据库

## 5. 候选方案总览

D009 的"方案"分布在 9 项 ADR（spec § 11 + r1 升级出 2 项）。每项 ADR 在 §7 给出 compare view + 选定结论。本节只列 ADR 索引：

| ADR | 主题 | 候选数 | 选定 |
|---|---|---|---|
| **ADR-D9-1** | manifest schema 2 字段命名 | 3（"project"/"user" / "workspace"/"global" / "local"/"global"）| `"project"` / `"user"` |
| **ADR-D9-2** | pipeline scope 分流落点（CON-902 严守 phase 1 + phase 3 不变）| 2（phase 2 vs 跨 phase）| Phase 2 内部唯一改动点 |
| **ADR-D9-3** | manifest absolute path 序列化是否带 `~/` 前缀 | 3（绝对展开 / `~/` 前缀 / 二选一开关） | 绝对展开（POSIX `/home/<user>/...`），与 NFR-903 + Path.home() 自然行为一致 |
| **ADR-D9-4** | manifest dst 跨用户立场（与 ADR-D9-3 + CON-904 联动）| 2（追求可移植 / 不追求） | 不追求（与 CON-904 一致；manifest 默认不入项目 git） |
| **ADR-D9-5** | 交互式 UX 三选一 | 3（A 两轮 / B 一轮带后缀 / C 两轮+all P/all u/per-host）| **C** — 两轮+三个开关（first prompt 选宿主，second prompt 给 "all P / all u / per-host" 三个开关；选 per-host 时再逐个问）|
| **ADR-D9-6** | HostInstallAdapter Protocol 新增 method 命名 | 2（`target_skill_path_user` 后缀 / `target_skill_path(scope=...)` 改既有签名）| `_user` 后缀 method（保留 F007 既有签名兼容） |
| **ADR-D9-7** | `garage status` 输出格式 + stdout 多 scope 段格式 | 3（ASCII table / nested bullets / JSON）| **Nested bullets** — 与 F007/F008 现有 status 文本风格一致 |
| **ADR-D9-8** | ManifestMigrationError 类型与退出码 | 2（exit 1 沿用 / exit 3 专用）| **exit 1** — 与 unknown host / OS error 同级，与 spec § 11 非阻塞 #2 默认一致 |
| **ADR-D9-9** | host_id 命名约束（不允许字面 `:`） | 2（运行时检查 / 静态文档）| 双层：注册表 import 时静态 assert + Protocol docstring 显式声明 |

## 6. 候选方案对比与 trade-offs

详见 §7 各 ADR compare view。本节只回顾整体设计倾向：

| 维度 | D009 整体倾向 |
|---|---|
| 复杂度 | 最低（无代码新模块、无依赖、F007 算法骨架严守不动） |
| 可逆性 | 高（schema 1→2 migration 单向，但代码 ADR 选择均可在未来 cycle 反向） |
| 与 spec 一致性 | 严守 spec § 11 + NFR-901 + CON-902 + CON-904 多重约束 |
| 面向未来 | 留好 F010+ entry point（uninstall/update/dotfiles 风格 OpenCode/enterprise scope/plugin scope 等） |
| 用户感知 | 默认行为完全等价 F008（CON-901 + Dogfood 不变性硬门槛）；user scope 是显式可选 |

## 7. 选定方案与关键决策（ADR）

### ADR-D9-1: manifest schema 2 字段命名

**Context**：spec § 11 非阻塞 #1。

**Compare**:

| 候选 | 字段值 | 优点 | 主要代价 / 风险 | NFR / 约束适配 | 可逆性 |
|------|------|------|------------------|----------------|--------|
| **"project" / "user"**（spec 默认） | `files[].scope: "project"` 或 `"user"` | (1) 与 spec / docs / FR / 用户面对话 wording 完全一致（spec 全文用 "project scope" / "user scope"）(2) Anthropic Claude Code 官方文档用 "project / personal" 但 "personal" 在 Garage 语境下歧义（Anthropic 还有 "enterprise"），用 "user" 更直接 | 与 Anthropic 官方 "personal" wording 略有偏差 | 与 spec § 12 术语表一致 ✓ | 高（schema 升级未来仍可调） |
| "workspace" / "global" | `files[].scope: "workspace"` 或 `"global"` | (1) "workspace" 与 docs/soul/design-principles.md "workspace-first" 信念用词一致 (2) "global" 强调跨项目复用 | (1) "global" 在 OpenSpec issue #752 语境下也指 OS-level 全局（更激进），与 user scope 语义不严格一致 (2) spec / docs 全文需重写 | 与 spec § 12 术语表偏差 ❌ | 高 |
| "local" / "global" | `files[].scope: "local"` 或 `"global"` | (1) "local" 紧凑 | (1) "local" 在 git 语境下歧义（local branch vs project local）(2) "global" 同上歧义 | 与 spec 偏差 ❌ | 高 |

**Decision**: 选定 **"project" / "user"** — 与 spec / docs / 用户面 wording 完全一致；OpenCode/Cursor 官方文档用 "project-level" / "user-level" 也匹配。

**Consequences**:
- ✅ spec / docs / 测试常量 / CLI 输出 / manifest 字段值四方完全一致
- ⚠️ 与 Anthropic Claude Code 官方 "personal" wording 略偏差，但 Garage 不引入 enterprise scope（spec § 2.3），不构成歧义
- ✅ 用户面 `--scope project` / `--scope user` flag 与字段值直接对应

**Reversibility**: 高 — schema 升级未来仍可在 D10+ 改名（schema_version: 2 → 3）。

### ADR-D9-2: Pipeline scope 分流落点（CON-902 严守 phase 1 + phase 3 不变）

**Context**：spec CON-902 + FR-906 严守 phase 1 + phase 3 算法主体字节级不变。

**Compare**:

| 候选 | 思路 | 优点 | 主要代价 / 风险 | NFR / 约束适配 | 可逆性 |
|---|---|---|---|---|---|
| **Phase 2 内部唯一改动点**（spec 默认） | `_resolve_targets` 内按 target.scope 选 base path：`base = workspace_root if scope == "project" else Path.home()` | (1) phase 1 / 3 / 4 / 5 算法主体严格不变 (2) `_Target` dataclass 增 `scope` 字段对其它 phase 是透明的（仅 type signatures 扩展）(3) CON-902 design reviewer 可拒红线天然满足 | 无显著代价 | 完美承接 CON-902 ✓ | 高 |
| 跨 phase 分流 | phase 2 / 3 / 4 / 5 各自处理 scope 维度 | 灵活 | 严重违反 CON-902（phase 1/3 必须严格不动）；review surface 失控；hf-traceability-review 无法验证 | FAIL — 触发 CON-902 design-review 可拒红线 | 中 |

**Decision**: 选定 **Phase 2 内部唯一改动点**。

**Consequences**:
- ✅ CON-902 phase 1 + phase 3 严格不动硬门槛通过
- ✅ phase 4 比对 key 4→5 元组扩展、phase 5 schema_version 写入差异是 CON-902 enum 内允许的最小改动
- ⚠️ `_Target` 增 `scope` 字段需要 type signatures 扩展，但算法主体不变

**Reversibility**: 高 — 未来如需更激进的 scope 模型（如 enterprise），可在那个 cycle 重新分流。

### ADR-D9-3: manifest absolute path 序列化是否带 `~/` 前缀

**Context**：spec § 11 非阻塞 #4。

**Compare**:

| 候选 | 序列化形态 | 优点 | 主要代价 / 风险 | 可逆性 |
|---|---|---|---|---|
| **绝对展开**（POSIX `/home/<user>/...`） | `files[].dst = "/home/alice/.claude/skills/hf-specify/SKILL.md"` | (1) 与 `Path.home()` 自然行为一致，无序列化逻辑扩展 (2) 与 NFR-903 POSIX 序列化一致 (3) manifest 是用户本地状态记录（不入项目 git，CON-904 已声明）| 跨用户不可移植（user A commit manifest 后 user B clone 看到 `/home/alice/...`）— 但 CON-904 已声明本 cycle 不追求跨用户可移植 | 高 |
| `~/` 前缀 | `files[].dst = "~/.claude/skills/hf-specify/SKILL.md"` | 跨用户可移植 | (1) 需要序列化逻辑识别 home 部分并替换 (2) 反序列化需要 `os.path.expanduser` (3) 与 NFR-903 POSIX 严格序列化一致性偏差 (4) project scope dst 仍是 absolute（如 `/workspace/.claude/skills/...`），用户也不可移植 — `~/` 前缀只对 user scope 有效，破坏字段统一性 | 中 |
| 二选一开关 | `manifest.json` 加 `dst_format: "absolute" \| "tilde"` 元字段 | 灵活 | YAGNI（spec 没提需要切换） | 中 |

**Decision**: 选定 **绝对展开**。

**Consequences**:
- ✅ 与 `Path.home()` 自然行为一致，无 serialization 复杂度
- ✅ 与 NFR-903 POSIX 序列化一致
- ⚠️ manifest 跨用户不可移植 — 但 CON-904 已声明本 cycle 不追求；与 F008 dogfood `.gitignore` 政策一致
- ⚠️ user A 与 user B 在同一项目内 commit manifest 会有冲突 — 但 manifest 已在 `.gitignore`，本 cycle 仍不入项目 git

**Reversibility**: 高 — 未来如需可移植，在 D10+ 加 `dst_format: "tilde"` 选项。

### ADR-D9-4: manifest dst 跨用户立场（与 ADR-D9-3 + CON-904 联动）

**Context**：spec CON-904 已声明立场，本 ADR 锚定具体技术实现。

**Decision**: **不追求跨用户可移植**。`files[].dst` 是 absolute POSIX path（含用户 home 部分）；manifest 默认不入项目 git（与 F008 dogfood `.gitignore` 政策一致 — `.gitignore` 已排除 `.garage/config/host-installer.json`）。

**Consequences**:
- ✅ 与 ADR-D9-3 一致
- ✅ 与 CON-904 一致
- ✅ 与 F008 dogfood 政策一致

**Reversibility**: 高 — 未来同 ADR-D9-3。

### ADR-D9-5: 交互式 UX 三选一（spec § 11 非阻塞 #5 + r1 important #3 扩展为三选一）

**Context**：spec § 11 非阻塞 #5。

**Compare**:

| 候选 | 思路 | 优点 | 主要代价 / 风险 | UX 体验 |
|---|---|---|---|---|
| A 两轮 | 第一轮选宿主，第二轮逐个问 P/u | (1) 直观 (2) 每个宿主独立选 | N=3 宿主时回答 3 次 P/u，冗长 | 中 |
| B 一轮带后缀 | 选宿主时直接输入 `claude:user, cursor` | (1) 紧凑 | (1) 输入语法学习成本 (2) 与 `--hosts claude:user,cursor` 重复，但 CLI 已支持 | 低 |
| **C 两轮+三个开关**（spec r1 important #3 扩展） | 第一轮选宿主 (F007 行为不变)；第二轮先问 "Install all selected hosts to: [a]ll project / [u]ser for all / [p]er-host? [a/u/p]: " 默认 a；选 p 才进入逐个 P/u 提示 | (1) 默认 `a`（all project）一键回车，与 F007/F008 体验完全一致（CON-901 友好） (2) 选 `u` 一键全 user (3) 真有 mix 需求时输入 `p` 进入逐个询问 (4) 兼顾常见场景与高级场景 | (1) 第二轮多一个 a/u/p 提示 (与 F007 直接装相比多 1 次回车) — 但默认值兼容 | 高 |

**Decision**: 选定 **C 两轮+三个开关**。

**Consequences**:
- ✅ 默认 `a` 一键回车 = F007/F008 行为（CON-901 兼容）
- ✅ 高级 mix 场景用 `p` 进入逐个询问
- ✅ 中间 "all u" 场景一键 `u`
- ⚠️ 第二轮多一次 a/u/p 提示，与 F007 仅一轮选宿主对比多一次 — 但 spec FR-903 验收 #2 已显式说"全部回车 = 全 project = F007/F008 行为"，不破坏 CON-901

**Reversibility**: 高。

### ADR-D9-6: HostInstallAdapter Protocol 新增 method 命名

**Context**：spec § 11 非阻塞 #6。

**Compare**:

| 候选 | 签名 | 优点 | 主要代价 / 风险 | 可逆性 |
|---|---|---|---|---|
| **`target_skill_path_user` 后缀**（spec 默认） | `target_skill_path(skill_id) -> Path` (F007 既有, project scope 相对路径) + `target_skill_path_user(skill_id) -> Path` (新增, user scope 绝对路径) | (1) 完全保留 F007 既有 method 签名 (零破坏 backward compat) (2) `_user` 后缀清晰区分 scope (3) Protocol 实现时易于增量扩展 | (1) Protocol method 数翻倍（4 个 method） (2) pipeline 内需要 `if scope == "project"` 分支选择调用哪个 method | 高 |
| `target_skill_path(scope=...)` 改既有签名 | `target_skill_path(skill_id, scope: Literal["project", "user"] = "project") -> Path` | (1) 单 method 对称 (2) pipeline 不需要分支 | (1) 破坏 F007 既有签名 backward compat（既有调用 `adapter.target_skill_path(skill_id)` 仍可工作但语义"默认 project"是新引入）(2) 影响 F007 既有 `target_agent_path` 同步改造 (3) 新返回值类型 `Path`（既有相对路径）vs `absolute Path`（user scope）类型一致但语义不同，需要 Protocol docstring 详细说明 | 中 |

**Decision**: 选定 **`target_skill_path_user` 后缀** method（spec 默认）。

**Consequences**:
- ✅ F007 既有 method 签名零破坏
- ✅ Protocol method 与 scope 一一对应，pipeline 内 `if target.scope == "project"` 分支清晰
- ⚠️ Protocol method 数从 3 翻倍到 5（target_skill_path / target_skill_path_user / target_agent_path / target_agent_path_user / render）
- 🔧 实现细节：3 家 adapter 各加 `target_skill_path_user` + `target_agent_path_user` method（cursor 的 user agent path 仍返回 None，与 project scope 一致）

**Reversibility**: 高 — 未来如需统一 single-method scope 参数化，可在 D10+ 引入兼容包装。

### ADR-D9-7: `garage status` + stdout 多 scope 段输出格式

**Context**：spec § 11 非阻塞 #3 + #7。

**Compare**:

| 候选 | 格式 | 优点 | 主要代价 / 风险 | 可读性 |
|---|---|---|---|---|
| ASCII table | 表格化 | 整齐 | (1) 与 F007/F008 现有 status 文本风格不一致 (2) 行宽问题 | 中 |
| **Nested bullets**（spec 默认） | 项目状态段 / scope 段 / host 子段 / count + path 前缀 | (1) 与 F007/F008 现有 status 文本风格一致 (2) 易扩展 (3) `grep` / `awk` 友好 | 略冗长 | 高 |
| JSON | `--format json` | 机器可读 | (1) 不是默认 (2) F007/F008 没有 JSON 输出基础设施，过度设计 | 高（机器） / 低（人） |

**Decision**: 选定 **Nested bullets**。

**`garage status` 输出样板**：

```
Garage OS at /workspace
  schema_version: 2

Installed packs (project scope):
  claude:    29 skills, 1 agent  → /workspace/.claude/{skills,agents}/
  cursor:    29 skills            → /workspace/.cursor/skills/

Installed packs (user scope):
  opencode:  29 skills, 1 agent  → /home/alice/.config/opencode/{skills,agent}/
```

**stdout 多 scope 段（FR-909）样板**：

```
Initialized Garage OS in /tmp/test/.garage
Installed 87 skills, 2 agents into hosts: claude, cursor, opencode
  (29 user-scope skills + 58 project-scope skills, 1 user-scope agent + 1 project-scope agent)
```

**关键约束（FR-909 验收）**：第二行 F007 既有 marker 字面不变；附加段必须独立一行（缩进 2 空格）；F007 grep `^Installed [0-9]+ skills, [0-9]+ agents into hosts:` 仍恰好命中第二行。

**Consequences**:
- ✅ `grep -cE '^Installed [0-9]+ skills, [0-9]+ agents into hosts:' stdout` == 1（FR-909 验收）
- ✅ 与 F007/F008 现有 status 风格一致
- ⚠️ 多 scope 时 stdout 多一行，但仍可冷读

**Reversibility**: 高。

### ADR-D9-8: ManifestMigrationError 类型与退出码

**Context**：spec § 11 非阻塞 #2 + r1 important #2 升级。

**Compare**:

| 候选 | 退出码 | 优点 | 主要代价 / 风险 |
|---|---|---|---|
| **exit 1**（spec 默认） | exit 1（与 unknown host / OS error 同级） | (1) 与 F007 退出码语义一致（input/migration/IO error 统一 1）(2) 简单 | 与 conflict (exit 2) 区分度低 |
| exit 3（专用）| exit 3 | 区分度高 | (1) F007 只有 0/1/2，新增 3 破坏退出码语义稳定性 (2) 下游 CI script 可能依赖 exit 1/2 二分 |

**Decision**: 选定 **exit 1**。

**类型定义**：在 `manifest.py` 加 `class ManifestMigrationError(ValueError)`；`pipeline.install_packs` 不主动 catch，由 CLI 层 `cli._init` catch + print stderr + return 1。

**Consequences**:
- ✅ 与 F007 退出码 0/1/2 语义稳定（不引入新 exit code）
- ✅ stderr 含 `Manifest migration failed: <reason>` 可 grep
- ⚠️ 与 F007 既有 OSError → exit 1 / UnknownHostError → exit 1 同级

**Reversibility**: 高 — 未来如需细化区分，可在 D10+ 引入 exit 3。

### ADR-D9-9: host_id 命名约束（不允许字面 `:` 字符）

**Context**：spec § 4.1 包含表 + r1 minor #2 升级。

**Decision**: **双层守门**：
1. **运行时静态 assert**：`host_registry.py` 在 `_build_registry()` 末尾 `assert all(":" not in host_id for host_id in HOST_REGISTRY)`，import 时即检查
2. **Protocol docstring 显式声明**：`HostInstallAdapter` Protocol 的 `host_id: str` 字段 docstring 加 "MUST NOT contain literal `:` character (used as scope override delimiter, F009 FR-902)"

**Consequences**:
- ✅ 当前 first-class 三家（claude/opencode/cursor）天然符合
- ✅ 未来注册 host adapter 时 import-time 静态 assert 立即捕获违反
- ✅ docstring 提供 author 编写时的设计意图记录
- ⚠️ 加测试 `test_host_registry::test_no_host_id_contains_colon` 守门

**Reversibility**: 高 — 未来如需放宽（如换用其它分隔符），可在 D10+ 调整。

## 8. 架构视图

### 8.1 安装管道（D7 不动 + D9 phase 2 增 scope 分流）

```
                    ┌─────────────────────────┐
                    │ packs/{garage,coding,    │
                    │   writing}/             │
                    └─────────────┬───────────┘
                                  │ discover_packs() (PHASE 1, 不变)
                                  ▼
              ┌───────────────────────────────────────────────────┐
              │  D9 install_packs(workspace, packs, hosts, scope) │
              │                                                    │
              │  PHASE 2 (改): _resolve_targets                    │
              │    for target in expanded(packs × hosts):           │
              │      if target.scope == "project":                  │
              │        base = workspace_root                        │
              │      else:  # "user"                                │
              │        base = Path.home()                           │
              │      target.dst_abs = base / adapter.target_skill_path...│
              │                                                    │
              │  PHASE 3 (不变): _check_conflicts                  │
              │    key = (host, scope, dst_abs) 三元组              │
              │                                                    │
              │  PHASE 4 (不变结构, 5 元组扩展): _decide_action    │
              │    key = (src, dst_abs, host, pack_id, scope)      │
              │                                                    │
              │  PHASE 5 (不变结构, schema 1→2): apply + manifest  │
              │    if prior schema_version == 1:                    │
              │      VersionManager.migrate_v1_to_v2(prior)        │
              │    write manifest schema_version=2                  │
              │      files[].dst = absolute POSIX path              │
              │      files[].scope = "project" | "user"             │
              └───────────────┬───────────────────────────────────┘
                              │ adapter.target_skill_path(...) (project, F007 既有)
                              │ adapter.target_skill_path_user(...) (user, F009 新增)
                              ▼
        ┌─────────────────────┬─────────────────────┬────────────────────┐
        │  Project scope:     │ User scope:         │ User scope (XDG):  │
        │  <cwd>/.claude/...  │ ~/.claude/...       │ ~/.config/opencode/│
        │  <cwd>/.cursor/...  │ ~/.cursor/...       │ ...                │
        └─────────────────────┴─────────────────────┴────────────────────┘
                              │
                              ▼
              <cwd>/.garage/config/host-installer.json (schema_version: 2)
              { schema_version=2,
                installed_hosts=[...],
                installed_packs=[...],
                files=[{src, dst (absolute POSIX), host, pack_id, scope, content_hash}, ...] }
```

### 8.2 交互式两轮 UX (ADR-D9-5 candidate C)

```
$ garage init  (TTY, no --hosts, no --yes)

[ROUND 1: select hosts (F007 行为不变)]
Detected hosts you can install Garage packs into:
  [1] claude
  [2] cursor
  [3] opencode
Enter host numbers separated by space (or 'all'): 1 2

[ROUND 2: select scope (F009 新增)]
Install selected hosts to:
  [a] all project (./.{host}/skills/) — F007/F008 default
  [u] all user    (~/.{host}/skills/)
  [p] per-host    — pick scope individually
Choice [a/u/p]: a   ← 默认回车 = a, 等价 F007/F008

  (if 'p' selected, ROUND 2b iterates per host:)
  Install claude to: [P]roject or [u]ser? [P/u]: u
  Install cursor to: [P]roject or [u]ser? [P/u]: <enter>  → P

→ Equivalent to: garage init --hosts claude:user,cursor:project
```

### 8.3 Manifest schema 1 vs 2

**Schema 1 (F007/F008)**:
```json
{
  "schema_version": 1,
  "installed_hosts": ["claude"],
  "installed_packs": ["coding", "garage", "writing"],
  "installed_at": "2026-04-23T14:02:35",
  "files": [
    {"src": "packs/coding/skills/hf-specify/SKILL.md",
     "dst": ".claude/skills/hf-specify/SKILL.md",
     "host": "claude",
     "pack_id": "coding",
     "content_hash": "1f3c..."}
  ]
}
```

**Schema 2 (F009, migration 后)**:
```json
{
  "schema_version": 2,
  "installed_hosts": ["claude"],
  "installed_packs": ["coding", "garage", "writing"],
  "installed_at": "2026-04-23T14:02:35",
  "files": [
    {"src": "packs/coding/skills/hf-specify/SKILL.md",
     "dst": "/workspace/.claude/skills/hf-specify/SKILL.md",  ← absolute
     "host": "claude",
     "pack_id": "coding",
     "scope": "project",  ← 新增, migration 时所有旧 entry 默认 project
     "content_hash": "1f3c..."}
  ]
}
```

**Migration 规则**：每条 entry：(a) `scope` 字段补 `"project"` (b) `dst` relative → absolute（`workspace_root / dst`）(c) 顶层 `schema_version` 字段 1 → 2；其它字段保持。

## 9. 模块职责与边界

| 模块 | 职责（D9 增量）| 边界 |
|---|---|---|
| `src/garage_os/adapter/installer/host_registry.py` | (1) 解析 `--hosts <list>` 支持 `<host>:<scope>` 语法（FR-902）(2) 静态 assert host_id 不含 `:`（ADR-D9-9）| 不动 `HostInstallAdapter` Protocol 既有 method 签名 |
| `src/garage_os/adapter/installer/hosts/{claude,opencode,cursor}.py` | 各加 `target_skill_path_user` + `target_agent_path_user` method（FR-904 / ADR-D9-6）| Project scope method 签名严格不变（CON-901） |
| `src/garage_os/adapter/installer/pipeline.py` | Phase 2 scope 分流（FR-906 / ADR-D9-2）；Phase 4 比对 key 5 元组扩展；Phase 5 调用 manifest migration | Phase 1 + Phase 3 算法主体严格不变（CON-902 design reviewer 可拒红线） |
| `src/garage_os/adapter/installer/manifest.py` | (1) `MANIFEST_SCHEMA_VERSION = 2`（F007 是 1）(2) `Manifest` dataclass 字段扩展 (3) `migrate_v1_to_v2(prior) -> Manifest` 函数 (4) `ManifestMigrationError` 类型（ADR-D9-8）| schema 1 字段含义在 schema 2 下保留可冷读 |
| `src/garage_os/adapter/installer/interactive.py` | 新增 `prompt_scopes_per_host(host_ids, *, stdin, stderr) -> dict[str, str]`（ADR-D9-5 candidate C） | F007 既有 `prompt_hosts` 行为不变 |
| `src/garage_os/platform/version_manager.py` | 注册 host-installer migration 链 (1 → 2) | F001 platform contract 政策不变 |
| `src/garage_os/cli.py` | (1) init subparser 加 `--scope` flag (2) `_init()` 接收 scope 参数 (3) `_resolve_init_hosts` 接收 hosts 二元组 list 而非 str list (4) `_status` 按 scope 分组打印 | F007 既有 `--hosts` `--yes` `--force` flag + `_init` 缺省行为字节级不变 |

## 10. 数据流、控制流与关键交互

### 10.1 D009 实施流（6 类提交分组，对应 NFR-904）

```
T1 (adapter):    cp -r 三家 adapter (claude/opencode/cursor) 各加 target_skill_path_user + target_agent_path_user method
                 + host_registry.py 加 host_id 不含 ':' assert + Protocol docstring
                 + 4 个新增测试文件: test_adapter_user_scope.py / test_host_registry_colon_assert.py
                 git commit -m "f009(adapter): 三家 first-class adapter 加 user scope path + host_id 命名约束"

T2 (pipeline):   pipeline._resolve_targets phase 2 scope 分流 + _Target 增 scope 字段
                 + _check_conflicts 比对 key 三元组 + _decide_action 比对 key 5 元组
                 + 新增测试: test_pipeline_scope_routing.py
                 git commit -m "f009(pipeline): phase 2 scope 分流 + phase 4 5 元组比对 (CON-902 严守)"

T3 (manifest):   manifest.MANIFEST_SCHEMA_VERSION = 2 + Manifest dataclass 增 dst absolute + scope 字段
                 + ManifestMigrationError + migrate_v1_to_v2 函数
                 + version_manager.py 注册 host-installer migration 链
                 + 新增测试: test_manifest_schema_v2.py / test_manifest_migration_v1_to_v2.py
                 git commit -m "f009(manifest): schema 1 → 2 migration + ManifestMigrationError + VersionManager 注册"

T4 (cli):        cli.py: init subparser 加 --scope flag + _init 接收 scope + _resolve_init_hosts 改造接收二元组 list
                 + interactive.py: prompt_scopes_per_host (ADR-D9-5 candidate C 三个开关)
                 + cli._status 按 scope 分组 (ADR-D9-7 nested bullets)
                 + 新增测试: test_cli_scope_flag.py / test_cli_per_host_override.py / test_interactive_two_round.py / test_status_scope_grouped.py
                 + carry-forward: 既有 test_cli.py 内 schema_version assertion 放宽 (与 F008 carry-forward 同精神)
                 git commit -m "f009(cli): --scope flag + per-host override + 交互式两轮 + status scope 分组"

T5 (tests):      新增 sentinel test: test_dogfood_invariance_F009.py (NFR-901 Dogfood 不变性硬门槛 SHA-256)
                 + 集成测试: test_full_init_user_scope.py (端到端 garage init --scope user 三家宿主)
                 git commit -m "f009(tests): Dogfood 不变性 sentinel + user scope 全装集成测试"

T6 (docs):       packs/README.md 增 "Install Scope" 段
                 + docs/guides/garage-os-user-guide.md "Pack & Host Installer" 段加 --scope 用法 + 交互示例
                 + AGENTS.md § "Packs & Host Installer (F007/F008)" 升级到 F007/F008/F009 + 新增 "Install Scope" 子段
                 + RELEASE_NOTES.md 新增 F009 段 (按 F008 同等结构)
                 git commit -m "f009(docs): packs/README + user-guide + AGENTS.md + RELEASE_NOTES F009 占位段"
```

### 10.2 验证步骤（对应 spec § 4.2 + § 11 多重约束）

| 约束 | 验证命令 | 预期 |
|---|---|---|
| CON-901 字节级不变 | `garage init --hosts claude` 字节级与 F008 baseline 一致（除 manifest schema migration 例外）| 测试 `test_dogfood_invariance_F009.py` 自动守门 |
| CON-902 phase 1 + phase 3 严格不变 | `git diff main..HEAD -- src/garage_os/adapter/installer/pipeline.py` 检查 phase 1 + phase 3 函数 | hf-traceability-review 阶段人工 + 自动 grep 守门 |
| CON-903 packs/ + EXEMPTION_LIST 不动 | `git diff main..HEAD -- packs/ tests/adapter/installer/test_neutrality_exemption_list.py` | 输出空 |
| CON-904 manifest 不入 git | `.gitignore` 仍含 `.garage/config/host-installer.json` | grep 命中 |
| Dogfood 不变性 | dogfood `garage init --hosts cursor,claude` 后 SHA-256 与 F008 baseline 一致 | sentinel test 自动守门 |
| Manifest migration | F008 manifest schema 1 → 2 自动迁移 | `test_manifest_migration_v1_to_v2.py` |
| 测试基线 | `pytest tests/ -q` ≥ 633 + 25 增量 | 全 PR 守门 |

## 11. 接口、契约与关键不变量

### 11.1 不变量（implementation 阶段必须守住）

| Invariant | 验证方式 | 责任 commit |
|---|---|---|
| INV-F9-1 CON-901 字节级 + Dogfood 不变性 | `test_dogfood_invariance_F009.py` SHA-256 对比 F008 baseline | T5 |
| INV-F9-2 CON-902 phase 1 + phase 3 严格不变 | `git diff` 人工 + 自动 grep 守门 | 全 PR (T2 主要) |
| INV-F9-3 CON-903 packs/ + EXEMPTION_LIST 不动 | git diff = 空 | 全 PR |
| INV-F9-4 CON-904 manifest 不入 git | `.gitignore` 含排除 + 测试 | T3 |
| INV-F9-5 测试基线 ≥ 633 + 25 增量 | pytest 总数 | 全 PR |
| INV-F9-6 host_id 命名约束 | `test_host_registry_colon_assert.py` | T1 |
| INV-F9-7 manifest schema 2 三方一致 | spec NFR-801 + design ADR-D9-1 + manifest.py 常量 | T3 |
| INV-F9-8 user scope 测试 fixture-isolated | 测试用 `tmp_path` + monkeypatch `Path.home()` | T1 / T2 / T5 |
| INV-F9-9 F007 stdout grep 兼容 | `test_status_scope_grouped::test_F007_marker_grep_compat` | T4 |

### 11.2 不引入的契约

- 不新增 `pack.json` 字段（CON-903）
- 不新增 host adapter（仍 claude/opencode/cursor 三家）
- 不新增退出码（仍 0/1/2，ADR-D9-8 选 exit 1）
- 不新增依赖（NFR 零依赖）

## 12. 非功能需求与约束落地

| NFR / CON | 落地模块 / 步骤 |
|---|---|
| NFR-901 字节级 + Dogfood | T5 sentinel test + T2/T3/T4 各测试 carry-forward |
| NFR-902 测试基线 ≥ 633 + 25 增量 | T1+T2+T3+T4+T5 共 ≥ 8 个新增测试文件 |
| NFR-903 跨平台 POSIX | adapter / pipeline 全用 `Path.home()` + `Path.as_posix()` |
| NFR-904 git diff 可审计 | 6 类提交分组 (T1-T6) |
| CON-901 不破坏 F002/F007/F008 | 默认 scope project + carry-forward wording |
| CON-902 phase 1 + phase 3 严格 | T2 实施 + INV-F9-2 守门 |
| CON-903 packs/ + EXEMPTION_LIST | INV-F9-3 守门 |
| CON-904 manifest 不入 git | INV-F9-4 守门 |

## 13. 测试与验证策略

### 13.1 自动化测试（hf-tasks 拆任务后由 hf-test-driven-dev 实施）

| 测试文件 | 覆盖 spec FR/NFR | 触发 INV | 落地 commit |
|---|---|---|---|
| `tests/adapter/installer/test_adapter_user_scope.py` | FR-904（3 家 user scope path）| 间接 INV-F9-1 | T1 |
| `tests/adapter/installer/test_host_registry_colon_assert.py` | ADR-D9-9 host_id 命名约束 | INV-F9-6 | T1 |
| `tests/adapter/installer/test_pipeline_scope_routing.py` | FR-906 phase 2 + phase 4 + phase 7（跨 scope 不冲突）| INV-F9-2 间接 | T2 |
| `tests/adapter/installer/test_manifest_schema_v2.py` | FR-905 schema 2 字段 + ADR-D9-1/3 | INV-F9-7 | T3 |
| `tests/adapter/installer/test_manifest_migration_v1_to_v2.py` | FR-905 migration + ADR-D9-8 ManifestMigrationError | INV-F9-7 | T3 |
| `tests/test_cli.py::TestInitWithScope` 新增 class | FR-901 `--scope` flag + FR-902 per-host override + FR-909 stdout marker | INV-F9-9 | T4 |
| `tests/adapter/installer/test_interactive_two_round.py` | FR-903 + ADR-D9-5 candidate C | — | T4 |
| `tests/test_cli.py::TestStatusScopeGrouped` 新增 class | FR-908 + ADR-D9-7 | — | T4 |
| `tests/adapter/installer/test_dogfood_invariance_F009.py` | NFR-901 Dogfood SHA-256 不变性 | INV-F9-1 | T5 |
| `tests/adapter/installer/test_full_init_user_scope.py` | 端到端 user scope 三家宿主集成 | INV-F9-1 / INV-F9-7 | T5 |

预期总增量 ≥ 30（10 文件 × 平均 3 用例），与 NFR-902 informational anchor "≥ 25" 一致。

### 13.2 Manual Smoke

`/tmp/f009-smoke/` 跑：
1. `garage init --hosts all`（F007/F008 兼容验证）
2. `garage init --hosts all --scope user`（user scope 端到端）
3. `garage init --hosts claude:user,cursor:project`（混合 scope）
4. `garage init`（TTY 交互式，按 ADR-D9-5 candidate C 走 `a` / `u` / `p` 三路径）
5. `garage status`（按 scope 分组展示）

归档到 `/opt/cursor/artifacts/f009_smoke_*.log` 等。

## 14. 失败模式与韧性策略

| 失败模式 | 触发 | 缓解 |
|---|---|---|
| F1 `Path.home()` 抛 RuntimeError | 用户 shell 环境异常（`$HOME` 未设置）| pipeline 捕获 → ManifestMigrationError 不适用，应抛 `UserHomeNotFoundError` → CLI exit 1 + stderr 含 `Cannot determine user home directory: ...`（ASM-903 缓解） |
| F2 manifest schema 1 → 2 migration 失败 | 旧 manifest JSON 损坏 / 字段缺失 | ManifestMigrationError → CLI exit 1 + 旧 manifest 不被覆盖（CON-904） |
| F3 dogfood 字节级 sentinel 失败 | 未来某次实施意外引入 marker 改动 | sentinel test catch + CI 卡 PR |
| F4 user scope 测试污染真实 ~/ | 未隔离 `Path.home()` | 全部 user scope 测试用 `tmp_path` + monkeypatch `Path.home()` 隔离（INV-F9-8） |
| F5 host_id 注册时含 `:` | 未来某 adapter 实现违反 ADR-D9-9 | host_registry import-time assert 立即捕获 |
| F6 F007 grep 兼容性破坏 | FR-909 多 scope 段误塞同一行 | INV-F9-9 测试守门 |
| F7 carry-forward wording 修复遗漏 | F007/F008 测试假设 schema_version=1 | T4 commit 内显式同步 + commit message 声明 |

## 15. 任务规划准备度

D009 6 类工作分组（T1-T6）已清晰对应 NFR-904 六类 commit。`hf-tasks` 阶段可直接：
- 按 6 类拆 6 个 task（或视情况合并 sub-commit）
- 每个 task 独立可 review
- T5 sentinel + 集成测试是关键合流点（依赖 T1-T4 全部完成）
- T6 docs 含 RELEASE_NOTES F009 占位段（finalize 阶段填实测）

## 16. 关键决策记录（ADR 摘要）

见 §7。共 9 项 ADR，每项可逆性高。

## 17. 明确排除与延后项（与 spec § 5 完整集合等价）

| 项 | 为什么不做 | 延后到 |
|---|---|---|
| `garage uninstall --scope <scope>` | 与 F009 正交 | F010 候选 |
| `garage update --scope <scope>` | 同上 | F010 候选 |
| Enterprise scope | 太重 | 单独候选 |
| Plugin scope | 同上 | 单独候选 |
| OpenCode `~/.opencode/` dotfiles 风格 | XDG 默认覆盖 90%+ | 单独子选项候选 |
| 跨 scope 同名 skill 优先级解析 | 宿主自己负责 | 不做 |
| `~/.garage/config/` 全局 manifest | workspace-first 信念冲突 | 不做 |
| Cursor 老版本 fallback | F007 已 deferred | 单独候选 |
| `--prefix <path>` 自定义路径 | 超出 user/project 二分常见场景 | 单独候选 |
| user scope `~/.garage/config/` | 与 ADR-D9-4 一致不写 | 不做 |
| 新增宿主 | 仍 first-class adapter 模式 | F010+ 增量 |
| LLM 辅助"自动建议 scope" | 与 manifesto "你做主" 信念冲突 | 不做 |
| 反向同步 user → packs/ | F007 已 deferred | 单独候选 |
| D7 管道扩展为递归 references/ | F008 已 deferred 为 D9 候选 | 仍是 D10 候选 |

## 18. 风险与开放问题

### 阻塞性（必须在 hf-design-review 通过前关闭）

无。

### 非阻塞性（hf-tasks / 实施阶段细化）

1. dogfood SHA-256 baseline 录制方式（人工生成静态 fixture vs 测试 setUp 时计算）— hf-tasks 决定
2. ManifestMigrationError 的 stderr 文案完整模板（design 给框架，hf-tasks 决定确切 wording）
3. T6 docs 增量是否过大需进一步拆分 — hf-tasks 决定
