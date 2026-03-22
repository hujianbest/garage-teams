# Awesome Harness Engineering — Agent 指引

## 仓库定位

这是 **Agent Harness Engineering** 资源库：以可安装 **Skills**、**MCP** 实践、**TDD** 与 **技能评测** 为主，不是单一业务应用。主资产在 `daily-skills/<技能名>/`，入口一般为 `SKILL.md`。项目内已接入的 Cursor 技能可能在 `.cursor/skills/`。

## 工作方式

1. **任务映射到资产**：用户提到 Word / Excel / PPT / PDF、MCP 开发、编写或评测技能、TDD 等主题时，先打开对应目录下的 `SKILL.md`（或 `.cursor/skills/` 中的副本），再执行具体操作。
2. **始终从入口读起**：除非用户指定文件，否则从该技能的 `SKILL.md` 开始，再按需阅读子文档、`reference/`、`scripts/`。
3. **尊重许可证**：`docx`、`xlsx`、`pptx`、`pdf`、`mcp-builder` 等目录常含 `LICENSE.txt`；复制、分发或商用前以各目录许可证为准。
4. **控制改动范围**：只修改用户点名的技能、文档或目录；不要为「统一整理」而批量改写无关技能内容。
5. **Harness 扩展目录**：`playbooks/` 用于流程与清单，`templates/` 用于可复用脚手架；若为空则不必臆造内容，除非用户要求撰写。

## 路径速查

| 路径 | 用途 |
|------|------|
| `daily-skills/docx/` | .docx 文档 |
| `daily-skills/xlsx/` | 电子表格 |
| `daily-skills/pptx/` | 演示文稿 |
| `daily-skills/pdf/` | PDF 处理 |
| `daily-skills/mcp-builder/` | MCP 服务端开发 |
| `daily-skills/skill-creator/` | 技能的创建与评估 |
| `daily-skills/test-driven-development/` | TDD 流程 |
| `.cursor/skills/` | 仓库内 Cursor 已链接的技能 |
| `playbooks/` | Harness 流程与检查清单（按需） |
| `templates/` | 新项目/新技能模板（按需） |

人类可读的总览与协作说明见根目录 [README.md](README.md)。
