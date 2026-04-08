# AHE Workflow Shared Conventions

## Purpose

本文集中收口 `ahe-*` workflow family 的共享约定，避免这些规则散落在各个 skill、reference 与计划文档中。

它优先回答以下问题：

1. progress schema 应该怎么写
2. 什么算 fresh evidence
3. review / gate 的 verdict、severity 与 handoff 应该如何统一
4. `record_path`、评审记录、验证记录与状态工件应如何表达
5. 哪些旧字段只允许“读时归一化”，不允许继续写回

## Canonical Progress Schema

默认 progress state 建议统一使用以下字段：

| 字段 | 含义 | 写法约定 |
|---|---|---|
| `Current Stage` | 当前 workflow 所处节点 | 新工件优先直接写 canonical 节点名 |
| `Workflow Profile` | 当前 workflow 密度 | 仅使用 `full` / `standard` / `lightweight` |
| `Current Active Task` | 当前唯一活跃任务 | 必须可唯一指向一个任务；未锁定时留空或写项目约定占位值 |
| `Pending Reviews And Gates` | 仍未完成的 review / gate 节点 | 用 canonical 节点名列出剩余链路 |
| `Next Action Or Recommended Skill` | 当前显式下一步 | 只能写一个 canonical 节点值，不得写自由文本 |

### `Current Stage`

推荐写法：

- 新的 AHE progress 记录优先直接写 canonical 节点名，例如 `ahe-test-driven-dev`
- 若项目必须使用别名，应在 `AGENTS.md` 中声明一对一映射，并保证 router（及读入时的 **legacy 合并路由** 别名）可唯一归一化
- 不再继续写 `phase`、`Current Phase`、自然语言阶段名等 generic 字段

### `Current Active Task`

约束：

- 一个工作周期只允许一个权威版活跃任务
- 在任务尚未被正式锁定前，不伪造活跃任务
- 若原任务已失效，可留空或写项目约定占位值，例如 `pending reselection`

### `Next Action Or Recommended Skill`

约束：

- 只能写一个 canonical 值
- 不得使用 `done`、`继续推进`、`看情况`、`工作流完成` 这类自然语言
- workflow 已结束时，留空或使用项目约定 null 值；不要伪造新的下游节点

## Canonical Verdict And Severity

### Verdict vocabulary

review / gate 节点统一使用：

- `通过`
- `需修改`
- `阻塞`

如果项目需要英文映射，可在 `AGENTS.md` 中声明 `pass` / `revise` / `blocked` 的等价词，但 live AHE family 文档应保持 verdict vocabulary 稳定。

### Severity vocabulary

review / bug-patterns 发现项统一使用：

- `critical`: 会阻塞下游判断，或会直接污染下一阶段输入
- `important`: 不一定立刻阻塞整个 workflow，但必须在进入指定下一节点前修复
- `minor`: 不阻塞当前主链，但应作为改进项显式记录

约束：

- severity 用于描述发现项，不替代 verdict
- 不要把所有问题都标成 `critical`
- 先有 finding，再给 severity；不要脱离证据抽象判级
- 本节只冻结 vocabulary；各 `ahe-*review` skill 对 `critical` / `important` 的触发阈值仍以各自 `SKILL.md` 为准

## Fresh Evidence

### 定义

fresh evidence 指与当前最新代码状态、当前任务边界和当前验证目标直接对应的证据，而不是旧日志、旧截图或口头描述。

### 最低要求

当 skill 依赖 fresh evidence 时，记录中至少应能看出：

- 执行了什么命令或验证动作
- 结果是什么
- 这次执行为什么属于当前最新代码状态
- 它覆盖了哪一部分风险、行为或声明边界

### 常见适用节点

- `ahe-test-driven-dev`：需要 fresh RED / GREEN evidence
- `ahe-regression-gate`：需要 fresh regression evidence
- `ahe-completion-gate`：需要 fresh completion evidence
- `ahe-hotfix`：需要 fresh defect reproduction / fix evidence

### 不被接受的写法

- “上次已经跑过了”
- “旧日志显示之前是绿的”
- “口头上确认没问题”
- 只写“测试通过”，不写命令、摘要或新鲜度锚点

## Canonical Next Action Vocabulary

`Next Action Or Recommended Skill` 与 reviewer 摘要里的 `next_action_or_recommended_skill` 应统一落到以下受控 vocabulary：

- upstream authoring: `ahe-specify` / `ahe-design` / `ahe-tasks`
- upstream review: `ahe-spec-review` / `ahe-design-review` / `ahe-tasks-review`
- human confirmation: `规格真人确认` / `设计真人确认` / `任务真人确认`
- implementation and quality: `ahe-test-driven-dev` / `ahe-bug-patterns` / `ahe-test-review` / `ahe-code-review` / `ahe-traceability-review` / `ahe-regression-gate` / `ahe-completion-gate` / `ahe-finalize`
- branch and orchestration: `ahe-hotfix` / `ahe-increment` / `ahe-workflow-router`

约束：

- 必须是唯一值
- 不得把多个候选动作拼成一个字符串
- review 节点返回 review 节点，表示父会话应派发 reviewer subagent，而不是在当前上下文内联继续 review
- 写时必须使用 canonical 值；若读取到旧工件中的 legacy 合并路由写法、坏值或自由文本，运行时容错规则以 `skills/ahe-workflow-router/references/execution-semantics.md` 为准（历史工件若仍引用 legacy 路径前缀下的同文件，按兼容读法处理）

## Record Path Conventions

