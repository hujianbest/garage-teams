# F008: Garage Coding Pack 与 Writing Pack — 把 `.agents/skills/` 物化为可分发 packs，让 `garage init` 真正交付"挂上目录就有 ~29 skills"（数由 manifest 派生）

- 状态: 已批准（auto-mode approval；见 `docs/approvals/F008-spec-approval.md`）
- 主题: 把当前散落在 `.agents/skills/` 下的 28 个已写好 SKILL.md（22 个 HF workflow [21 hf-* + 1 using-hf-workflow] + 4 个 write-blog 系列 + 1 个 writing-skills + 1 个 find-skills）按主题归并到 `packs/coding/` 与 `packs/writing/` 两个一级 pack，并把 F007 已落 `packs/garage/` 从 1 sample skill 扩到 3 skill（叠加 find-skills + writing-skills），让下游用户在自己项目里执行 `garage init --hosts <list>` 后，能直接获得 manifesto 承诺的 "Agent 几秒钟变成你的 Agent" 体验
- 日期: 2026-04-22
- 关联:
  - F001 § `CON-002` — 已声明 "Skills 存放在 `packs/coding/skills/` 和 `packs/product-insights/skills/`"，本 cycle 兑现 `packs/coding/`（`product-insights/` 留待后续，参见 § 5）
  - F007（Garage Packs 与宿主安装器）— 已落 `packs/<pack-id>/` 目录契约 + `garage init --hosts ...` 安装管道 + conflict 检测 + marker 注入 + extend mode + manifest；本 cycle **只增加 packs 内容**，安装管道与 host adapter 注册表零改动
  - `docs/soul/manifesto.md` § "终极形态"（"几秒后这个 Agent 就变成了你的 Agent"）+ § "核心信念" 第 1 / 5 条（数据归你、可传承）
  - `docs/soul/growth-strategy.md` § "Stage 1 → Stage 2 触发信号"（"用户日常工作中频繁使用 Garage 的 skills"）+ § "Stage 3 触发信号"（"Skills 数量 > 30"——本 cycle 把可分发 skills 从 1 推到约 29，越过该信号的前置工程基本就位）
  - `docs/soul/design-principles.md` § 1 宿主无关原则（搬迁过程必须保持源文件无任何宿主特定术语）
  - `packs/README.md` — 现有目录契约（顶层契约不变，只新增 2 个 `<pack-id>` 子目录）
  - `RELEASE_NOTES.md` "F007 — 已知限制 / 后续工作" 段第 1 条（"F008 候选 — 把 .agents/skills/ 30 个 HF skills 搬迁到 packs/coding/skills/，搬迁本身是机械动作 + 路径替换"）

## 1. 背景与问题陈述

F007 cycle 在仓库里建好了 packs 目录契约 + `garage init --hosts ...` 安装管道 + 三家宿主 adapter + 安装清单 + extend mode。但 cycle 收尾时，`packs/` 下**只放了一个占位 pack `packs/garage/`**（含 1 sample skill `garage-hello` + 1 sample agent `garage-sample-agent`），用来验证管道端到端能跑通。

这意味着今天用户场景的实际表现是：

```
用户在自己项目：
  cd ~/projects/my-app
  garage init --hosts claude

实际效果：
  .claude/skills/garage-hello/SKILL.md    ← 1 个 toy skill
  .garage/config/host-installer.json
```

——`docs/soul/manifesto.md` 承诺的 "几秒后 Agent 就变成你的 Agent，能调用你积累的 50 个 skills" 在交付路径上**仍是空头支票**。manifesto 承诺与实际 `garage init` 输出之间的最大缺口不在管道（F007 已闭合），而在 packs 内容物。

仓库里其实已经存在 28 个高质量 SKILL.md（实测：`find .agents/skills -maxdepth 4 -name SKILL.md | wc -l` = 28），但全部位于 `.agents/skills/` 下：

| 子目录 | SKILL.md 数 | 主题 |
|---|---|---|
| `.agents/skills/harness-flow/skills/hf-*` | 21 个 hf-*（实测：`ls .agents/skills/harness-flow/skills/ \| grep -c '^hf-'` = 21） | 工程工作流（spec / design / tasks / TDD / 各类 review / 各类 gate / hotfix / increment / finalize / discovery） |
| `.agents/skills/harness-flow/skills/using-hf-workflow/` | **1** | HF family public entry |
| `.agents/skills/harness-flow/skills/docs/` | 0（4 个共享 docs：command-entrypoints / workflow-entrypoints / workflow-shared-conventions / worktree-isolation） | HF family 共享 references |
| `.agents/skills/harness-flow/skills/templates/` | 0（5 个 templates：finalize-closeout-pack / review-record / task-board / task-progress / verification-record） | HF family 共享 templates |
| `.agents/skills/harness-flow/docs/principles/` | 0（2 个 principles：hf-sdd-tdd-skill-design / skill-anatomy） | family-level 设计原则 |
| `.agents/skills/write-blog/{blog-writing,humanizer-zh,hv-analysis,khazix-writer}` | **4** | 内容创作（个人博客、AI 痕迹去除、横纵分析法、卡兹克公众号风格） |
| `.agents/skills/find-skills/` | **1** | 帮用户发现并安装新 skill 的元 skill |
| `.agents/skills/writing-skills/` | **1**（含 anthropic-best-practices / persuasion-principles / testing-skills-with-subagents 三份 reference + 1 个 graphviz 渲染脚本） | 写新 skill 时的 SOP |

合计 **28 个 source SKILL.md**（21 hf-* + 1 using-hf-workflow + 4 write-blog + 1 find-skills + 1 writing-skills），加 F007 已在 `packs/garage/` 落下的 `garage-hello`，本 cycle 落地后总 packs SKILL.md 数 = **29**。

更具体的真实摩擦：

1. **manifesto / packs / `.agents/skills/` 三方割裂**：今天 `packs/README.md` 自己就说 "F008 候选会把 `.agents/skills/` 下 30 个 HF skills 搬到 `packs/coding/skills/`"——这条 future tense 在 F007 closeout 时是合理的延期，在 F008 启动时必须收敛。`docs/soul/growth-strategy.md` Stage 3 触发信号写明 "Skills > 30"，本 cycle 不实现就永远卡在 Stage 1。
2. **HF family 的 4 个共享 docs + 5 个 templates 不是 skill 但被 skill 引用**：当前 `.agents/skills/harness-flow/skills/docs/hf-workflow-shared-conventions.md` 被多个 hf-* SKILL.md 用相对路径引用（如 `references/.../shared-conventions.md`）。任何搬迁方案必须在 `packs/<pack-id>/` 层级保留这种**家族内引用关系**，否则搬完 skill 在下游宿主里点击引用就 404。F007 spec § 11 开放问题 4 已留口子 "是否在 `packs/<pack-id>/` 下区分 `coding` / `product-insights` 子 pack——design 阶段决定"，本 cycle 必须收敛。
3. **写作系 vs 工程系是两类用户场景**：write-blog 4 个 skill 服务于"写公众号 / 写博客 / 写研究报告"场景，与 hf-* 工程 workflow 的目标用户、调用频率、依赖关系完全正交。装到一个 `packs/coding/` 之下是反语义。F008 必须把它们拆成独立的 `packs/writing/`。
4. **find-skills + writing-skills 是 family-level meta-skill**：它们既不属于 coding 也不属于 writing，而是 "怎么用 / 怎么扩展 packs 体系" 这个元层。`find-skills` 帮用户发现新 skill，`writing-skills` 帮用户写新 skill，二者在 `packs/garage/` 下作为 "getting started" 入口最合适——可以与 F007 落下的 `garage-hello` 比邻。
5. **F007 安装管道已铺好但未被真正吃满**：F007 已实现 (a) 同名 skill 跨 pack 冲突检测（退出码 2）、(b) extend mode + content_hash 幂等、(c) `installed_pack` 字段记录归属、(d) 三家宿主 adapter。如果搬迁不发生，这些能力都被 1 个 `garage-hello` 占用——投资回报率为零。
6. **`AGENTS.md` § "Skill 写作原则" 引用的 `docs/principles/skill-anatomy.md` 在仓库根**实际存在**（16707 字节），**且已与** `.agents/skills/harness-flow/docs/principles/skill-anatomy.md`（16637 字节）**发生内容 drift**（实测 `diff` 显示根级用 `AHE` / `packs/coding/skills/docs/` 等术语，HF family 副本用 `HF` / `skills/docs/` 术语，源自项目早期 AHE → HF rename 未同步）。F008 必须显式收敛这个**双副本 + drift** 问题：哪一份是规范源、另一份是删除还是反向同步、是否把根级改为 `packs/coding/principles/skill-anatomy.md` 的软链。这是独立于 § 5 `.agents/skills/` 处置的另一项处置决策，design 必须给出明确 ADR；F008 落地后**不允许** drift 的两份副本同时存在。

