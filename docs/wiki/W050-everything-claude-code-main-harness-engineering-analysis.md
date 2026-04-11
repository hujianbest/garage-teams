# W050: Everything Claude Code Harness Engineering Analysis

- Wiki ID: `W050`
- 状态: 参考
- 日期: 2026-04-11
- 定位: 记录外部项目、方法与设计资料的分析结果，提炼对 `Garage` 的结构启发；默认作为参考资料，不作为当前主线真相源。
- 关联文档:
  - `docs/README.md`
  - `docs/GARAGE.md`
  - `docs/ROADMAP.md`

这份报告的目标不是介绍外部项目 `everything-claude-code-main` 有多少命令、多少技能，而是回答一个更实用的问题：

**如果你的团队要把 Agent 从“能用”推进到“可复用、可治理、可验证、可演进”，这套框架里哪些设计最值得借鉴，应该如何落地。**

说明：本文中出现的路径均指被分析项目 `everything-claude-code-main` 内部的路径，不代表当前 `ahe` 仓库的目录结构。

---

## 一、结论先行

如果把 `everything-claude-code-main` 简化成一句话，它本质上不是一个“提示词仓库”，而是一套围绕 AI coding agent 的 **harness performance system**。它把团队使用 Agent 时最容易失控的几件事，拆成了可独立治理的工程构件：

- `AGENTS.md` / `CLAUDE.md`：统一行为边界与项目级约束
- `agents/`：角色化执行者
- `commands/`：可触发的工作流入口
- `skills/`：可自动激活的知识模块
- `rules/`：始终生效的规范层
- `hooks/`：事件驱动的强制门禁与自动化
- `contexts/`：模式化上下文切换
- `scripts/`：安装、适配、hook 运行时、编排、审计
- `manifests/`：选择性安装与模块化交付
- `tests/`：对上述资产本身做回归验证

对团队搭建 harness engineering 来说，ECC 最有价值的不是某个单独的 prompt，而是它把 Agent 工程分成了五层：

1. **入口层**：统一入口文档和角色边界
2. **知识层**：rules、skills、contexts 的分层装配
3. **执行层**：commands、agents、hooks、scripts 的运行闭环
4. **运营层**：install manifest、profile、跨宿主适配
5. **治理层**：验证、学习、记忆、状态、审计、演进

如果你的团队要落地自己的 harness，最应该学的是这五层的分治方式，而不是照搬它全部目录。

---

## 二、分析范围与方法

本报告基于对外部项目 `everything-claude-code-main` 的源码级阅读，重点关注以下文件与目录：

- 根入口：`README.md`、`AGENTS.md`、`CLAUDE.md`
- 规则与知识治理：`rules/README.md`、`docs/SKILL-PLACEMENT-POLICY.md`、`docs/SKILL-DEVELOPMENT-GUIDE.md`
- 自动化与门禁：`hooks/README.md`
- 流程编排：`commands/orchestrate.md`、`commands/verify.md`
- 安装与模块化交付：`manifests/install-profiles.json`、`manifests/install-modules.json`
- 以及仓库顶层目录、跨宿主目录、测试目录的整体组织

这份报告不试图穷举所有 agent、skill、command，而是提炼对团队工程化最关键的架构模式。

---

## 三、它到底是什么：不是“配置包”，而是 Agent Harness 系统

从根 README 的表述可以看出，ECC 已经明确把自己定义为：

- **performance optimization system for AI agent harnesses**
- **complete system**
- 支持 **Claude Code、Cursor、Codex、OpenCode** 等多宿主

这说明它的设计重点不是“只在某个 IDE 下好用”，而是：

1. 如何把 Agent 行为抽象成可迁移资产
2. 如何把这些资产按宿主能力差异重新装配
3. 如何用 hooks、rules、tests 和 manifests 约束它们的运行

这对团队很重要，因为很多内部 Agent 基建之所以很快烂尾，往往不是 prompt 不够聪明，而是：

- 资产散落在个人配置里，无法复用
- 规则只存在口头约定里，无法执行
- 技能没有生命周期，越积越乱
- 宿主一换，全部重写
- 没有质量门禁，越自动越危险

ECC 的核心价值正是把这些问题产品化、模块化、代码化。

---

