---
name: ahe-workflow-starter
description: 兼容旧写法的 workflow alias。适用于旧文档、旧 handoff、旧 reviewer return 或用户仍明确提到 `ahe-workflow-starter` 的场景；一旦命中该别名，应立即把 public entry 需求转交给 `using-ahe-workflow`，或把 authoritative runtime routing 转交给 `ahe-workflow-router`，而不是继续把 starter 当作 canonical runtime contract。
---

# AHE Workflow Starter

## Overview

`ahe-workflow-starter` 现在是一个 **compatibility alias**，不再承担 canonical runtime contract。

当前迁移阶段里：

- `using-ahe-workflow` 是 public entry / family discovery
- `ahe-workflow-router` 是 canonical runtime router
- `ahe-workflow-starter` 只负责兼容旧入口、旧 handoff 与旧文档

这意味着：

- 读到旧写法 `ahe-workflow-starter` 时，仍然接受
- 写新的 runtime 语义时，不再优先写 `ahe-workflow-starter`

## When to Use

在这些场景使用本 alias：

- 旧文档仍指向 `ahe-workflow-starter`
- 旧 `Next Action Or Recommended Skill` 写成了 `ahe-workflow-starter`
- reviewer return 中出现 `reroute_via_starter=true`
- 用户明确说“用 starter”，但当前仓库已经进入迁移阶段

不要在这些场景继续停留在 starter：

- 新会话只是想进入 AHE workflow
- 命令入口只是表达 `/ahe-*` 的高频意图
- 当前需要 authoritative route / stage / profile 判断
- 当前需要恢复 review / gate 后续编排

## Alias Resolution Rules

### 1. 先判断当前属于哪一层

若当前只是：

- 新会话进入 AHE
- 命令入口解析
- family-level entry discovery

则转交给：

- `skills/using-ahe-workflow/SKILL.md`

若当前属于：

- continue / 推进
- review / gate 刚完成后的恢复编排
- route / stage / profile 判断
- evidence conflict
- branch 切换（`ahe-hotfix` / `ahe-increment`）

则转交给：

- `skills/ahe-workflow-router/SKILL.md`

### 2. 读旧值时接受 starter，写新值时优先 router

兼容读取：

- `Next Action Or Recommended Skill: ahe-workflow-starter`
- `next_action_or_recommended_skill = ahe-workflow-starter`
- `reroute_via_starter = true`

新的 runtime 写法应优先改为：

- `ahe-workflow-router`

不要再把新的 runtime handoff、reviewer summary 或 canonical reroute target 写成：

- `ahe-workflow-starter`

### 3. starter 不再展开完整状态机

本 alias 不再承载：

- profile 选择细则
- canonical route map
- 结果驱动迁移表
- review dispatch machine contract
- pause-point machine contract

这些 canonical 运行时规则现在由：

- `ahe-workflow-router`

负责。

### 4. 当前 reference 物理路径先不移动

迁移期内，以下 runtime reference 仍然暂存在 starter 目录下：

- `skills/ahe-workflow-starter/references/profile-node-and-transition-map.md`
- `skills/ahe-workflow-starter/references/execution-semantics.md`
- `skills/ahe-workflow-starter/references/review-dispatch-protocol.md`
- `skills/ahe-workflow-starter/references/reviewer-return-contract.md`

这代表的是“物理路径尚未迁移”，不代表 starter 仍是 canonical runtime authority。

## Correct Behavior

当本 alias 被命中时，正确行为只有两类：

1. 明确转交给 `using-ahe-workflow`
2. 明确转交给 `ahe-workflow-router`

不要在这里：

- 继续复制 router 的完整判断规则
- 把 starter 当成新的 public entry
- 把 starter 继续当成新的 runtime canonical name

## Output Contract

本 alias 的最小输出是：

- 说明当前命中的是 compatibility alias
- 说明下一步应转交到哪一层
- 然后立即转交到 `using-ahe-workflow` 或 `ahe-workflow-router`

新的 canonical 写法：

- public entry：`using-ahe-workflow`
- runtime router：`ahe-workflow-router`

迁移期兼容读取：

- `ahe-workflow-starter`

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “reference 还在 starter 目录里，所以 starter 还是 canonical” | 物理路径未迁移不等于语义权威未迁移。 |
| “用户都说 starter 了，就继续把所有逻辑都放这里吧” | alias 的职责是兼容旧写法，不是永久保留双重 authority。 |
| “既然 starter 还能读，那新 handoff 继续写 starter 也没关系” | read-time alias 兼容不等于 write-time canonical 仍是 starter。 |
| “starter 作为 alias，也可以顺手继续做 public entry discovery” | public entry discovery 已经属于 `using-ahe-workflow`，不应重新混回 starter。 |
| “router 太新了，先别转过去” | 本阶段新增 router 的目的就是收敛 canonical runtime contract。 |

## Red Flags

- 在 starter 里重新复制完整状态机
- 把新的 runtime handoff 写成 `ahe-workflow-starter`
- 把 starter 同时当作 public entry 和 runtime authority
- 因为旧文档还没清理完，就拒绝转交到 router
- 看到 `reroute_via_starter=true` 仍然继续停留在 alias，而不是交给 router

## Supporting References

按需读取：

- `skills/using-ahe-workflow/SKILL.md`
- `skills/ahe-workflow-router/SKILL.md`
- `skills/ahe-workflow-starter/references/profile-node-and-transition-map.md`
- `skills/ahe-workflow-starter/references/execution-semantics.md`
- `skills/ahe-workflow-starter/references/review-dispatch-protocol.md`
- `skills/ahe-workflow-starter/references/reviewer-return-contract.md`

## Verification

只有在以下条件全部满足时，这个 alias 才算正确：

- [ ] 你已经把 starter 识别为 compatibility alias，而不是 canonical runtime contract
- [ ] 你已经区分当前需求是 public entry 还是 runtime routing
- [ ] 若是 public entry，你会转交给 `using-ahe-workflow`
- [ ] 若是 runtime routing，你会转交给 `ahe-workflow-router`
- [ ] 你没有在 starter 中重新复制完整状态机
- [ ] 你没有把新的 runtime handoff 写成 `ahe-workflow-starter`
