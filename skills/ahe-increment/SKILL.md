---
name: ahe-increment
description: 在不绕过规格与设计纪律的前提下处理需求变更。适用于用户明确要求增删改需求、`ahe-workflow-starter` 已判定当前属于 increment 分支、或已批准范围 / 验收 / 约束发生变化、必须在继续实现前先完成高质量变更分析、失效判断、工件同步与 canonical handoff 的场景。本 skill 不直接推进实现，而是负责把增量变化安全带回 AHE 主链。
---

# AHE 增量变更

在不破坏主 AHE 流程的前提下处理需求变更。

## 角色定位

`ahe-increment` 负责四件事：

1. 判断当前变化是不是增量变更，而不是热修复或纯文案澄清
2. 固定当前 workflow 基线，形成结构化变更包与影响矩阵
3. 显式标记哪些批准、任务、验证证据和活跃任务已经失效
4. 同步受影响工件，并写回 canonical `Next Action Or Recommended Skill`

它的作用是防止“随手改需求”直接渗透到设计或实现层。

## 与 AHE 主链的关系

- 当前会话命中增量变更分支时，由 `ahe-workflow-starter` 路由到本 skill
- 本 skill 负责同步增量变化，不直接替代 `ahe-specify`、`ahe-design`、`ahe-tasks` 或 `ahe-test-driven-dev`
- 变更完成后的 canonical 下一步仍由当前父会话按 workflow 约定恢复编排；当当前父会话是 `ahe-workflow-starter` 时，由 starter 统一恢复下游节点
- 若 canonical 下一步是 review 节点，则执行方式是由当前父会话按 review dispatch protocol 派发独立 reviewer subagent；gate 节点仍由父工作流按当前 workflow 约定执行
- 如果发现当前并不是范围变化，而是“原本行为没有被正确实现”，应退出 increment 分支并回到 `ahe-hotfix`

## 高质量增量基线

高质量的 `ahe-increment` 结果，至少应满足：

- 开始前已经固定当前 profile、当前阶段、当前活跃任务和已批准工件基线
- 变更不只是口头描述，而是被整理成 `New / Modified / Deprecated` 的结构化变更包
- 受影响工件、失效批准、失效任务、失效验证证据被显式列出
- 只有最小必要的工件被更新，不把 increment 写成第二次从零规格化
- 回到主链时写的是 canonical `ahe-*` handoff，而不是自然语言阶段名
- 若变化已经超出当前 profile 或当前主链假设，明确记录 profile 升级信号

## Hotfix / Increment 快速判断

| 信号 | 更像 `ahe-increment` | 更像 `ahe-hotfix` |
|---|---|---|
| 问题本质 | 预期、范围、验收标准、约束发生变化 | 原本应成立的行为没有被正确实现 |
| 目标 | 重写变化后的正确目标与影响面 | 恢复既有目标下应成立的行为 |
| 下游去向 | 规格 / 设计 / 任务链刷新后再恢复主链 | 热修分析后交给 `ahe-test-driven-dev` 实现修复 |

如果你发现当前是在修实现缺陷，而不是改目标、改范围、改验收，不要继续把它当 increment 推进。

## 硬性门禁

不要从变更请求直接跳进编码。

任何变更都必须先分析它对规格、设计、任务计划、验证策略和已实现内容的影响。

如果变更会使已批准规格、设计、任务或当前活跃任务失效，先把失效项和影响包明确写回工件，再继续做最小必要同步；不要在证据仍稳定的情况下额外制造 pause point。

如果当前变化仍然含糊到无法稳定写成变更包，不要假装已经收敛完成；应显式记录歧义，并把下一步交回 `ahe-specify` 或 `ahe-hotfix`。

## 红旗信号

出现以下想法时，先停下。这通常说明你正在为“跳过变更同步”找理由：

| 想法 | 实际要求 |
|---|---|
| “这只是个小改动，直接改实现就好” | 只要需求、范围或验收标准变了，就先做影响分析。 |
| “先把代码改了，文档后面再补” | 变更必须先同步到正确工件，再决定是否继续实现。 |
| “这次应该只影响任务，不用看规格和设计” | 必须检查规格、设计、任务、验证策略和已实现内容的影响。 |
| “旧批准应该还能沿用，不用重审” | 只要实质内容变化，就必须重新判断批准是否仍然有效。 |
| “发布说明和进度记录不重要” | 只要用户可见结果或项目状态受影响，就要同步更新。 |
| “先推进，回头再决定回哪个阶段” | 变更完成后必须选定唯一正确的下一步阶段。 |
| “这更像实现修复，但先按 increment 走也没关系” | hotfix / increment 选错分支会直接污染后续工件和路由。 |
| “下一步先写成 `回到实现阶段`，starter 自己能懂” | `Next Action Or Recommended Skill` 优先写 canonical `ahe-*` skill ID。 |

