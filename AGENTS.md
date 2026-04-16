# AGENTS

## AHE 文档约定

- 在本仓库的 AHE workflow 中，`docs/features/` 下的 `Fxxx` 文档就是 `specs`。
- 当提到 `spec`、`specs` 或"规格"时，默认指 `docs/features/` 的 feature specs，而不是 `docs/tasks/`。

## Skill 写作原则

`docs/principles/skill-anatomy.md` 定义所有 Garage skill 的目标态写法，包括：

- 核心 7 原则（description 是分类器、主文件要短、边界必须显式等）
- 目录 anatomy（SKILL.md、references/、evals/、scripts/、assets/）
- 章节骨架（When to Use、Workflow、Output Contract、Red Flags、Verification 等）
- 演化与版本管理机制

新增或重写任何 skill 时，必须遵循此文档。

## 项目灵魂

`docs/soul/` 下存放 Garage 的核心信念和承诺，是所有设计决策的价值锚点：

- `manifesto.md` — 愿景宣言：Garage 为什么存在
- `user-pact.md` — 用户契约：Garage 对用户的承诺
- `design-principles.md` — 设计原则：架构决策的判断标准
- `growth-strategy.md` — 成长策略：系统怎么从简单变复杂

当设计决策出现价值冲突时，回溯到这里做判断。

## Garage OS

- 运行时数据存储: .garage/
- 平台配置: .garage/config/platform.json
- 宿主适配器配置: .garage/config/host-adapter.json
- 平台契约: .garage/contracts/
- 技术栈: Python 3.11+ (Poetry)

### Garage OS 开发者参考

#### 模块概览

Garage OS 源码位于 `src/garage_os/`，由 7 个核心模块组成：

| 模块 | 路径 | 职责 |
|------|------|------|
| **types** | `src/garage_os/types/` | 核心类型定义：`SessionState`、`ArtifactReference`、`KnowledgeEntry`、`ExperienceRecord`、`Checkpoint` 等数据结构 |
| **storage** | `src/garage_os/storage/` | 文件存储基础设施：`FileStorage`（带文件锁的读写）、`AtomicWriter`（原子写入）、`FrontMatterParser`（YAML front matter 解析） |
| **runtime** | `src/garage_os/runtime/` | 运行时核心：`SessionManager`（会话生命周期）、`StateMachine`（状态机）、`SkillExecutor`（技能执行）、`ErrorHandler`（错误处理与重试）、`ArtifactBoardSync`（制品同步） |
| **knowledge** | `src/garage_os/knowledge/` | 知识管理：`KnowledgeStore`（知识条目 CRUD，markdown + front matter 存储）、`ExperienceIndex`（经验记录与索引）、`KnowledgeIntegration`（知识查询集成） |
| **adapter** | `src/garage_os/adapter/` | 宿主适配层：`HostAdapterProtocol`（宿主无关协议，定义 invoke_skill/read_file/write_file/get_repository_state 四个核心操作）、`ClaudeCodeAdapter`（Claude Code 实现） |
| **tools** | `src/garage_os/tools/` | 工具网关：`ToolRegistry`（工具注册与发现）、`ToolGateway`（工具调用记录与 mock 执行） |
| **platform** | `src/garage_os/platform/` | 平台契约管理：`VersionManager`（版本检测、兼容性检查、schema 迁移） |

模块依赖关系（自底向上）：
```
types → storage → runtime → knowledge
                  ↑            ↑
              adapter ← tools ← platform
```

#### 关键命令

```bash
# 运行全部测试
uv run pytest tests/ -q

# 运行指定模块测试
uv run pytest tests/runtime/ -q
uv run pytest tests/knowledge/ -q

# 运行性能基准测试
uv run python scripts/benchmark.py

# 类型检查
uv run mypy src/

# 代码风格检查
uv run ruff check src/ tests/
```

#### .garage/ 目录结构

`.garage/` 是 Garage OS 的运行时数据目录，所有数据以文件形式存储，git 可追踪：

```
.garage/
├── README.md                              # 目录说明
├── config/
│   ├── platform.json                      # 平台配置（schema_version, storage_mode, session_timeout 等）
│   ├── host-adapter.json                  # 宿主适配器配置（host_type, interaction_mode, capabilities）
│   └── tools/
│       └── registered-tools.yaml          # 已注册工具清单
├── contracts/
│   ├── session-manager-interface.yaml     # SessionManager 接口契约
│   ├── state-machine-interface.yaml       # StateMachine 接口契约
│   ├── skill-executor-interface.yaml      # SkillExecutor 接口契约
│   ├── knowledge-store-interface.yaml     # KnowledgeStore 接口契约
│   ├── host-adapter-interface.yaml        # HostAdapter 接口契约
│   ├── error-handler-interface.yaml       # ErrorHandler 接口契约
│   ├── tool-registry-interface.yaml       # ToolRegistry 接口契约
│   └── version-manager-interface.yaml     # VersionManager 接口契约
├── knowledge/
│   ├── .metadata/
│   │   └── index.json                     # 经验索引（中心索引）
│   ├── decisions/                         # 决策类知识条目（markdown + front matter）
│   ├── patterns/                          # 模式类知识条目
│   └── solutions/                         # 解决方案类知识条目
├── experience/
│   └── records/                           # 经验记录（JSON 格式）
└── sessions/
    ├── active/                            # 活跃会话
    └── archived/                          # 归档会话
```

- **零配置启动**：首次使用时目录由 `FileStorage` 自动创建
- **文件即契约**：所有配置文件都有 `schema_version` 字段，变更通过 `VersionManager` 管理
- **人类可读**：知识条目使用 markdown + YAML front matter，可直接用编辑器阅读

#### 测试约定

- **测试目录结构**与源码模块一一对应：`tests/runtime/`、`tests/storage/`、`tests/knowledge/`、`tests/adapter/`、`tests/tools/`、`tests/platform/`
- **测试文件命名**：`test_<module_name>.py`，如 `test_session_manager.py`、`test_knowledge_store.py`
- **测试类命名**：`Test*`，如 `TestSessionManager`、`TestKnowledgeStore`
- **每个测试使用 `tmp_path` fixture** 创建临时 `.garage/` 目录，不污染项目状态
- **集成测试**放在 `tests/integration/`，如 `test_e2e_workflow.py`
- **安全测试**放在 `tests/security/`
- **兼容性测试**放在 `tests/compatibility/`
- 当前共 **323 个测试**，全部通过
- 运行测试：`uv run pytest tests/ -q`（快速模式）或 `uv run pytest tests/ -v`（详细模式）
