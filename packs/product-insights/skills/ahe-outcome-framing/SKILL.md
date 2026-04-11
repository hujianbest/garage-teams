---
name: ahe-outcome-framing
description: Reframe a vague product idea into a sharper outcome, target user, current substitute, and focus question. Use when an idea still sounds like “build an app for X,” when a shipped product feels generic, or when you need to diagnose why a concept lacks pull before doing research or specs.
---

# AHE Outcome Framing

## Overview

这个 skill 的职责不是帮用户“想几个功能”，而是把模糊 idea 重写成一个更锋利的问题定义。

它优先回答：

- 谁的哪段 progress 被卡住了
- 他们现在用什么 workaround 或替代品
- 这件事如果解决，会带来什么 outcome
- 当前 idea 最容易 commodity 化的地方是什么

## When to Use

在这些场景使用：

- 用户只有一个宽泛品类想法
- 用户说项目“普通”“没有吸引力”
- 你需要先把问题写锋利，再决定查什么
- 你怀疑当前讨论还停留在 solution-first

不要在这些场景使用：

- 已有清晰 outcome 和用户 progress，当前更缺 evidence，改用 `ahe-insight-mining`
- 已有足够 framing，当前需要机会排序，改用 `ahe-opportunity-mapping`

## Output Goal

默认产出一份更清晰的 `problem / outcome frame`，可作为后续 insight pack 的起点。

## Workflow

按以下顺序执行。

### 1. 先把当前 idea 还原成一句“未经打磨的原始说法”

例如：

- “做一个摄影社区”
- “做一个 AI 创业工具”
- “做一个 xx 管理平台”

不要假装这已经是好问题定义。

### 2. 强制改写成 outcome 语言

至少补齐：

- 目标用户是谁
- 他们在什么情境下遇到问题
- 现在怎么凑合解决
- 如果这件事被解决，会改善什么 outcome

### 3. 识别当前 framing 的 commodity 风险

至少检查：

- 这是不是一个“任何人都能说”的大类目
- 它是不是只描述了工具形态，没有描述 progress
- 它是不是没有说明为什么现在值得做
- 它是不是没有说清为什么用户不会继续用现有替代品

### 4. 生成多个 framing，而不是只保留一个

至少提出 3 个候选 framing：

- `pain-first`
- `progress-first`
- `wedge-first`

每个 framing 都应说明：

- 一句话问题定义
- 目标用户
- outcome
- 最大风险

### 5. 选择当前最值得继续研究的 framing

优先选择同时满足：

- 有潜在强痛点或强动机
- 有清晰替代品或 workaround
- 有机会形成差异化 wedge

### 6. 落盘到可继续研究的结构

默认使用：

- `ahe-product-skills/templates/insight-pack-template.md`

至少先填：

- `Problem Snapshot`
- `Commodity Risks`
- `Open Questions`

## Quality Bar

高质量 framing 至少应满足：

- 不再只是一个品类名
- 明确说出目标用户和触发情境
- 明确说出 desired outcome
- 明确说出当前替代品或 workaround
- 明确说出为什么原始 idea 容易平庸

## Red Flags

- 说了很多 feature，但说不出用户现在怎么凑合做
- outcome 仍然是“提升体验”“做得更好”这种空话
- 只有一个 framing，没有做任何发散
- 把品牌 slogan 当问题定义

## Recommended Next Step

默认下一步：

- `ahe-insight-mining`

如果用户已经有大量外部信号，也可以直接进入：

- `ahe-opportunity-mapping`
