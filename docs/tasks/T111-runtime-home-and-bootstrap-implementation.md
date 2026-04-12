# T111: Runtime Home And Bootstrap Implementation

- Task ID: `T111`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 落 runtime home / workspace topology、bootstrap 和 RuntimeProfile authority 的实现切片。
- 关联设计文档:
  - `docs/features/F111-runtime-home-and-workspace-topology.md`
  - `docs/features/F112-bootstrap-and-runtime-profile.md`

## 1. 交付目标

- runtime home / workspace 绑定
- bootstrap 主链
- profile authority resolution

## 2. 最小交付物

- 可检查的 runtime home / workspace topology
- 统一 bootstrap 链
- `RuntimeProfile` authority resolution

## 3. 验收

- 不同入口共享同一 bootstrap / topology 主线
- runtime home 与 workspace 不再互相吞并
- provider authority 的 owner 清楚可实现
