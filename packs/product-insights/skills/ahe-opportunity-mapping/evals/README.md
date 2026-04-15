# Eval: ahe-opportunity-mapping

## 保护的行为 contract

1. 给定 insight-pack，能提炼 JTBD（至少 3 层：functional/social/emotional）
2. 生成的机会是 problem 语言而非 solution 语言
3. 通过多 agent PK 对至少 3 个候选机会做排序
4. 若无 insight 工件，应 reroute 到 `ahe-insight-mining`

## 运行方式

```bash
# 使用 evals.json 中的 prompt 分别运行 with_skill 和 without_skill
# 对比输出是否满足 assertions
```