### `record_path`

当 reviewer subagent 返回结构化摘要时：

- `record_path` 必须指向实际已经写入的 review 记录路径
- `record_path` 不能只是“计划写到哪里”
- 父会话消费摘要时，应以 `record_path` 作为 review artifact 的权威落点

### 默认逻辑工件布局

除非 `AGENTS.md` 已声明等价路径，否则默认推荐：

| 逻辑工件 | 默认路径 |
|---|---|
| requirement spec | `docs/specs/YYYY-MM-DD-<topic>-srs.md` |
| design doc | `docs/designs/YYYY-MM-DD-<topic>-design.md` |
| task plan | `docs/tasks/YYYY-MM-DD-<topic>-tasks.md` |
| progress state | `task-progress.md` |
| reviews | `docs/reviews/`（可选但建议） |
| verification | `docs/verification/`（可选但建议） |
| release notes | `RELEASE_NOTES.md` |

### 记录落盘原则

- review / gate 结论必须写入仓库工件
- 对话中的摘要不能替代 review / verification 记录
- finalize 只能消费已落盘的 completion / regression / release artifacts，不能把对话记忆当成 closeout evidence

## Review / Gate Return Rules

### Reviewer return contract

reviewer subagent 的最小结构化摘要统一使用：

```json
{
  "conclusion": "通过|需修改|阻塞",
  "next_action_or_recommended_skill": "唯一 canonical 节点",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["关键发现 1"],
  "needs_human_confirmation": false,
  "reroute_via_router": false
}
```

补充规则：

- `needs_human_confirmation=true` 仅用于 `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review` 在 `conclusion=通过` 时
- 若 `conclusion=需修改` 或 `阻塞`，默认 `needs_human_confirmation=false`
- 若问题本质属于 route / stage / profile / 上游证据冲突，应设置 `reroute_via_router=true`
- 历史摘要或旧 skill 若仍返回 legacy reroute 字段，读时应视为与 `reroute_via_router` 同义（映射见下节 Legacy Alias Policy）；新产出应优先写 `reroute_via_router`

### 父会话消费顺序

父会话读取 reviewer 摘要时，先检查是否命中 `skills/ahe-workflow-router/references/execution-semantics.md` 中定义的暂停点与“先向用户展示”的义务；在完成任何必需的展示或讨论后，再按以下顺序处理：

1. 若 `reroute_via_router=true`（或读时把 legacy reroute 字段视为 true），先回到 `ahe-workflow-router`
2. 否则若 `conclusion=通过` 且 `needs_human_confirmation=true`，进入真人确认节点
3. 否则若 `conclusion=通过` 且无需真人确认，进入 `next_action_or_recommended_skill`
4. 否则若 `conclusion=需修改` 或 `阻塞`，按 `next_action_or_recommended_skill` 回修或补条件

补充规则：

- 对 `ahe-spec-review` / `ahe-design-review`，`需修改` 与内容回修型 `阻塞` 不是“静默自动回修”；父会话需先向用户展示评审结论与修订重点
- 对 `ahe-spec-review` / `ahe-design-review`，若 `阻塞` 且需要经 router 重编排，父会话需先向用户展示阻塞原因，再回到 `ahe-workflow-router`
- 对其他 review / gate，若结论为 `需修改` / `阻塞` 且修订方向不明确，也应先与用户讨论，而不是机械自动推进

### Gate / implementation 回流规则

对 `ahe-test-driven-dev`、`ahe-regression-gate`、`ahe-completion-gate` 这类非 reviewer 节点，回流约定统一为：

- 内容修订、缺少测试、验证失败、局部证据不足：回到最近的实现或门禁节点
- route / stage / profile / 上游证据冲突：回到 `ahe-workflow-router`
- 新的范围变化：优先判断是否切到 `ahe-increment`
- 新的紧急缺陷：优先判断是否切到 `ahe-hotfix`

## Human Confirmation Rules

以下节点的“评审通过”不等于“已批准”：

- `ahe-spec-review`
- `ahe-design-review`
- `ahe-tasks-review`

对应地，以下真人确认节点由父会话负责：

- `规格真人确认`
- `设计真人确认`
- `任务真人确认`

只有 reviewer 返回 `通过`，且对应真人确认完成后，相关上游工件才算已批准。

## Legacy Alias Policy

旧字段与旧别名只允许用于“读取旧工件时的归一化判断”，不应继续写回：

- `phase` -> `Current Stage`
- `Current Task` -> `Current Active Task`
- `Next Action` / `next skill` -> `Next Action Or Recommended Skill`
- `ahe-workflow-starter` -> `ahe-workflow-router`（历史 **legacy 合并入口/router** skill 名；独立目录已移除）
- `reroute_via_starter` -> `reroute_via_router`（legacy reroute 字段名；读时同义）

原则：

- 读时可兼容
- 写时必须收口到 canonical schema
- 若项目必须保留别名，必须在 `AGENTS.md` 中声明映射

## Practical Checklist

当你在编写或审阅某个 `ahe-*` skill 时，至少确认：

- [ ] progress schema 使用 canonical 字段名
- [ ] verdict 与 severity vocabulary 没有漂移
- [ ] `Next Action Or Recommended Skill` / `next_action_or_recommended_skill` 只写唯一 canonical 值
- [ ] review / gate 结论会落盘到仓库工件
- [ ] 依赖 fresh evidence 的节点明确写出新鲜度锚点
- [ ] route / stage / profile / 上游证据冲突会回到 `ahe-workflow-router`
