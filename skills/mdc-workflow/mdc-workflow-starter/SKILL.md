---
name: mdc-workflow-starter
description: 在 workflow 场景中先判断当前阶段，再把软件工作路由到正确位置。适用于需求、规格、设计、任务规划、实现、变更、缺陷修复等软件交付请求的起点，或用户说 continue/start/推进/继续开发、但当前阶段仍不清楚的场景。
---

# MDC 工作流入口

当当前软件交付工作仍需要判断阶段时，先使用这个 skill。

## 系列级入口规则

这个 skill 不是普通起始建议，而是 `mdc-*` workflow 的统一前置门。

只要当前请求属于软件交付流程中的任一场景，且你还需要判断当前阶段、核对工件状态、决定下一步，或恢复后续编排，就应先经过这里：

- 开始一个新需求、功能或项目
- 用户说“继续”“推进”“开始做”“先处理这个”
- 用户要求看代码、澄清需求、做设计、拆任务或直接实现
- 用户只要求做某种 review / gate，或明确点名某个 `mdc-*` 能力 skill
- 用户提出需求变更
- 用户提出紧急缺陷修复

如果当前阶段尚未完成这里的路由判断，就不要先进入下游 skill，也不要先开始推进主链或支线工作。

## 目的

你的职责不是直接实现，而是判断当前所处阶段、识别 workflow 中推荐的下一步 skill、决定后续编排顺序，并阻止乱序推进。

这个 skill 用于把软件作业按这套 skills 体系路由到正确阶段。

它是 workflow 的入口门禁：

`mdc-specify -> mdc-spec-review -> 规格真人确认 -> mdc-design -> mdc-design-review -> 设计真人确认 -> mdc-tasks -> mdc-tasks-review -> mdc-implement -> mdc-bug-patterns -> mdc-test-review -> mdc-code-review -> mdc-traceability-review -> mdc-regression-gate -> mdc-completion-gate`

变更请求和热修复会被路由到专门的支线流程。

## 编排职责

`mdc-workflow-starter` 不只负责“第一次进哪个 skill”，还负责在以下情况中恢复后续编排：

- 用户说“继续”，需要根据最新证据决定下一步
- 某个 review / gate 完成后，需要决定是回到上游修订，还是继续进入下一个质量节点
- 用户明确点名某个 `mdc-*` 能力 skill，但仍需要由 workflow 判断它是否是当前正确的下一步
- 主链、变更支线、热修复支线之间需要做受控切换

能力型 skill 只负责完成本类检查并给出结论；至于当前会话应不应该进入它、之后该进入哪里，由本 skill 统一编排。

## 状态机原则

把 `mdc-workflow` 视为一个由本 skill 驱动的轻量状态机，而不是一组可以随意挑选的能力说明：

- 任一时刻只允许存在一个**当前推荐节点**
- 当前推荐节点必须由最新工件证据、review / gate 结论和用户请求共同决定
- 下游 skill 不负责自行挑选下一步；它们只负责完成本节点职责并返回结论
- 任何新的用户请求、证据冲突、review / gate 结论、变更信号、热修复信号，都会触发本 skill 重新编排

如果你发现自己在没有重新经过本 skill 的情况下，就直接把会话从一个节点切到另一个节点，这通常说明你已经绕开了状态机。

## 合法状态集合

主链推荐节点只允许落在以下集合中：

- `mdc-specify`
- `mdc-spec-review`
- 规格真人确认
- `mdc-design`
- `mdc-design-review`
- 设计真人确认
- `mdc-tasks`
- `mdc-tasks-review`
- `mdc-implement`
- `mdc-bug-patterns`
- `mdc-test-review`
- `mdc-code-review`
- `mdc-traceability-review`
- `mdc-regression-gate`
- `mdc-completion-gate`
- `mdc-finalize`

支线推荐节点只允许落在以下集合中：

- `mdc-increment`
- `mdc-hotfix`

如果某个用户请求、口头描述或局部记录暗示跳到上述集合之外，按无效迁移处理，回到最近一个有证据支撑的上游节点。

## 状态转移来源

