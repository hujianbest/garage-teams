---
name: ahe-workflow-starter
description: 在 workflow 场景中先判断当前阶段，再把软件工作路由到正确位置。适用于需求、规格、设计、任务规划、实现、变更、缺陷修复等软件交付请求的起点，或用户说 continue/start/推进/继续开发、但当前阶段仍不清楚的场景。
---

# AHE 工作流入口

当当前软件交付工作仍需要判断阶段时，先使用这个 skill。

## 系列级入口规则

这个 skill 不是普通起始建议，而是 `ahe-*` workflow 的统一前置门。

只要当前请求属于软件交付流程中的任一场景，且你还需要判断当前阶段、核对工件状态、决定下一步，或恢复后续编排，就应先经过这里：

- 开始一个新需求、功能或项目
- 用户说"继续""推进""开始做""先处理这个"
- 用户要求看代码、澄清需求、做设计、拆任务或直接实现
- 用户只要求做某种 review / gate，或明确点名某个 `ahe-*` 能力 skill
- 用户提出需求变更
- 用户提出紧急缺陷修复

如果当前阶段尚未完成这里的路由判断，就不要先进入下游 skill，也不要先开始推进主链或支线工作。

## 目的

你的职责不是直接实现，而是判断当前所处阶段、选择 workflow profile、识别 workflow 中推荐的下一步 skill、决定后续编排顺序，并阻止乱序推进。

这个 skill 用于把软件作业按这套 skills 体系路由到正确阶段。

它是 workflow 的入口门禁，根据选定的 profile 编排不同密度的节点链路。

变更请求和热修复会被路由到专门的支线流程。

## 编排职责

`ahe-workflow-starter` 不只负责"第一次进哪个 skill"，还负责在以下情况中恢复后续编排：

- 用户说"继续"，需要根据最新证据决定下一步
- 某个 review / gate 完成后，需要决定是回到上游修订，还是继续进入下一个质量节点
- 用户明确点名某个 `ahe-*` 能力 skill，但仍需要由 workflow 判断它是否是当前正确的下一步
- 主链、变更支线、热修复支线之间需要做受控切换

当当前推荐节点是 review 节点时，本 skill 还负责把该 review 动作派发给独立 reviewer subagent，而不是在父会话里直接内联执行评审判断。

能力型 skill 只负责完成本类检查并给出结论；至于当前会话应不应该进入它、之后该进入哪里，由本 skill 统一编排。

## 状态机原则

把 `ahe-workflow` 视为一个由本 skill 驱动的轻量状态机，而不是一组可以随意挑选的能力说明：

- 任一时刻只允许存在一个**当前推荐节点**和一个**当前 workflow profile**
- 当前推荐节点必须由最新工件证据、review / gate 结论和用户请求共同决定
- 推荐节点必须在当前 profile 的合法节点集合内
- 下游 skill 不负责自行挑选下一步；它们只负责完成本节点职责并返回结论
- review 节点保留原 canonical 节点名，但其实际执行方式是：父会话派发 reviewer subagent，reviewer 在 fresh context 中调用对应 `ahe-*review`
- 任何新的用户请求、证据冲突、review / gate 结论、变更信号、热修复信号，都会触发本 skill 重新编排

如果你发现自己在没有重新经过本 skill 的情况下，就直接把会话从一个节点切到另一个节点，这通常说明你已经绕开了状态机。

## 决策分类

为避免在边界场景里凭感觉路由，先判断当前属于哪类决策：

- **机械决策**：工件状态、review / gate 结论和当前 profile 足以唯一决定下一节点，直接路由
- **保守决策**：证据冲突、批准状态不清或工件彼此矛盾，回到更上游阶段或更重 profile
- **暂停决策**：命中明确 pause point，必须等待用户输入
- **挑战决策**：用户请求与当前工件证据冲突，先指出冲突，再按保守原则路由

优先顺序：

