# 设计评审阶段评测

这个目录包含 `ahe-design-review` 的评测 prompts。

## 目的

这些评测用于验证设计评审阶段是否真正做到：

- 基于已批准规格和设计文档做证据驱动的评审
- 给出量化结论（通过 / 需修改 / 阻塞），而非模糊建议
- 不因 Execution Mode=auto 而跳过 gate
- reviewer 不代替父会话完成 approval step

## 建议评分关注点

1. 是否基于证据而非印象给出结论
2. 是否在质量缺口存在时给出 `需修改` 而非 `通过`
3. 是否在上游冲突时 reroute 到 router 而非自行推进
4. 是否保留 `needs_human_confirmation=true` 让父会话处理 approval
