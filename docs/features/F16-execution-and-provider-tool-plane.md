# F16: Execution And Provider Tool Plane

- Feature ID: `F16`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 provider、tool、execution trace 与 authority placement 的稳定 capability family。
- 关联文档:
  - `docs/architecture/12-execution-and-provider-layer.md`
  - `docs/architecture/103-execution-runtime.md`
  - `docs/architecture/101-bootstrap-and-profiles.md`
  - `docs/features/F161-provider-authority-placement.md`
  - `docs/features/F162-tool-execution-capability-surface.md`
  - `docs/features/F163-execution-trace.md`
  - `docs/features/F164-evidence-linked-execution-outcomes.md`

## 1. 这份文档回答什么

Garage Team runtime 如何统一执行 provider/tool work，并把 authority 放在正确位置。

## 2. stable capability family

- provider authority in runtime configuration
- provider/tool execution
- tool capability surface
- execution trace
- evidence-linked execution outcomes

## 3. 下游 specs

- `F161`：provider authority placement
- `F162`：tool execution capability surface
- `F163`：execution trace
- `F164`：evidence-linked execution outcomes
