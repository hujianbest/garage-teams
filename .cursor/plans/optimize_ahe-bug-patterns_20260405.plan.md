---
name: optimize ahe-bug-patterns
overview: 提升 `ahe-bug-patterns` 的 fallback 执行方式和专项排查边界，重点补强无 catalog 时的退化策略、模式标识和非目标说明，同时保持现有 tri-state 输出与 handoff 契约不变。
---

# 优化 `ahe-bug-patterns` 方案

## 目标

让 `ahe-bug-patterns` 在有无缺陷模式库两种情况下都更稳定地执行。
