# T000: Garage Implementation Tracks

- Task ID: `T000`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: `docs/architecture/`、`docs/design/` 与 `docs/features/` 负责解释 `Garage` 的完整系统边界；`docs/tasks/` 负责把这套边界按实施顺序拆成 delivery slices。当前 `T010-T130` 是第一组主要实施切片，它们不再拥有产品主线定义权，只负责承接当前实现顺序。
- 当前阶段: 完整架构主线下的第一组实施切片
- 关联文档:
  - `docs/README.md`
  - `docs/GARAGE.md`
  - `docs/ROADMAP.md`
  - `packs/README.md`

## 1. 这组文档回答什么

这组文档不再重复解释 `Garage` 为什么这样设计，而是回答下面这些执行问题：

- 应该先做什么，后做什么
- 哪些任务可以并行，哪些必须串行
- 每个 delivery slice 要交付什么
- 当前实现如何对齐完整架构

一句话说：

**`docs/architecture/`、`docs/design/`、`docs/features/` 解释系统真相，`docs/tasks/` 解释当前交付顺序。**

## 2. 如何阅读当前任务树

理解这组任务文档时，请先记住下面 4 个判断：

1. 先读 `docs/architecture/`、`docs/features/`、`docs/design/`，再读 `docs/tasks/`。
2. 当前 `T010-T130` 是第一组 implementation tracks，不是完整架构的全文镜像。
3. task 文件名已经统一对齐到 `Txxx-<title-slug>.md` 规则，但这些文档仍然只是当前 implementation tracks。
4. 当设计文档和 task 文档冲突时，应先回写设计文档，再重切任务文档。

## 3. 命名规则

- 目录入口使用 `docs/tasks/README.md`
- `docs/tasks/README.md` 保留目录索引入口的 canonical 文件名
- task docs 统一使用稳定 `Txxx` 作为 identity
- 当前 `T010-T130` 保留既有文件路径
- 未来新增 task docs 继续使用 `Txxx-<title-slug>.md`

## 4. 当前 implementation tracks

| Track | Task IDs | 目标 | 主要输入 |
| --- | --- | --- | --- |
| Runtime Foundations | `T010-T060` | 搭基础 runtime skeleton、records、contracts、governance、artifact / evidence surface 与 continuity baseline | `A110`、`A120`、`A130`、`F010`、`F030`、`F050`、`F060`、`F070`、`F080` |
| Reference Packs And Bridge | `T070-T100` | 搭 `Product Insights Pack`、`Coding Pack` 与当前 cross-pack bridge | `F110`、`F120`、`D110`、`D120`、`F070`、`F080` |
| Standalone Runtime Surfaces | `T110-T130` | 把当前 repo-local 形态继续推进到 runtime topology、bootstrap 与 execution layer | `F210`、`F220`、`F230`、`F050`、`F060`、`F080` |

## 5. 当前详细交付顺序

| 顺序 | Task ID | 文件 | 当前角色 | 主要依赖 |
| --- | --- | --- | --- | --- |
| 01 | `T010` | `docs/tasks/T010-garage-foundation-and-repository-layout.md` | 第一组 runtime foundation 的仓库骨架与边界起点 | `A110-garage-extensible-architecture.md` |
| 02 | `T020` | `docs/tasks/T020-garage-core-runtime-records.md` | 落 `Garage Core` 的运行时对象与记录语义 | `F030-core-runtime-records.md` |
| 03 | `T030` | `docs/tasks/T030-garage-shared-contracts-and-registry.md` | 落 shared contracts、校验、加载与 registry | `F010-shared-contracts.md`、`F020-shared-contract-schemas.md` |
| 04 | `T040` | `docs/tasks/T040-garage-session-lifecycle-and-governance.md` | 落 session 主链、handoff、gate、approval 与 exception | `F040-session-lifecycle-and-handoffs.md`、`F050-governance-model.md` |
| 05 | `T050` | `docs/tasks/T050-garage-artifact-routing-and-evidence-surface.md` | 落 workspace-first artifact / evidence surface | `F060-artifact-and-evidence-surface.md` |
| 06 | `T060` | `docs/tasks/T060-garage-continuity-and-promotion.md` | 落 continuity、promotion baseline 与学习 loop 的第一层实现切片 | `A130-garage-continuity-memory-skill-architecture.md`、`F070-continuity-mapping-and-promotion.md`、`F080-garage-self-evolving-learning-loop.md` |
| 07 | `T070` | `docs/tasks/T070-garage-reference-pack-shells.md` | 搭两个 reference packs 的共同骨架 | `F110-reference-packs.md` |
| 08 | `T080` | `docs/tasks/T080-garage-product-insights-pack.md` | 落 `Product Insights Pack`，并对齐成长 loop 的 candidate mapping | `D110-garage-product-insights-pack-design.md`、`F070-continuity-mapping-and-promotion.md`、`F080-garage-self-evolving-learning-loop.md` |
| 09 | `T090` | `docs/tasks/T090-garage-coding-pack.md` | 落 `Coding Pack`，并对齐成长 loop 的 candidate mapping | `D120-garage-coding-pack-design.md`、`F070-continuity-mapping-and-promotion.md`、`F080-garage-self-evolving-learning-loop.md` |
| 10 | `T100` | `docs/tasks/T100-garage-cross-pack-bridge-and-walkthrough.md` | 打通当前 reference packs 主桥并做端到端走通 | `F120-cross-pack-bridge.md` |
| 11 | `T110` | `docs/tasks/T110-garage-runtime-home-and-workspace-topology.md` | 把 repo-local dogfooding 形态提升成显式 `runtime home / workspace` 拓扑 | `F210-runtime-home-and-workspace-topology.md`、`F060-artifact-and-evidence-surface.md` |
| 12 | `T120` | `docs/tasks/T120-garage-runtime-bootstrap-and-entrypoints.md` | 落统一 launcher、profile / workspace / host binding 与 create / resume 启动链 | `F220-runtime-bootstrap-and-entrypoints.md`、`F210-runtime-home-and-workspace-topology.md` |
| 13 | `T130` | `docs/tasks/T130-garage-runtime-provider-and-tool-execution.md` | 落 provider adapters、tool registry、execution trace 与受治理的 runtime execution layer | `F230-runtime-provider-and-tool-execution.md`、`F080-garage-self-evolving-learning-loop.md` |

