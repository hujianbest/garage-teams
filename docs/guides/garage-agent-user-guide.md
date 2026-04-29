# garage-agent 使用手册

- 定位: 面向 solo creator 的本地优先 Agent 能力之家
- 项目名: `garage-agent`
- CLI 命令: `garage`
- 日期: 2026-04-29

---

## garage-agent 是什么

`garage-agent` 是一个本地优先的 Agent 能力之家，用来把你的 Agent 能力留在自己的仓库里：skills、agents、知识、经验、上下文交接和可分发 packs 都以文件形式沉淀，随着项目一起迁移。

它不是 SaaS，不是单一宿主外壳，也不是大而全 AI 框架。它服务的核心场景是：你在 Claude Code、Cursor、OpenCode 等宿主之间切换时，不丢掉已经积累的能力。

### 核心原则

- **数据归你**：`.garage/`、`packs/`、docs 都是普通文件，可读、可审计、可提交。
- **宿主可换**：当前支持 Claude Code、Cursor、OpenCode，核心能力不绑定单一宿主。
- **渐进增强**：第一天可以只用 packs；积累变多后再打开 memory、sync、skill mining。
- **人始终掌舵**：删除、发布、共享、自动提炼都需要显式确认。

### 名称说明

- 对外项目名是 `garage-agent`。
- 命令行入口是 `garage`。
- Python package 和源码路径仍保留 `garage-os` / `src/garage_os/` 作为兼容实现细节，普通使用者不需要把它理解成产品概念。

---

## 已完成能力速览

| 能力 | 用户可见入口 |
|---|---|
| 初始化本地能力仓库 | `garage init`, `garage status` |
| 分发内置 skills / agents | `garage init --hosts claude,cursor,opencode` |
| 项目级 / 用户级安装 | `--scope project`, `--scope user`, `claude:user,cursor:project` |
| 运行单个 skill | `garage run <skill-name>` |
| 知识与经验 CRUD | `garage knowledge ...`, `garage experience ...` |
| 记忆候选审批 | `garage memory review ...` |
| 主动召回与知识图谱 | `garage recommend`, `garage knowledge link`, `garage knowledge graph` |
| 宿主上下文同步 | `garage sync` |
| 宿主会话回流 | `garage session import --from claude --all` |
| pack 生命周期 | `garage pack install/ls/update/uninstall/publish` |
| 知识脱敏导出 | `garage knowledge export --anonymize` |
| pattern → skill 建议 | `garage skill suggest`, `garage skill promote` |
| 历史 workflow 路径建议 | `garage recall workflow` |

---

## 快速开始

### 环境要求

- Python 3.11+
- `uv`
- Git
- 至少一个 Agent 宿主：Claude Code、Cursor 或 OpenCode

### 安装

```bash
git clone https://github.com/hujianbest/garage-agent.git
cd garage-agent
uv pip install -e .
```

安装后可以使用 `garage` 命令。

### 初始化一个项目

```bash
# 只创建 .garage/
garage init

# 创建 .garage/ 并把内置 packs 装到宿主目录
garage init --hosts claude,cursor --yes

# 装到用户级目录，方便跨项目复用
garage init --hosts all --scope user
```

`garage init` 是幂等的。重复执行不会破坏用户修改过的 Garage-owned 文件；本地改过的文件会提示 `Skipped <path> (locally modified, pass --force to overwrite)`，需要覆盖时显式传 `--force`。

### 查看状态

```bash
garage status
garage status --path /path/to/project
```

`garage status` 会显示 sessions、knowledge、experience、skill mining、workflow recall 等摘要。

### `.garage/` 目录

```text
.garage/
├── config/
│   ├── platform.json
│   └── host-installer.json
├── contracts/
├── knowledge/
│   ├── decisions/
│   ├── patterns/
│   ├── solutions/
│   └── style/
├── experience/
│   └── records/
├── memory/
├── skill-suggestions/
├── workflow-recall/
└── sessions/
    ├── active/
    └── archived/
```

建议把 `.garage/` 提交到 Git。活跃 session 是否提交可按项目习惯决定。

---

## Packs、Skills 和 Agents

本节也是 Pack & Host Installer 的用户入口：`garage-agent` 把 `packs/` 中的 skills / agents 安装到各宿主原生目录。

`packs/` 是可分发能力的 single source of truth。当前内置 packs：

| Pack | 内容 |
|---|---|
| `packs/garage/` | 入门 skills + `code-review-agent` / `blog-writing-agent` |
| `packs/coding/` | HarnessFlow / AHE 工程 workflow skills，含 `hf-workflow-router` |
| `packs/writing/` | 博客、人味改写、分析、PPT 等写作 skills |
| `packs/search/` | `ai-weekly` 信息聚合 skill |

### 安装到宿主

