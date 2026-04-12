# M010: Garage Docs

- Document ID: `M010`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: `docs/` 是 `Garage` 的主文档树，用来维护完整架构、稳定能力切面、pack 设计与实施切片之间的清晰分工，让读者先理解“Garage 到底是什么系统”，再进入具体实现与演进细节。

## 1. 设计思想

当前 `docs/` 采用下面这组信息架构原则：

- `完整架构先于实施切片`：先把 `Garage` 的完整系统故事讲清楚，再讨论分阶段实现。
- `入口先于细节`：先给清晰入口，再进入长文。
- `按职责分层`：按 `architecture / design / features / tasks / wiki` 分组，而不是把所有内容混成一个总目录。
- `主线一致性优先`：修改 `architecture / design / features` 任一主线文档时，要回看同主题的另外两类文档，避免名称、边界、生命周期、图示或共享语义在主线内部漂移。
- `主线与参考分离`：`Garage` 主线文档与外部分析、历史资料、迁移参考分开维护。
- `一文一问`：每篇文档尽量只回答一个稳定问题，避免重复造出多个真相源。

## 2. 当前目录结构

| 路径 | 作用 |
| --- | --- |
| `docs/VISION.md` | `Garage` 的产品愿景、初衷与不可退让的产品哲学 |
| `docs/GARAGE.md` | `Garage` 的产品具体定义、当前能力、入口、边界与阅读入口 |
| `docs/ROADMAP.md` | `docs/features/` 的 feature map、能力分组与实施路线索引 |
| `docs/architecture/` | 以 `L0 / L1 / L2` 组织的架构主线：整体架构、分层架构、子系统架构 |
| `docs/design/` | pack-specific 或子系统级详细设计，例如 `Coding Pack` 与 `Product Insights Pack` |
| `docs/features/` | 跟随新 architecture 主线组织的稳定 capability families 与共享语义 |
| `docs/tasks/` | 实施切片、开发轨道与交付顺序；它们跟随主线设计，不反向拥有主线真相 |
| `docs/wiki/` | 外部项目分析、历史背景、采用方式、路径映射与 supporting references |

这里最重要的区分是：

- `architecture / features / design` 讲系统本体。
- `tasks` 讲如何逐步把系统做出来。
- `wiki` 讲外部参考和分析来源。

## 3. 建议阅读顺序

如果你是第一次进入这个仓库，建议按下面顺序阅读：

1. `docs/README.md`
2. `docs/VISION.md`
3. `docs/GARAGE.md`
4. `docs/ROADMAP.md`
5. `docs/architecture/`
6. `docs/features/`
7. `docs/design/`
8. `docs/tasks/README.md`

如果你想按新的架构主线细读，建议使用下面这条顺序：

`1 -> 2 -> 10/11/12 -> 20/21 -> 30/31 -> 40/41 -> 100+`

如果你的目标更明确，也可以直接跳到对应入口：

- 想理解 `Garage` 为什么必须存在、它想改变什么工作方式，读 `docs/VISION.md`
- 想理解 `Garage` 当前是什么产品、有哪些入口、能力和边界，读 `docs/GARAGE.md`
- 想理解 Garage Team runtime 的整体架构、分层关系与关键子系统，读 `docs/architecture/`
- 想理解产品能力、入口能力、governance、workspace truth、continuity、execution 与扩展语义，读 `docs/features/`
- 想理解 `Coding Pack`、`Product Insights Pack` 等详细设计，读 `docs/design/`
- 想理解能力 map、feature 分组与路线索引，读 `docs/ROADMAP.md`
- 想理解实施轨道与落地顺序，读 `docs/tasks/README.md`
- 想看外部参考、历史分析与映射资料，读 `docs/wiki/`

## 4. Docs 编号规则

整个 `docs/` 使用稳定的 `<prefix><NNN>` 文档 ID。

当前前缀如下：

- `M`：top-level main docs，例如 `docs/README.md`、`docs/VISION.md`、`docs/GARAGE.md`、`docs/ROADMAP.md`
- `A`：保留给旧架构文档引用；当前 architecture 主线改用 `L0/L1/L2` 数字分层文件名
- `D`：`docs/design/`
- `F`：`docs/features/`
- `T`：`docs/tasks/`
- `W`：`docs/wiki/`

