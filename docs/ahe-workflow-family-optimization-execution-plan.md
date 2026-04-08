# AHE workflow family 分阶段优化执行计划

## Router-era 说明

下文大量条款成稿于 **pre-split legacy 合并入口/router 时代**（历史旧 skill 目录已移除）。当前 canonical runtime 为 **`ahe-workflow-router`**，家族公开入口为 **`using-ahe-workflow`**。阅读时请将文中的 “legacy 合并 skill” **默认映射为今日的 router + 公开入口分层**，除非小节明确在回顾历史批次。

## 背景

本文把 `docs/agent-skills-main-vs-ahe-workflow-report.md` 中的 `P0`、`P1`、`P2` 优先级建议，转换为一份可执行的分阶段优化路线图。

计划目标不是把 AHE 改造成另一套通用 skill 产品包，而是在保留 AHE 现有强项的前提下，系统性降低维护摩擦、收敛家族契约，并为未来可能的对外复用预留空间。

本轮计划额外引入一个明确目标：让 `ahe-*` skill 粒度兼容“独立调用 + 串联调用”两种模式。

- `独立调用`：用户可直接点名某个 `ahe-*` skill，skill 依据自身前置条件与证据要求执行本节点职责；若前置条件不满足或当前阶段不清，则显式回退到 `ahe-workflow-router`（可先经 `using-ahe-workflow` 再交给 router）。
- `串联调用`：skill 作为 workflow 节点被 `ahe-workflow-router`（或上游节点）串联进入，并在完成后写回 canonical handoff，供主链继续编排。

当前判断保持不变：

- AHE 的核心优势是状态机式路由、profile-aware 主链、显式工件契约、review/gate 闭环和 fresh evidence 约束。
- 最值得借鉴 `agent-skills-main` 的地方，是统一 anatomy、统一入口、统一配套资产和低摩擦加载方式。
- 最不应该牺牲的，是 `ahe-workflow-router` 的编排权威、pause points、profile 约束和 evidence-first 模型。
- 双模式调用不等于弱化 workflow kernel，而是要求每个节点同时具备 `standalone contract` 与 `chain contract`：前者负责自检与必要回退，后者负责交接与串联恢复。

## 当前执行状态

| 条目 | 状态 | 说明 |
| --- | --- | --- |
| 家族级执行计划 | 已完成 | 当前文档即执行计划 |
| 家族级 anatomy 文档 | 已完成 | `docs/ahe-workflow-skill-anatomy.md` 已创建 |
| 双模式目标定义 | 已完成 | 计划与 anatomy 都已明确 `独立调用 + 串联调用` |
| AHE vs `agent-skills-main` 对比刷新 | 已完成 | `docs/agent-skills-main-vs-ahe-workflow-report.md` 已按最新 skills 状态刷新 |
| router / 契约附属文档关键对齐 | 进行中 | 已同步 lightweight 链路、progress example 与 reviewer handoff 核心表达；剩余全量 reviewer rollout 进入后续 sweep |
| shared `task-progress` template 更新 | 已完成 | `templates/task-progress-template.md` 已切换到 canonical core 字段 |
| 当前最高优先级 | 进行中 | live skills 对新 contract / schema 的 adopt，以及 core skills contract adoption |

## 输入与边界

### 主要输入

- `docs/agent-skills-main-vs-ahe-workflow-report.md`
- `skills/README.md`
- `skills/design_rules.md`
- `skills/ahe-workflow-router/SKILL.md`
- `skills/ahe-specify/SKILL.md`
- `skills/ahe-design/SKILL.md`
- `skills/ahe-tasks/SKILL.md`
- `skills/ahe-test-driven-dev/SKILL.md`
- `skills/ahe-regression-gate/SKILL.md`
- `skills/ahe-completion-gate/SKILL.md`
- `skills/ahe-finalize/SKILL.md`
- `templates/task-progress-template.md`

### 当前已知结构性问题

- 家族级公共约定分散在多个 `ahe-*` skill 中重复表达。
- （历史）legacy 合并入口曾把家族级说明压在单一 skill 上，导致认知负担偏高；现状应靠 `using-ahe-workflow` / docs 减负，保持 `ahe-workflow-router` 偏 kernel。
- 各 skill 的固定骨架相似但尚未完全标准化，长期维护容易继续漂移。
- 当前家族虽然已经出现 direct invoke 雏形，但节点 skill 的独立调用契约、前置条件自检和 fallback 行为还没有被统一定义。
- live skills 与周边文档对 canonical progress schema、reviewer handoff contract 的 adopt 还没有完全完成。
- review subagent 协议已出现，但 live skills 对它的写法与 anatomy 的 section contract 还没有完全统一。

