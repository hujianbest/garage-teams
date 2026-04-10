# awesome-harness-engineering (AHE)

`awesome-harness-engineering`，简称 `ahe`，是一个面向个人使用的 harness engineering 工作台，用于沉淀可复用的 agent 资产、workflow skills、模板、规则草案和研究文档。

这是一个 Markdown-first 仓库，没有业务应用构建链路。AHE workflow family 采用扁平 `ahe-coding-skills/ahe-*` 目录组织，每个 skill 的权威入口都是对应目录下的 `SKILL.md`。

## 先看哪里

1. 初次进入仓库时，先读 `README.md` 和 `AGENTS.md`。
2. 如果问题还停留在“这个产品值不值得做、为什么不吸引人、先打哪个 wedge、先做什么低成本验证”，先读 `ahe-product-skills/README.md`，再进入 `ahe-product-skills/using-ahe-product-workflow/SKILL.md`。
3. 需要进入 AHE workflow 时，先读 `ahe-coding-skills/docs/ahe-workflow-entrypoints.md`，再进入 `ahe-coding-skills/using-ahe-workflow/SKILL.md`。
4. 若当前属于 runtime 恢复编排、阶段判断、profile 判断或证据冲突，再进入 `ahe-coding-skills/ahe-workflow-router/SKILL.md`。（旧文档或旧 handoff 若仍使用 **legacy 合并路由** 旧名称，按 `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md` 的读时归一化规则，等同当前 router 语义。）
5. 需要理解 progress、evidence、review verdict 和记录格式时，读 `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md`。
6. 需要维护某个 skill 时，先读 `ahe-coding-skills/README.md`；若维护的是产品洞察 family，则先读 `ahe-product-skills/README.md`。
7. 需要复用 AHE workflow 模板时，进入 `ahe-coding-skills/templates/`；需要复用产品洞察模板时，进入 `ahe-product-skills/templates/`；其他通用模板仍在 `templates/`。
8. 需要做 skill 校验、打包或评测时，以 `.cursor/skills/skill-creator/` 为工作目录执行脚本。

## 默认入口规则

- 若当前还在判断产品价值、产品吸引力、目标用户、机会优先级、差异化概念或低成本验证，默认先走 `ahe-product-skills/using-ahe-product-workflow`，不要直接进入 `ahe-coding-skills`。
- 新会话默认先走 `using-ahe-workflow`。
- 若当前需要 authoritative route / stage / profile 判断、review / gate 后恢复编排，或 evidence 冲突，则交给 `ahe-workflow-router`。
- 若用户显式要求 `auto` / 自动执行，把它视为 `Execution Mode` 偏好，一并交给 entry layer 或 router 处理；不要把它当成新的 profile。
- 只有在当前节点、前置工件和批准状态都已经明确时，才 direct invoke 某个具体 `ahe-*` skill。
- review / gate skill 只处理本节点职责，不替代主链编排。

更完整的入口规则见 `ahe-coding-skills/docs/ahe-workflow-entrypoints.md`。

## 仓库结构

| 路径 | 作用 |
| --- | --- |
| `README.md` | 仓库总览与使用入口 |
| `AGENTS.md` | 仓库级 agent 工作约定 |
| `docs/` | 按 `analysis/`、`architecture/`、`designs/`、`guides/`、`plans/`、`references/` 分组的长文文档 |
| `docs/insights/` | `ahe-product-skills` 默认落盘的上游产品洞察工件 |
| `ahe-coding-skills/` | 仓库内自有 skills（含 `ahe-*` workflow family）与相关设计规则 |
| `ahe-coding-skills/docs/` | 直接服务 live workflow skills 的共享文档 |
| `ahe-coding-skills/templates/` | 直接服务 live workflow skills 的模板 |
| `ahe-product-skills/` | 上游产品洞察 skills，用于 framing、research、opportunity、concept、probe 和 bridge |
| `ahe-product-skills/docs/` | 直接服务产品洞察 workflow 的共享文档 |
| `ahe-product-skills/templates/` | 直接服务产品洞察 workflow 的模板 |
| `templates/` | 其他可复用的 Markdown 模板 |
| `agents/` | 预留给角色化 agent 说明或提示词 |
| `rules/` | 预留给常驻规则 |
| `hooks/` | 预留给 hooks 设计与辅助脚本 |
| `.cursor/skills/skill-creator/` | skill 校验、打包、评测辅助脚本 |

