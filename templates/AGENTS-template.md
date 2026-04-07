# AGENTS.md 模板

下面是一份适用于个人 harness 仓库的 `AGENTS.md` 样板，可作为 `awesome-harness-engineering` 风格项目的起点。

---

# <仓库名称> — Agent 指引

## 仓库定位

这是一个用于维护 `<主要资产类型>` 的个人 harness 工作台。请以当前仓库实际目录结构为准；若使用 AHE 风格 workflow skills，工作流类能力位于扁平目录 `skills/ahe-*`（入口为各目录下 `SKILL.md`）。

## 工作方式

1. 先从 `README.md`、`AGENTS.md` 或用户指定入口开始。
2. 只引用仓库中真实存在的路径。
3. skill 从 `skills/<skill-name>/SKILL.md` 开始阅读；workflow 族从 `skills/ahe-*/SKILL.md` 开始。
4. 模板统一放在 `templates/`，保持通用和可复用。
5. 长文说明、分析或设计记录统一放在 `docs/`。

## 路径速查

| 路径 | 用途 |
| --- | --- |
| `README.md` | 仓库总览 |
| `AGENTS.md` | 仓库级约定 |
| `docs/` | 分析、说明和设计记录 |
| `skills/` | 仓库自有 skills（含 `ahe-*` workflow 家族时） |
| `templates/` | 通用模板 |
| `agents/` | 角色化 agent 说明 |
| `rules/` | 常驻规则 |
| `hooks/` | hooks 说明或脚本 |

## 验证方式

- 如果仓库主要是文档资产，优先检查路径、交叉引用和模板可用性。
- 如果仓库包含 skill 工具链，补充这里的校验、打包或评测命令。

## 注意事项

- 不要保留指向历史目录的失效引用；workflow 使用 `skills/ahe-*`。
- 不要为了统一格式而重写无关资料。
- 保持说明短而稳定，避免把 `AGENTS.md` 写成冗长流程手册。
