---
name: ahe-bug-patterns
description: 基于团队历史错误案例和通用缺陷模式，对当前改动做专项排查，判断高风险模式是否已被识别并得到足够防护，从而决定是进入 `ahe-test-review` 还是先回到 `ahe-test-driven-dev`。适用于 full / standard profile 中实现完成后的首个质量节点；若阶段不清、证据冲突或当前其实缺少实现交接块，先回到 `ahe-workflow-router` 或 `ahe-test-driven-dev`。
---

# AHE 缺陷模式排查

基于已知错误模式，对当前改动做专项风险排查，并决定是否可以进入 `ahe-test-review`。

## Overview

这个 skill 用来把“团队已经吃过的亏”前置到当前任务。

高质量缺陷模式排查不只是列风险清单，而是判断：

- 当前改动命中了哪些已知 defect families
- 这些风险是否已经被测试、保护逻辑或约束吸收
- 下游 `ahe-test-review` 是否可以在已有风险视角上继续推进

## When to Use

在这些场景使用：

- `ahe-test-driven-dev` 已完成当前任务实现，准备进入正式质量链
- 用户明确要求“按缺陷模式排查这次改动”
- 当前改动涉及边界、状态、时序、幂等、资源释放、配置读取、历史复发区域等高风险面
- 热修复、缺陷复发或疑似双路径不一致场景需要专项排查

不要在这些场景使用：

- 当前需要一般测试质量裁决，改用 `ahe-test-review`
- 当前需要一般实现质量裁决，改用 `ahe-code-review`
- 当前需要执行回归验证，改用 `ahe-regression-gate`
- 当前请求只是阶段不清、profile 不稳或证据链冲突，先回到 `ahe-workflow-router`

## Standalone Contract

当用户直接点名 `ahe-bug-patterns` 时，至少确认以下条件：

- 存在当前改动范围或实现交接块
- 存在当前任务目标或最少可核对的实现背景
- 能读取 `AGENTS.md` 中与历史事故、风险区域、必查模式或排查约定有关的内容（如果存在）
- 当前请求确实是专项风险排查，而不是一般代码评审或测试评审

如果前提不满足：

- 缺改动范围、缺实现交接块或本质上需要继续实现：回到 `ahe-test-driven-dev`
- 缺 route / stage 判断、profile 不清或输入证据冲突：回到 `ahe-workflow-router`

## Chain Contract

当本 skill 作为链路节点被带入时，默认在父会话 / 当前执行上下文中运行，而不是按 reviewer subagent return contract 消费。

默认读取：

- 当前实现交接块或等价证据
- 当前改动涉及的实现与测试变更
- `AGENTS.md` 中与历史事故、风险区域、必查模式和验证约定有关的内容
- 当前任务相关的规格 / 设计 / 任务锚点（如有）
- 团队已有缺陷模式库、事故复盘或通用 defect families（如有）
- `task-progress.md` 中的 `Current Stage`、`Current Active Task`、`Workflow Profile`，以及 `Workspace Isolation` / `Worktree Path` / `Worktree Branch`（如果存在）

本节点完成后应写回：

- 缺陷模式排查记录
- canonical `Next Action Or Recommended Skill`
- 当前高风险模式、缺失防护与建议证伪方式
- 若当前 workflow 已使用 worktree，则显式保留 / 写回 `Workspace Isolation` / `Worktree Path` / `Worktree Branch`

若当前是 lightweight 手动补充分析，默认把结果视为补充性发现，不自动改写 canonical 主链；但若排查证明当前 profile / route 已不成立，则必须把下一步显式写为 `ahe-workflow-router`。

## Hard Gates

- 在 full / standard 正式链路中，未完成缺陷模式排查前，不得把当前任务视为已准备好进入 `ahe-test-review`。
- 如果当前输入工件还不足以判定 stage / route，不直接开始缺陷模式排查。
- 若上游实现交接块声明 `worktree-active`，但当前记录中缺少 `Worktree Path` / `Worktree Branch`，不得返回 `通过`。
- 本 skill 不替代 `ahe-test-review`、`ahe-code-review`、`ahe-regression-gate` 或主链重编排。

