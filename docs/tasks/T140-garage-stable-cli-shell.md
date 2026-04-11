# T140: Garage Stable CLI Shell

- Task ID: `T140`
- 状态: 已完成
- 日期: 2026-04-11
- 定位: 把 `GarageLauncher`、`RuntimeProfile`、`WorkspaceBinding` 与 `SessionApi` 收敛成最薄、稳定、可恢复的 `CLIEntry`，作为三类入口中的第一条真实产品化切片。
- 当前阶段: 完整架构主线下的第二组独立入口 implementation tracks
- 关联设计文档:
  - `docs/features/F220-runtime-bootstrap-and-entrypoints.md`
  - `docs/features/F210-runtime-home-and-workspace-topology.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F010-shared-contracts.md`
  - `docs/features/F230-runtime-provider-and-tool-execution.md`

## 1. 任务目标

先把 `Garage` 的三类入口里最薄、最容易验证的一类真正落下来：

- `CLIEntry`

这一篇要证明的是：

- `CLI` 不是另一个私有 runtime
- `CLI` 可以通过统一 `GarageLauncher` 进入系统
- `CLI` 的 create / resume / attach / submitStep 都复用同一条 `Bootstrap -> SessionApi -> Session` 主链

## 2. 输入设计文档

这一篇主要承接：

- `CLIEntry` 作为一等入口 family
- `GarageLauncher` 与 canonical bootstrap sequence
- `RuntimeProfile`、`WorkspaceBinding`、`HostAdapterBinding`
- `SessionApi` 作为 entry-facing session seam
- `runtime home` 中 profile / provider authority 的基础语义

## 3. 本文范围

- `CLIEntry` 的最小命令入口语义
- profile / runtime home / workspace 的选择与绑定
- CLI 默认 host adapter 的薄绑定方式
- `SessionApi` 的 create / resume / attach / submitStep 投递
- 启动失败、绑定冲突与 session 恢复失败的错误面

## 4. 非目标

- 不冻结完整命令行 flags taxonomy
- 不设计完整 TUI 或终端富交互层
- 不让 CLI 自己决定 provider / model authority
- 不把 `WebEntry` 或 `HostBridgeEntry` 的需求偷塞进 CLI slice

## 5. 交付物

- 一个稳定的 `CLIEntry` 最小入口壳
- 一条 CLI 可直接复用的统一 bootstrap 链
- 一组 CLI 到 `SessionApi` 的最小动作映射
- 一组面向用户可理解的启动 / 恢复错误面
- 给 `15`、`16`、`17` 复用的共享入口骨架

## 6. 实施任务拆解

### 6.1 冻结 `CLIEntry` 的最小入口语义

- 明确 CLI 负责提交什么启动意图与交互意图。
- 明确 CLI 只是 `EntrySurface`，不拥有自己的 session / execution 语义。
- 为 CLI 准备默认的 host adapter 绑定方式，但不在这里扩展成宿主桥。

### 6.2 接通 profile / home / workspace 选择

- 让 CLI 能显式选择或恢复 `RuntimeProfile`。
- 让 CLI 能显式绑定 `runtime home` 与目标 workspace。
- 明确 source-coupled workspace 与外部 workspace 在 CLI 下如何被选择与报错。

### 6.3 把 CLI 请求送进 `SessionApi`

- create / resume / attach 先进入统一 `SessionApi`，而不是直接触碰 `Session`。
- submitStep、interrupt、closeout 等最小动作也沿用同一条 session-bound seam。
- 保持 CLI 不直接调用 `ExecutionLayer` 或 provider backend。

### 6.4 补齐错误恢复与可恢复体验

- 明确 profile 缺失、workspace 不存在、session 找不到、host 不兼容时如何报错。
- 明确 CLI 如何提示用户当前绑定的是哪个 workspace、profile 与 session。
- 避免 CLI 通过静默回退掩盖拓扑或治理错误。

### 6.5 做最小验证闭环

- 验证 CLI 能在同一 workspace 上稳定 create / resume / attach。
- 验证 CLI 的 session 恢复不需要私有 host 状态。
- 验证后续入口 family 可以直接复用这条 bootstrap / `SessionApi` 主链。

## 7. 依赖与并行建议

- 依赖 `11`、`12`、`13`
- 是 `15`、`16`、`17` 的共同前置
- 应先于 `HostBridgeEntry` 与 `WebEntry` 落地，避免多入口同时发明自己的入口壳

## 8. 验收与验证

完成这篇任务后，应能验证：

- `CLIEntry` 已成为真实入口，而不是架构名词
- CLI 通过同一条 `GarageLauncher -> SessionApi` 主链进入 runtime
- session 创建、恢复与后续动作不再散落在 CLI 私有逻辑里
- CLI 不会直接抢占 provider / execution authority

## 9. 完成后进入哪一篇

- `docs/tasks/T150-garage-host-bridge-entry.md`
- `docs/tasks/T160-garage-local-first-web-control-plane.md`
