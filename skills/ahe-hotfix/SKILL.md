---
name: ahe-hotfix
description: 在不放弃验证纪律的前提下处理紧急缺陷修复。适用于用户明确提出紧急修复、`ahe-workflow-starter` 已判定当前属于 hotfix 分支、或某个实现缺陷必须尽快修复但仍需遵守先复现、root cause 收敛、最小安全修复边界和 canonical handoff 的场景。本 skill 负责热修分析与交接，不直接替代 `ahe-test-driven-dev` 的实现职责。
---

# AHE 热修复

处理紧急缺陷，但不能绕过工程纪律。

## 角色定位

`ahe-hotfix` 负责三件事：

1. 判断当前是否真的是热修复，而不是增量变更或需求漂移
2. 固化复现证据、收敛 root cause，并定义最小安全修复边界
3. 把结果交接给唯一实现节点 `ahe-test-driven-dev`，或在不适合继续 hotfix 时回到 `ahe-increment` / `ahe-workflow-starter`

它不直接写生产代码，也不替代后续 `ahe-bug-patterns`、`ahe-regression-gate` 或 `ahe-completion-gate`。

## 与 AHE 主链的关系

- 当前会话命中紧急缺陷分支时，由 `ahe-workflow-starter` 路由到本 skill
- 若需要实际改代码，唯一实现节点仍是 `ahe-test-driven-dev`
- 实现完成后的 canonical 质量链恢复仍由当前父会话按 workflow 约定推进；当当前父会话是 `ahe-workflow-starter` 时，由 starter 统一编排并恢复下游节点
- 当 hotfix 进入实现并恢复后续质量链时，`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review` 等 review 节点应由当前父会话按 review dispatch protocol 派发独立 reviewer subagent；gate 节点仍由父工作流按当前 workflow 约定执行
- 若发现问题本质是需求 / 验收 / 范围变化，而不是实现缺陷，应退出 hotfix 分支并回到 `ahe-increment` 或 `ahe-workflow-starter`

## 高质量热修基线

高质量的 `ahe-hotfix` 结果，至少应满足：

- 不是凭直觉认定“要热修”，而是有明确缺陷信号和紧急性依据
- 在进入实现前，已经建立最小且可靠的复现路径
- 不是只描述症状，而是形成一句能被挑战的 root cause 结论
- 修复边界、blast radius、回滚 / feature flag 和监控关注点已经被显式收敛
- 分析阶段本身也有 fresh evidence，而不是只写推断
- 写回的 handoff 能被 `ahe-test-driven-dev` 和 `ahe-workflow-starter` 直接消费

## Hotfix / Increment 快速判断

| 信号 | 更像 `ahe-hotfix` | 更像 `ahe-increment` |
|---|---|---|
| 问题本质 | 已有预期 / 已有行为没有被正确实现 | 预期、验收标准或范围本身发生变化 |
| 目标 | 恢复原本应成立的行为 | 引入新行为、改规则、扩范围 |
| 处理方式 | 收敛最小安全修复 | 重新做影响分析、设计 / 任务调整 |

如果你发现当前其实是在改规则、改预期、改验收，而不是修实现缺陷，不要继续把它当热修推进。

## 硬性门禁

不要仅凭直觉打热修复。

必须先复现，再交接到 `ahe-test-driven-dev` 进入修复实现，再重新验证。

在 root cause 和最小安全修复边界没有确认前，不得把当前 hotfix 交接给 `ahe-test-driven-dev` 进入修复实现。

如果问题无法稳定复现，或证据不足以支持唯一下一步，不得假装已经准备好进入实现。

## Root Cause 规则

热修分析至少要收敛出以下链路：

- 现象
- 证据
- 当前假设
- 最小验证
- 已确认 root cause

规则：

- 一次只推进一个主要假设，不要同时追多个猜测
- 三次连续验证后仍无法确认 root cause，应暂停并报告阻塞，而不是继续猜
- “能绕过去”不等于“已经理解问题”

## TDD 规则

热修复必须遵守与实现阶段一致的 fail-first 纪律：先建立失败复现，并把测试设计种子交给 `ahe-test-driven-dev` 去执行最小安全修复。

除非当前问题明确无法立即自动化且该例外已被记录到仓库工件，否则不得在没有失败复现证据的情况下把当前 hotfix 推进到代码修改阶段。

## 红旗信号

出现以下想法时，先停下。这通常说明你正在为“紧急情况下跳过流程”找理由：

