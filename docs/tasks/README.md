# T000: Garage Phase 1 Development Tasks

- Task ID: `T000`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: `docs/architecture/`、`docs/design/` 与 `docs/features/` 负责解释 `Garage` 的 phase 1 设计与边界；`docs/tasks/` 负责把这套设计按开发顺序拆成可执行的任务切面，避免所有内容堆成一篇超长文档。
- 当前阶段: phase 1
- 关联文档:
  - `docs/README.md`
  - `docs/GARAGE.md`
  - `packs/README.md`

## 1. 这组文档回答什么

这组文档不再重复解释 `Garage` 为什么这样设计，而是回答下面这些执行问题：

- 应该先做什么，后做什么
- 哪些任务可以并行，哪些必须串行
- 每一阶段要交付什么
- 每一阶段完成后如何判断“可以进入下一阶段”

一句话说：

**`docs/architecture/`、`docs/design/`、`docs/features/` 解释设计，`docs/tasks/` 解释开发顺序。**

## 2. 命名规则

- 目录入口使用 `docs/tasks/README.md`
- `docs/tasks/README.md` 保留目录索引入口的 canonical 文件名
- phase 1 的执行文档统一使用 `Txxx-<title-slug>.md`
- `Txxx` 代表稳定 task identity；当前 `01..13` 对应 `T010..T130`
- 推荐开发顺序继续由本页表格维护，而不是再编码进文件名前缀

## 3. 阅读与执行顺序

| 顺序 | Task ID | 文件 | 目标 | 主要依赖 |
| --- | --- | --- | --- | --- |
| 01 | `T010` | `docs/tasks/T010-garage-phase-1-foundation-and-repository-layout.md` | 冻结 phase 1 仓库骨架、实现边界与入口规则 | `A110-garage-extensible-architecture.md` |
| 02 | `T020` | `docs/tasks/T020-garage-phase-1-core-runtime-records.md` | 落 `Garage Core` 的运行时对象与记录语义 | `F030-core-runtime-records.md` |
| 03 | `T030` | `docs/tasks/T030-garage-phase-1-shared-contracts-and-registry.md` | 落共享 contracts、校验、加载与 registry | `F010-shared-contracts.md`、`F020-shared-contract-schemas.md` |
| 04 | `T040` | `docs/tasks/T040-garage-phase-1-session-lifecycle-and-governance.md` | 落 session 主链、handoff、gate、approval 与 exception | `F040-session-lifecycle-and-handoffs.md`、`F050-governance-model.md` |
| 05 | `T050` | `docs/tasks/T050-garage-phase-1-artifact-routing-and-evidence-surface.md` | 落 file-backed artifact / evidence surface | `F060-artifact-and-evidence-surface.md` |
| 06 | `T060` | `docs/tasks/T060-garage-phase-1-continuity-and-promotion.md` | 落 continuity 分层与 promotion 规则 | `A130-garage-continuity-memory-skill-architecture.md`、`F070-continuity-mapping-and-promotion.md` |
| 07 | `T070` | `docs/tasks/T070-garage-phase-1-reference-pack-shells.md` | 搭两个 reference packs 的共同骨架 | `F110-reference-packs.md` |
| 08 | `T080` | `docs/tasks/T080-garage-phase-1-product-insights-pack.md` | 落 `Product Insights Pack` | `D110-garage-product-insights-pack-design.md` |
| 09 | `T090` | `docs/tasks/T090-garage-phase-1-coding-pack.md` | 落 `Coding Pack` | `D120-garage-coding-pack-design.md` |
| 10 | `T100` | `docs/tasks/T100-garage-phase-1-cross-pack-bridge-and-phase-1-walkthrough.md` | 打通 `product-insights -> coding` 主桥并做端到端走通 | `F120-cross-pack-bridge.md` |
| 11 | `T110` | `docs/tasks/T110-garage-phase-1-runtime-home-and-workspace-topology.md` | 把当前 repo-local dogfooding 形态提升成可显式绑定 `runtime home / workspace` 的运行时拓扑 | `F210-runtime-home-and-workspace-topology.md`、`F060-artifact-and-evidence-surface.md` |
| 12 | `T120` | `docs/tasks/T120-garage-phase-1-runtime-bootstrap-and-entrypoints.md` | 落统一 launcher、profile / workspace / host binding 与 create / resume 启动链 | `F220-runtime-bootstrap-and-entrypoints.md`、`F210-runtime-home-and-workspace-topology.md` |
| 13 | `T130` | `docs/tasks/T130-garage-phase-1-runtime-provider-and-tool-execution.md` | 落 provider adapters、tool registry、execution trace 与可治理的 runtime execution layer | `F230-runtime-provider-and-tool-execution.md` |

