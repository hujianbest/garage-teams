# Garage

- 状态: 草稿
- 日期: 2026-04-11
- 定位: `Garage` 是一个服务个人创作者的 `Creator OS`，它不是单点 AI 工具，而是一群像在车库里创业一样协作的 AI 角色所组成的长期创作系统。
- 当前阶段: phase 1
- 关联文档:
  - `docs/README.md`
  - `docs/garage/garage-extensible-architecture.md`
  - `docs/garage/garage-core-subsystems-architecture.md`
  - `docs/garage/garage-phase1-core-runtime-records.md`
  - `docs/garage/garage-phase1-session-lifecycle-and-handoffs.md`
  - `docs/garage/garage-phase1-governance-model.md`
  - `docs/garage/garage-phase1-artifact-and-evidence-surface.md`
  - `docs/garage/garage-shared-contracts.md`
  - `docs/garage/garage-phase1-shared-contract-schemas.md`
  - `docs/garage/garage-continuity-memory-skill-architecture.md`
  - `docs/garage/garage-phase1-continuity-mapping-and-promotion.md`
  - `docs/garage/garage-phase1-reference-packs.md`
  - `docs/garage/garage-product-insights-pack-design.md`
  - `docs/garage/garage-coding-pack-design.md`
  - `docs/garage/garage-phase1-cross-pack-bridge.md`
  - `docs/tasks/README.md`
  - `docs/architecture/ahe-platform-first-multi-agent-architecture.md`
  - `docs/analysis/hermes-agent-harness-engineering-analysis.md`
  - `docs/analysis/clowder-ai-harness-engineering-analysis.md`

## 0. 阅读顺序

如果你想快速理解 `Garage`，建议按下面顺序阅读：

1. 先读本文，理解 `Garage` 的品牌语义、项目定位和愿景。
2. 再读 `docs/garage/garage-extensible-architecture.md`，理解 phase 1 的可扩展分层架构。
3. 再读 `docs/garage/garage-core-subsystems-architecture.md`，理解 `Garage Core` 的五个稳定子系统与主链交互。
4. 再读 `docs/garage/garage-phase1-core-runtime-records.md`，冻结 `Garage Core` 在 phase 1 的运行时对象、持久记录与写入语义。
5. 再读 `docs/garage/garage-phase1-session-lifecycle-and-handoffs.md`，冻结 `session` 的推进、暂停、交接、返工、收尾与归档准备语义。
6. 再读 `docs/garage/garage-phase1-governance-model.md`，冻结 `global / core / pack / node` 四层治理与 gate 语义。
7. 再读 `docs/garage/garage-phase1-artifact-and-evidence-surface.md`，冻结 phase 1 的文件表面、权威规则与归档语义。
8. 再读 `docs/garage/garage-shared-contracts.md`，理解 `Garage` 用什么共享 contract 承接 pack、role、node、artifact、evidence 与 host。
9. 再读 `docs/garage/garage-phase1-shared-contract-schemas.md`，冻结 6 类 contract 的最小 schema shape。
10. 再读 `docs/garage/garage-continuity-memory-skill-architecture.md`，理解 `memory`、`session`、`skill`、`evidence` 的持续性分层。
11. 再读 `docs/garage/garage-phase1-continuity-mapping-and-promotion.md`，冻结 phase 1 的 continuity 候选来源与 promotion 规则。
12. 再读 `docs/garage/garage-phase1-reference-packs.md`，理解为什么 phase 1 先用 `Coding Pack` 与 `Product Insights Pack` 验证平台中立性。
13. 再读 `docs/garage/garage-product-insights-pack-design.md` 与 `docs/garage/garage-coding-pack-design.md`，理解两个 reference packs 的详细设计。
14. 再读 `docs/garage/garage-phase1-cross-pack-bridge.md`，冻结 `product-insights -> coding` 的 bridge seam。
15. 再读 `docs/tasks/README.md`，按开发顺序进入 phase 1 的实现任务拆解。
16. 最后再进入 `ahe-coding-skills/README.md` 与 `ahe-product-skills/README.md`，判断现有 `coding` / `product insights` 资产如何逐步转译成 `Garage` 下的 reference packs。

## 1. 为什么叫 Garage

`Garage` 的品牌语义来自“在车库里创业”这件事本身。

它要表达的不是怀旧，也不是创业神话，而是下面这组产品判断：

- 重要的东西往往从一个小而聚焦的空间开始，而不是从庞大的组织结构开始
- 创作、试错、构建、修正和沉淀，应该发生在同一个连续环境里
- 人是方向的拥有者，AI 角色是一起工作的创业伙伴，而不是一组零散工具
- 系统要支持从 idea 到产出的完整演进，而不是只优化某一个局部环节

一句话说，`Garage` 想做的，是把“一个人在车库里带着一群 AI 伙伴把想法做出来”的工作方式，变成一个长期可复用的创作系统。

## 2. 项目定位

`Garage` 是一个面向 `solo creator` 的 `Creator OS`。

它的核心不是聊天，不是单个模型，也不是某个固定领域的自动化脚本，而是一个能把多个 AI 角色组织起来、持续为创作者生产结果的分层平台。

当前我们把它定义为：

- 一个 `Markdown-first`、`file-backed` 的创作操作系统
- 一个能够组织 `AI 创作团队` 协作的控制面
- 一个可扩展的平台骨架，未来能力通过新增 pack 挂载，而不是不断改写核心
- 一个先服务个人创作者，再考虑更复杂协作形态的系统

它首先要服务的用户，不是大团队，也不是纯技术用户，而是那些既要思考方向、又要把东西真正做出来的个人创作者与独立开发者。

