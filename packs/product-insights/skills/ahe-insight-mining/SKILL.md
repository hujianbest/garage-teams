---
name: ahe-insight-mining
description: 适用于已有 idea 但缺少外部证据、需要从 web/GitHub/社区/替代品中提取信号并形成 insight pack 的场景。不适用于还没做基本 framing（→ ahe-outcome-framing）或研究已充分只需排序机会（→ ahe-opportunity-mapping）的场景。
---

# AHE Insight Mining

负责把"感觉"变成可引用的 product signals——找出用户/市场真实信号、替代品做法、开源过度模式和值得切入的 tension。不直接决定产品方案或机会排序。

## When to Use

**正向触发：**
- idea 已经存在，但没有足够证据判断值不值得做
- 怀疑当前方向只是 category clone
- 需要系统整理外部资料、GitHub 项目和社区信号
- 需要形成 insight-pack

**不适用：**
- 还没做基本 framing → `ahe-outcome-framing`
- 研究已经足够，当前只是要机会排序 → `ahe-opportunity-mapping`

**Direct invoke：** 用户说"先查查市场""看看别人怎么做的""有没有开源方案""这个方向是不是太普通"

**相邻边界：** 若在挖掘过程中发现 framing 本身有问题（目标用户不清），退回 `ahe-outcome-framing`。

## Workflow

### 1. 先读取已有 framing 和项目材料

读取项目中的 problem/outcome frame、现有文档、用户反馈等已有证据。若无任何 framing 工件，reroute 到 `ahe-outcome-framing`。

### 2. 把当前主题拆成 4 类研究问题

默认至少包含：

- user-signal：用户困扰、需求、行为、投诉、切换信号
- substitute-signal：当前替代品、workaround、人工流程
- pattern-signal：GitHub / 开源 / 同类产品的常见机制
- white-space-signal：没人解决好、但可能值得切入的 tension

### 3. 先收集高可信外部信号

使用 `../../agents/product-web-researcher.md` 和 `../../agents/github-pattern-scout.md` 并行带回证据。

优先：

- 官方产品页面
- GitHub 仓库与 README
- 社区讨论、issue、评论、文章
- 已存在的项目材料

结论必须尽量带来源，且说明它属于：

- Observed
- Inferred
- Invented
- Untested

**决策点：** 若外部信号极度稀少，可能说明方向定义太窄或太超前，回到 step 2 调整研究范围。

### 4. 让 Advocate 提出候选 insight thesis

使用 `../../agents/product-thesis-advocate.md`，提出 2-3 个候选 thesis。

每个 thesis 至少写清：

- 对应哪些 Observed signals
- 为什么它可能成立
- 如果成立，会导向什么 wedge 或方向

### 5. 让 Contrarian 对候选 thesis 做反向挑战

使用 `../../agents/product-contrarian.md`，至少回答：

- 这是不是大家都在做、因此很难形成吸引力的方向
- 这类产品最容易被高估的价值是什么
- 哪些常见做法其实只是实现方便，不代表用户真的在乎

### 6. 让 Referee 做 insight PK

使用 `../../agents/product-debate-referee.md`，至少区分：

- 哪些 thesis survive / park / drop

如果争论仍停留在主观判断，回到 step 3 补充证据，而不是强行定论。

### 7. 形成 insight-pack

使用 pack 内模板 `../templates/insight-pack-template.md`，至少补齐：

- Observed Signals
- Inferred Insights
- White Space / Non-obvious Tensions
- Commodity Risks
- No-go Signals
- Debate Verdict

### 8. 判断研究是否已足够进入机会收敛

如果已能回答以下问题，可进入 `ahe-opportunity-mapping`：

- 用户真正要推进的 progress 是什么
- 现在的替代品 / workaround 是什么
- 哪些信号最值得继续放大

## Output Contract

- **写什么：** insight-pack 文档
- **写到哪里：** 项目约定位置（参考 AGENTS.md），默认示例 `docs/insights/YYYY-MM-DD-<topic>-insight-pack.md`
- **状态同步：** insight-pack 包含信号分类、thesis PK 结论、白空间方向
- **下一步：** `ahe-opportunity-mapping`

## Red Flags

- 整份输出只有"某某也支持这个功能"
- 引用了很多资料，但没有抽出 tensions
- 完全没有 no-go signals
- 把"有市场"当成"有吸引力"
- 名义上用了多个 agent，但没有真正做观点对撞或淘汰

## Common Mistakes

| 错误 | 后果 | 修复 |
|------|------|------|
| 只做 feature list 对比 | 无法发现白空间 | 每条信号必须标注类型（Observed/Inferred/Invented/Untested） |
| 跳过 contrarian 挑战 | 信号分析偏向乐观 | 必须经过反向挑战才能定论 |
| 没有标注信号来源 | 事实和推测混在一起 | 所有信号标注来源分类 |

## 和其他 Skill 的区别

| 对比项 | ahe-insight-mining | ahe-outcome-framing | ahe-opportunity-mapping | ahe-concept-shaping |
|--------|--------------------|--------------------|------------------------|---------------------|
| 核心任务 | 提取外部信号和洞察 | 重写模糊 idea 为锋利问题 | 选择优先机会 | 发散收敛概念方向 |
| 输入 | framing 文档 | 用户模糊 idea | insight-pack | opportunity-map |
| 输出 | insight-pack | problem/outcome frame | opportunity-map | concept-brief |
| 关键动作 | 多源信号 → thesis PK | 问题重构 → commodity 检查 | JTBD → 机会排序 | 多方向 PK → wedge |

## Reference Guide

| 材料 | 路径 | 用途 |
|------|------|------|
| Insight Pack 模板 | `../templates/insight-pack-template.md` | 落盘格式 |
| 产品洞察共享约定 | `../docs/product-insight-shared-conventions.md` | 家族级术语和约定 |
| 产品辩论协议 | `../docs/product-debate-protocol.md` | 多 agent 讨论规范 |
| 产品洞察基础 | `../docs/product-insight-foundations.md` | 方法论背景 |
| Agent: web-researcher | `../../agents/product-web-researcher.md` | 外部信号收集 |
| Agent: github-scout | `../../agents/github-pattern-scout.md` | GitHub 模式识别 |
| Agent: thesis-advocate | `../../agents/product-thesis-advocate.md` | 为 thesis 辩护 |
| Agent: contrarian | `../../agents/product-contrarian.md` | 反向挑战 |
| Agent: debate-referee | `../../agents/product-debate-referee.md` | PK 裁判 |

## Verification

- [ ] insight-pack 已落盘
- [ ] 信号已分类为 Observed / Inferred / Invented / Untested
- [ ] 至少指出 1-3 个 commodity 风险
- [ ] 至少指出 1 个白空间方向
- [ ] 有多 agent PK 结论记录（Debate Verdict）
- [ ] 下一步 skill 已明确（→ ahe-opportunity-mapping）
