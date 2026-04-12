# T15: Product Hardening And Delivery Tracks

- Task ID: `T15`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 拆解 secrets、distribution、ops、observability 和后续产品深化的实现任务。
- 关联设计文档:
  - `docs/features/F16-execution-and-provider-tool-plane.md`
  - `docs/design/D10-agent-team-workspace-designs.md`
  - `docs/design/D12-governance-and-growth-operations-designs.md`

## 1. 这份文档回答什么

在核心产品入口和 runtime 主线稳定后，哪些 hardening / delivery 任务应继续推进。

## 2. 推荐顺序

1. `T151` secrets, doctor, and distribution
2. `T152` runtime ops and observability
3. `T153` web depth and optional orchestration

## 3. family 交付目标

- provider authority 和 secrets 主线稳定
- distribution / doctor / diagnostics 稳定
- observability 与更深 Web surfaces 可在 shared truth 上展开

## 4. 并行与依赖

- `T151` 是本 family 的交付基线
- `T152` 依赖 `T151`
- `T153` 依赖 `T152`，且只有在产品主入口稳定后才值得继续加深

## 5. 验收

- hardening 和 delivery 不会反向改写产品主线
- 下游 web depth / orchestration 不再需要猜基础运维和 authority 前提

## 6. 非目标

- 不要求一次性把所有产品深度都做完
- 不把 optional orchestration 提前为平台前提

## 7. 下游 specs

- `T151`：secrets, doctor, and distribution implementation
- `T152`：runtime ops and observability implementation
- `T153`：web depth and optional orchestration implementation
