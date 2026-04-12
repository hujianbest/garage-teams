# T12: Governance And Workspace Truth Tracks

- Task ID: `T12`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 拆解 workspace-first facts、artifact routing、evidence 与 governance 表面的实现任务。
- 关联设计文档:
  - `docs/features/F13-governance-and-workspace-truth.md`
  - `docs/design/D12-governance-and-growth-operations-designs.md`

## 1. 这份文档回答什么

workspace-first facts、artifact routing、evidence 与 governance 表面，应按什么顺序推进实现。

## 2. 推荐顺序

1. `T121` workspace facts and artifact routing
2. `T122` governance and evidence

## 3. family 交付目标

- workspace facts 成为主事实面
- artifact routing 进入明确 authority 语义
- governance / evidence 成为显式工作表面

## 4. 并行与依赖

- `T121` 是 workspace truth 基线
- `T122` 依赖 `T121` 的主事实面，同时绑定治理结果与 evidence

## 5. 验收

- workspace facts、routing、governance、evidence 的关系可被稳定实现
- 下游 growth 和 pack collaboration 不需要重新定义事实面

## 6. 非目标

- 不在这里定义长期 continuity 存储
- 不在这里定义 provider/tool execution 主线

## 7. 下游 specs

- `T121`：workspace facts and artifact routing implementation
- `T122`：governance and evidence implementation
