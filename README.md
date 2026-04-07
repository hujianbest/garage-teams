# awesome-harness-engineering (AHE)

`awesome-harness-engineering`，简称 `ahe`，是一个面向个人使用的 harness engineering 工作台。它用于沉淀可复用的 agent 资产、工作约定、模板和参考分析；工作流类能力以 **AHE workflow skills** 的形式维护在扁平目录 `skills/ahe-*` 下，见 `skills/README.md`。

## AHE workflow 入口

- 新会话默认先走 `skills/using-ahe-workflow/SKILL.md`。
- 若当前属于 runtime 恢复编排、阶段判断、profile 判断或 evidence 冲突，再交给 `skills/ahe-workflow-starter/SKILL.md`。
- 只有当前节点、前置工件和批准状态都已经明确时，才 direct invoke 某个具体 `ahe-*` skill。

## 仓库结构

| 路径 | 作用 |
| --- | --- |
| `README.md` | 仓库总览与使用入口 |
| `AGENTS.md` | 仓库级 agent 工作约定 |
| `docs/` | 长文分析、设计说明和研究笔记 |
| `skills/` | 仓库内自有 skills（含 `ahe-*` 工作流 skill 家族）与相关设计规则 |
| `templates/` | 可复用的 Markdown 模板 |
| `agents/` | 预留给角色化 agent 说明或提示词 |
| `rules/` | 预留给常驻规则 |
| `hooks/` | 预留给 hooks 设计与辅助脚本 |
| `.cursor/skills/skill-creator/` | 技能校验、打包、评测辅助脚本 |

`agents/`、`rules/`、`hooks/` 当前还是轻量骨架目录，可按后续需要逐步填充。

## 使用方式

1. 优先从 `README.md` 和 `AGENTS.md` 了解仓库定位与规则。
2. 需要进入 AHE workflow 时，先读 `docs/ahe-workflow-entrypoints.md`，再从 `skills/using-ahe-workflow/SKILL.md` 进入。
3. 若当前属于 runtime 恢复编排、阶段判断、profile 判断或 evidence 冲突，再交给 `skills/ahe-workflow-starter/SKILL.md`。
4. 需要查看参考材料时，进入 `docs/`。
5. 需要维护仓库自有 skill 时，进入 `skills/`：工作流类从 `skills/ahe-*` 各目录的 `SKILL.md` 入手；其他 skill 同样使用 `skills/<skill-name>/SKILL.md` 约定。
6. 需要复用文档骨架时，进入 `templates/`。
7. 需要做 skill 校验、打包或评测时，以 `.cursor/skills/skill-creator/` 为工作目录执行脚本。

## 当前约束

- 以当前实际目录结构为准；引用 workflow 能力时使用 `skills/ahe-*` 和仓库中真实存在的路径。
- 这个仓库没有业务应用构建流程、数据库或 CI 流水线。
- 仓库中的大多数内容是 Markdown 资产；变更时优先保持路径清晰、引用准确、内容可复用。

## 可用验证

若修改的是仓库内或本地挂载的 Cursor skill，可在 `.cursor/skills/skill-creator/` 下运行这些脚本：

- `python -m scripts.quick_validate <skill-dir>`
- `python -m scripts.package_skill <skill-dir> [output-dir]`
- `python -m scripts.aggregate_benchmark <benchmark-dir>`
- `python -m scripts.generate_report <json-input> [-o output.html]`

依赖 `claude` CLI 的评测脚本在当前环境下通常不可用，这是预期限制。