`agents/`、`rules/`、`hooks/` 当前仍是轻量骨架目录，可按后续需要逐步填充。

## AHE Workflow Family

| 类别 | Skills | 作用 |
| --- | --- | --- |
| Public Entry | `using-ahe-workflow` | 新会话入口、命令入口与 family discovery |
| Orchestrator | `ahe-workflow-router` | 当前 runtime router、恢复编排、路由与阶段判断；旧资料中的 legacy 别名读法见 `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md` |
| Authoring | `ahe-specify`、`ahe-design`、`ahe-tasks` | 产出主链规格、设计和任务工件 |
| Upstream Review | `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review` | 评审上游主工件并给出结构化结论 |
| Implementation And Branches | `ahe-test-driven-dev`、`ahe-hotfix`、`ahe-increment`、`ahe-finalize` | 实现、支线分析与收尾闭环 |
| Quality And Gates | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate` | 缺陷模式排查、质量评审、回归与完成门禁 |

完整 skill 目录说明见 `ahe-coding-skills/README.md`。

## AHE Product Skills

| 类别 | Skills | 作用 |
| --- | --- | --- |
| Public Entry | `using-ahe-product-workflow` | 判断当前应该先从 framing、research、opportunity、concept、probe 还是 bridge 起步 |
| Framing | `ahe-outcome-framing` | 把模糊 idea 重写成更锋利的 outcome、用户、替代品和非目标 |
| Research | `ahe-insight-mining` | 从 web、GitHub、社区和本地材料里提取信号，并默认通过多 agent 讨论 / PK 收敛 `insight-pack` |
| Convergence | `ahe-opportunity-mapping`、`ahe-concept-shaping` | 选优先机会、生成多个 concept direction，并收敛 wedge |
| Validation | `ahe-assumption-probes` | 把最危险未知项转成低成本 probe 和 kill criteria |
| Bridge | `ahe-spec-bridge` | 把上游洞察和验证结果压缩成 `ahe-coding-skills` 可消费输入 |

如果你只知道“先别写代码，先帮我把产品想清楚”，默认入口就是 `ahe-product-skills/using-ahe-product-workflow`。更细的使用说明和提示词案例见 `ahe-product-skills/README.md`。

## 关键文档

- `docs/README.md`：`docs/` 分组索引与维护约定入口。
- `docs/architecture/ahe-platform-first-multi-agent-architecture.md`：定义当前主架构文档采用的平台优先控制面与共享契约边界。
- `docs/plans/ahe-agent-platform-roadmap-and-adr-backlog.md`：定义长期能力路线图、阶段退出条件与需要逐步冻结的 ADR 清单。
- `ahe-coding-skills/docs/ahe-workflow-entrypoints.md`：定义何时先走 `ahe-coding-skills/using-ahe-workflow/SKILL.md`，何时交给 `ahe-workflow-router`，以及何时允许 direct invoke。
- `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md`：集中定义 progress schema、`Execution Mode`、fresh evidence、verdict、severity 和记录表达方式。
- `ahe-coding-skills/docs/ahe-command-entrypoints.md`：定义 `/ahe-spec`、`/ahe-build`、`/ahe-review`、`/ahe-closeout` 这类 docs-only command contract。
- `docs/architecture/ahe-workflow-skill-anatomy.md`：定义 workflow skill 的目标态 anatomy。
- `docs/guides/ahe-workflow-externalization-guide.md`：说明外部仓库采用 AHE workflow family 时的最小能力面。
- `docs/guides/ahe-path-mapping-guide.md`：说明默认逻辑工件如何映射到实际仓库路径。
- `docs/plans/ahe-review-subagent-optimization-plan.md`：整理 review 动作独立 subagent 化的优化方案。

## 常用模板

- `templates/AGENTS-template.md`
- `ahe-coding-skills/templates/task-progress-template.md`
- `ahe-coding-skills/templates/task-board-template.md`
- `ahe-coding-skills/templates/review-record-template.md`
- `ahe-coding-skills/templates/verification-record-template.md`

## 当前约束

- 以当前实际目录结构为准；引用 workflow 能力时使用 `ahe-coding-skills/ahe-*` 和仓库中真实存在的路径。
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