## 四、源码架构拆解：ECC 的 10 个关键子系统

### 1. 根入口文档：统一“行为宪法”

ECC 同时使用 `AGENTS.md` 与 `CLAUDE.md`：

- `AGENTS.md` 更像跨工具的总约束，定义原则、代理职责、开发顺序、安全底线、Git 习惯
- `CLAUDE.md` 更像仓库内工作说明，解释目录、测试命令、资产格式、贡献方式

这两个文件共同承担了团队 harness 中非常关键的职责：**把“默认行为”从隐性经验变成显性协议**。

对团队来说，这一层至少要覆盖：

- 何时必须规划、何时必须评审
- 何时必须跑验证
- 哪类任务必须走专门 agent
- 哪些信息允许写入代码、哪些必须写入文档
- 提交与 PR 约定

如果没有这一层，后续 commands、skills、hooks 都会因为缺少统一语义而失去一致性。

### 2. `agents/`：角色化执行而不是单一大脑

ECC 的 agent 不是“不同名字的同一个 prompt”，而是把常见任务拆成相对稳定的角色：

- planner
- architect
- tdd-guide
- code-reviewer
- security-reviewer
- build-error-resolver
- e2e-runner
- docs-lookup
- harness-optimizer
- loop-operator
- 各语言 reviewer / build resolver

这代表了一种重要设计选择：

**不要把所有复杂行为堆进一个主 agent，而要把稳定的专家视角提炼成可复用角色。**

对团队落地的启发：

- 先抽象“工作视角”，再抽象“技能内容”
- 角色要围绕结果责任，而不是围绕技术名词
- 高价值角色通常不是很多，3-8 个就能覆盖 80% 团队场景

### 3. `commands/`：把复杂流程收敛为显式入口

ECC 的 commands 不是普通命令别名，而是工作流入口：

- `/plan`
- `/tdd`
- `/code-review`
- `/verify`
- `/eval`
- `/checkpoint`
- `/orchestrate`
- `/multi-*`
- `/learn`
- `/update-docs`

commands 的真正价值在于：

- 让用户和 agent 都知道“从哪里进入”
- 把多步骤流程变成稳定接口
- 将复杂任务模板化，而不是每次重新描述

团队落地时，最先需要的通常不是很多 commands，而是少数几个**必须有统一入口**的流程：

- `/plan`
- `/verify`
- `/review`
- `/ship` 或 `/release`

这四类往往足以构成最初的工程骨架。

### 4. `skills/`：知识模块，而不是命令

ECC 的技能体系非常明确：skill 是被上下文自动激活的知识模块，不是主动执行器。

在 `docs/SKILL-DEVELOPMENT-GUIDE.md` 里，组件分工被定义为：

- skill：知识仓库，自动激活
- agent：任务执行者，显式委派
- command：用户动作入口
- hook：事件自动化
- rule：始终生效的约束

这是一个非常值得团队直接继承的分层。

很多团队做内部 Agent 时常见的问题是：

- 把“规范”写成 skill
- 把“命令说明”写成 skill
- 把“工作流”写成 agent

结果是激活条件混乱、行为不可预测。

ECC 的做法告诉我们：**知识与执行必须分离，知识与约束也必须分离。**

### 5. `rules/`：始终生效的规范层

`rules/README.md` 很清楚地定义了 ECC 的规则体系：

- `rules/common/`：通用规则
- `rules/<language>/`：语言扩展规则
- 语言规则覆盖通用规则
- 安装时必须复制整个目录，不能 flatten

它还明确区分：

- Rules 告诉你 **what**
- Skills 告诉你 **how**

这几乎是团队 harness 最容易被忽略、但最关键的一层。

因为一旦没有独立的 rule 层，团队会把：

- 代码风格
- 测试门槛
- 安全清单
- Git 习惯
- 上下文管理

全部散落到 prompt、文档、review comment 里，最终没人真正遵守。

对团队最值得复用的点：

1. 规则分层必须是物理分层，不只是逻辑分层
2. 通用规则和技术栈规则要分开演进
3. 规则必须能被安装、复制、覆盖，而不是只能在脑中记住

### 6. `hooks/`：从“建议”升级到“可执行门禁”

ECC 的 hooks 是整套系统最工程化的一部分之一。