## 4. phase 1 guardrails

所有 task docs 默认继承下面这些约束：

- `Markdown-first`
- `file-backed`
- `Contract-first`
- core 只理解中立对象，不吸收 pack 领域词
- 新增能力优先通过 pack 扩展，而不是修改 core 语义
- 不新增独立 `BridgeContract`
- continuity 默认保守，不做自动晋升
- 不先做重型 database-first 控制面
- 不先做多租户、多人实时协作和复杂权限系统
- one runtime, many entry surfaces
- `workspace facts` 不被 `runtime home` 吞并
- packs 只声明 capabilities，不绑定 vendor
- provider differences stay below core

## 5. 统一文档结构

每篇 task doc 尽量保持短小，并统一使用下面这组结构：

- 任务目标
- 输入设计文档
- 本文范围
- 非目标
- 交付物
- 实施任务拆解
- 依赖与并行建议
- 验收与验证
- 完成后进入哪一篇

## 6. 设计到任务的映射

| 设计文档 | 主要落到哪些 task docs |
| --- | --- |
| `A110-garage-extensible-architecture.md` | `01`、`07` |
| `A120-garage-core-subsystems-architecture.md` | `01`、`02`、`03`、`04`、`05`、`12`、`13` |
| `F220-runtime-bootstrap-and-entrypoints.md` | `12` |
| `F230-runtime-provider-and-tool-execution.md` | `13` |
| `F210-runtime-home-and-workspace-topology.md` | `11`、`12` |
| `F030-core-runtime-records.md` | `02` |
| `F040-session-lifecycle-and-handoffs.md` | `04`、`10` |
| `F050-governance-model.md` | `04`、`06`、`10`、`13` |
| `F060-artifact-and-evidence-surface.md` | `05`、`10`、`11`、`13` |
| `F010-shared-contracts.md` | `03`、`07`、`12` |
| `F020-shared-contract-schemas.md` | `03` |
| `A130-garage-continuity-memory-skill-architecture.md` | `06` |
| `F070-continuity-mapping-and-promotion.md` | `06`、`08`、`09` |
| `F110-reference-packs.md` | `07` |
| `D110-garage-product-insights-pack-design.md` | `08` |
| `D120-garage-coding-pack-design.md` | `09` |
| `F120-cross-pack-bridge.md` | `10` |

## 7. 使用方式

建议按下面方式使用这组文档：

1. 先从 `01` 到 `03` 搭出平台最小骨架。
2. 再从 `04` 到 `06` 落地 core 的控制流、文件表面和 continuity 规则。
3. 再从 `07` 到 `10` 验证两个 reference packs 与主桥的 phase 1 平台语义。
4. 最后从 `11` 到 `13` 把当前 repo-local dogfooding 形态往“独立可运行程序”方向推进。

如果开发中发现某篇 task doc 变得过长，优先新增新的 phase 1 task 文档，而不是继续把所有细节塞回现有文档里。

## 8. 维护约定

- task docs 保持执行导向，不重复设计文档里的长篇论证。
- 设计变更优先回写 `docs/architecture/`、`docs/design/` 或 `docs/features/`；任务变更优先回写 `docs/tasks/`。
- phase 2 或非 `Garage` 任务，不要继续塞进这组 phase 1 文档。
- 新增 task doc 时，先更新本页索引与依赖顺序。
