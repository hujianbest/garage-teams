# Bug Patterns 评测

## Protected Behavior Contracts

这些评测保护 `ahe-bug-patterns` 的以下行为契约：

1. **模式匹配必须基于当前代码变更**：不读代码变更就做模式检查是 red flag
2. **高风险模式必须记录**：发现 critical/important 命中但不在 findings 中记录是违规
3. **Verdict 唯一下一步**：不允许返回多个候选下一步
4. **"测试通过"不能跳过模式排查**：测试覆盖和缺陷模式检查是不同维度
