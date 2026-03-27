# 实现阶段评测

这个目录包含 `mdc-implement` 的评测 prompts。

## 目的

这些评测用于验证实现阶段是否真正做到：

- 读取当前活跃任务
- 先设计测试并等待确认
- 严格按 TDD 与 review/gate 顺序推进

## 建议评分关注点

1. 是否先对齐 `task-progress.md` 与当前活跃任务
2. 是否先输出测试设计并等待真人确认
3. 是否按顺序进入 `mdc-test-driven-dev` 和后续 review/gate
