# A105: Garage Team Workspace And First-Class Objects

- Architecture ID: `A105`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 在 `docs/VISION.md` 与 `docs/GARAGE.md` 已明确 `Garage` 是一个辅助创作者的 `Agent Teams` 工作环境之后，先冻结什么是 `Garage Team`、什么是一等产品对象，以及 workspace surfaces 如何锚定 team 的长期状态。
- 当前阶段: 完整架构主线，实施将按切片推进
- 关联文档:
  - `docs/VISION.md`
  - `docs/GARAGE.md`
  - `docs/architecture/A110-garage-extensible-architecture.md`
  - `docs/architecture/A115-product-surfaces-and-host-capability-injection.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F060-artifact-and-evidence-surface.md`
  - `docs/features/F210-runtime-home-and-workspace-topology.md`

## 1. 文档目标与范围

这篇文档只回答一个问题：

**如果 `Garage` 首先是一个 `Agent Teams` 工作环境，那么什么是 `Garage Team`，哪些对象必须是一等产品对象，workspace surfaces 又怎样把这个团队锚定成长期存在的工作环境。**

本文覆盖：

- `Garage Team` 的产品和系统双重定义
- 哪些对象是一等产品对象，哪些对象是二级运行时对象
- `Garage Team` 与 workspace surfaces 的关系
- `Garage Team` 与 `Session`、`memory`、`skill`、`packs` 的关系

本文不覆盖：

- 具体 runtime 子系统图
- 具体 feature schema 和字段细节
- 具体 pack 角色树或节点图
- 具体任务拆解与交付顺序

## 2. 为什么要先冻结这篇文档

在新的产品主线下，`Garage` 不再应该先被理解成：

- 一个更强的聊天工具
- 一个 model/tool 管理台
- 一个只有开发者才能真正使用的集成框架

它首先应该被理解成：

- 一个工作环境
- 一个团队环境
- 一个让创作者进入自己的 `Garage Team` 并长期培养它的产品

如果缺少这一层冻结，后续 architecture 很容易继续沿着旧路径漂移：

- 把模型、工具、provider 开关错当成产品主对象
- 把 `Garage Team` 只写成愿景修辞，而不是系统对象
- 把 workspace surfaces 只看成文件输出目录，而不是团队长期状态的锚点

## 3. `Garage Team` 的正式定义

`Garage Team` 同时具有两层含义。

### 3.1 产品层定义

对用户来说，`Garage Team` 是：

- 用户在 `Garage` 中拥有并培养的一支 AI 团队
- 用户进入 `Garage` 时真正进入的工作环境主体
- 用户长期协作、复查、沉淀、训练和扩展的对象

### 3.2 系统层定义

对系统来说，`Garage Team` 是：

- 一组运行在统一 runtime 之上的 agents、roles、handoffs、reviews、memory、skills 与 governance 关系
- 一个能够通过统一 `SessionApi`、workspace facts 与 growth paths 持续扩展和持续成长的 team runtime 实例

因此，`Garage Team` 既不是纯 UI 概念，也不是纯架构隐喻，而是产品对象和系统对象的重叠面。

## 4. 一等产品对象与二级运行时对象

在新的产品主线下，一等产品对象应当包括：

- `Garage Team`
- `agent`
- `role`
- `handoff`
- `review`
- `session`
- `memory`
- `skill`
- `workspace facts`

这些对象之所以是一等对象，是因为它们直接决定用户如何理解和使用产品。

二级运行时对象则包括：

- model provider
- tool backend
- adapter settings
- transport details
- execution internals

这些对象依然重要，但它们不应成为用户理解 `Garage` 的第一语言。

## 5. `Garage Team` 与 workspace surfaces

`Garage Team` 之所以能成为长期工作环境，而不是一次性对话壳，关键在于它有稳定的 workspace 锚点。

当前主线下，这个锚点主要是：

- `artifacts/`
- `evidence/`
- `sessions/`
- `archives/`
- `.garage/`

这意味着：

- `Garage Team` 的长期状态优先锚定在 workspace-first facts 上
- 团队的协作结果、审计记录、session 主线和 sidecars 都能够被回读
- 团队不是宿主窗口里的短暂状态，而是围绕 workspace 持续存在

## 6. `Garage Team` 与其他核心对象的关系

### 6.1 与 `Session`

- `Session` 是 `Garage Team` 在某条当前工作主线上的推进边界
- `Garage Team` 高于单次 `Session` 存在

### 6.2 与 `memory`

- `memory` 是 `Garage Team` 的长期事实层
- 它不等于 session 历史，也不等于 evidence 桶

### 6.3 与 `skill`

- `skill` 是 `Garage Team` 的可复用方法层
- 它表达“团队以后怎样做得更好”，而不是“这次做过什么”

### 6.4 与 `packs`

- packs 扩展的是 `Garage Team` 的能力面
- packs 不等于团队本身，也不应替代团队作为一等产品对象

## 7. 边界上的 5 条红线

1. `Garage Team` 不能退化成模型清单或工具清单。
2. workspace surfaces 不能退化成单纯输出目录，它们必须继续承担 team state 的长期锚点职责。
3. `Session` 不能被误写成 `Garage Team` 的全部真相。
4. packs 扩展团队能力，但不能取代团队作为产品主对象。
5. provider、adapter、tool backend 不能反向上升成产品第一语言。

## 8. 这篇文档与其他文档的关系

这篇文档负责：

- 冻结 `Garage Team` 作为一等产品对象的架构含义
- 冻结 workspace surfaces 与 team state 的关系
- 明确哪些对象属于产品第一语言，哪些对象只属于运行时第二语言

后续由不同文档继续展开：

- `A110`：继续冻结平台边界、扩展 seam 与成长 seam
- `A115`：继续解释产品入口与宿主能力注入的关系
- `A120`：继续解释 `Garage Team runtime` 的子系统图
- `A130`：继续解释 `memory / session / skill / evidence` 的长期分层

## 9. 一句话总结

`Garage` 之所以首先是一个 `Agent Teams` 工作环境，是因为用户真正拥有和长期培养的是自己的 `Garage Team`；而这个团队之所以能长期存在，是因为它被统一 runtime 和 workspace-first facts 一起锚定成了一个真实的长期系统。
