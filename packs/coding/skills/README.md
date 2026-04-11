# AHE Skills

`ahe-coding-skills/` 用于存放 `awesome-harness-engineering`（`ahe`）仓库自己的可复用 skill 资产，以及直接服务于这些 skill 的设计规则。

## 目录约定

- `ahe-coding-skills/README.md`：本目录总览
- `ahe-coding-skills/docs/`：AHE workflow family 的共享文档
- `ahe-coding-skills/templates/`：AHE workflow family 的共享模板
- `ahe-coding-skills/design_rules.md`：skill 与 harness 资产的设计原则
- `ahe-coding-skills/<skill-name>/SKILL.md`：单个 skill 的入口文件
- `ahe-coding-skills/<skill-name>/references/`：该 skill 的补充说明、模板或参考资料

## Public entry skill

除 `ahe-*` workflow 节点外，AHE 还包含一层公开入口：

- `ahe-coding-skills/using-ahe-workflow/` — AHE workflow family 的公开入口、命令入口解释层和 discovery shell；它帮助判断应 direct invoke 哪个节点，或何时交给当前 runtime router。

## Runtime router and alias

- `ahe-coding-skills/ahe-workflow-router/` — AHE workflow family 的 canonical runtime router，负责 stage / profile / branch / review recovery authority。
- 历史文档或旧 handoff 若仍出现 **legacy 合并入口/路由** 旧名称，按 `ahe-workflow-router` 读法理解（非当前独立 skill）；明细见 `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md`。

## Worktree isolation

AHE workflow 现在支持把 Git worktree 作为 pack-local 隔离工作目录来使用。

对外应这样理解：

- `ahe-workflow-router` 负责决定当前任务是继续 `in-place`，还是进入 `worktree-required` / `worktree-active`
- `task-progress.md` 可追加 `Workspace Isolation`、`Worktree Path`、`Worktree Branch` 作为 coordination fields
- `ahe-test-driven-dev`、review dispatch、`ahe-bug-patterns`、`ahe-regression-gate`、`ahe-completion-gate`、`ahe-finalize` 会沿用同一 worktree 上下文，而不是在质量链中途退回仓库根目录
- 这些字段属于 AHE pack-local workflow 语义，不是平台共享 contract 的保留关键字

共享规则入口见：

- `ahe-coding-skills/docs/ahe-worktree-isolation.md`
- `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md`
- `ahe-coding-skills/templates/task-progress-template.md`

## AHE workflow skills（`ahe-*`）

工作流类能力以 **扁平** 目录 `ahe-coding-skills/ahe-*` 维护。每个目录一个 skill，入口仍为该目录下的 `SKILL.md`。

当前工作区已包含的 workflow 成员包括：

- `ahe-coding-skills/ahe-specify/`、`ahe-coding-skills/ahe-design/`、`ahe-coding-skills/ahe-tasks/` — 主链产出
- `ahe-coding-skills/ahe-spec-review/`、`ahe-coding-skills/ahe-design-review/`、`ahe-coding-skills/ahe-tasks-review/` — 上游评审
- `ahe-coding-skills/ahe-test-driven-dev/`、`ahe-coding-skills/ahe-hotfix/`、`ahe-coding-skills/ahe-increment/`、`ahe-coding-skills/ahe-finalize/` — 执行与支线闭环
- `ahe-coding-skills/ahe-bug-patterns/`、`ahe-coding-skills/ahe-test-review/`、`ahe-coding-skills/ahe-code-review/`、`ahe-coding-skills/ahe-traceability-review/`、`ahe-coding-skills/ahe-regression-gate/`、`ahe-coding-skills/ahe-completion-gate/` — 质量与门禁

查阅时：

- 新会话、命令入口或 family discovery 优先从 `ahe-coding-skills/using-ahe-workflow/SKILL.md` 开始
- 需要 authoritative runtime routing 或恢复编排时，从 `ahe-coding-skills/ahe-workflow-router/SKILL.md` 开始
- 已进入某个具体 workflow 节点时，从对应目录的 `SKILL.md` 开始
- 与任务进度、task queue、评审、验证配套的文档骨架见 `ahe-coding-skills/templates/`（如 `task-progress-template.md`、`task-board-template.md`、`review-record-template.md`、`verification-record-template.md`）

## 新增 skill 时的建议

1. 先明确 skill 只解决一个清晰问题。
2. 入口统一放在 `ahe-coding-skills/<skill-name>/SKILL.md`；workflow 族优先使用 `ahe-*` 前缀并与现有家族命名一致。
3. 大段参考资料、模板和案例放到同目录下的 `references/`。
4. 文档中的路径始终引用当前仓库真实存在的位置。
5. 如果需要校验或打包，使用 `.cursor/skills/skill-creator/` 下的脚本，而不是在本目录重复造工具。

## 命名与路径约定

- **Workflow 族**：使用 `ahe-coding-skills/ahe-*`。
- **旧结构**：不要引用已移除路径；若文档中仍出现，应改为当前扁平 `ahe-coding-skills/ahe-*` 或真实存在的路径。