## 2. 目标与成功标准

### 2.1 核心目标

把 `.agents/skills/` 下 28 个 source SKILL.md 目录 + 4 个 family 共享 docs + 5 个 templates + 2 个 family principles 按主题归并到 `packs/<pack-id>/` 下三个一级 pack：

```
packs/
├── garage/      (F007 已存在，本 cycle 在其下追加 find-skills + writing-skills 两个 meta-skill)
├── coding/      (F008 新增) — HF workflow family
│   ├── pack.json
│   ├── README.md
│   ├── skills/  (21 hf-* + using-hf-workflow = 22 项)
│   ├── docs/    (4 个 shared docs，沿用 F007 spec § 11 开放问题 4 收敛后的 family-level 共享路径)
│   ├── templates/ (5 个 HF family templates)
│   └── principles/ (2 个 family principles：skill-anatomy.md / hf-sdd-tdd-skill-design.md)
└── writing/     (F008 新增) — 内容创作 family
    ├── pack.json
    ├── README.md
    └── skills/  (4 个 write-blog skill)
```

让下游用户单条命令：

```bash
garage init --hosts claude
```

后，`.claude/skills/` 下立即出现 21 hf-* + using-hf-workflow + 4 write-blog + find-skills + writing-skills + garage-hello = **29 个真实可用 SKILL.md**（含 F007 落下的 `garage-hello`），每个文件 front matter 含 `installed_by: garage` + `installed_pack: <coding|writing|garage>`，让 6 个月后回看的用户能一眼分辨"哪些是 Garage 装的"。验收侧不锁死字面 `29`，而是约束 `Installed N skills` 的 `N` 必须等于 3 个 `pack.json.skills[]` 长度之和（详见 FR-806 与 § 6 验收 #1）。

本 cycle 收敛：
- 把 28 个 source SKILL.md 目录从 `.agents/skills/` 物化到 `packs/{coding,writing,garage}/skills/<id>/SKILL.md`
- 在 `packs/coding/` 内沉淀 4 个 shared docs + 5 个 templates + 2 个 principles 这 11 个 family-level 资产，使其在下游宿主的 skill 加载路径下可被 hf-* skill 用相对路径引用
- 处理 `.agents/skills/` 与 `packs/` 在搬迁后的关系（保留软链 / 完全删除 / 作为 dev-only mirror）
- 处理 `docs/principles/skill-anatomy.md` 与 `.agents/skills/harness-flow/docs/principles/skill-anatomy.md` 的双副本 drift（设计阶段决定是去 root 留 `packs/coding/principles/` + AGENTS.md 路径同步、还是保留 root 入口 + family 内部不再保留私副本）
- 三个 pack 各自的 `pack.json` (`schema_version=1` 沿用 F007) + `README.md`
- 跑一次 `garage init --hosts all` 端到端验证，并在 `RELEASE_NOTES.md` 归档证据

**显式不在本 cycle**（详见 § 5）：
- 不新增任何 host（仍为 F007 既定 claude / opencode / cursor）
- 不修改 F007 安装管道、conflict 检测、extend mode、manifest schema
- 不引入 `~/.claude/` 全局安装
- 不实现 `garage uninstall` / `garage update`
- 不改写既有 skill 内容（搬迁是字节级 1:1 + 必要的相对引用路径修复，不重写 SKILL 业务逻辑）
- 不新增 `packs/product-insights/`（无现成 skill 内容物，等真实 product discovery skill 沉淀后再开 cycle）

### 2.2 成功标准

1. **承诺兑现可演示**：在干净的下游项目（`mkdir /tmp/f008-smoke && cd /tmp/f008-smoke && git init`）执行 `garage init --hosts all`，stdout 必须出现 `Installed N skills, M agents into hosts: claude, cursor, opencode` 形式 marker，其中 `N == sum(pack.json.skills[] 长度 for pack in [garage,coding,writing])`、`M == sum(pack.json.agents[] 长度 for pack in [garage,coding,writing])`（按本 spec § 4 收敛后的预期值，N≈29 / M∈{0,1}，但 acceptance 不锁字面值，由 manifest 派生）；三家宿主目录下 `*/skills/` 子目录数合计 == `N × 3`，退出码 0。
2. **family-level docs / templates / principles 可被引用**：`packs/coding/skills/hf-specify/SKILL.md` 内任何 `references/spec-template.md` 形式相对引用，在被装到 `.claude/skills/hf-specify/` 后必须仍能 resolve 到磁盘存在的目标文件；具体路径模式（`packs/coding/docs/...` 或同级 `references/`）由 design 决定，本 spec 只约束"装完后引用不 404"。同时 design 选定的方案必须满足 **family-level 资产去重不变量**：同一 family-level 文件在仓库内不允许出现 ≥2 份磁盘副本（除非 design 明确以"内部不变 + lint 守门"形式 ADR 出例外，否则视为 design-review 阻塞）。
3. **三个 pack 自描述完整**：`packs/{garage,coding,writing}/pack.json` 三个 manifest 的 `skills[]` 字段加和必须 == 装到任一宿主的 `*/skills/` 子目录数（即 § 2.2 #1 的 `N`，按本 spec 收敛后的预期值约 29，含 F007 已有 `garage-hello`）；任何 Agent 仅读 3 个 pack.json 必须能回答 "本仓库一共能装多少 skill / 哪些 skill / 各属哪个 pack" 三个问题。
4. **F007 NFR-701 (宿主无关性) 仍守住**：`grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/` 的命中数 ≤ F007 baseline（F007 已是 0）；本 cycle 搬迁动作不得引入新的宿主特定字面值。
5. **F007 安装管道零退绿**：`uv run pytest tests/adapter/installer/` 在搬迁完成后必须仍 100% 通过；只允许新增 "全 packs 在三家宿主下都能被装" 的 smoke 用例（覆盖 FR-806），不允许改写既有 conflict / extend / manifest 测试。
6. **既有 F001-F007 测试基线零回归**：`uv run pytest tests/ -q` 整体计数 ≥ F007 基线 586，旧用例 0 退绿。
7. **`.agents/skills/` 物理状态明确无歧义**：本 cycle 必须在 § 4 给出收敛结论——是 (a) 删除整个 `.agents/skills/`、改为 git symlink 或 sparse-checkout 指回 packs；(b) 保留 `.agents/skills/` 作为本仓库自身 IDE 加载入口、与 `packs/` 双副本（用 lint 约束二者字节相等）；(c) 改 `.agents/skills/` 为 `packs/` 的软链入口。在 review 通过前不得在 prose 里说"以后定"。设计选定方案后必须满足 **`.agents/skills/` 处置不变量**：cycle 落地后 `git status` 干净（无 untracked / modified 残留）、不存在 dead 文件、不存在 mtime drift 的双副本（与 § 2.2 #2 family asset 去重不变量同精神）。
8. **5 分钟冷读链不破**：`AGENTS.md` 与 `packs/README.md` 的入口指针在搬迁后仍指向真实存在的文件；`AGENTS.md § "Skill 写作原则"` 引用的 `docs/principles/skill-anatomy.md` 必须有真实物理位置（沿用 § 4 收敛结论），且不再与任何其它副本 drift。
9. **同名 skill 跨 pack 冲突保护被实战验证**：跑一次故意冲突的搬迁（例如把 `find-skills` 同时放到 `packs/garage/` 和 `packs/coding/`，仅作冒烟）→ `garage init --hosts claude` 必须如 F007 FR-704 #4 承诺退出码 2 + stderr 列出冲突，证明 F007 投资在 F008 内容物上仍生效；冒烟后回滚冲突布置。

