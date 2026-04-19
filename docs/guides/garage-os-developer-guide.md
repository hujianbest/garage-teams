# Garage OS 开发者指南

- 定位: 面向开发者的 Garage OS 扩展与贡献指南
- 版本: 0.1.0 (Phase 1)
- 日期: 2026-04-16

---

## 架构概览

Garage OS 采用 **Layered File-First Runtime with Host Adapter** 架构，5 层结构：

```
┌─────────────────────────────────────────┐
│          宿主层 (Host Layer)             │  Claude Code / Hermes / Cursor
├─────────────────────────────────────────┤
│        宿主适配层 (Host Adapter)         │  HostAdapterProtocol 接口
├─────────────────────────────────────────┤
│         平台契约层 (Contracts)           │  YAML/JSON 契约定义
├─────────────────────────────────────────┤
│  运行时核心 + 知识模块 + 工具注册表       │  核心业务逻辑
├─────────────────────────────────────────┤
│        文件系统存储层 (.garage/)         │  所有数据的持久化
└─────────────────────────────────────────┘
```

### 模块地图

```
src/garage_os/
├── types/              # 核心类型定义
│   └── __init__.py     # SessionState, ErrorCategory, ArtifactReference 等
├── storage/            # 存储基础设施
│   ├── file_storage.py       # FileStorage — 文件 CRUD
│   ├── atomic_writer.py      # AtomicWriter — 原子写入 + checksum
│   └── front_matter.py       # FrontMatterParser — YAML front matter 解析
├── runtime/            # 运行时核心
│   ├── session_manager.py    # SessionManager — 会话生命周期
│   ├── state_machine.py      # StateMachine — 状态转换引擎
│   ├── error_handler.py      # ErrorHandler — 错误分类 + 重试
│   ├── artifact_board_sync.py # ArtifactBoardSync — 工件一致性协议
│   └── skill_executor.py     # SkillExecutor — 技能执行引擎
├── knowledge/          # 知识模块
│   ├── knowledge_store.py    # KnowledgeStore — 知识 CRUD
│   ├── experience_index.py   # ExperienceIndex — 经验记录 + 检索
│   └── integration.py        # KnowledgeIntegration — 跨模块联动
├── adapter/            # 宿主适配层
│   ├── host_adapter.py       # HostAdapterProtocol — 协议定义
│   └── claude_code_adapter.py # ClaudeCodeAdapter — Claude Code 实现
├── tools/              # 工具注册表
│   ├── tool_registry.py      # ToolRegistry — 声明式工具注册
│   └── tool_gateway.py       # ToolGateway — 权限检查 + 调用日志
└── platform/           # 平台层
    └── version_manager.py    # VersionManager — 版本检测 + 迁移
```

---

## 如何添加新模块

### 1. 创建目录结构

```bash
mkdir -p src/garage_os/new_module/
touch src/garage_os/new_module/__init__.py
mkdir -p tests/new_module/
touch tests/new_module/__init__.py
```

### 2. 定义类型

在 `src/garage_os/types/__init__.py` 中添加新的 Enum 或 dataclass：

```python
@dataclass
class NewType:
    """Description of the new type."""
    id: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
```

记得在 `__all__` 列表中导出。

### 3. 实现模块

```python
# src/garage_os/new_module/new_thing.py
"""Module docstring."""

from pathlib import Path
from garage_os.types import NewType

class NewThing:
    """Does something new."""

    def __init__(self, storage_dir: Path):
        self._storage_dir = storage_dir

    def create(self, name: str) -> NewType:
        """Create a new thing."""
        ...
```

### 4. 写测试

严格 TDD：先写测试，再实现。

```python
# tests/new_module/test_new_thing.py
import pytest
from pathlib import Path
from garage_os.new_module.new_thing import NewThing

class TestNewThing:
    def test_create(self, tmp_path: Path):
        thing = NewThing(tmp_path)
        result = thing.create("test")
        assert result.name == "test"
```

### 5. 运行测试

```bash
uv run pytest tests/new_module/test_new_thing.py -v
uv run pytest tests/ -q  # 全量回归
```

---

## 如何添加新 Host Adapter

Host Adapter 是 Garage OS 与具体 AI Agent 宿主的桥梁。添加新适配器只需两步：

### 1. 实现协议

`HostAdapterProtocol` 是一个 `@runtime_checkable` 协议，包含 4 个方法：

