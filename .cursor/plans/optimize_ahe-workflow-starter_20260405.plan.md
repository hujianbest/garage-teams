# 优化 workflow router kernel 方案（归档）

> **Historical：** 本文件归档时的旧名见当前磁盘文件名，针对已移除的 **pre-split legacy 合并 router** skill。当前 canonical runtime 为 **`ahe-workflow-router`**；公开家族入口为 **`using-ahe-workflow`**。下文路径与对象在今日应读作对 **`skills/ahe-workflow-router/SKILL.md`** 的同类优化思路。

## 目标

把 `skills/ahe-workflow-router/SKILL.md`（计划撰写时位于 legacy 合并 router 目录下的同名入口）从“能工作的一套状态机说明”提升为“能稳定做出高质量路由 / 恢复编排决策的 workflow kernel skill”。

本次优化不会改变 AHE 的核心状态机事实：

- 仍然只有一个当前 workflow profile 和一个当前推荐节点
- 仍然由 `ahe-workflow-router` 统一拥有路由与恢复编排权
- 仍然遵守 `通过 | 需修改 | 阻塞` 的 review / gate 迁移语义
- 仍然保持非暂停点连续执行、暂停点等待用户
- 仍然以 `ahe-test-driven-dev` 作为实现阶段统一入口

## 当前问题

当前 `ahe-workflow-router`（计划撰写时的对象即 legacy 合并 router）已经信息很全，但还存在几个高价值短板：

- 核心状态机主要靠长篇线性文字表达，不够 glanceable
- 缺少一套显式的“决策分类”，导致证据冲突、边界场景时容易不一致
- 轻量 profile 的声明节点链路与迁移表之间仍有轻微不对齐感
- 对 stall / churn / 证据冲突等路由失败模式的恢复说明还不够显式
- 过多关键信息堆在一份大 SKILL.md 里，容易让执行时只读到局部

## 优化方向

### 1. 增加一张 canonical 路由图

用一张简明的 graph / route map 表达：

- full / standard / lightweight 三种 profile 的主链
- hotfix / increment 支线入口
- review / gate 通过与未通过后的回流方向

为什么这么改：

- 长文字虽然完整，但对于路由 skill 来说，视觉化的主骨架能显著降低跳步和误读概率

主要参考：

- `references/longtaskforagent-main/skills/using-long-task/SKILL.md`
- `docs/skills_refer.md`

### 2. 增加“决策分类”

显式区分：

- 机械决策：有明确工件证据，直接路由
- 保守决策：证据冲突时回更上游
- 必须暂停：命中 pause point
- 必须挑战：需要指出用户请求与当前工件证据冲突

为什么这么改：

- 这能让 router 在复杂恢复编排场景下更稳定

主要参考：

- `references/gstack-main/autoplan/SKILL.md`
- `skills/ahe-workflow-router/SKILL.md`

### 3. 补强 profile 与迁移表一致性

重点检查并补齐：

- lightweight profile 中 `ahe-tasks-review` 的迁移表达
- 各 profile 下 review / gate 的返回方向是否一一可映射

为什么这么改：

- 状态机里最怕“声明的节点链路”和“实际迁移表”有隐性空洞

主要参考：

- `skills/ahe-workflow-router/SKILL.md`

### 4. 增加路由恢复协议

显式说明常见失败模式：

- 证据冲突
- 路由来回抖动
- profile 判断不稳
- 当前节点缺少对应迁移规则

为什么这么改：

- 高质量 orchestration 不只是能路由，还要能在异常情况下稳定恢复

主要参考：

- `references/everything-claude-code-main/skills/continuous-agent-loop/SKILL.md`
- `skills/ahe-workflow-router/SKILL.md`

### 5. 强化优先级表达

明确：

- 先 branch，再 gate，再主链缺失工件判断
- 不能因为用户点名某个 skill 就绕过入口
- 不能因为“只是继续”就直接进入实现

为什么这么改：

- 这类优先级歧义是 router 最容易出错的地方之一

主要参考：

- `references/superpowers-main/skills/using-superpowers/SKILL.md`
- `skills/ahe-hotfix/SKILL.md`
- `skills/ahe-increment/SKILL.md`

## 明确不做的事

- 不重写整个状态机
- 不新增新的 workflow profile
- 不修改下游 skill 的核心职责边界
- 不把 router 变成另一个 planner skill

## 计划中的实际改动

会对 `skills/ahe-workflow-router/SKILL.md` 做一轮聚焦增强，预计包括：

- 增加 canonical 路由图
- 增加决策分类
- 强化优先级 / branch / pause point 表达
- 补齐轻量 profile 迁移表与恢复协议
- 收紧“何时必须回到 router”的失败模式说明

## 预期效果

优化后的 `ahe-workflow-router` 应该具备这些特征：

- 更像一个稳定可执行的状态机入口，而不是一篇很长的流程说明
- 在 “继续 / review 完成 / gate 回流 / 支线切换” 场景下更少走错
- 更容易让后续 `ahe-*` skill 的路由契约保持一致