### 非目标

- 不把 AHE 重写成通用工程 skill 大全。
- 不削弱 `ahe-workflow-router` 的路由 authority。
- 不为了“像产品”而提前引入过量 packaging、hooks、commands、agents。
- 不把 docs-first 仓库改造成脚本优先或工具链优先仓库。
- 不在单轮里同步大改全部 `ahe-*` skills。
- 不把“支持独立调用”理解为可以绕过前置条件、review/gate 或 evidence-first 约束。

## 执行原则

### 1. 保留 workflow kernel

`ahe-workflow-router` 仍然是 runtime 编排中枢，也是“阶段不清、证据冲突、需要恢复主链时”的权威入口（新会话常先经 `using-ahe-workflow`）。优化的目标是瘦身与抽离解释层，不是下放或削弱路由权。

### 2. 兼容双模式调用

每个 `ahe-*` skill 都应逐步具备两套清晰契约：

- `standalone contract`：什么情况下可以被直接调用、最少需要什么输入、何时必须回退到 router
- `chain contract`：作为主链节点被串联调用时，如何消费上游证据、如何写回 handoff 与下一步

### 3. 先收敛契约，再批量改文件

所有跨 skill 的结构调整，先固化为家族级文档契约，再开始逐个 skill 对齐。避免边改边发明新规则。

### 4. 优先修复 live mismatch

先解决当前已经造成真实使用摩擦的矛盾，例如 `task-progress` 字段不一致，而不是先做更漂亮的包装层。

### 5. 保持 Markdown-first

优先用文档、模板和 references 收敛行为。只有在重复收益明确时，才增加 wrapper、persona、hook 或 setup 资产。

### 6. 适配单人维护现实

每个阶段都应拆成小批次执行，优先做“少量文件、闭环明确、回滚容易”的结构收敛。

### 7. 证据优先

阶段推进以“已有文档/模板/skill 是否对齐”为准，而不是以“看起来方向正确”为准。

## 阶段总览

| 阶段 | 核心目标 | 主要结果 | 变更性质 |
| --- | --- | --- | --- |
| `P0` 结构收敛 | 在已建立 anatomy 基础上关闭现存矛盾、统一双模式 contract、降低 router 主文件负担 | collateral 对齐、canonical progress schema 落地、router kernel 瘦身（历史批次曾称 pre-split 合并 router 二次瘦身）、核心 skill contract adoption | 文档优先 + 小范围 skill/template 重构 |
| `P1` 降摩擦与共享约定 | 降低维护重复，并让 direct invoke 与 chain invoke 的入口都更低摩擦 | shared conventions、entrypoint 文档、可选 meta-skill / persona / command 约定 | 先文档，后按需小幅扩展 |
| `P2` 对外化准备 | 在真实需求出现后，为跨仓库采用建立映射、包装边界与双模式接入说明 | externalization guide、core vs extensions、可选 setup/hook 示例 | 条件触发，非当前刚需 |

## `P0`：结构收敛

### 目标

在已建立家族级 anatomy 的基础上，优先消除当前最明显的结构性不一致，并让 `ahe-workflow-router` 更接近“路由内核”，而不是“路由 + 全家说明书”的混合体（解释层优先落在 `using-ahe-workflow` 与 docs）。同时把核心节点对“独立调用 + 串联调用”的支持真正落到 live skills。

### 范围

- 家族级 anatomy
- canonical `task-progress` schema
- 独立调用与串联调用 contract
- router 主文件与 `references/` 的边界重划
- 主链核心 skills 的固定骨架对齐
- review / branch skills 的第二轮对齐

### 工作流分解

### `P0-1` 冻结家族 anatomy 与 vocabulary

目标：

- 用一份家族级 anatomy 文档固定 vocabulary 与结构基线，作为后续所有 `ahe-*` skill 的统一参考。

当前状态：

- `docs/ahe-workflow-skill-anatomy.md`

状态判断：

- 已完成第一版，可作为后续技能对齐的基线文档。

至少定义：

