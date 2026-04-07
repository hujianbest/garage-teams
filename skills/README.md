# AHE Skills

`skills/` 用于存放 `awesome-harness-engineering`（`ahe`）仓库自己的可复用 skill 资产，以及直接服务于这些 skill 的设计规则。

## 目录约定

- `skills/README.md`：本目录总览
- `skills/design_rules.md`：skill 与 harness 资产的设计原则
- `skills/<skill-name>/SKILL.md`：单个 skill 的入口文件
- `skills/<skill-name>/references/`：该 skill 的补充说明、模板或参考资料

## Public entry skill

除 `ahe-*` workflow 节点外，AHE 还包含一层公开入口：

- `skills/using-ahe-workflow/` — AHE workflow family 的公开入口、命令入口解释层和 discovery shell；它帮助判断应 direct invoke 哪个节点，或何时交给当前 runtime router。

## Runtime router and alias

- `skills/ahe-workflow-router/` — AHE workflow family 的 canonical runtime router，负责 stage / profile / branch / review recovery authority。
- `skills/ahe-workflow-starter/` — 兼容旧入口、旧 handoff 与旧文档的 compatibility alias；新的 runtime 语义优先写 `ahe-workflow-router`。

## AHE workflow skills（`ahe-*`）

工作流类能力以 **扁平** 目录 `skills/ahe-*` 维护。每个目录一个 skill，入口仍为该目录下的 `SKILL.md`。

当前工作区已包含的 workflow 成员包括：

- `skills/ahe-specify/`、`skills/ahe-design/`、`skills/ahe-tasks/` — 主链产出
- `skills/ahe-spec-review/`、`skills/ahe-design-review/`、`skills/ahe-tasks-review/` — 上游评审
- `skills/ahe-test-driven-dev/`、`skills/ahe-hotfix/`、`skills/ahe-increment/`、`skills/ahe-finalize/` — 执行与支线闭环
- `skills/ahe-bug-patterns/`、`skills/ahe-test-review/`、`skills/ahe-code-review/`、`skills/ahe-traceability-review/`、`skills/ahe-regression-gate/`、`skills/ahe-completion-gate/` — 质量与门禁

查阅时：

- 新会话、命令入口或 family discovery 优先从 `skills/using-ahe-workflow/SKILL.md` 开始
- 需要 authoritative runtime routing 或恢复编排时，从 `skills/ahe-workflow-router/SKILL.md` 开始
- 已进入某个具体 workflow 节点时，从对应目录的 `SKILL.md` 开始
- 与任务进度、评审、验证配套的文档骨架见 `templates/`（如 `task-progress-template.md`、`review-record-template.md`、`verification-record-template.md`）

## 新增 skill 时的建议

1. 先明确 skill 只解决一个清晰问题。
2. 入口统一放在 `skills/<skill-name>/SKILL.md`；workflow 族优先使用 `ahe-*` 前缀并与现有家族命名一致。
3. 大段参考资料、模板和案例放到同目录下的 `references/`。
4. 文档中的路径始终引用当前仓库真实存在的位置。
5. 如果需要校验或打包，使用 `.cursor/skills/skill-creator/` 下的脚本，而不是在本目录重复造工具。

## 命名与路径约定

- **Workflow 族**：使用 `skills/ahe-*`。
- **旧结构**：不要引用已移除路径；若文档中仍出现，应改为当前扁平 `skills/ahe-*` 或真实存在的路径。
