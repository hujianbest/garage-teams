# Gemini CLI 工具映射

技能使用 Claude Code 的工具名。在技能里遇到下列名称时，请改用你平台上的等价能力：

| 技能中的名称 | Gemini CLI 等价 |
|-----------------|----------------------|
| `Read`（读文件） | `read_file` |
| `Write`（建文件） | `write_file` |
| `Edit`（改文件） | `replace` |
| `Bash`（执行命令） | `run_shell_command` |
| `Grep`（搜文件内容） | `grep_search` |
| `Glob`（按名搜文件） | `glob` |
| `TodoWrite`（任务跟踪） | `write_todos` |
| `Skill` 工具（调用技能） | `activate_skill` |
| `WebSearch` | `google_web_search` |
| `WebFetch` | `web_fetch` |
| `Task` 工具（派发子代理） | 无等价能力 — Gemini CLI 不支持子代理 |

## 无子代理支持

Gemini CLI 没有与 Claude Code `Task` 工具对应的能力。依赖子代理派发的技能（`subagent-driven-development`、`dispatching-parallel-agents`）会退化为通过 `executing-plans` 在单会话中执行。

## Gemini CLI 额外工具

下列工具在 Gemini CLI 中可用，但没有 Claude Code 对应项：

| 工具 | 用途 |
|------|---------|
| `list_directory` | 列出文件与子目录 |
| `save_memory` | 将事实持久化到 GEMINI.md 跨会话保留 |
| `ask_user` | 向用户请求结构化输入 |
| `tracker_create_task` | 丰富任务管理（创建、更新、列表、可视化） |
| `enter_plan_mode` / `exit_plan_mode` | 在改动前切换到只读调研模式 |