在 `hooks/README.md` 中，hook 被分成：

- `PreToolUse`
- `PostToolUse`
- `Stop`
- `SessionStart`
- `SessionEnd`
- `PreCompact`

它们的能力覆盖：

- 阻止不合规的 shell 操作
- 提醒或阻止危险提交
- 编辑后自动做质量检查
- 会话开始/结束时装载与保存状态
- 连续学习与模式提取
- 成本追踪与通知

这说明 ECC 并不满足于“请模型自觉遵守规范”，而是把高价值规范推到 hook 层强制执行。

这正是团队 harness 从玩具走向生产的关键分水岭。

对团队的直接启发：

- 建议类约束放 rule / skill
- 高风险约束放 hook
- 能自动跑的检查不要只写成 checklist

第一批最值得做成 hook 的通常是：

1. 危险命令拦截
2. 提交前基础质量检查
3. 编辑后快速静态检查
4. 提示词或配置中的 secret 检测

### 7. `contexts/`：模式切换而不是上下文堆砌

ECC 提供了 `dev`、`review`、`research` 等 context 文档。

这意味着它没有试图把所有行为都塞进同一个永久 system prompt，而是引入了“模式上下文”：

- 开发时关注实现与验证
- 评审时关注风险、回归与证据
- 调研时关注探索与信息收敛

这种设计特别适合团队，因为真实工作里“当前模式”对 Agent 行为影响极大。

建议团队在自己的 harness 中至少保留 2-3 个 context：

- `dev`
- `review`
- `research`

这就足以显著降低单一 prompt 过载的问题。

### 8. `scripts/`：让非 prompt 资产真正可运行

ECC 的 Node 脚本承担了多个关键职责：

- 安装与增量安装
- package manager 识别
- hook 实现与适配
- orchestration 辅助
- 状态存储与查询
- 各类校验工具

对团队来说，真正应该学习的是这个原则：

**一旦某项能力需要跨平台、可复用、可测试，就不要把它留在 Markdown 里，要落成脚本。**

典型适合脚本化的能力包括：

- 配置同步
- 工程检查
- 生成任务
- 交接文档整理
- 状态查询

### 9. `manifests/`：模块化交付，而不是一键全装

`install-profiles.json` 和 `install-modules.json` 展示了 ECC 非常成熟的一点：它不是把所有资产捆成一个大包，而是通过 profile 和 module 装配。

例如 profile 有：

- `core`
- `developer`
- `security`
- `research`
- `full`

module 则把资产按能力域拆成：

- `rules-core`
- `agents-core`
- `commands-core`
- `hooks-runtime`
- `platform-configs`
- `workflow-quality`
- `framework-language`
- `database`
- `security`
- `orchestration`
- 以及大量可选 domain modules

这对团队极其重要，因为内部 harness 一旦没有模块边界，就会迅速出现两个问题：

- 新成员安装成本极高
- 团队只需要 20% 能力，却被迫承受 100% 复杂度

ECC 的启发是：

- 先把可复用能力模块化
- 再把模块组合成不同角色或团队 profile
- 最后才谈“全家桶”

### 10. `tests/`：把 harness 自己也纳入回归保护

ECC 不只对业务代码做测试，而是对 harness 资产本身做测试，包括：

- 脚本测试
- hook 测试
- 安装器测试
- 配置兼容性测试
- catalog / manifest 测试

这非常关键，因为一套面向团队的 harness，本质上已经是一种“开发者平台”。

既然是平台，就必须测试：

- 安装是否正确
- hook 是否误拦截
- 配置是否兼容
- manifests 是否漂移
- 资产计数与引用是否一致

如果没有这一层，团队越依赖 harness，升级风险就越高。

---

## 五、ECC 最值得团队借鉴的 7 个设计模式

### 模式 1：统一入口文档 + 分角色资产

组合方式：

- `AGENTS.md` 负责总约束
- `CLAUDE.md` 负责仓库工作说明
- `agents/commands/skills/rules` 各司其职

借鉴理由：

- 降低认知歧义
- 明确谁负责“说什么、做什么、何时触发”
- 为后续自动化奠定稳定语义基础

### 模式 2：规则与知识分层

ECC 明确不把所有内容都写进 skill，而是把：

