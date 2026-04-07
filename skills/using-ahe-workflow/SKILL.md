---
name: using-ahe-workflow
description: Provides the public entrypoint to the AHE workflow family. Use when starting a new AHE workflow session, deciding which `ahe-*` skill to enter, interpreting `/ahe-*` command intent, or when the user wants to continue, review, build, or close out work but the correct node is not yet obvious. Prefer this skill before guessing between direct invoke and workflow routing.
---

# Using AHE Workflow

## Overview

这个 skill 是 AHE workflow family 的公开入口层。

它负责降低“现在到底该从哪个 AHE 节点进入”的认知摩擦，但**不替代** runtime 路由 authority。它的职责是帮助你在以下两种模式之间做出正确选择：

- `direct invoke`：当前节点已经足够明确，直接进入某个 leaf skill
- `route-first`：当前阶段、profile、分支或证据仍不稳定，先交给当前 runtime router

当前迁移阶段里，runtime router 已经收敛为：

- `ahe-workflow-router`

也就是说，这个 skill 现在是 **public shell**，不是 **authoritative router**。

## When to Use

在这些场景使用：

- 刚开始一个新的 AHE 工作周期，不确定先从哪个 `ahe-*` skill 进入
- 用户说“继续”“推进”“开始做”“先处理这个”，但你还没确认当前 canonical 节点
- 用户想用 `/ahe-spec`、`/ahe-build`、`/ahe-review`、`/ahe-closeout` 这类命令意图进入 AHE
- 用户点名某个 `ahe-*` skill，但你需要先判断这是不是合法 direct invoke
- 你需要快速判断“现在应该直接进 leaf skill，还是先回到 router”

不要在这些场景使用：

- 你已经在某个 leaf skill 内部，且当前节点职责与输入都清楚
- 你已经确认需要 authoritative route / stage / profile 判断，此时直接交给 `ahe-workflow-router`
- 你已经确认当前就是某个 leaf skill 的本地职责，且该 skill 的 standalone contract 已满足

常见触发信号：

- “AHE 这次该从哪开始？”
- “继续这个 workflow”
- “先帮我走 AHE”
- “这个请求该进 `ahe-specify` 还是先路由？”
- “/ahe-review code TASK-003”

## Workflow Discovery

按以下顺序工作。

### 1. 先判断你现在是在做 entry，还是在做 runtime recovery

先问自己一个问题：

- 当前需求是“帮助用户进入 AHE”，还是“根据现有工件恢复正在运行的 workflow”？

如果更像下面这些情况，说明你应该先用本 skill：

- 新会话刚开始
- 用户只表达了高层意图，没有明确当前节点
- 用户想用某个 `/ahe-*` 命令，但命令只是 bias，不是 authority
- 你需要在 direct invoke 和 route-first 之间做选择

如果更像下面这些情况，说明你不应继续停留在本 skill，而应直接交给当前 router：

- review / gate 刚完成，需要恢复后续编排
- 当前阶段、profile、批准状态或 evidence 冲突，需要 authoritative 判断
- 需要决定是否切到 `ahe-hotfix` 或 `ahe-increment`
- 需要消费 review return、gate 结论或状态工件来决定下一步

当前这些 authoritative runtime 情况，统一交给：

- `ahe-workflow-router`

### 2. 识别请求的主意图

把当前请求优先归到以下类别之一：

- 新需求 / 新功能 / 新工作周期
- 继续推进现有 workflow
- review-only
- gate-only
- 当前活跃任务实现
- 规格相关工作
- hotfix 分析
- increment 分析
- closeout / finalize

这一步的目标不是立刻决定下一节点，而是先判断：

- 当前更像 entry bias
- 还是更像必须交给 router 的 runtime decision

### 3. 判断是否允许 direct invoke

只有当以下条件同时满足时，才 direct invoke 某个 leaf skill：

1. 当前节点已经足够明确
2. 当前请求确实属于该 skill 的本地职责
3. 最少必要工件已经存在且可读
4. 不存在 route / stage / profile 冲突
5. 调用方接受“该 skill 只完成本节点职责，后续编排不由它决定”

如果任一条件不满足，不要赌 direct invoke，直接把 authoritative 判断交给：

- `ahe-workflow-router`

### 4. 应用 family entry bias

默认偏向如下：

| 用户意图 | 可优先尝试的入口 | 一旦不明确时回哪里 |
| --- | --- | --- |
| 规格澄清 / 规格修订 | `ahe-specify` | `ahe-workflow-router` |
| 当前活跃任务实现 | `ahe-test-driven-dev` | `ahe-workflow-router` |
| review / gate 请求 | 具体 review / gate skill | `ahe-workflow-router` |
| closeout / finalize | `ahe-completion-gate` 或 `ahe-finalize` | `ahe-workflow-router` |
| 线上问题修复分析 | `ahe-hotfix` | `ahe-workflow-router` |
| 范围 / 验收 / 约束变化分析 | `ahe-increment` | `ahe-workflow-router` |

### 5. 解释 `/ahe-*` 命令时，把命令当作 bias，不当作 authority

对命令意图的默认解释：

