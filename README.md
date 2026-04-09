# awesome-harness-engineering (AHE)

`awesome-harness-engineering`，简称 `ahe`，是一个面向个人使用的 harness engineering 工作台，用于沉淀可复用的 agent 资产、workflow skills、模板、规则草案和研究文档。

这是一个 Markdown-first 仓库，没有业务应用构建链路。AHE workflow family 采用扁平 `ahe-coding-skills/ahe-*` 目录组织，每个 skill 的权威入口都是对应目录下的 `SKILL.md`。

## 先看哪里

1. 初次进入仓库时，先读 `README.md` 和 `AGENTS.md`。
2. 需要进入 AHE workflow 时，先读 `ahe-coding-skills/docs/ahe-workflow-entrypoints.md`，再进入 `ahe-coding-skills/using-ahe-workflow/SKILL.md`。
3. 若当前属于 runtime 恢复编排、阶段判断、profile 判断或证据冲突，再进入 `ahe-coding-skills/ahe-workflow-router/SKILL.md`。（旧文档或旧 handoff 若仍使用 **legacy 合并路由** 旧名称，按 `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md` 的读时归一化规则，等同当前 router 语义。）
4. 需要理解 progress、evidence、review verdict 和记录格式时，读 `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md`。
5. 需要维护 AHE workflow skill 时，先读 `ahe-coding-skills/README.md`；需要维护独立 SE 分析 skill 时，先读 `ahe-se-skills/README.md`，再进入目标目录下的 `SKILL.md`。
6. 需要复用 AHE workflow 模板时，进入 `ahe-coding-skills/templates/`；其他通用模板仍在 `templates/`。
7. 需要做 skill 校验、打包或评测时，以 `.cursor/skills/skill-creator/` 为工作目录执行脚本。

## 默认入口规则

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
| `ahe-coding-skills/` | 仓库内自有 skills（含 `ahe-*` workflow family）与相关设计规则 |
| `ahe-se-skills/` | 独立的 `se-*` 分析 workflow skills |
| `ahe-coding-skills/docs/` | 直接服务 live workflow skills 的共享文档 |
| `ahe-coding-skills/templates/` | 直接服务 live workflow skills 的模板 |
| `templates/` | 其他可复用的 Markdown 模板 |
| `agents/` | 角色化 agent 说明、提示词与可复用子 agent 合同 |
| `rules/` | 预留给常驻规则 |
| `hooks/` | 预留给 hooks 设计与辅助脚本 |
| `.cursor/skills/skill-creator/` | skill 校验、打包、评测辅助脚本 |

`rules/`、`hooks/` 当前仍以轻量骨架为主；`agents/` 目录现已开始承载可复用子 agent 提示文档。

## AHE Workflow Family

| 类别 | Skills | 作用 |
| --- | --- | --- |
| Public Entry | `using-ahe-workflow` | 新会话入口、命令入口与 family discovery |
| Orchestrator | `ahe-workflow-router` | 当前 runtime router、恢复编排、路由与阶段判断；旧资料中的 legacy 别名读法见 `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md` |
| Authoring | `ahe-specify`、`ahe-design`、`ahe-tasks` | 产出主链规格、设计和任务工件 |
| Upstream Review | `ahe-spec-review`、`ahe-design-review`、`ahe-tasks-review` | 评审上游主工件并给出结构化结论 |
| Implementation And Branches | `ahe-test-driven-dev`、`ahe-hotfix`、`ahe-increment`、`ahe-finalize` | 实现、支线分析与收尾闭环 |
| Quality And Gates | `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate` | 缺陷模式排查、质量评审、回归与完成门禁 |

完整 AHE workflow skill 目录说明见 `ahe-coding-skills/README.md`；独立 SE analysis skill 目录说明见 `ahe-se-skills/README.md`。

## Standalone SE Analysis Workflow

除 `ahe-*` 主链外，仓库现在还包含一套独立的 `se-*` 分析 workflow，用于帮助对系统不熟的新手 SE 做方案分析、需求拆解和多方案收敛。

- `ahe-se-skills/se-analysis-workflow/`：公开入口，负责判断从访谈、调研还是正式收敛起步
- `ahe-se-skills/se-discovery/`：通过采访和术语归一化收敛问题定义
- `ahe-se-skills/se-research-and-options/`：做仓库调研、外部研究和候选方案比较
- `ahe-se-skills/se-design-pack/`：输出 analysis pack、solution pack、接口设计、时序图、DFX、AR 分解和参考代码量估算
- `ahe-se-skills/se-analysis-workflow/references/`：共享访谈清单、输出模板、DFX / AR / 估算口径和示例
- `agents/`：供这套 workflow 复用的仓库调研、网络调研和方案挑战子 agent 提示

这套 `se-*` workflow 默认把分析结果写到：

- `docs/analysis/`
- `docs/designs/`

注意：

- 它是独立 workflow，不属于 `ahe-workflow-router` 管理的 canonical `ahe-*` 节点族
- 使用时不要把 `se-*` 名称写入 AHE canonical `Next Action Or Recommended Skill`

## 关键文档

- `docs/README.md`：`docs/` 分组索引与维护约定入口。
- `ahe-coding-skills/docs/ahe-workflow-entrypoints.md`：定义何时先走 `ahe-coding-skills/using-ahe-workflow/SKILL.md`，何时交给 `ahe-workflow-router`，以及何时允许 direct invoke。
- `ahe-coding-skills/docs/ahe-workflow-shared-conventions.md`：集中定义 progress schema、`Execution Mode`、fresh evidence、verdict、severity 和记录表达方式。
- `ahe-coding-skills/docs/ahe-command-entrypoints.md`：定义 `/ahe-spec`、`/ahe-build`、`/ahe-review`、`/ahe-closeout` 这类 docs-only command contract。
- `docs/designs/ahe-platform-first-multi-agent-implementation-design.md`：描述平台优先 multi-agent runtime 的实现设计，以及 AHE 作为首个 coding pack 的接入方案。
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