## 前置条件

在以下情况下使用本 skill：

- 用户明确要求修改已批准范围或需求
- 现有规格、设计、任务或实现中已经出现实质性变更信号

## 参考资料

如果团队还没有统一的变更影响同步记录格式，可先使用以下模板：

- `references/change-impact-sync-record-template.md`

## 记录与状态要求

变更影响分析完成后，默认应将本次分析记录到项目的变更记录中；若没有专门路径，可至少同步到：

- `task-progress.md`
- 相关规格 / 设计 / 任务工件

先固定以下状态基线，再开始改动：

- `task-progress.md` 中的 `Workflow Profile`
- `task-progress.md` 中的 `Current Stage`
- `task-progress.md` 中的 `Current Active Task`
- 当前已批准规格 / 设计 / 任务工件
- 当前已存在的验证 / review 证据（如受影响）

如果变更影响了已批准工件，应明确记录：

- 哪些批准状态失效
- 哪些任务计划不再可执行
- 哪些测试设计、验证证据或 review 结论已经失效
- 哪些失效的 review 结论需要由父会话重新派发对应 reviewer subagent
- 当前活跃任务是否仍然有效；若失效，是否必须清空为待重选
- 当前阶段是否需要回退
- `task-progress.md` 中的 `Next Action Or Recommended Skill` 应该改成什么
- 是否出现需要升级 profile 的新信号

## 工作流

### 1. 固定当前基线并阅读变更请求

阅读：

- `task-progress.md`
- 当前 workflow profile 与当前阶段
- 变更请求本身
- 已批准需求规格
- 已批准设计
- 当前任务计划（如有）
- 若已有实现或已存在 review / gate 证据，读取最少必要的实现 / 验证上下文

明确：

- 具体变了什么
- 哪些内容仍然有效
- 哪些工件会受影响
- 当前活跃任务是否还可信
- 当前变化更像 increment 还是 hotfix

### 2. 形成结构化变更包与影响矩阵

把本次变化整理成至少以下结构：

- `New`
- `Modified`
- `Deprecated`

然后评估对以下内容的影响：

- 范围与需求
- 约束或验收标准
- 架构或接口
- 任务顺序与依赖
- 测试与验证策略
- 已完成实现

同时显式写出：

- 受影响工件
- 失效的批准状态
- 失效的任务 / Active Task
- 失效的测试设计 / 验证证据 / review 结论
- 是否出现 profile 升级信号

如果当前变化仍然太含糊，无法稳定写成 `New / Modified / Deprecated`，不要直接补脑继续；应把歧义记录清楚，并把下一步交回更合适的上游 skill。

### 3. 确认需要改哪些工件，以及哪些旧结论已失效

至少回答以下问题：

- 这次变化是否使原规格中的某些 FR / NFR / 约束条目不再成立？
- 这次变化是否使原设计中的关键决策、接口、边界或图示失效？
- 这次变化是否使原任务顺序、完成条件、测试设计种子或 `Current Active Task` 失效？
- 这次变化是否使已有实现、已有验证证据或已有 review 结论不再可信？

若答案是“会失效”，先把失效项明确写出来，再继续更新工件。

若某个 review 结论因本次变更失效，不要只写“需要重审”。应明确写出需要重新派发的 canonical review 节点，例如 `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`。

### 4. 更新正确的工件

用最小必要改动保持各类工件一致。

规则如下：

- 需求变更先落到需求规格
- 只有当需求变化影响“如何实现”时，才继续更新设计
- 只有当设计或范围变化影响执行时，才更新任务计划
- 当行为结论或风险边界变化时，要同步更新验证策略与完成依据
- 如果用户可见结果或项目状态受影响，也要同步更新发布说明和进度记录

如果变更规模已经大到不适合“增量同步”，应明确指出这一点，并把下一步改成更上游的重新规格化 / 重新设计 / 重新任务拆解，而不是继续假装是小步更新。

