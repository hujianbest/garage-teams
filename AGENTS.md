# Awesome Harness Engineering — Agent 指引

## 仓库定位

这是 **Agent Harness Engineering** 资源库：以可安装 **Skills**、**MCP** 实践、**TDD** 与 **技能评测** 为主，不是单一业务应用。主资产在 `daily-skills/<技能名>/`，入口一般为 `SKILL.md`。项目内已接入的 Cursor 技能可能在 `.cursor/skills/`。

## 工作方式

1. **任务映射到资产**：用户提到 Word / Excel / PPT / PDF、MCP 开发、编写或评测技能、TDD 等主题时，先打开对应目录下的 `SKILL.md`（或 `.cursor/skills/` 中的副本），再执行具体操作。
2. **始终从入口读起**：除非用户指定文件，否则从该技能的 `SKILL.md` 开始，再按需阅读子文档、`reference/`、`scripts/`。
3. **尊重许可证**：`docx`、`xlsx`、`pptx`、`pdf`、`mcp-builder` 等目录常含 `LICENSE.txt`；复制、分发或商用前以各目录许可证为准。
4. **控制改动范围**：只修改用户点名的技能、文档或目录；不要为「统一整理」而批量改写无关技能内容。
5. **Harness 扩展目录**：`playbooks/` 用于流程与清单，`templates/` 用于可复用脚手架；若为空则不必臆造内容，除非用户要求撰写。

## MDC Workflow 扩展协议

当仓库或下游项目采用 `skills/mdc-workflow/` 时，`AGENTS.md` 也是该工作流的**唯一扩展入口**。

1. **先读 `AGENTS.md`，再读具体 skill**：进入任一 `mdc-*` skill 前，先查找这里是否声明了 `mdc-workflow` 相关约定。
2. **由 `AGENTS.md` 统一承载映射与规范**：包括工件路径映射、审批状态别名、真人确认等价证据、模板覆盖路径、编码规范、设计规范、测试规范、例外规则与多产品命名空间。
3. **skill 本体只保留流程内核**：`skills/mdc-workflow/` 负责阶段顺序、门禁、证据优先级与交接格式，不再额外引入平行的映射契约。
4. **未声明时才回落默认值**：若 `AGENTS.md` 没有给出某项映射或规范，`mdc-workflow` 才使用默认路径、默认模板和默认状态词。
5. **避免双源配置**：新方案下不要再新增任何与 `AGENTS.md` 并行的映射源；`mdc-workflow` 的路径映射、审批别名、模板覆盖和团队规范都应直接写在 `AGENTS.md` 中。

推荐至少在 `AGENTS.md` 中覆盖以下 `mdc-workflow` 信息：

- 工件路径：spec、design、tasks、reviews、verification、progress、release notes
- 审批与评审状态：approved、pass、revise、blocked 的项目别名
- 真人确认证据：人工批注、审批记录、PR 审批、工单状态等可接受来源
- 模板覆盖：spec/design/tasks/review/verification 模板位置
- 团队规范：coding/design/testing 约束、常用命令、mock 边界、覆盖率门槛、允许例外

## 路径速查

| 路径 | 用途 |
|------|------|
| `daily-skills/docx/` | .docx 文档 |
| `daily-skills/xlsx/` | 电子表格 |
| `daily-skills/pptx/` | 演示文稿 |
| `daily-skills/pdf/` | PDF 处理 |
| `daily-skills/mcp-builder/` | MCP 服务端开发 |
| `daily-skills/skill-creator/` | 技能的创建与评估 |
| `daily-skills/tdd-cpp/` | C++ TDD（GoogleTest + CMake） |
| `daily-skills/test-driven-development/` | TDD 流程（通用） |
| `skills/mdc-workflow/` | 面向软件交付的强约束 workflow skills |
| `.cursor/skills/` | 仓库内 Cursor 已链接的技能 |
| `playbooks/` | Harness 流程与检查清单（按需） |
| `templates/` | 新项目/新技能模板（按需） |

人类可读的总览与协作说明见根目录 [README.md](README.md)。