### 2.3 非目标

- 不修改任何 SKILL.md 的业务逻辑（front matter `name` / `description` 字段、Workflow 章节、Verification 章节都按字节复制；唯一允许的变化是相对引用路径——见 § 4 § 9）。
- 不重新设计 HF skill 之间的依赖图、调用链或工作流转移表。
- 不为 packs 引入跨仓库依赖、版本管理、lockfile 升级语义（这是 deferred backlog）。
- 不改 `garage init` 命令面或退出码语义。
- 不为 `packs/coding/` 增加新的 hf-* skill 或 review 节点。
- 不替 write-blog 4 个 skill 添加 humanizer-zh 之外的语种变体。
- 不实现 `find-skills` / `writing-skills` 两个 meta-skill 的功能升级——只是把它们物理地搬到 `packs/garage/`。

## 3. 用户角色与关键场景

### 3.1 用户角色

- **下游 Solo Creator**：在自己项目执行 `garage init --hosts claude` 后期望立刻得到 HF workflow + write-blog 完整能力，不需要去 GitHub 翻 Garage 仓库手工拷文件。
- **CI / Cloud Agent 调用方**：在 cloud agent VM 启动脚本里 `garage init --hosts all --yes`，期望得到完整 packs 装好的环境（按本 cycle 落地后约 29 个 skill；具体数由 manifest 派生）。
- **Garage 仓库自身（dogfooding）**：本仓库自己用 `.agents/skills/` 加载 skill。F008 搬迁后，本仓库的 IDE / Cursor / Claude Code 必须仍能加载到这 28 个 source SKILL.md 对应的 skill（具体机制由 § 4 收敛）。
- **Pack 作者 / 维护者**：6 个月后想给 `packs/coding/` 加一个新 hf-* skill 的人，期望流程是 "在 `packs/coding/skills/<new-id>/` 写 SKILL.md → 改 `pack.json.skills[]` → 跑 grep 守门测试 → push"，不需要再改 `.agents/skills/`。
- **Garage 审计读者**：`git diff` 看 PR 时，期望搬迁动作集中在 `packs/{coding,writing}/` 新增 + `.agents/skills/` 的处置（删除 / 保留 / 软链），不掺杂安装管道改动。

### 3.2 关键场景

1. **下游首装（happy path）**：
   ```bash
   cd ~/projects/my-app && git init
   garage init --hosts claude
   # stdout: Installed N skills, M agents into hosts: claude   (N == sum(pack.json.skills[]); 预期 ≈ 29)
   ls .claude/skills/ | wc -l   # → N
   cat .claude/skills/hf-specify/SKILL.md | head -5
   # → 含 installed_by: garage, installed_pack: coding
   ```

2. **多宿主全装（验收 #1）**：
   ```bash
   garage init --hosts all
   # stdout: Installed N skills, M agents into hosts: claude, cursor, opencode   (N 同上)
   for h in claude cursor opencode; do echo "$h: $(ls .$h/skills/ | wc -l)"; done
   # claude: N / cursor: N / opencode: N
   ```

3. **family 内引用**：装完 `.claude/skills/hf-specify/SKILL.md` 后，用户/Agent 在 Claude Code 里加载该 skill，skill 内 `references/spec-template.md` 形式的引用必须能定位到磁盘真实文件（具体路径由 § 4 决定）。

4. **`garage` pack getting-started 入口**：
   ```bash
   garage init --hosts claude
   ls .claude/skills/garage-hello/      # F007 落下的占位 sample
   ls .claude/skills/find-skills/        # F008 搬来的发现 meta-skill
   ls .claude/skills/writing-skills/     # F008 搬来的写 skill 的 meta-skill
   # 三者构成 "新用户第一次接触 Garage" 的入口三件套
   ```

5. **冲突保护实战**（验收 #9，仅冒烟，不持久化）：
   ```bash
   cp -r packs/garage/skills/garage-hello packs/coding/skills/garage-hello   # 故意冲突
   garage init --hosts claude
   # exit code 2, stderr: Conflicting skill 'garage-hello' in packs garage and coding
   rm -rf packs/coding/skills/garage-hello                                     # 冒烟回滚
   ```

6. **再次运行幂等**：执行场景 1 之后再跑一次 `garage init --hosts claude`，行为应符合 F007 FR-706a（未修改的 29 个文件 mtime 不刷新）；F008 不引入新的幂等行为。

7. **Garage 自身 dogfood**：在 Garage 仓库本身执行 `garage init --hosts cursor`，`.cursor/skills/` 下出现包括 `hf-specify` 在内的 N 个 skill（按本 cycle 落地后约 29）；本仓库自身 IDE 加载 skill 的来源不被破坏（`.agents/skills/` 处置由 § 4 决定）。

## 4. 当前轮范围与关键边界

### 4.1 包含

| 能力 | 描述 |
|------|------|
| `packs/coding/` 新增 | `pack.json` (`schema_version=1`, `pack_id="coding"`, `version="0.1.0"`, `description`, `skills[22]`, `agents[]`)、`README.md`（pack 概述 + 22 skill 清单）、`skills/<id>/SKILL.md`（21 hf-* + using-hf-workflow = **22 项**，每个含 evals/ references/ 等子目录原样照搬） |
| `packs/coding/` family-level 共享资产 | 4 个 shared docs（`hf-command-entrypoints` / `hf-workflow-entrypoints` / `hf-workflow-shared-conventions` / `hf-worktree-isolation`）+ 5 个 templates（`finalize-closeout-pack` / `review-record` / `task-board` / `task-progress` / `verification-record`）+ 2 个 principles（`skill-anatomy` / `hf-sdd-tdd-skill-design`）共 11 个 family-level 资产，落在 design 阶段决定的 family-level 路径下（候选 A：`packs/coding/{docs,templates,principles}/`；候选 B：复制到每个 hf-* skill 的 `references/` 子目录；候选 C：留在 `packs/coding/skills/_shared/`） |
| `packs/writing/` 新增 | `pack.json` (`schema_version=1`, `pack_id="writing"`, `version="0.1.0"`, `description`, `skills[4]`, `agents[]`)、`README.md`（pack 概述 + 4 skill 清单 + 与卡兹克 humanizer 协作示例）、`skills/<id>/SKILL.md`（blog-writing / humanizer-zh / hv-analysis / khazix-writer，每个含 prompts/ examples/ 等子目录原样照搬） |
| `packs/garage/` 扩展 | 在 F007 落下的 1 sample skill 基础上追加 `find-skills` 与 `writing-skills` 两个 meta-skill；`pack.json.skills[]` 从 `["garage-hello"]` 扩到稳定排序的 `["find-skills", "garage-hello", "writing-skills"]`（顺序由 design 决定但必须确定性）；`README.md` 同步刷新 |
| `.agents/skills/` 处置收敛 | 在 design 阶段从 § 5 列出的三个候选（A 删除 + git symlink 回 packs / B 双副本 + lint 守门 / C 删除并仅在 IDE 配置里指向 packs）选定一个并实施；本 spec 不预设答案，但 spec 必须把 "选定后能保证本仓库自身 IDE 加载链不破" 写进验收 |
| `docs/principles/skill-anatomy.md` drift 收敛 | cycle 落地后**必须只剩一份规范副本**，不允许 drift 的两份并存（详见 § 1 #6 + FR-804 验收 #4） |
| 文档 | 三个 pack 各自 `README.md` + `packs/README.md` "当前 packs" 表更新 + `AGENTS.md "Skills 入口指针" 段刷新（如有）+ `docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段补一句 "目前 garage init 默认装 N skill"（N 由 manifest 派生）+ `RELEASE_NOTES.md` 新增 F008 段 |
| smoke 验证 | 在 `/tmp/f008-smoke/` 跑 `garage init --hosts all` 端到端，把 stdout/stderr 与三家宿主目录 ls 输出归档为 walkthrough artifact |
| design reviewer 判定边界（spec 层 anchor） | 把 § 4.2 "design 决定" 部分给 design-review 提供可拒标准（详见 § 4.2 末尾 "Design Reviewer 可拒红线" 列表），让 design 阶段 ADR 不会因为缺判定边界就反弹回 spec |