- 始终生效的约束放进 `rules/`
- 任务型知识放进 `skills/`

借鉴理由：

- 降低自动激活的不确定性
- 让“必须遵守”和“按需参考”不混淆
- 方便技术栈差异化扩展

### 模式 3：hooks 兜底，防止纯提示词系统失效

如果团队只靠 instructions，没有 hook，那么：

- 容易漏跑质量检查
- 容易误执行危险命令
- 容易把安全约束当成“软建议”

ECC 用 hook 把这些高风险点工程化了。

借鉴理由：

- 把风险从“依赖模型自觉”降到“事件可控”
- 让最关键的治理点可以被代码测试

### 模式 4：选择性安装，而不是强推全量能力

ECC 的 profile/module 架构说明：harness 要像平台产品，而不是像个人配置。

借鉴理由：

- 支持不同团队、不同项目、不同成熟度阶段
- 安装与升级时更可控
- 便于做内部分发

### 模式 5：技能生命周期治理

ECC 在 `SKILL-PLACEMENT-POLICY.md` 中明确区分：

- curated
- learned
- imported
- evolved

并给出了 learned/imported 需要 provenance 的治理方向。需要注意的是，这一层在 ECC 中更像“目录与发布边界已经清晰、部分自动 enforcement 仍在补完”的生命周期 policy，而不是一个已经完全闭环的自动治理系统。

借鉴理由：

- 防止团队把临时学习结果误当成正式资产
- 让可发布资产和本地演化资产分开
- 为未来评审、回滚、审计提供基础

### 模式 6：跨宿主适配作为一级问题处理

ECC 明确同时服务 Claude Code、Cursor、Codex、OpenCode。

借鉴理由：

- 团队实际环境往往异构
- 可以先沉淀一层跨宿主共用资产，再为不同宿主补适配层
- 共用资产可以沉淀得更稳定

但这里要避免过度乐观。ECC 的跨宿主并不是“完全一套实现到处通吃”，而是把系统拆成：

- **可复用核心层**：`AGENTS.md`、部分 skills、commands 文档、manifests、部分脚本
- **宿主适配层**：rules 分发方式、hooks 执行能力、平台配置目录、额外 runtime 依赖

例如，Claude Code 插件本身无法自动分发 `rules`，Codex 目前也没有与 Claude Code 对等的 hook 能力，某些 `multi-*` 工作流还依赖额外 runtime。因此，团队真正应该借鉴的是“把宿主差异显式建模”，而不是假设换宿主时几乎零成本迁移。

### 模式 7：把“验证流程”做成显式 command

`/verify` 这类命令的意义不只是方便，而是把“上线前最小证据集”变成显式流程。

借鉴理由：

- 统一团队对“完成”的定义
- 让主 agent、review agent、开发者看到相同标准
- 有助于后期接入 CI 或自动 loop

---

## 六、如果你的团队要照着搭，最小可行版本应该长什么样

ECC 很完整，但不适合一开始照单全收。对于大多数团队，建议的最小可行 harness 只包含以下 6 类资产。

### 1. 一个统一入口文件

建议：

- 项目级 `AGENTS.md`

它至少定义：

- 开发默认工作流
- 必须执行的验证步骤
- 哪些情况必须 review
- 哪些命令或目录属于高风险区域

### 2. 一套分层规则

建议至少有：

- `rules/common/`
- `rules/<主要技术栈>/`

内容先聚焦：

- coding-style
- testing
- security
- git-workflow

### 3. 三到五个核心 commands

建议优先建设：

- `/plan`
- `/verify`
- `/review`
- `/ship`
- `/learn`（如果团队已经有稳定复盘机制）

### 4. 三到六个核心 agents

建议优先建设：

- planner
- code-reviewer
- security-reviewer
- build-error-resolver
- docs-researcher 或 docs-lookup

### 5. 两到四个关键 hooks

建议优先建设：

- 编辑后快速检查
- commit 前质量门禁
- secret / 高危配置拦截
- 长任务或 dev server 提醒

### 6. 一个最小验证脚本

哪怕没有完整 CI，也要至少有一个团队认同的验证入口，例如：

- `scripts/verify.sh`
- 或 Node/Python 版本的 verify runner

它输出的不是详细日志，而是：

