# M010: Garage Docs

- Document ID: `M010`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: `docs/` 是 `Garage` 的主文档树，采用按职责分层而不是按历史来源分层的组织方式，目标是让读者先找到“现在该读什么”，再进入具体长文。

## 1. 设计思想

当前 `docs/` 采用下面这组信息架构原则：

- `入口先于细节`：先给清晰入口，再进入长文。
- `按职责分层`：按 `architecture / design / features / tasks / wiki` 分组，而不是继续把所有内容堆在一个 `garage/` 目录下。
- `主线与参考分离`：`Garage` 主线文档与外部参考、历史分析分开维护。
- `一文一问`：每篇文档尽量只回答一个主要问题，避免重新长成总论文。

## 2. 当前目录结构

| 路径 | 作用 |
| --- | --- |
| `docs/VISION.md` | `Garage` 的愿景、产品哲学与 why |
| `docs/GARAGE.md` | `Garage` 的品牌定位、项目愿景、主线阅读顺序入口 |
| `docs/ROADMAP.md` | `docs/features/` 的 feature map、编号规则与当前路线图 |
| `docs/architecture/` | 平台中立的架构边界、核心子系统与 continuity 架构 |
| `docs/design/` | 子系统与 pack-specific 的详细设计，当前包括 skill anatomy、`Coding Pack` 与 `Product Insights Pack` |
| `docs/features/` | phase 1 的能力切面与共享语义，例如 contracts、governance、artifact surface、bridge、runtime bootstrap |
| `docs/tasks/` | phase 1 开发任务链与推荐实施顺序 |
| `docs/wiki/` | 外部项目分析、设计启发、采用方式、路径映射与参考资料；默认不作为当前主线真相源 |

## 3. 建议阅读顺序

如果你是第一次进入这个仓库，建议按下面顺序阅读：

1. `docs/README.md`
2. `docs/VISION.md`
3. `docs/GARAGE.md`
4. `docs/ROADMAP.md`
5. `docs/architecture/`
6. `docs/features/` 与 `docs/design/`
7. `docs/tasks/README.md`

如果你的目标更明确，也可以直接跳到对应入口：

- 想理解产品定位与整体愿景，读 `docs/GARAGE.md`
- 想理解 `Garage` 为什么存在、它想建立怎样的工作方式，读 `docs/VISION.md`
- 想理解 `docs/features/` 当前有哪些稳定 feature cuts、编号如何分配，读 `docs/ROADMAP.md`
- 想理解平台边界和核心设计，读 `docs/architecture/`
- 想理解 phase 1 的 contracts / bridge / artifact / governance，读 `docs/features/`
- 想理解两个 reference packs 的详细设计，读 `docs/design/`
- 想理解开发顺序与落地任务，读 `docs/tasks/README.md`
- 想看外部化、路径映射或历史参考，读 `docs/wiki/`

## 4. Docs 编号规则

整个 `docs/` 使用稳定的 `<prefix><NNN>` 文档 ID。

当前前缀如下：

- `M`：top-level main docs，例如 `docs/README.md`、`docs/VISION.md`、`docs/GARAGE.md`、`docs/ROADMAP.md`
- `A`：`docs/architecture/`
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
- `docs/tasks/README.md` 作为目录索引保留 canonical 文件名；单个 task docs 统一使用 `Txxx-<title-slug>.md`，其中 `Txxx` 是稳定检索 ID，推荐执行顺序由 `docs/tasks/README.md` 维护。

当前保留下面这些号段：

- `M000-M099`：top-level main docs
- `A000-A199`：architecture docs
- `D000-D199`：design docs
- `F000-F099`：core semantics、contracts、governance、artifact 与 continuity
- `F100-F199`：reference packs 与 cross-pack bridge
- `F200-F299`：runtime topology、bootstrap 与 execution
- `T000-T199`：task index 与 phase 1 execution tasks
- `W000-W199`：wiki / references

## 5. 维护约定

- `docs/VISION.md` 负责讲清楚 `Garage` 为什么存在、它想成为什么。
- `docs/GARAGE.md` 负责讲清楚 `Garage` 是什么、当前阶段在哪里、接下来应该读什么。
- `docs/ROADMAP.md` 负责维护 `docs/features/` 的 feature map、稳定 ID 与当前路线图。
- `docs/architecture/` 负责讲“平台为什么这样设计”和“边界怎么切”。
- `docs/design/` 负责讲具体 pack 或具体能力面的详细设计。
- `docs/features/` 负责讲 phase 1 的共享语义和稳定切面。
- `docs/tasks/` 只负责开发顺序、交付物与验收，不重复大段设计论证。
- `docs/wiki/` 负责外部项目分析、采用方式、路径映射与 supporting references，不应该反向成为当前主线的唯一依据。

## 6. 当前约束

- 默认只引用当前仓库中真实存在的路径。
- 不再新增新的 `docs/garage/` 兼容目录；主线文档直接落在现有分类中。
- 需要新增长文时，先判断它属于 `architecture`、`design`、`features`、`tasks` 还是 `wiki`，再创建文件。
