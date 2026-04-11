# T040: Garage Phase 1 Session Lifecycle And Governance

- Task ID: `T040`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Garage` 的 session 主链、状态转移、handoff、review-hold、rework、closeout 与四层治理模型落成稳定的控制流实现面。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/features/F040-session-lifecycle-and-handoffs.md`
  - `docs/features/F050-governance-model.md`
  - `docs/features/F030-core-runtime-records.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`

## 1. 任务目标

让 `Garage` 的核心控制流从抽象语义进入可执行状态机：

- session 如何创建、恢复、暂停、交接、返工、收尾
- governance 如何在关键动作前做 gate 判断
- review、approval、exception 如何留痕

## 2. 输入设计文档

这一篇主要承接：

- `session lifecycle` 的动作与状态语义
- `global / core / pack / node` 四层治理
- approval、review、archive、exception 的边界

## 3. 本文范围

- lifecycle action 与 persisted state 的映射
- handoff 前后动作
- gate 调用点
- review / approval / exception / rework 流
- closeout 与 archive-ready 转移

## 4. 非目标

- 不落具体 pack 内部节点图
- 不做 host-specific 交互界面
- 不做复杂组织权限系统
- 不承担 evidence 文件表面的具体落盘实现

## 5. 交付物

- 一套稳定的 session state machine
- 一套治理评估入口
- handoff / review / rework / closeout 的 record 触发规则
- invalid transition 与 blocked gate 的错误面

## 6. 实施任务拆解

### 6.1 落生命周期动作与状态矩阵

- 定义允许的 action set。
- 定义 `active / paused / handoff-pending / review-hold / rework / closeout / archive-ready / closed` 的转移矩阵。
- 明确动作触发时必须产生哪些 runtime records 与 evidence 事件。

### 6.2 落治理评估入口

- 把 `global / core / pack / node` 四层规则统一成可评估入口。
- 明确 gate 的结果语义：`allow`、`hold`、`need-review`、`need-approval`、`need-evidence`、`block`。
- 明确更严格规则优先的冲突裁决方式。

### 6.3 落 review / approval / exception 主链

- review 如何把 session 送入 `review-hold`
- approval 如何放行关键动作
- exception 如何成为显式豁免记录，而不是隐式绕过

### 6.4 落 handoff / rework / closeout

- handoff 前必须准备哪些记录
- rework 如何携带缺口与回流范围
- closeout 与 archive-ready 如何保持不同语义
- 这里只冻结语义与触发点，具体 evidence 写入表面由 `05` 承接

### 6.5 补齐异常路径

- 非法状态转移如何报错
- evidence 不足如何阻断关键动作
- gate 冲突如何被解释和回指

## 7. 依赖与并行建议

- 依赖 `02`、`03`
- 应先冻结状态与 gate 语义，再由 `05` 承接具体 file-backed materialization
- 是 `08`、`09`、`10` 的前置

## 8. 验收与验证

完成这篇任务后，应能验证：

- 所有关键状态转移都可解释
- gate 阻断会留下可追溯记录
- handoff 与 rework 不会退化成隐式上下文切换
- closeout 与 archive-ready 不会被混写

## 9. 完成后进入哪一篇

- `docs/tasks/T050-garage-phase-1-artifact-routing-and-evidence-surface.md`
- `docs/tasks/T080-garage-phase-1-product-insights-pack.md`
- `docs/tasks/T090-garage-phase-1-coding-pack.md`
