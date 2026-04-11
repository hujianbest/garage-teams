# AHE Coding Skills

`packs/coding/skills/` 是当前仓库里 `Coding Pack` 的来源技能面，承接 AHE coding workflow family 的 skill、共享文档、模板与设计规则。

它在 phase 1 的定位是：

- `Garage` 的 coding 来源资产
- `Coding Pack` 的参考 workflow 面
- pack-local docs、templates 与设计规则的维护入口

它不是完整的 `Garage Core`，也不是未来 runtime 的全部实现。

## 目录约定

- `packs/coding/skills/README.md`：本目录总览
- `packs/coding/skills/docs/`：AHE coding workflow 的共享文档
- `packs/coding/skills/templates/`：AHE coding workflow 的共享模板
- `packs/coding/skills/design_rules.md`：skill 与 harness 资产的设计原则
- `packs/coding/skills/<skill-name>/SKILL.md`：单个 skill 的入口文件
- `packs/coding/skills/<skill-name>/references/`：该 skill 的补充说明、模板或参考资料

## 先看哪里

- 新会话入口、命令入口或 family discovery，先读 `packs/coding/skills/using-ahe-workflow/SKILL.md`
- 需要 authoritative runtime routing 或恢复编排时，读 `packs/coding/skills/ahe-workflow-router/SKILL.md`
- 需要共享规则时，读 `packs/coding/skills/docs/`
- 需要模板时，读 `packs/coding/skills/templates/`

## 当前 workflow family

当前主要成员包括：

- `ahe-specify`、`ahe-design`、`ahe-tasks`：上游主链产出
- `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review`：上游评审
- `ahe-test-driven-dev`、`ahe-hotfix`、`ahe-increment`、`ahe-finalize`：执行与支线闭环
- `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate`：质量与门禁

## 相关 supporting surfaces

- `packs/coding/skills/docs/ahe-workflow-entrypoints.md`
- `packs/coding/skills/docs/ahe-workflow-shared-conventions.md`
- `packs/coding/skills/docs/ahe-command-entrypoints.md`
- `packs/coding/skills/docs/ahe-worktree-isolation.md`
- `packs/coding/skills/templates/task-progress-template.md`
- `packs/coding/skills/templates/task-board-template.md`
- `packs/coding/skills/templates/review-record-template.md`
- `packs/coding/skills/templates/verification-record-template.md`

## 维护约定

1. workflow skill 继续使用 `ahe-*` 命名族，但路径引用必须使用当前真实路径。
2. 每个 skill 入口统一放在 `packs/coding/skills/<skill-name>/SKILL.md`。
3. 长案例、模板说明和补充材料放到各 skill 的 `references/` 或共享 `docs/` / `templates/` 中。
4. 需要校验、打包或评测时，使用 `.agents/skills/skill-creator/` 下的脚本，而不是在本目录重复造工具。
