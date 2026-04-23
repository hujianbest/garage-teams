# D008: Garage Coding Pack 与 Writing Pack 设计

- 状态: 草稿
- 日期: 2026-04-22
- Revision: r1
- 关联规格: `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准 r2，见 `docs/approvals/F008-spec-approval.md`）
- 关联评审: `docs/reviews/spec-review-F008-coding-pack-and-writing-pack.md`（r1 需修改 → r2 通过）
- 关联前序设计: `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`（D7，本设计**严禁修改**其代码与契约）
- 关联前序代码: `src/garage_os/adapter/installer/{pack_discovery,pipeline,marker,manifest,host_registry}.py`、`src/garage_os/adapter/installer/hosts/{claude,opencode,cursor}.py`

## 1. 概述

D008 把 spec § 2.1 核心目标拆成 5 件可独立审计、可分支提交的工程动作（与 NFR-804 五类提交分组一一对应）：

1. **packs/coding/** 落盘（22 skill）
2. **packs/writing/** 落盘（4 skill）
3. **packs/garage/** 扩容（+2 meta-skill）
4. **family-level 资产 + drift 收敛**（11 项 family asset + `docs/principles/skill-anatomy.md` 双副本治理）
5. **`.agents/skills/` 处置**（删除 + IDE 重定向）

D008 **零修改 D7 代码**，仅向 `packs/` 添加内容物 + 改写若干配置/文档：

- `src/garage_os/` 全树 0 修改（CON-801 硬约束）
- `pack.json` schema 与 host adapter 注册表零修改（CON-802）
- 现有 30 个 installer 测试全部沿用，仅追加新用例覆盖 F008-specific invariants

设计原则保持不变：workspace-first、文件即契约、宿主无关、用户确认先于覆盖、第一天零配置可用。

## 2. 设计驱动因素

### 2.1 来自规格的核心驱动力（FR）

| FR | 设计承接要点 |
|---|---|
| FR-801 `packs/coding/` 22 skill 落盘 | `cp -r .agents/skills/harness-flow/skills/{hf-*,using-hf-workflow}/ packs/coding/skills/`；写 `packs/coding/pack.json`（`schema_version=1`, `pack_id="coding"`, `version="0.1.0"`, `skills` 长度 = 22）；写 `packs/coding/README.md` |
| FR-802 `packs/writing/` 4 skill 落盘 | `cp -r .agents/skills/write-blog/{blog-writing,humanizer-zh,hv-analysis,khazix-writer}/ packs/writing/skills/`；写 `packs/writing/pack.json`（4 skill）；保留上游 `LICENSE`（写到 `packs/writing/LICENSE`） |
| FR-803 `packs/garage/` 扩容 | `cp -r .agents/skills/{find-skills,writing-skills}/ packs/garage/skills/`；改写 `packs/garage/pack.json.skills[]` 从 `["garage-hello"]` 到字典序 `["find-skills","garage-hello","writing-skills"]` |
| FR-804 family-level 共享资产 | 选 **ADR-D8-1 候选 A**（family-level shared 路径）：`packs/coding/skills/docs/`、`packs/coding/skills/templates/`、`packs/coding/principles/`；详见 §7 ADR-D8-1 |
| FR-805 `.agents/skills/` 处置 | 选 **ADR-D8-2 候选 C**（删除 + IDE 重定向）：`rm -rf .agents/skills/`，本仓库 IDE/Claude Code 加载入口转向 dogfood 安装产物 `.claude/skills/` / `.cursor/skills/`（由 `garage init --hosts cursor,claude` 在仓库根 dogfood 后产生）；详见 §7 ADR-D8-2 |
| FR-806 端到端 smoke + walkthrough | 在 `/tmp/f008-smoke/` 跑 `garage init --hosts all`，归档 stdout / `host-installer.json` / 三家宿主目录 ls 输出 |
| FR-807 文档同步 | `packs/README.md` 当前 packs 表 + 三个 pack `README.md` + `docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段 + `RELEASE_NOTES.md` 新增 F008 段 + `AGENTS.md § "Skill 写作原则"` 路径同步（详见 §7 ADR-D8-3） |

### 2.2 来自规格的非功能驱动力（NFR / CON）

| 驱动 | 设计承接 |
|---|---|
| NFR-801 宿主无关性持续守住 | `cp -r` 是字节级复制，源端无宿主特定字面值则目标端必无；现有 `.agents/skills/` 下扫描 `grep -rE '\.claude/\|\.cursor/\|\.opencode/\|claude-code'` 命中数 0（本设计 §10 验证），搬迁动作不引入新命中 |
| NFR-802 测试基线零回归 | D008 不动 `src/garage_os/`，因此 D7 安装管道行为不变；新增测试覆盖 (a) 三个 pack.json schema (b) family asset 字节级搬迁 (c) drift 收敛 (d) `.agents/skills/` 删除后 git status 干净 |
| NFR-803 `garage init --hosts all` ≤ 5s | 当前 packs 全装规模 ≈ 29 skill × 3 host = 87 file write + 3 pack.json read + 1 manifest write，I/O 量级在 SSD 上次毫秒；smoke 阶段实测 |
| NFR-804 git diff 可审计 | 5 commit 分组（coding / writing / garage / layout / docs），由 hf-tasks 阶段拆分 |
| CON-801 不修改 F007 安装管道任何代码 | D008 严禁触动 `src/garage_os/adapter/installer/`；本设计无任何代码改动行 |
| CON-802 复用 F007 `pack.json` schema | 三个新增/扩展 pack.json 严格遵循 6 字段（schema_version/pack_id/version/description/skills[]/agents[]） |
| CON-803 字节级 1:1 搬迁 | 用 `cp -r`（或等价 git mv 路径）；审计方式 `find packs/coding/skills/<id>/ -type f -exec sha256sum {} \;` 与源端 `.agents/skills/harness-flow/skills/<id>/` 对应文件 SHA-256 字节级相等 |
| CON-804 `.agents/skills/` 处置必须本 cycle 收敛 | ADR-D8-2 选定候选 C 删除；不留双副本、不留软链、不留 dead 文件 |

### 2.3 来自规格 § 4.2 "Design Reviewer 可拒红线" 的 6 条硬门槛