```python
from garage_os.adapter.host_adapter import HostAdapterProtocol

class MyAdapter:
    """Adapter for My AI Agent."""

    def invoke_skill(self, skill_name: str, params: dict | None = None) -> dict:
        """调用宿主的 skill 执行能力。"""
        ...

    def read_file(self, path: str) -> str:
        """通过宿主读取文件。"""
        ...

    def write_file(self, path: str, content: str) -> None:
        """通过宿主写入文件。"""
        ...

    def get_repository_state(self) -> dict:
        """获取仓库状态（分支、commit、是否脏）。"""
        ...
```

### 2. 验证宿主无关性

使用 `isinstance(adapter, HostAdapterProtocol)` 验证：

```python
def test_my_adapter_satisfies_protocol():
    adapter = MyAdapter(workspace_root=Path("/tmp"))
    assert isinstance(adapter, HostAdapterProtocol)
```

SkillExecutor 可以无缝切换到新适配器，无需修改核心逻辑。

---

## 如何扩展知识模块

### 添加新的知识类型

KnowledgeStore 支持三种类型：`decision`、`pattern`、`solution`。如需添加新类型：

1. 在 `types/__init__.py` 中扩展 `KnowledgeType` 枚举
2. 在 `knowledge_store.py` 的 `_VALID_TYPES` 中注册
3. 添加对应的知识目录名映射
4. 更新测试

### 自定义经验检索

ExperienceIndex 支持按 `task_type`、`domain`、`skill_ids`、`key_patterns` 检索。扩展检索维度：

1. 在 `ExperienceRecord` dataclass 中添加新字段
2. 在 `ExperienceIndex.search()` 中添加新过滤逻辑
3. 在 `matches_xxx()` 方法中实现匹配

---

## 测试约定

### 测试结构

```
tests/
├── adapter/           # 宿主适配器测试
├── compatibility/     # 兼容性测试（skills、迁移）
├── integration/       # 端到端集成测试
├── knowledge/         # 知识模块测试
├── platform/          # 平台层测试
├── runtime/           # 运行时核心测试
├── security/          # 安全测试
├── storage/           # 存储层测试
└── tools/             # 工具注册表测试
```

### 测试命令

```bash
# 全量测试（~416 个测试，~26 秒）
uv run pytest tests/ -q

# 单模块测试
uv run pytest tests/runtime/ -v

# 单个测试文件
uv run pytest tests/runtime/test_error_handler.py -v
```

### 测试风格

