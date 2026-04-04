---
name: optimize ahe-tasks
overview: 提升 `ahe-tasks` 的可执行性与任务粒度控制，重点补强适用时机、文件触及表、任务级 DoD 与依赖顺序表达，同时保持现有 handoff 到 `ahe-tasks-review` 的契约不变。
---

# 优化 `ahe-tasks` 方案

## 目标

让 `ahe-tasks` 更稳定地产出可执行、可评审、可恢复的任务计划。

## 计划中的实际改动

- 收紧 description
- 增加适用时机
- 增加文件触及表要求
- 补强任务级 DoD / 验证方式 / 依赖顺序表达

## 预期效果

- 任务计划更容易被直接用于实现
- `ahe-tasks-review` 更容易判断粒度是否合理
