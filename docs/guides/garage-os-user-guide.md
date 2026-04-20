# Garage OS 用户指南

- 定位: 面向独立创作者的 Agent OS 运行时使用手册
- 版本: 0.2.0 (F002 Garage Live)
- 日期: 2026-04-16

---

## Garage OS 是什么

Garage OS 是一个**面向独立创作者（Solo Creator）的 Agent 操作系统运行时**。它的核心使命是：

1. **管理 Agent 工作流**：从创建会话、执行技能到归档结果，完整的工作流生命周期管理
2. **积累项目知识**：将每次工作中的决策、模式、解决方案自动沉淀为可复用的知识
3. **记住执行经验**：记录每次任务执行的过程和结果，让 Agent 越用越聪明
4. **宿主无关**：不绑定任何特定的 AI Agent 宿主（Claude Code、Hermes、Cursor 等），可以随时切换

### 设计理念

- **文件优先（File-first）**：所有数据以文件形式存储在 `.garage/` 目录中，git 可追踪，人类可读
- **零配置启动**：第一天不需要任何配置就能工作
- **渐进增强**：从最简形态开始，按需增加复杂度
- **宿主无关**：核心能力定义在 Garage 层面，宿主只是运行时适配层

---

## 快速开始

### 1. 环境要求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 包管理器
- Git
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)（`claude` 命令可用）

### 2. 安装

```bash
cd /path/to/Garage
uv pip install -e .
```

安装后即可使用 `garage` 命令。

### 3. 初始化项目

```bash
# 在项目目录下初始化 .garage/ 目录结构
garage init

# 幂等操作，重复执行不会报错
garage init
```

### 4. 查看状态

```bash
# 显示 sessions、知识条目、经验记录统计
garage status

# 指定项目路径
garage status --path /path/to/project
```

### 5. 核心目录

首次使用后，`.garage/` 目录结构如下：

```
.garage/
├── config/                 # 配置文件
│   ├── platform.json       # 平台配置
│   └── host-adapter.json   # 宿主适配器配置
├── contracts/              # 接口契约（YAML 格式）
├── knowledge/              # 知识库
│   ├── decisions/          # 决策记录
│   ├── patterns/           # 模式记录
│   └── solutions/          # 解决方案记录
├── experience/             # 经验记录
│   └── records/            # JSON 格式的执行经验
└── sessions/               # 会话数据
    ├── active/             # 活跃会话
    └── archived/           # 归档会话
```

---

## 核心概念

### Session（会话）

**会话**是一次工作流的完整执行实例。每个会话有明确的生命周期：

```
idle → running → paused → running → completed
                 ↓
               failed → （可恢复）
                          ↓
                       archived
```

- 每个会话关联一个 `pack_id`（工作流包）和一个 `topic`（主题）
- 会话状态通过 `StateMachine` 管理，转换有严格约束
- 会话支持**检查点（Checkpoint）**，中断后可恢复执行
- 会话完成后自动归档到 `.garage/sessions/archived/`

### Skill（技能）

**技能**是工作流中的可执行单元。技能通过宿主适配器调用：

- 技能由 `SkillExecutor` 统一调度执行
- 执行过程中自动进行状态转换（`idle` → `running` → `completed`）
- 技能执行失败时，`ErrorHandler` 根据错误类别决定重试或中断
- 技能执行产生的制品（Spec、Design、Tasks、Code 等）通过 `ArtifactBoardSync` 同步

### Knowledge（知识）

**知识**是从工作流中沉淀的可复用信息。Garage OS 支持三种知识类型：

| 类型 | 说明 | 存储位置 |
|------|------|----------|
| **Decision（决策）** | 架构或设计决策及其理由 | `.garage/knowledge/decisions/` |
| **Pattern（模式）** | 可复用的代码模式或工作流模式 | `.garage/knowledge/patterns/` |
| **Solution（解决方案）** | 针对特定问题的解决方案 | `.garage/knowledge/solutions/` |

知识条目使用 **Markdown + YAML Front Matter** 格式存储：

```markdown
---
type: decision
topic: "选择文件系统作为存储后端"
date: 2026-04-16
tags: [storage, architecture]
status: active
version: 1
---

## 决策内容

选择文件系统而非数据库作为存储后端，理由：
- 零配置启动
- Git 可追踪
- 人类可读
```

### Experience（经验）

**经验**是任务执行过程的完整记录，用于未来相似任务的参考：

