# M030: Garage

- Document ID: `M030`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: `Garage` 是一个服务个人创作者的 `Creator OS`：它不是单点 AI 工具，也不是只会执行静态 workflow 的控制壳，而是一群像在车库里创业一样协作、扩展并主动成长的 AI 角色所组成的长期系统。
- 当前阶段: 主线已切换到完整架构；实施将按需拆成多个 delivery slices 推进
- 关联文档:
  - `docs/README.md`
  - `docs/VISION.md`
  - `docs/ROADMAP.md`
  - `docs/architecture/A110-garage-extensible-architecture.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/architecture/A130-garage-continuity-memory-skill-architecture.md`
  - `docs/architecture/A140-garage-system-architecture.md`
  - `docs/features/F010-shared-contracts.md`
  - `docs/features/F020-shared-contract-schemas.md`
  - `docs/features/F030-core-runtime-records.md`
  - `docs/features/F040-session-lifecycle-and-handoffs.md`
  - `docs/features/F050-governance-model.md`
  - `docs/features/F060-artifact-and-evidence-surface.md`
  - `docs/features/F070-continuity-mapping-and-promotion.md`
  - `docs/features/F080-garage-self-evolving-learning-loop.md`
  - `docs/features/F110-reference-packs.md`
  - `docs/features/F120-cross-pack-bridge.md`
  - `docs/features/F210-runtime-home-and-workspace-topology.md`
  - `docs/features/F220-runtime-bootstrap-and-entrypoints.md`
  - `docs/features/F230-runtime-provider-and-tool-execution.md`
  - `docs/design/D110-garage-product-insights-pack-design.md`
  - `docs/design/D120-garage-coding-pack-design.md`
  - `docs/tasks/README.md`
  - `packs/README.md`
  - `docs/wiki/W140-ahe-platform-first-multi-agent-architecture.md`
  - `docs/wiki/W030-hermes-agent-harness-engineering-analysis.md`
  - `docs/wiki/W040-hermes-agent-core-design-ideas.md`
  - `docs/wiki/W010-clowder-ai-harness-engineering-analysis.md`

## 0. 阅读顺序

如果你想快速理解 `Garage`，建议按下面顺序阅读：

1. 先读 `docs/README.md`，理解当前 `docs` 的信息架构与真相源分工。
2. 再读 `docs/VISION.md`，理解 `Garage` 为什么存在，以及它想建立怎样的创作工作方式。
3. 再读本文，理解 `Garage` 的品牌语义、系统定义和主线阅读顺序。
4. 再读 `docs/ROADMAP.md`，理解 `docs/features/` 的稳定 feature IDs、能力分组与路线索引。
5. 再读 `docs/architecture/A110-garage-extensible-architecture.md`，理解顶层分层骨架与扩展性主线。
6. 再读 `docs/architecture/A120-garage-core-subsystems-architecture.md`，理解完整 runtime 的核心子系统。
7. 再读 `docs/architecture/A130-garage-continuity-memory-skill-architecture.md`，理解 `memory / session / skill / evidence` 如何分层。
8. 再读 `docs/architecture/A140-garage-system-architecture.md`，理解端到端系统设计与关键架构决策。
9. 再读 `docs/features/`，理解 contracts、governance、artifact surface、continuity、learning loop、runtime topology 与 execution 语义。
10. 再读 `docs/design/`，理解 `Product Insights Pack` 与 `Coding Pack` 等 pack 设计如何挂到完整架构上。
11. 最后再读 `docs/tasks/README.md`，理解完整架构会如何被拆成实施切片。

## 1. 为什么叫 Garage

`Garage` 的品牌语义来自“在车库里创业”这件事本身。

它要表达的不是怀旧，也不是创业神话，而是下面这组产品判断：

- 重要的系统往往从一个小而聚焦的团队开始，而不是从庞大组织开始。
- 起步阶段能力少、做的事情少，是正常状态，但不应该被当成长期上限。
- 真正好的车库团队，不只是会做事，还会在做事过程中积累经验、形成方法、升级自身能力。
- 如果一个系统只能执行当前任务，却不会因为做过的事情而变强，它就不是“团队”，而只是工具集合。

一句话说，`Garage` 想做的，是把“一个人在车库里带着一群 AI 伙伴把想法做出来”的工作方式，变成一个能随着经验持续扩展、持续成长的长期系统。

## 2. 项目定位

`Garage` 是一个面向 `solo creator` 的 `Creator OS`。

它的核心不是聊天，不是单个模型，也不是某个固定领域的自动化脚本，而是一个能把多个 AI 角色组织起来、持续为创作者生产结果，并且会在治理约束下主动成长的分层 runtime。

当前我们把它定义为：

- 一个 `local-first`、`multi-entry`、`workspace-first` 的 agent runtime
- 一个能够组织 `AI 创作团队` 协作的控制面
- 一个可扩展的平台骨架，未来能力通过新增 pack、role 和 runtime capability 接入
- 一个会从经验中形成 evidence、提出长期资产候选、并推动团队自我改进的系统
- 一个先服务个人创作者，再考虑更复杂协作形态的系统

它首先要服务的用户，不是大团队，也不是纯技术用户，而是那些既要思考方向、又要把东西真正做出来的个人创作者与独立开发者。

## 3. Garage 到底是什么系统

如果压缩成一句话，`Garage` 是：