## Quality Bar

高质量缺陷模式排查结果至少应做到：

- 对每个命中模式写清 Pattern、机制、证据锚点、严重级别与置信度
- 区分“已被防护吸收的风险”与“仍然需要测试 / 实现补强的风险”
- 指出扩散面与最合适的证伪方式，而不是只说“这里有风险”
- 若当前候选实现位于 worktree，排查证据能说明它消费的是同一 `Worktree Path` / `Worktree Branch`
- 给下游 `ahe-test-review` 或上游 `ahe-test-driven-dev` 留下清晰可执行的 handoff
- 给出唯一下一步，并显式使用 canonical `Next Action Or Recommended Skill`

## Inputs / Required Artifacts

排查完成后，必须将本次结论写入：

- `docs/reviews/bug-patterns-<task>.md`

如 `AGENTS.md` 为当前项目声明了等价路径，按其中映射路径保存。

若项目尚未形成固定 review 记录格式，默认使用：

- `ahe-coding-skills/templates/review-record-template.md`

如果使用通用模板中的英文结论字段，请按以下方式映射：

- `通过` -> `pass`
- `需修改` -> `revise`
- `阻塞` -> `blocked`

如果当前任务正在使用 `task-progress.md` 驱动 workflow，且当前 profile 是 full / standard，则父会话在消费本节点输出后，还应同步更新：

- `task-progress.md` 中的缺陷模式排查状态
- `task-progress.md` 中的 `Next Action Or Recommended Skill`
- `task-progress.md` 中的 `Workspace Isolation` / `Worktree Path` / `Worktree Branch`（若当前 workflow 已使用 worktree）
- 当前命中的高风险模式、缺失防护与待补动作（如有）

若项目尚未形成固定进度记录格式，默认使用：

- `ahe-coding-skills/templates/task-progress-template.md`

如果团队还没有成型的缺陷模式库，可先从以下模板初始化：

- `ahe-coding-skills/ahe-bug-patterns/references/bug-pattern-catalog-template.md`

## Workflow

### 1. 先建立证据基线

在给出结论前，先读取并固定以下证据来源：

- 当前实现交接块或等价证据
- 当前改动涉及的实现与测试变更
- `AGENTS.md` 中与历史事故、风险区域、必查模式和验证约定有关的内容
- 当前任务相关的规格 / 设计 / 任务锚点（如有）
- 团队已有缺陷模式库、事故复盘或通用 defect families（如有）
- `task-progress.md` 中的 `Current Stage`、`Current Active Task`、`Workflow Profile`，以及 `Workspace Isolation` / `Worktree Path` / `Worktree Branch`（如果存在）

不要只根据“经验直觉”或“这个区域以前总出问题”就直接下结论；每个命中模式都要落回当前改动证据。

若当前实现交接块写明 `worktree-active`，应在同一 `Worktree Path` / `Worktree Branch` 视角下读取候选实现，而不是退回仓库根目录看另一份状态。

### 2. 选定本轮 pattern families

至少覆盖以下风险族中的适用部分：

- 历史重复缺陷
- 边界值 / 空值 / 默认值
- 状态切换 / 时序 / 重入 / 幂等
- 资源释放 / 异常恢复 / 配置读取
- AI-assisted blind spots：双路径不一致、跨层传播不完整、保护性分支未同步更新

若项目存在更具体的 team-specific pattern catalog，优先按项目模式族展开。

### 3. 结构化记录命中模式

对每个命中模式，至少写清：

- Pattern ID / 名称
- 机制
- 证据锚点
- 严重级别：`critical|important|minor`
- 重复性：`重复缺陷|近似缺陷|新风险`
- 置信度：`demonstrated|probable|weak-signal`

并额外判断：