- 记录任务类型、使用的技术栈、执行时长、复杂度
- 包含经验教训（`lessons_learned`）、陷阱（`pitfalls`）、建议（`recommendations`）
- 经验记录存储在 `.garage/experience/records/`（JSON 格式）
- 通过 `ExperienceIndex` 构建中心索引，支持按条件查询

---

## 使用流程

### 典型工作流

```
1. 创建会话 → 2. 执行技能 → 3. 积累知识 → 4. 归档会话
```

#### 步骤 1：创建会话

当你启动一个新工作流时，`SessionManager` 会创建一个新的会话：

```python
from pathlib import Path
from garage_os.storage import FileStorage
from garage_os.runtime import SessionManager

storage = FileStorage(Path(".garage"))
session_mgr = SessionManager(storage)

# 创建一个新会话
session = session_mgr.create_session(
    pack_id="ahe-coding",
    topic="实现用户认证功能",
    user_goals=["完成登录/注册功能", "支持 JWT 认证"],
    constraints=["不使用外部认证服务"],
)
# session.session_id → "session-20260416-abcd1234"
# session.state → SessionState.IDLE
```

#### 步骤 2：执行技能

会话创建后，通过 `SkillExecutor` 执行具体的技能：

```python
from garage_os.runtime import SkillExecutor
from garage_os.adapter import ClaudeCodeAdapter

adapter = ClaudeCodeAdapter()
executor = SkillExecutor(
    session_manager=session_mgr,
    state_machine=StateMachine(),
    error_handler=ErrorHandler(),
    knowledge_integration=KnowledgeIntegration(storage),
    host_adapter=adapter,
)

# 执行技能
result = executor.execute_skill(
    session_id=session.session_id,
    skill_name="ahe-design",
    params={"topic": "用户认证设计"},
)
# result.success → True
# result.artifacts → [产出的制品列表]
```

#### 步骤 3：积累知识

在工作流执行过程中，重要决策和经验会自动或手动记录到知识库：

```python
from garage_os.knowledge import KnowledgeStore
from garage_os.types import KnowledgeEntry, KnowledgeType

knowledge_store = KnowledgeStore(storage)

# 记录一个决策
entry = KnowledgeEntry(
    id="decision-001",
    type=KnowledgeType.DECISION,
    topic="认证方案选择",
    date=datetime.now(),
    tags=["auth", "jwt", "security"],
    content="选择 JWT 作为认证方案...",
)
knowledge_store.store(entry)
```

#### 步骤 4：归档会话

工作流完成后，会话会被归档：

```python
# 归档会话
session_mgr.archive_session(session.session_id)
# 会话状态: completed → archived
# 数据移动到 .garage/sessions/archived/
```

---

## 常见场景

### 查询历史知识

```python
# 按标签查询知识
entries = knowledge_store.query_by_tag("auth")

# 按类型查询
decisions = knowledge_store.query_by_type(KnowledgeType.DECISION)

# 全文搜索
results = knowledge_store.search("JWT 认证")
```

### 恢复中断的会话

```python
# 从检查点恢复会话
recovery = session_mgr.recover_session(session.session_id)
# recovery.recovery_method → "checkpoint"
# 会话恢复到最近的检查点状态
```

### 记录执行经验

```python
from garage_os.knowledge import ExperienceIndex
from garage_os.types import ExperienceRecord

exp_index = ExperienceIndex(storage)

record = ExperienceRecord(
    record_id="exp-001",
    task_type="feature-implementation",
    skill_ids=["ahe-design", "ahe-code"],
    tech_stack=["Python", "FastAPI", "JWT"],
    domain="web-backend",
    problem_domain="用户认证",
    outcome="success",
    duration_seconds=3600,
    complexity="medium",
    session_id=session.session_id,
    lessons_learned=["JWT 刷新令牌需要考虑并发场景"],
    pitfalls=["不要在 JWT payload 中存储敏感信息"],
)
exp_index.store(record)
```

---

## Memory review — abandon paths

`garage memory review` 提供两条不同的 "abandon" 路径，命名相似但**语义有别**。理解它们对审计候选状态、事后回溯发布行为很关键。