- frontmatter 的最小要求
- 家族级推荐固定章节
- canonical handoff 字段
- review / gate verdict 枚举
- `task-progress` 关键字段定义
- `standalone contract` 与 `chain contract` 的最小定义
- direct invoke 失败时回退 `ahe-workflow-router` 的规则
- 什么内容应保留在 `SKILL.md`
- 什么内容应下沉到 `references/`
- 什么情况只写文档，不新增工具层

依赖关系：

- 无前置依赖，应作为整个计划的第一批输出。

### `P0-2` 对齐 router collateral 与主文件（历史批次名：pre-split 合并 router collateral）

目标：

- 先消除 router 主文件与其 collateral 文档之间的显式矛盾，避免后续对齐工作建立在冲突说明之上。

建议涉及文件：

- `skills/ahe-workflow-router/SKILL.md`
- `skills/ahe-workflow-router/references/profile-selection-guide.md`
- `skills/ahe-workflow-router/references/routing-evidence-guide.md`
- `skills/ahe-workflow-router/references/routing-evidence-examples.md`
- `skills/ahe-workflow-router/references/review-dispatch-protocol.md`
- `skills/ahe-workflow-router/references/reviewer-return-contract.md`

改动重点：

- 统一 `lightweight` 的合法链路说明
- 统一 canonical handoff 字段表达
- 明确哪些内容属于 router authority，哪些属于 reviewer protocol 解释层
- 清理过时示例，避免继续传播旧字段心智

依赖关系：

- 依赖 `P0-1` 先把 vocabulary 冻结。

### `P0-3` 更新共享模板并关闭 progress schema live mismatch

目标：

- 让仓库里的默认 `task-progress` 模板与家族 contract 真正对齐。

建议涉及文件：

- `templates/task-progress-template.md`

改动重点：

- 用 canonical 字段替换或显式映射当前 generic 字段
- 在模板开头说明该模板与 `ahe-*` workflow 的关系
- 避免继续传播 generic progress 别名，统一收口到 canonical progress schema

前置条件：

- `docs/ahe-workflow-skill-anatomy.md` 中的 canonical schema 已冻结。

依赖关系：

- 建议在 `P0-2` 之后执行，避免 collateral 仍在传播旧字段时反复改名。

### `P0-4` 统一核心主链 skills 的 dual-mode contract

目标：

- 让核心主链节点真正 adopt anatomy 中定义的 `standalone contract` / `chain contract`，把当前“部分存在、部分隐含”的双模式能力显式化。

第一批建议覆盖：

- `skills/ahe-specify/SKILL.md`
- `skills/ahe-design/SKILL.md`
- `skills/ahe-tasks/SKILL.md`
- `skills/ahe-test-driven-dev/SKILL.md`
- `skills/ahe-regression-gate/SKILL.md`
- `skills/ahe-completion-gate/SKILL.md`
- `skills/ahe-finalize/SKILL.md`

统一重点：

- direct invoke 适用条件
- direct invoke 最少输入
- direct invoke 回退 router 的规则
- chain invoke 默认读取哪些上游工件 / handoff
- chain invoke 完成后如何写回 canonical next action
- 本节点 authority 与 router authority 的边界

依赖关系：

- 依赖 `P0-1` 的 anatomy
- 依赖 `P0-3` 的 canonical schema，避免 contract 与模板再次分离

### `P0-5` review 与 branch skills 第二轮统一

目标：

- 在核心主链稳定后，对 review / branch 节点做第二轮结构补齐，避免一次性大改全家族。

第二批建议覆盖：

- `skills/ahe-spec-review/SKILL.md`
- `skills/ahe-design-review/SKILL.md`
- `skills/ahe-tasks-review/SKILL.md`
- `skills/ahe-test-review/SKILL.md`
- `skills/ahe-code-review/SKILL.md`
- `skills/ahe-traceability-review/SKILL.md`
- `skills/ahe-bug-patterns/SKILL.md`
- `skills/ahe-hotfix/SKILL.md`
- `skills/ahe-increment/SKILL.md`

重点不是把所有 skill 写成同一个样子，而是统一 verdict、handoff、record-path、evidence、边界说明，以及独立调用 / 串联调用的表达方式。

### `P0-6` 对 router kernel 做第二轮瘦身（历史：对 pre-split 合并 router 的第二轮瘦身）

目标：

- 在 collateral 已对齐、core contracts 已明确之后，再做 router 主文件的第二轮瘦身，避免过早抽离导致 authority 和示例一起丢失。