### 5. 做同步收口检查

确认以下问题已经被回答：

- 需求变化是否已经同步到了设计？
- 设计变化是否已经同步到了任务与验证策略？
- 失效的批准、任务、验证证据是否已经被显式标记？
- 当前活跃任务是否已经保留，或在必要时清空为待重选（而不是在这里直接重选）？
- 是否出现需要升级 profile 的新信号，并已经记录原因？
- 是否还需要回写发布说明、状态记录或交接信息？

### 6. 写回 canonical handoff 并回到正确阶段

更新完成后：

- 如果变化仍然含糊，需要重新收敛需求 -> `ahe-specify`
- 如果当前判断其实是实现缺陷修复 -> `ahe-hotfix`
- 如果规格变化过大，无法在本轮同步中稳定冻结新的规格草稿 -> `ahe-specify`
- 如果规格发生实质变化且需要重新评审 -> `ahe-spec-review`
- 如果设计变化过大，已不适合在 increment 中做就地同步 -> `ahe-design`
- 如果设计发生实质变化且需要重新评审 -> `ahe-design-review`
- 如果任务计划、活跃任务、测试设计种子或验证依据需要重新收敛 -> `ahe-tasks`
- 如果主要变化落在任务顺序、完成条件或验证策略 -> `ahe-tasks-review`
- 如果相关工件已保持一致、批准仍然有效、当前活跃任务仍可执行，且当前任务的测试设计种子与验证依据仍然有效 -> `ahe-test-driven-dev`

回流时应显式同步：

- `task-progress.md` 的 Current Stage
- `task-progress.md` 的 Workflow Profile（如出现升级信号）
- `task-progress.md` 的 Current Active Task：仅在原任务仍然有效时保留；若已失效则清空或标记 `pending reselection`
- `task-progress.md` 的 Pending Reviews And Gates（如受影响）
- `task-progress.md` 的 `Next Action Or Recommended Skill`

若 `Next Action Or Recommended Skill` 指向 review 节点，其含义是父会话或 `ahe-workflow-starter` 会按 review dispatch protocol 派发 reviewer subagent，而不是当前 increment 会话直接内联继续评审。

若本次 increment 只是使旧 review 结论失效，而相关工件已经同步到位，应把对应 canonical review skill 写成下一步，并显式要求重派 reviewer，而不是泛化成“需要重审”。

若同时有多个失效的 review 需要重派发，则将主 re-entry 节点写入 `Next Action Or Recommended Skill`，并在 `Pending Reviews And Gates` 或等价状态字段中列出其余仍需重派发的 review 节点。

主 re-entry 节点优先选择当前 canonical workflow 中最先应恢复的那个 review 节点；若存在同级候选，则选择最能解除当前阻塞的那个，并把其余节点继续写入 `Pending Reviews And Gates`。

## 输出格式

请严格使用以下结构：

```markdown
## 变更摘要

- 变更摘要
- 当前 workflow profile / 当前阶段
- 当前判断：真实 increment | 更像 hotfix | 仍需进一步规格化

## 变更包

- New
- Modified
- Deprecated

## 影响矩阵

- 受影响工件
- 失效的批准状态
- 失效的任务 / Active Task
- 失效的测试设计 / 验证证据 / review 结论
- 需重新派发的 reviewer / review 节点（如有）
- Profile 升级信号（如有）

## 同步更新项

- 更新项
- 明确不做的内容

## 状态回流

- `Current Stage`
- `Workflow Profile`
- `Current Active Task`（保留原值或写 `pending reselection`）
- `Pending Reviews And Gates`
- `Next Action Or Recommended Skill`
```

## 反模式

- 先改实现，后补文档
- 把需求变更误当成单纯任务调整
- 把实现缺陷误判成 increment，导致错分支
- 范围发生实质变化后，仍假定旧批准有效
- 让多个工件处于不同步状态
- 不显式标记失效的批准、任务或验证证据
- 没有完成影响分析，就提前回到实现阶段
- `Next Action Or Recommended Skill` 写成自由文本或自然语言阶段名
- 变更后不回写 `task-progress.md`，导致后续会话进入错误阶段

## 完成条件

只有在变更包已经形成、受影响工件与失效项已被同步或显式标记、并且已经写回 canonical `Next Action Or Recommended Skill` 以及必要状态字段后，这个 skill 才算完成。