| 用户输入 | 何时使用 | publisher 是否被调用 | confirmation 字段 | stdout 标识符 | 候选最终状态 |
|---------|---------|---------------------|------------------|---------------|-------------|
| `garage memory review <bid> --candidate-id c --action abandon` | **主动放弃**：你看完候选后直接判断"这条不值得发布"，与冲突无关 | 否（CLI 在调 publisher 前就早返回） | `resolution=abandon`、`conflict_strategy=null` | `Candidate '<cid>' abandoned without publication attempt` | `abandoned` |
| `garage memory review <bid> --candidate-id c --action accept --strategy abandon` | **遇冲突放弃**：你本来想发布，但 publisher 检测到与已发布知识有真实冲突，你选择"这次冲突时放弃"，下次同样冲突仍可重试 | 是（publisher 返回 `conflict_strategy=abandon` 早返回） | `resolution=accept`、`conflict_strategy=abandon` | `Candidate '<cid>' abandoned due to conflict with published knowledge` | `abandoned` |

两条路径都把候选置为 `abandoned`，但 confirmation 文件与 stdout 标识符**互不重叠**，可被独立 grep / 解析：

```bash
grep "abandoned without publication attempt" .garage/memory/confirmations/*.json
grep "abandoned due to conflict" .garage/memory/confirmations/*.json
```

如果 `--action accept --strategy abandon` 时 publisher **没有**检测到任何真实冲突，行为退化为正常 accept publish（候选 → `published`，confirmation `resolution=accept`、`conflict_strategy=null`），与 v1 完全一致。

### 一句话怎么选

- 想说"这条候选我不要了"→ `--action abandon`
- 想说"这条候选只在冲突时放弃，我下次还想试"→ `--action accept --strategy abandon`

---

## Knowledge authoring (CLI)

F005 起，`garage` 的 `knowledge` 与 `experience` 子命令支持完整 CRUD，让你不依赖 session 归档与候选提取，直接从终端把一条决策 / 模式 / 解法（或一条经验记录）持久化到 `.garage/knowledge/` 与 `.garage/experience/`。

### Knowledge 子命令

| 命令 | 用途 | 关键参数 |
|------|------|---------|
| `garage knowledge add` | 新增一条知识 | `--type {decision,pattern,solution}`、`--topic`、`--content` 或 `--from-file`、`--tags`、`--id`（可选） |
| `garage knowledge edit` | 修改已存在的知识，自动 `version+=1` | `--type`、`--id`、`--topic` / `--content` / `--from-file` / `--tags` / `--status`（至少传一个） |
| `garage knowledge show` | 精确读取一条知识 | `--type`、`--id` |
| `garage knowledge delete` | 删除一条知识 | `--type`、`--id` |
| `garage knowledge search` | （已有）按文本 / tag / type 搜索 | `query` |
| `garage knowledge list` | （已有）列出全部知识 | — |

### Experience 子命令

| 命令 | 用途 | 关键参数 |
|------|------|---------|
| `garage experience add` | 手动追加一条经验记录 | `--task-type`、`--skill`（可重复）、`--domain`、`--outcome {success,failure,partial}`、`--duration`、`--complexity {low,medium,high}`、`--summary`、可选 `--tech` / `--tags` / `--problem-domain` / `--id` |
| `garage experience show` | 读取单条经验（JSON） | `--id` |
| `garage experience delete` | 删除单条经验，同时清理中央索引 | `--id` |

### 最小示例

```bash
# 新增一条决策
garage knowledge add --type decision \
    --topic "Pick SQLite over Postgres for local index" \
    --tags storage,decision \
    --content "Postgres needs a daemon, violates workspace-first."

# 用文件作为正文
garage knowledge add --type pattern \
    --topic "Front-matter as schema" \
    --from-file pattern-notes.md \
    --tags arch

# 修改 tag（自动 version 递增）
garage knowledge edit --type decision --id <id> --tags storage,decision,sqlite

# 读取
garage knowledge show --type decision --id <id>

# 删除
garage knowledge delete --type pattern --id <id>

# 手动记录一条 spike 经验
garage experience add \
    --task-type spike --skill ahe-design --skill ahe-tasks \
    --domain platform --outcome success --duration 1800 \
    --complexity medium --summary "试出了 SQLite 索引方案"

# 读取单条 experience
garage experience show --id exp-...

# 删除（同时清理 .garage/knowledge/.metadata/index.json 引用）
garage experience delete --id exp-...
```

### ID 与来源标记

