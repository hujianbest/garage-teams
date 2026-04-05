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
| **standard** | 中等功能、已有规格+设计的功能扩展、非高风险 bugfix | `ahe-tasks` → `ahe-tasks-review` → `任务真人确认` → `ahe-test-driven-dev` → 完整质量层 → `ahe-finalize` |
| **lightweight** | 纯文档/配置/样式变更、低风险 bugfix（单文件、无接口变化） | `ahe-tasks` → `ahe-tasks-review` → `任务真人确认` → `ahe-test-driven-dev` → `ahe-regression-gate` → `ahe-completion-gate` → `ahe-finalize` |

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

profile 对应的合法节点集合、默认链路和结果驱动迁移表请阅读：`references/profile-node-and-transition-map.md`

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

每个 profile 的合法主链节点是该 profile 节点链路中包含的节点子集；支线节点 `ahe-increment` / `ahe-hotfix` 对所有 profile 通用。

在当前 profile 不包含的节点上推进，视为无效迁移，应回到最近一个有证据支撑的上游节点，或触发 profile 升级。

完整的合法节点集合、canonical route map 与结果驱动迁移表已下沉到：

- `references/profile-node-and-transition-map.md`

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

整条 workflow 链路默认以连续执行模式运行：一个节点完成后，自动判断下一个节点并立刻进入，直到命中明确 pause point。

完整的暂停点、非暂停点、连续执行红旗信号与路由失败模式已下沉到：

- `references/execution-semantics.md`

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

其中 reviewer 返回摘要里的 canonical handoff 字段统一使用 `next_action_or_recommended_skill`。

规则边界：

- review 记录由 reviewer subagent 负责落盘
- workflow 推进仍由父会话负责
- `规格真人确认`、`设计真人确认`、`任务真人确认` 始终由父会话负责
- gate 节点当前仍按原有方式执行，不在本轮协议内自动改成 verifier subagent

## 红旗信号

执行级路由红旗信号已下沉到 `references/execution-semantics.md`。

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
- `references/profile-node-and-transition-map.md`
- `references/execution-semantics.md`
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
- 保留节点 `规格真人确认`、`设计真人确认`、`任务真人确认` 仍然是合法值
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
8. 若规格评审已通过，但仍缺规格真人确认，进入 `规格真人确认`（仅 full）
9. 若设计评审已通过，但仍缺设计真人确认，进入 `设计真人确认`（仅 full）
10. 若任务评审已通过，但仍缺任务真人确认，进入 `任务真人确认`（full / standard / lightweight）
11. 若没有已批准需求规格，进入 `ahe-specify`（仅 full；若 standard / lightweight 检测到缺少规格依据，触发 profile 升级）
12. 若没有已批准实现设计，进入 `ahe-design`（仅 full；若 standard / lightweight 检测到缺少设计依据，触发 profile 升级）
13. 若没有已批准任务计划，进入 `ahe-tasks`（full / standard / lightweight）
14. 若仍有未完成计划任务，进入 `ahe-test-driven-dev`
15. 若当前任务已实现，但缺少缺陷模式排查证据，进入 `ahe-bug-patterns`（full / standard；lightweight 跳过）
16. 若当前任务缺少测试、代码或追溯性评审结论，依次进入 `ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`（full / standard；lightweight 跳过）
17. 若当前任务缺少回归验证证据，进入 `ahe-regression-gate`
18. 若当前任务缺少完成验证证据，进入 `ahe-completion-gate`
19. 否则进入 `ahe-finalize`

### Profile 感知的自动升级

在第 7-12 步中，如果 standard 或 lightweight profile 路由时检测到缺少规格或设计依据，不是直接跳过这些阶段，而是触发 profile 升级后再路由。

### 补充判定规则

- 若需求规格存在，但仍是草稿或评审未通过，仍进入 `ahe-specify`
- 若需求规格评审已通过但缺少真人确认，进入 `规格真人确认`
- 若设计文档存在，但仍是草稿或评审未通过，仍进入 `ahe-design`
- 若设计评审已通过但缺少真人确认，进入 `设计真人确认`
- 若任务计划评审已通过但缺少任务真人确认，进入 `任务真人确认`
- 若任务计划存在，但批准状态不清楚，或与 `task-progress.md` 中的当前阶段冲突，按未批准处理，回到 `ahe-tasks`
- 若 `task-progress.md` 指向实现，但规格 / 设计 / 任务任一工件没有明确批准证据，优先相信上游工件状态，不能直接进入 `ahe-test-driven-dev`
- 若用户请求与工件状态冲突，先报告冲突，再选择保守的上游阶段
- 不把"评审通过但尚未真人确认"误判成"已批准"
- 若用户点名某个能力型 skill，但当前证据显示仍缺更上游工件或前置 review / gate，优先回到缺失的上游阶段，而不是机械执行点名 skill

## 后续编排规则

当 review / gate 完成后，不要凭记忆或主观感觉决定下一步，仍要依据结论、当前 profile 的迁移表和证据重新编排：

- 若结论为 `通过`，进入该节点在当前 profile 迁移表中的下一个 skill
- 若结论为 `需修改`，回到该节点对应的上游修订 skill
- 若结论为 `阻塞`，且 reviewer 明确返回 `reroute_via_starter=true` 或 `next_action_or_recommended_skill=ahe-workflow-starter`，先回到本 skill 重编排
- 若结论为 `阻塞`，且没有显式要求重编排，先补齐阻塞条件，再回到当前节点或其上游修订 skill 重试；若阻塞原因指向上游工件缺失，评估是否需要 profile 升级
- 若用户在 review / gate 过程中提出了新范围、新需求或紧急缺陷线索，优先重新判断是否切到 `ahe-increment` 或 `ahe-hotfix`

详细的合法节点集合、canonical route map、结果驱动迁移表与恢复编排协议已下沉到：

- `references/profile-node-and-transition-map.md`

若 reviewer 返回摘要显式要求 `reroute_via_starter=true`，或把 `next_action_or_recommended_skill` 指向 `ahe-workflow-starter`，该显式重编排信号优先于默认迁移表。

什么算"已批准"、哪些证据不够、以及证据冲突时如何保守回退，统一参考：

- `references/routing-evidence-guide.md`
- `references/routing-evidence-examples.md`

## 输出约定

路由判断是内部编排步骤，不是需要用户确认的独立消息。

完成路由后，将路由结论作为简短内联说明嵌入执行流中，然后立刻进入目标 skill。不要把路由结论作为独立消息发送后等待用户回复。

最小输出应包含：

1. 当前识别阶段
2. 选定的 Workflow Profile
3. 推荐的下一步 skill

若目标是 review 节点，则立刻派发 reviewer subagent。若命中暂停点，才等待用户输入。

恢复编排后的交接语义与暂停点定义，统一参考 `references/execution-semantics.md`。

## 风险信号

常见的执行级风险信号、跳步借口和失败恢复，统一参考 `references/execution-semantics.md`。

## 交接

一旦路由完成，就在同一轮中立刻进入对应 skill 并执行，不要先发送路由结论再等用户回复。

能力型 skill 负责完成本类检查；是否进入它、之后如何衔接下一个节点，由本入口统一负责。

当一个 skill 执行完成后，立刻按恢复编排协议判断下一步，并在同一轮中继续进入下一个 skill，直到遇到暂停点。

恢复编排协议、暂停点与需要回到 starter 重编排的典型场景，请参考：

- `references/profile-node-and-transition-map.md`
- `references/execution-semantics.md`
