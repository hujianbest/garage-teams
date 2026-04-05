# AHE Workflow Entrypoints

## Purpose

本文定义 `ahe-*` family 的入口策略，回答三个问题：

1. 什么时候必须先走 `ahe-workflow-starter`
2. 什么时候允许 direct invoke 某个具体 `ahe-*` skill
3. starter 编排模式与 direct invoke 模式在输入、输出和责任边界上有什么差异

## One-Line Rule

默认先走 `ahe-workflow-starter`。

direct invoke 不是主路径替代品，而是在“当前节点已经足够明确、前置条件已经满足、且 route / stage / profile 不存在冲突”时允许使用的受控捷径。

## Always Start With `ahe-workflow-starter`

以下场景默认都应先经过 starter：

- 开始新的需求、功能、项目或一轮新工作周期
- 用户说“继续”“推进”“开始做”“先处理这个”
- 用户点名某个 `ahe-*` skill，但当前仍需确认它是不是正确节点
- 用户只说“帮我 review / gate 一下”，但还没明确是哪一个 review / gate 节点
- 当前存在 route / stage / profile 不确定性
- 当前工件证据冲突
- 用户提出需求变更、范围变化、验收变化
- 用户提出紧急缺陷修复
- 某个 review / gate 刚完成，需要恢复后续编排

理由：

- starter 负责决定 `Workflow Profile`
- starter 负责决定当前 canonical 节点
- starter 负责在主链、increment、hotfix 之间做受控切换
- starter 负责在命中 review 节点时派发 reviewer subagent

## Direct Invoke Is Allowed Only When

同时满足以下条件时，才允许 direct invoke 某个具体 skill：

1. 当前节点已经清楚，不需要再做 route / stage 判断
2. 当前请求是该 skill 的本地职责，而不是更上游或并行节点职责
3. 所需核心工件已经存在且可读
4. 没有 profile 冲突、批准状态冲突或证据冲突
5. 调用方接受“本 skill 只完成本节点职责，后续编排仍回到父会话 / starter”

若任一条件不满足，回到 `ahe-workflow-starter`。

## Entrypoint Matrix

| 节点类别 | 代表 skill | 典型入口条件 | 不该这样进入的典型情况 |
|---|---|---|---|
| Orchestrator | `ahe-workflow-starter` | 阶段不清、需要恢复编排、需要判断 profile 或下一步 | 无；它就是默认入口 |
| Authoring | `ahe-specify` / `ahe-design` / `ahe-tasks` | 当前明确是在补齐规格、设计或任务计划正文；上游前置条件满足 | 阶段不清、其实该做 review、其实该走支线、或已进入实现 |
| Review | `ahe-spec-review` / `ahe-design-review` / `ahe-tasks-review` / downstream reviews | 当前明确是 review-only，请求和工件都指向一个具体 review 节点 | 没有可评审草稿 / 记录、其实需要继续产出正文、或 route / stage 冲突 |
| Implementation | `ahe-test-driven-dev` | 已有唯一活跃任务，且任务计划已批准，或已有 hotfix handoff / 回流 findings | 无唯一活跃任务、批准状态冲突、其实要做 review / gate |
| Quality analysis | `ahe-bug-patterns` | 已有实现交接块或明确改动范围，当前需要专项缺陷模式排查 | 缺实现范围、其实要继续实现、其实只是一般 review / gate |
| Gates | `ahe-regression-gate` / `ahe-completion-gate` | 上游记录已落盘，当前就是要跑正式门禁 | 缺上游 handoff / verification 输入、缺环境、其实该回到实现或 starter |
| Finalize | `ahe-finalize` | completion gate 已允许收尾，当前要做状态 / 文档 / 发布说明收口 | 仍需补实现或补验证、gate 记录缺失或不支持 finalize |
| Branch analysis | `ahe-hotfix` / `ahe-increment` | 问题明确属于 hotfix 或 increment，当前要做影响分析与 re-entry，而不是直接改代码 | 阶段不清、输入证据冲突、其实已经明确进入实现 |

## Special Rule For Review Skills

review skills 有双重入口语义：

- direct invoke：用户明确要求“review 这份 spec/design/tasks/tests/code/traceability”，调用方可直接把当前工作视为某个 review 节点
- chain invoke：starter 或父会话已经判定当前 canonical 节点是某个 review 节点