- 不传 `--id` 时，CLI 自动生成 `<type>-<YYYYMMDD>-<6 hex chars>`，hash 输入含秒级时间戳；同一秒同一 topic + content 重复 add 会被拒绝（`Entry with id '<id>' already exists`），不会原地覆盖现有 entry。
- 传 `--id custom` 则直接使用。`(type, custom)` 已存在时同样拒绝。
- 通过 CLI 写入的 entry / record 在持久化层带有 `cli:` 命名空间前缀的来源标记：
  - `garage knowledge add` → front matter `source_artifact: cli:knowledge-add`
  - `garage knowledge edit` → 覆盖为 `source_artifact: cli:knowledge-edit`（**不**触动 publisher 路径写入的 `published_from_candidate` 等元数据）
  - `garage experience add` → `record.artifacts[0] = "cli:experience-add"`

可以用 `grep -l "cli:" .garage/knowledge/**/*.md` 一键筛选手工添加路径产出物，与 F003/F004 的候选 → publisher 路径产出物分离审计。

### CLI authoring path 与 candidate→publisher path 的关系

两条路径并列、互不依赖：

- F003/F004 的 `garage memory review` 仍是**自动候选 → 用户确认 → 正式发布**的官方流程
- F005 的 `garage knowledge add` / `experience add` 是**手工 ad-hoc 入库**的旁路
- 两者写入相同的 `.garage/knowledge/` / `.garage/experience/` 目录，但通过 `source_artifact` / `artifacts[0]` 的 `cli:` 前缀可在审计时区分来源

如果你发现自己在 `garage memory review` 之前已经手工 add 了等价 entry，candidate review 时 publisher 的相似度探测会触发常规冲突路径（`coexist` / `supersede` / `abandon`），不会静默覆盖你的手工版本。

---

## Active recall and knowledge graph

F006 起，`garage` CLI 增加了 3 个新子命令，让你**主动**召回积累的知识、把孤立的 entry 连成图：

### `garage recommend <query>` — 主动召回

不依赖 `garage run` 的 skill 执行流程，用户直接 pull 排序后的相关 entry（mixed knowledge + experience）：

```bash
# 基础召回
garage recommend "auth jwt expiry"

# 带过滤
garage recommend "rate limiting" --tag api --domain platform --top 3

# 零结果时给明确兜底文案
garage recommend "anything"
# → No matching knowledge or experience for query: 'anything'
```

输出格式（每条 entry 一个 block）：

```
[DECISION] auth jwt expiry
  ID: decision-20260419-...
  Score: 1.40
  Match: tag:auth, domain:platform
  Source: <session id, if any>
```

每条结果都带 `Match:` 行解释命中理由（与 F003 `RecommendationService` 同样的 `match_reasons` 字段），方便你判断"为什么是这条"。

### `garage knowledge link --from --to [--kind ...]` — 维护知识图边

把一条 entry 与另一条 ID 显式关联：

```bash
# 把 decision A 关联到 decision B（默认 --kind related-decision）
garage knowledge link --from decision-A --to decision-B

# 关联到一个外部 task ID
garage knowledge link --from decision-A --to T005 --kind related-task

# 重复 link 是幂等的（字段去重，但 version 仍 +1，符合 v1.1 不变量）
garage knowledge link --from decision-A --to decision-B
# → Already linked 'decision-A' -> 'decision-B' (related-decision)
```

`--from` 必须是 `.garage/knowledge/` 内已存在的 entry id；`--to` 接受任意字符串（不强制存在性，便于引用 task ID 等外部标识）。`link` 写盘时自动设 `source_artifact = "cli:knowledge-link"`，与 F005 cli: 命名空间一致，可被审计 grep。

### `garage knowledge graph --id` — 1 跳邻居视图

打印一个 entry 节点 + 其全部 1 跳邻居（出边 + 入边）：

```bash
garage knowledge graph --id decision-A
```

```
[DECISION] auth-related architecture decision
ID: decision-A
Outgoing edges:
  -> decision-B (related-decision)
  -> T005 (related-task)
Incoming edges:
  <- pattern-frontmatter (related-decision)
```

- **出边**：`entry.related_decisions` + `entry.related_tasks` 字段直接列出
- **入边**：全库扫描"哪些其他 entry 把本 entry 列为 related"

不持久化反向索引（按 OD-605 接受 N=100 阈值下 O(N) 扫描）。

### `garage memory review` 与 `garage recommend` 的区别

