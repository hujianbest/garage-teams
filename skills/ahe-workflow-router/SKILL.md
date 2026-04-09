---
name: ahe-workflow-router
description: 作为 AHE workflow 的 canonical runtime router，根据最新证据决定当前阶段、Workflow Profile、Execution Mode、branch 切换、review dispatch 与恢复编排。适用于 continue/推进、review 或 gate 刚完成、route 或 profile 不清、工件证据冲突、需要判断是否切到 `ahe-hotfix` 或 `ahe-increment`，或用户明确要求 `auto` 连续执行等必须做 authoritative workflow routing 的场景。
---

# AHE Workflow Router

## Overview

`ahe-workflow-router` 是 AHE workflow family 的 **runtime authority**。

它不是 public entry，也不是命令入口解释层。它的职责是根据最新证据决定：

- 当前 `Workflow Profile`
- 当前 `Execution Mode`
- 当前 canonical 节点
- 是否切到 `ahe-hotfix` 或 `ahe-increment`
- review 节点是否应派发 reviewer subagent
- review / gate 结论之后如何恢复后续编排

当前架构中：

- `using-ahe-workflow` 负责 public entry / family discovery
- `ahe-workflow-router` 负责 runtime routing / recovery
- runtime handoff 与 reviewer reroute 语义统一使用 `ahe-workflow-router` 与 `reroute_via_router`

## When to Use

在这些场景使用：

- 用户说“继续”“推进”“开始做”，且必须依据最新工件判断当前节点
- 某个 review / gate 刚完成，需要恢复后续编排
- 当前 route / stage / profile 不清
- 当前工件证据冲突，必须按保守原则回退
- 需要判断是否进入 `ahe-hotfix` 或 `ahe-increment`
- 某个 leaf skill 给出了显式 handoff，但你需要验证它是否仍然合法
- 当前推荐节点是 review 节点，需要派发 reviewer subagent

不要在这些场景使用：

- 新会话只是想进入 AHE，还处于 family discovery 阶段
- 命令入口只是在表达 `/ahe-*` 的高频意图
- 某个 leaf skill 的本地职责已经明确，且不需要重新判断 route

这些场景应先走：

- `skills/using-ahe-workflow/SKILL.md`

## Core Authority

`ahe-workflow-router` 负责以下 authority：

- 选择或升级 `Workflow Profile`
- 归一化并约束 `Execution Mode`
- 识别当前合法推荐节点
- 约束推荐节点必须位于当前 profile 的合法节点集合中
- 消费 review / gate / verification 结论
- 读取并验证 `Next Action Or Recommended Skill`
- 在当前任务的 `ahe-completion-gate` 通过后，判断是锁定新的 `Current Active Task` 继续实现，还是进入 `ahe-finalize`
- 决定是否恢复主链、切到支线，或命中暂停点
- 对 review 节点执行 review-dispatch protocol

不属于它的职责：

- 面向新会话解释 AHE family 的用途
- 把 `/ahe-*` 命令直接映射成 runtime authority
- 让 leaf skill 自己决定完整主链下一步
- 在父会话里内联执行 review 判断

## Workflow

按以下顺序工作。

### 1. 先确认当前是否属于 runtime routing

先问自己：

- 当前是在做 public entry discovery，还是在做 authoritative runtime recovery？

如果只是“用户刚进入 AHE，不知道该从哪开始”，先回到：

- `using-ahe-workflow`

如果当前已经是下列任一场景，继续留在本 skill：

- 需要恢复编排
- 需要做 profile 判断
- 需要消费 review / gate 结论
- 需要处理 evidence conflict
- 需要判断是否切支线

### 2. 读取最少必要证据

只读取完成路由所需的最少内容：

1. `AGENTS.md` 中与 `ahe-workflow` 相关的路径映射、批准状态别名、profile 规则和 auto mode policy
2. 用户当前请求
3. 已批准或未批准的规格 / 设计 / 任务工件状态，以及任务计划中的依赖 / ready 规则或独立 task board
4. `task-progress.md`（包括 `Workflow Profile`、`Execution Mode`、`Current Active Task` 与显式 handoff）
5. review / verification / release artifacts

路由阶段不要先做大范围代码探索。

如果证据冲突：

- 按未批准处理
- 选择更上游节点
- 必要时升级到更重 profile

### 3. 先判断是否命中支线

优先检查是否存在以下信号：

- 紧急缺陷修复 -> `ahe-hotfix`
- 需求变更、范围调整、验收标准变化 -> `ahe-increment`

支线信号优先于普通主链推进。

### 4. 决定 `Workflow Profile`

`Workflow Profile` 由 router 决定，不允许由用户或下游 skill 自行声称。

| Profile | 适用场景 |
| --- | --- |
| `full` | 无已批准规格或设计、架构/接口/数据模型变化、高风险模块、从头开始 |
| `standard` | 已有已批准规格+设计，需要新增任务；中等复杂度扩展或 bugfix |
| `lightweight` | 纯文档/配置/样式变化，或低风险单文件 bugfix，且无功能行为变化 |