本 skill 只能依据以下四类输入决定迁移：

1. 当前用户请求
2. 已批准或未批准的工件状态
3. review / gate 结论
4. 进度记录、验证记录、发布记录中的阶段证据

不要把“我记得上轮已经做到这里了”当作合法输入。

不要把“某个 skill 看起来就很适合这个请求”当作合法输入。

## 铁律

在把会话正确路由到合适阶段之前，不要开始推进主链或支线工作。

如果有任何不确定，先解决“当前阶段是什么”这个问题。

对 workflow 场景而言，澄清、探索、读代码、review、gate、设计、任务拆解、实现都属于推进动作，推进之前必须先完成路由。

## 红旗信号

出现以下想法时，先停下。这通常说明你正在为“跳过流程”找理由：

| 想法 | 实际要求 |
|---|---|
| “这只是个简单请求，可以直接做” | 简单请求也要先判断当前阶段。 |
| “我先快速看看代码再说” | 先路由，再按目标 skill 的要求读代码。 |
| “我先多收集一点信息更稳妥” | 路由只读取最少必要证据，不先做大范围探索。 |
| “用户都说继续了，应该就是实现” | “继续”不等于实现，必须先检查规格、设计、任务和进度证据。 |
| “用户只是让我做 review，不算进入流程” | review / gate 请求也属于 workflow 编排的一部分，仍要先做路由判断。 |
| “文档大概已经齐了，先往下推进吧” | 没有明确批准证据，就按未批准处理。 |
| “这个流程太完整了，先跳一步节省时间” | 任何跳过规格、设计、任务、评审或门禁的行为都视为违规。 |
| “热修复很急，可以先改再补流程” | 热修复也必须先进入 `mdc-hotfix`，不能绕过复现、评审和门禁。 |
| “这是个小变更，不用走变更支线” | 只要是需求或范围变化，就先判断是否应进入 `mdc-increment`。 |
| “我已经知道现在在哪个阶段了” | 结论必须绑定当前工件证据，而不是依赖印象或聊天记忆。 |
| “用户已经点名某个 mdc skill，就不用再经过入口了” | 点名 skill 也不等于当前时机正确，仍要由本 skill 判断是否应进入它。 |
| “先做一点实现，后面再补 route 说明” | 路由必须先完成，之后才能进入下游 skill。 |

## `AGENTS.md` 扩展约定

在读取任何阶段证据之前，先检查项目根部或工作区约定中的 `AGENTS.md`。

若其中声明了 `mdc-workflow` 相关规则，优先读取：

- 工件路径映射
- 审批状态别名与 review 结论别名
- 真人确认的等价证据来源
- 进度记录、review、verification 的实际位置
- spec / design / tasks / review / verification 模板覆盖路径
- 团队级 coding / design / testing 规范

若 `AGENTS.md` 没有覆盖某一项，再回落到本 skill 和参考文档中的默认路径、默认状态词与默认模板。

## 优先读取内容

只读取完成路由所需的最少内容：

1. `AGENTS.md` 中与 `mdc-workflow` 相关的工件映射和团队约定（如果存在）
2. 当前需求、缺陷、变更或继续推进的用户请求
3. 现有已批准的规格、设计、任务工件，但只读取判断“是否存在、是否已批准”所需的最少内容
4. 当前进度记录、发布说明、评审记录、验证记录等可作为阶段证据的工件

路由阶段不要开始大范围探索代码库。

如果证据彼此冲突，采用保守原则：

- 按未批准处理
- 回到更上游的阶段
- 不因为某一条口头描述或孤立记录就继续往下游推进

## 附加资源

当项目的 `AGENTS.md` 还没有完整声明 `mdc-workflow` 映射，或交付件布局与阶段判断方式不清晰时，阅读以下参考文档：

- `references/routing-evidence-guide.md`

用它来先补齐 `AGENTS.md` 中的工件位置和阶段证据来源，避免后续工作流越来越混乱。

## 路由顺序

严格按以下顺序检查：

