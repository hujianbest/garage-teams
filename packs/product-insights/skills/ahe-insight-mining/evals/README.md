# Eval: ahe-insight-mining

## 保护的行为 contract

1. 给定 framing，能从多源提取信号并分类为 Observed/Inferred/Invented/Untested
2. 对信号做 thesis 提炼和 contrarian 挑战
3. 输出包含白空间方向和 no-go 信号
4. 若无 framing 工件，应 reroute 到 `ahe-outcome-framing`

## 运行方式

```bash
# 使用 evals.json 中的 prompt 分别运行 with_skill 和 without_skill
# 对比输出是否满足 assertions
```