| 命令 | 心智模型 | 何时用 |
|------|---------|------|
| `garage memory review <bid>` | 自动**候选 → 用户确认 → 正式发布** | session 归档触发候选提取后，决定哪些进入正式知识库 |
| `garage recommend <query>` | 已发布知识 / 经验的**主动召回** | 想问"我以前对 X 类问题怎么决策的"，直接 pull |

两者互不影响：`recommend` 是 read-only，`review` 是写入 `.garage/knowledge/` 与 `.garage/memory/confirmations/`。

---

## 配置说明

### 平台配置（`.garage/config/platform.json`）

```json
{
  "schema_version": 1,
  "platform_name": "Garage Agent OS",
  "stage": 1,
  "storage_mode": "artifact-first",
  "host_type": "claude-code",
  "session_timeout_seconds": 7200,
  "max_active_sessions": 1,
  "knowledge_indexing": "manual"
}
```

### 宿主适配器配置（`.garage/config/host-adapter.json`）

```json
{
  "schema_version": 1,
  "host_type": "claude-code",
  "interaction_mode": "file-system",
  "capabilities": {
    "session_state_api": false,
    "file_read_write": true,
    "memory_auto_load": true,
    "subprocess": true
  }
}
```

---

## 常见问题

### Q: `.garage/` 目录需要提交到 Git 吗？

是的。`.garage/` 中的知识、经验和配置都是项目的一部分，应该纳入版本控制。会话数据也可以提交，但活跃会话文件（`.garage/sessions/active/`）可以在 `.gitignore` 中忽略。

### Q: 如何切换宿主环境？

修改 `.garage/config/host-adapter.json` 中的 `host_type` 字段，然后实现对应的 `HostAdapterProtocol`。核心工作流和知识数据不需要任何改动。

### Q: 知识条目太多怎么办？

当知识条目超过 100 个时，`.garage/knowledge/.metadata/index.json` 会自动生成索引。当条目超过 1000 个时，可以启用结构化索引模式。

---

## Pack & Host Installer

Garage 自带的 skills 与 agents 沉淀在仓库的 `packs/<pack-id>/` 目录下（spec F007）。`garage init` 提供 host installer 把它们物化到下游项目里 Claude Code / OpenCode / Cursor 三家宿主原生识别的目录。

> **重要**：下面提到的 `.claude/skills/...`、`.opencode/skills/...`、`.cursor/skills/...` 等路径**都是各宿主的原生约定**（OpenSpec `docs/supported-tools.md` 与各家官方文档已记录），Garage 只是把内容写到那里，没有自创任何路径。

### 架构

```
源（Garage 仓库, 宿主无关）：
    packs/<pack-id>/skills/<skill-name>/SKILL.md
    packs/<pack-id>/agents/<agent-name>.md
    packs/<pack-id>/pack.json
    packs/<pack-id>/README.md

动作（在用户项目目录执行 garage init）：
    garage init --hosts claude,cursor,opencode
    ├── .claude/skills/...    .claude/agents/...        (Claude Code)
    ├── .opencode/skills/...  .opencode/agent/...       (OpenCode)
    ├── .cursor/skills/...                              (Cursor — 仅 skill)
    └── .garage/config/host-installer.json              (安装清单)
```

### 用法 1：交互式（默认）

在自己项目根目录运行：

```bash
cd ~/projects/my-app
garage init
```

不带 `--hosts` 也不带 `--yes` 时，CLI 在 TTY 下会问你每个 first-class 宿主：

```
Initialized Garage OS in /home/me/projects/my-app/.garage
Install Garage packs into claude? [y/N, or 'a' = yes-to-all-remaining, 'q' = stop-here]: y
Install Garage packs into cursor? [y/N, ...]:
Install Garage packs into opencode? [y/N, ...]: y
Installed 1 skills, 1 agents into hosts: claude, opencode
```

| 输入 | 含义 |
|---|---|
| `y` | 安装到当前宿主 |
| 回车 / `n` / `N` | 跳过当前宿主，继续问下一个 |
| `a` | 安装到当前宿主 + 之后所有宿主 |
| `q` | 停止询问，只用已选择的宿主 |

**non-TTY 退化**（CI / 脚本场景）：当 `stdin` 不是 TTY 且没传 `--hosts`、没传 `--yes`，CLI 会向 stderr 打印 `non-interactive shell detected; install no hosts (pass --hosts <list> to override)` 然后正常退出（`.garage/` 仍创建）。

### 用法 2：非交互（CI / 脚本）

