# Eval: using-ahe-product-workflow

## 保护的行为 contract

1. 给定模糊产品想法，能正确路由到最合适的 product insight 节点
2. 不在 product insight scope 内的问题应被拒绝或转交
3. 输出使用 3 行快路径格式（classification / target / why）
4. 不跳过路由直接开始执行某个节点的工作

## 运行方式

```bash
# 使用 evals.json 中的 prompt 分别运行 with_skill 和 without_skill
# 对比输出是否满足 assertions
```