1. 先识别是否命中支线信号（`ahe-hotfix` / `ahe-increment`）
2. 再判断当前 profile 与合法节点集合
3. 再根据工件批准状态和 review / gate 结论做机械或保守决策
4. 只有命中 pause point 时才暂停，其他情况继续执行

## Workflow Profiles

本 skill 在路由时同时决定当前工作应使用哪个 workflow profile。

profile 控制的是当前工作需要走哪些节点，而不是降低门禁强度：每个 profile 内的节点仍执行完整检查。

### Profile 定义

| Profile | 适用场景 | 节点链路 |
|---------|---------|---------|
| **full** | 新功能、架构变更、高风险模块、跨模块重构、无已批准规格或设计 | 全部主链节点 |
| **standard** | 中等功能、已有规格+设计的功能扩展、非高风险 bugfix | `ahe-tasks` → `ahe-tasks-review` → `ahe-test-driven-dev` → 完整质量层 → `ahe-finalize` |
| **lightweight** | 纯文档/配置/样式变更、低风险 bugfix（单文件、无接口变化） | `ahe-tasks` → `ahe-tasks-review` → `ahe-test-driven-dev` → `ahe-regression-gate` → `ahe-completion-gate` → `ahe-finalize` |

### Profile 选择规则

Profile 由本 skill 在路由阶段决定，不允许用户自行声称或 agent 擅自假定。

选择顺序：

1. 若 `AGENTS.md` 声明了强制 profile 规则（如"涉及支付的任何改动强制 full"），优先执行。
2. 若 `task-progress.md` 中已记录 Workflow Profile 且仍在同一工作周期内，沿用该 profile。
3. 否则根据以下信号判断。

这里的“同一工作周期”至少要求以下条件仍成立：

- 当前目标没有切换到新的需求 / 新的热修 / 新的增量
- 已批准上游工件集合没有变化
- 没有出现需要升级 profile 的新证据

选择信号：

- **full**：无已批准规格或设计；用户明确要求从头开始；涉及架构/接口/数据模型变更；`AGENTS.md` 声明的高风险模块。
- **standard**：已有已批准规格+设计，但需新增任务；中等复杂度 bugfix（非高风险）；已有设计内的功能扩展。
- **lightweight**：纯文档/配置/样式变更；低风险 bugfix（单文件、无接口变化）；改动行数 ≤ 30 且无功能行为变化。

当信号冲突时，选择更重的 profile（保守原则）。

详细选择信号矩阵与示例请阅读：`references/profile-selection-guide.md`

### Profile 升级规则

在流程执行中，如果发现实际复杂度超出当前 profile：

- lightweight 可升级到 standard 或 full
- standard 可升级到 full
- **不允许降级**

升级触发条件：

- 实现过程中发现缺少规格或设计依据
- review / gate 返回 `阻塞`，且阻塞原因指向上游工件缺失
- 改动范围超出预期（例如从单文件扩散到多模块）

升级时必须：

1. 在 `task-progress.md` 中更新 Workflow Profile 字段并记录升级原因
2. 按新 profile 的节点链路重新路由到正确阶段

### Profile 与合法状态集合的关系

每个 profile 的合法主链节点是该 profile 节点链路中包含的节点子集。在当前 profile 不包含的节点上推进，视为无效迁移。

## 合法状态集合

full profile 主链推荐节点：

- `ahe-specify`
- `ahe-spec-review`
- 规格真人确认
- `ahe-design`
- `ahe-design-review`
- 设计真人确认
- `ahe-tasks`
- `ahe-tasks-review`
- `ahe-test-driven-dev`
- `ahe-bug-patterns`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`
- `ahe-regression-gate`
- `ahe-completion-gate`
- `ahe-finalize`

standard profile 主链推荐节点：

- `ahe-tasks`
- `ahe-tasks-review`
- `ahe-test-driven-dev`
- `ahe-bug-patterns`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`
- `ahe-regression-gate`
- `ahe-completion-gate`
- `ahe-finalize`

lightweight profile 主链推荐节点：