1. 若用户明确提出紧急缺陷修复，或现有工件清楚表明当前处于热修复场景，优先进入 `mdc-hotfix`
2. 否则若用户明确提出需求变更、范围调整、验收标准变化，进入 `mdc-increment`
3. 若用户明确要求规格评审，且当前证据支持此时应评审规格，进入 `mdc-spec-review`
4. 若用户明确要求设计评审，且当前证据支持此时应评审设计，进入 `mdc-design-review`
5. 若用户明确要求任务评审，且当前证据支持此时应评审任务计划，进入 `mdc-tasks-review`
6. 若用户明确要求测试评审 / 代码评审 / 追溯性评审 / 回归门禁 / 完成门禁，且当前证据支持此时应进入该能力，则进入对应 skill
7. 若没有已批准需求规格，进入 `mdc-specify`
8. 若没有已批准实现设计，进入 `mdc-design`
9. 若没有已批准任务计划，进入 `mdc-tasks`
10. 若仍有未完成计划任务，进入 `mdc-implement`
11. 若当前任务已实现，但缺少缺陷模式排查证据，进入 `mdc-bug-patterns`
12. 若当前任务缺少测试、代码或追溯性评审结论，依次进入 `mdc-test-review`、`mdc-code-review`、`mdc-traceability-review`
13. 若当前任务缺少回归或完成验证证据，进入 `mdc-regression-gate` 或 `mdc-completion-gate`
14. 否则进入 `mdc-finalize`

补充判定规则：

- 若需求规格存在，但仍是草稿、评审未通过，或评审虽通过但缺少真人确认，仍进入 `mdc-specify`
- 若设计文档存在，但仍是草稿、评审未通过，或评审虽通过但缺少真人确认，仍进入 `mdc-design`
- 若任务计划存在，但批准状态不清楚，或与 `task-progress.md` 中的当前阶段冲突，按未批准处理，回到 `mdc-tasks`
- 若 `task-progress.md` 指向实现，但规格 / 设计 / 任务任一工件没有明确批准证据，优先相信上游工件状态，不能直接进入 `mdc-implement`
- 若用户请求与工件状态冲突，先报告冲突，再选择保守的上游阶段
- 不把“评审通过但尚未真人确认”误判成“已批准”
- 若用户点名某个能力型 skill，但当前证据显示仍缺更上游工件或前置 review / gate，优先回到缺失的上游阶段，而不是机械执行点名 skill

## 后续编排规则

当 review / gate 完成后，不要凭记忆或主观感觉决定下一步，仍要依据结论和证据重新编排：

- 若结论为 `通过`，进入该节点在主链或支线中的下一个 skill
- 若结论为 `需修改`，回到该节点对应的上游修订 skill
- 若结论为 `阻塞`，先补齐阻塞条件，再回到当前节点重试
- 若用户在 review / gate 过程中提出了新范围、新需求或紧急缺陷线索，优先重新判断是否切到 `mdc-increment` 或 `mdc-hotfix`

默认主链编排如下：

`mdc-specify -> mdc-spec-review -> 规格真人确认 -> mdc-design -> mdc-design-review -> 设计真人确认 -> mdc-tasks -> mdc-tasks-review -> mdc-implement -> mdc-bug-patterns -> mdc-test-review -> mdc-code-review -> mdc-traceability-review -> mdc-regression-gate -> mdc-completion-gate -> mdc-finalize`

## 结果驱动迁移表

把 review / gate 结论视为显式迁移信号，而不是普通建议：

