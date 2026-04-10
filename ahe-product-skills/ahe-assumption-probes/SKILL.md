---
name: ahe-assumption-probes
description: Turn risky unknowns into cheap, disposable product probes with kill criteria. Use when a concept looks promising but key desirability, usability, viability, or feasibility assumptions still need evidence before you enter specs or implementation.
---

# AHE Assumption Probes

## Overview

这个 skill 的职责是在进入 `ahe-coding-skills` 之前，先暴露和缩小危险未知项。

它默认假设：

- 现在最缺的不是更多功能想法
- 而是更便宜、更残酷的 truth test

## When to Use

在这些场景使用：

- 已有 concept brief，但没有明确 kill criteria
- 你担心团队会直接把一个未经验证的方向送进实现
- 需要区分 desirability、usability、viability、feasibility 风险

不要在这些场景使用：

- 方向还没选清楚，先回到 `ahe-concept-shaping`
- 已经验证得足够充分，当前只差 handoff，改用 `ahe-spec-bridge`

## Default Agents

按需读取并复用：

- `agents/probe-designer.md`
- `agents/product-contrarian.md`

## Workflow

按以下顺序执行。

### 1. 先列出完整风险栈

至少区分：

- desirability：用户真的在乎吗
- usability：用户真的能顺畅完成吗
- viability：这件事对业务有价值吗
- feasibility：技术和流程上真的可行吗

### 2. 只选最危险的 1 到 3 个假设

不要一口气设计十几个 probe。

优先挑：

- 一旦被证伪，整条方向都要重来
- 或者会直接改变 scope 和 spec 写法

### 3. 为每个关键假设设计最便宜 probe

默认优先：

- 访谈脚本
- 人工 concierge
- 低保真原型
- fake door
- 单页叙事稿
- 局部技术 spike

不是所有问题都要写代码。

### 4. 明确 harsh truth

每个 probe 都应写清：

- pass 条件
- fail 条件
- 哪个结果会让你停止继续下注

如果 probe 没有 kill criteria，它大概率只是“给自己打气”。

### 5. 明确 disposal plan

默认把 probe 当 disposable artifact，而不是 proto-MVP。

### 6. 落盘成 `probe-plan`

默认使用：

- `ahe-product-skills/templates/probe-plan-template.md`

至少补齐：

- `Risk Stack`
- `Selected Probe`
- `Success / Failure`
- `Minimal Setup`

## Quality Bar

高质量 probe plan 至少应满足：

- 只针对少量高杠杆未知项
- 每个 probe 都能回答一个明确问题
- 有明确的 pass / fail / kill criteria
- 方案足够便宜，不会天然诱导团队继续硬做

## Red Flags

- probe 太大，已经接近做半个产品
- success criteria 全是模糊词
- 完全没有 failure threshold
- 所谓验证其实只是收集正反馈

## Recommended Next Step

若 probe 已完成或已有足够 bridge 信息，默认下一步：

- `ahe-spec-bridge`

若 probe 尚未执行，则先执行 probe，再回到本节点更新结果。
