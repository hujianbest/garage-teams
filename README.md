# awesome-harness-engineering (AHE)

`awesome-harness-engineering`，简称 `ahe`，是一个面向个人使用的 harness engineering 工作台，用于沉淀可复用的 agent 资产、workflow skills、模板、规则草案和研究文档。

这是一个 Markdown-first 仓库，没有业务应用构建链路。AHE workflow family 采用扁平 `skills/ahe-*` 目录组织，每个 skill 的权威入口都是对应目录下的 `SKILL.md`。

## 先看哪里

1. 初次进入仓库时，先读 `README.md` 和 `AGENTS.md`。
2. 需要进入 AHE workflow 时，先读 `docs/ahe-workflow-entrypoints.md`，再进入 `skills/using-ahe-workflow/SKILL.md`。
3. 若当前属于 runtime 恢复编排、阶段判断、profile 判断或证据冲突，再进入 `skills/ahe-workflow-router/SKILL.md`。（旧文档或旧 handoff 若仍使用 **legacy 合并路由** 旧名称，按 `docs/ahe-workflow-shared-conventions.md` 的读时归一化规则，等同当前 router 语义。）
4. 需要理解 progress、evidence、review verdict 和记录格式时，读 `docs/ahe-workflow-shared-conventions.md`。
5. 需要维护某个 skill 时，先读 `skills/README.md`，再进入目标 `skills/<skill-name>/SKILL.md`。
6. 需要复用文档骨架时，进入 `templates/`。
7. 需要做 skill 校验、打包或评测时，以 `.cursor/skills/skill-creator/` 为工作目录执行脚本。

## 默认入口规则

- 新会话默认先走 `using-ahe-workflow`。
- 若当前需要 authoritative route / stage / profile 判断、review / gate 后恢复编排，或 evidence 冲突，则交给 `ahe-workflow-router`。
- 只有在当前节点、前置工件和批准状态都已经明确时，才 direct invoke 某个具体 `ahe-*` skill。
- review / gate skill 只处理本节点职责，不替代主链编排。

更完整的入口规则见 `docs/ahe-workflow-entrypoints.md`。

## 仓库结构

| 路径 | 作用 |
| --- | --- |
| `README.md` | 仓库总览与使用入口 |
| `AGENTS.md` | 仓库级 agent 工作约定 |
| `docs/` | 长文分析、设计说明、研究笔记与 workflow 设计文档 |
| `skills/` | 仓库内自有 skills（含 `ahe-*` workflow family）与相关设计规则 |
| `templates/` | 可复用的 Markdown 模板 |
| `agents/` | 预留给角色化 agent 说明或提示词 |
| `rules/` | 预留给常驻规则 |
| `hooks/` | 预留给 hooks 设计与辅助脚本 |
| `.cursor/skills/skill-creator/` | skill 校验、打包、评测辅助脚本 |

`agents/`、`rules/`、`hooks/` 当前仍是轻量骨架目录，可按后续需要逐步填充。

## AHE Workflow Family

| 类别 | Skills | 作用 |
| --- | --- | --- |
| Public Entry | `using-ahe-workflow` | 新会话入口、命令入口与 family discovery |
| Orchestrator | `ahe-workflow-router` | 当前 runtime router、恢复编排、路由与阶段判断；旧资料中的 legacy 别名读法见 `docs/ahe-workflow-shared-conventions.md` |
| Authoring | `ahe-specify`、`ahe-design`、`ahe-tasks` | 产出主链规格、设计和任务工件 |
| Upstream Review | `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review` | 评审上游主工件并给出结构化结论 |
| Implementation And Branches | `ahe-test-driven-dev`、`ahe-hotfix`、`ahe-increment`、`ahe-finalize` | 实现、支线分析与收尾闭环 |
| Quality And Gates | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate` | 缺陷模式排查、质量评审、回归与完成门禁 |

完整 skill 目录说明见 `skills/README.md`。

## 关键文档

- `docs/ahe-workflow-entrypoints.md`：定义何时先走 `skills/using-ahe-workflow/SKILL.md`，何时交给 `ahe-workflow-router`，以及何时允许 direct invoke。
- `docs/ahe-workflow-shared-conventions.md`：集中定义 progress schema、fresh evidence、verdict、severity 和记录表达方式。
- `docs/ahe-command-entrypoints.md`：定义 `/ahe-spec`、`/ahe-build`、`/ahe-review`、`/ahe-closeout` 这类 docs-only command contract。
- `docs/ahe-workflow-multi-agent-operating-model-design.md`：描述 AHE 多 agent 运行模型与 coordination 设计。
- `docs/ahe-workflow-skill-anatomy.md`：定义 workflow skill 的目标态 anatomy。
- `docs/ahe-workflow-skill-gap-matrix.md`：评估当前 `ahe-*` family 与目标态 anatomy 的差距与改造优先级。
- `docs/ahe-review-subagent-implementation-checklist.md`：整理 review subagent 化的具体落地清单。

## 常用模板

- `templates/AGENTS-template.md`
- `templates/task-progress-template.md`
- `templates/review-record-template.md`
- `templates/verification-record-template.md`

## 当前约束

- 以当前实际目录结构为准；引用 workflow 能力时使用 `skills/ahe-*` 和仓库中真实存在的路径。
- 这个仓库没有业务应用构建流程、数据库或统一 CI 流水线。
- 仓库中的大多数内容是 Markdown 资产；变更时优先保持路径清晰、引用准确、内容可复用。

## 可用验证

若修改的是仓库内或本地挂载的 Cursor skill，可在 `.cursor/skills/skill-creator/` 下运行这些脚本：

- `python -m scripts.quick_validate <skill-dir>`
- `python -m scripts.package_skill <skill-dir> [output-dir]`
- `python -m scripts.aggregate_benchmark <benchmark-dir>`
- `python -m scripts.generate_report <json-input> [-o output.html]`
- `python -m scripts.run_eval ...`
- `python -m scripts.run_loop ...`

运行这些脚本通常需要 `Python 3.12+`；部分评测命令额外依赖 `claude` CLI，在当前环境下通常不可用，这是预期限制。
