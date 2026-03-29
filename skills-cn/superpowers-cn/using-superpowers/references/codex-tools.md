# Codex 工具映射

技能使用 Claude Code 的工具名。在技能里遇到下列名称时，请改用你平台上的等价能力：

| 技能中的名称 | Codex 等价 |
|-----------------|------------------|
| `Task` 工具（派发子代理） | `spawn_agent` |
| 多次 `Task` 调用（并行） | 多次 `spawn_agent` 调用 |
| Task 返回结果 | `wait` |
| Task 自动结束 | `close_agent` 以释放槽位 |
| `TodoWrite`（任务跟踪） | `update_plan` |
| `Skill` 工具（调用技能） | 技能原生加载 — 直接遵循说明即可 |
| `Read`、`Write`、`Edit`（文件） | 使用你原生的文件工具 |
| `Bash`（执行命令） | 使用你原生的 shell 工具 |

## 子代理派发需要多代理支持

在 Codex 配置（`~/.codex/config.toml`）中加入：

```toml
[features]
multi_agent = true
```

这样会启用 `spawn_agent`、`wait`、`close_agent`，供 `dispatching-parallel-agents`、`subagent-driven-development` 等技能使用。