| 想法 | 实际要求 |
|---|---|
| “这是线上问题，先改了再说” | 热修复也必须先复现，再修复。 |
| “现在来不及写失败测试” | 能自动化时必须先建立失败证据。 |
| “症状已经很明显，不用确认 root cause 了” | 症状不是 root cause；进入实现前必须先收敛原因。 |
| “复现不稳定，但我先试着改一下” | 先记录证据缺口和阻塞，不要把猜测直接写进生产代码。 |
| “先把问题压住，回头再补验证” | 修复后必须立即重新验证，并进入后续门禁。 |
| “顺手把附近老问题一起清掉” | 只做与当前缺陷直接相关的最小安全修复。 |
| “这可能是预期变了，但先按热修处理” | 若本质是规则 / 范围变化，应退出热修分支。 |
| “测试没变，就不用走后续检查了” | 是否进入某个具体质量能力可按实际判断，但不能擅自省略必要的实现质量、追溯、回归和完成判断。 |
| “太急了，不用同步文档或状态” | 若缺陷暴露出工件已过时，稳定后仍需同步。 |
| “下一步先写一句自然语言，starter 自己会猜” | `Next Action Or Recommended Skill` 优先写 canonical `ahe-*` skill ID。 |

## 前置条件

在以下情况下使用本 skill：

- 用户明确要求紧急修复缺陷或上线前修复问题
- 现有工件、线上反馈或验证结果已经明确表明当前属于热修复场景

## 参考资料

如果团队还没有统一的热修复闭环记录格式，可先使用以下模板：

- `references/hotfix-repro-and-sync-record-template.md`

## 记录与状态要求

热修复过程中，至少应把关键信息落到以下工件之一：

- `docs/reviews/` 下的热修复记录
- 项目既有的缺陷修复记录
- `task-progress.md`

若已存在热修任务 ID、缺陷 ID 或线上事件记录，优先沿用，不自行新造一套命名。

修复稳定后，还应同步：

- `task-progress.md`
- 必要时 `RELEASE_NOTES.md`
- 必要时受影响的规格、设计、任务记录

若当前仍未进入实现，也要至少同步：

- `Current Stage`
- `Current Active Task` 或显式 hotfix-task 映射
- `Pending Reviews And Gates`
- 当前是否已完成复现
- 当前 root cause 是否已确认
- 当前最小修复边界与 out-of-scope
- 若已满足合法下游交接条件，再写 `Next Action Or Recommended Skill`

## 工作流

### 1. 阅读热修请求并固定上下文

阅读：

- 缺陷描述
- 环境 / 版本 / 提交信息（如果能拿到）
- 当前相关的规格、设计、任务上下文（如有）
- 已存在的失败证据

明确：

- 期望行为
- 实际行为
- 受影响区域
- 严重级别与紧急性理由

### 2. 建立最小且可靠的复现方式

优先建立最小且可靠的失败复现方式：

- 优先复用现有测试、现有验证入口或无需改文件的失败验证步骤
- 否则至少提供一个清晰的手工验证步骤，后续可再自动化

若判断需要新增自动化失败测试，把它记录为建议测试设计种子，交给 `ahe-test-driven-dev` 在真人确认后落地；不要在本 skill 内直接编辑测试文件。

在说“问题已确认存在”之前，至少留下：

- 命令或操作入口
- 运行环境
- 失败签名或关键异常
- 一段足以复用的证据摘要

在证明问题真实存在之前，不要把当前 hotfix 交给 `ahe-test-driven-dev` 开始修复实现。

#### 若无法稳定复现或问题间歇出现

不要硬进入实现。至少记录：

- 已尝试的复现步骤
- 仍然缺什么证据
- 当前最可能的触发条件
- 为什么此时不能安全进入代码修复
- 唯一下一步 skill（通常是 `ahe-workflow-starter`，再由它决定是否等待更多证据或改走其它分支）

### 3. 收敛 root cause 与最小安全修复边界

在进入实现前，至少完成：

1. 用现有证据提出一个当前最强假设
2. 设计一个最小验证来挑战这个假设
3. 根据验证结果收敛或否定假设
4. 给出一句已确认 root cause
5. 锁定本次最小安全修复边界

同时显式写明：

- 本次明确不做什么
- 可能影响哪些模块 / 文件 / 路径
- 是否有 feature flag、回滚手段或临时缓解策略
- 修复后应重点观察哪些监控或验证点

### 4. 交接到唯一实现节点

如需实际修改代码，唯一实现节点仍是 `ahe-test-driven-dev`。

进入该实现节点前，应把以下内容交接清楚：

- 当前 hotfix ID / Task ID（如有）
- 复现方式与失败签名
- 已确认 root cause
- 最小修复边界与 out-of-scope
- 建议优先验证的测试设计种子
- canonical `Next Action Or Recommended Skill`：通常是 `ahe-test-driven-dev`

`ahe-hotfix` 只负责把实现前上下文收敛好；真正的测试设计确认、Red-Green-Refactor 仍在 `ahe-test-driven-dev` 中完成。