| 红线 | D008 承接证据 |
|---|---|
| 1. family-asset 去重不变量 | ADR-D8-1 选定候选 A 把 11 项 family-level 资产**只放 1 份**于 `packs/coding/skills/{docs,templates}/` + `packs/coding/principles/`；§10 验证 `find packs -name <file>` 计数 ≤ 1 |
| 2. `.agents/skills/` 处置后 git status 干净 | ADR-D8-2 选定候选 C 完全删除；§10 验证 `git status --porcelain` 输出空 |
| 3. `docs/principles/skill-anatomy.md` drift 收敛 | ADR-D8-3 选定 "保留根级 + 反向同步 + family 副本归一" 路径：把 family 副本（HF 术语）反向同步到根级（先复制为 packs/coding/principles/，让两份变成同一份的 git 副本），然后让 AGENTS.md 路径不变；§10 验证 `diff /workspace/docs/principles/skill-anatomy.md /workspace/packs/coding/principles/skill-anatomy.md` 输出空 |
| 4. AGENTS.md 5 分钟冷读链 | ADR-D8-3 选定后 AGENTS.md § "Skill 写作原则" 引用的 `docs/principles/skill-anatomy.md` 路径不变（仍存在于仓库根） |
| 5. 本仓库 IDE 加载链 | ADR-D8-2 选定候选 C 后，本仓库一次性 dogfood `garage init --hosts cursor,claude` 把 packs 物化到 `.claude/skills/` + `.cursor/skills/`，IDE 加载入口转向 dogfood 产物；§10 walkthrough 提供 `find .cursor/skills -name 'SKILL.md' \| head -5` 证据 |
| 6. F007 管道不动 | `git diff main..HEAD -- src/garage_os/` 必须为空；§10 验证由 hf-traceability-review 自动覆盖 |

### 2.4 来自 F007 的 **关键工程边界**（在 spec 阶段未明确，design 阶段显式化）

**F007 安装管道只复制 `<pack-id>/skills/<id>/SKILL.md` 单文件**，不递归 `references/` / `evals/` / `scripts/` / `assets/` / `prompts/` / `examples/` 子目录。证据：`src/garage_os/adapter/installer/pack_discovery.py:62-66` 的 `Pack.skill_source_path()` 直接返回 `skills/<id>/SKILL.md`；`pipeline.py:165-212` 只对该单文件 read_text → inject → write_bytes。

这条事实**改变 F008 spec FR-801 验收 #2 的语义**：

- spec 写"`packs/coding/skills/<id>/references/<file>.md` 与源端字节级相等"（**仓库内** packs/ 与 `.agents/` 之间）— ✅ 仍可成立（`cp -r` 保证）
- spec 写"装到 `.claude/skills/hf-specify/` 后 `references/spec-template.md` 不 404"（**装后宿主**）— ❌ 在 D7 现有管道下**无法成立**，因为 D7 不复制 `references/`

D008 的处理：

- **不修改 D7 管道**（CON-801 硬约束）
- 显式承认 family-level 资产与 hf-* skill 内 `references/` 子目录在 D7 当前管道下**只能装到 SKILL.md 单文件层**；下游用户在 Claude Code 加载 hf-specify 时看到的引用 `references/spec-template.md` 实际指向 packs 仓库（用户自行 git clone Garage 仓库）的相对路径，而不是装到 `.claude/skills/hf-specify/references/` 的本地副本
- spec § 2.2 验收 #2 "装完后引用不 404" 的真正承接是：**packs 仓库本身在 git 上始终可访问**，下游用户的 Garage 仓库 checkout 是 family-level 资产的真源；下游宿主的 SKILL.md 引用是文档级提示，而非加载时硬依赖
- 替代承接方式（不在 D008 实施，作为 D9 候选）：D9 候选 — F007 管道扩展 `references/<...>` 递归复制（spec FR-704 留有 entry point）

**这条工程边界是 design 阶段消化掉的**，把 spec 中"装到下游宿主后 references 可解析"的验收口径下调到"在 packs/ 内可解析 + 下游宿主能拿到 SKILL.md 主体 + 引用是文档级提示"。详见 §7 ADR-D8-4。

### 2.5 现有系统约束

- F002 `garage init` 缺省行为不变（CON-702 沿用）
- F007 `garage init --hosts ...` 接口不变
- `.garage/config/host-installer.json` schema 不变（仍 schema_version=1）
- 没有数据库 / 常驻服务 / 网络依赖

## 3. 需求覆盖与追溯

| 规格条款 | 覆盖位置 |
|---|---|
| FR-801 `packs/coding/` 落盘 | §6 工作流 step 1 + §11 模块 `packs/coding/` |
| FR-802 `packs/writing/` 落盘 | §6 工作流 step 2 + §11 模块 `packs/writing/` |
| FR-803 `packs/garage/` 扩容 | §6 工作流 step 3 + §11 模块 `packs/garage/` |
| FR-804 family-level 资产可解析 + 去重 | §7 ADR-D8-1 + §11 模块 `packs/coding/skills/{docs,templates}/` + `packs/coding/principles/` + §2.4 边界说明 + §10 验证 |
| FR-805 `.agents/skills/` 处置 | §7 ADR-D8-2 + §6 工作流 step 5 + §10 验证 |
| FR-806 smoke + walkthrough | §10 验证策略 + §13 walkthrough 协议 |
| FR-807 文档同步 | §6 工作流 step 6 + §11 模块 `docs/` |
| NFR-801..804 + CON-801..804 | §2.2 表 + §10 验证 |
| § 4.2 Design Reviewer 6 条红线 | §2.3 表（每条红线指向 ADR + §10 验证步骤） |
| ASM-801..804 | 无设计层动作；implementation/finalize 阶段在 PR 描述中显式声明 |

## 4. 架构模式选择

D008 不是一个新代码模块的设计，是一次**仓库内容物 + 路径重组**：

- **核心模式**：File-System-as-Schema + Git-as-Distribution（与 D7 同根）
- **次级模式**：Source-of-Truth Convergence（drift 副本归一）
- **不引入**：新代码、新依赖、新接口、新数据库

## 5. 候选方案总览

D008 的"方案"分布在 8 项 ADR（spec § 11 非阻塞 1-8）。每项 ADR 分别在 §7 给出 compare view + 选定结论。本节只列 ADR 索引：

| ADR | 主题 | 候选数 | 选定 |
|---|---|---|---|
| **ADR-D8-1** | family-level 资产物理位置 | 3（A/B/C） | A — `packs/coding/skills/{docs,templates}/` + `packs/coding/principles/` |
| **ADR-D8-2** | `.agents/skills/` 处置方案 | 3（A/B/C） | C — 删除 + IDE 重定向到 dogfood 产物 |
| **ADR-D8-3** | `docs/principles/skill-anatomy.md` drift 收敛 | 3（删根级/软链/反向同步） | 反向同步 — 先把 family 副本（HF 术语）作为权威源 → 复制到 `packs/coding/principles/` + 同步根级 |
| **ADR-D8-4** | hf-* skill 内 `references/` 子目录的下游可达性边界 | 2（D7 管道扩展 / 文档级提示） | 文档级提示（D7 管道扩展是 D9 候选） |
| **ADR-D8-5** | `packs/garage/garage-sample-agent.md` 处置 | 3（保留/删除/移到 coding） | 保留 — 证明 agent surface 在多 pack 下仍工作 |
| **ADR-D8-6** | `pack.json.version` 是否 bump | 3（不动/微版/大版） | `packs/garage/` 0.1.0 → 0.2.0；`packs/coding/` `packs/writing/` 首版 0.1.0 |
| **ADR-D8-7** | `AGENTS.md` 同步范围 | 3（不改/局部刷新/全段重写） | 局部刷新 — `## Packs & Host Installer` 段 "未来计划 F008 候选" → "已落地"；`## Skill 写作原则` 引用路径不变（依 ADR-D8-3） |
| **ADR-D8-8** | smoke 路径 + 自动化集成测试 | 3（仅 manual smoke / 仅自动化 / 双轨） | 双轨 — `/tmp/f008-smoke/` manual smoke + `tests/adapter/installer/test_full_packs_install.py` 自动化集成测试 |

