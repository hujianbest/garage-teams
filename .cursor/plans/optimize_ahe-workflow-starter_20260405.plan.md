---
name: optimize ahe-workflow-starter
overview: 提升 `ahe-workflow-starter` 的可执行性与连续编排清晰度，重点补强路由交接载荷、状态结果、恢复前检查和适用范围边界，同时保持现有 profile、迁移表、暂停点和保守路由原则不变。
---

# 优化 `ahe-workflow-starter` 方案

## 目标

把 `skills/ahe-workflow-starter/SKILL.md` 从“规则完整的入口 skill”提升为“更容易稳定执行的 workflow 状态机入口”，降低路由歧义、恢复编排歧义和 handoff 漂移。

## 当前短板

- 路由规则和迁移表已经完整，但缺少一个更明确的“交给下一个 skill 时必须带什么信息”的交接载荷。
- 连续执行原则写得很强，但“无法唯一路由时该如何停下”缺少一个统一的结果状态词。
- `ahe-*` 系列中目前只有这个 skill 在扮演编排器角色，但“何时必须跑它、何时可视为已跑过”仍可以写得更清楚。
- 恢复编排协议存在，但缺少一个更靠近实际执行的“交接前检查”小清单，容易被模型心里跳过。

## 优化方向

### 1. 收紧 frontmatter 的触发描述

把 description 更明确地写成触发条件，而不是泛化介绍。

参考：

- `references/superpowers-main/skills/using-superpowers/SKILL.md`
- `references/longtaskforagent-main/skills/using-long-task/SKILL.md`

### 2. 增加“适用范围与例外”

明确说明：

- 什么时候必须经过 `ahe-workflow-starter`
- 下游 skill 在哪些前提下可以假定已经完成路由
- 不要把它理解成每个子步骤都要重新显式让用户确认的报告器

参考：

- `references/superpowers-main/skills/using-superpowers/SKILL.md`

### 3. 增加“路由交接载荷”

要求在进入下一个 `ahe-*` skill 之前，至少明确：

- 当前 profile
- 当前识别阶段 / 当前节点
- 触发这次迁移的主要证据
- 需要继续读取的核心工件
- 推荐下一步 skill

这样能让状态机从“只有结论”变成“有最小上下文契约的 handoff”。

参考：

- `references/longtaskforagent-main/skills/using-long-task/SKILL.md`
- `references/gstack-main/autoplan/SKILL.md`

### 4. 增加“路由结果状态”

加入统一状态，例如：

- `ROUTED`
- `BLOCKED`
- `NEEDS_CONTEXT`

用于约束“不能唯一迁移”时的行为，避免一边说保守，一边实际上继续往下游推进。

参考：

- `references/gstack-main/autoplan/SKILL.md`

### 5. 在恢复编排协议后补“交接前检查”

把恢复编排落成更接近操作的 checklist，例如：

- profile 是否仍有效
- 当前迁移是否在合法状态集合内
- 是否误跳过暂停点
- 是否出现新范围 / 热修复信号
- `task-progress.md` 的当前阶段与推荐下一步是否一致

参考：

- `references/gstack-main/autoplan/SKILL.md`
- `references/superpowers-main/skills/verification-before-completion/SKILL.md`

## 明确不做

- 不改现有 profile 定义
- 不改现有合法状态集合和结果驱动迁移表
- 不改变“路由后同轮自动进入下一个 skill”的连续执行原则
- 不引入 subagent 或新的外部状态文件

## 计划中的实际改动

- 收紧 frontmatter description
- 增加“适用范围与例外”
- 增加“路由交接载荷”
- 增加“路由结果状态”
- 增加“交接前检查”
- 只做必要的结构增强，不重写整份 `SKILL.md`

## 预期效果

- 更容易稳定恢复 workflow 编排
- 更不容易把路由结果误当成等待用户确认的独立汇报
- 下游 `ahe-*` skills 能获得更一致的最小上下文
- 在证据不足或冲突时，更容易停在正确的位置而不是误推进
