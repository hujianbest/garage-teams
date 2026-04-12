# M030: Garage

- Document ID: `M030`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 这份文档负责定义 `Garage` 当前到底是什么产品、用户进入的是什么环境、`Garage Team` 是什么、有哪些入口、能力、边界与主线阅读入口。
- 当前阶段: 主线已切换到完整架构；实施将按需拆成多个 delivery slices 推进
- 关联文档:
  - `docs/README.md`
  - `docs/VISION.md`
  - `docs/ROADMAP.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/architecture/A140-garage-system-architecture.md`
  - `docs/features/F210-runtime-home-and-workspace-topology.md`
  - `docs/features/F220-runtime-bootstrap-and-entrypoints.md`
  - `docs/features/F230-runtime-provider-and-tool-execution.md`
  - `docs/tasks/README.md`
  - `packs/README.md`

## 0. 阅读顺序

如果你想快速理解 `Garage`，建议按下面顺序阅读：

1. 先读 `docs/README.md`，理解当前 `docs` 的信息架构与真相源分工。
2. 再读 `docs/VISION.md`，理解 `Garage` 为什么存在，以及它想改变怎样的创作工作方式。
3. 再读本文，理解 `Garage` 当前到底是什么产品、有哪些入口、能力和边界。
4. 再读 `docs/ROADMAP.md`，理解能力切面与 feature map。
5. 再读 `docs/architecture/`、`docs/features/`、`docs/design/`，理解系统如何支撑这个产品定义。
6. 最后再读 `docs/tasks/README.md`，理解完整架构如何被拆成实施切片。

## 1. `Garage` 当前是什么产品

`Garage` 当前首先应被理解为：

**一个辅助创作者的 `Agent Teams` 工作环境，也是一个可持续成长的 `Garage Team runtime`。**

它不是：

- 单点 AI 工具
- 只会执行静态 workflow 的控制壳
- 只能通过手工集成才真正可用的底层框架

它更接近的是：

- 一个让创作者直接进入并使用的工作环境
- 一个组织多种 agents 协作、交接、复查和沉淀的方法层
- 一个让团队能力随着经验持续扩展和成长的长期系统

## 2. `Garage Team` 的正式定义

`Garage Team` 是 `Garage` 里的第一产品对象。

对用户来说：

- `Garage Team` 是用户在 `Garage` 中拥有并培养的一支 AI 团队
- 用户进入 `Garage`，本质上就是进入自己的 `Garage Team` 工作环境

对系统来说：

- `Garage Team` 是运行在统一 runtime 之上的一组 agents、roles、handoffs、skills、memory 和 governance 关系
- 它可以持续扩展新能力，也可以在治理约束下持续成长

这意味着 `Garage` 的最小产品单位不是：

- model list
- tool list
- provider toggles

而是：

- team
- agent
- role
- handoff
- review
- memory
- skill

## 3. 目标用户与典型使用方式

`Garage` 首先服务的是：

- `solo creator`
- 独立开发者
- 既要思考方向、又要真正做出结果的人

典型使用方式不是“问一次问题拿一个答案”，而是：

- 在同一个环境里长期推进一个或多个创作主线
- 让不同类型的 agents 分工合作
- 把一次性经验逐步沉淀成长期可复用的团队能力

这类工作可能包括：

- 写代码
- 写文章
- 设计产品
- 做音乐
- 做视频
- 其他尚未定义、但能产生明确创作结果的能力面

## 4. 入口策略：CLI / Web / HostBridge

`Garage` 当前采用三类一等入口 family：

- `CLIEntry`
- `WebEntry`
- `HostBridgeEntry`

它们的产品关系不是“谁都一样重要”，而是：

1. `Garage` 首先是一个独立工作环境，用户可以直接通过 `CLI` 或 `Web` 进入
2. 如果用户已经有正在使用的工具，如 `Claude`、`OpenCode`、`Cursor`，`Garage` 也可以把底层的 agents、skills 和长期能力注入这些宿主环境

这里最关键的判断是：

- 宿主集成是能力注入层，不是 `Garage` 的唯一存在方式
- 不同入口可以有不同 UX，但不能拥有不同的 runtime 真相

## 5. 当前能力面与自然扩展方向

`Garage` 当前已经明确承接的能力面包括：

- `coding`
- `product insights`

未来自然要承接的能力面包括：

- `writing`
- `music`
- `video`
- `research`
- 其他尚未定义但具有明确创作产出的 agent / pack family

这里的关键判断不是“今天有没有把所有能力都做完”，而是：

- `Garage Team` 是否已经具备持续吸收新 agent 类型的结构条件
- 新能力面是否能复用已有的 memory、skills、governance 和 workspace facts
- 新能力面是否能在不推翻核心边界的前提下进入系统

## 6. 产品边界与非目标

`Garage` 当前明确不追求：

- 把系统做成一个无限自治、无限递归的 agent society
- 把所有知识沉淀都做成无解释的黑箱自动学习
- 把平台先做成数据库优先、组织优先的重型控制面
- 把 Garage 的主要价值变成“让开发者自己写代码集成”
- 为了“看起来功能很多”牺牲长期边界、治理和可维护性

`Garage` 也不应被误解为：

- 一个已经完全打磨完成的终端产品
- 一个只有 CLI 的开发者工具
- 一个只是聊天壳外面挂了些 plugins 的集成层

## 7. 与当前仓库、runtime、packs、skills 的关系

这个仓库当前同时承担：

- `Garage` 的 source root
- 当前默认的 dogfooding workspace

从产品定义视角看，这意味着：

- `src/` 承接 runtime 的当前实现面
- `docs/` 承接产品愿景、产品定义、系统架构和实施切片的真相源
- `packs/` 承接当前 reference packs 与能力面
- `.agents/skills/` 承接本地 skill 资产和文档维护辅助面
- `artifacts/`、`evidence/`、`sessions/`、`archives/`、`.garage/` 承接 workspace-first facts

这里最重要的规则是：

- `Garage` 可以通过不同入口进入
- 但它始终应共享同一个 runtime 主链
- 它可以把能力注入现有宿主
- 但宿主不应拥有 `Garage` 的核心真相

## 8. 主线阅读入口

如果你想理解 `Garage` 的顶层主线，建议按下面顺序阅读：

1. `docs/README.md`
2. `docs/VISION.md`
3. `docs/GARAGE.md`
4. `docs/ROADMAP.md`
5. `docs/architecture/`
6. `docs/features/`
7. `docs/design/`
8. `docs/tasks/README.md`

按主题跳读时：

- 想理解为什么要做 `Garage`：读 `docs/VISION.md`
- 想理解 `Garage` 当前是什么产品：读本文
- 想理解系统如何支撑这个产品定义：读 `docs/architecture/` 与 `docs/features/`
- 想理解当前怎么逐步把它做出来：读 `docs/tasks/README.md`

## 9. 一句话总结

`Garage` 当前应被定义为一个辅助创作者的 `Agent Teams` 工作环境：用户进入的是自己的 `Garage Team`，可以通过 CLI 或 Web 直接工作，也可以把底层能力注入现有工具；系统本身则通过统一 runtime、可扩展 agents、显式治理和可持续成长机制，让这支团队随着经验不断扩展和成熟。