```bash
# 装到三个 first-class 宿主
garage init --hosts all

# 装到指定宿主
garage init --hosts claude,cursor

# 显式不装任何宿主（仅创建 .garage/，等同于 F002 行为）
garage init --hosts none
# 或
garage init --yes
```

### 用法 3：再次运行（Extend Mode + 幂等）

`garage init` 是幂等的。再次运行：

- 已安装且**未被本地修改**的目标文件 → 重新写入相同内容（mtime 不变，详见 NFR-702）
- 已安装但**用户编辑过**的目标文件 → 默认跳过，stderr 输出 `Skipped <path> (locally modified, pass --force to overwrite)`；只有 `--force` 才会覆盖
- 新增宿主（如之前只装 claude，今天加 cursor）→ 既有宿主目录零变更，新增宿主追加；`installed_hosts` 累加

```bash
# 升级到 v2 packs 内容（强制覆盖本地修改）
garage init --hosts all --force
```

### 安装清单：`.garage/config/host-installer.json`

每次成功安装后写入；`schema_version=1`，受 `VersionManager` 管控（CON-703）。结构：

```json
{
  "schema_version": 1,
  "installed_hosts": ["claude", "cursor"],
  "installed_packs": ["garage"],
  "installed_at": "2026-04-19T18:04:19",
  "files": [
    {
      "src": "packs/garage/skills/garage-hello/SKILL.md",
      "dst": ".claude/skills/garage-hello/SKILL.md",
      "host": "claude",
      "pack_id": "garage",
      "content_hash": "1f5e1270b1dfb046382695b541b9d34d4ef9ddc06b5db8644d696ac4a5272927"
    }
  ]
}
```

任何后续 Agent 仅凭这个文件就能回答「本仓库装过哪些 host、哪些 pack、哪些文件来自 Garage」三个问题。

### Pack 与宿主映射表

| 宿主 ID | 宿主 | skill 路径 | agent 路径 | 来源依据 |
|---|---|---|---|---|
| `claude` | Claude Code | `.claude/skills/<id>/SKILL.md` | `.claude/agents/<id>.md` | OpenSpec `docs/supported-tools.md` claudeAdapter + Anthropic 官方 |
| `opencode` | OpenCode | `.opencode/skills/<id>/SKILL.md` | `.opencode/agent/<id>.md`（注意 agent 单数） | OpenSpec `docs/supported-tools.md` opencodeAdapter |
| `cursor` | Cursor | `.cursor/skills/<id>/SKILL.md` | （不支持，Cursor 当前无原生 agent surface） | OpenSpec `docs/supported-tools.md` cursorAdapter |

### 已知风险

- **Cursor 较旧版本可能不识别 `.cursor/skills/`**：本 cycle 选用 `.cursor/skills/` 是因为 OpenSpec 已验证可行、与 Anthropic SKILL.md 格式同构、不污染 always-loaded 的 `.cursor/rules/` context。如果你的 Cursor 版本不支持，请升级 Cursor 或临时改用其他宿主；后续可能新增 `.cursor/rules/` fallback（F007 § 5 deferred）。
- **同名 skill 跨多个 pack 冲突**：本 cycle 内单一 `packs/garage/` 不会触发，但如果未来 F008 把 HF skills 搬到 `packs/coding/` 后又有 pack 复用同名 skill，`garage init` 会以退出码 2 + stderr 列出冲突。

### 退出码

| 退出码 | 含义 |
|---|---|
| 0 | 成功（含「无 packs，仅创建 .garage/」） |
| 1 | 输入错误（unknown host）/ pack.json 非法 / SKILL.md 缺 front matter / OS 文件 IO 错误 |
| 2 | 同名 skill 跨 pack 冲突（FR-704 验收 #4） |

### 可发现性链

新 Agent / 用户从仓库根开始读，按下列顺序 5 分钟内可掌握全部用法（FR-710 验收 #1）：

1. `AGENTS.md` — 项目约定中心
2. `packs/README.md` — `packs/` 目录契约
3. `docs/guides/garage-os-user-guide.md` 本段（"Pack & Host Installer"）

---

## 相关文档

- [Garage OS 开发者指南](./garage-os-developer-guide.md) — 架构细节和扩展开发
- [设计原则](../soul/design-principles.md) — Garage 的 5 条核心设计原则
- [AGENTS.md](../../AGENTS.md) — 项目约定中心
- [F007 spec](../features/F007-garage-packs-and-host-installer.md) — Pack & Host Installer 规格