- build 是否通过
- test 是否通过
- lint / typecheck 是否通过
- 是否存在高风险残留

这就是最早期的“完成定义”。

---

## 七、推荐的团队落地路线

下面是一条比“照搬 ECC”更现实的演进顺序。

### 阶段 0：统一行为，不急着自动化

目标：

- 先让团队对 Agent 工作方式有共识

建议产物：

- `AGENTS.md`
- 1 份项目级验证清单
- 1 份主要技术栈规则

成功标志：

- 团队对“Agent 什么时候该计划、什么时候该验证、什么时候该 review”有统一定义

### 阶段 1：把共识变成 commands 与 rules

目标：

- 把高频流程变成统一入口

建议产物：

- `/plan`
- `/verify`
- `/review`
- 分层 `rules/`

成功标志：

- 80% 常见任务都能走统一入口，而不是每个人自己描述流程

### 阶段 2：引入 hooks，把关键风险自动化

目标：

- 降低“模型忘了做”的风险

建议产物：

- pre-commit 质量门禁
- 编辑后静态检查
- secrets / 高危命令拦截

成功标志：

- 最危险的错误开始被自动阻止，而不是事后 review 才发现

### 阶段 3：引入 skill 生命周期和模块化安装

目标：

- 让资产可演进、可安装、可裁剪

建议产物：

- curated / learned / imported 分层
- install profiles
- install modules

成功标志：

- 团队可以按角色和项目安装不同能力组合

### 阶段 4：引入 orchestrate、learning、state

目标：

- 从“单次交互”升级到“持续运营”

建议产物：

- 多 agent handoff 模板
- session summary / checkpoint
- learn / eval / evolve
- orchestration status

成功标志：

- 团队开始把 harness 当成长期平台，而不是一次性配置

---

## 八、哪些值得借鉴，哪些不建议直接照搬

### 建议直接借鉴的部分

1. **组件分层方法**
2. **rule 与 skill 分治**
3. **hooks 驱动的门禁思路**
4. **profile / module 安装架构**
5. **技能生命周期与 provenance**
6. **verify / orchestrate 这类显式工作流命令**
7. **跨宿主目录并存的组织方式**

### 不建议直接照搬的部分

1. **全部 agent / commands / skills 数量**
   - ECC 面向的是通用公众仓库，你的团队需要的是高频场景优先

2. **完整 continuous-learning 体系**
   - 这类能力运维成本高，且容易引入噪音资产

3. **多模型 / worktree / tmux 全套编排**
   - 适合复杂任务与重运营团队，不适合起步阶段

4. **所有宿主同时支持**
   - 起步时先把主宿主做好，再考虑横向扩展

5. **所有 domain skills**
   - 团队初期最需要的是工程工作流，不是内容、媒体、行业技能全家桶

一句话：**先学 ECC 的架构，不要先学 ECC 的规模。**

---

## 九、结合你当前 AHE 仓库，最值得优先补上的映射

你当前仓库已经有一些非常好的基础：

- 根级 `AGENTS.md`
- 新增的根级 `README.md`
- `.cursor/skills/` 的本地接入方式
- `skills/` 这个仓库自有 skill 工作区
- `templates/`、`agents/`、`rules/`、`hooks/` 这些明确分层的位置

这意味着你不是从零开始，真正需要做的是把这个个人知识仓库持续推进成“可执行、可维护的 harness”。

### 建议优先补强 1：显式区分 rule / skill / workflow / command

当前仓库更偏“知识与技能集合”，下一步可以更明确地区分：

- 哪些是规范
- 哪些是技能
- 哪些是流程入口
- 哪些是宿主级约束

否则后续资产一多，触发边界会变模糊。

### 建议优先补强 2：为团队工程任务提供最小 command 集

即使当前仓库本身不是一个业务应用，也可以为后续团队落地先沉淀 command 模板，例如：

- `plan`
- `verify`
- `review`
- `release-notes`

这些会比继续增加大量知识型文档更接近“harness engineering”。

### 建议优先补强 3：为高风险操作设计宿主级 hook 规则

你们的仓库里已经强调了 Cloud / Agent 运行约定，但还可以进一步形成：

- 文档生成后的自动校验
- skill frontmatter 校验
- 特定目录误写保护
- 评测或打包前的强制检查

