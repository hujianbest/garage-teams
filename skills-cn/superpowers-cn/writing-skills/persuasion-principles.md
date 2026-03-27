# 技能设计中的说服原则

## 概述

大语言模型与人类一样会对说服原则作出反应。理解这种心理学有助于设计更有效的技能——不是为了操纵，而是为了在压力下仍能落实关键实践。

**研究基础：** Meincke 等（2025）在 N=28,000 场 AI 对话中检验了 7 条说服原则。说服技巧使遵从率提升一倍以上（33% → 72%，p < .001）。

## 七条原则

### 1. 权威（Authority）
**是什么：** 服从专业、资历或官方来源。

**在技能中如何起作用：**
- 祈使语气：「YOU MUST」「Never」「Always」
- 不可协商的框定：「No exceptions」
- 减少决策疲劳与自我合理化

**何时使用：**
- 强调纪律的技能（TDD、验证要求）
- 安全关键实践
- 已确立的最佳实践

**示例：**
```markdown
✅ Write code before test? Delete it. Start over. No exceptions.
❌ Consider writing tests first when feasible.
```

### 2. 承诺（Commitment）
**是什么：** 与先前行为、陈述或公开表态保持一致。

**在技能中如何起作用：**
- 要求宣告：「Announce skill usage」
- 强迫明确选择：「Choose A, B, or C」
- 使用跟踪：TodoWrite 清单

**何时使用：**
- 确保技能真的被遵循
- 多步流程
- 问责机制

**示例：**
```markdown
✅ When you find a skill, you MUST announce: "I'm using [Skill Name]"
❌ Consider letting your partner know which skill you're using.
```

### 3. 稀缺（Scarcity）
**是什么：** 来自时限或「机会有限」的紧迫感。

**在技能中如何起作用：**
- 时限要求：「Before proceeding」
- 顺序依赖：「Immediately after X」
- 防止拖延

**何时使用：**
- 立即验证要求
- 时间敏感工作流
- 防止「稍后再做」

**示例：**
```markdown
✅ After completing a task, IMMEDIATELY request code review before proceeding.
❌ You can review code when convenient.
```

### 4. 社会认同（Social Proof）
**是什么：** 从众——与他人一致或符合常态。

**在技能中如何起作用：**
- 普遍模式：「Every time」「Always」
- 失败模式：「X without Y = failure」
- 建立规范

**何时使用：**
- 记录普遍实践
- 警示常见失败
- 强化标准

**示例：**
```markdown
✅ Checklists without TodoWrite tracking = steps get skipped. Every time.
❌ Some people find TodoWrite helpful for checklists.
```

### 5. 认同／一体（Unity）
**是什么：** 共同身份、「我们感」、ingroup 归属。

**在技能中如何起作用：**
- 协作语言：「our codebase」「we're colleagues」
- 共同目标：「we both want quality」

**何时使用：**
- 协作工作流
- 建立团队文化
- 非层级实践

**示例：**
```markdown
✅ We're colleagues working together. I need your honest technical judgment.
❌ You should probably tell me if I'm wrong.
```

### 6. 互惠（Reciprocity）
**是什么：** 回报所得的义务。

**如何起作用：**
- 少用——易显得操纵
- 技能中很少需要

**何时避免：**
- 几乎总是（其他原则更有效）

### 7. 喜好（Liking）
**是什么：** 更愿意与我们喜欢的人合作。

**如何起作用：**
- **不要用于合规**
- 与坦诚反馈文化冲突
- 助长谄媚

**何时避免：**
- 强调纪律时始终避免

## 按技能类型的原则组合

| 技能类型 | 宜用 | 宜避 |
|------------|-----|-------|
| 纪律强化 | 权威 + 承诺 + 社会认同 | 喜好、互惠 |
| 指导/技术 | 适度权威 + 认同 | 过重权威 |
| 协作 | 认同 + 承诺 | 权威、喜好 |
| 参考 | 仅清晰 | 各类说服 |

## 为何有效：心理学

**清晰界线减少合理化：**
- 「YOU MUST」减少决策疲劳
- 绝对表述消除「这算不算例外？」
- 明确的反合理化条目堵住具体漏洞

**执行意图促成自动行为：**
- 清晰触发 + 必需动作 → 自动执行
- 「When X, do Y」比「generally do Y」更有效
- 降低遵从的认知负担

**LLM 类人类（parahuman）：**
- 在人类文本上训练，内含这些模式
- 训练数据中权威语言常先于遵从出现
- 承诺序列（陈述 → 行动）频繁被建模
- 社会认同模式（人人都做 X）建立规范

## 伦理使用

**正当：**
- 确保关键实践被遵循
- 撰写有效文档
- 预防可预见的失败

**不正当：**
- 为私利操纵
- 制造虚假紧迫感
- 基于愧疚的服从

**检验：** 若用户完全理解该技巧，它是否仍符合用户的真实利益？

## 研究引用

**Cialdini, R. B. (2021).** *Influence: The Psychology of Persuasion (New and Expanded).* Harper Business.
- 七条说服原则
- 影响力研究的实证基础

**Meincke, L., Shapiro, D., Duckworth, A. L., Mollick, E., Mollick, L., & Cialdini, R. (2025).** Call Me A Jerk: Persuading AI to Comply with Objectionable Requests. University of Pennsylvania.
- 在 N=28,000 场 LLM 对话中检验 7 条原则
- 说服技巧使遵从率由 33% 升至 72%
- 权威、承诺、稀缺最有效
- 支持 LLM 行为的类人类模型

## 速查

设计技能时自问：

1. **属于哪一类？**（纪律 vs 指导 vs 参考）
2. **想改变什么行为？**
3. **哪些原则适用？**（纪律类通常是权威 + 承诺）
4. **是否叠得太多？**（不要七条全上）
5. **是否合乎伦理？**（是否服务于用户真实利益？）
