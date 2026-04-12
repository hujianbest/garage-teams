# T13: Continuity And Growth Tracks

- Task ID: `T13`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 拆解 continuity、memory、skill 与 growth promotion 的实现任务。
- 关联设计文档:
  - `docs/features/F14-continuity-and-growth.md`
  - `docs/design/D12-governance-and-growth-operations-designs.md`

## 1. 这份文档回答什么

continuity、memory、skill 与 growth proposal 的实现应如何拆成可连续推进的任务。

## 2. 推荐顺序

1. `T131` continuity stores
2. `T132` growth proposal and promotion

## 3. family 交付目标

- continuity stores 与团队长期资产分层稳定
- growth proposal 主线稳定
- promotion 仍然 evidence-first、governance-bounded

## 4. 并行与依赖

- `T131` 是长期资产的基础
- `T132` 依赖 `T131`，并消费 governance / evidence 主线

## 5. 验收

- memory / skill / proposal 的 owner 与边界可被实现
- 下游不需要再把 continuity 和 growth 混成一个抽象“学习系统”

## 6. 非目标

- 不在这里定义 packs 的具体业务能力
- 不把 growth 简化成自动黑箱学习

## 7. 下游 specs

- `T131`：continuity stores implementation
- `T132`：growth proposal and promotion implementation
