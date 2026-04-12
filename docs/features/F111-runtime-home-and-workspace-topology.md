# F111: Runtime Home And Workspace Topology

- Feature ID: `F111`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 `runtime home / workspace` 的稳定拓扑语义。

## 1. 稳定语义

- workspace facts live in the workspace
- runtime home owns runtime config, cache, and adapter metadata
- source root, runtime home, and workspace must remain distinct layers