```bash
# project scope：写到当前项目 .claude/.cursor/.opencode
garage init --hosts claude,cursor

# user scope：写到用户目录，跨项目复用
garage init --hosts all --scope user

# 每个宿主独立 scope
garage init --hosts claude:user,cursor:project
```

| Host | project scope | user scope |
|---|---|---|
| Claude Code | `.claude/skills/`, `.claude/agents/` | `~/.claude/skills/`, `~/.claude/agents/` |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| OpenCode | `.opencode/skills/`, `.opencode/agent/` | `~/.config/opencode/skills/`, `~/.config/opencode/agent/` |

安装清单写在 `.garage/config/host-installer.json`，记录 host、scope、pack、文件路径与 content hash。

### Pack Lifecycle

```bash
# 从 git URL 安装第三方 pack
garage pack install https://github.com/<user>/<pack>.git

# 查看本地 packs
garage pack ls

# 从 source_url 更新
garage pack update <pack-id> --yes

# 从 packs/ 和 Garage-owned 宿主文件中移除
garage pack uninstall <pack-id> --yes

# 发布到 git remote；默认 sensitive scan + force-push 提示
garage pack publish <pack-id> --to https://github.com/<you>/<pack>.git --yes
```

破坏性或共享性操作都需要交互确认或显式 flag。先看影响范围时用 `--dry-run`。

---

## Knowledge 与 Experience

Knowledge 是可复用信息，当前支持四类：

| 类型 | 用途 | 路径 |
|---|---|---|
| `decision` | 架构 / 产品 / 技术决策 | `.garage/knowledge/decisions/` |
| `pattern` | 可复用模式 | `.garage/knowledge/patterns/` |
| `solution` | 问题解法 | `.garage/knowledge/solutions/` |
| `style` | 编码、写作、review 偏好 | `.garage/knowledge/style/` |

Experience 是一次任务的结构化经验记录，放在 `.garage/experience/records/`。

### Knowledge authoring (CLI)

```bash
# cli:knowledge-add
garage knowledge add --type decision --topic "Use file-first storage" --content "..."

# cli:knowledge-edit
garage knowledge edit <knowledge-id> --content "..."

garage knowledge show <knowledge-id>
garage knowledge delete <knowledge-id> --yes
garage knowledge list
garage knowledge search "JWT auth"
```

### Experience CLI

```bash
# cli:experience-add
garage experience add \
  --task-type implement \
  --skill-ids hf-specify,hf-design \
  --domain platform \
  --problem-domain cli-design \
  --outcome success

garage experience show <record-id>
garage experience delete <record-id> --yes
```

### Knowledge 脱敏导出

```bash
# 导出到 ~/.garage/exports/knowledge-<ts>.tar.gz
garage knowledge export --anonymize

# 只看规则命中统计
garage knowledge export --anonymize --dry-run

# 指定输出目录
garage knowledge export --anonymize --output ./my-export
```

导出保留 front matter，只脱敏正文。内置规则覆盖 password、api_key、secret、token、private_key、email、sha1_hash；可在 `~/.garage/anonymize-patterns.txt` 添加本地正则。

---

## Memory Review

当 session import 或 archive 触发 memory extraction 后，候选会进入 `.garage/memory/candidates/`，需要用户 review。

```bash
garage memory review <batch-id>
garage memory review <batch-id> --action accept --candidate-id <id>
garage memory review <batch-id> --action abandon --candidate-id <id>
garage memory review <batch-id> --action accept --candidate-id <id> --strategy abandon
```

两条 abandon 路径不同：

| 路径 | 语义 |
|---|---|
| `--action abandon` | 主动放弃候选，without publication attempt |
| `--action accept --strategy abandon` | 尝试发布但 due to conflict 放弃，记录 `conflict_strategy=abandon` |

一句话：不想要这条候选，用 `--action abandon`；想保留“我接受过但因冲突不发布”的审计轨迹，用 `--strategy abandon`。

---

## Active recall and knowledge graph

### `garage recommend`

```bash
garage recommend "JWT auth"
garage recommend "review workflow" --json
```

`recommend` 从 knowledge + experience 中拉取相关内容，适合在开始任务前找历史上下文。

### `garage knowledge link`

```bash
# cli:knowledge-link
garage knowledge link --from <knowledge-id-a> --to <knowledge-id-b> --kind supports
```

### `garage knowledge graph`

```bash
garage knowledge graph --id <knowledge-id>
```

输出会包含：

- `Outgoing edges:`
- `Incoming edges:`

---

## Sync 与 Session Import

### `garage sync`

```bash
# 默认 sync 到所有 host 的 project scope
garage sync

# 指定 host 和 scope
garage sync --hosts claude --scope user

# per-host scope
garage sync --hosts claude:user,cursor:project

# marker 内内容被用户改过时，显式覆盖
garage sync --hosts claude --force
```

