# T130: Garage Phase 1 Runtime Provider And Tool Execution

- Task ID: `T130`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Garage` 的 provider adapters、tool registry、execution trace 与治理挂点落成统一 execution layer，让平台从“可编排”进一步推进到“可真正执行”。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/features/F230-runtime-provider-and-tool-execution.md`
  - `docs/features/F220-runtime-bootstrap-and-entrypoints.md`
  - `docs/features/F050-governance-model.md`
  - `docs/features/F060-artifact-and-evidence-surface.md`
  - `docs/design/D120-garage-coding-pack-design.md`
  - `docs/design/D110-garage-product-insights-pack-design.md`

## 1. 任务目标

给 `Garage` 补上真正的 runtime execution layer，使它能够在受治理、可留痕的条件下统一执行：

- provider 调用
- tool 调用
- execution trace 留痕

而不是把这些逻辑散落在 host、core 或 pack 中。

## 2. 输入设计文档

这一篇主要承接：

- `ProviderAdapter`
- `ToolRegistry`
- `ExecutionRequest / ExecutionContext / ProviderResponse`
- execution events 的统一语义

## 3. 本文范围

- provider adapter 壳
- tool registry 与 tool capability 挂点
- execution request / response / trace
- governance checkpoints
- evidence trace materialization
- packs 的 capability 请求面

## 4. 非目标

- 不做 provider marketplace
- 不做复杂沙箱系统
- 不做多 provider 并发编排
- 不一次性接完所有 vendor 或工具后端

## 5. 交付物

- 一套统一 execution layer 对象
- 一套 provider adapter 与 tool registry 骨架
- 一组稳定的 execution events
- 一条 execution trace -> evidence 的最小物化链路
- pack 声明 capability、runtime 选择 backend 的分层约束

## 6. 实施任务拆解

### 6.1 冻结 execution objects

- 明确 `ExecutionRequest`、`ExecutionContext`、`ProviderResponse`、`ExecutionTrace` 的最小 shape。
- 明确哪些字段属于 runtime，哪些字段属于 pack-local 语义。
- 避免 pack 直接发明自己的执行协议。

### 6.2 落 provider adapter 壳

- 给模型或执行后端预留统一 adapter 入口。
- 吸收厂商差异，归一化返回结果与错误。
- 保持 vendor 差异留在 adapter 之下，而不是扩散到 core。

### 6.3 落 tool registry 与 capability 挂点

- 明确工具如何注册。
- 明确 packs 如何声明允许的 capability，而不是绑定具体实现。
- 明确 host 可以限制能力边界，但不能重写工具语义。

### 6.4 接治理与证据

- 关键 execution 动作先走 gate / approval / evidence 要求判断。
- 执行过程中的 tool call、失败、中断、完成等事件要能物化为 evidence。
- 避免 execution 退化成不可追溯的黑箱。

### 6.5 接 runtime bootstrap 与 reference packs

- 让 `12` 里预留的 execution 接口真正可装配。
- 让 `Product Insights Pack` 与 `Coding Pack` 使用同一 execution 语汇。
- 验证 packs 请求的是 capability，不是 vendor name。

## 7. 依赖与并行建议

- 依赖 `04`、`05`、`08`、`09`、`12`
- 建议先有 reference packs 的最小语义，再把 execution layer 接进来
- 是 phase 1 朝“独立可运行程序”推进的最后一篇任务

## 8. 验收与验证

完成这篇任务后，应能验证：

- provider 与 tool execution 已有统一 runtime 层
- execution 不再散落在 host、core 或 pack 中
- 治理与 evidence 能约束关键执行动作
- `Garage` 已从 repo-local dogfooding 进一步推进到真正可运行程序的实现方向

## 9. 完成后进入哪一篇

- 进入独立可运行程序的实现排期、打包与运维层设计
- 或单独新增 `runtime ops / packaging / secrets` 任务文档