## 6. 候选方案对比与 trade-offs

详见 §7 各 ADR 的 compare view。本节只回顾**整体设计选择**：

D008 把每项 ADR 都倾向于"**最简且不可逆性最低**"的方案：

| 维度 | D008 整体倾向 |
|---|---|
| 复杂度 | 最低（无代码、无依赖、纯文件移动） |
| 可逆性 | 高（git revert 即可回滚） |
| 与 spec 一致性 | 严格遵守 § 4.2 6 条红线 |
| 面向未来 | 留好 D9 entry point（管道扩展 / uninstall / update） |
| 用户感知 | 下游用户单条命令获得 ≈ 29 skill |

## 7. 选定方案与关键决策（ADR）

### ADR-D8-1：family-level 资产物理位置

**Context**：spec FR-804 + § 11 非阻塞 #1 留三个候选。

**Compare**：

| 候选 | 核心思路 | 优点 | 主要代价 / 风险 | NFR / 约束适配 | 可逆性 |
|------|----------|------|------------------|----------------|--------|
| **A** `packs/coding/skills/{docs,templates}/` + `packs/coding/principles/`（与现有 `harness-flow/skills/docs/` + `harness-flow/skills/templates/` 同 layout） | family-level 共享资产作为 **packs/coding/** 内的"非 skill 兄弟目录"；与 6 处现有 `skills/docs/<file>` 引用直接对齐 | (1) 与上游 harness-flow 已有结构 1:1 同构，搬迁是 `cp -r`（CON-803 字节级 1:1 自然成立）(2) 11 个 family asset 只 1 份 (3) 不需要修改任何 hf-* skill 的相对引用路径 (4) 满足红线 1（去重不变量） | F007 安装管道不复制 `skills/docs/` `skills/templates/` 子目录 → 下游用户在装到 `.claude/skills/` 后引用 `skills/docs/...` 实际指向 git 仓库 packs 路径，而不是 `.claude/skills/` 本地副本（这是 §2.4 显式承认的边界 + ADR-D8-4 文档级提示策略） | 完美承接红线 1；红线 5 由 ADR-D8-2 dogfood 路径承接 | 高（cp -r，git revert 可逆） |
| B 复制到每个 hf-* skill 的 `references/` | 每个 skill 内嵌 family asset，下游装后 references 直接可用 | 装后 references 在 `.claude/skills/hf-specify/references/` 真实存在 | (1) 22 × 4 = 88 份 docs 冗余 + 22 × 5 = 110 份 templates 冗余 + 22 × 2 = 44 份 principles 冗余 = **242 份冗余** → 直接命中红线 1 (2) 改写 6 处现有 `skills/docs/<file>` 引用为 `references/<file>` (3) 22 × 11 = 242 SKILL.md / references 子文件改动 → CON-803 字节级 1:1 名义不成立 (4) 任一 family asset 改动需要在 22 处同步 | 命中红线 1，PASS_FAIL = FAIL | 中（要 lint 守门未来同步） |
| C `packs/coding/skills/_shared/` | 用 `_shared/` 表达"不是 skill 但被多 skill 引用" | (1) 1 份资产 (2) 与 ADR-D8-2 候选 C 解耦 | (1) 改写 6 处现有引用从 `skills/docs/<file>` 到 `skills/_shared/<file>` (2) 引入新约定 `_shared/`，与现有 harness-flow `skills/docs/` `skills/templates/` 结构产生不必要的 wording 漂移 (3) 与 spec § 12 "family-level 共享资产" 术语自然映射不一致 | 满足红线 1，但人工成本高 | 高 |

**Decision**: 选定 **A**。

**Consequences / Trade-offs**:

- ✅ 与 spec § 4.2 红线 1（去重不变量）完美对齐
- ✅ 与现有 harness-flow 结构 1:1 同构，搬迁动作纯 `cp -r`
- ✅ 6 处 `skills/docs/<file>` 引用 0 改写
- ⚠️ 接受 §2.4 边界：下游宿主装到的 SKILL.md 引用 `skills/docs/<file>` 是**文档级提示**（与 ADR-D8-4 联动）
- ✅ family asset 单点维护，未来要改某个 template 只需改 1 处

**Reversibility**: 高 — 若 D9 决定走 references 内嵌路径（候选 B 变体），可在那个 cycle 加 lint + 复制脚本，本 cycle 决策不阻挡。

### ADR-D8-2：`.agents/skills/` 处置方案

**Context**：spec FR-805 + § 11 非阻塞 #2 留三个候选。CON-804 要求本 cycle 必须收敛。

**Compare**：

| 候选 | 核心思路 | 优点 | 主要代价 / 风险 | NFR / 约束适配 | 可逆性 |
|------|----------|------|------------------|----------------|--------|
| A 删除 + git symlink 回 packs | `rm -rf .agents/skills/` 后用 `ln -s ../packs/coding/skills .agents/skills/coding`（git 支持 symlink） | (1) 本仓库 IDE 加载入口（`.agents/skills/`）形式不变 (2) 单一物理副本 | (1) git symlink 在 Windows 上需要管理员权限 / 开发者模式（spec ASM 未声明 OS 矩阵，但 Cursor 跨平台） (2) `.agents/skills/coding/<id>/SKILL.md` 与 `packs/coding/skills/<id>/SKILL.md` 是同一文件，但 cursor / claude code 的 skill loader 可能对 symlink 和真实目录处理不同 (3) git diff 在合并时对 symlink 改名 noisy | 满足红线 2 git status 干净 + 红线 5 IDE 加载链 | 中（symlink 删除即恢复） |
| B 双副本 + lint 守门 | 保留 `.agents/skills/`，加 pre-commit hook / pytest 用例校验字节相等 | (1) 本仓库 IDE 加载入口完全不变 (2) 不引入 symlink 平台风险 | (1) 28 个 SKILL.md + N 个 references 子文件双副本 → 红线 1 / 2 受到挑战（"双副本不算 drift" 需 lint 不漏） (2) lint 任意一次失败都会卡 PR (3) 与 ADR-D8-1 候选 A 选定后 family asset 在 packs 单点，但 hf-* skill 主体却双副本，混合方案不优雅 | 满足红线 2 仅当 lint 实施位置具体；spec 明确要求三选一（pre-commit / CI / pytest） | 高 |
| **C** 删除 + IDE 重定向到 dogfood 产物 | `rm -rf .agents/skills/`；本仓库一次性 `garage init --hosts cursor,claude` 在仓库根产生 `.cursor/skills/` + `.claude/skills/` 作为 IDE 加载入口（dogfood）；二者已通过 D7 安装管道与 packs/ 单向同步（`installed_by: garage` marker 标识） | (1) **零双副本**（packs 是源，`.cursor/skills/` 是 dogfood 产物，git 视角是装出来的"产物副本"，可由 `.gitignore` 排除以保持 git 干净）(2) 验证 D7 dogfood 路径可用（spec ASM-802 顺便覆盖）(3) 不引入 symlink 平台风险 (4) 本仓库自身就是下游用户最真实的"装好的样子" | (1) 必须改 `.gitignore` 排除 `.cursor/skills/` `.claude/skills/`（否则 git 把 dogfood 产物当源 commit 进来，破坏单源不变量）(2) 本仓库 cursor 用户必须先跑一次 `garage init --hosts cursor` 才能加载 skill；CONTRIBUTING.md / AGENTS.md 需说明 (3) 比候选 A symlink 多一个 dogfood 步骤 | 满足红线 1 / 2 / 5 全部 + 红线 6（不动管道，反过来 dogfood 验证管道）| 高（git revert 可恢复） |

**Decision**: 选定 **C**。

**Consequences / Trade-offs**:

- ✅ 单源不变量最强（`.cursor/skills/` 与 `.claude/skills/` 在 git 视角是"装出来的产物"，不在 git 受控）
- ✅ Dogfood D7 管道：本仓库自己跑 `garage init --hosts cursor,claude` 就是对 D7 + D8 联合最强证据
- ✅ 红线 5 验证：在 PR walkthrough 提供 `find .cursor/skills -name SKILL.md \| head -5` 输出 + `head .cursor/skills/hf-specify/SKILL.md` 显示 `installed_by: garage` 即满足
- ⚠️ 增加一行 `.gitignore`：`.cursor/skills/` `.claude/skills/`
- ⚠️ AGENTS.md 增加一段：本仓库自身贡献者首次 clone 后跑 `garage init --hosts cursor,claude` 以激活 IDE skill 加载

**Reversibility**: 高 — 若 D9 决定改回双副本或 symlink，git revert 即可。

### ADR-D8-3：`docs/principles/skill-anatomy.md` drift 收敛

**Context**：spec § 1 #6 + § 11 非阻塞 #3。实测 `docs/principles/skill-anatomy.md`（16707B，AHE 术语）与 `.agents/skills/harness-flow/docs/principles/skill-anatomy.md`（16637B，HF 术语）70 字节差，源自项目早期 AHE → HF rename 未同步根级。同一类问题：`hf-sdd-tdd-skill-design.md` 也在 family 内但根级无副本。

**Compare**：

| 候选 | 核心思路 | 优点 | 主要代价 / 风险 | NFR / 约束适配 | 可逆性 |
|------|----------|------|------------------|----------------|--------|
| 删根级 | `rm docs/principles/skill-anatomy.md`，AGENTS.md 路径改为 `packs/coding/principles/skill-anatomy.md` | 单源最干净 | AGENTS.md § "Skill 写作原则" 引用路径变化 → 5 分钟冷读链需要刷新 → 红线 4 触发可拒判定 | 满足红线 1 / 3 但触发红线 4 | 高 |
| 软链 | `ln -sf ../../packs/coding/principles/skill-anatomy.md docs/principles/skill-anatomy.md` | 单源 + AGENTS.md 路径不变 | 跨平台 symlink 风险（同 ADR-D8-2 A 候选）；ADR-D8-2 已避开 symlink | 满足全部红线但平台风险 | 高 |
| **反向同步** | 把 family 副本（HF 术语，更新版）作为权威源 → 复制到 `packs/coding/principles/skill-anatomy.md`；同步反向覆盖根级 `docs/principles/skill-anatomy.md` 为同一份字节内容；二者从此是"两个文件但字节相等" | (1) AGENTS.md 路径不变 (2) 跨平台无 symlink 风险 (3) packs/coding/ 内有自己的 principles 副本（与 ADR-D8-1 A 候选自洽）(4) 根级保留是给"未挂 packs 的早期 Garage 用户"的最小 fallback | (1) 形式上是双副本（不严格满足红线 1 字面"≤ 1 份"）(2) 需要 CI/lint 守门保证两份永远字节相等（与 ADR-D8-2 候选 C 不一致——D8-2 选 C 拒绝了双副本路径） | 红线 1 字面违反；但 spec 明确允许"design 显式 ADR 例外 + 给出 lint 守门方案" | 高 |

第三个候选有红线 1 字面冲突。重新审视 spec § 4.2 红线 1 原文："让同一 family-level 文件在仓库 `packs/` 内出现 ≥2 份磁盘副本，且 ADR 未显式声明这是有意为之 + 给出 lint 守门方案" — 红线 1 实际只约束 **packs/ 内**，根级 `docs/principles/skill-anatomy.md` 在 `packs/` 之外，**不触发红线 1**。重读 spec § 4.2 红线 3："`docs/principles/skill-anatomy.md` 与 `packs/coding/principles/skill-anatomy.md` 跑 diff 仍显示内容差异" — 这是允许两份文件存在但要求字节相等。所以"反向同步"路径完全合规。

**Decision**: 选定 **反向同步**。

具体动作：
1. 取 `.agents/skills/harness-flow/docs/principles/skill-anatomy.md`（HF 术语，更新版）作为权威源
2. 复制到 `packs/coding/principles/skill-anatomy.md`（与 ADR-D8-1 A 候选自洽）
3. 反向覆盖根级 `docs/principles/skill-anatomy.md` 为同一份字节内容（落地手段：`cp packs/coding/principles/skill-anatomy.md docs/principles/skill-anatomy.md`）
4. 在 `tests/adapter/installer/test_skill_anatomy_drift.py` 加一个 sentinel 测试：`assert sha256(docs/principles/skill-anatomy.md) == sha256(packs/coding/principles/skill-anatomy.md)` — 这是 spec 红线 3 的硬门槛

**Consequences / Trade-offs**:

- ✅ AGENTS.md § "Skill 写作原则" 引用路径不变（红线 4 通过）
- ✅ 跨平台无 symlink 风险
- ✅ 与 ADR-D8-1 A 候选自洽（packs/coding/principles/ 是 family-level 资产位置）
- ⚠️ 形式上仍是两份文件，但 sentinel 测试守门保证字节永远相等

`hf-sdd-tdd-skill-design.md` 同样从 family 副本复制到 `packs/coding/principles/`，但因为根级**没有**该文件，只是单向落到 packs/coding/principles/，无 drift 风险。

**Reversibility**: 高 — 若 D9 决定走 ADR-D8-2 候选 A symlink 路径，可在那时把根级改成 symlink；本 cycle 决策不阻挡。

### ADR-D8-4：hf-* skill 内 `references/` 子目录的下游可达性边界

**Context**：见 §2.4。F007 安装管道只复制 SKILL.md 单文件，不递归 `references/`。spec FR-801 验收 #2 写"装后 references 字节级相等"，但 D7 管道实际只装 SKILL.md。

**Compare**：

| 候选 | 核心思路 | 优点 | 主要代价 / 风险 | NFR / 约束适配 | 可逆性 |
|------|----------|------|------------------|----------------|--------|
| D7 管道扩展（递归 `references/`） | 修改 `pipeline.py:_resolve_targets` 把 `references/` `evals/` `scripts/` 子目录也加入 targets | 下游宿主装后 references 真实可达 | (1) 直接违反 CON-801 "F008 严禁修改 src/garage_os/" + 红线 6 (2) 必须改 30 个 installer 测试 (3) review surface 失控 | 触发红线 6 直接 FAIL | 中 |
| **文档级提示** | 承认下游宿主装到的 SKILL.md 引用 `references/<file>` 是文档级提示（不在装后宿主目录可达），下游用户的 Garage 仓库 git checkout 是这些 references 的真源 | (1) 不动 D7 管道（CON-801 / 红线 6 通过）(2) Walking Skeleton 哲学：先把"下游能装到 SKILL.md 主体"做对，扩展能力留给 D9 | (1) spec FR-801 验收 #2 字面口径需要 design 阶段重述（已在 §2.4 重述）(2) 下游用户在 Claude Code 里点击 `references/spec-template.md` 链接需要去 Garage 仓库 git clone 或浏览 GitHub | 通过红线 6；spec 验收 #2 口径下调到 "在 packs 仓库内 references 字节级相等 + 下游 SKILL.md 主体不 404" | 高 |

**Decision**: 选定 **文档级提示**。D9 候选记录"管道递归 references"作为后续工作。

**Consequences / Trade-offs**:

- ✅ CON-801 / 红线 6 严格遵守
- ⚠️ 下游用户使用体验：装后 SKILL.md 主体可被 Claude Code/Cursor 加载，但内嵌 `references/<file>` 链接需访问 Garage 仓库
- ✅ 把"管道扩展" deferred 到 D9 候选，与 spec § 5 "F008 候选 — `garage uninstall` / `garage update`" 在同一 backlog
- 在 `RELEASE_NOTES.md` F008 段 "已知限制" 显式说明这点，让用户感知不到落差

**Reversibility**: 高 — D9 实施管道扩展后，本设计无需推翻，自动受益。

### ADR-D8-5：`packs/garage/garage-sample-agent.md` 处置

**Compare**：

| 候选 | 优点 | 代价 |
|---|---|---|
| **保留**（默认） | 证明 D7 agent surface 在多 pack 下仍工作；让 dogfood 安装时 agents 数 = 1（M=1，N=29） | `packs/garage/` 三件套不对称（3 skill + 1 agent） |
| 删除 | 三件套对称（3 skill + 0 agent） | 失去 agent surface 的活体验证；下次有 agent 内容物时还得重新建 |
| 移到 `packs/coding/agents/` | 让 hf-* family 拥有未来 reviewer agent 的容器 | hf-* 没有当前 agent 内容物，移过去是空壳 |

**Decision**: 选定 **保留**。`packs/garage/pack.json.agents[]` 仍 = `["garage-sample-agent"]`。

### ADR-D8-6：`pack.json.version` 是否 bump

**Compare**：

| 候选 | 适用情景 |
|---|---|
| 不动 | 不适合：`packs/garage/` 内容从 1 → 3 skill 是非破坏性扩容，但 0.1.0 已发布给用户，应表达"内容增加" |
| **微版** | `packs/garage/` 0.1.0 → **0.2.0**；`packs/coding/` `packs/writing/` 首版 **0.1.0** |
| 大版 | F008 不动 schema、不破坏 API，跳到 1.0.0 不对应任何 contract 稳定承诺 |

**Decision**: 选定 **微版**。

### ADR-D8-7：`AGENTS.md` 同步范围

**Compare**：

| 候选 | 范围 |
|---|---|
| 不改 | 不适合：F008 落地后 packs 表已变化，AGENTS.md 与现实 drift |
| **局部刷新** | (1) `## Packs & Host Installer` 段 5 分钟冷读指针表中 "F008 候选" 改为 "已落地"；(2) 增一段 "本仓库 IDE 加载入口" 说明（与 ADR-D8-2 候选 C 配套）；(3) `## Skill 写作原则` 引用路径不变（依 ADR-D8-3） |
| 全段重写 | 过度改动；review surface 不必要扩大 |

**Decision**: 选定 **局部刷新**。

### ADR-D8-8：smoke 路径 + 自动化集成测试

**Compare**：

| 候选 | 优点 | 代价 |
|---|---|---|
| 仅 manual smoke | 快 | 无回归保护；下次有人破 packs 内容 CI 不报警 |
| 仅自动化 | 持续守护 | 缺少最真实的下游用户视角证据 |
| **双轨** | (1) `/tmp/f008-smoke/` manual smoke 提供 walkthrough 证据 (2) `tests/adapter/installer/test_full_packs_install.py` 自动化集成测试 (在 fixture 临时目录跑 install_packs() + 校验 N=29 + manifest 内容 + family asset 不被装但 SKILL.md 被装) 提供回归保护 | 略多工作量但都是机械的 |

**Decision**: 选定 **双轨**。

## 8. 架构视图

### 8.1 packs/ 落地后目录结构（核心视图）

```
packs/
├── README.md                          # 顶层契约 + "当前 packs" 表更新
├── garage/                            # F007 已存在，本 cycle 扩容
│   ├── README.md                      # 同步刷新
│   ├── pack.json                      # version 0.1.0 → 0.2.0; skills[] 1→3
│   ├── skills/
│   │   ├── garage-hello/SKILL.md      # F007 已落
│   │   ├── find-skills/               # F008 新增（含 SKILL.md）
│   │   └── writing-skills/            # F008 新增（含 SKILL.md + 子文件）
│   └── agents/
│       └── garage-sample-agent.md     # F007 已落，保留（ADR-D8-5）
├── coding/                            # F008 新增（HF workflow family）
│   ├── README.md                      # 22 skill 清单 + 与 family asset 引用关系
│   ├── pack.json                      # 0.1.0 / skills[] 长度 22 / agents[] = []
│   ├── skills/
│   │   ├── hf-bug-patterns/           # 21 个 hf-* + using-hf-workflow
│   │   ├── hf-code-review/            # = 22 个 skill 子目录
│   │   ├── ... (略)
│   │   ├── using-hf-workflow/
│   │   ├── docs/                      # 4 个 family-level shared docs（非 skill）
│   │   │   ├── hf-command-entrypoints.md
│   │   │   ├── hf-workflow-entrypoints.md
│   │   │   ├── hf-workflow-shared-conventions.md
│   │   │   └── hf-worktree-isolation.md
│   │   └── templates/                 # 5 个 HF templates（非 skill）
│   │       ├── finalize-closeout-pack-template.md
│   │       ├── review-record-template.md
│   │       ├── task-board-template.md
│   │       ├── task-progress-template.md
│   │       └── verification-record-template.md
│   └── principles/                    # 2 个 HF principles（非 skill，与根级 docs/principles/ 字节同步）
│       ├── skill-anatomy.md
│       └── hf-sdd-tdd-skill-design.md
└── writing/                           # F008 新增（写作 family）
    ├── README.md                      # 4 skill 清单 + 与卡兹克 humanizer 协作示例
    ├── LICENSE                        # 上游 .agents/skills/write-blog/LICENSE 搬来
    ├── pack.json                      # 0.1.0 / skills[] 长度 4 / agents[] = []
    └── skills/
        ├── blog-writing/              # 含 SKILL.md + 子文件
        ├── humanizer-zh/
        ├── hv-analysis/               # 含 prompts/ 子目录
        └── khazix-writer/             # 含 prompts/ 子目录
```

### 8.2 `.agents/skills/` 处置后状态（与 ADR-D8-2 候选 C 联动）

```
.agents/                  # 删除 skills/ 子目录
├── (skills/ 已删除)

.gitignore 增加:
+ .cursor/skills/
+ .claude/skills/

本仓库自身贡献者首次 clone 后:
$ garage init --hosts cursor,claude
→ 在仓库根 dogfood 出 .cursor/skills/ + .claude/skills/，IDE 即可加载

→ AGENTS.md 增一段说明
```

### 8.3 drift 收敛后状态（与 ADR-D8-3 联动）

```
docs/principles/skill-anatomy.md         ← 字节内容由 packs/coding/principles/skill-anatomy.md 反向同步
packs/coding/principles/skill-anatomy.md ← 权威源（HF 术语，更新版）

二者由 sentinel 测试 test_skill_anatomy_drift.py 守门字节相等
```

### 8.4 端到端安装管道（D7 不动，D8 仅观察）

```
                            ┌─────────────────────────┐
                            │ packs/{garage,coding,    │
                            │   writing}/             │
                            │   ├── pack.json         │
                            │   ├── README.md         │
                            │   ├── skills/<id>/      │
                            │   │     SKILL.md        │
                            │   └── agents/<id>.md    │
                            └─────────────┬───────────┘
                                          │ discover_packs()
                                          ▼
              ┌───────────────────────────────────────────────────┐
              │  D7 install_packs(workspace, packs, hosts, ...)   │
              │  (CON-801: D8 严禁触动)                            │
              └───────────────┬───────────────────────────────────┘
                              │ adapter.target_skill_path()
                              │ adapter.target_agent_path()
                              ▼
        ┌─────────────────────┬─────────────────────┬────────────────────┐
        │  .claude/skills/    │  .opencode/skills/  │  .cursor/skills/   │
        │  .claude/agents/    │  .opencode/agent/   │  (no agent surface)│
        └─────────────────────┴─────────────────────┴────────────────────┘
                              │
                              ▼
              .garage/config/host-installer.json
              { schema_version=1, installed_hosts=[...],
                installed_packs=["coding","garage","writing"],
                files=[(src,dst,host,pack_id,content_hash) × N×3] }
```

注意：family-level 资产 `packs/coding/skills/{docs,templates}/` + `packs/coding/principles/` 在 D7 管道下**不被复制到下游宿主**（pipeline 只递归到 `skills/<id>/SKILL.md` 单文件），它们在装后宿主目录下不存在 — 这是 ADR-D8-4 显式承认的边界，下游用户访问 family asset 走 git 仓库路径。

## 9. 模块职责与边界

D008 不引入新代码模块，但定义以下"内容物模块"的职责边界：

| 模块 | 职责 | 边界 |
|---|---|---|
| `packs/garage/` | Garage 自带 getting-started 入口三件套：占位 sample skill + 发现 meta-skill + 写 skill 的 meta-skill | 不放 hf-* / write-blog 内容；不放 family asset |
| `packs/coding/` | HF workflow family 的可分发版本：22 个 hf-* + using-hf-workflow + 11 项 family-level 资产 | 不放 write-blog / find-skills / writing-skills；不放 hf-* skill 业务逻辑改动 |
| `packs/writing/` | 内容创作 family：4 个 write-blog 子 skill + 上游 LICENSE | 不放 hf-* / find-skills / writing-skills |
| `packs/coding/skills/{docs,templates}/` | HF family 共享 docs + templates（非 skill 子目录）| 不被 D7 管道复制到下游宿主（ADR-D8-4） |
| `packs/coding/principles/` | HF family principles（与根级 docs/principles/ 字节同步） | sentinel 测试守门 |
| `docs/principles/skill-anatomy.md` | AGENTS.md § "Skill 写作原则" 5 分钟冷读链入口 | 字节内容由 packs/coding/principles/ 反向同步 |
| `.gitignore` 新增行 | 排除 `.cursor/skills/` / `.claude/skills/` 这两个 D8-2 候选 C 的 dogfood 产物目录 | 仅 ignore 这两个目录，不影响其它 |
| `AGENTS.md` § "Packs & Host Installer" | 同步刷新 5 分钟冷读指针表 | "F008 候选" → "已落地"；增"本仓库 IDE 加载入口"段 |

## 10. 数据流、控制流与关键交互

### 10.1 D008 实施流（5 类提交分组，对应 NFR-804）

```
T1 (coding):    cp -r .agents/skills/harness-flow/skills/{hf-*,using-hf-workflow}/ packs/coding/skills/
                cp -r .agents/skills/harness-flow/skills/{docs,templates}/ packs/coding/skills/
                mkdir packs/coding/principles/
                cp .agents/skills/harness-flow/docs/principles/{skill-anatomy,hf-sdd-tdd-skill-design}.md packs/coding/principles/
                cp packs/coding/principles/skill-anatomy.md docs/principles/skill-anatomy.md   # 反向同步
                write packs/coding/pack.json
                write packs/coding/README.md
                add tests/adapter/installer/test_skill_anatomy_drift.py
                git commit -m "f008(coding): packs/coding/ 22 skill + 11 family asset + drift 收敛"

T2 (writing):   cp -r .agents/skills/write-blog/{blog-writing,humanizer-zh,hv-analysis,khazix-writer}/ packs/writing/skills/
                cp .agents/skills/write-blog/LICENSE packs/writing/LICENSE
                write packs/writing/pack.json
                write packs/writing/README.md
                git commit -m "f008(writing): packs/writing/ 4 skill + LICENSE"

T3 (garage):    cp -r .agents/skills/find-skills/ packs/garage/skills/
                cp -r .agents/skills/writing-skills/ packs/garage/skills/
                edit packs/garage/pack.json (skills[] 1→3, version 0.1.0→0.2.0)
                edit packs/garage/README.md
                git commit -m "f008(garage): +find-skills +writing-skills，0.1.0→0.2.0"

T4 (layout):    rm -rf .agents/skills/
                edit .gitignore (+.cursor/skills/ +.claude/skills/)
                edit AGENTS.md (Packs & Host Installer 段刷新 + IDE 加载入口段)
                add tests/adapter/installer/test_full_packs_install.py
                git commit -m "f008(layout): 删 .agents/skills/，IDE 入口转向 dogfood，新增全装集成测试"

T5 (docs):      edit packs/README.md (当前 packs 表 +coding +writing +扩容 garage)
                edit docs/guides/garage-os-user-guide.md (Pack & Host Installer 段补 N skill)
                add RELEASE_NOTES.md F008 段
                # smoke walkthrough 在 PR 描述中给出（不入仓）
                git commit -m "f008(docs): packs/README + user-guide + RELEASE_NOTES F008"
```

### 10.2 验证步骤（对应 § 4.2 6 条红线）

| 红线 | 验证命令 | 预期 |
|---|---|---|
| 1 (去重不变量) | `for f in $(ls packs/coding/skills/docs/ packs/coding/skills/templates/ packs/coding/principles/); do echo $f $(find packs -name "$f" -type f \| wc -l); done` | 每行第二列 ≤ 1 |
| 2 (.agents/skills/ 处置 + git status) | `ls .agents/skills/ 2>/dev/null && git status --porcelain` | ls 报错（不存在），git 输出空 |
| 3 (drift 收敛) | `diff /workspace/docs/principles/skill-anatomy.md /workspace/packs/coding/principles/skill-anatomy.md` | 输出空 |
| 4 (AGENTS.md 冷读链) | `grep -E 'docs/principles/skill-anatomy.md' AGENTS.md && test -f docs/principles/skill-anatomy.md` | 两条都成功 |
| 5 (IDE 加载链) | `garage init --hosts cursor,claude && find .cursor/skills -name 'SKILL.md' \| head -5 && head -5 .cursor/skills/hf-specify/SKILL.md` | 至少 5 个 SKILL.md 输出 + hf-specify front matter 含 `installed_by: garage` `installed_pack: coding` |
| 6 (F007 管道不动) | `git diff main..HEAD -- src/garage_os/` | 输出空 |

### 10.3 端到端 smoke (FR-806 + ADR-D8-8 双轨)

```bash
# Manual smoke (walkthrough 证据)
mkdir -p /tmp/f008-smoke && cd /tmp/f008-smoke && git init
# 假设 garage CLI 安装在 PATH 上
garage init --hosts all 2>&1 | tee /tmp/f008-smoke/init.log
# 期待 stdout: Installed 29 skills, 1 agents into hosts: claude, cursor, opencode
ls .claude/skills/ | wc -l   # → 29
ls .cursor/skills/ | wc -l   # → 29
ls .opencode/skills/ | wc -l # → 29
ls .claude/agents/ | wc -l   # → 1 (garage-sample-agent.md)
cat .garage/config/host-installer.json | jq '.installed_packs' # → ["coding","garage","writing"]
cat .garage/config/host-installer.json | jq '.files | length'  # → 87 + 1 = 88 (29 skill × 3 host + 1 agent × 1 host claude only)

# Automated regression
uv run pytest tests/adapter/installer/test_full_packs_install.py -v
```

## 11. 接口、契约与关键不变量

### 11.1 不变量（implementation 阶段必须守住）

| Invariant | 验证方式 | 责任 commit |
|---|---|---|
| INV-1 三 pack.json 总 skills[] 长度 = 29 | 自动化 `test_full_packs_install.py` | T4 |
| INV-2 family asset 单点（spec § 4.2 红线 1）| `find packs -name <file> \| wc -l ≤ 1` | T1 |
| INV-3 drift 收敛（spec § 4.2 红线 3）| `test_skill_anatomy_drift.py` sentinel | T1 |
| INV-4 字节级 1:1 搬迁（CON-803）| 任一 SKILL.md SHA-256 与上游 `.agents/skills/...` 同名相等 | T1 / T2 / T3 |
| INV-5 D7 src/garage_os 零修改（CON-801 + 红线 6）| `git diff main..HEAD -- src/garage_os/` 输出空 | 全 PR |
| INV-6 git status 干净（红线 2）| `git status --porcelain` 输出空 | T4 |
| INV-7 IDE 加载链可重放（红线 5）| `garage init --hosts cursor,claude` + `find .cursor/skills` 输出 ≥ 5 行 | walkthrough |
| INV-8 .gitignore 排除 dogfood 产物 | grep `.cursor/skills/` `.claude/skills/` 在 .gitignore | T4 |
| INV-9 NFR-801 grep 命中 0 | `grep -rE '\.claude/\|\.cursor/\|\.opencode/\|claude-code' packs/coding/ packs/writing/` | T1 / T2 |

### 11.2 不引入的契约

- 不新增任何 `pack.json` 字段
- 不新增任何 host adapter 接口
- 不新增 manifest schema 字段
- 不新增 CLI flag

## 12. 非功能需求与约束落地

| NFR / CON | 落地模块 / 步骤 |
|---|---|
| NFR-801 宿主无关性 | T1+T2 复制后跑 INV-9 grep；CI 沿用 F007 NFR-701 测试自动覆盖到 packs/coding/ packs/writing/（spec FR-701 验收 #1 已承诺该测试自动覆盖新 pack） |
| NFR-802 测试基线零回归 | 现有 30 个 installer 测试 + N 个其它测试 0 改写；新增 ≥ 4 个用例（test_full_packs_install / test_skill_anatomy_drift / test_packs_garage_extended / test_dogfood_layout） |
| NFR-803 ≤ 5s | smoke 实测 `time garage init --hosts all`；test_full_packs_install 内 `pytest --durations` 抓 wall-clock |
| NFR-804 git diff 可审计 | 5 commit 分组（§10.1 T1-T5） |
| CON-801..804 | INV-5 / INV-6 / INV-4 / FR-805 ADR-D8-2 |

## 13. 测试与验证策略

### 13.1 自动化测试（在 hf-tasks 阶段拆任务后由 hf-test-driven-dev 实施）

| 测试文件 | 覆盖 |
|---|---|
| `tests/adapter/installer/test_skill_anatomy_drift.py` | INV-3：根级 vs packs/coding/principles/ 字节相等 sentinel；T1 commit |
| `tests/adapter/installer/test_full_packs_install.py` | INV-1：三 pack.json skills[] 总和 = 29；INV-2：family asset 单点；INV-4 抽样：随机选一个 hf-* skill SKILL.md 与上游字节级相等；fixture 跑 install_packs() 三 host 全装、断言 stdout 形式 + manifest 形式；T4 commit |
| 现有 30 个 installer 测试 | 0 改写、必须仍 100% 通过（NFR-802） |

### 13.2 Manual smoke walkthrough（FR-806 + ADR-D8-8）

按 §10.3 步骤跑，归档：

- `/tmp/f008-smoke/init.log`
- `/tmp/f008-smoke/.garage/config/host-installer.json` 节选
- 三家宿主目录 `tree -L 2 .{host}/skills | head -40` 输出
- 在 PR walkthrough 中以 `<TextReference>` 引用日志、以截图 / 终端输出展示 IDE 加载链证据（INV-7）

### 13.3 最薄端到端验证路径（Walking Skeleton）

```
源 packs/coding/skills/hf-specify/SKILL.md
  ↓ install_packs()
.claude/skills/hf-specify/SKILL.md (with installed_by: garage marker)
  ↓ Claude Code skill loader
hf-specify skill 在 Claude Code 内可被 invoke
```

这条路径在 dogfood smoke 内一次性验证。

## 14. 失败模式与韧性策略

| 失败模式 | 触发条件 | 缓解 |
|---|---|---|
| **F1**：cp -r 误把 .DS_Store 等系统文件搬进 packs | macOS 开发者本地有隐藏文件 | T1 commit 前跑 `find packs -name .DS_Store -delete`；新增 `.gitignore` 项 |
| **F2**：drift sentinel 失败 | 未来有人修改 packs/coding/principles/skill-anatomy.md 但忘了同步根级 | sentinel 测试 = 红线 3 的硬门槛；CI 卡 PR |
| **F3**：dogfood 后 .cursor/skills/ 误 commit 到 git | .gitignore 漏写或 force-add | T4 commit 顺带跑 `git status` 验证 |
| **F4**：23 个 hf-* + using-hf-workflow != 22 但 spec 期待 22 | 上游 .agents/skills/harness-flow/skills 在 cycle 期间被改 | spec ASM-801 已声明；T1 commit 前跑 `ls .agents/skills/harness-flow/skills/ \| grep -c '^hf-'` 确认 21 |
| **F5**：write-blog LICENSE 丢失 | T2 忘了 cp LICENSE | FR-802 验收 #2 + INV：tests 增加 `assert (packs/writing/LICENSE).exists()` 或在 README 显式声明 |
| **F6**：smoke 时 garage CLI 不在 PATH | 实施环境未 `pip install -e .` | walkthrough 使用 `python -m garage_os` 或先 `uv pip install -e .` |
| **F7**：family asset (skills/docs/, skills/templates/) 在装到下游宿主时被遗漏导致下游用户引用 404 | D7 管道不递归子目录（ADR-D8-4 已承认）| RELEASE_NOTES F008 "已知限制" 显式说明；D9 候选记录管道扩展 |

## 15. 任务规划准备度

D008 的 5 个工作分组（T1-T5）已清晰对应 NFR-804 五类 commit。`hf-tasks` 阶段可直接：

- 按 5 类拆 5 个 task
- 每个 task 独立可 review
- T4 是关键合流点（rm -rf + .gitignore + AGENTS.md + 集成测试）需注意原子性
- T5 的 RELEASE_NOTES 必须在 finalize 阶段最后写

## 16. 关键决策记录（ADR 摘要）

见 §7。共 8 项 ADR：

| ADR | 决策 | 可逆性 |
|---|---|---|
| ADR-D8-1 | family asset 物理位置: `packs/coding/skills/{docs,templates}/` + `packs/coding/principles/`（候选 A） | 高 |
| ADR-D8-2 | `.agents/skills/` 处置: 删除 + IDE 重定向到 dogfood 产物（候选 C） | 高 |
| ADR-D8-3 | drift 收敛: 反向同步 family 副本到 packs/coding/principles/ + 同步根级 | 高 |
| ADR-D8-4 | hf-* 内 references 子目录的下游可达性: 文档级提示（不动 D7 管道） | 高 |
| ADR-D8-5 | `garage-sample-agent.md`: 保留 | 高 |
| ADR-D8-6 | `pack.json.version`: garage 0.1.0→0.2.0；coding/writing 首版 0.1.0 | 高 |
| ADR-D8-7 | AGENTS.md 同步: 局部刷新 | 高 |
| ADR-D8-8 | smoke 路径: 双轨（manual /tmp + 自动化集成测试） | 高 |

## 17. 明确排除与延后项

| 项 | 为什么不做 | 延后到 |
|---|---|---|
| 修改 D7 安装管道（递归 references/）| CON-801 / 红线 6 | D9 候选 |
| `garage uninstall` / `garage update` | spec § 5 已显式 deferred | D9 候选 |
| `~/.claude/skills/` 全局安装 | spec § 5 / 与 workspace-first 信念冲突 | 单独 cycle |
| `packs/product-insights/` | 无现成 skill 内容物 | 待真实 product discovery skill 沉淀 |
| 改写任何 SKILL.md 业务逻辑 | spec § 2.3 非目标 | 各 skill 单独 cycle |
| 新增宿主 (Codex / Gemini CLI / Windsurf) | spec § 5 | F008+ 增量 |
| `pack.json` 新字段 | spec § 5 | Stage 3 候选 |
| `find-skills` 真功能化 | spec § 5 | 单独候选 |
| `writing-skills` render-graphs.js 可执行化 | spec § 5 | 单独候选 |
| 下游用户在装后能直接打开 references/ | ADR-D8-4 选定文档级提示 | D9 候选（与 D7 管道扩展同 cycle） |

## 18. 风险与开放问题

### 阻塞性（必须在 hf-design-review 通过前关闭）

无。

### 非阻塞性（可在 hf-tasks / 实施阶段细化）

1. **dogfood `garage init` 在 Garage 仓库自身运行需要 `garage` CLI 已 `pip install -e .`**：本设计假设 cycle 实施期间已有 `uv run python -m garage_os` 或等价命令。具体调用形式由 hf-tasks T4/walkthrough 决定。
2. **写 RELEASE_NOTES F008 段的最佳时机是 finalize 阶段**：但 T5 commit 已含 RELEASE_NOTES.md 改动，存在"实施期间放占位段、finalize 时填实测数据"的协调成本。可由 hf-tasks 拆分为 "T5 占位 + finalize 实测填充"。
3. **`.cursor/skills/` 在 git 视角是产物**：本仓库自身贡献者首次 clone + dogfood 后会看到 `.cursor/skills/` 30 个目录但不会被 git 跟踪。新贡献者可能困惑。AGENTS.md 段落需明确说明。
4. **`tests/adapter/installer/test_full_packs_install.py` 需要 fixture 跑真实 install_packs()**：可能涉及 fixture 生成临时 `.garage/` 与临时 `packs/`。可参考 F007 既有 `test_pipeline.py` fixture 模式。