**一个以 workspace 为主事实面、以 session 为主线、以 pack 为能力面、以 governance 为边界、以 evidence 为追溯面、以 `memory / skill` 为长期成长资产的 self-evolving agent runtime。**

这里最重要的不是“模型有多强”，而是下面这些系统判断：

- 用户面对的是团队，而不是单体助手
- 不同入口共享同一套 runtime 语义，而不是各有各的 workflow
- 新能力主要通过扩展进入系统，而不是修改核心
- 团队不仅执行任务，还会从经验中主动提出成长建议
- 主动成长受到治理、审批、review 和 evidence 约束，而不是黑箱式自动漂移

## 4. 两条同等重要的主线

`Garage` 的主线不是单一的“做一个更强的 agent”。

它至少有两条同等重要的主线。

### 4.1 可扩展性

`Garage` 不能被当前能力集合锁死。

它必须允许下面这些变化持续发生：

- 新增 pack
- 新增 role
- 新增 node
- 新增 artifact mapping
- 新增 runtime capability
- 新增入口与宿主适配

理想状态下，这些扩展主要通过注册、映射与边界装配进入系统，而不是回头修改 `Garage Core`。

### 4.2 可成长性

`Garage` 也不能永远停留在“第一天刚启动时的团队水平”。

它必须允许下面这些成长持续发生：

- 从工作结果中形成 `evidence`
- 从 `evidence` 中主动识别 `memory` 与 `skill` 候选
- 在治理约束下持久化长期知识
- 从经验中 patch 旧 skill、改进协作纪律、调整运行策略
- 让未来的 session、role 和 pack 因过去经验而变得更有效率

如果只有扩展性，没有成长性，`Garage` 会变成一个越来越大的静态平台；如果只有成长性，没有扩展性，`Garage` 会变成一个越来越会记东西、但能力边界越来越乱的黑箱。

`Garage` 要同时守住这两条主线。

## 5. 系统形态

从系统形态看，`Garage` 应被理解成：

- 一个长期存在的团队运行时，而不是一次性请求处理器
- 一个高于入口的统一核心，而不是多套入口逻辑的松散集合
- 一个以 `workspace` 为主事实面、以 `runtime home` 承载运行配置的分层系统
- 一个通过 `contracts + packs` 承接能力、通过 `evidence + governance` 承接成长的运行时

这意味着：

- `CLI`、`IDE`、聊天入口、轻 UI 都不应拥有各自私有的运行语义
- pack 不应直接绑定 provider 协议或宿主特性
- 记忆、技能、证据和当前 session 不能混成一个历史桶
- 主动成长必须能回指其来源和治理过程

## 6. Garage 与当前仓库的关系

这个仓库的过去，是一个以 `harness engineering` 为中心的工作台。

`Garage` 的定义意味着：

- 这个仓库不再只描述“怎么组织 agent workflow”
- 它开始转向“如何为个人创作者组织一个长期 AI 创作系统”
- 现有 `coding` 与 `product insights` 资产，不再只是两个并列工具集，而是未来 `Garage` 上的两个 reference packs
- 当前仓库既是 `Garage` 的 source root，也是当前默认的 dogfooding workspace

换句话说，`Garage` 不是在旧仓库上贴一个新名字，而是在重新定义这个项目的产品本体。

## 7. 当前能力面与未来能力面

`Garage` 当前已经明确的能力面包括：

- `coding`
- `product insights`

未来自然应当承接的能力面包括：

- `writing`
- `video`
- `research`
- `course`
- 其他尚未定义但具有明确创作产出的 pack

这里的关键判断不是“什么时候把所有能力都做出来”，而是：

- 系统是否已经具备承接更多能力面的结构条件
- 团队是否能够随着能力面扩张而保持边界清晰
- 新能力面是否能继承已有的成长资产，而不是重新从零开始

## 8. 非目标

当前 `Garage` 明确不追求：

- 把系统做成一个无限自治、无限递归的 agent society
- 把所有知识沉淀都做成无解释的黑箱自动学习
- 把平台先做成数据库优先、组织优先的重型控制面
- 把角色体系写死成固定组织架构
- 为了“看起来功能很多”牺牲长期边界、治理和可维护性

`Garage` 要做的，不是“所有东西都自动”，而是：

**在清晰边界、可解释 evidence 和显式治理之上，允许团队主动成长。**

## 9. 如何理解接下来的文档树

从文档树视角看：

- `docs/VISION.md` 解释为什么要做 `Garage`
- `docs/GARAGE.md` 解释 `Garage` 是什么、应该从哪里读起
- `docs/architecture/` 解释顶层平台边界、完整 runtime 与长期 continuity
- `docs/features/` 解释稳定 capability cuts 与共享语义
- `docs/design/` 解释 pack-specific 详细设计
- `docs/tasks/` 解释完整架构如何按实施切片逐步落地

这里最重要的规则是：

- 主线真相先在 `architecture / features / design`
- 实施切片再在 `tasks`

而不是反过来让阶段性任务文档定义系统本体。

## 10. 一句话总结

`Garage` 是一个面向个人创作者的 `Creator OS`：人在其中定义方向，一群像在车库里创业一样协作的 AI 角色负责研究、构建、表达、沉淀与主动成长，平台则用稳定核心、可扩展 pack 结构、显式治理和 workspace-first 的长期资产面，把这种工作方式变成一个完整且可持续演化的系统。
