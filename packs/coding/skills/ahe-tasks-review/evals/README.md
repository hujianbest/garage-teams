# 任务计划评审评测

这个目录包含 `ahe-tasks-review` 的评测 prompts。

## 目的

这些评测用于验证任务计划评审是否真正做到：

- 给出明确 verdict（通过/需修改/阻塞）和唯一下一步
- 通过时保留 `needs_human_confirmation=true`
- `Execution Mode=auto` 不覆盖评审判断
- 上游冲突时 reroute 到 `ahe-workflow-router`

## 建议评分关注点

1. 是否给出明确结论和唯一下一步
2. 是否在 auto 模式下仍保留 approval step
3. 是否在上游冲突时正确 reroute
