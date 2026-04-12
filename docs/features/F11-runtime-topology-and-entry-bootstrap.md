# F11: Runtime Topology And Entry Bootstrap

- Feature ID: `F11`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 `runtime home / workspace / entry bootstrap` 的稳定 capability family，确保不同入口都进入同一条启动链。
- 关联文档:
  - `docs/architecture/10-entry-and-host-injection-layer.md`
  - `docs/architecture/11-runtime-coordination-layer.md`
  - `docs/architecture/101-bootstrap-and-profiles.md`
  - `docs/features/F111-runtime-home-and-workspace-topology.md`
  - `docs/features/F112-bootstrap-and-runtime-profile.md`
  - `docs/features/F113-session-api-and-shared-entry-binding.md`

## 1. 这份文档回答什么

Garage 的入口如何在不分叉系统真相的前提下进入同一个 runtime。

## 2. stable capability family

- `runtime home`
- `workspace`
- `Bootstrap`
- `RuntimeProfile`
- `SessionApi`
- shared entry binding for CLI / Web / HostBridge

## 3. 下游 specs

- `F111`：runtime home 与 workspace 拓扑
- `F112`：bootstrap 与 runtime profile authority
- `F113`：SessionApi 与 shared entry binding
