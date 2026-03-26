# SDD Eval 样例包

这个目录提供一组可直接手工演练的前置工件，用来配合：

- `workflow-skills/sdd-skills-eval-prompts.md`
- `.cursor/skills/sdd-workflow-starter/evals/evals.json`

目标不是验证业务实现，而是验证 SDD skills 的触发与路由是否正确。

## 目录说明

- `01-new-requirement/`
  空项目起步场景。故意不放 approved spec、design、task plan。
- `02-approved-spec-no-design/`
  已有 approved spec，但还没有 design，应该路由到 `sdd-work-design`。
- `03-approved-plan-ready-implement/`
  spec、design、task plan 都已批准，应该路由到 `sdd-work-implement`。
- `04-change-request/`
  主链工件已存在，且有 `change-request.json`，应该路由到 `sdd-work-increment`。
- `05-hotfix/`
  主链工件已存在，且有 `hotfix-request.json`，应该路由到 `sdd-work-hotfix`。

## 使用方法

1. 打开某个场景目录，确认前置工件存在
2. 使用该场景 README 中提供的用户 prompt
3. 观察是否先命中 `sdd-workflow-starter`
4. 记录是否被正确路由到期望下游 skill

## 评估建议

建议每次只跑一个场景，避免多个信号文件同时存在导致路由噪音。

如需记录结果，可配合 `workflow-skills/sdd-skills-eval-prompts.md` 末尾的记录模板一起使用。
