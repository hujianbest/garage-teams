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
- **Pack 安装清单（F007）**: `.garage/config/host-installer.json`（schema_version=1，`garage init --hosts ...` 写入；记录已安装宿主集合 + Garage-owned 文件清单 + content_hash，作为幂等再运行凭证）
- 平台契约: .garage/contracts/
- 技术栈: Python 3.11+ (Poetry)

## Packs & Host Installer (F007/F008)

Garage 自带的可分发 skills + agents 沉淀在仓库 `packs/<pack-id>/` 下；`garage init --hosts ...` 把它们物化到下游项目里 Claude Code / OpenCode / Cursor 三家宿主原生目录。

### 当前 packs（F008 落地后）

| Pack | version | skills | agents | 用途 |
|---|---|---|---|---|
| `packs/garage/` | `0.2.0` | 3 | 1 | Getting-started 三件套：garage-hello（占位 sample）+ find-skills（发现新 skill）+ writing-skills（写新 skill）+ garage-sample-agent |
| `packs/coding/` | `0.1.0` | 22 | 0 | HarnessFlow 工程工作流 family（21 hf-* + using-hf-workflow + 11 个 family-level 共享资产 docs/templates/principles）|
| `packs/writing/` | `0.1.0` | 4 | 0 | 内容创作 family：blog-writing / humanizer-zh / hv-analysis / khazix-writer + family-level prompts/横纵分析法.md |

合计 3 个 pack × 29 个 skill × 3 个宿主 = `garage init --hosts all` 物化 87 个 skill 文件 + 1 个 agent 文件（agent 仅装到 claude / opencode）。

### 入口指针（FR-710 5 分钟冷读链）

| 文档 | 角色 |
|---|---|
| `packs/README.md` | 顶层契约：pack 目录结构、`pack.json` schema、与宿主关系、不变量 |
| `packs/<pack-id>/README.md` | 每个 pack 的概述 + skill/agent 清单（强制） |
| `docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段 | 端到端用法（交互/非交互/extend mode、退出码、宿主路径表、风险） |
| `docs/features/F007-garage-packs-and-host-installer.md` | F007 已批准规格（packs/ 目录契约 + `garage init --hosts ...` 安装管道） |
| `docs/features/F008-garage-coding-pack-and-writing-pack.md` | F008 已批准规格（把 `.agents/skills/` 物化为 packs 内容物）|

代码入口：`src/garage_os/adapter/installer/`（与 F001 `host_adapter.py` 同包但接口独立，详见 design ADR-D7-1）。三个 first-class host adapter 在 `src/garage_os/adapter/installer/hosts/{claude,opencode,cursor}.py`。

### 本仓库自身 IDE 加载入口（F008 ADR-D8-2 候选 C）

F008 cycle 把 `.agents/skills/` 整个删除，改为 dogfood 安装产物作为 IDE 加载入口。**首次 clone 本仓库的贡献者**必须在仓库根跑一次 dogfood 才能在 IDE 内加载到这 29 个 skill：

```bash
cd /path/to/garage-agent
garage init --hosts cursor,claude
# → 在仓库根 dogfood 出 .cursor/skills/ + .claude/skills/，IDE 即可加载 29 个 skill
# 注：.cursor/skills/ + .claude/skills/ 已在 .gitignore 内排除，不入 git 追踪
# → AGENTS.md / README.md 更新后无需再次跑 dogfood，但 packs/ 内容物变化时需要重跑
```

为什么这么设计？

- 单源不变量最强：`packs/<pack-id>/` 是唯一权威源，`.cursor/skills/` 与 `.claude/skills/` 在 git 视角是 dogfood 安装产物（与下游用户体验完全一致）
- 验证 D7 安装管道可用：本仓库自己跑 `garage init --hosts cursor,claude` 就是对 F007 + F008 联合最强证据
- 无平台 symlink 风险（与 candidate A 的 git symlink 路径相比，跨平台兼容更强）

详见 design ADR-D8-2（`docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`）。

### Garage OS 开发者参考

#### 模块概览

Garage OS 源码位于 `src/garage_os/`，由 7 个核心模块组成：

| 模块 | 路径 | 职责 |
|------|------|------|
| **types** | `src/garage_os/types/` | 核心类型定义：`SessionState`、`ArtifactReference`、`KnowledgeEntry`、`ExperienceRecord`、`Checkpoint` 等数据结构 |
| **storage** | `src/garage_os/storage/` | 文件存储基础设施：`FileStorage`（带文件锁的读写）、`AtomicWriter`（原子写入）、`FrontMatterParser`（YAML front matter 解析） |
| **runtime** | `src/garage_os/runtime/` | 运行时核心：`SessionManager`（会话生命周期）、`StateMachine`（状态机）、`SkillExecutor`（技能执行）、`ErrorHandler`（错误处理与重试）、`ArtifactBoardSync`（制品同步） |
| **knowledge** | `src/garage_os/knowledge/` | 知识管理：`KnowledgeStore`（知识条目 CRUD，markdown + front matter 存储）、`ExperienceIndex`（经验记录与索引）、`KnowledgeIntegration`（知识查询集成） |
| **adapter** | `src/garage_os/adapter/` | 宿主适配层：`HostAdapterProtocol`（运行时执行协议）、`ClaudeCodeAdapter`（运行时执行实现）；**`adapter/installer/` 子包（F007）**：`HostInstallAdapter` Protocol（安装期路径映射，与运行时 protocol 独立）、`HOST_REGISTRY` 三宿主、`pipeline.install_packs` 端到端 |
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