这样知识仓库就开始具备平台的防呆能力。

### 建议优先补强 4：定义资产生命周期

ECC 对 curated / learned / imported / evolved 的区分很有参考价值。

对你们仓库，建议至少定义：

- 仓库内正式技能
- 个人实验技能
- 自动生成技能
- 外部导入技能

否则后续非常容易把实验性资产直接混进正式目录。

### 建议优先补强 5：把“如何搭建 harness”的内容沉淀成结构化文档

当前仓库没有单独的 `playbooks/` 目录，因此更适合先在 `docs/` 中沉淀这类内容。可以考虑后续补出：

- 团队 harness 设计清单
- 宿主适配清单
- hooks 设计清单
- skills 生命周期清单
- 评测与验收清单

这会比单纯增加技能目录更利于团队实施。

---

## 十、给团队的实施清单

如果你接下来要正式为团队搭建 harness engineering，可以按下面顺序推进。

### 第一步：定义骨架

- 统一入口文件放哪里
- 团队规范放哪里
- 技能、规则、命令、脚本分别放哪里
- 哪些目录允许自动生成，哪些必须人工维护

### 第二步：定义最小流程

- 需求分析入口
- 规划入口
- 验证入口
- 评审入口
- 发布入口

### 第三步：定义最小门禁

- 编辑后检查什么
- 提交前检查什么
- 哪些行为必须阻止
- 哪些行为只提醒

### 第四步：定义资产生命周期

- 正式资产与实验资产怎么区分
- 是否允许自动学习
- 学习结果如何审查后进入正式资产
- 是否需要 provenance

### 第五步：定义宿主策略

- 当前主宿主是哪一个
- 是否需要兼容 Cursor / Claude Code / Codex
- 哪些资产跨宿主共享
- 哪些资产按宿主生成

### 第六步：定义验证策略

- harness 自己怎么测试
- hooks 怎么回归验证
- 安装器怎么验证
- skill / command / rule 的引用一致性怎么检查

---

## 十一、一个现实判断：什么样的团队最适合借鉴 ECC

ECC 特别适合以下团队：

- 已经高频使用 coding agents
- 团队内存在多个项目或多个宿主环境
- 希望把个人经验沉淀成组织资产
- 希望把“做法”升级为“机制”
- 能接受为 Agent 基建投入持续维护成本

如果团队还处于很早期阶段，只是偶尔使用 Agent，那么应该先借鉴：

- 入口文档
- 分层规则
- 少量 commands
- 少量 hooks

而不是一上来建设复杂的 orchestration、continuous learning、multi-model runtime。

---

## 十二、最终建议

站在“指导团队后续搭建 harness engineering”的角度，我对 ECC 的最终判断是：

### 它最值得学习的，不是“内容量”，而是“结构化治理”

ECC 的真正强项不在于 30 个 agent、135 个 skill、60 个 command 这些数字，而在于它把 Agent 工程拆成了：

- 可说明的角色
- 可安装的模块
- 可执行的门禁
- 可切换的上下文
- 可回归的脚本
- 可运营的资产生命周期

### 你的团队最值得复用的核心原则有三条

1. **先分层，再扩容**
   - 先把 rule / skill / command / hook / agent 分清楚，再慢慢加数量

2. **先把高风险点工程化，再追求智能化**
   - 先把验证、门禁、安装、升级做好，再谈自动学习和多 agent 编排

3. **先做团队最小闭环，再做平台雄心**
   - 先让团队的 plan / verify / review / release 跑顺，再扩展到更多宿主和领域

### 如果只做一件事

那我建议你先按 ECC 的思路，为团队建立这样一个最小闭环：

- 一个统一入口文档
- 一套分层 rules
- 三个 commands：`plan`、`verify`、`review`
- 三个 agents：planner、reviewer、security reviewer
- 两个 hooks：编辑后检查、提交前检查
- 一个 install profile：`core`

只要这个闭环稳定运行，你们的 harness engineering 就已经从“个人技巧”跨入“团队工程”了。

---

## 附录：一句话总结这套框架

`everything-claude-code-main` 不是在教团队“怎么写更长的 Agent prompt”，而是在示范：**如何把 Agent 使用经验沉淀成一套可安装、可执行、可验证、可演进的工程系统。**