### 4.2 关键边界

- **搬迁是字节级 1:1**（除相对引用路径修复）：`SKILL.md` 主体、`evals/`、`references/`、`scripts/`、`assets/`、`prompts/`、`examples/` 等子目录全部按 `cp -R` 等价语义搬，不允许借机修改 skill 业务逻辑。所有 SKILL.md 修改必须可在 `git diff` 里被审计为 "仅 path / 引用相关"。
- **`packs/garage/` 已落版本 = `0.1.0`**（F007 cycle 写入），本 cycle 把内容物从 1 → 3 是非破坏性扩容，沿用 `0.1.0` 还是 bump 到 `0.2.0` 由 design 决定；`pack.json.schema_version` 始终为 1（受 F007 CON-703 + VersionManager 管控）。
- **`packs/coding/` family-level 共享资产路径在 spec 不固定**，但本 spec 强约束："任一 hf-* skill 在任一宿主下被加载后，其内对 4 docs / 5 templates / 2 principles 的引用必须能 resolve 到磁盘存在的真实文件"——这是验收 #2 与场景 3 的硬门槛。
- **`.agents/skills/` 处置必须本 cycle 收敛**（不允许 prose 里写 "以后再决定"），但具体方案（A/B/C）落到 design。spec 验收要求："收敛方案选定后，本仓库 IDE 与 Cursor 加载 hf-* skill 的入口仍可用"。
- **不动 F007 安装管道任何代码**：`src/garage_os/adapter/installer/` 子包 11 个源文件 0 修改；如果搬迁过程中发现管道有 bug（例如对 `references/` 子目录递归不够深），先用 `hf-hotfix` 单独 cycle 处理，不能放进 F008。
- **不动 F001-F006 任何模块**：types / storage / runtime / knowledge / tools / platform 全部零修改。
- **不修改 host adapter 注册表**：`HOST_REGISTRY` 仍是 claude / opencode / cursor 三项；新增宿主属于 F008+ 候选。
- **`pack.json` schema 不变**：仍是 F007 落下的 6 字段（schema_version / pack_id / version / description / skills[] / agents[]）。本 cycle 不引入 `dependencies[]` / `tags[]` / `family[]` 等新字段（这些是 Stage 3 候选）。
- **F007 占位 `garage-sample-agent` 处置**：保留还是删除由 design 决定（保留可证明 agent surface 仍工作；删除让 `packs/garage/` 三件套更对称）；spec 不强制。

#### Design Reviewer 可拒红线（spec 给 design-review 的最低判定边界）

为防止 design 阶段 ADR 因为缺 acceptance 反弹回 spec，本 spec 显式给 `hf-design-review` 列出 design 收敛的可拒红线。任一命中以下任一项，design-review 应直接 `阻塞`：

1. **Family-level 资产去重不变量违反**：design 选定的方案让同一 family-level 文件（4 docs / 5 templates / 2 principles 中任一）在仓库 `packs/` 内出现 ≥2 份磁盘副本（含软链以外的实拷贝），且 ADR 未显式声明这是有意为之 + 给出 lint 守门方案。例：candidate B "复制到每个 hf-* skill 的 `references/`" 会产生 22 × 4 = 88 份冗余 docs 副本，必须有明确去重策略才能采纳。
2. **`.agents/skills/` 处置后仓库 git 状态不干净**：cycle 落地后存在 untracked 文件、modified 残留、dead 软链、或 `.agents/skills/` 下与 `packs/` 内容字节级 drift 的双副本。例：candidate B "双副本 + lint 守门" 必须显式给出 lint 实施路径（pre-commit hook / CI 检查 / pytest 用例 三选一），不允许只声明 "lint 已加" 而无实现位置。
3. **`docs/principles/skill-anatomy.md` 双副本 drift 未收敛**：cycle 落地后 `diff /workspace/docs/principles/skill-anatomy.md /workspace/<F008 选定的 family-level 副本路径>` 仍显示内容差异。
4. **`AGENTS.md` 5 分钟冷读链断裂**：`AGENTS.md § "Skill 写作原则"` 提到的 `docs/principles/skill-anatomy.md` 路径在 cycle 落地后定位不到磁盘真实文件（无论是 git 软链、目录复制还是路径同步任一方式）。
5. **本仓库自身 IDE 加载链断裂**：cycle 落地后，本仓库 Cursor / Claude Code 加载 `hf-specify` skill 的入口完全失效（`find` 输出 / 启动日志 / 显式截图 任一证据缺失）。
6. **F007 安装管道被动到**：`git diff main..HEAD -- src/garage_os/` 非空（除了搬迁过程中发现 F007 bug 的 `hf-hotfix` 单独 cycle 已合并）。

满足以上红线的 design 草稿，design-review 应判 `阻塞`，回 `hf-design` 修订；不满足任一红线 + 满足 spec 其它 acceptance → 可判 `通过`。

### 4.3 与 F001-F007 的边界

| 既有契约 | F008 影响 |
|---------|----------|
| `packs/<pack-id>/` 目录契约（F007 FR-701） | **零修改**，本 cycle 仅在该契约下增加 2 个一级 pack |
| `garage init --hosts ...` CLI 接口（F007 FR-702/703） | **零修改** |
| 安装管道 `src/garage_os/adapter/installer/`（F007 FR-704） | **零修改** |
| 安装清单 `.garage/config/host-installer.json` schema（F007 FR-705 / CON-703） | **零修改**，仅 manifest 内 `installed_packs[]` 与 `files[]` 两个数组的实际内容变多 |
| Extend mode + content_hash 幂等（F007 FR-706a/706b） | **零修改** |
| Host adapter 注册表（F007 FR-707） | **零修改** |
| 安装标记块 / front matter `installed_by/installed_pack`（F007 FR-708） | **零修改** |
| 退出码 / stdout marker（F007 FR-709） | **零修改** |
| 同名 skill 跨 pack 冲突检测（F007 FR-704 #4） | **零修改**；本 cycle 在验收 #9 实战触发一次后回滚，作为冒烟证据 |
| `KnowledgeStore` / `ExperienceIndex` / `SessionManager` / `HostAdapterProtocol`（F001-F006） | **零修改** |

## 5. 范围外内容（显式 deferred backlog）

下列项真实存在且会发生，但**显式不在 F008**：

