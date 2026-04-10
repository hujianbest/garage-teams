# Garage Core

- 状态: phase 1 scaffold
- 日期: 2026-04-11
- 定位: `garage/core/` 是 `Garage Core` 的稳定实现面，后续承接 `session`、`registry`、`governance`、artifact routing 与 evidence coordination。

## 边界

这里放：

- core runtime objects
- session lifecycle coordination
- registry / governance / routing 等平台中立能力

这里不放：

- pack-specific 角色、节点与 artifact 语义
- host-specific 适配实现
- 设计长文与分析资料

## phase 1 说明

phase 1 先把这里当成稳定内核目录预留出来，不在 `01` 中提前写入 pack 领域词。
