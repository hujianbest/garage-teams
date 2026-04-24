# `packs/garage/` — Garage Getting-Started Pack

本 pack 是 Garage 自带的 **getting-started 三件套**，用于：

1. **验证 packs/ 目录契约**：让 `pack_discovery` 模块有可消费的真实 fixture（F007 落下）。
2. **验证 host installer 端到端管道**：让 `garage init --hosts ...` 有可物化的源（F007 落下）。
3. **作为下游用户的 'getting started' 入口三件套**：用户首次跑 `garage init` 后立刻得到 (a) 一个能跑通的 sample skill (b) 发现新 skill 的 meta 工具 (c) 写新 skill 的 SOP（F008 cycle 扩容）。

## Pack 概况

| 字段 | 值 |
|---|---|
| `pack_id` | `garage` |
| `version` | `0.2.0`（F007 0.1.0 → F008 扩容到 3 skill） |
| `schema_version` | `1` |
| `skills` | 3 |
| `agents` | 1 |

## Getting-Started 三件套

### Skills

| id | 文件 | 用途 | 来源 cycle |
|---|---|---|---|
| `garage-hello` | [`skills/garage-hello/SKILL.md`](skills/garage-hello/SKILL.md) | 最小欢迎 skill，演示 SKILL.md 形态 + 验证安装管道 | F007 |
| `find-skills` | [`skills/find-skills/SKILL.md`](skills/find-skills/SKILL.md) | 帮用户发现并安装新 skill 的 meta-skill（"how do I do X / find a skill for X"）| F008 |
| `writing-skills` | [`skills/writing-skills/SKILL.md`](skills/writing-skills/SKILL.md) | 写新 skill 时的 SOP（含 anthropic best-practices / persuasion principles / testing skills with subagents 三份 reference + render-graphs.js）| F008 |

### Agents

| id | 文件 | 用途 |
|---|---|---|
| `garage-sample-agent` | [`agents/garage-sample-agent.md`](agents/garage-sample-agent.md) | 最小 sample agent，演示 agent.md 形态（无 front matter，覆盖 marker.inject 容错路径）|

## Pack 元数据

详见 [`pack.json`](pack.json)。

```json
{
  "schema_version": 1,
  "pack_id": "garage",
  "version": "0.2.0",
  "skills": ["find-skills", "garage-hello", "writing-skills"],
  "agents": ["garage-sample-agent"]
}
```

## NFR-801 文件级豁免（spec NFR-801 + design ADR-D8-9）

`writing-skills` 子目录内有两个 meta/教学文件含 `~/.claude/skills/` 字面值，按 design ADR-D8-9 豁免清单整文件保留：

- `skills/writing-skills/anthropic-best-practices.md`：Anthropic 官方文档 link `/en/docs/claude-code/skills` 是引用 URL 的一部分（参考资料，1 行命中）
- `skills/writing-skills/examples/CLAUDE_MD_TESTING.md`：writing-skills skill 的核心**测试场景文档**（pressure scenarios for testing CLAUDE.md），其讨论对象就是 Claude Code 中 skills 目录的发现机制；改动会破坏教学意图（14 行命中）

SKILL.md 主体仍受 NFR-801 强约束（`writing-skills/SKILL.md` line 12 的 `~/.claude/skills` + `~/.agents/skills/` 已被宿主中性化替换为 "refer to your host's documentation for the canonical skills directory path"）。

## 与下游用户的关系

下游用户 `garage init --hosts claude` 后，立刻看到本 pack 的 3 个 skill + 1 个 agent。`garage-hello` 帮你确认安装成功；`find-skills` 帮你浏览/发现可装的更多 skill；`writing-skills` 帮你写自己的 skill。

## 与 F007/F008 的关系

- F007 (PR #18) 落下 `garage-hello` + `garage-sample-agent`，验证 packs 目录契约 + host installer 端到端管道
- F008 (PR #22) 在不改 D7 管道的前提下扩容到 3 skill + 11 family asset（packs/coding/）+ 4 skill（packs/writing/），把 `.agents/skills/` 下 28 个 source SKILL.md 物化为可分发；`garage` pack 内追加 `find-skills` + `writing-skills` 两个 meta-skill，与 `garage-hello` 比邻