| 项 | 为什么本 cycle 不做 | 期望落点 |
|----|--------------------|----------|
| `garage uninstall --hosts <list>` | F007 cycle 已显式 deferred；与 F008 是正交工作；先把 packs 内容物搬完 | F009 候选 |
| `garage update --hosts <list>` | 同上；packs 内容稳定后再开 update 拉新流程 | F009 候选 |
| 全局安装到 `~/.claude/skills/...` | OpenSpec issue #752 模式；与 workspace-first 信念有 trade-off，需独立 spec | 单独候选 |
| 新增宿主（Codex / Gemini CLI / Windsurf / Copilot 等） | F007 已确立 first-class adapter 注册模式；新增宿主成本 = 1 adapter 子模块 + `HOST_REGISTRY` 1 行；可独立小 cycle | F008+ 增量 |
| `packs/product-insights/` 新增 | F001 CON-002 提及但仓库当前**无任何 product discovery skill 内容物**；造空 pack 价值为零 | 待真实 product discovery skill 沉淀后开 cycle |
| 改写任意 SKILL.md 业务逻辑 | 搬迁 cycle 严禁混入业务变更；review surface 会爆炸 | 各 skill 单独维护 cycle |
| 给 `packs/coding/` family 加新 hf-* skill | 不是搬迁，是新增；走独立 cycle | 单独候选 |
| `pack.json` 新字段（`dependencies` / `tags` / `family` / `min_garage_version`） | F007 schema 稳定刚落，过早扩展会破坏 5 分钟冷读 | Stage 3 候选 |
| `find-skills` 真正实现 "从远程 registry 发现 skill" | 当前 `find-skills/SKILL.md` 是 SOP 文本，无网络 / 无 registry 语义；扩成功能性需要单独 spec | 单独候选 |
| 让 `writing-skills` 的 `render-graphs.js` 在装到下游后能直接执行 | 需要 design Node 依赖管理；与 packs schema-only 原则冲突 | 单独候选 |
| 多语言 / i18n 版本（write-blog 仅中文） | write-blog skill 本身就以中文场景为主；英文化是独立工作 | 单独候选 |
| 反向同步：用户在 `.claude/skills/` 改了之后回流到 `packs/` | F007 已显式 deferred，本 cycle 不动 | 单独候选 |

## 6. 功能需求

### FR-801 `packs/coding/` 落盘

- **优先级**: Must
- **来源**: § 1.1 `F001 CON-002` 未兑现约束 + `RELEASE_NOTES.md` "F007 — 已知限制" 第 1 条 "F008 候选 — 把 .agents/skills/ 30 个 HF skills 搬到 packs/coding/skills/"
- **需求陈述**: 系统必须在仓库 `packs/coding/` 下提供完整 HF workflow family pack，至少含 `pack.json`、`README.md`、`skills/<id>/SKILL.md` 形式的 21 个 hf-* skill + 1 个 `using-hf-workflow` skill（共 **22 项**），且每个 skill 子目录的 `evals/` / `references/` / `scripts/` / `assets/` 等附属内容按 1:1 字节级搬迁。
- **验收标准**:
  - Given F008 实施完成，When 任意 Agent 读取 `packs/coding/pack.json`，Then `pack_id == "coding"` 且 `skills[]` 长度 == 22，且 `skills[]` 每一项都对应 `packs/coding/skills/<id>/SKILL.md` 真实存在。
  - Given `ls .agents/skills/harness-flow/skills/ | grep -c '^hf-'` == 21（实测基线）+ `using-hf-workflow` 1 项，When `packs/coding/skills/` 落盘，Then 子目录数 == 22 且与上面源集合按 id 一一对应。
  - Given 某个 hf-* skill 在 `.agents/skills/harness-flow/skills/<id>/` 下有 `references/<file>.md`，When 同名内容被搬到 `packs/coding/skills/<id>/references/<file>.md`，Then 二者按 SHA-256 字节级相等。
  - Given `packs/coding/skills/<id>/SKILL.md` 的 front matter，When 解析 `name` 与 `description` 字段，Then 与 `.agents/skills/harness-flow/skills/<id>/SKILL.md` 同字段字节级相等（搬迁不修改业务字段）。

### FR-802 `packs/writing/` 落盘

- **优先级**: Must
- **来源**: § 1 现状摩擦 #3 "写作系 vs 工程系是两类用户场景" + § 2.1 核心目标
- **需求陈述**: 系统必须在仓库 `packs/writing/` 下提供完整内容创作 family pack，至少含 `pack.json`、`README.md`、`skills/<id>/SKILL.md` 形式的 4 个 write-blog 子 skill（`blog-writing` / `humanizer-zh` / `hv-analysis` / `khazix-writer`），且每个 skill 子目录的 `prompts/` / `examples/` 等附属内容按 1:1 字节级搬迁。
- **验收标准**:
  - Given F008 实施完成，When 任意 Agent 读取 `packs/writing/pack.json`，Then `pack_id == "writing"` 且 `skills[]` 长度 = 4，且每一项对应 `packs/writing/skills/<id>/SKILL.md` 真实存在。
  - Given write-blog 原 LICENSE 文件 `.agents/skills/write-blog/LICENSE`，When 检查 `packs/writing/`，Then 该 LICENSE 必须以可发现方式存在（落 `packs/writing/LICENSE` 或在 `packs/writing/README.md` 内显式声明 license 与上游来源），不允许丢失上游版权信息。
  - Given `packs/writing/skills/khazix-writer/SKILL.md` 的 description 字段，When 与原文件对比，Then 字节级相等（搬迁不删减原作者意图）。

### FR-803 `packs/garage/` 扩容到 3 skill

- **优先级**: Must
- **来源**: § 1 现状摩擦 #4 "find-skills + writing-skills 是 family-level meta-skill"；放在 `packs/garage/` 与 F007 落下的 `garage-hello` 比邻最合适
- **需求陈述**: 系统必须把 `find-skills` 与 `writing-skills` 两个 meta-skill 落到 `packs/garage/skills/<id>/SKILL.md`，并把 `packs/garage/pack.json.skills[]` 从 `["garage-hello"]` 扩到稳定排序的三元素数组（默认假设 `["find-skills", "garage-hello", "writing-skills"]` 字典序，最终顺序由 design 决定，但必须确定性）。
- **验收标准**:
  - Given F008 实施完成，When 任意 Agent 读取 `packs/garage/pack.json`，Then `skills[]` 长度 == 3 且按集合等价于 {`garage-hello`, `find-skills`, `writing-skills`}。
  - Given 任意一次 `garage init --hosts claude` 成功，When 检查 `.claude/skills/`，Then 三个 skill 子目录全部存在。
  - Given `writing-skills` 子目录在 `.agents/skills/writing-skills/` 下有 `examples/` / `render-graphs.js` / `*.md` references，When 落到 `packs/garage/skills/writing-skills/`，Then 全部按 1:1 搬迁（render-graphs.js 不可执行不在本 cycle 处理，是 deferred）。

### FR-804 family-level 共享资产可解析

