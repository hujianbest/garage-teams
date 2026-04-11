# T110: Garage Phase 1 Runtime Home And Workspace Topology

- Task ID: `T110`
- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Garage` 在 phase 1 的 `source root / runtime home / workspace` 三层拓扑落成稳定的绑定规则，明确当前 repo-local dogfooding 形态与未来独立运行形态之间的关系。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/features/F210-runtime-home-and-workspace-topology.md`
  - `docs/features/F060-artifact-and-evidence-surface.md`
  - `docs/features/F220-runtime-bootstrap-and-entrypoints.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `packs/README.md`

## 1. 任务目标

把 phase 1 已经在设计文档中提出的三层拓扑变成明确的实现约束：

- 什么属于 `source root`
- 什么属于 `runtime home`
- 什么属于 `workspace`
- 当前仓库为什么既是 source root，又临时承担默认 dogfooding workspace

## 2. 输入设计文档

这一篇主要承接：

- `runtime home / workspace` 的三层拓扑
- root-level file-backed surfaces 的归属边界
- `source-coupled workspace mode` 的阶段性解释
- 后续 `launcher` 与 `host binding` 需要消费的绑定语义

## 3. 本文范围

- `Garage Source Root`
- `Garage Runtime Home`
- `Garage Workspace`
- 当前仓库的 phase 1 解释
- session 与 workspace 的绑定规则
- workspace surfaces 与 runtime home 的边界

## 4. 非目标

- 不实现具体安装脚本
- 不实现 secrets / config 管理系统
- 不实现多设备同步
- 不实现 service-backed runtime topology

## 5. 交付物

- 一套稳定的三层拓扑术语与绑定规则
- 当前仓库 dogfooding 形态的正式解释
- workspace surfaces 的权威归属规则
- 给 `12` 使用的最小 `workspace / runtime home / host` 绑定前提

## 6. 实施任务拆解

### 6.1 冻结三层拓扑

- 明确 `source root` 承载源码、设计文档与来源资产。
- 明确 `runtime home` 承载 profile、adapter metadata、cache 与安装实例级配置。
- 明确 `workspace` 承载 `artifacts / evidence / sessions / archives / .garage` 等主事实面。

### 6.2 解释当前仓库的 phase 1 形态

- 明确当前仓库处于 `source-coupled workspace mode`。
- 明确这是一种 phase 1 友好的 dogfooding 形态，而不是未来唯一运行方式。
- 明确哪些当前根目录事实属于 workspace，哪些只是 source root 文档与来源资产。

### 6.3 冻结 workspace surfaces 的归属边界

- 明确 `artifacts / evidence / sessions / archives / .garage` 属于 workspace，而不是 runtime home。
- 明确 pack-specific 内容如何通过 workspace surfaces 落盘，而不是再长新的顶层目录。
- 明确 session 不能跨多个 workspace 混写主事实面。

### 6.4 冻结 runtime home 的最小职责

- 明确 runtime home 只承载安装实例级配置、profile、cache 与 adapter 绑定信息。
- 明确 runtime home 不直接承载某个 workspace 的主 artifacts、主要 evidence 或显式 session 主线。
- 为后续 `profile / workspace / host` 绑定预留统一装配面。

### 6.5 给 `12` 的 bootstrap 链准备输入

- 明确 `launcher` 启动前最少需要哪些绑定信息。
- 明确 `create / resume` 如何先确定 workspace，再进入 session 主链。
- 明确 workspace 缺失、绑定冲突或拓扑不一致时如何报错，而不是静默回退。

## 7. 依赖与并行建议

- 依赖 `05`
- 建议在 `12` 之前完成
- 与 `08`、`09`、`10` 没有强实现耦合，但会影响后续独立运行形态的解释方式

## 8. 验收与验证

完成这篇任务后，应能验证：

- `source root / runtime home / workspace` 三层职责已经清晰分开
- 当前仓库的 dogfooding 形态已有正式解释，而不是隐式约定
- workspace surfaces 不会被 runtime home 吞并
- `12` 可以在不重新解释拓扑的前提下直接装配启动链

## 9. 完成后进入哪一篇

- `docs/tasks/T120-garage-phase-1-runtime-bootstrap-and-entrypoints.md`
- `docs/tasks/T130-garage-phase-1-runtime-provider-and-tool-execution.md`