建议涉及文件：

- `skills/ahe-workflow-router/SKILL.md`
- `skills/ahe-workflow-router/references/*.md`

优先下沉到 `references/` 的内容：

- 长示例
- 详细信号矩阵
- 解释性边界案例
- 较长的 evidence 示例
- 对 review-subagent 协议的扩展说明

### `P0` 建议执行顺序

1. 已完成：写 `docs/ahe-workflow-skill-anatomy.md`
2. 已完成：修正 router collateral 与 router 主文件之间的关键冲突（历史表述：pre-split 合并 router collateral）
3. 已完成：在 anatomy 里冻结并落实 canonical `task-progress` schema
4. 已完成：更新 `templates/task-progress-template.md`
5. 统一核心主链 skills 的 dual-mode contract
6. 最后扫 review / branch skills
7. 对 router kernel 做第二轮瘦身

### `P0` 风险与控制点

| 风险 | 说明 | 控制方式 |
| --- | --- | --- |
| 过度规范化 | anatomy 写得过细，反而增加维护负担 | 只定义家族 contract，不写过度教科书式说明 |
| collateral 与主文件继续冲突 | 文档层自己互相打架，会放大后续对齐成本 | 先修 router collateral，再做大规模 skill adoption |
| router 被瘦身过度 | 把 authority 一起下沉，导致路由弱化 | 主文件只减解释层，不减路由核心规则 |
| 一次动太多文件 | vocabulary 和 structure 同时变动，容易失控 | 严格按两批 sweep 执行 |
| 模板与 skills 再次漂移 | 只改 skill，不改模板 | 先做 schema，再做模板，再改 skill |

### `P0` 完成标志

- 已存在一份可引用的家族 anatomy 文档。
- router 主文件与 collateral 文档不再互相冲突。
- `templates/task-progress-template.md` 与 canonical schema 已对齐。
- `ahe-workflow-router` 更像 routing kernel，长解释已下沉到 `references/`（家族说明由 `using-ahe-workflow` / docs 承担）。
- 核心主链 skills 已共享一致的固定骨架与 vocabulary。
- 核心主链 skills 已明确独立调用前置条件、fallback 到 router 的规则，以及串联调用时的 handoff contract。
- 当前报告中指出的最高优先级结构矛盾已经关闭。

## `P1`：降摩擦与共享约定

### 目标

在 `P0` 结构收敛完成后，减少跨 skill 的重复维护，补足低摩擦入口和共享说明层，并让 direct invoke 与 chain invoke 两种模式都更容易被正确使用，但仍然坚持“先文档、后资产、按需扩展”的策略。

### 范围

- shared conventions
- 家族入口与调用说明
- 双模式调用的用户心智模型
- reviewer / gate persona 的文档化定义
- 薄命令层的约定文档

### 工作流分解

### `P1-1` 抽离 shared conventions

目标：

- 把现在分散在多个 skill 中重复出现的公共约定，集中到一份维护文档。

建议产物：

- `docs/ahe-workflow-shared-conventions.md`

建议收口内容：

- fresh evidence 约束
- severity / verdict vocabulary
- canonical next action 规则
- record-path 约定
- review / gate 回流边界
- parent session 与下游 reviewer 的职责分界

### `P1-2` 建立家族级低摩擦入口说明

目标：

- 降低“什么时候先走 `using-ahe-workflow` / `ahe-workflow-router`，什么时候能直接点名节点”的理解成本，并明确 direct invoke 与 chain invoke 各自适合的入口。

建议产物：

- `docs/ahe-workflow-entrypoints.md`

内容建议：

- 什么时候必须先用 `using-ahe-workflow` 或 `ahe-workflow-router`
- 什么时候用户显式点名某个 skill 仍应先回 router
- 什么时候节点 skill 可以独立调用并直接完成本节点职责
- direct invoke 与 chain invoke 在输入、输出、handoff 上有何差异
- 常见失败模式
- family guarantees 的统一说明

### `P1-3` 文档先行地定义 persona matrix

目标：

- 先判断 persona 资产是否真的有复用价值，而不是直接新增一组 `agents/*.md`。

建议先做：

- `docs/ahe-review-persona-matrix.md`

优先评估的角色：

- test review
- code review
- traceability review
- regression / completion gate

只有当这些角色在多个优化回合里确实反复被引用时，再考虑新增真实 persona 文件。