- **优先级**: Must
- **来源**: § 1 现状摩擦 #2 "HF family 4 个共享 docs + 5 个 templates 不是 skill 但被 skill 引用" + § 2.2 验收 #2
- **需求陈述**: 系统必须为 4 个 HF shared docs（command-entrypoints / workflow-entrypoints / workflow-shared-conventions / worktree-isolation）+ 5 个 HF templates（finalize-closeout-pack / review-record / task-board / task-progress / verification-record）+ 2 个 HF principles（skill-anatomy / hf-sdd-tdd-skill-design）共 11 个 family-level 资产选定一个稳定的物理位置，且在该位置下被 22 个 packs/coding/skills/* SKILL.md 内任意相对引用必须能 resolve。
- **验收标准**:
  - Given F008 实施完成 + 任意一次 `garage init --hosts claude` 成功，When 任意 hf-* SKILL.md 内含 `references/spec-template.md` / `skills/docs/hf-workflow-shared-conventions.md` / `templates/task-progress-template.md` 等形式相对引用，Then 该相对路径在 `.claude/skills/` 加载入口下必须能 resolve 到磁盘存在的真实文件（具体路径由 design 决定）。
  - Given 任一 family-level 资产，When 用 SHA-256 比较其落盘内容与 `.agents/skills/harness-flow/skills/docs/<file>` 或 `.agents/skills/harness-flow/skills/templates/<file>` 或 `.agents/skills/harness-flow/docs/principles/<file>` 同名文件，Then 字节级相等。
  - Given `AGENTS.md § "Skill 写作原则"` 引用的 `docs/principles/skill-anatomy.md`，When 任意 Agent 顺路径打开，Then 必须能定位到 F008 选定的物理位置（要么 `AGENTS.md` 路径同步更新，要么在仓库根 `docs/principles/skill-anatomy.md` 用 git 软链/复制保留入口）。
  - **去重不变量（与 § 4.2 "Design Reviewer 可拒红线" 第 1 条同精神）**: Given F008 落地后，When 对 11 个 family-level 资产任一个 `<file>` 跑 `find packs/ -name '<file>' -type f | wc -l`，Then 计数 ≤ 1（design 显式 ADR 例外 + lint 守门方案的情况下可豁免，但任一例外必须在 design 文档显式 anchor）。
  - **drift 收敛不变量**: Given F008 落地后，When 对 `docs/principles/skill-anatomy.md` 与 `packs/coding/principles/skill-anatomy.md`（或 design 选定的 family-level 等价路径）跑 `diff`，Then 输出为空（两者要么是同文件 / 同软链 / 字节级相等的 git 受控副本）。

### FR-805 `.agents/skills/` 与 `packs/` 关系收敛

- **优先级**: Must
- **来源**: § 1 现状摩擦 #5 "F007 投资回报率为零" + § 2.2 验收 #7 + § 2.1 核心目标 "处理 .agents/skills/ 与 packs 在搬迁后的关系"
- **需求陈述**: 系统必须在本 cycle 显式收敛 `.agents/skills/` 在 F008 后的物理状态，候选方案至少包括 (A) 删除整个 `.agents/skills/`、改用 git symlink 指回 `packs/`；(B) 保留 `.agents/skills/` 与 `packs/` 双副本并加 lint 检查保证字节相等；(C) 删除 `.agents/skills/`、本仓库自身 IDE 加载链改为指向 `packs/<pack-id>/skills/`；具体方案由 design 决定，但本 cycle 必须实施一种且对应工程改动落 PR。
- **验收标准**:
  - Given design 选定方案 X，When F008 实施完成，Then `.agents/skills/` 的物理状态严格符合方案 X 描述（无歧义、无遗留 dead 文件）。
  - Given 本仓库自身在 Cursor / Claude Code 中加载 hf-* skill 的入口路径，When 走选定方案 X 后的物理 layout，Then 至少 1 个 hf-* skill（推荐 `hf-specify`）能被本仓库 IDE 成功加载（**验证方式必须可在 PR walkthrough 中重放**：可以是 manual 截图 / `find` 输出 / IDE 日志 / cursor MCP 调用，但不允许只在 design ADR 内声明而 PR 无可重放证据）。
  - Given 选定方案 A 或 C（涉及删除 `.agents/skills/`），When 检查 git history，Then `.agents/skills/` 删除必须发生在与 packs 落盘**同一 PR / commit chain** 内，不允许中间状态出现 "本仓库 IDE 加载链断裂" 的窗口。
  - **git status 干净不变量**: Given F008 PR 合并后任一 commit，When `git status --porcelain` 在干净 checkout 上跑，Then 输出为空（无 untracked / modified / deleted 残留）；若选定方案 B 双副本，When 对任一 `.agents/skills/.../<file>` 与 `packs/.../<file>` 同名对跑 SHA-256，Then 字节级相等（lint 守门必须实施，例如 pre-commit hook / CI 检查 / pytest 用例 三选一，design ADR 必须明确选定其一）。

### FR-806 端到端 smoke 与 walkthrough 证据

- **优先级**: Must
- **来源**: § 2.2 验收 #1 + 项目级"manual testing 优先"约定（系统提示 § Testing）
- **需求陈述**: 系统必须随本 cycle 提供至少一份端到端 smoke 证据：在干净下游目录执行 `garage init --hosts all`，归档 stdout / stderr / 三家宿主目录 `ls` 输出 + `host-installer.json` 截取，作为 PR walkthrough artifact。
- **验收标准**:
  - Given `mkdir /tmp/f008-smoke && cd /tmp/f008-smoke && git init`，When 执行 `garage init --hosts all`，Then 退出码 0 + stdout 含 `Installed N skills, M agents` 形式 marker（`N == sum(pack.json.skills[] 长度 for pack in [garage, coding, writing])`，按本 cycle 落地后预期值约 29；`M` 同理由 manifest 派生，预期 ∈ {0, 1}）+ stderr 无 ERROR 级日志。
  - Given smoke 完成，When 检查 `.claude/skills/` / `.cursor/skills/` / `.opencode/skills/` 三个目录，Then 每个目录下子目录数 == `N`（与上面同一 N）。
  - Given `.garage/config/host-installer.json` 在 smoke 后写入，When 解析，Then `installed_packs[]` 按集合等价于 {`garage`, `coding`, `writing`}；`installed_hosts[]` 按集合等价于 {`claude`, `cursor`, `opencode`}；`files[]` 长度 == `N × 3`（按 host 维度物化）。
  - Given smoke 证据归档，When 在 PR walkthrough 中查找，Then 必须含 stdout/stderr 截取 + `host-installer.json` 节选 + 3 个宿主目录 ls 截取（推荐 `tree -L 2 .claude/skills | head -40` 形式）。

### FR-807 文档更新

- **优先级**: Must
- **来源**: F007 FR-710 5 分钟冷读链 + § 2.2 验收 #8
- **需求陈述**: 系统必须随本 cycle 同步更新以下用户可见文档：
  - `packs/README.md` "当前 packs" 表加入 `coding` 与 `writing` 两行；"未来计划" 段从 "F008 候选" 形式改为 "已落地" 状态描述
  - `packs/coding/README.md` + `packs/writing/README.md` + `packs/garage/README.md` 三个 pack 概述（含 skill 清单、pack 用途、与同 family 其它 skill 的引用关系）
  - `docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段补一句 "目前 garage init 默认装 N skill（N == 三个 pack.json.skills[] 长度之和，按本 cycle 落地后约 29），分布在 garage / coding / writing 三个 pack"
  - `RELEASE_NOTES.md` 新增 F008 段（按 F007 同等详尽度）
  - `AGENTS.md` § "Skill 写作原则" 引用的 `docs/principles/skill-anatomy.md` 路径与 § 4 收敛后的物理位置同步（具体动作由 design 决定）
- **验收标准**:
  - Given F008 PR 合并，When `cat packs/README.md | grep -E '\\| (coding|writing) \\|'`，Then 两个 pack 都出现在 "当前 packs" 表内且 "状态" 列为 "✅ 已落盘（F008）"。
  - Given 任意新 Agent / 新用户从 `AGENTS.md` 出发，When 顺序读 `AGENTS.md` → `packs/README.md` → 三个 `packs/<id>/README.md` → `docs/guides/garage-os-user-guide.md`，Then 必须能在 5 分钟内回答 (a) 三个 pack 各装哪些 skill、(b) 一行命令怎么装、(c) `.agents/skills/` 与 `packs/` 收敛后是什么关系 三个问题。
  - Given `RELEASE_NOTES.md`，When grep `## F008`，Then 必须出现，且段落结构与 F007 段一致（用户可见变化 / 数据与契约影响 / 验证证据 / 已知限制 四段）。

## 7. 非功能需求

### NFR-801 NFR-701 (宿主无关性) 在新 packs 下持续守住

- **优先级**: Must
- **来源**: F007 NFR-701 + `docs/soul/design-principles.md` § 1
- **需求陈述**: F008 新增的 `packs/coding/` 与 `packs/writing/` 全部源文件（`.md` / `.json` / `.js` / 其它）**不得**出现宿主特定术语（黑名单：`.claude/` / `.cursor/` / `.opencode/` / `claude-code` / "在 Claude Code 里" 等表述）。
- **验收标准**:
  - Given F008 实施完成，When 执行 `grep -rE '\\.claude/|\\.cursor/|\\.opencode/|claude-code' packs/coding/ packs/writing/`，Then 命中数 = 0（除 README 中作为示例字符串出现且明确标注为 "宿主目录示例"，design 阶段决定是否引入白名单豁免）。
  - Given `tests/adapter/installer/test_*.py` 中已有的 NFR-701 grep 检查（F007 落下），When F008 后再跑，Then 该测试仍通过且覆盖范围已自动延伸到 `packs/coding/` 与 `packs/writing/`（F007 spec § FR-701 验收 #1 / NFR-701 grep 测试已为 `packs/coding/` 自动覆盖，验证此承诺）。

### NFR-802 测试基线零回归

- **优先级**: Must
- **来源**: § 2.2 验收 #5 + #6
- **需求陈述**: F008 实施完成后，`uv run pytest tests/ -q` 整体计数必须 ≥ F007 基线 586，旧用例 0 退绿；新增测试至少覆盖 (a) 三个 pack.json schema 与 skills[] 长度 (b) 任一 hf-* skill 字节级搬迁 (c) family-level 资产可被找到 (d) F805 选定方案的物理状态。
- **验收标准**:
  - Given F008 PR，When CI / 本地 `uv run pytest tests/ -q`，Then 旧用例 100% 通过；新增用例 ≥ 4 个分别覆盖上述四类。
  - Given F007 既有 `tests/adapter/installer/` 30 个测试（实测 `grep -cE '^def test_' tests/adapter/installer/*.py | awk -F: '{s+=$2} END{print s}'`），When F008 后再跑，Then 0 退绿且 0 改写（只允许新增 smoke 用例）。

### NFR-803 `garage init --hosts all` 在本 cycle 落地的 packs 规模下耗时 ≤ 5 秒

- **优先级**: Should
- **来源**: F007 NFR-702 ≤ 2 秒在 1 skill 时已实测；本 cycle 落地后约 29 skill × 3 host ≈ 87 文件写入，应仍在用户感知友好范围
- **需求陈述**: 在干净下游目录、本 cycle 全部 packs（按 manifest 派生约 29 skill）× 3 host 全装基准下，单次 `garage init --hosts all` 总耗时（不含 python 启动）应 ≤ 5 秒；幂等再运行（无任何文件变化）应仍满足 F007 NFR-702 ≤ 2 秒。
- **验收标准**:
  - Given /tmp/f008-smoke 干净目录，When 第一次 `time garage init --hosts all`，Then 实测 wall-clock ≤ 5 秒。
  - Given 同上目录，When 第二次连续执行，Then 实测 wall-clock ≤ 2 秒（沿用 F007 NFR-702）。

### NFR-804 git diff 可审计

- **优先级**: Should
- **来源**: § 3.1 用户角色 "Garage 审计读者"
- **需求陈述**: F008 PR 的 git diff 必须按 "新增 packs/coding/" / "新增 packs/writing/" / "扩展 packs/garage/" / "处置 .agents/skills/" / "文档" 五类分组提交（推荐每组一个 commit），让 reviewer 能逐类审计。
- **验收标准**:
  - Given F008 PR，When `git log --oneline cursor/f008-...`，Then commit 数 ≥ 5 且 commit message 主题前缀清晰对应五类分组（如 `f008(coding):` / `f008(writing):` / `f008(garage):` / `f008(layout):` / `f008(docs):`）。
  - 注：实际允许 1 个或多个 commit/group，本 NFR 不强求数量，强求**可审计性**——任意一组改动可被独立 review。

## 8. 外部接口与依赖

- **依赖**: 仅依赖项目既有 `pyproject.toml` 中已有依赖。本 cycle **零依赖变更**（`uv.lock` 不变）。
- **外部接口**: 无新增。F007 落下的 `garage init --hosts ...` CLI 接口、退出码语义、stdout/stderr marker 全部沿用。
- **AGENTS.md 路径映射**: 本 cycle 可能涉及 `AGENTS.md § "Skill 写作原则"` 引用路径同步（FR-807 验收 #2），是否实际改动由 design 阶段决定 § 4 收敛方案后再定。

## 9. 约束与兼容性要求

### CON-801 不修改 F007 安装管道任何代码

- **优先级**: Must
- **来源**: § 4.2 关键边界 + § 4.3 与 F007 的边界表
- **需求陈述**: F008 PR 的 `git diff src/garage_os/` **必须为空**（除非搬迁过程中发现 F007 管道有 bug，那种情况下应单独开 `hf-hotfix` cycle 修复，不混进 F008）。
- **详细说明**: 这是把"内容物搬迁"与"管道改动"两件事彻底分开的硬约束，防止 F008 review surface 失控。

### CON-802 复用 F007 `pack.json` schema

- **优先级**: Must
- **来源**: F007 FR-701 + CON-703 schema_version 受 VersionManager 管控
- **需求陈述**: 三个新增 / 扩展 pack 的 `pack.json` 必须沿用 F007 落下的 6 字段 schema：`schema_version` (=1) / `pack_id` (= 目录名) / `version` (语义版本字符串) / `description` (人类可读) / `skills[]` / `agents[]`。本 cycle 不引入任何新字段。
- **详细说明**: 在 F008 阶段稳住 schema，让 F009+ 的 uninstall / update 在同一 schema 上落地。

### CON-803 搬迁是字节级 1:1，例外仅限相对引用路径

- **优先级**: Must
- **来源**: § 4.2 关键边界 "搬迁是字节级 1:1"
- **需求陈述**: 任一 SKILL.md / references 子文件 / templates 子文件的 `cp -R` 等价搬迁内容必须按 SHA-256 与原文件相等；唯一允许的例外是 family-level 资产的相对引用路径（如 `references/spec-template.md` → `../docs/skill-anatomy.md`）按 § 4 收敛方案做的最小修复。
- **详细说明**: 这是验收 #5 / FR-801/802/803 验收标准的根。

### CON-804 `.agents/skills/` 处置必须本 cycle 收敛

- **优先级**: Must
- **来源**: § 2.2 验收 #7
- **需求陈述**: F008 PR 合并后，`.agents/skills/` 在仓库内必须处于一个**明确的、单一确定的物理状态**（依据 § 4 收敛方案 A/B/C）；不允许 prose 中写 "暂时保留 / 以后再决定" 这类摇摆。
- **详细说明**: 见 FR-805。

## 10. 假设

### ASM-801 `.agents/skills/` 现有 28 个 source SKILL.md 内容全部已稳定

- **优先级**: Should
- **来源**: 本仓库 git history 显示 `.agents/skills/` 在最近 1 个月内主要变更集中在 write-blog 子目录（如 `093ffed Merge pull request #21 from hujianbest/cursor/blog-illustrations-b3dc`、`b249ed0 blog: 精简为每章一张代表性插图`、`c40679e blog: 将博客插图从 SVG 改为 PNG`，可通过 `git log --oneline --since="1 month ago" -- .agents/skills/` 复核）；hf-* / find-skills / writing-skills 主体未变。
- **需求陈述**: 假设 F008 cycle 期间 `.agents/skills/` 下 28 个 source SKILL.md（实测 `find .agents/skills -maxdepth 4 -name SKILL.md \| wc -l` = 28）+ 全部 references / evals / templates / docs 等附属内容不会有用户层并行改动。
- **失效风险**: 若 cycle 期间用户在 `.agents/skills/` 下修改了某 hf-* skill，搬迁后的 `packs/coding/` 内容会与最新版本字节不等。
- **缓解措施**: 实施前在 PR 描述中显式声明 "本 cycle 期间请勿在 `.agents/skills/` 下提交改动"；CI 中加 `git diff main..HEAD -- .agents/skills/ packs/` 同步检查（design 阶段决定是否实施）。

### ASM-802 三家宿主在 F008 实施期间仍承认 `.{host}/skills/<name>/SKILL.md` surface

- **优先级**: Should
- **来源**: F007 ASM-701 同来源（OpenSpec `docs/supported-tools.md` + 各家公开文档）
- **需求陈述**: 假设 Claude Code / OpenCode / Cursor 在 F008 cycle 期间不发生 `*/skills/` 路径 breaking change。
- **失效风险**: 若某家静默改名/弃用，会让本 cycle smoke 失败但 spec 本身不需要变。
- **缓解措施**: 沿用 F007 ASM-701 的缓解：smoke 时跑一次 manual 验证。

### ASM-803 family-level 共享资产数量在本 cycle 内稳定

- **优先级**: Could
- **来源**: § 1 表格清点（4 docs + 5 templates + 2 principles = 11 项）
- **需求陈述**: 假设本 cycle 期间不会有新的 hf-* shared docs / templates / principles 被加入。
- **失效风险**: 新增项可能改变 § 4 收敛方案的判断。
- **缓解措施**: 实施前再清点一次，作为 design 阶段第一步。

### ASM-804 用户在自己项目执行 `garage init` 时 `packs/` 来源是 Garage 仓库 git checkout

- **优先级**: Should
- **来源**: F007 ASM-702 + 本 cycle 不引入跨仓库 / 远程 pack 拉取语义
- **需求陈述**: 假设下游用户的 "可用 packs 集合" 等价于其本地 Garage 仓库 checkout 的 `packs/` 目录内容（无远程 / 无 lockfile / 无版本协商）。
- **失效风险**: 用户 checkout 旧版本 Garage 仓库会装到旧版 packs。
- **缓解措施**: F008 落地后在 release notes 中显式说明 "升级 packs 内容 = `cd ~/.../garage-agent && git pull`"；远程 / version-aware pack 是独立 cycle 候选。

## 11. 开放问题

### 阻塞性（必须在 hf-spec-review 通过前关闭）

当前**无阻塞性开放问题**。若 spec reviewer 发现以下任一项摇摆，应反馈以阻塞 finding 形式提出：
- `find-skills` 与 `writing-skills` 是否真的归 `packs/garage/`，还是该独立到 `packs/meta/`（spec 默认假设归 `garage/`）
- `.agents/skills/` 处置三个候选 (A/B/C) 是否需要在 spec 层就缩到一个，还是允许 design 阶段再裁决（spec 默认放权给 design）
- 是否在本 cycle 同时落 `packs/product-insights/`（spec 默认 deferred，等真实内容物到位）

### 非阻塞性（可在 design 阶段细化）

1. **family-level 共享资产物理位置**（FR-804）：候选 A `packs/coding/{docs,templates,principles}/` vs 候选 B 复制到每个 hf-* skill 的 `references/` vs 候选 C `packs/coding/skills/_shared/`——design 决定。本 spec 接受任一方案，前提是 FR-804 验收 #1 + § 4.2 "Design Reviewer 可拒红线" 第 1 条（去重不变量）同时满足。
2. **`.agents/skills/` 处置方案**（FR-805）：A 删除 + git symlink 回 packs / B 双副本 + lint 守门 / C 删除并改 IDE 加载入口——design 决定。本 spec 接受任一方案，前提是 FR-805 验收 #2/#4 + § 4.2 "Design Reviewer 可拒红线" 第 2 条（git status 干净 + lint 守门有具体实施位置）同时满足。
3. **`docs/principles/skill-anatomy.md` 双副本 drift 收敛策略**（§ 1 #6 + FR-804 验收 #4）：(a) 删根级 + 用 `packs/coding/principles/` 作唯一源 + 同步 `AGENTS.md` 路径；(b) 保留根级 + 用 git 软链指向 `packs/coding/principles/skill-anatomy.md` + family 内不再保留私副本；(c) 反向同步把 family 副本删掉、保留根级 + family 内通过相对路径引用根级——design 决定，前提是 FR-804 验收 #4 + § 4.2 "Design Reviewer 可拒红线" 第 3、4 条同时满足。
4. **`packs/garage/garage-sample-agent.md` 处置**：保留（证明 agent surface 在多 pack 下仍工作）vs 删除（让 `packs/garage/` 三件套对称）vs 移到 `packs/coding/agents/`（如果未来 hf-* 想引入 reviewer agent）——design 决定。
5. **`pack.json.version` 是否 bump**：`packs/garage/` 从 1 → 3 skill 的扩容是否要从 `0.1.0` → `0.2.0`；`packs/coding/` 与 `packs/writing/` 首版用 `0.1.0` 还是 `1.0.0`——design 决定。
6. **`AGENTS.md` 同步范围**：是否在本 cycle 同时刷新 `## Packs & Host Installer` 段的 5 分钟冷读指针表（如 "未来计划 F008+ 候选" 改为 "已落地"），还是仅刷新 `## Skill 写作原则` 引用路径——design 决定。
7. **smoke 用 `garage` 仓库自身 dogfood 还是干净 `/tmp/f008-smoke`**：spec 默认 `/tmp/f008-smoke`（更接近真实下游用户场景），但允许 design 阶段补一个 dogfood 反向 smoke 作为额外证据。
8. **是否在 `tests/adapter/installer/` 下加一个 "全 packs 全装" 集成测试**，还是只用 manual smoke walkthrough——design 决定（自动化测试优于人工 smoke，但 cycle 时间紧时可只做 smoke）。

