# AHE SE Skills

`ahe-se-skills/` 用于存放面向需求分析、方案收敛和 SE 调研场景的独立 skill 资产。

它与 `ahe-coding-skills/` 的关系是：

- `ahe-coding-skills/`：承载 AHE workflow family 及其相关设计规则
- `ahe-se-skills/`：承载独立的 `se-*` 分析 workflow，不属于 `ahe-workflow-router` 的 canonical 节点族

## 当前目录

- `ahe-se-skills/se-analysis-workflow/` — 独立入口，负责在 discovery / research / design pack 之间选择起点
- `ahe-se-skills/se-discovery/` — 采访用户、归一化术语、收敛问题定义
- `ahe-se-skills/se-research-and-options/` — 做仓库调研、外部研究和方案矩阵
- `ahe-se-skills/se-design-pack/` — 输出 analysis pack、solution pack、接口设计、时序图、DFX、AR 分解和工作量估算

## 共享参考

- `ahe-se-skills/se-analysis-workflow/references/` — 访谈清单、输出模板、DFX / AR / 估算口径和示例

## 使用约定

- `se-*` 是独立 workflow，不属于 `ahe-workflow-router` 管理的 canonical `ahe-*` 节点
- 默认从 `ahe-se-skills/se-analysis-workflow/SKILL.md` 进入
- 默认产物落到 `docs/analysis/` 与 `docs/designs/`
- 使用时不要把 `se-*` 名称写入 AHE canonical `Next Action Or Recommended Skill`
- 子 agent 提示文档仍可放在仓库根的 `agents/` 目录
