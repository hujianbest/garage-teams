# Garage Shared Contracts

- 状态: phase 1 scaffold
- 日期: 2026-04-11
- 定位: `garage/contracts/` 是 `Garage` 共享 contracts 的实现面，后续承接 contract definitions、schema 校验、加载与 registry 对接。

## 边界

这里放：

- `PackManifest`
- `RoleContract`
- `WorkflowNodeContract`
- `ArtifactContract`
- `EvidenceContract`
- `HostAdapterContract`

以及与它们相关的：

- schema validators
- loader / discovery glue
- 兼容与版本检查

这里不放：

- core runtime state
- pack-specific 节点逻辑
- host-specific UI 或交互逻辑