## 12. 术语与定义

| 术语 | 定义 |
|------|------|
| **Pack**（沿用 F007） | 一组以共同主题打包的 Garage skills + agents，目录形态 `packs/<pack-id>/skills/...`、`packs/<pack-id>/agents/...`，含 `pack.json` 元描述 |
| **family-level 共享资产** | 不是单个 skill 内部的 references，而是一个 pack 内多个 skill 共享引用的 docs / templates / principles（HF family 共有 11 项） |
| **搬迁**（migration） | 把 `.agents/skills/<id>/` 下完整内容（含子目录）按 `cp -R` 等价语义复制到 `packs/<pack-id>/skills/<id>/`，字节级 1:1（仅相对引用路径允许最小修复） |
| **处置**（disposition） | 搬迁完成后，对 `.agents/skills/` 物理状态的最终决策，候选包括删除 / 软链 / 双副本 |
| **首装** | 下游用户在干净项目首次执行 `garage init --hosts <list>`（沿用 F007 § 3.2 场景 1） |
| **smoke 验证**（沿用 F007） | 端到端跑一次 `garage init --hosts all`，验证 packs / 安装管道 / manifest / 三家宿主目录全链路 |
| **getting-started 三件套** | F008 后 `packs/garage/` 含 `garage-hello`（占位 sample，验证 schema）+ `find-skills`（发现新 skill）+ `writing-skills`（写新 skill），构成下游用户首次接触 Garage 的入口三件套 |