通用约束如下：

- `NNN` 是稳定 ID，一旦分配就不应因为排序或重构而重新编号。
- 编号表达的是文档在信息架构中的稳定位置与扩展留白，不等于实现完成时间。
- 每篇文档头部都应显式写出对应的 `* ID` 元数据，并与文档自身 ID 保持一致。
- 每篇文档的一级标题都应使用 `# ID: 标题` 形式。
- 如果文件名使用编号前缀，文件名中的 ID 必须和头部 meta、一级标题保持一致。
- `docs/README.md`、`docs/VISION.md`、`docs/GARAGE.md`、`docs/ROADMAP.md` 为了入口稳定性保留 canonical 文件名，但仍使用 `Mxxx` 作为稳定文档 ID。
- `docs/architecture/` 当前按层次使用数字文件名：`L0=1位编号`、`L1=2位编号`、`L2=3位编号`。
- `docs/features/` 当前使用两层结构：family 使用 `F10-F19`，具体 spec 使用 `F101-F199`。
- `docs/design/` 当前使用两层结构：family 使用 `D10-D19`，具体 spec 使用 `D101-D199`。
- `docs/tasks/README.md` 作为目录索引保留 canonical 文件名；`docs/tasks/` 当前使用两层结构：family 使用 `T10-T19`，具体 task spec 使用 `T101-T199`。

当前保留下面这些号段：

- `M000-M099`：top-level main docs
- `A000-A199`：旧 architecture docs 预留引用区；当前主线不再继续扩展
- `D10-D19`：当前 design families
- `D101-D199`：当前 design specs
- `F10-F19`：顶层 feature families
- `F101-F199`：当前 feature specs 主线
- `T10-T19`：当前 task families
- `T101-T199`：当前 task specs
- `W000-W199`：wiki / references

## 5. 维护约定

- `docs/VISION.md` 负责讲清楚 `Garage` 为什么存在、它想改变什么工作方式，以及哪些产品哲学不能退让。
- `docs/GARAGE.md` 负责讲清楚 `Garage` 当前是什么产品、有哪些入口、能力、边界与主线阅读入口。
- `docs/ROADMAP.md` 负责维护 `docs/features/` 的 feature map、稳定 ID 与路线索引。
- `docs/architecture/` 负责讲“Garage Team runtime 应如何按 L0/L1/L2 分层设计”。
- `docs/design/` 负责讲具体 pack、入口或子系统的详细设计。
- `docs/features/` 负责讲稳定 capability families 与具体 capability specs 的共享系统语义。
- `docs/architecture/`、`docs/design/` 与 `docs/features/` 共同构成主线真相源；修改其中任一类时，应先从当前文档的 `关联文档` 和同主题邻近文档开始检查一致性。如名称、边界、生命周期、图示或共享语义发生变化，应同步更新相关 owner docs，或先明确需要回写的上游真相源。
- `docs/tasks/` 只负责实施切片、开发顺序、交付物与验收，不重复拥有主线设计真相。
- `docs/wiki/` 负责外部项目分析、采用方式、路径映射与 supporting references，不应反向成为当前主线的唯一依据。
- 当 `docs/VISION.md` 与 `docs/GARAGE.md` 的职责边界发生明显调整时，至少同步检查 `README.md`、`README.zh-CN.md`、`docs/ROADMAP.md` 与当前 `docs/architecture/` 主线入口文档是否仍沿用旧产品语言。

## 6. 当前约束

- 默认只引用当前仓库中真实存在的路径。
- 不再新增新的 `docs/garage/` 兼容目录；主线文档直接落在现有分类中。
- 需要新增长文时，先判断它属于 `architecture`、`design`、`features`、`tasks` 还是 `wiki`，再创建文件。
- 当“完整架构”和“阶段实施”发生冲突时，以 `architecture / features / design` 中的主线真相源为准，由 `tasks` 跟随收敛。