- 当前风险是否已被测试承接
- 当前风险是否已被保护逻辑、约束或设计说明吸收
- 若没有，最适合交给哪个下游动作补齐

### 4. 形成 verdict 与下一步

判定规则：

- 只有在主要 defect families 已被检查，且关键风险已被测试、保护逻辑或合理说明吸收时，才返回 `通过`
- 命中了已知高风险模式，但仍缺必要测试、保护逻辑、修正或约束说明时，返回 `需修改`
- 连最基本的改动面、实现证据、活动任务或当前 profile 都无法判定，或 route / stage / profile / 上游证据冲突时，返回 `阻塞`

下一步规则：

- `通过`：`ahe-test-review`
- `需修改`：`ahe-test-driven-dev`
- `阻塞` 且属于实现 / 证据补齐类：`ahe-test-driven-dev`
- `阻塞` 且属于 route / stage / profile / 上游证据冲突：`ahe-workflow-router`

### 5. 写记录并回传主链

- full / standard 正式链路中，应把 canonical `Next Action Or Recommended Skill` 写成 `ahe-test-review`、`ahe-test-driven-dev` 或 `ahe-workflow-router`
- lightweight 手动调用时，默认只记录发现；但若判断当前 lightweight profile 不再成立，应显式把下一步写成 `ahe-workflow-router`

## Output Contract

排查记录正文请严格使用以下结构：

```markdown
## 结论

通过 | 需修改 | 阻塞

## 上游已消费证据

- Task ID
- 实现交接块 / 等价证据
- 触碰工件
- `Workspace Isolation`
- `Worktree Path`
- `Worktree Branch`

## 命中的缺陷模式（结构化）

- Pattern ID / 名称
- 机制
- 证据锚点
- 严重级别
- 重复性
- 置信度

## 缺失的防护

- 条目

## 回归假设与扩散面

- 假设
- 建议证伪方式

## 下一步

- `通过`：`ahe-test-review`
- `需修改`：`ahe-test-driven-dev`
- `阻塞`：`ahe-test-driven-dev` 或 `ahe-workflow-router`

## 记录位置

- `docs/reviews/bug-patterns-<task>.md` 或映射路径
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| “先大概扫一眼就行” | 缺陷模式排查的价值来自结构化命中记录，而不是泛泛担心。 |
| “这些风险后面 review 会再看” | 下游 review 需要消费你已经识别出的风险，而不是替你从零开始找。 |
| “没有团队 pattern catalog，就没法做” | 没有本地模式库时，至少要覆盖通用 defect families。 |
| “命中模式但现在没出错，可以先过” | 命中高风险模式但缺少防护，应该在这里暴露，而不是等回归失败。 |
| “把所有风险都写成 critical 更稳” | 严重级别失真会让下游无法区分真正阻塞项。 |
| “反正后面还有 gate，这里不用关心 worktree 来自哪里” | 若当前改动在 worktree 中产生，缺陷模式排查也必须锚定到同一工作目录。 |

## Red Flags

- 不读实现交接块就直接按经验排查
- 只列风险，不写机制和证据锚点
- 明知命中历史缺陷模式，却不给测试 / 防护补强建议
- 把 `ahe-bug-patterns` 做成泛泛代码评审
- 返回多个候选下一步，而不是唯一 canonical handoff
- 当前实现明明来自 `worktree-active`，却在排查记录中丢失 `Worktree Path` / `Worktree Branch`

## Verification

只有在以下条件全部满足时，这个 skill 才算完成：

- [ ] 排查记录已经落盘
- [ ] 给出明确结论、命中模式、缺失防护和唯一下一步
- [ ] 命中模式已经结构化记录了机制、证据锚点、严重级别和置信度
- [ ] 若当前 workflow 使用 worktree，记录已显式写出 `Workspace Isolation` / `Worktree Path` / `Worktree Branch`
- [ ] 当前结论已经足以让父会话判断是进入 `ahe-test-review`、回到 `ahe-test-driven-dev`，还是回到 `ahe-workflow-router`