判定规则：

1. 先执行 `AGENTS.md` 中的强制 profile 规则
2. 若 `task-progress.md` 中已有仍有效的 profile，沿用
3. 否则按当前证据选择最匹配的 profile
4. 若信号冲突，选择更重的 profile

升级规则：

- `lightweight` 可升级到 `standard` 或 `full`
- `standard` 可升级到 `full`
- 不允许降级

### 5. 决定 `Execution Mode`

`Execution Mode` 与 `Workflow Profile` 正交，不允许混写成复合 profile 值。

归一化顺序：

1. 用户当前请求中的显式模式要求（如“auto mode”“自动执行”“不用等我确认”）
2. `AGENTS.md` 中声明的默认模式与禁止 auto 的范围
3. `task-progress.md` 中已有且仍有效的 `Execution Mode`
4. 若以上都没有，默认 `interactive`

约束：

- `interactive`：approval step 需要等待用户输入
- `auto`：approval step 可由父会话按 policy 写 approval record 后自动继续
- 若当前范围、profile、模块或风险类型命中 `AGENTS.md` 中的 auto 禁止条件，不得继续假装 `auto` 仍然有效
- `auto` 只改变 pause / approval step 的处理方式，不删除 review、gate 或 approval 节点

### 6. 归一化显式 handoff

把 `Next Action Or Recommended Skill` 视为受控字段，而不是自由文本。

若当前工件已经写回显式下一步：

- 先检查它能否唯一归一化为合法 canonical 节点
- 再检查它是否仍与最新 evidence 一致
- 再检查它是否位于当前 profile 的合法节点集合内

只有全部满足时，才优先采用这个显式 handoff。

否则：

- 忽略无效 handoff
- 回退到迁移表和工件证据重新判断

### 7. 在当前 profile 下决定 canonical 节点

路由顺序始终遵守以下原则：

1. 支线信号优先于普通主链推进
2. review / gate 恢复优先于“继续做点实现”
3. 缺失上游已批准工件优先于进入下游能力
4. 若 evidence 冲突，选择更保守的上游节点或更重 profile
5. 当前任务完成后的 task reselection 优先于 finalize；只有在无剩余 ready / pending task 时才进入 `ahe-finalize`

然后：

- 若存在合法且仍有效的显式下一节点，优先采用
- 否则按当前 profile 的合法节点集合与默认迁移表决定唯一下一节点
- 若结论无法映射到唯一节点，重新路由，不要自行补脑推进

profile 合法节点集合与迁移表参考：

- `skills/ahe-workflow-router/references/profile-node-and-transition-map.md`

### 8. 处理 review / gate 恢复编排

当某个 review / gate 刚完成时：

1. 先读取最新结论
2. 再确认当前 `Workflow Profile`
3. 再确认当前 `Execution Mode`
4. 再检查显式 handoff 是否存在且仍有效
5. 若 `reroute_via_router=true` 或 handoff 明确要求重新编排，直接按 router authority 重判
6. 若 `conclusion=通过` 且 reviewer 摘要返回 `needs_human_confirmation=true`：
   - `interactive`：进入对应 approval 节点并等待用户确认
   - `auto`：先写 approval record，再继续进入该 approval 节点解锁后的下游节点
7. 若刚完成的是 `ahe-completion-gate`，先判断当前任务完成后是否仍有剩余任务：
   - 存在唯一 `next-ready task`：更新 `Current Active Task` 并进入 `ahe-test-driven-dev`
   - 不存在剩余 ready / pending task：进入 `ahe-finalize`
   - 候选不唯一、依赖状态冲突或 ready 判定不稳定：把它视为 hard stop，并按 router authority 报告需重判
8. 否则按当前 profile 的结果驱动迁移表恢复下一节点

若用户在恢复过程中提出了新的范围变化或紧急缺陷线索，优先重新判断是否切到：

- `ahe-increment`
- `ahe-hotfix`

### 9. review 节点必须派发 reviewer subagent

当当前推荐节点是 review 节点时：

- 不要在父会话里直接展开 review 判断
- 构造最小 review request
- 派发独立 reviewer subagent
- 消费结构化 reviewer summary
- 再由父会话决定下一步或 approval step

review dispatch 与 return contract 参考：

- `skills/ahe-workflow-router/references/review-dispatch-protocol.md`
- `skills/ahe-workflow-router/references/reviewer-return-contract.md`

### 10. 遵守连续执行、approval step 与暂停点规则

路由结论是内部编排步骤，不是独立用户交互。

因此：

- 若结果不是暂停点，立刻在同一轮进入目标 skill
- 若结果是 review 节点，立刻派发 reviewer subagent
- 若结果只是因为当前任务完成而回到 router 做 next-task reselection，且新的 `Current Active Task` 已唯一锁定，也要在同一轮继续进入 `ahe-test-driven-dev`
- 若结果是 approval step：
  - `interactive`：等待用户输入
  - `auto`：先写 approval record，再继续进入下游节点
