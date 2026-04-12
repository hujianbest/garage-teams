# T11: Runtime Core And Topology Tracks

- Task ID: `T11`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 拆解 `Garage Team runtime` 核心对象、拓扑与共享 entry binding 的实现任务。
- 关联设计文档:
  - `docs/features/F11-runtime-topology-and-entry-bootstrap.md`
  - `docs/features/F12-garage-team-runtime-core.md`
  - `docs/features/F16-execution-and-provider-tool-plane.md`

## 1. 这份文档回答什么

在入口工作环境已经成立后，哪些 runtime core 和 topology 任务必须先被实现，才能支撑后续治理、growth 和 packs。

## 2. 推荐顺序

1. `T111` runtime home and bootstrap
2. `T112` session runtime core
3. `T113` execution authority

## 3. family 交付目标

- runtime home / workspace / profile authority 主链稳定
- neutral records / session / registry 主链稳定
- execution authority placement 稳定

## 4. 并行与依赖

- `T111` 是本 family 的基线
- `T112` 依赖 `T111`
- `T113` 依赖 `T111`，并与 `T112` 共享 session/runtime context

## 5. 验收

- runtime core 的 owner 和边界对下游治理、growth、pack、entry 都一致
- profile / workspace / session / execution 不再互相补猜
- 下游 tasks 可以复用同一套 runtime 主语义

## 6. 非目标

- 不在这里定义 Web/CLI/HostBridge UX
- 不在这里定义 packs 的业务能力

## 7. 下游 specs

- `T111`：runtime home and bootstrap implementation
- `T112`：session runtime core implementation
- `T113`：execution authority implementation
