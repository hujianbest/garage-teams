# D122: Growth Promotion Operations Design

- Design ID: `D122`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 展开 `GrowthProposal`、promotion 与长期更新运营方式的具体设计。
- 关联文档:
  - `docs/design/D12-governance-and-growth-operations-designs.md`
  - `docs/features/F144-growth-proposal-and-promotion.md`

## 1. 设计目标

- 说明 growth proposal 如何被提出、评审、接受或驳回
- 说明长期成长如何保持 evidence-first 与 governance-bounded

## 2. 最小运营阶段

growth promotion 至少应被组织成这些阶段：

1. observation
2. evidence baseline formed
3. proposal created
4. review / approval / rejection
5. accepted promotion target recorded

## 3. 主要对象

- proposal
- supporting evidence
- promotion target
- decision / approval result
- resulting continuity update

## 4. 对用户可见的东西

用户至少应能知道：

- 为什么这个 proposal 出现
- 它引用了哪些 evidence
- 它打算进入 memory、skill 还是 runtime update
- 它当前是待评审、已接受还是已驳回

## 5. 边界规则

- growth 不能绕过 proposal
- proposal 不能绕过 governance
- accepted proposal 不直接等于自动落地，仍需有明确目标与结果记录

## 6. 非目标

- 不把 growth promotion 做成无边界自动学习
- 不让 proposal 成为宿主私有 shortcut
- 不在这里定义所有 continuity 存储细节

## 7. 设计完成标准

- growth proposal 的最小运营阶段清楚
- proposal / evidence / promotion target / governance 的关系清楚
- 下游 task 可以据此切出 proposal lifecycle 实现
