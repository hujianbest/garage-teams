---
name: ahe-insight-mining
description: Mine product insight signals from web, GitHub, community, substitutes, and local context. Use when a concept needs evidence, when you need to understand why an idea feels commodity, or when you want non-obvious tensions and white space before mapping opportunities.
---

# AHE Insight Mining

## Overview

这个 skill 负责把“感觉”变成可引用的 product signals。

它不直接决定最终产品方案，而是先找出：

- 用户和市场里真实出现过什么信号
- 现有替代品和竞品都怎么解决
- GitHub / 开源项目里哪些模式已经过度常见
- 哪些 tensions、缺口或 no-go 信号值得认真对待

## When to Use

在这些场景使用：

- idea 已经存在，但没有足够证据判断值不值得做
- 你怀疑当前方向只是 category clone
- 需要系统整理外部资料、GitHub 项目和社区信号
- 需要形成 `insight-pack`

不要在这些场景使用：

- 还没做基本 framing，先回到 `ahe-outcome-framing`
- 研究已经足够，当前只是要机会排序，改用 `ahe-opportunity-mapping`

## Default Agents

按需读取并复用：

- `agents/product-web-researcher.md`
- `agents/github-pattern-scout.md`
- `agents/product-thesis-advocate.md`
- `agents/product-contrarian.md`
- `agents/product-debate-referee.md`

## Workflow

按以下顺序执行。

### 1. 把当前主题拆成 4 类研究问题

默认至少包含：

- `user-signal`：用户困扰、需求、行为、投诉、切换信号
- `substitute-signal`：当前替代品、workaround、人工流程
- `pattern-signal`：GitHub / 开源 / 同类产品的常见机制
- `white-space-signal`：没人解决好、但可能值得切入的 tension

### 2. 先收集高可信外部信号

优先：

- 官方产品页面
- GitHub 仓库与 README
- 社区讨论、issue、评论、文章
- 已存在的项目材料

结论必须尽量带来源，且说明它属于：

- `Observed`
- `Inferred`
- `Invented`
- `Untested`

### 3. 先让 `Scout` agents 并行带回证据

默认至少并行两路：

- `what exists`：现有产品 / repo / workflow 到底已经做到什么程度
- `what hurts`：用户或团队在现有做法里最难受的地方是什么

不要只做 feature list。

### 4. 让 `Advocate` 先提出 2 到 3 个候选 insight thesis

候选 thesis 应是“值得继续押注的洞察”，而不是原始摘录。

每个 thesis 至少写清：

- 对应哪些 `Observed` signals
- 为什么它可能成立
- 如果成立，会导向什么 wedge 或方向

### 5. 让 `Contrarian` 对候选 thesis 做反向挑战

至少回答：

- 这是不是大家都在做、因此很难形成吸引力的方向
- 这类产品最容易被高估的价值是什么
- 哪些常见做法其实只是实现方便，不代表用户真的在乎

### 6. 让 `Referee` 做一次 insight PK

至少区分：

- 哪些 thesis `survive`
- 哪些 thesis `park`
- 哪些 thesis `drop`

如果争论仍停留在主观判断，回到证据补充，而不是强行定论。

### 7. 形成 `insight-pack`

默认使用：

- `ahe-product-skills/templates/insight-pack-template.md`

至少补齐：

- `Observed Signals`
- `Inferred Insights`
- `White Space / Non-obvious Tensions`
- `Commodity Risks`
- `No-go Signals`
- `Debate Verdict`

### 8. 明确下一步研究是否已经足够进入机会收敛

如果你已经能回答以下问题，就可以进入 `ahe-opportunity-mapping`：

- 用户真正要推进的 progress 是什么
- 现在的替代品 / workaround 是什么
- 哪些信号最值得继续放大

## Quality Bar

高质量 insight pack 至少应满足：

- 不只是罗列竞品和功能
- 同时包含“已有模式”和“真实痛点 / tension”
- 明确哪些是事实，哪些只是推断
- 至少指出 1 到 3 个平庸化风险
- 至少指出 1 个值得继续下注的白空间方向
- 至少保留一段基于多 agent PK 的 `Debate Verdict`

## Red Flags

- 整份输出只有“某某也支持这个功能”
- 引用了很多资料，但没有抽出 tensions
- 完全没有 no-go signals
- 把“有市场”当成“有吸引力”
- 名义上用了多个 agent，但没有真正做观点对撞或淘汰

## Recommended Next Step

默认下一步：

- `ahe-opportunity-mapping`
