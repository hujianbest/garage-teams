# T120: Garage Phase 1 Runtime Bootstrap And Entrypoints

- Task ID: `T120`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Garage` 的多入口体验收敛到同一条 runtime bootstrap chain，落统一 launcher、profile / workspace / host binding 与 session create / resume 主入口。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/features/F220-runtime-bootstrap-and-entrypoints.md`
  - `docs/features/F210-runtime-home-and-workspace-topology.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F010-shared-contracts.md`
  - `docs/features/F040-session-lifecycle-and-handoffs.md`

## 1. 任务目标

让 `Garage` 不再只有“文档上可以多入口”，而是实现上也能保证：

- 多入口共享同一 runtime
- session 的创建与恢复走同一套主入口
- profile、workspace 与 host adapter 的绑定不会散落在不同入口里

## 2. 输入设计文档

这一篇主要承接：

- `GarageLauncher` 与 canonical bootstrap sequence
- `RuntimeProfile`、`WorkspaceBinding`、`HostAdapterBinding`
- one runtime, many entry surfaces

## 3. 本文范围

- launcher 主入口
- runtime profile 解析
- workspace binding 接入
- host adapter 选择与绑定
- session create / resume 启动链
- runtime services 的最小装配顺序

## 4. 非目标

- 不冻结完整命令行 flags
- 不实现完整 GUI
- 不做远程控制面 API
- 不做多进程 supervisor

## 5. 交付物

- 一套统一 launcher 语义
- 一条稳定的 bootstrap 顺序
- create / resume / attach 的最小入口壳
- host adapter 与 runtime services 的最小装配骨架
- 启动失败与绑定冲突的错误面

## 6. 实施任务拆解

### 6.1 冻结 launcher 输入输出

- 明确 launcher 至少接收哪些启动意图。
- 明确哪些信息在 bootstrap 前必须确定，哪些可以使用默认值。
- 避免不同入口各自发明启动参数语义。

### 6.2 解析 profile / home / workspace / host

- 先解析 `RuntimeProfile`。
- 再绑定 `runtime home` 与目标 workspace。
- 再选择 `HostAdapterBinding`。
- 让这组绑定关系形成稳定的启动上下文。

### 6.3 装配最小 runtime services

- 初始化 registry、governance loaders、workspace surfaces 与 session 相关服务。
- 保持 bootstrap 只负责装配，不越权解释 pack 语义。
- 给后续 execution layer 预留接入位，而不是先在入口里硬写 provider 逻辑。

### 6.4 统一 create / resume 主链

- 新 session 如何进入 runtime。
- 已有 session 如何恢复。
- create / resume 后如何把交互推进交给同一个 `Garage Core`。

### 6.5 补齐多入口与错误路径

- 至少预留 `CLI`、`IDE`、聊天入口的接入壳。
- 明确 workspace 缺失、profile 冲突、host 不兼容时如何报错。
- 避免入口静默绕过 bootstrap。

## 7. 依赖与并行建议

- 依赖 `02`、`03`、`04`、`05`、`11`
- `11` 先把拓扑绑定说清楚，`12` 再把它装进启动链
- 是 `13` 的直接前置

## 8. 验收与验证

完成这篇任务后，应能验证：

- 不同入口确实汇入同一 runtime bootstrap chain
- session 创建与恢复不再散落在各入口内部
- host adapter 只负责入口差异，不接管 core 语义
- 后续 execution layer 已有稳定接入点

## 9. 完成后进入哪一篇

- `docs/tasks/T130-garage-runtime-provider-and-tool-execution.md`
