# Garage Mainline Task Plan

- 状态: 已确认
- 主题: Garage mainline implementation plan after approved design
- 输入基线:
  - specs: `docs/features/`
  - design: `docs/design/D10-agent-team-workspace-designs.md`, `docs/design/D101-cli-workspace-design.md`, `docs/design/D102-web-workspace-design.md`, `docs/design/D103-host-bridge-integration-design.md`
  - review: `docs/reviews/spec-review-features-mainline.md`, `docs/reviews/design-review-entry-mainline.md`
  - approval: `docs/approvals/design-approval-entry-mainline.md`, `docs/approvals/tasks-approval-mainline.md`

## 1. 概述

本计划将当前 `T10` 到 `T15` 的实现切片收敛为单一可执行队列，优先保证：

- 入口与 runtime truth 先稳定，再推进治理、continuity、pack、hardening
- 每个任务均可被单任务推进并给出新鲜证据
- router 在 completion gate 后可稳定重选下一任务（无并列 ready 歧义）

## 2. 里程碑

| Milestone | 覆盖任务 | 退出标准 |
| --- | --- | --- |
| M1 Entry Surface Baseline | `T101` `T103` `T102` | 三入口共享 `SessionApi`，错误语义一致 |
| M2 Runtime Core Baseline | `T111` `T112` `T113` | runtime home/session/execution authority 主链稳定 |
| M3 Governance & Continuity | `T121` `T122` `T131` `T132` | workspace facts/governance/growth 主链可回读 |
| M4 Pack Collaboration | `T141` `T142` `T143` | contracts/registry/reference packs/cross-pack bridge 闭环 |
| M5 Hardening & Delivery | `T151` `T152` `T153` | secrets/ops/observability/web depth 形成交付闭环 |

## 3. 文件 / 工件影响图

- 核心代码与运行时: `src/bootstrap/`, `src/session/`, `src/execution/`, `src/governance/`, `src/bridge/`, `src/packs/`, `src/registry/`, `src/continuity/`
- 测试资产: `tests/`
- 任务与状态工件: `docs/tasks/`, `task-progress.md`, `docs/reviews/`, `docs/approvals/`
- 可观测/运维资产: `src/bootstrap/runtime_ops.py`（或等价模块）、trace/evidence 相关模块

## 4. 需求与设计追溯

| 追溯锚点 | 任务承接 |
| --- | --- |
| `F102/F103/F113` + `D101/D102/D103` | `T101` `T103` `T102` |
| `F111/F112/F121/F122/F123/F124/F161/F162/F163/F164` + `D10` | `T111` `T112` `T113` |
| `F131/F132/F133/F134/F141/F142/F143/F144` + `D121/D122` | `T121` `T122` `T131` `T132` |
| `F151/F152/F153/F154` + `D111/D112/D113` | `T141` `T142` `T143` |
| `F161/F163/F164/F102` + `D102/D103` | `T151` `T152` `T153` |

## 5. 任务拆解

### T101. CLI Entry Implementation
- 目标: 建立 CLI create/resume/attach/step 主路径
- 依赖: -
- Ready When: tasks plan approved
- 初始队列状态: ready
- Selection Priority: P1
- 触碰工件: `docs/tasks/T101-cli-entry-implementation.md`, `src/bootstrap/`, `src/session/`, `tests/test_cli.py`
- 测试设计种子: create/resume 正向链路；missing session 负向链路
- 验证方式: `pytest tests/test_cli.py tests/test_session_runtime_core.py`
- 预期证据: fail-first + CLI/session tests 转绿记录
- 完成条件: CLI 最小入口闭环与错误语义可回读

### T103. Host Bridge Implementation
- 目标: 固化 shared host bridge seam 与拒绝语义
- 依赖: T101
- Ready When: T101=done
- 初始队列状态: pending
- Selection Priority: P2
- 触碰工件: `docs/tasks/T103-host-bridge-implementation.md`, `src/bridge/`, `src/bootstrap/host_bridge*`, `tests/test_host_bridge.py`
- 测试设计种子: host inject 正向；authority_violation 负向
- 验证方式: `pytest tests/test_host_bridge.py tests/test_concrete_host_bridge.py`
- 预期证据: bridge tests 转绿 + 失败路径断言
- 完成条件: HostBridge 注入能力但不越权

### T102. Web Entry Implementation
- 目标: 建立 Web local-first session/workspace/review 最小工作面
- 依赖: T103
- Ready When: T103=done
- 初始队列状态: pending
- Selection Priority: P3
- 触碰工件: `docs/tasks/T102-web-entry-implementation.md`, `src/bootstrap/web.py`, `tests/test_web_control_plane.py`
- 测试设计种子: resume 恢复正向；facts_unavailable 降级路径
- 验证方式: `pytest tests/test_web_control_plane.py`
- 预期证据: web control-plane tests 转绿
- 完成条件: Web 不复制第二套 runtime truth

