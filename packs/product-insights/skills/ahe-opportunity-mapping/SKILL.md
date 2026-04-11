---
name: ahe-opportunity-mapping
description: Turn evidence into JTBD, opportunities, and a prioritized wedge map. Use when you already have framing and insight signals and need to decide which user problem is most worth pursuing before inventing solution concepts.
---

# AHE Opportunity Mapping

## Overview

这个 skill 负责把上游 research 收敛成“先追哪个机会”。

它借鉴 JTBD 和 OST 思路，但目标不是画一棵漂亮树，而是避免：

- 把 solution 假装成 opportunity
- 同时追 10 个分散痛点
- 还没想清目标问题就开始 spec 和实现

## When to Use

在这些场景使用：

- 已经有 `insight-pack` 或相近 research 结论
- 需要从多个痛点中选一个优先机会
- 需要把 feature wishlist 退回到 problem / job 视角

不要在这些场景使用：

- 证据还不够，先回到 `ahe-insight-mining`
- 已选定机会，当前更缺概念方向，改用 `ahe-concept-shaping`

## Default Agents

按需读取并复用：

- `agents/product-thesis-advocate.md`
- `agents/product-contrarian.md`
- `agents/product-debate-referee.md`

## Workflow

按以下顺序执行。

### 1. 锁定 desired outcome

先写清：

- 希望改变什么产品 / 业务结果
- 为什么这是当前轮次的顶层 outcome

如果连 top outcome 都模糊，停下来补齐，而不是继续画机会图。

### 2. 提炼 JTBD

至少分别提炼：

- functional jobs
- social jobs
- emotional jobs

不要只写“用户想要一个更好的工具”。

### 3. 生成机会分支

机会应写成：

- 未满足的 progress
- 被阻碍的动作
- 重复出现的痛点
- 用户明确的 desire

不要写成：

- “做推荐算法”
- “上 AI 助手”
- “支持 dark mode”

如果一个“机会”只有一种实现方式，它大概率是 solution 伪装。

### 4. 为每个机会补齐 4 个判断维度

- 频率 / 强度
- outcome leverage
- 差异化空间
- 风险或依赖

### 5. 至少保留 3 个候选机会再收敛

除非证据极强，否则不要只剩一个机会。

### 6. 让 `Advocate` 为前 2 到 3 个候选机会建立 strongest case

至少说明：

- 为什么用户会优先为这个机会买单或改变行为
- 为什么它比其他机会更接近强 wedge
- 它成立需要哪些条件

### 7. 让 `Contrarian` 对这些候选机会做 PK challenge

至少挑战：

- 哪个机会只是 problem wording 更好看，但不更重要
- 哪个机会看起来有价值，但其实会落回 commodity 功能
- 哪个机会依赖太多前提，不适合当前轮次下注

### 8. 让 `Referee` 给出机会 PK verdict

至少输出：

- 候选机会排序
- `survive / park / drop`
- 为什么不选其他机会

### 9. 选择当前最值得下注的机会

优先选择：

- 用户痛感强
- outcome leverage 高
- 不是所有人都已经解决得很好
- 有形成 wedge 的空间

### 10. 落盘成 `opportunity-map`

默认使用：

- `ahe-product-skills/templates/opportunity-map-template.md`

至少补齐：

- `JTBD Summary`
- `Opportunity Branches`
- `Opportunity Ranking`
- `Selected Opportunity`
- `Debate Verdict`

## Quality Bar

高质量机会图至少应满足：

- 机会不是 solution 伪装
- outcome 清晰
- JTBD 不只停留在功能层
- 至少比较了多个机会
- 最终选中的机会有明确理由
- 至少留下基于多 agent PK 的不选理由

## Red Flags

- 机会写法本质上还是功能清单
- 没有 social / emotional job
- 只按“好不好做”排机会
- 没有说明为什么不选其他机会
- 多个候选机会没有经过正反对撞就直接拍板

## Recommended Next Step

默认下一步：

- `ahe-concept-shaping`
