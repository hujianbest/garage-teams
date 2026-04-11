# M040: Garage Feature Roadmap

- Document ID: `M040`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: `docs/ROADMAP.md` 维护 `docs/features/` 的稳定 feature IDs、当前 capability map 与实施切片映射，帮助读者先按完整架构理解 `Garage` 的能力切面，再进入 `docs/tasks/` 查看当前交付顺序。
- 关联文档:
  - `docs/README.md`
  - `docs/VISION.md`
  - `docs/GARAGE.md`
  - `docs/tasks/README.md`

## 1. 这份文档回答什么

这份文档主要回答 3 个问题：

- `docs/features/` 的编号规则是什么
- 当前完整架构已经冻结了哪些 feature cuts
- 这些 feature cuts 当前由哪些 implementation slices 承接

它不替代：

- `docs/GARAGE.md` 的主线叙事
- `docs/tasks/README.md` 的实施顺序索引
- 具体 feature 文档自身的详细设计

## 2. 读这份路线图时要先记住的事

- `docs/features/` 负责稳定 capability cuts，不负责阶段性开发故事。
- `docs/tasks/` 负责当前 implementation slices，不反向拥有系统真相。
- `Status` 表示文档成熟度，而不是代码完成度。
- 当 feature 语义和 task 语义冲突时，以 `docs/features/` 为准，再回头重切 `docs/tasks/`。

## 3. 编号规则

`docs/features/` 统一使用：

- `FNNN-<topic>.md`

规则如下：

1. `F` 代表 feature doc。
2. `NNN` 是稳定编号，一旦分配就不应因目录整理而重新编号。
3. 编号的主要作用是让目录有序、让引用稳定、为后续插入新 feature 留空位。
4. 编号表达的是 feature family 的稳定位置，不等于实现完成时间。
5. 每篇 `docs/features/` 文档头部都应包含显式的 `Feature ID` 元数据，并与文件名中的 `FNNN` 保持一致。
6. 每篇 `docs/features/` 文档的一级标题都应使用 `# FNNN: 标题` 形式，与文件名和 `Feature ID` 保持一致。

当前保留下面这些号段：

- `F000-F099`：core semantics、contracts、governance、artifact、continuity 与 learning
- `F100-F199`：reference packs 与 cross-pack collaboration
- `F200-F299`：runtime topology、bootstrap、execution 与 runtime evolution

## 4. 当前 Feature Map

### F000-F099 Core Semantics And Learning

| ID | Feature | 作用 | 当前实施切片 | 链接 |
| --- | --- | --- | --- | --- |
| `F010` | Shared Contracts | 冻结 core 与 packs 的共同语言 | `T030`、`T070`、`T120` | `docs/features/F010-shared-contracts.md` |
| `F020` | Shared Contract Schemas | 冻结 contract schema shapes | `T030` | `docs/features/F020-shared-contract-schemas.md` |
| `F030` | Core Runtime Records | 冻结 runtime records 与持久记录语义 | `T020` | `docs/features/F030-core-runtime-records.md` |
| `F040` | Session Lifecycle And Handoffs | 冻结 session 主链与交接边界 | `T040`、`T100` | `docs/features/F040-session-lifecycle-and-handoffs.md` |
| `F050` | Governance Model | 冻结 rules、gates、approval、archive 与 growth governance 语义 | `T040`、`T060`、`T100`、`T130` | `docs/features/F050-governance-model.md` |
| `F060` | Artifact And Evidence Surface | 冻结 workspace-first artifact / evidence surfaces | `T050`、`T100`、`T110`、`T130` | `docs/features/F060-artifact-and-evidence-surface.md` |
| `F070` | Continuity Mapping And Promotion | 冻结 pack-specific continuity mapping 与晋升规则 | `T060`、`T080`、`T090` | `docs/features/F070-continuity-mapping-and-promotion.md` |
| `F080` | Self-Evolving Learning Loop | 冻结主动成长 loop、本地 proposal persistence 与长期更新路径 | `T060`、`T080`、`T090`、`T130` | `docs/features/F080-garage-self-evolving-learning-loop.md` |

### F100-F199 Packs And Cross-Pack Collaboration

| ID | Feature | 作用 | 当前实施切片 | 链接 |
| --- | --- | --- | --- | --- |
| `F110` | Reference Packs | 定义当前 reference packs 的平台角色 | `T070` | `docs/features/F110-reference-packs.md` |
| `F120` | Cross-Pack Bridge | 定义 `product-insights -> coding` 与后续 pack handoff seam | `T100` | `docs/features/F120-cross-pack-bridge.md` |

### F200-F299 Runtime Topology And Execution

| ID | Feature | 作用 | 当前实施切片 | 链接 |
| --- | --- | --- | --- | --- |
| `F210` | Runtime Home And Workspace Topology | 定义 `source root / runtime home / workspace` 拓扑 | `T110`、`T120` | `docs/features/F210-runtime-home-and-workspace-topology.md` |
| `F220` | Runtime Bootstrap And Entrypoints | 定义多入口统一 bootstrap 链 | `T120` | `docs/features/F220-runtime-bootstrap-and-entrypoints.md` |
| `F230` | Runtime Provider And Tool Execution | 定义 execution layer 与 provider / tool 边界 | `T130` | `docs/features/F230-runtime-provider-and-tool-execution.md` |

## 5. Feature 与 Task 的关系

这份路线图按 feature family 排序，方便理解系统边界和能力分层。

真正进入开发时，建议这样理解 `docs/tasks/`：

- `docs/tasks/` 记录当前 implementation slices
- 当前 `T010-T130` 是第一组主要实施切片
- 当前 task 文件名已经对齐到 `Txxx-<title-slug>.md` 规则，但这些文档仍然只是 implementation slices

因此：

- 先读 `docs/features/` 理解系统应该具备什么能力
- 再读 `docs/tasks/README.md` 理解当前先交付哪一部分

## 6. 当前实施切片的三组主线

当前任务链大致可以看成 3 组：

1. `T010-T060`
   - 搭 runtime foundation、contracts、session、governance、artifact / evidence surface、continuity baseline
2. `T070-T100`
   - 搭 reference packs 与 cross-pack bridge
3. `T110-T130`
   - 把 repo-local 形态继续推向独立 runtime topology、bootstrap 与 execution layer

其中 `F080` 是一个跨切片 feature：

- 它当前由 `T060`、`T080`、`T090`、`T130` 分散承接
- 后续当实现语义稳定后，再考虑单独切出更明确的 growth-engine delivery slice

## 7. 后续新增 Feature 的分配建议

未来新增 `docs/features/` 文档时，建议遵守：

- 不修改已有 ID
- 优先在对应号段内补空号
- pack-specific 详细设计继续放在 `docs/design/`
- 如果一个主题已经明显变成 implementation track，而不是 capability cut，应新增到 `docs/tasks/`，而不是塞回 `docs/features/`

## 8. 一句话总结

`docs/ROADMAP.md` 的作用，不是替代详细设计或任务拆解，而是给 `docs/features/` 提供一套稳定、可排序、可引用的 feature family 视图，并明确这些能力当前由哪些 implementation slices 承接。