## 6. 当前 implementation guardrails

所有 task docs 默认继承下面这些约束：

- task docs 跟随设计真相，不反向定义架构
- `Markdown-first`
- `file-backed`
- `Contract-first`
- core 只理解中立对象，不吸收 pack 领域词
- 新增能力优先通过 pack 扩展，而不是修改 core 语义
- `evidence -> proposal -> governance -> update` 是 canonical growth loop
- workspace-first growth 优先于全局自动共享
- 不新增独立 `BridgeContract`
- one runtime, many entry surfaces
- `workspace facts` 不被 `runtime home` 吞并
- packs 只声明 capabilities，不绑定 vendors
- provider differences stay below core

## 7. 设计到任务的映射

| 设计文档 | 当前主要落到哪些 task docs |
| --- | --- |
| `A110-garage-extensible-architecture.md` | `T010`、`T070` |
| `A120-garage-core-subsystems-architecture.md` | `T010`、`T020`、`T030`、`T040`、`T050`、`T120`、`T130` |
| `A130-garage-continuity-memory-skill-architecture.md` | `T060` |
| `A140-garage-system-architecture.md` | 作为全部切片的 system-level 对齐输入 |
| `F220-runtime-bootstrap-and-entrypoints.md` | `T120` |
| `F230-runtime-provider-and-tool-execution.md` | `T130` |
| `F210-runtime-home-and-workspace-topology.md` | `T110`、`T120` |
| `F030-core-runtime-records.md` | `T020` |
| `F040-session-lifecycle-and-handoffs.md` | `T040`、`T100` |
| `F050-governance-model.md` | `T040`、`T060`、`T100`、`T130` |
| `F060-artifact-and-evidence-surface.md` | `T050`、`T100`、`T110`、`T130` |
| `F010-shared-contracts.md` | `T030`、`T070`、`T120` |
| `F020-shared-contract-schemas.md` | `T030` |
| `F070-continuity-mapping-and-promotion.md` | `T060`、`T080`、`T090` |
| `F080-garage-self-evolving-learning-loop.md` | `T060`、`T080`、`T090`、`T130` |
| `F110-reference-packs.md` | `T070` |
| `D110-garage-product-insights-pack-design.md` | `T080` |
| `D120-garage-coding-pack-design.md` | `T090` |
| `F120-cross-pack-bridge.md` | `T100` |

## 8. 后续重切建议

当前任务树仍然是第一组实施切片，因此建议在主线设计稳定后优先重切下面这些方向：

- 为 `F080` 单独切出更明确的 growth engine / runtime update delivery slice
- 把 `T060` 从 continuity baseline 扩成更完整的 proposal lifecycle implementation track
- 在新增 capability packs 前，先明确它们复用现有 growth loop 的方式

## 9. 维护约定

- task docs 保持执行导向，不重复设计文档里的长篇论证。
- 设计变更优先回写 `docs/architecture/`、`docs/design/` 或 `docs/features/`；任务变更优先回写 `docs/tasks/`。
- 新增 task doc 时，先更新本页索引与依赖顺序。
- 如果某个 task 已经明显变成独立 capability 或稳定系统语义，应把真相源提升回 `docs/features/` 或 `docs/architecture/`，而不是继续堆在 task doc 里。
