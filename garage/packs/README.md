# Garage Packs

- 状态: phase 1 scaffold
- 日期: 2026-04-11
- 定位: `garage/packs/` 是 `Garage` reference packs 的实现根目录，pack-specific 角色、节点、artifact、evidence 与治理 overlay 都应留在各自 pack 下。

## 当前 phase 1 packs

- `garage/packs/product-insights/`
- `garage/packs/coding/`

## 边界

这里放：

- pack manifests
- pack-local roles / nodes / policies
- pack-local artifact 与 evidence mappings
- continuity candidates 的 pack 输出钩子

这里不放：

- 平台中立 core 逻辑
- 共享 contract 定义
- 与 pack 无关的 host adapter 逻辑