### T111. Runtime Home And Bootstrap
- 目标: 固化 runtime home/workspace topology 与 bootstrap authority
- 依赖: T102
- Ready When: T102=done
- 初始队列状态: pending
- Selection Priority: P4
- 触碰工件: `docs/tasks/T111-runtime-home-and-bootstrap-implementation.md`, `src/bootstrap/`, `tests/test_bootstrap.py`, `tests/test_install_layout.py`
- 测试设计种子: topology 正向；profile authority 冲突负向
- 验证方式: `pytest tests/test_bootstrap.py tests/test_install_layout.py`
- 预期证据: bootstrap/install tests 转绿
- 完成条件: bootstrap/topology 语义稳定且可复用

### T112. Session Runtime Core
- 目标: 补齐 neutral records + lifecycle + SessionApi core
- 依赖: T111
- Ready When: T111=done
- 初始队列状态: pending
- Selection Priority: P5
- 触碰工件: `docs/tasks/T112-session-runtime-core-implementation.md`, `src/session/`, `src/contracts/`, `tests/test_session_governance.py`
- 测试设计种子: lifecycle 状态转移正向；invalid transition 负向
- 验证方式: `pytest tests/test_session_governance.py tests/test_core_records.py`
- 预期证据: lifecycle/core records tests 转绿
- 完成条件: SessionApi/lifecycle/records 一致可回读

### T113. Execution Authority Implementation
- 目标: provider authority placement + execution trace mainline
- 依赖: T112
- Ready When: T112=done
- 初始队列状态: pending
- Selection Priority: P6
- 触碰工件: `docs/tasks/T113-execution-authority-implementation.md`, `src/execution/`, `tests/test_execution_runtime.py`, `tests/test_trace_ops.py`
- 测试设计种子: execution 正向；authority violation 负向
- 验证方式: `pytest tests/test_execution_runtime.py tests/test_trace_ops.py`
- 预期证据: execution/trace tests 转绿
- 完成条件: execution authority 与 trace 链路闭环

### T121. Workspace Facts & Artifact Routing
- 目标: workspace facts 与 artifact routing authority 化
- 依赖: T113
- Ready When: T113=done
- 初始队列状态: pending
- Selection Priority: P7
- 触碰工件: `docs/tasks/T121-workspace-facts-and-artifact-routing-implementation.md`, `src/surfaces/`, `src/governance/`, `tests/test_filebacked_surfaces.py`
- 测试设计种子: routing 正向；wrong destination 负向
- 验证方式: `pytest tests/test_filebacked_surfaces.py`
- 预期证据: surfaces/routing tests 转绿
- 完成条件: facts/routing owner 与路径规则稳定

### T122. Governance & Evidence
- 目标: gate/approval/archive/evidence 形成统一治理表面
- 依赖: T121
- Ready When: T121=done
- 初始队列状态: pending
- Selection Priority: P8
- 触碰工件: `docs/tasks/T122-governance-and-evidence-implementation.md`, `src/governance/`, `tests/test_session_governance.py`
- 测试设计种子: gate pass 正向；gate reject 负向
- 验证方式: `pytest tests/test_session_governance.py`
- 预期证据: governance tests 转绿
- 完成条件: gate/evidence/archive 可共同回读

### T131. Continuity Stores
- 目标: memory/skill continuity stores 与 readback 语义
- 依赖: T122
- Ready When: T122=done
- 初始队列状态: pending
- Selection Priority: P9
- 触碰工件: `docs/tasks/T131-continuity-stores-implementation.md`, `src/continuity/`, `tests/test_growth_engine.py`
- 测试设计种子: readback 正向；cross-bucket 混写负向
- 验证方式: `pytest tests/test_growth_engine.py`
- 预期证据: continuity tests 转绿
- 完成条件: continuity 边界清晰不与 evidence/session 混桶

### T132. Growth Proposal & Promotion
- 目标: evidence->proposal->promotion 受治理约束
- 依赖: T131
- Ready When: T131=done
- 初始队列状态: pending
- Selection Priority: P10
- 触碰工件: `docs/tasks/T132-growth-proposal-and-promotion-implementation.md`, `src/continuity/growth.py`, `tests/test_growth_engine.py`
- 测试设计种子: accepted/rejected/deferred 分支
- 验证方式: `pytest tests/test_growth_engine.py`
- 预期证据: growth lifecycle tests 转绿
- 完成条件: proposal lifecycle 可验证且治理边界明确

### T141. Shared Contracts & Registry
- 目标: contracts/schema/registry binding 基线
- 依赖: T132
- Ready When: T132=done
- 初始队列状态: pending
- Selection Priority: P11
- 触碰工件: `docs/tasks/T141-shared-contracts-and-registry-implementation.md`, `src/contracts/`, `src/registry/`, `tests/test_contract_registry.py`
- 测试设计种子: schema valid 正向；schema invalid 负向
- 验证方式: `pytest tests/test_contract_registry.py`
- 预期证据: contract/registry tests 转绿
- 完成条件: shared contracts 可被 runtime/governance/execution 共同消费

