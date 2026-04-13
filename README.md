# AHE Skills Repository

面向团队开源的 AHE skills 仓库。

本仓库只维护 **skills 资产本身**（工作流技能、共享文档、模板、评测样例），不承担 runtime、平台核心代码或业务实现。

## 仓库定位

- **目标**：沉淀可复用的工程协作技能，支持规范化的需求、设计、任务拆解、实现、评审与收口流程。
- **形态**：纯 skills repo，按 skill 目录组织，入口统一为 `SKILL.md`。
- **使用方式**：可作为团队内部统一参考，也可按需复制到本地 agent skill 目录中使用。

## 目录结构

- `skills/`：主技能目录
  - `skills/<skill-name>/SKILL.md`：单个 skill 的主入口
  - `skills/<skill-name>/references/`：该 skill 的补充资料、模板或长文档
  - `skills/<skill-name>/evals/`：评测样例与回归数据
- `skills/docs/`：跨 skill 的共享约定与说明
- `skills/templates/`：通用模板（任务板、评审记录、验证记录等）
- `skills/design_rules.md`：skills 设计原则
- `ahe-workflow-skill-anatomy.md`：AHE workflow skill 结构说明

## 快速开始

1. 先阅读 `skills/README.md` 了解技能全景与导航入口。
2. 新会话或 workflow 入口场景，优先查看 `skills/using-ahe-workflow/SKILL.md`。
3. 需要路由编排与恢复控制，查看 `skills/ahe-workflow-router/SKILL.md`。
4. 需要通用规范与模板时，使用 `skills/docs/` 与 `skills/templates/`。

## 当前技能族（节选）

- 上游主链：`ahe-specify`、`ahe-design`、`ahe-tasks`
- 上游评审：`ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review`
- 执行闭环：`ahe-test-driven-dev`、`ahe-hotfix`、`ahe-increment`、`ahe-finalize`
- 质量门禁：`ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate`

## 常见使用场景

- **新需求从 0 到上线收口**：从 `skills/ahe-specify/SKILL.md` 起草规格，经 `skills/ahe-spec-review/SKILL.md`、`skills/ahe-design/SKILL.md`、`skills/ahe-design-review/SKILL.md`、`skills/ahe-tasks/SKILL.md`、`skills/ahe-tasks-review/SKILL.md` 进入 `skills/ahe-test-driven-dev/SKILL.md`，再经过质量门禁与 `skills/ahe-finalize/SKILL.md` 完成收尾。
- **会话恢复或阶段不确定**：当“现在该做什么”不清楚、证据链有冲突、或 review/gate 刚完成需要继续编排时，先用 `skills/using-ahe-workflow/SKILL.md` 和 `skills/ahe-workflow-router/SKILL.md` 做 authoritative routing。
- **单任务受控实现**：任务计划已批准后，统一从 `skills/ahe-test-driven-dev/SKILL.md` 进入实现，遵循 fail-first 与 fresh evidence 回写，并通过 handoff 返回 router 选择下一步。
- **紧急缺陷修复（Hotfix）**：线上问题需要快速修复时，由 `skills/ahe-hotfix/SKILL.md` 先完成复现、根因收敛与最小修复边界，再回流到 `skills/ahe-test-driven-dev/SKILL.md` 执行受控实现和验证。
- **需求中途变化（Increment）**：范围、验收或约束发生变化时，先用 `skills/ahe-increment/SKILL.md` 做变更影响与工件同步，再安全回到主链，避免直接带着失效设计继续编码。
- **质量把关与发布前决策**：实现完成后依次经过 `skills/ahe-bug-patterns/SKILL.md`、`skills/ahe-test-review/SKILL.md`、`skills/ahe-code-review/SKILL.md`、`skills/ahe-traceability-review/SKILL.md`、`skills/ahe-regression-gate/SKILL.md`、`skills/ahe-completion-gate/SKILL.md`，据 fresh evidence 决定返工还是进入 `skills/ahe-finalize/SKILL.md`。