- `ahe-tasks`
- `ahe-tasks-review`
- `ahe-test-driven-dev`
- `ahe-regression-gate`
- `ahe-completion-gate`
- `ahe-finalize`

支线推荐节点（所有 profile 通用）：

- `ahe-increment`
- `ahe-hotfix`

如果某个用户请求、口头描述或局部记录暗示跳到当前 profile 合法集合之外，按无效迁移处理，回到最近一个有证据支撑的上游节点，或触发 profile 升级。

## Canonical Route Map

把下列主骨架视为默认路由图；任何实际迁移都必须同时满足 profile 合法集合、批准证据和迁移表规则：

```text
full:
  ahe-specify -> ahe-spec-review -> 规格真人确认
  -> ahe-design -> ahe-design-review -> 设计真人确认
  -> ahe-tasks -> ahe-tasks-review -> ahe-test-driven-dev
  -> ahe-bug-patterns -> ahe-test-review -> ahe-code-review
  -> ahe-traceability-review -> ahe-regression-gate
  -> ahe-completion-gate -> ahe-finalize

standard:
  ahe-tasks -> ahe-tasks-review -> ahe-test-driven-dev
  -> ahe-bug-patterns -> ahe-test-review -> ahe-code-review
  -> ahe-traceability-review -> ahe-regression-gate
  -> ahe-completion-gate -> ahe-finalize

lightweight:
  ahe-tasks -> ahe-tasks-review -> ahe-test-driven-dev
  -> ahe-regression-gate -> ahe-completion-gate -> ahe-finalize

branches:
  increment -> ahe-increment -> return via starter
  hotfix -> ahe-hotfix -> return via starter
```

## 状态转移来源

本 skill 只能依据以下四类输入决定迁移：

1. 当前用户请求
2. 已批准或未批准的工件状态
3. review / gate 结论
4. 进度记录、验证记录、发布记录中的阶段证据

不要把"我记得上轮已经做到这里了"当作合法输入。

不要把"某个 skill 看起来就很适合这个请求"当作合法输入。

## 铁律

在把会话正确路由到合适阶段之前，不要开始推进主链或支线工作。

如果有任何不确定，先解决"当前阶段是什么"和"当前 profile 是什么"这两个问题。

对 workflow 场景而言，澄清、探索、读代码、review、gate、设计、任务拆解、实现都属于推进动作，推进之前必须先完成路由。

## 连续执行原则

路由完成后，应在同一轮中立刻进入目标 skill 并执行，不等待用户确认。

整条 workflow 链路默认以连续执行模式运行：一个节点完成后，自动判断下一个节点并立刻进入，直到遇到设计中的暂停点。

### 暂停点

只有以下场景才暂停执行并等待用户输入：

1. **规格真人确认**：reviewer subagent 返回 `ahe-spec-review` 结论为"通过"后，必须由父会话向用户展示评审结论并等待用户明确批准
2. **设计真人确认**：reviewer subagent 返回 `ahe-design-review` 结论为"通过"后，必须由父会话向用户展示评审结论并等待用户明确批准
3. **测试用例设计确认**：`ahe-test-driven-dev` 在进入 Red-Green-Refactor 前，必须向用户展示测试用例设计并等待用户确认
4. **规格评审 / 设计评审未通过**：`ahe-spec-review` 或 `ahe-design-review` 返回 `需修改` / `阻塞` 时，必须先向用户展示评审结论和修订重点，再回到相应上游修订 skill
5. **证据冲突需澄清**：工件状态互相矛盾，且无法用保守原则自动解决时
6. **其他 review / gate 结论为"需修改"或"阻塞"且修订方向不明确**：需要与用户讨论修订方案

### 非暂停点

以下转场不需要等待用户确认，应在同一轮中自动推进：