### T142. Reference Packs
- 目标: Product Insights/Coding reference packs 基线
- 依赖: T141
- Ready When: T141=done
- 初始队列状态: pending
- Selection Priority: P12
- 触碰工件: `docs/tasks/T142-reference-packs-implementation.md`, `src/packs/`, `tests/test_reference_pack_shells.py`
- 测试设计种子: pack discover 正向；invalid pack metadata 负向
- 验证方式: `pytest tests/test_reference_pack_shells.py`
- 预期证据: reference pack tests 转绿
- 完成条件: reference packs 具备稳定 capability calibration

### T143. Cross-Pack Bridge
- 目标: cross-pack handoff/acceptance/rework/lineage 流程
- 依赖: T142
- Ready When: T142=done
- 初始队列状态: pending
- Selection Priority: P13
- 触碰工件: `docs/tasks/T143-cross-pack-bridge-implementation.md`, `src/bridge/workflow.py`, `tests/test_bridge_workflow.py`
- 测试设计种子: handoff accept 正向；rework loop 负向
- 验证方式: `pytest tests/test_bridge_workflow.py`
- 预期证据: bridge workflow tests 转绿
- 完成条件: cross-pack 流程可追溯且可回退

### T151. Secrets, Doctor, Distribution
- 目标: secrets/doctor/distribution 主链收口
- 依赖: T143
- Ready When: T143=done
- 初始队列状态: pending
- Selection Priority: P14
- 触碰工件: `docs/tasks/T151-secrets-doctor-and-distribution-implementation.md`, `src/bootstrap/credential_resolution.py`, `src/bootstrap/runtime_home_doctor.py`, `tests/test_credential_resolution.py`, `tests/test_runtime_home_doctor.py`
- 测试设计种子: credential resolve 正向；missing credential 负向
- 验证方式: `pytest tests/test_credential_resolution.py tests/test_runtime_home_doctor.py`
- 预期证据: secrets/doctor tests 转绿
- 完成条件: authority-backed secrets + runtime doctor 可用

### T152. Runtime Ops & Observability
- 目标: diagnostics/trace/observability 运行可见性
- 依赖: T151
- Ready When: T151=done
- 初始队列状态: pending
- Selection Priority: P15
- 触碰工件: `docs/tasks/T152-runtime-ops-and-observability-implementation.md`, `src/bootstrap/runtime_ops.py`, `src/bootstrap/trace_ops.py`, `tests/test_runtime_ops.py`, `tests/test_trace_ops.py`
- 测试设计种子: trace readback 正向；missing trace 负向
- 验证方式: `pytest tests/test_runtime_ops.py tests/test_trace_ops.py`
- 预期证据: ops/trace tests 转绿
- 完成条件: runtime 问题可通过 diagnostics+trace+evidence 定位

### T153. Web Depth & Optional Orchestration
- 目标: 深化 WebEntry 表面，仅在主链稳定后推进 optional orchestration
- 依赖: T152
- Ready When: T152=done
- 初始队列状态: pending
- Selection Priority: P16
- 触碰工件: `docs/tasks/T153-web-depth-and-optional-orchestration-implementation.md`, `src/bootstrap/web.py`, `tests/test_web_control_plane.py`
- 测试设计种子: deeper web panel 正向；optional orchestration guardrail 负向
- 验证方式: `pytest tests/test_web_control_plane.py`
- 预期证据: web depth tests 转绿
- 完成条件: Web depth 增强且不破坏 shared truth

## 6. 依赖与关键路径

关键路径（单链，确保 auto 模式下始终唯一 ready）：

`T101 -> T103 -> T102 -> T111 -> T112 -> T113 -> T121 -> T122 -> T131 -> T132 -> T141 -> T142 -> T143 -> T151 -> T152 -> T153`

## 7. 完成定义与验证策略

- 每个任务完成必须满足：
  - 任务文档列出的最小交付物与验收点
  - 任务对应测试入口 fresh 绿证据
  - 实现交接块或等价验证记录已落盘
- full profile 下继续遵守：
  - `ahe-test-driven-dev` -> review chain -> `ahe-regression-gate` -> `ahe-completion-gate`

## 8. 当前活跃任务选择规则

- 若存在且仅存在一个 `ready` 任务，则将其锁定为 `Current Active Task`。
- 若出现多个 `ready` 任务或依赖状态冲突，停止自动推进并回到 `ahe-workflow-router`。
- 在 `ahe-tasks-review` 通过且 `任务真人确认` 完成前，不写入权威版 `Current Active Task`。

## 9. 任务队列投影视图 / Task Board Path

- Task Board Path: `docs/tasks/2026-04-13-garage-mainline-task-board.md`
- 初始投影:
  - `T101=ready`
  - 其余任务=`pending`
  - 每次 completion gate 后，根据依赖将下一任务置为 `ready`

## 10. 风险与顺序说明

- 风险 R1: 若跳过 entry/runtime 基线，后续治理与 packs 语义会漂移。缓解: 保持前半链路串行。
- 风险 R2: optional orchestration 过早推进会污染核心路径。缓解: 固定 `T153` 放在末尾。
- 风险 R3: 错误语义不统一导致跨入口不可恢复。缓解: 在 `T101/T102/T103` 明确负向测试种子。