写入位置：

| Host | project | user |
|---|---|---|
| Claude Code | `<cwd>/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| Cursor | `<cwd>/.cursor/rules/garage-context.mdc` | `~/.cursor/rules/garage-context.mdc` |
| OpenCode | `<cwd>/.opencode/AGENTS.md` | `~/.config/opencode/AGENTS.md` |

Garage 写入内容用 marker 包住，marker 外用户内容保持不变。

### `garage session import`

```bash
# 交互选择 Claude Code 对话
garage session import --from claude-code

# 非交互导入全部
garage session import --from claude --all
```

Cursor history reader 仍未稳定，`garage session import --from cursor` 当前是 deferred 路径。

---

## Skill Mining

Skill Mining 是使用飞轮的 push 端：系统从 `KnowledgeStore` + `ExperienceIndex` 中扫描重复 `(problem_domain, tag-bucket)`，达到阈值后建议把 pattern → skill。

```bash
# 查看 proposed 建议
garage skill suggest

# 手动全量重扫；默认阈值 N=5，可临时降低
garage skill suggest --rescan --threshold 3

# 查看证据链和 SKILL.md preview
garage skill suggest --id sg-20260426-ddac9d

# 查看历史状态或清理 expired
garage skill suggest --status all
garage skill suggest --purge-expired --yes
```

```bash
# 只预览，不写文件
garage skill promote sg-20260426-ddac9d --dry-run

# 写入 packs/<target-pack>/skills/<suggested-name>/SKILL.md
garage skill promote sg-20260426-ddac9d --target-pack garage --yes

# 拒绝建议
garage skill promote sg-20260426-ddac9d --reject --yes
```

`skill_mining.hook_enabled=false` 可以关闭自动 hook；手动 `garage skill suggest --rescan` 仍可显式重扫。用户级偏好放在 `~/.garage/skill-mining-config.json`。

promote 不会自动改 `pack.json`，也不会自动运行 `garage run hf-test-driven-dev`。是否把草稿变成正式 skill，仍由用户决定。

---

## Workflow Recall

Workflow Recall 让 `hf-workflow-router` 在 step 3.5 查询历史经验：当 `ExperienceIndex` 里同 `(task_type, problem_domain)` 的记录足够多时，输出过去常见 skill path，作为 advisory 放进 handoff。router 的权威决策权不变。

```bash
# 按任务类型查
garage recall workflow --task-type implement

# 按问题域查
garage recall workflow --problem-domain cli-design

# 从某个 skill 后截取后续路径
garage recall workflow --skill-id hf-design

# 给 router / 自动化消费
garage recall workflow --problem-domain cli-design --json

# 强制重建 cache
garage recall workflow --rebuild-cache --problem-domain cli-design
```

`workflow_recall.enabled=false` 可以关闭自动 cache invalidation hook；手动 `garage recall workflow --rebuild-cache` 仍可显式重算。

`garage recommend` 推内容，`garage recall workflow` 推路径。

---

## 配置

`.garage/config/platform.json` 常见字段：

```json
{
  "schema_version": 1,
  "platform_name": "garage-agent",
  "stage": 1,
  "storage_mode": "artifact-first",
  "host_type": "claude-code",
  "session_timeout_seconds": 7200,
  "max_active_sessions": 1,
  "knowledge_indexing": "manual",
  "memory": {
    "extraction_enabled": false,
    "recommendation_enabled": false
  },
  "skill_mining": {
    "hook_enabled": true
  },
  "workflow_recall": {
    "enabled": true
  }
}
```

---

## 常见问题

### `.garage/` 要提交吗？

建议提交。它是你的能力资产。若不想提交活跃 session，可只忽略 `.garage/sessions/active/`。

### 我只想用 skills，不想用 memory，可以吗？

可以。只运行 `garage init --hosts ...` 安装 packs 即可。memory extraction、skill mining、workflow recall 都是渐进增强。

### Cursor / Claude / OpenCode 必须都装吗？

不用。`--hosts` 可以只选一个，也可以用 `--hosts none` 只初始化 `.garage/`。

### 为什么还有 `garage-os` 这个包名？

这是兼容保留的 Python 包名和源码路径，不是当前产品概念。用户入口以 `garage-agent` 和 `garage` CLI 为准。

---

## 相关文档

- [README](../../README.zh-CN.md) — 项目总览
- [packs 目录说明](../../packs/README.md) — pack 结构和宿主安装契约
- [Garage 愿景宣言](../soul/manifesto.md)
- [Garage 用户契约](../soul/user-pact.md)
- [Garage 成长策略](../soul/growth-strategy.md)
- [Skill 写作原则](../principles/skill-anatomy.md)
- [Release Notes](../../RELEASE_NOTES.md)
