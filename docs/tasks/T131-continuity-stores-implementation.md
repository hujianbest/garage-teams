# T131: Continuity Stores Implementation

- Task ID: `T131`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 落 memory / skill 等 continuity stores 的实现切片。
- 关联设计文档:
  - `docs/features/F142-memory.md`
  - `docs/features/F143-skill-assets.md`

## 1. 交付目标

- memory storage
- skill asset storage
- continuity readback semantics

## 2. 最小交付物

- memory store
- skill asset store
- continuity readback paths

## 3. 验收

- memory / skill 的长期资产边界清楚
- continuity stores 不与 evidence / session 混桶
- growth proposal 下游不需要重新定义长期资产入口
