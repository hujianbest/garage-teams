# T132: Growth Proposal And Promotion Implementation

- Task ID: `T132`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 落 `GrowthProposal` 与 governance-bounded promotion 的实现切片。
- 关联设计文档:
  - `docs/features/F141-evidence-to-continuity.md`
  - `docs/features/F144-growth-proposal-and-promotion.md`
  - `docs/design/D122-growth-promotion-operations-design.md`

## 1. 交付目标

- evidence-to-proposal path
- proposal lifecycle
- governed promotion

## 2. 最小交付物

- evidence 到 proposal 的显式路径
- proposal lifecycle
- accepted / rejected / deferred promotion handling

## 3. 依赖

- `F141`
- `F144`
- `D122`

## 4. 验收

- growth 不再绕过 proposal
- promotion 保持 governance-bounded
- proposal lifecycle 可被下游实现和运维共同消费