### `P1-4` 形成命令入口约定

目标：

- 为高频路径提供更低摩擦的入口说明，但仍把它们当作薄封装，而不是基础设施，并明确哪些命令偏向 direct invoke，哪些偏向 chain invoke。

建议先做：

- `docs/ahe-command-entrypoints.md`

可先定义的入口：

- `/ahe-spec`
- `/ahe-build`
- `/ahe-review`
- `/ahe-closeout`

此阶段不强制新增真实命令文件；先验证命名、边界和使用收益。

### `P1` 风险与控制点

| 风险 | 说明 | 控制方式 |
| --- | --- | --- |
| 与 router 重叠 | 新入口文档或 meta-skill 变成第二个 kernel | 所有新入口都只解释“如何进入”，不替代 `ahe-workflow-router` |
| 新增资产太多 | 文档、persona、commands 一起加，造成维护税 | 先文档，后按需资产化 |
| 规则再次分散 | shared conventions 没真正收口，反而又多一层 | 明确 shared doc 是公共约定唯一入口 |

### `P1` 完成标志

- 跨 skill 重复的公共规则已有集中落点。
- 家族入口方式对新会话更低摩擦，且 direct invoke / chain invoke 的使用边界清楚。
- router 的公共说明负担继续下降（由 `using-ahe-workflow` 与 entrypoint docs 承接）。
- 新增的任何 wrapper / persona 都有明确、窄而真实的使用场景。

## `P2`：对外化准备

### 目标

只有在出现真实跨仓库复用需求时，才为 AHE workflow family 补齐对外采用所需的映射、边界和可选包装层，并明确外部仓库是采用“单 skill 独立调用”还是“整条 workflow 串联调用”。

### 范围

- repo-agnostic mapping
- 独立调用 vs 全链路接入说明
- core vs extension 分层
- setup / install 文档
- 可选 hook / plugin / packaging 示意

### 工作流分解

### `P2-1` 写外部采用 readiness checklist

建议产物：

- `docs/ahe-workflow-externalization-guide.md`

至少说明：

- 当前 AHE 默认依赖哪些目录与工件
- 哪些工件是必须映射的
- 哪些审批点与 evidence 约束不能被省略
- 外部仓库若只采用单个 `ahe-*` skill，需要最少满足哪些 direct invoke 前置条件

### `P2-2` 写路径映射指南

目标：

- 让非 AHE 仓库知道如何映射以下路径，而不弱化 workflow contract：

- `docs/specs/`
- `docs/tasks/`
- `docs/reviews/`
- `docs/verification/`
- `task-progress.md`
- `RELEASE_NOTES.md`

### `P2-3` 定义 core vs extensions

建议产物：

- `docs/ahe-workflow-core-vs-extensions.md`

建议 core 包含：

- `ahe-workflow-router` 路由
- profile
- evidence chain
- review / gate / finalize contract
- direct invoke fallback 规则

建议 extension 包含：

- 命令入口
- persona
- setup helpers
- 可选 hooks
- 可选 packaging

### `P2-4` 只在真实需求出现后补 setup 与包装层

只有满足以下至少一个条件时，才建议进入：

- 明确有第二个仓库要采用 AHE workflow
- 已经出现重复的手动安装 / 接入动作
- 已有内部使用者反复请求更低摩擦 setup

此时才考虑：

- setup / install 文档
- hook 示例
- plugin 示例
- 更明确的核心包 / 扩展包落地方式
- 单节点采用与整链采用的接入示例

### `P2` 风险与控制点

| 风险 | 说明 | 控制方式 |
| --- | --- | --- |
| 过早产品化 | 还没稳定就加包装层 | 以真实复用需求作为进入条件 |
| 稀释核心约束 | 为了通用化而弱化 pause points / gates | externalization 只做映射，不做软化 |
| 维护税上升 | setup/hook/plugin 长期无人使用 | 所有包装层都标记为 optional |

### `P2` 完成标志

- 外部仓库能理解如何映射必要工件与目录。
- core 与 optional surface 的边界已经清楚。
- 对外化文档不要求弱化 AHE 的 evidence-first 与 route-first 原则。

## 阶段门槛

