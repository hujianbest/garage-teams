# M040: Garage Feature Roadmap

- Document ID: `M040`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: `docs/ROADMAP.md` 维护 `docs/features/` 的稳定 feature IDs、当前 feature map 与路线图，帮助读者按统一编号理解 `Garage` 的 feature cuts，而不是在文件树里手工猜顺序。
- 关联文档:
  - `docs/README.md`
  - `docs/VISION.md`
  - `docs/GARAGE.md`
  - `docs/tasks/README.md`

## 1. 这份文档回答什么

这份文档主要回答 3 个问题：

- `docs/features/` 的编号规则是什么
- 当前已经冻结了哪些 feature docs
- 这些 feature docs 和 `docs/tasks/` 的实施顺序如何对应

它不替代：

- `docs/GARAGE.md` 的主线叙事
- `docs/tasks/README.md` 的开发任务拆解
- 具体 feature 文档自身的详细设计

## 2. 编号规则

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

- `F000-F099`：core semantics、contracts、governance、artifact 与 continuity
- `F100-F199`：reference packs 与 cross-pack bridge
- `F200-F299`：runtime topology、bootstrap 与 execution

当前阶段只有 `docs/features/` 使用这套规则；`docs/design/` 和 `docs/tasks/` 继续维持各自的命名体系。

## 3. 如何读这份路线图

- `Status` 目前表示文档成熟度，而不是代码完成度。
- `draft` 表示 feature cut 已进入主线设计，但仍处于草稿阶段。
- 具体开发顺序以 `docs/tasks/README.md` 为准。
- 如果 feature 编号和 task 编号看起来不一致，以 feature 的稳定 ID 为目录顺序，以 task 的编号为实施顺序。

## 4. 当前 Feature Map

### F000-F099 Core Semantics

| ID | Feature | Status | 对应任务 | 链接 |
| --- | --- | --- | --- | --- |
| `F010` | Shared Contracts | `draft` | `03`、`07`、`12` | `docs/features/F010-shared-contracts.md` |
| `F020` | Shared Contract Schemas | `draft` | `03` | `docs/features/F020-shared-contract-schemas.md` |
| `F030` | Core Runtime Records | `draft` | `02` | `docs/features/F030-core-runtime-records.md` |
| `F040` | Session Lifecycle And Handoffs | `draft` | `04`、`10` | `docs/features/F040-session-lifecycle-and-handoffs.md` |
| `F050` | Governance Model | `draft` | `04`、`06`、`10`、`13` | `docs/features/F050-governance-model.md` |
| `F060` | Artifact And Evidence Surface | `draft` | `05`、`10`、`11`、`13` | `docs/features/F060-artifact-and-evidence-surface.md` |
| `F070` | Continuity Mapping And Promotion | `draft` | `06`、`08`、`09` | `docs/features/F070-continuity-mapping-and-promotion.md` |

### F100-F199 Packs And Bridge

| ID | Feature | Status | 对应任务 | 链接 |
| --- | --- | --- | --- | --- |
| `F110` | Reference Packs | `draft` | `07` | `docs/features/F110-reference-packs.md` |
| `F120` | Cross-Pack Bridge | `draft` | `10` | `docs/features/F120-cross-pack-bridge.md` |

### F200-F299 Runtime Topology And Execution

| ID | Feature | Status | 对应任务 | 链接 |
| --- | --- | --- | --- | --- |
| `F210` | Runtime Home And Workspace Topology | `draft` | `11`、`12` | `docs/features/F210-runtime-home-and-workspace-topology.md` |
| `F220` | Runtime Bootstrap And Entrypoints | `draft` | `12` | `docs/features/F220-runtime-bootstrap-and-entrypoints.md` |
| `F230` | Runtime Provider And Tool Execution | `draft` | `13` | `docs/features/F230-runtime-provider-and-tool-execution.md` |

## 5. 与 Task 链的关系

这份路线图按 feature family 排序，方便理解系统边界和目录结构。

真正进入开发时，建议仍然按 `docs/tasks/README.md` 的顺序推进：

1. 先落 `F030`、`F010`、`F020`
2. 再落 `F040`、`F050`、`F060`、`F070`
3. 再落 `F110`、`F120`
4. 最后落 `F210`、`F220`、`F230`

## 6. 后续新增 Feature 的分配建议

未来新增 `docs/features/` 文档时，建议遵守：

- 不修改已有 ID
- 优先在对应号段内补空号
- pack-specific 详细设计继续放在 `docs/design/`
- 如果一个主题已经明显变成实施任务，而不是 feature cut，应新增到 `docs/tasks/`，而不是塞回 `docs/features/`

## 7. 一句话总结

`docs/ROADMAP.md` 的作用，不是替代详细设计，而是给 `docs/features/` 提供一套稳定、可排序、可引用的 feature ID 体系，让 `Garage` 的主线能力切面从文件树层面就具备长期可维护性。
