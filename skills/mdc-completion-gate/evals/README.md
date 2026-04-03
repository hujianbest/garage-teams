# 完成门禁评测

这个目录包含 `mdc-completion-gate` 的评测 prompts。

## 目的

这些评测用于验证完成门禁是否真正做到：

- 只认最新验证证据
- 拒绝没有 fresh verification evidence 的完成宣告
- 在证据不足时回到 `mdc-test-driven-dev`

## 建议评分关注点

1. 是否先明确要宣告的结论
2. 是否要求运行真正能证明该结论的命令
3. 是否在证据不足时拒绝通过