`ahe-hotfix` 自身不新增第二个实现入口；它只负责限定复现范围、最小修复边界和需要回写的工件。

这里的交接只到唯一实现入口为止，不代表当前 hotfix 会话会继续内联完成后续 review / gate。

如果需要提前表达后续质量关注点，应把它们写成可被下游消费的证据、风险提示或 `Pending Reviews And Gates`，供 `ahe-test-driven-dev`、下游 reviewer subagent 和 gate 节点恢复使用；不要把当前会话描述成会顺手继续执行 `ahe-test-review`、`ahe-code-review`、`ahe-traceability-review` 或某个 gate。

除非确实是为了安全完成修复，否则不要顺手做机会式重构。

### 5. 写回 fresh evidence 并恢复后续编排

不要在本 skill 内部抢 starter 的恢复编排权。应在热修复记录和 `task-progress.md` 中至少写明：

1. 当前复现状态
2. 已确认 root cause 或当前证据缺口
3. 本次最小修复的范围边界
4. 最新分析 / 验证证据
5. 若已满足合法下游交接条件，再写 `Next Action Or Recommended Skill`

通常写法：

- 已准备进入实现：`ahe-test-driven-dev`
- 发现其实是需求 / 验收变化：`ahe-increment`
- 证据不足、无法继续稳定推进：在 `Blocked / Evidence Gap` 中写明，不伪造 `Next Action Or Recommended Skill`

后续质量链的恢复方式应理解为：

- `ahe-test-driven-dev` 完成后，由当前父会话或 `ahe-workflow-starter` 消费 canonical handoff
- 若下一步是 review 节点，则由父会话派发独立 reviewer subagent
- 若下一步是 gate 节点，则由父工作流按当前 workflow 约定执行，不在本 skill 中提前内联执行

若 hotfix 回流后需要标记多个待恢复的 review / gate，则将主 re-entry 节点写入 `Next Action Or Recommended Skill`，其余节点写入 `Pending Reviews And Gates`，由父会话按顺序恢复。

### 6. 必要时同步工件

如果该缺陷暴露出规格、设计、任务、发布说明或状态记录已过时或不正确，应在修复稳定后同步更新相关工件。

同步后还应明确：

- 当前热修已回流到主链的哪个阶段
- `task-progress.md` 中记录的下一步动作或推荐 skill 是什么
- 是否还需要后续 review / gate 之外的文档回写

## 输出格式

请严格使用以下结构：

```markdown
## 热修复摘要

- Hotfix ID / Task ID
- 严重级别与影响面
- 当前判断：真实 hotfix | 更像 increment | 证据不足暂停

## 复现方式

- 环境 / 提交 / 版本
- 复现步骤或命令
- 失败签名
- 最新证据摘要

## Root Cause

- 当前假设
- 已确认 root cause
- 若尚未确认，当前证据缺口

## 修复范围

- 最小安全修复边界
- 明确不做的内容
- Blast Radius
- 回滚 / Feature Flag / 缓解手段
- 建议优先验证的测试设计种子

## 状态同步

- 已更新工件
- `Current Stage`
- `Current Active Task` 或 hotfix-task 映射
- `Pending Reviews And Gates`
- 当前复现状态
- 当前监控 / 验证关注点
- Blocked / Evidence Gap（如有）

## 交接字段

- `Next Action Or Recommended Skill`: 仅在已经满足合法下游交接条件时填写，优先使用 canonical skill ID，例如：`ahe-test-driven-dev` | `ahe-increment`
- 若需提前标记后续质量链，写 canonical review / gate 节点名或 `Pending Reviews And Gates`，供父会话后续恢复；不要写成“当前会话继续评审 / 门禁”
```

## 反模式

- 先打补丁，后补解释
- 在没有失败复现证据时直接修改实现
- 在没有确认 root cause 时直接推进到代码修复
- 未先复现就声称问题已修复
- 明明无法稳定复现，却假装已经准备好进入实现
- 以“很紧急”为理由跳过回归检查
- 在热修复中夹带无关清理工作
- 把本应进入 `ahe-increment` 的范围变更偷偷包进热修
- 还没确认复现路径转绿，就提前宣称修复完成
- `Next Action Or Recommended Skill` 写成自由文本，导致 starter 难以恢复编排
- 热修做完后不更新 `task-progress.md`，导致主链状态失真

## 完成条件

只有在以下两种情况之一成立时，这个 skill 才算完成：

1. 已成功复现缺陷，确认 root cause，锁定最小修复边界，并把 fresh evidence 与合法的 `Next Action Or Recommended Skill` 写回仓库工件
2. 已明确记录“当前无法稳定复现或证据不足”的阻塞状态、证据缺口与状态同步字段，且没有伪造下游 handoff 或假装继续进入实现