- 路由完成后进入目标 skill
- 执行型 skill 完成后进入下一个能力型 skill（如 `ahe-specify` 完成 → `ahe-spec-review`）
- review / gate 结论为"通过"后进入迁移表中的下一个节点（真人确认节点除外）
- 除 `ahe-spec-review` / `ahe-design-review` 外，review / gate 结论为"需修改"且修订方向明确时，自动回到上游 skill 继续修订
- 恢复编排协议判断出唯一下一推荐节点时

### 连续执行的红旗信号

如果你发现自己在非暂停点输出路由报告后停下来等用户回复，这说明你把路由报告当成了用户交互，而不是内部编排步骤。正确做法是把路由说明嵌入执行流中，然后立刻进入目标 skill。

## Review 节点执行方式

review 节点仍然是 workflow 的 canonical 节点，但执行方式与普通执行型 skill 不同。

当当前推荐节点是以下任一 review 节点时：

- `ahe-spec-review`
- `ahe-design-review`
- `ahe-tasks-review`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`

不要在父会话里直接展开评审判断。应：

1. 根据节点名选择对应的 `ahe-*review` skill
2. 组装最小 review request
3. 启动独立 reviewer subagent
4. 读取 reviewer 返回的结构化摘要
5. 再由父会话决定下一步或真人确认

详细协议见：

- `references/review-dispatch-protocol.md`
- `references/reviewer-return-contract.md`

规则边界：

- review 记录由 reviewer subagent 负责落盘
- workflow 推进仍由父会话负责
- `ahe-spec-review`、`ahe-design-review` 的真人确认始终由父会话负责
- gate 节点当前仍按原有方式执行，不在本轮协议内自动改成 verifier subagent

## 红旗信号

出现以下想法时，先停下。这通常说明你正在为"跳过流程"找理由：

| 想法 | 实际要求 |
|---|---|
| "这只是个简单请求，可以直接做" | 简单请求也要先判断当前阶段和 profile。 |
| "我先快速看看代码再说" | 先路由，再按目标 skill 的要求读代码。 |
| "我先多收集一点信息更稳妥" | 路由只读取最少必要证据，不先做大范围探索。 |
| "用户都说继续了，应该就是实现" | "继续"不等于实现，必须先检查规格、设计、任务和进度证据。 |
| "用户只是让我做 review，不算进入流程" | review / gate 请求也属于 workflow 编排的一部分，仍要先做路由判断。 |
| "文档大概已经齐了，先往下推进吧" | 没有明确批准证据，就按未批准处理。 |
| "这个流程太完整了，先跳一步节省时间" | 如果觉得流程过重，应评估是否适用更轻的 profile，而不是在当前 profile 内跳步。 |
| "热修复很急，可以先改再补流程" | 热修复也必须先进入 `ahe-hotfix`，不能绕过复现、评审和门禁。 |
| "这是个小变更，不用走变更支线" | 只要是需求或范围变化，就先判断是否应进入 `ahe-increment`。 |
| "我已经知道现在在哪个阶段了" | 结论必须绑定当前工件证据，而不是依赖印象或聊天记忆。 |
| "用户已经点名某个 ahe skill，就不用再经过入口了" | 点名 skill 也不等于当前时机正确，仍要由本 skill 判断是否应进入它。 |
| "先做一点实现，后面再补 route 说明" | 路由必须先完成，之后才能进入下游 skill。 |
| "这个改动很小，直接用 lightweight 就行" | Profile 由本 skill 根据信号判断，不允许用户或 agent 自行声称。 |

## `AGENTS.md` 扩展约定

在读取任何阶段证据之前，先检查项目根部或工作区约定中的 `AGENTS.md`。

若其中声明了 `ahe-workflow` 相关规则，优先读取：

- 工件路径映射
- 审批状态别名与 review 结论别名
- 真人确认的等价证据来源
- 进度记录、review、verification 的实际位置
- spec / design / tasks / review / verification 模板覆盖路径
- 团队级 coding / design / testing 规范
- Workflow Profiles 配置（默认 profile、强制 full 规则、允许 / 禁止 lightweight 条件）

若 `AGENTS.md` 没有覆盖某一项，再回落到本 skill 和参考文档中的默认路径、默认状态词与默认模板。

## 优先读取内容

只读取完成路由所需的最少内容：

1. `AGENTS.md` 中与 `ahe-workflow` 相关的工件映射、团队约定和 Workflow Profiles 配置（如果存在）
2. 当前需求、缺陷、变更或继续推进的用户请求
3. 现有已批准的规格、设计、任务工件，但只读取判断"是否存在、是否已批准"所需的最少内容
4. 当前进度记录（含 Workflow Profile 字段）、发布说明、评审记录、验证记录等可作为阶段证据的工件

路由阶段不要开始大范围探索代码库。

如果证据彼此冲突，采用保守原则：

- 按未批准处理
- 回到更上游的阶段
- 不因为某一条口头描述或孤立记录就继续往下游推进

## 附加资源

当项目的 `AGENTS.md` 还没有完整声明 `ahe-workflow` 映射，或交付件布局与阶段判断方式不清晰时，阅读以下参考文档：

- `references/routing-evidence-guide.md`
- `references/profile-selection-guide.md`
- `references/review-dispatch-protocol.md`
- `references/reviewer-return-contract.md`

用它们来先补齐 `AGENTS.md` 中的工件位置、阶段证据来源和 profile 规则，避免后续工作流越来越混乱。

## 路由顺序

路由分两步：先决定 profile，再决定当前阶段。

### 路由优先级原则

当多个信号同时出现时，按以下优先级解释：

1. 支线信号优先于主链普通推进
2. 明确的 review / gate 恢复优先于“继续做点实现”
3. 缺失上游已批准工件优先于进入下游能力
4. 若证据冲突，优先选择更保守的上游阶段或更重 profile

如果 `ahe-hotfix`、`ahe-increment` 或 `ahe-test-driven-dev` 已经在工件中写回了明确的 `Next Action Or Recommended Skill`，且该下一步与最新证据不冲突、也在当前 profile 的合法节点集合内，则优先尊重这个显式交接，而不是重新根据旧支线信号或默认主链顺序回卷。

### 显式交接值规范

把 `Next Action Or Recommended Skill` 视为一个受控字段，而不是自由文本：

- 首选写法：直接写规范 skill ID，例如 `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review`、`ahe-test-driven-dev`、`ahe-code-review`
- 保留节点 `规格真人确认`、`设计真人确认` 仍然是合法值
- 若读到旧写法或自然语言标签，先按下列映射归一化后再参与路由判断：
  - `重新进入规格评审` -> `ahe-spec-review`
  - `重新进入设计评审` -> `ahe-design-review`
  - `重新进入任务评审` -> `ahe-tasks-review`
  - `回到实现阶段` -> `ahe-test-driven-dev`
- 若某个值无法唯一归一化为当前 profile 中的合法节点，则把它视为无效显式交接，回退到迁移表和工件证据继续判断
- 若显式交接与最新 evidence 冲突，即使值本身合法，也优先相信更上游、更保守的证据

### 第一步：决定 Workflow Profile

按 Workflow Profiles 章节的选择规则确定 profile。若已在 `task-progress.md` 中记录且仍在同一工作周期，沿用。

### 第二步：在 profile 约束下决定阶段

严格按以下顺序检查，但只路由到当前 profile 包含的节点：

1. 若当前工件已经记录了合法、可归一化且仍然有效的 `Next Action Or Recommended Skill`，优先进入该显式下一节点
2. 否则若用户明确提出紧急缺陷修复，或现有工件清楚表明当前处于热修复场景，优先进入 `ahe-hotfix`
3. 否则若用户明确提出需求变更、范围调整、验收标准变化，进入 `ahe-increment`
4. 若用户明确要求规格评审，且当前证据支持此时应评审规格，进入 `ahe-spec-review`（仅 full）
5. 若用户明确要求设计评审，且当前证据支持此时应评审设计，进入 `ahe-design-review`（仅 full）
6. 若用户明确要求任务评审，且当前证据支持此时应评审任务计划，进入 `ahe-tasks-review`（full / standard / lightweight）
7. 若用户明确要求测试评审 / 代码评审 / 追溯性评审 / 回归门禁 / 完成门禁，且当前证据支持此时应进入该能力，则进入对应 skill（需在当前 profile 节点链路内）
8. 若没有已批准需求规格，进入 `ahe-specify`（仅 full；若 standard / lightweight 检测到缺少规格依据，触发 profile 升级）
9. 若没有已批准实现设计，进入 `ahe-design`（仅 full；若 standard / lightweight 检测到缺少设计依据，触发 profile 升级）
10. 若没有已批准任务计划，进入 `ahe-tasks`（full / standard / lightweight）
11. 若仍有未完成计划任务，进入 `ahe-test-driven-dev`
12. 若当前任务已实现，但缺少缺陷模式排查证据，进入 `ahe-bug-patterns`（full / standard；lightweight 跳过）
13. 若当前任务缺少测试、代码或追溯性评审结论，依次进入 `ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`（full / standard；lightweight 跳过）
14. 若当前任务缺少回归验证证据，进入 `ahe-regression-gate`
15. 若当前任务缺少完成验证证据，进入 `ahe-completion-gate`
16. 否则进入 `ahe-finalize`

### Profile 感知的自动升级

在第 7-8 步中，如果 standard 或 lightweight profile 路由时检测到缺少规格或设计依据，不是直接跳过这些阶段，而是触发 profile 升级后再路由。

### 补充判定规则

- 若需求规格存在，但仍是草稿、评审未通过，或评审虽通过但缺少真人确认，仍进入 `ahe-specify`
- 若设计文档存在，但仍是草稿、评审未通过，或评审虽通过但缺少真人确认，仍进入 `ahe-design`
- 若任务计划存在，但批准状态不清楚，或与 `task-progress.md` 中的当前阶段冲突，按未批准处理，回到 `ahe-tasks`
- 若 `task-progress.md` 指向实现，但规格 / 设计 / 任务任一工件没有明确批准证据，优先相信上游工件状态，不能直接进入 `ahe-test-driven-dev`
- 若用户请求与工件状态冲突，先报告冲突，再选择保守的上游阶段
- 不把"评审通过但尚未真人确认"误判成"已批准"
- 若用户点名某个能力型 skill，但当前证据显示仍缺更上游工件或前置 review / gate，优先回到缺失的上游阶段，而不是机械执行点名 skill

## 后续编排规则

当 review / gate 完成后，不要凭记忆或主观感觉决定下一步，仍要依据结论、当前 profile 的迁移表和证据重新编排：

- 若结论为 `通过`，进入该节点在当前 profile 迁移表中的下一个 skill
- 若结论为 `需修改`，回到该节点对应的上游修订 skill
- 若结论为 `阻塞`，先补齐阻塞条件，再回到当前节点重试；若阻塞原因指向上游工件缺失，评估是否需要 profile 升级
- 若用户在 review / gate 过程中提出了新范围、新需求或紧急缺陷线索，优先重新判断是否切到 `ahe-increment` 或 `ahe-hotfix`

## 结果驱动迁移表

把 review / gate 结论视为显式迁移信号，而不是普通建议。

### full profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `ahe-spec-review` | `通过` | 规格真人确认 |
| `ahe-spec-review` | `需修改` / `阻塞` | `ahe-specify` |
| 规格真人确认 | 确认通过 | `ahe-design` |
| 规格真人确认 | 要求修改 / 未确认 | `ahe-specify` |
| `ahe-design-review` | `通过` | 设计真人确认 |
| `ahe-design-review` | `需修改` / `阻塞` | `ahe-design` |
| 设计真人确认 | 确认通过 | `ahe-tasks` |
| 设计真人确认 | 要求修改 / 未确认 | `ahe-design` |
| `ahe-tasks-review` | `通过` | `ahe-test-driven-dev` |
| `ahe-tasks-review` | `需修改` / `阻塞` | `ahe-tasks` |
| `ahe-test-driven-dev` | 实现完成 | `ahe-bug-patterns` |
| `ahe-bug-patterns` | `通过` | `ahe-test-review` |
| `ahe-bug-patterns` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-test-review` | `通过` | `ahe-code-review` |
| `ahe-test-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-code-review` | `通过` | `ahe-traceability-review` |
| `ahe-code-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-traceability-review` | `通过` | `ahe-regression-gate` |
| `ahe-traceability-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-regression-gate` | `通过` | `ahe-completion-gate` |
| `ahe-regression-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-completion-gate` | `通过` | `ahe-finalize` |
| `ahe-completion-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |

### standard profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `ahe-tasks-review` | `通过` | `ahe-test-driven-dev` |
| `ahe-tasks-review` | `需修改` / `阻塞` | `ahe-tasks` |
| `ahe-test-driven-dev` | 实现完成 | `ahe-bug-patterns` |
| `ahe-bug-patterns` | `通过` | `ahe-test-review` |
| `ahe-bug-patterns` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-test-review` | `通过` | `ahe-code-review` |
| `ahe-test-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-code-review` | `通过` | `ahe-traceability-review` |
| `ahe-code-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-traceability-review` | `通过` | `ahe-regression-gate` |
| `ahe-traceability-review` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-regression-gate` | `通过` | `ahe-completion-gate` |
| `ahe-regression-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-completion-gate` | `通过` | `ahe-finalize` |
| `ahe-completion-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |

### lightweight profile 迁移表

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `ahe-tasks-review` | `通过` | `ahe-test-driven-dev` |
| `ahe-tasks-review` | `需修改` / `阻塞` | `ahe-tasks` |
| `ahe-test-driven-dev` | 实现完成 | `ahe-regression-gate` |
| `ahe-regression-gate` | `通过` | `ahe-completion-gate` |
| `ahe-regression-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |
| `ahe-completion-gate` | `通过` | `ahe-finalize` |
| `ahe-completion-gate` | `需修改` / `阻塞` | `ahe-test-driven-dev` |

如果某个下游 skill 给出的结论无法映射到当前 profile 迁移表中的唯一下一推荐节点，则说明编排信息还不完整，应回到本 skill 重新判断，而不是自行补脑推进。

## 恢复编排协议

当某个节点完成后，按以下顺序恢复状态机：

1. 读取该节点的最新结论
2. 确认当前 workflow profile（从 `task-progress.md` 读取）
3. 若 `task-progress.md` 或等价工件已经写入合法或可归一化的 `Next Action Or Recommended Skill`，且它来自上一个已完成节点并与最新证据不冲突，优先采用这个显式下一步
4. 否则检查该结论对应的上游 / 下游迁移是否在当前 profile 迁移表中有明确规则
5. 根据当前会话上下文判断用户是否已经提出了新范围、新缺陷或新阻塞（基于已有信息判断，不主动询问用户）
6. 若有范围变化，优先判断是否切到 `ahe-increment`
7. 若有紧急缺陷，优先判断是否切到 `ahe-hotfix`
8. 若没有新的支线信号，则按当前 profile 迁移表进入唯一下一推荐节点

不要跳过第 2 步、第 3 步和第 4 步。

恢复编排完成后，若下一推荐节点不是暂停点（见"连续执行原则"），立刻在同一轮中进入该节点，不等待用户确认。

若该下一推荐节点是 review 节点，则“进入该节点”的含义是：按 `references/review-dispatch-protocol.md` 派发 reviewer subagent，并按 `references/reviewer-return-contract.md` 消费返回摘要，而不是在父会话内联执行 review。

## 路由失败模式与恢复

如果出现以下情况，不要继续凭感觉推进：

- **证据冲突**：不同工件指向不同阶段时，先报告冲突，再按保守原则回到更上游节点
- **路由抖动**：同一轮里在两个节点之间来回切换但没有新证据时，停止切换，明确说明缺少哪个决定性证据
- **迁移表缺口**：若某结论无法映射到唯一下一推荐节点，回到本入口重编排，而不是自行补脑
- **profile 不稳**：若新证据触发 upgrade 条件，先升级 profile 并写明原因，再继续路由
- **显式交接不可解析**：若 `Next Action Or Recommended Skill` 是自由文本、无法唯一归一化，明确忽略该值并按迁移表 + 工件证据继续编排

如果你已经连续两次因为同一类证据缺口而无法稳定路由，应明确把它报告为当前阻塞，而不是继续重复解释同一状态机判断。

## 什么叫"已批准"

不要只根据聊天记录推断"已批准"。优先寻找工件中的显式证据：

- 若 `AGENTS.md` 为当前项目声明了批准状态别名，优先按该别名判断
- `状态: 已批准`
- 兼容旧写法：`Status: Approved`
- 审批章节或评审记录
- 对规格和设计而言，还应能看出真人确认已经完成
- 进度记录、任务状态或验证记录中的阶段性标记

如果状态不清楚，就按"未批准"处理。

## 输出约定

路由判断是内部编排步骤，不是需要用户确认的独立消息。

完成路由后，将路由结论作为简短内联说明嵌入执行流中，然后立刻进入目标 skill。不要把路由结论作为独立消息发送后等待用户回复。

路由说明应包含：

1. 当前识别阶段
2. 选定的 Workflow Profile
3. 推荐的下一步 skill

仅在以下情况补充详细说明：

- 存在证据冲突
- 发生了 profile 升级
- 当前是 review / gate 后的恢复编排且跳转不直观

简洁示例（嵌入执行流中，不独立停顿）：

> 路由：full profile → `ahe-specify`（无已批准规格）

> 路由：lightweight profile → `ahe-tasks`（纯配置调整，但仍需最小任务计划与任务评审）

> 路由：standard profile，`ahe-code-review` 通过 → 进入 `ahe-traceability-review`

发出路由说明后，立刻进入目标 skill，不等待用户确认。若目标是 review 节点，则立刻派发 reviewer subagent。唯一例外：当路由结果指向暂停点（见"连续执行原则"）时，才需要等待用户输入。

## 风险信号

- 用户说"继续"，你却直接开始写代码
- 用户只说"帮我 review"，你却没先判断该进入哪个 review skill
- 用户已经点名某个 skill，你却没有核对它是否符合当前阶段和 profile
- 规格虽然存在，但仍是草稿，你却当成已批准
- 还没判断阶段，就先去读实现文件
- 因为图快，就直接把流程路由到实现阶段
- `task-progress.md` 和工件批准状态冲突时，你仍然选了更激进的下游阶段
- 没有热修复或变更证据，却擅自进入支线
- 已知缺少评审或门禁证据，却仍然继续往下游推进
- 用户声称"这个很简单"，你就直接选 lightweight，而没有根据实际信号判断
- standard / lightweight 执行中发现缺少上游依据，却不升级 profile

## 交接

一旦路由完成，就在同一轮中立刻进入对应 skill 并执行，不要先发送路由结论再等用户回复。

能力型 skill 负责完成本类检查；是否进入它、之后如何衔接下一个节点，由本入口统一负责。

当一个 skill 执行完成后，立刻按恢复编排协议判断下一步，并在同一轮中继续进入下一个 skill，直到遇到暂停点（见"连续执行原则"）。

凡是出现以下任一情况，都应回到本入口重新编排：

- 用户说"继续"
- 某个 review / gate 刚完成，需要决定下一步
- 用户提出新的范围变化或缺陷修复要求
- 当前证据与既有阶段判断发生冲突
- 需要进行 profile 升级

重新编排本身也遵循连续执行原则：编排完成后立刻进入目标 skill，不额外等待用户。
