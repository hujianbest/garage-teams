---
name: ahe-concept-shaping
description: Generate and challenge multiple product concepts, then converge on a sharper wedge. Use when a priority opportunity is clear but the solution direction still feels generic, overfamiliar, or too easy to copy.
---

# AHE Concept Shaping

## Overview

这个 skill 负责把“值得追的机会”变成“值得被记住的概念方向”。

它的核心任务不是选功能，而是回答：

- 哪个概念方向最有 pull
- 哪个方向最不容易沦为 category clone
- 哪个方向的 retained value 和传播逻辑更强

## When to Use

在这些场景使用：

- opportunity 已选好，但解法仍然泛泛
- 你需要提出多个 product concept，再收敛 wedge
- 你怀疑当前方向“看起来正确，但没有记忆点”

不要在这些场景使用：

- 机会还没选清楚，先回到 `ahe-opportunity-mapping`
- 关键未知项还没暴露，先完成概念初步收敛后再去 `ahe-assumption-probes`

## Default Agents

按需读取并复用：

- `agents/product-thesis-advocate.md`
- `agents/product-contrarian.md`
- `agents/product-debate-referee.md`
- `agents/wedge-synthesizer.md`

## Workflow

按以下顺序执行。

### 1. 先把 selected opportunity 写成一句人话

确保你能用 1 到 2 句话说明：

- 用户到底卡在哪一步
- 现有替代方案为什么不够好

### 2. 强制发散至少 3 个 concept direction

每个方向都要写：

- 一句话 pitch
- 主要价值
- 与现有常见做法的差异
- 为什么用户可能记得住

### 3. 让 `Advocate` 为每个方向写 strongest case

至少说明：

- 为什么用户会被这个方向吸引
- 如果它成立，真正的 wedge 是什么
- 为什么它可能比其他方向更有 pull

### 4. 对每个方向做 commodity challenge

至少问：

- 这个方向是不是只是在已有产品上加一层新外壳
- 这个方向最容易被复制的部分是什么
- 如果没有品牌光环，这个方向还有什么硬 wedge

### 5. 让 `Referee` 做 concept PK

至少输出：

- 哪些方向 `survive`
- 哪些方向 `park`
- 哪些方向 `drop`
- 每个被淘汰方向为什么出局

### 6. 补齐 surviving concepts 的 retained value 逻辑

每个候选方向至少回答：

- 用户第一次为什么会试
- 用户第二次为什么会回来
- 随着使用增加，价值会不会变强

### 7. 让 `wedge-synthesizer` 在 surviving concepts 上做最终收敛

要求：

- 不能跳过前面的 PK
- 必须明确为什么推荐方向胜过其他 surviving options

### 8. 选择当前推荐 wedge

推荐 wedge 不一定是最完整的方向，而是：

- 最有差异化
- 最有初始 pull
- 最能被便宜验证
- 最适合进入下一步 probe

### 9. 落盘成 `concept-brief`

默认使用：

- `ahe-product-skills/templates/concept-brief-template.md`

至少补齐：

- `Concept Directions`
- `Concept PK`
- `Recommended Wedge`
- `Loop / Retention Logic`
- `Scope Guess`

## Quality Bar

高质量 concept brief 至少应满足：

- 至少对 3 个方向做过比较
- 至少指出 1 个最容易平庸化的方向
- 推荐 wedge 清楚解释“为什么不是 clone”
- 能说出初始 value 和 retained value
- 至少留下 1 段多 agent PK 结论，而不是只写单人偏好

## Red Flags

- 所谓多个方向，其实只是同一方案换说法
- 推荐理由只有“容易做”或“功能多”
- 完全没有 retained value 逻辑
- 明明很像竞品 copy，却没有正面承认
- 还没经过 PK 就让 `wedge-synthesizer` 直接拍板

## Recommended Next Step

默认下一步：

- `ahe-assumption-probes`