- `/ahe-spec`：偏向 `ahe-specify`
- `/ahe-build`：偏向 `ahe-test-driven-dev`
- `/ahe-review`：偏向某个具体 review / gate skill
- `/ahe-closeout`：偏向 `ahe-completion-gate` 或 `ahe-finalize`

但命令不能替代工件检查、route 判断或 profile 判断。

因此：

- 若节点足够明确，可 direct invoke 对应 skill
- 若节点不明确、证据冲突或 profile 不稳，交给 `ahe-workflow-router`

### 6. 正确结束本 skill

本 skill 的正确输出只有两类：

1. 明确进入一个合法 leaf skill
2. 明确交给 `ahe-workflow-router`

不要在这里：

- 自己展开完整 transition map
- 自己决定 review return 之后的恢复编排
- 自己把 `using-ahe-workflow` 写进 `Next Action Or Recommended Skill`

## Core Operating Rules

### Rule 1. `using-ahe-workflow` 是 public entry，不是 runtime handoff

它适合作为：

- 新会话的 family 入口
- 命令入口的解释层
- “现在先用哪个 AHE skill” 的发现层

它不适合作为：

- `Next Action Or Recommended Skill`
- reviewer return 的 `next_action_or_recommended_skill`
- gate / transition map 的 canonical 下一节点

### Rule 2. authoritative routing 仍归 router

当前迁移阶段中，canonical router 是：

- `ahe-workflow-router`

因此，所有以下问题都不应由本 skill 私自决定：

- 当前 profile 是什么
- 当前 canonical 节点是什么
- 该不该切到 `ahe-hotfix` 或 `ahe-increment`
- review 节点是否应立即派发 reviewer subagent
- review / gate 结论之后该恢复到哪里

### Rule 3. direct invoke 失败时，宁可 route-first，也不要赌

如果你有一丝疑问“当前节点到底清不清楚”，默认交给：

- `ahe-workflow-router`

不要为了看起来更快，就把 entry skill 变成简化版 router。

## Entrypoint Matrix

| 情况 | 首选动作 | 原因 |
| --- | --- | --- |
| 新会话，不知道从哪开始 | 用本 skill 做 entry discovery | 先判断是 direct invoke 还是 route-first |
| 用户说“继续”但当前阶段不明 | 交给 `ahe-workflow-router` | 这是 runtime recovery，不是简单 entry bias |
| 用户说“帮我写 spec”且上下文明确 | direct invoke `ahe-specify` | 当前职责明确，适合 leaf skill |
| 用户说“帮我 review 一下”但对象不明确 | 交给 `ahe-workflow-router` | review-only 也需要 authoritative 节点判断 |
| 用户说“按 TDD 做当前 active task”且前置齐全 | direct invoke `ahe-test-driven-dev` | 节点清楚且本地输入足够 |
| 用户说“completion gate 过了，帮我收尾”且 gate 记录存在 | direct invoke `ahe-finalize` | 当前职责明确 |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “反正最终都会走 starter，我就别加这个入口层了” | 这个 skill 的职责是降低 entry friction，而不是复制 router。 |
| “用户点名了某个 `ahe-*` skill，就直接进去吧” | 点名 skill 不等于当前时机正确，仍要先判断能否合法 direct invoke。 |
| “我大概知道现在在哪个节点，不用再交给 router” | 只要 route / stage / profile 不稳，就应交给 authoritative router。 |
| “把 `using-ahe-workflow` 也写进 handoff 会更统一” | public entry 和 runtime handoff 不是同一层语义。 |
| “既然我已经在做 entry，不如顺手把 transition map 也判断了” | 这会把本 skill 重新写成第二个 starter。 |

## Red Flags

- 把 `using-ahe-workflow` 写成完整状态机
- 在 route 不清时硬做 direct invoke
- 把 `using-ahe-workflow` 写进 `Next Action Or Recommended Skill`
- 因为用户点名 leaf skill，就跳过工件检查
- 在 review / gate 完成后仍停留在本 skill 里做恢复编排
- 在本 skill 中复制 `ahe-workflow-router` 的 transition map 或 pause-point rules

## Supporting References

按需读取：

- `docs/ahe-workflow-entrypoints.md`
- `docs/ahe-command-entrypoints.md`
- `docs/ahe-workflow-shared-conventions.md`
- `skills/ahe-workflow-router/SKILL.md`

读取规则：

- 需要理解 public entry 与 direct invoke 边界时，先看 `docs/ahe-workflow-entrypoints.md`
- 需要解释 `/ahe-*` 命令时，读 `docs/ahe-command-entrypoints.md`
- 需要 authoritative runtime routing 时，进入 `skills/ahe-workflow-router/SKILL.md`
- 不要为了 entry discovery 在这里复制 starter 的 runtime rules

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 你已经先判断当前是在做 public entry，还是 runtime recovery
- [ ] 你已经明确区分“可 direct invoke”与“必须 route-first”
- [ ] 若节点已明确，你进入了合法 leaf skill
- [ ] 若节点不明确、证据冲突或 profile 不稳，你把 authoritative 判断交给了 `ahe-workflow-router`
- [ ] 你没有把 `using-ahe-workflow` 写入任何 runtime handoff 字段
- [ ] 你没有在本 skill 中复制或取代 router 的 machine contract