## 3. 愿景

`Garage` 的长期愿景是：

**让个人创作者像拥有一间永不下线的创业车库一样，带着一支会持续积累方法、记忆和协作默契的 AI 团队，把洞察变成产品，把想法变成内容，把创作变成持续生产。**

这个愿景包含 4 层意思：

### 3.1 不只是回答问题，而是持续创造结果

`Garage` 不应该停留在“你问一句，我答一句”的工具形态。

它的目标是帮助用户持续推进真正的创作闭环，例如：

- 从模糊 idea 到问题重写与机会判断
- 从研究与产品洞察到概念收敛
- 从规格与设计到 coding 实现
- 从开发结果到表达、写作、发布与后续内容化

### 3.2 不只是一个 AI，而是一支 AI 创作团队

用户面对的不应是一个什么都想做的单体助手，而应该是一支在同一平台中协作的 AI 团队。

这支团队的特征是：

- 不同角色承担不同职责
- 角色之间可以交接、复查、补位和沉淀经验
- 人始终负责愿景、判断与关键取舍
- AI 负责执行、放大、复盘与持续积累

### 3.3 不只是当前能力，而是能持续扩展的能力面

`Garage` 的第一阶段虽然从 `coding` 和 `product insights` 起步，但它的设计不能被这两个能力锁死。

未来它应该可以自然承接：

- `writing`
- `video`
- `research`
- `course`
- 其他尚未定义但具有明确创作产出的能力 pack

扩展的方式应是：

- 新增 pack
- 注册新角色
- 映射新 artifact
- 复用稳定 core

而不是每次扩展都回头重写平台层。

### 3.4 不只是会做事，还要越用越顺手

`Garage` 需要具备长期连续性。

这意味着它必须逐步形成：

- `memory`：稳定事实与长期偏好
- `session`：任务过程、当前上下文与 handoff 状态
- `skill`：被沉淀下来的方法、套路和可复用工作流

这样它才不是一次性工具，而是一个越用越贴合用户工作方式的长期系统。

## 4. 我们要解决的问题

当前很多 AI 产品都有明显断层：

- 洞察、开发、写作、发布是割裂的
- 用户需要自己充当路由器，把不同工具和不同上下文手工串起来
- AI 的记忆、方法和角色分工不稳定
- 每加一种新能力，系统就要加很多特例逻辑

`Garage` 要解决的，不是“再做一个更聪明的聊天壳”，而是把创作者真正需要的长期协作结构先搭起来。

## 5. 核心设计原则

### 5.1 Human-directed, AI-team-executed

人负责：

- 方向
- 判断
- 审批
- 最终取舍

AI 团队负责：

- 研究
- 生成
- 编排
- 复查
- 沉淀

### 5.2 Platform first, packs second

先定义 `Garage` 的稳定核心和共享契约，再定义 `coding`、`product insights`、`writing`、`video` 等具体能力 pack。

平台是长期骨架，pack 是可增长能力面。

### 5.3 Open for extension, closed for modification

新增能力时，应该优先：

- 新增 pack
- 新增 role
- 新增 artifact mapping
- 新增 templates / prompts / rules

而不是修改核心去适配某个新领域。

### 5.4 Memory, session, skill must be separated

长期偏好、会话过程状态、可复用方法必须是三类不同资产；而 `evidence` 应作为独立的可追溯记录层存在。

只有分层，`Garage` 才能真正形成长期连续性，而不是把一切都堆进聊天上下文。

### 5.5 Governance as artifacts

愿景、术语、规则、评审、门禁和归档都应该先写成工件，再让系统和 pack 去读取这些工件。

`Garage` 不应该把核心约束藏在聊天历史里。

### 5.6 Markdown-first in phase 1

第一阶段坚持：

- 以 Markdown 为主工件
- 以文件化结构为主事实源
- 以轻量 metadata / sidecar 支撑索引和状态

在没有必要之前，不把系统过早做成重型服务平台。

## 6. 能力边界

phase 1 正式承接的能力 pack：

- `coding`
- `product insights`

phase 1 预留但暂不完整展开的能力 pack：

- `writing`
- `video`

这意味着当前 `Garage` 的重点，不是把所有创作能力一次性做满，而是先证明平台骨架能够稳定承接多种内容能力。

## 7. 非目标

当前阶段，`Garage` 明确不追求：

- 先做成完整多用户协作 SaaS
- 先做成重型数据库控制面
- 先覆盖所有内容创作媒介
- 先把角色体系写死为固定组织架构
- 先为每一种能力做深度实现

phase 1 的成功标准不是“功能很多”，而是：

- 品牌和定位清晰
- 顶层架构稳定
- 核心契约可扩展
- `coding` 与 `product insights` 能作为 reference packs 证明架构成立

## 8. Garage 与当前仓库的关系

这个仓库的过去，是一个以 `harness engineering` 为中心的工作台。

`Garage` 的定义意味着：

- 这个仓库不再只描述“怎么组织 agent workflow”
- 它开始转向“如何为个人创作者组织一个长期 AI 创作系统”
- 现有 `coding` 与 `product insights` 资产，不再只是两个并列工具集，而是未来 `Garage` 上的两个 reference packs

换句话说，`Garage` 不是在旧仓库上贴一个新名字，而是在重新定义这个项目的产品本体。

## 9. 一句话总结

`Garage` 是一个面向个人创作者的 `Creator OS`：人在其中定义方向，一群像在车库里创业一样协作的 AI 角色负责研究、构建、表达与沉淀，平台则用稳定核心和可扩展 pack 结构，把这种工作方式变成一个长期可演进的系统。
