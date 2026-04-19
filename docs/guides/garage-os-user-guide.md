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

## 相关文档

- [Garage OS 开发者指南](./garage-os-developer-guide.md) — 架构细节和扩展开发
- [设计原则](../soul/design-principles.md) — Garage 的 5 条核心设计原则
- [AGENTS.md](../../AGENTS.md) — 项目约定中心