差异：

- direct invoke 时，调用方需要自己先确认这真的是 review-only 场景
- 无论是 direct invoke 还是 chain invoke，review 的实际执行都仍遵循 `skills/ahe-workflow-starter/references/review-dispatch-protocol.md`：由父会话构造 review request，并派发 reviewer subagent
- 无论哪种模式，review skill 只负责给出 review 记录与结构化摘要，不负责推进主链

## Starter Mode vs Direct Invoke

| 维度 | Starter 编排模式 | Direct invoke 模式 |
|---|---|---|
| 目标 | 决定当前应该进入哪个节点 | 完成某一个已经明确的节点职责 |
| 最小输入 | 用户请求 + `AGENTS.md` + 上游工件状态 + `task-progress.md` + review / gate / verification 证据 | 当前节点所需最小工件 + 当前请求 |
| 是否判断 profile | 是 | 否；若 profile 不清，回 starter |
| 是否判断 route / stage | 是 | 否；若 route / stage 不清，回 starter |
| 是否决定下一节点 | 是 | 否；只写 canonical handoff，后续编排交回父会话 / starter |
| review 如何执行 | 一旦进入 review 节点，统一由父会话按 review-dispatch protocol 派发 reviewer subagent | 与 starter 模式相同；差别只在于 review 节点是由调用方直接选定，还是由 starter 先判定出来 |
| 输出 | 当前阶段判断、选定 profile、推荐节点，并立即继续执行或命中暂停点 | 节点本地工件、状态更新、canonical handoff、必要的 review / verification record |

## Input Differences

### Starter 应优先读取

- `AGENTS.md` 中与 `ahe-workflow` 相关的映射、批准状态别名、profile 规则
- 规格 / 设计 / 任务工件的存在情况与批准状态
- `task-progress.md`
- review / verification / release artifacts
- 用户当前请求

starter 阶段不应先做大范围代码探索。

### Direct invoke 应优先读取

- 当前 skill 明确要求的最小工件
- 与本节点直接相关的上游记录或 findings
- 当前请求中与本节点职责直接相关的部分

direct invoke 不应顺手接管 orchestrator 职责。

## Output Differences

### Starter 输出

starter 的最小输出是：

1. 当前识别阶段
2. 选定的 `Workflow Profile`
3. 推荐的下一步 skill

随后：

- 若命中 review 节点，由父会话派发 reviewer subagent，而不是在当前上下文内联执行 review
- 否则若命中暂停点，停在父会话等待用户输入
- 否则，立即进入目标 skill

### Direct invoke 输出

direct invoke 的最小输出是当前节点的本地交付：

- 规格 / 设计 / 任务草稿
- review 记录与结构化摘要
- 实现交接块
- verification / gate 记录
- closeout pack
- canonical `Next Action Or Recommended Skill`

direct invoke 的 handoff 只表达“本节点之后推荐谁”，不替代 starter 做全链路恢复编排。

## Canonical Direct Invoke Examples

- “先把需求梳理清楚，不要做设计” -> 可 direct invoke `ahe-specify`
- “帮我 review 这份 spec 草稿” -> 若规格草稿已存在且这是 review-only 请求，可 direct invoke `ahe-spec-review`
- “按 TDD 实现当前 active task” -> 若任务计划已批准且活跃任务唯一，可 direct invoke `ahe-test-driven-dev`
- “这是线上 bug，先收敛 root cause 和最小修复边界” -> 可 direct invoke `ahe-hotfix`
- “completion gate 过了，帮我做收尾和 release notes” -> 若 gate 记录已落盘，可 direct invoke `ahe-finalize`

## Anti-Patterns

以下做法都不算合法 direct invoke：

- 用户点名 skill，就直接执行，不核对当前阶段
- direct invoke 某个 implementation / gate skill，却没有读取最小上游工件
- 让 authoring skill 顺手决定完整下游链路
- 让 review skill 顺手开始修文档或做实现
- 让 finalize 在 gate 未通过时提前收尾
- 在 route / stage / profile 冲突下继续硬做当前 skill

## Practical Rule Of Thumb

若你有一丝疑问“现在到底是不是这个节点”，就不要赌 direct invoke，直接回到 `ahe-workflow-starter`。
