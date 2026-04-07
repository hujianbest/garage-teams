# awesome-harness-engineering (AHE) — Agent 指引

## 仓库定位

这是 `awesome-harness-engineering`（`ahe`）个人工作台，用于维护可复用的 harness 资产、skills、模板、规则草案和研究文档。工作流类 skill 以 **AHE workflow skills** 形式放在扁平目录 `skills/ahe-*` 下；其他自有 skill 仍按需放在 `skills/<skill-name>/`。

## 工作方式

1. **先看当前入口**：默认从 `README.md`、`AGENTS.md` 或用户明确指定的文件开始，而不是假设存在历史入口。
2. **以实际目录为准**：只引用当前仓库中真实存在的路径。不要使用已废弃目录名或已删除的旧路径；workflow 能力统一通过 `skills/ahe-*` 下的 `SKILL.md` 查阅。
3. **从局部入口继续深入**：查看 skill 时从 `skills/<skill-name>/SKILL.md` 开始（workflow 族为 `skills/ahe-*/SKILL.md`）；查看模板时从 `templates/` 开始；查看长文资料时从 `docs/` 开始。
4. **控制改动范围**：只修改当前任务涉及的目录与文档，不为了“统一整理”去批量改写无关分析资料。
5. **保持资产可复用**：模板保持通用、说明保持简洁、路径保持稳定；新增或引用 workflow 约定时统一使用 `ahe-*` 命名。

## 路径速查

| 路径 | 用途 |
| --- | --- |
| `README.md` | 仓库总览与使用入口 |
| `AGENTS.md` | 仓库级 agent 约定 |
| `docs/` | 分析、设计说明与研究记录 |
| `skills/` | 仓库自有 skills（含 `ahe-*` workflow 家族）与设计规则 |
| `templates/` | 通用模板 |
| `agents/` | 角色化 agent 说明占位目录 |
| `rules/` | 常驻规则占位目录 |
| `hooks/` | hooks 说明或辅助脚本占位目录 |
| `.cursor/skills/skill-creator/` | skill 校验、打包、评测辅助脚本 |

## Cursor / 脚本说明

本仓库主要由 Markdown 资产和少量 Python 辅助脚本组成，没有业务应用构建链路。

### 运行时依赖

- `Python 3.12+`
- `PyYAML`（按需安装）

### 常用脚本

以下脚本都应在 `.cursor/skills/skill-creator/` 下执行：

| 命令 | 用途 |
| --- | --- |
| `python -m scripts.quick_validate <skill-dir>` | 校验 `SKILL.md` frontmatter |
| `python -m scripts.package_skill <skill-dir> [output-dir]` | 打包 skill |
| `python -m scripts.aggregate_benchmark <benchmark-dir>` | 汇总 benchmark |
| `python -m scripts.generate_report <json-input> [-o output.html]` | 生成 HTML 报告 |
| `python -m scripts.run_eval ...` | 触发评测，依赖 `claude` CLI |
| `python -m scripts.run_loop ...` | 评测改进循环，依赖 `claude` CLI |

### 注意事项

- `references/` 类型目录若存在，默认视为参考资料，不强行安装或运行其依赖。
- 本仓库当前没有统一 lint、CI 或自动化测试套件；核心验证方式是路径检查和上述 skill 脚本。
