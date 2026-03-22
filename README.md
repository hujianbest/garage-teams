# Awesome Harness Engineering

面向 **Agent Harness Engineering**（智能体配套工程）的精选资源库：把大模型 Agent 可靠地接入真实工作流所需的 **技能（Skills）**、**工具桥（MCP）**、**质量纪律（TDD）** 与 **评测迭代（Skill 工程化）** 放在同一处，便于复制、组合与持续演进。

「Harness」在这里指：**为 Agent 设计上下文边界、工具接口、验证方式与反馈闭环** 的一整套工程实践，而不是某个单一框架。

## 本仓库提供什么

| 维度 | 说明 |
|------|------|
| **Skills** | 可安装到 Cursor 等环境的技能包：每个目录自包含，入口一般为 `SKILL.md`，常配有脚本与参考文档。 |
| **MCP** | 将外部系统暴露为模型可调用的工具时的模式、示例与检查项。 |
| **质量与迭代** | 测试驱动习惯、技能描述与评测流程，降低「能跑但不可信」的风险。 |

## 目录结构

```
awesome-harness-engineering/
├── README.md                 # 本说明
├── AGENTS.md                 # 给自动化 Agent 的仓库内操作约定
├── daily-skills/             # 技能包集合（主资产）：docx / xlsx / pptx / pdf / mcp-builder / skill-creator / test-driven-development 等
├── playbooks/                # 可复用的 Harness 流程说明、检查清单、评审模板（按需补充）
├── templates/                # 新技能、MCP 服务等的起步骨架（按需补充）
└── .cursor/skills/           # 已在仓库内接入的 Cursor 技能（例如 skill-creator）
```

## 技能包索引（`daily-skills/`）

| 目录 | 用途 |
|------|------|
| [daily-skills/docx](daily-skills/docx) | Word（.docx）创建、编辑、审阅与 XML 级操作 |
| [daily-skills/xlsx](daily-skills/xlsx) | Excel（.xlsx / .xlsm 等）读写、建模与表格规范 |
| [daily-skills/pptx](daily-skills/pptx) | PowerPoint（.pptx）创建、编辑与内容提取 |
| [daily-skills/pdf](daily-skills/pdf) | PDF 合并、拆分、表单、OCR 等处理流程 |
| [daily-skills/mcp-builder](daily-skills/mcp-builder) | 使用 Python（FastMCP）或 Node/TypeScript 搭建 MCP 服务 |
| [daily-skills/skill-creator](daily-skills/skill-creator) | 编写新技能、迭代与评估技能效果 |
| [daily-skills/test-driven-development](daily-skills/test-driven-development) | 测试驱动开发（先写失败测试再实现） |

## 使用方式

- **在 Cursor 中使用技能**：将 `daily-skills/<技能名>/`（或 `.cursor/skills/` 下已接入的副本）放到 Cursor 配置的 skills 路径（例如用户级 `~/.cursor/skills-cursor/` 或团队约定目录），使 Agent 能加载对应 `SKILL.md`。
- **深入细节**：打开对应目录下的 `SKILL.md`；Office 与 PDF 类技能通常带有 `scripts/`、`LICENSE.txt` 等，复制、分发或商用前请阅读各目录许可证。
- **扩展本仓库**：新增流程文档可放在 `playbooks/`；新技能/MCP 脚手架可放在 `templates/`（或直接在 `daily-skills/` 下新增自包含目录）。

## 协作原则

- 保持**单技能目录自包含**，避免隐式跨目录依赖。
- 修改技能 frontmatter 中的 `description` 会显著影响触发准确度，可与 `skill-creator` 中的评测流程配合迭代。
- 尊重各子目录的 **LICENSE.txt**；未附带许可证的文档默认遵循仓库整体开源约定（若有 `LICENSE` 根文件则以根文件为准）。

欢迎通过 Issue / PR 贡献技能改进、Playbook 与模板；目标是让 **Harness** 可教、可测、可复用。