| 阶段切换 | 必须满足的条件 |
| --- | --- |
| `P0 -> P1` | anatomy 已冻结；router collateral 已对齐；`task-progress` schema 已对齐；核心主链技能已有统一骨架；核心技能的独立调用与串联调用 contract 已明确 |
| `P1 -> P2` | shared conventions 已稳定；direct invoke 与 chain invoke 的入口方式已清楚；新增 wrapper / persona 是否值得保留已有初步证据；出现真实跨仓库复用信号 |

## 批次执行建议

| 批次 | 建议范围 | 类型 |
| --- | --- | --- |
| Batch 1 | 计划文档 + anatomy 文档 | docs-only，已完成 |
| Batch 2 | router collateral 对齐 | docs / references alignment |
| Batch 3 | `templates/task-progress-template.md` | template refactor |
| Batch 4 | `ahe-specify` / `ahe-design` / `ahe-tasks` | core chain normalization + dual-mode contract |
| Batch 5 | `ahe-test-driven-dev` / `ahe-regression-gate` / `ahe-completion-gate` / `ahe-finalize` | core chain normalization + dual-mode contract |
| Batch 6 | review / branch skills sweep | secondary normalization + dual-mode contract |
| Batch 7 | `skills/ahe-workflow-router/SKILL.md` 第二轮瘦身（历史：pre-split 合并 router 第二轮瘦身） | kernel slimming |
| Batch 8 | shared conventions + entrypoints docs | friction reduction |
| Batch 9 | externalization docs 与可选包装层 | conditional |

## 交付物矩阵

| 交付物 | 阶段 | 类型 | 是否优先 |
| --- | --- | --- | --- |
| `docs/ahe-workflow-family-optimization-execution-plan.md` | `P0` | docs-only | 是 |
| `docs/ahe-workflow-skill-anatomy.md` | `P0` | docs-only | 是，已完成 |
| `templates/task-progress-template.md` | `P0` | template refactor | 是 |
| `skills/ahe-workflow-router/SKILL.md` | `P0` | skill refactor | 是 |
| `skills/ahe-workflow-router/references/*.md` | `P0` | docs / references alignment | 是 |
| 核心主链 `skills/ahe-*/SKILL.md` | `P0` | skill refactor | 是 |
| `docs/ahe-workflow-shared-conventions.md` | `P1` | docs-only | 是 |
| `docs/ahe-workflow-entrypoints.md` | `P1` | docs-only | 是 |
| `docs/ahe-review-persona-matrix.md` | `P1` | docs-only | 可选 |
| `docs/ahe-command-entrypoints.md` | `P1` | docs-only | 可选 |
| `skills/using-ahe-skills/SKILL.md` | `P1` | optional asset | 条件触发 |
| `agents/*.md` | `P1` | optional asset | 条件触发 |
| `docs/ahe-workflow-externalization-guide.md` | `P2` | docs-only | 条件触发 |
| `docs/ahe-workflow-core-vs-extensions.md` | `P2` | docs-only | 条件触发 |
| setup / hook / plugin 示例 | `P2` | optional asset | 条件触发 |

## 验证策略

本仓库当前没有统一 CI，因此本计划建议使用“文档检查 + 路径检查 + 轻量 skill 校验”的组合方式推进。

### docs-only 变更

- 检查路径是否真实存在
- 检查文档之间的引用是否一致
- 检查新增文档是否与 `skills/design_rules.md` 保持一致
- 使用编辑器诊断确认无明显 Markdown 问题

### skill / template 变更

- 校验 `SKILL.md` frontmatter 是否仍合法
- spot-check canonical 字段在上下游是否一致
- 检查 references 下沉后，主文件仍保留必要 authority

如需轻量校验，可在 `.cursor/skills/skill-creator/` 下运行：

```shell
python -m scripts.quick_validate <skill-dir>
```

建议优先用于：

- `skills/ahe-workflow-router/`
- 发生 frontmatter 调整的 `ahe-*` 目录

## 执行建议总结

- `P0` 先解决结构矛盾，不追求包装层。
- `P0` 的当前起点已经不是“有没有 anatomy”，而是“让 anatomy 真正落到 live skills 与 collateral 上”。
- `P1` 先补共享说明，再决定是否真的需要新增 persona、meta-skill 或命令层。
- `P2` 只在真实外部复用压力出现后开启。
- 整个计划都应围绕一个原则展开：保留 AHE 的 workflow kernel，让 `ahe-*` 节点兼容“独立调用 + 串联调用”，并借鉴 `agent-skills-main` 的统一外壳，而不是牺牲内核去追求“看起来更轻”。
