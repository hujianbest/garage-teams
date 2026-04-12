# T121: Workspace Facts And Artifact Routing Implementation

- Task ID: `T121`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 落 workspace-first facts 与 artifact routing 的实现切片。
- 关联设计文档:
  - `docs/features/F131-workspace-first-facts.md`
  - `docs/features/F132-artifact-routing.md`

## 1. 交付目标

- workspace-first facts
- artifact routing
- authority-preserving write paths

## 2. 最小交付物

- workspace facts 的权威目录与读写规则
- neutral artifact intent -> authoritative destination 的 routing 逻辑
- authority-preserving write semantics

## 3. 验收

- artifacts / evidence / sessions / archives / .garage 的归属清楚
- routing 不需要 pack 私有路径约定
- 下游 evidence / bridge 不会再次发明事实面