- **Class-based**: 每个测试类对应一个功能点
- **tmp_path**: 使用 pytest 的 tmp_path fixture 创建临时目录
- **mock**: 使用 unittest.mock 模拟外部依赖
- **不写入 ~/.garage/**: 所有测试使用隔离的临时目录

### 测试命名

```
test_<模块名>.py → Test<功能类> → test_<场景>
```

示例：`test_error_handler.py` → `TestRetryStrategy` → `test_retry_strategy_retryable`

---

## .garage/ 目录结构

```
.garage/
├── config/
│   ├── platform.json          # 平台配置（超时、最大会话数等）
│   ├── host-adapter.json      # 宿主适配器配置
│   └── tools/
│       └── registered-tools.yaml  # 工具声明
├── contracts/                  # 平台契约定义
├── sessions/
│   └── active/<session-id>/
│       ├── session.json        # 会话状态
│       ├── checkpoints/        # 检查点文件
│       └── sync-log.json       # 一致性同步日志
├── knowledge/
│   ├── decisions/              # 决策知识
│   ├── patterns/               # 模式知识
│   ├── solutions/              # 解决方案知识
│   └── .metadata/
│       └── index.json          # 知识索引
├── experience/
│   └── records/                # 经验记录
└── benchmark/                  # 性能基线数据
```

---

## 依赖关系

```
types ← (无依赖，被所有模块引用)
  ↑
storage ← (types)
  ↑
runtime ← (types, storage)
  ↑
knowledge ← (types, storage)
  ↑
adapter ← (types) — 独立于 runtime/knowledge
  ↑
tools ← (types, storage) — 独立于 runtime
  ↑
platform ← (types, storage) — 独立于 runtime
```

---

## Publisher 重复发布与 ID 生成规则（F004 v1.1）

`KnowledgePublisher` 在 v1.1 引入了 `PublicationIdentityGenerator` helper class，把"发布身份生成"职责从 `KnowledgeStore` 解耦出来。这让同一 candidate 被反复 `accept` / `edit_accept` 时的行为可预测、可冷读。

### 生成规则

`PublicationIdentityGenerator` 暴露两个**纯函数**方法，调用同 input 任意次返回同 output（NFR-401 决定性）：

| 方法 | 输入 | 输出 |
|------|------|------|
| `derive_knowledge_id(candidate_id, knowledge_type)` | candidate id + knowledge 类型 | v1.1 默认实现 = 直接返回 `candidate_id`（与 F003 v1 已发布数据完全兼容，无迁移） |
| `derive_experience_id(candidate_id)` | candidate id | v1.1 默认实现 = 直接返回 `candidate_id` |

如果未来 cycle 想切换到 namespaced id 或 hash 后缀，**只改 `derive_*` 实现**即可；调用方（CLI、orchestrator）签名不变。

### 重复发布走 update 路径

`KnowledgePublisher.publish_candidate` 在 store 前先调 `KnowledgeStore.retrieve(type, id)`：

- 若不存在 → `KnowledgeStore.store(entry)`（version=1）
- 若存在 → carry-over `related_decisions` 与 `PRESERVED_FRONT_MATTER_KEYS`（含 `supersedes`）→ `KnowledgeStore.update(entry)`（内部 `version+=1`）

experience 路径同理：`ExperienceIndex.retrieve(record_id)` → 不存在 store / 存在 update。

### 同名 candidate 不会触发 self-conflict

`ConflictDetector.detect(title, tags)` 会按 title 和 tags 反查 knowledge store，这意味着同 candidate 第二次发布时它自己就会被识别为 "similar entry"。publisher 在判定 `if similar_entries` 之前**剔除**等于 `derive_knowledge_id(candidate_id, type)` 的元素，让 self-conflict 不再要求 `--strategy`。

参见：`docs/features/F004-...md` FR-401、`docs/designs/2026-04-19-garage-memory-v1-1-design.md` § 11.1 / § 11.2 / § 11.2.1。

---

## Session memory-extraction-error.json schema（F004 v1.1）

`SessionManager.archive_session(...)` 在归档完成后会以 best-effort 调用 memory extraction orchestrator。F004 之前，这条触发链路任何点失败只走 `logger.warning(...)`，没有文件级证据；F004 v1.1 在每个 phase 失败时持久化一份 latest-error JSON 到 `sessions/archived/<session_id>/memory-extraction-error.json`。

### Schema (v1)

```json
{
  "schema_version": "1",
  "session_id": "<session id string>",
  "phase": "orchestrator_init" | "enablement_check" | "extraction",
  "error_type": "<Exception class name>",
  "error_message": "<str(exc)>",
  "triggered_at": "<ISO 8601 timestamp>"
}
```

### 字段约束

- `phase` 是封闭枚举，仅以下三值：
  - `orchestrator_init`：`MemoryExtractionOrchestrator(...)` 实例化抛错
  - `enablement_check`：`is_extraction_enabled()` 抛错
  - `extraction`：`extract_for_archived_session(...)` 抛错（orchestrator 内部 batch-level 错误仍由 `evaluation_summary=extraction_failed` batch 文件承担，不在此重复写）
- 同一 session 二次失败覆盖前次（latest-error 语义；archive-time 触发对每个 session 只发生一次）
- 文件不存在 = 提取链路成功 或 `extraction_enabled=false`
- 旧版本（F003 之前）归档目录无该文件可正常读取（向后兼容）

### 与 logger.warning 的关系

文件层 + stderr `logger.warning(...)` 是**双层防护**：操作员 tail 日志仍能看到错误；自动化 reader 可以直接读 JSON。两层不重复信息（log 含 phase + exc，文件含完整 schema）。

参见：`docs/features/F004-...md` FR-404、`docs/designs/2026-04-19-garage-memory-v1-1-design.md` § 10.4 / § 11.3 / § 11.4。

---

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 存储格式 | 文件系统 (JSON/YAML/markdown) | git 可追踪，人类可读 |
| 工件权威源 | 磁盘文件 | artifact-first 原则 |
| 宿主耦合 | Protocol 协议 | 宿主无关，可替换 |
| 并发控制 | 文件锁 (filelock) | Phase 1 简单方案 |
| 状态管理 | State Machine 模式 | 复杂 workflow 必要模式 |
| 错误策略 | 分类 + 重试 | 区分可恢复/不可恢复错误 |

---

## 贡献流程

1. **创建分支**: `git checkout -b feature/xxx`
2. **TDD 开发**: 先写测试 → 实现 → 通过
3. **全量回归**: `uv run pytest tests/ -q`
4. **提交**: 每完成一个功能点就提交
5. **Review**: 参照 AHE workflow 的 review 流程