| 当前节点 | 结论 | 下一推荐节点 |
|---|---|---|
| `mdc-spec-review` | `通过` | 规格真人确认 |
| `mdc-spec-review` | `需修改` / `阻塞` | `mdc-specify` |
| 规格真人确认 | 确认通过 | `mdc-design` |
| 规格真人确认 | 要求修改 / 未确认 | `mdc-specify` |
| `mdc-design-review` | `通过` | 设计真人确认 |
| `mdc-design-review` | `需修改` / `阻塞` | `mdc-design` |
| 设计真人确认 | 确认通过 | `mdc-tasks` |
| 设计真人确认 | 要求修改 / 未确认 | `mdc-design` |
| `mdc-tasks-review` | `通过` | `mdc-implement` |
| `mdc-tasks-review` | `需修改` / `阻塞` | `mdc-tasks` |
| `mdc-bug-patterns` | `通过` | `mdc-test-review` |
| `mdc-bug-patterns` | `需修改` / `阻塞` | `mdc-implement` |
| `mdc-test-review` | `通过` | `mdc-code-review` |
| `mdc-test-review` | `需修改` / `阻塞` | `mdc-implement` |
| `mdc-code-review` | `通过` | `mdc-traceability-review` |
| `mdc-code-review` | `需修改` / `阻塞` | `mdc-implement` |
| `mdc-traceability-review` | `通过` | `mdc-regression-gate` |
| `mdc-traceability-review` | `需修改` / `阻塞` | `mdc-implement` |
| `mdc-regression-gate` | `通过` | `mdc-completion-gate` |
| `mdc-regression-gate` | `需修改` / `阻塞` | `mdc-implement` |
| `mdc-completion-gate` | `通过` | `mdc-finalize` |
| `mdc-completion-gate` | `需修改` / `阻塞` | `mdc-implement` |

如果某个下游 skill 给出的结论无法映射到唯一下一推荐节点，则说明编排信息还不完整，应回到本 skill 重新判断，而不是自行补脑推进。

## 恢复编排协议

当某个节点完成后，按以下顺序恢复状态机：

1. 读取该节点的最新结论
2. 检查该结论对应的上游 / 下游迁移是否有明确规则
3. 检查用户是否在此期间提出了新范围、新缺陷或新阻塞
4. 若有范围变化，优先判断是否切到 `mdc-increment`
5. 若有紧急缺陷，优先判断是否切到 `mdc-hotfix`
6. 若没有新的支线信号，则按迁移表进入唯一下一推荐节点

不要跳过第 2 步和第 3 步。

## 什么叫“已批准”

不要只根据聊天记录推断“已批准”。优先寻找工件中的显式证据：

- 若 `AGENTS.md` 为当前项目声明了批准状态别名，优先按该别名判断
- `状态: 已批准`
- 兼容旧写法：`Status: Approved`
- 审批章节或评审记录
- 对规格和设计而言，还应能看出真人确认已经完成
- 进度记录、任务状态或验证记录中的阶段性标记

如果状态不清楚，就按“未批准”处理。

## 输出约定

完成路由后，报告以下内容：

1. 当前识别阶段
2. 作出判断所依据的证据
3. 推荐的下一步动作或 skill
4. 缺失或阻塞的工件（如有）
5. 若存在证据冲突，说明采用了什么保守处理
6. 若当前是 review / gate 后的恢复编排，说明为什么进入这个后续节点

请用简洁表达。示例：

```markdown
当前阶段：需求尚未批准。

证据：
- 未发现已批准的需求规格
- 当前请求也未提供足以进入变更或热修复支线的证据

推荐的下一步动作或 skill：`mdc-specify`
```

## 风险信号

- 用户说“继续”，你却直接开始写代码
- 用户只说“帮我 review”，你却没先判断该进入哪个 review skill
- 用户已经点名某个 skill，你却没有核对它是否符合当前阶段
- 规格虽然存在，但仍是草稿，你却当成已批准
- 还没判断阶段，就先去读实现文件
- 因为图快，就直接把流程路由到实现阶段
- `task-progress.md` 和工件批准状态冲突时，你仍然选了更激进的下游阶段
- 没有热修复或变更证据，却擅自进入支线
- 已知缺少评审或门禁证据，却仍然继续往下游推进

## 交接

一旦路由完成，就立刻使用对应 skill，并严格遵循它。

能力型 skill 负责完成本类检查；是否进入它、之后如何衔接下一个节点，由本入口统一负责。

凡是出现以下任一情况，都应回到本入口重新编排：

- 用户说“继续”
- 某个 review / gate 刚完成，需要决定下一步
- 用户提出新的范围变化或缺陷修复要求
- 当前证据与既有阶段判断发生冲突
