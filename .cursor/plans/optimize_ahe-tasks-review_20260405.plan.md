---
name: optimize ahe-tasks-review
overview: 提升 `ahe-tasks-review` 的任务粒度、依赖顺序与实现前门禁清晰度，重点补强适用时机、DoD 检查和依赖/并行判断，同时保持现有 tri-state 输出和 handoff 契约不变。
---

# 优化 `ahe-tasks-review` 方案

## 目标

让 `ahe-tasks-review` 更稳定地判断任务计划是否真的可执行。

## 计划中的实际改动

- 收紧 description
- 增加适用时机
- 补强依赖顺序与任务级 DoD 检查
- 强化实现前门禁措辞