- 只有命中明确 hard stop 时才等待用户输入或报告阻塞

暂停点、非暂停点与恢复失败模式参考：

- `skills/ahe-workflow-router/references/execution-semantics.md`

## Output Contract

最小输出必须包含：

1. 当前识别阶段
2. 选定的 `Workflow Profile`
3. 选定的 `Execution Mode`
4. 推荐的下一步 canonical skill

若当前路由结果是“completion gate 通过后重新锁定下一任务并继续实现”，还应显式写出新的 `Current Active Task`。

然后按以下规则处理：

- 若下一步是普通 leaf skill，立即进入它
- 若下一步是 review 节点，按 review-dispatch protocol 派发 reviewer subagent
- 若下一步是 approval step，则按 `Execution Mode` 决定等待确认还是先写 approval record 再继续
- 若下一步是 hard stop，才等待用户输入或报告阻塞

若当前 evidence 已经足以唯一决定下一步，优先使用紧凑输出：

1. `Current Stage`
2. `Workflow Profile`
3. `Execution Mode`
4. `Target Skill`
5. `Why`：只保留 1-2 条决定性证据

这里的标签只是当前回复的展示格式；若写回 handoff 或状态工件，仍使用现有 canonical schema。

在 clear case 中，不要再：

- 逐项回放所有未命中的 branch
- 复述整份 router authority 说明
- 为了看起来更谨慎，展开一长串其实无关的备选节点

router 的价值在于 authoritative decision，不在于每次都把整台 machine 重新讲一遍。

runtime canonical 写法统一为：

- `ahe-workflow-router`
- `reroute_via_router`

## Runtime Canonical Surface

runtime 参考资料 canonical 位置：

- `skills/ahe-workflow-router/references/`

因此当前阶段遵守：

- runtime handoff: `ahe-workflow-router`
- reviewer reroute field: `reroute_via_router`
- reference home: `skills/ahe-workflow-router/references/`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “用户已经点名某个 `ahe-*` skill 了，就不用再路由” | 点名 skill 不等于当前时机正确，router 仍要验证阶段和前置条件。 |
| “只是简单继续一下，不用重新判断 profile” | “继续”不等于实现阶段，必须绑定当前 evidence 重新判断。 |
| “用户说 auto，就等于可以跳过 approval step” | `auto` 只改变 approval step 的解决方式，不会删除 approval 节点，也不会放松 review / gate。 |
| “我先看看代码再决定更稳妥” | 路由阶段只读取最少必要证据，不先做大范围代码探索。 |
| “review / gate 已经做完了，下一步应该显而易见” | 结论必须通过迁移表、显式 handoff 与当前 profile 一起判定。 |
| “lightweight 看起来够了，先别升级” | 一旦缺上游依据或复杂度超出假设，就必须升级 profile。 |
| “我可以在父会话里顺手 review 一下” | review 节点的 canonical 执行方式是 reviewer subagent，不是父会话内联判断。 |

## Red Flags

- 在没有重新经过 router 的情况下，直接把会话从一个节点切到另一个节点
- 因为命令名或用户点名，就跳过 route / profile 判断
- 把 `using-ahe-workflow` 写进 runtime handoff
- 把 `ahe-workflow-router` 当成 public entry shell
- 在 route 阶段先做大范围代码探索
- 忽略 evidence conflict，继续沿用上一轮印象推进
- 把 `auto` 理解成“可以不写 approval record”
- 在父会话内联执行 review 判断
- 发现 profile 不再成立却不升级

## Supporting References

按需读取：

- `skills/using-ahe-workflow/SKILL.md`
- `skills/docs/ahe-workflow-entrypoints.md`
- `skills/ahe-workflow-router/references/profile-node-and-transition-map.md`
- `skills/ahe-workflow-router/references/execution-semantics.md`
- `skills/ahe-workflow-router/references/review-dispatch-protocol.md`
- `skills/ahe-workflow-router/references/reviewer-return-contract.md`

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 你已经确认当前是在做 runtime routing，而不是 public entry discovery
- [ ] 你已经基于最新 evidence 决定 `Workflow Profile`
- [ ] 你已经归一化当前 `Execution Mode`，并确认它没有违反当前 policy
- [ ] 你已经验证显式 handoff 是否合法、可归一化且仍有效
- [ ] 你已经把推荐节点约束在当前 profile 的合法节点集合内
- [ ] 若当前任务刚通过 `ahe-completion-gate`，你已经根据任务计划 / task board 决定是重选下一任务还是进入 `ahe-finalize`
- [ ] 若当前是 review 节点，你会派发 reviewer subagent，而不是在父会话里内联评审
- [ ] 若当前不是 hard stop，你会在同一轮继续执行；若命中 approval step，则按 `Execution Mode` 处理
- [ ] 你没有把 `using-ahe-workflow` 当成 runtime handoff
- [ ] 你已经统一使用 `ahe-workflow-router` 与 `reroute_via_router` 表达 runtime canonical 语义
