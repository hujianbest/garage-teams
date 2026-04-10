# Garage Phase 1 Development Tasks

- 状态: 草稿
- 日期: 2026-04-11
- 定位: `docs/garage/` 负责解释 `Garage` 的 phase 1 架构与边界；`docs/tasks/` 负责把这套设计按开发顺序拆成可执行的任务切面，避免所有内容堆成一篇超长文档。
- 当前阶段: phase 1
- 关联文档:
  - `docs/README.md`
  - `docs/garage/README.md`
  - `garage/README.md`

## 1. 这组文档回答什么

这组文档不再重复解释 `Garage` 为什么这样设计，而是回答下面这些执行问题：

- 应该先做什么，后做什么
- 哪些任务可以并行，哪些必须串行
- 每一阶段要交付什么
- 每一阶段完成后如何判断“可以进入下一阶段”

一句话说：

**`docs/garage/` 解释设计，`docs/tasks/` 解释开发顺序。**

## 2. 命名规则

- 目录入口使用 `docs/tasks/README.md`
- phase 1 的执行文档统一使用 `garage-phase1-XX-<topic>.md`
- `XX` 代表推荐开发顺序，而不是实现完成时间

## 3. 阅读与执行顺序

| 顺序 | 文件 | 目标 | 主要依赖 |
| --- | --- | --- | --- |
| 01 | `docs/tasks/garage-phase1-01-foundation-and-repository-layout.md` | 冻结 phase 1 仓库骨架、实现边界与入口规则 | `garage-extensible-architecture.md` |
| 02 | `docs/tasks/garage-phase1-02-core-runtime-records.md` | 落 `Garage Core` 的运行时对象与记录语义 | `garage-phase1-core-runtime-records.md` |
| 03 | `docs/tasks/garage-phase1-03-shared-contracts-and-registry.md` | 落共享 contracts、校验、加载与 registry | `garage-shared-contracts.md`、`garage-phase1-shared-contract-schemas.md` |
| 04 | `docs/tasks/garage-phase1-04-session-lifecycle-and-governance.md` | 落 session 主链、handoff、gate、approval 与 exception | `garage-phase1-session-lifecycle-and-handoffs.md`、`garage-phase1-governance-model.md` |
| 05 | `docs/tasks/garage-phase1-05-artifact-routing-and-evidence-surface.md` | 落 file-backed artifact / evidence surface | `garage-phase1-artifact-and-evidence-surface.md` |
| 06 | `docs/tasks/garage-phase1-06-continuity-and-promotion.md` | 落 continuity 分层与 promotion 规则 | `garage-continuity-memory-skill-architecture.md`、`garage-phase1-continuity-mapping-and-promotion.md` |
| 07 | `docs/tasks/garage-phase1-07-reference-pack-shells.md` | 搭两个 reference packs 的共同骨架 | `garage-phase1-reference-packs.md` |
| 08 | `docs/tasks/garage-phase1-08-product-insights-pack.md` | 落 `Product Insights Pack` | `garage-product-insights-pack-design.md` |
| 09 | `docs/tasks/garage-phase1-09-coding-pack.md` | 落 `Coding Pack` | `garage-coding-pack-design.md` |
| 10 | `docs/tasks/garage-phase1-10-cross-pack-bridge-and-phase1-walkthrough.md` | 打通 `product-insights -> coding` 主桥并做端到端走通 | `garage-phase1-cross-pack-bridge.md` |

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
| `garage-extensible-architecture.md` | `01`、`07` |
| `garage-core-subsystems-architecture.md` | `01`、`02`、`03`、`04`、`05` |
| `garage-phase1-core-runtime-records.md` | `02` |
| `garage-phase1-session-lifecycle-and-handoffs.md` | `04`、`10` |
| `garage-phase1-governance-model.md` | `04`、`06`、`10` |
| `garage-phase1-artifact-and-evidence-surface.md` | `05`、`10` |
| `garage-shared-contracts.md` | `03`、`07` |
| `garage-phase1-shared-contract-schemas.md` | `03` |
| `garage-continuity-memory-skill-architecture.md` | `06` |
| `garage-phase1-continuity-mapping-and-promotion.md` | `06`、`08`、`09` |
| `garage-phase1-reference-packs.md` | `07` |
| `garage-product-insights-pack-design.md` | `08` |
| `garage-coding-pack-design.md` | `09` |
| `garage-phase1-cross-pack-bridge.md` | `10` |

## 7. 使用方式

建议按下面方式使用这组文档：

1. 先从 `01` 到 `03` 搭出平台最小骨架。
2. 再从 `04` 到 `06` 落地 core 的控制流、文件表面和 continuity 规则。
3. 再从 `07` 到 `09` 搭 reference packs。
4. 最后用 `10` 验证整条 phase 1 主桥。

如果开发中发现某篇 task doc 变得过长，优先新增新的 phase 1 task 文档，而不是继续把所有细节塞回现有文档里。

## 8. 维护约定

- task docs 保持执行导向，不重复设计文档里的长篇论证。
- 设计变更优先回写 `docs/garage/`；任务变更优先回写 `docs/tasks/`。
- phase 2 或非 `Garage` 任务，不要继续塞进这组 phase 1 文档。
- 新增 task doc 时，先更新本页索引与依赖顺序。
