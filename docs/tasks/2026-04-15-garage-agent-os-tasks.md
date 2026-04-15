# Garage Agent 操作系统 Phase 1 任务计划

- 状态: 草稿
- 主题: F001 — Garage Agent 操作系统 Phase 1（Stage 1-2）
- 日期: 2026-04-15
- 关联规格: docs/features/F001-garage-agent-operating-system.md
- 关联设计: docs/designs/2026-04-15-garage-agent-os-design.md

---

## 1. 概述

本任务计划将 Garage Agent 操作系统 Phase 1 拆解为可独立验证的工程任务。Phase 1 覆盖：

- **Stage 1（工具箱）**：运行时基础，Claude Code 为首宿主，宿主适配层
- **Stage 2（记忆体）**：自动知识积累，经验检索，会话状态持续化

设计采用 Layered File-First Runtime with Host Adapter 架构，5 层结构：
1. 宿主层（Host Layer）
2. 宿主适配层（Host Adapter Layer）
3. 平台契约层（Platform Contract Layer）
4. 运行时核心 + 知识模块 + 工具注册表
5. 文件系统存储层

### 核心约束

- 不引入数据库、常驻服务、Web UI
- 优先使用 markdown、JSON、文件系统
- 所有数据存储在 Garage 仓库内部（`.garage/`）
- 保持现有 26 个 AHE skills 的兼容
- 为 Stage 2-4 预留扩展点但不提前实现

---

## 2. 里程碑

| 里程碑 | 目标 | 关键交付物 | 估计任务数 |
|--------|------|-----------|-----------|
| **M1: 基础验证** | Claude Code API 验证 + 目录结构 + 平台契约定义 | spike 报告、`.garage/` 骨架、契约文件 | 4 |
| **M2: 运行时核心** | Session Manager、State Machine、Error Handler | 运行时核心模块，可创建/恢复/归档 session | 5 |
| **M3: 知识模块** | Knowledge Store、Experience Index | 知识 CRUD、经验记录、手动检索 | 4 |
| **M4: 集成联通** | Skill Executor、Tool Gateway、端到端 workflow | 完整 skill 执行链路，Host Adapter 接入 | 5 |
| **M5: 加固验证** | NFR 验证、迁移测试、文档、兼容性确认 | 性能基线、安全审计、迁移脚本、用户文档 | 4 |

**总计：22 个任务，5 个里程碑**

---

## 3. 文件 / 工件影响图

### 3.1 新增目录结构

```
.garage/
├── sessions/
│   ├── active/<session-id>/
│   │   ├── session.json
│   │   ├── checkpoints/
│   │   ├── artifacts/
│   │   └── sync-log.json
│   └── archived/<session-id>/
│       └── archive.json
├── knowledge/
│   ├── decisions/
│   ├── patterns/
│   ├── solutions/
│   └── .metadata/
│       └── index.json
├── experience/
│   ├── records/
│   └── patterns/
├── config/
│   ├── platform.json
│   ├── host-adapter.json
│   └── tools/
│       └── registered-tools.yaml
├── contracts/
│   ├── host-adapter-interface.yaml
│   ├── session-manager-interface.yaml
│   ├── skill-executor-interface.yaml
│   ├── state-machine.yaml
│   ├── error-handler.yaml
│   ├── workflow-session.yaml
│   ├── node-definition.yaml
│   └── artifact-surface.yaml
└── benchmark/                   # 性能基线数据（M5）
```

### 3.2 新增源码模块（src/ 下）

```
src/
├── runtime/
│   ├── session-manager.ts
│   ├── state-machine.ts
│   ├── error-handler.ts
│   ├── skill-executor.ts
│   └── index.ts
├── knowledge/
│   ├── knowledge-store.ts
│   ├── experience-index.ts
│   └── index.ts
├── tools/
│   ├── tool-registry.ts
│   ├── tool-gateway.ts
│   └── index.ts
├── adapter/
│   ├── host-adapter.ts
│   ├── claude-code-adapter.ts
│   └── index.ts
├── platform/
│   ├── contracts.ts
│   ├── version-manager.ts
│   └── index.ts
├── storage/
│   ├── file-storage.ts
│   ├── atomic-writer.ts
│   └── index.ts
└── types/
    └── index.ts
```

### 3.3 影响的现有文件

| 文件 | 影响类型 | 说明 |
|------|---------|------|
| `AGENTS.md` | 修改 | 添加 Garage OS 约定入口 |
| `.gitignore` | 修改 | 排除 `.env`、`*.key`、敏感文件 |
| 现有 26 个 AHE skills | 无变更 | 兼容性约束，Phase 1 不修改 |

---

## 4. 需求与设计追溯

| 需求 | 设计模块 | 覆盖任务 |
|------|---------|---------|
| FR-001a 工作流技能执行 | Skill Executor + State Machine | T9, T10, T14 |
| FR-001b 执行状态管理 | Session Manager + State Machine | T5, T6, T7 |
| FR-001c 错误处理与恢复 | Error Handler | T8 |
| FR-002 知识存储与检索 | Knowledge Store + Experience Index | T11, T12 |
| FR-003 Claude Code 对接 | Host Adapter + Claude Code Adapter | T1, T13 |
| FR-004 数据仓库内部存储 | File Storage + `.garage/` 结构 | T3, T4 |
| FR-005 可迁移性 | 路径抽象 + 相对路径 | T17 |
| FR-006a/b 模式识别与经验 | Experience Index | T12 |
| FR-007 工具扩展接口 | Tool Registry + Tool Gateway | T15 |
| FR-008 渐进架构演进 | Platform Contract + Version Manager | T3, T4 |

---

## 5. 任务拆解

---

### M1: 基础验证

---

### T1. Claude Code Session API 技术验证 Spike

- **目标**: 验证 Claude Code session API 的实际能力，确认隐藏假设 ASM-EXT-001（Host Adapter 能否读取 session 状态、写入检查点、恢复到指定状态）
- **依赖**: 无
- **Ready When**: 设计已批准
- **初始队列状态**: ready
- **Selection Priority**: P0（最高优先级，所有后续任务的前置验证）
- **触碰工件**:
  - `docs/spikes/claude-code-session-api-spike.md`（spike 报告）
- **测试设计种子**:
  1. **能力探测**: 能否读取当前 session 的上下文信息（workspace path、conversation history）？
  2. **写入检查点**: 能否在 session 中间写入持久化状态？以什么形式（文件？环境变量？内存？）
  3. **恢复机制**: 新 session 能否读取上一 session 写入的状态？通过什么渠道（文件系统是最可靠回退）
  4. **限制识别**: Claude Code API 有哪些操作限制？超时、并发、上下文窗口？
  5. **回退策略**: 如果不支持原生 session 管理，纯 artifact-first 文件方案是否可行？
- **验证方式**: 编写 spike 报告，包含测试脚本和结论
- **预期证据**:
  - `docs/spikes/claude-code-session-api-spike.md` 包含：
    - 测试的 API 能力列表
    - 每个能力的测试结果（支持/不支持/部分支持）
    - 确认或否定 ASM-EXT-001 的结论
    - 如果否定，说明回退方案
- **完成条件**: spike 报告完成，ASM-EXT-001 假设已被确认或否定，Host Adapter 设计方向已确定

---

### T2. 运行时技术栈选型确认

- **目标**: 确认 Phase 1 的实现语言和构建工具链。评估 TypeScript/Node.js vs Python vs Shell scripts 的可行性
- **依赖**: T1（spike 结论可能影响选型）
- **Ready When**: T1=done
- **初始队列状态**: pending
- **Selection Priority**: P1
- **触碰工件**:
  - `docs/spikes/tech-stack-decision.md`（选型决策文档）
  - `package.json` 或 `pyproject.toml`（项目初始化）
  - `tsconfig.json` 或等价配置（如选 TypeScript）
- **测试设计种子**:
  1. 文件系统读写性能：100 个 JSON 文件的读写耗时
  2. YAML/Markdown 解析能力：front matter 解析正确性
  3. 与 Claude Code 的交互方式：CLI 调用、subprocess、SDK
- **验证方式**: 创建最小 hello-world 项目，运行基础测试
- **预期证据**: 技术选型决策文档 + 可运行的脚手架项目
- **完成条件**: 技术栈确定，项目骨架可构建和运行测试

---

### T3. `.garage/` 目录结构初始化 + 平台契约定义

- **目标**: 建立完整的 `.garage/` 目录结构和配置文件，定义所有平台契约 YAML 文件
- **依赖**: T1
- **Ready When**: T1=done
- **初始队列状态**: pending
- **Selection Priority**: P1
- **触碰工件**:
  - `.garage/` 完整目录结构（所有子目录）
  - `.garage/config/platform.json`
  - `.garage/config/host-adapter.json`
  - `.garage/contracts/*.yaml`（8 个契约文件）
  - `.gitignore`（更新）
  - `AGENTS.md`（更新，添加 Garage OS 入口）
- **测试设计种子**:
  1. 目录完整性检查：所有设计文档声明的目录都存在
  2. 配置文件格式验证：platform.json 包含所有必需字段
  3. 契约文件格式验证：每个 YAML 文件可被正确解析
  4. .gitignore 覆盖验证：敏感文件模式已被排除
- **验证方式**:
  - 脚本验证目录结构完整性
  - JSON/YAML schema 验证配置和契约文件格式
- **预期证据**: 完整的 `.garage/` 结构 + 所有契约文件 + 通过的验证脚本
- **完成条件**:
  - `.garage/` 下所有子目录已创建
  - `platform.json` 可被正确加载
  - 所有 8 个契约 YAML 文件内容完整
  - `.gitignore` 已更新
  - `AGENTS.md` 已更新

---

### T4. 类型定义 + 存储基础设施

- **目标**: 实现核心 TypeScript/Python 类型定义和文件存储基础设施（原子写入、文件锁、路径抽象）
- **依赖**: T2, T3
- **Ready When**: T2=done AND T3=done
- **初始队列状态**: pending
- **Selection Priority**: P1
- **触碰工件**:
  - `src/types/index.ts`（核心类型定义）
  - `src/storage/file-storage.ts`（文件存储接口）
  - `src/storage/atomic-writer.ts`（原子写入实现）
  - `src/storage/index.ts`
  - `tests/storage/atomic-writer.test.ts`
  - `tests/storage/file-storage.test.ts`
- **测试设计种子**:
  1. **原子写入**: 写入 JSON 文件 → kill 进程 → 验证文件要么完整要么不存在
  2. **文件锁**: 两个并发写入 → 验证无数据丢失（使用 temp file + rename）
  3. **路径抽象**: Windows 路径 / POSIX 路径都能正确处理
  4. **JSON 读写**: 写入 → 读取 → 验证内容一致
  5. **Front matter 解析**: markdown 文件的 YAML front matter 可被正确提取
- **验证方式**: 单元测试（目标覆盖率 > 80%）
- **预期证据**: 通过的测试套件 + 类型定义文档
- **完成条件**:
  - 所有类型定义编译通过
  - 原子写入测试通过（含故障注入）
  - 文件锁测试通过（含并发）
  - 路径抽象跨平台测试通过

---

### M2: 运行时核心

---

### T5. Session Manager 实现

- **目标**: 实现 Session Manager 模块，支持创建、恢复、更新、归档 session
- **依赖**: T4
- **Ready When**: T4=done
- **初始队列状态**: pending
- **Selection Priority**: P2
- **触碰工件**:
  - `src/runtime/session-manager.ts`
  - `src/runtime/index.ts`（更新）
  - `tests/runtime/session-manager.test.ts`
- **测试设计种子**:
  1. create_session → 验证 session_id 格式 `session-YYYYMMDD-NNN`
  2. create_session → 验证 session.json 已写入 `.garage/sessions/active/`
  3. restore_session（存在的 session）→ 返回正确 SessionState
  4. restore_session（不存在的 session）→ 返回 null
  5. update_session（修改 state）→ session.json 已更新
  6. update_session（修改 current_node_id）→ session.json 已更新
  7. archive_session → 文件从 active/ 移到 archived/
  8. list_active_sessions → 返回活跃 session 列表
  9. session 超时 → 自动归档（如果超过 session_timeout_seconds）
- **验证方式**: 单元测试（每个接口方法至少 2 个测试用例）
- **预期证据**: 通过的 Session Manager 测试套件
- **完成条件**:
  - create / restore / update / archive / list 接口全部通过测试
  - session.json 格式符合设计文档 10.1 节定义
  - 检查点（checkpoint）写入机制可用

---

### T6. State Machine 实现

- **目标**: 实现执行状态机，管理 idle → running → paused → completed / failed → archived 状态转换
- **依赖**: T4
- **Ready When**: T4=done
- **初始队列状态**: pending
- **Selection Priority**: P2
- **触碰工件**:
  - `src/runtime/state-machine.ts`
  - `tests/runtime/state-machine.test.ts`
- **测试设计种子**:
  1. 合法转换: idle→running, running→paused, paused→running, running→completed, running→failed, failed→running(重试), any→archived
  2. 非法转换: idle→completed, paused→completed, completed→running → 抛出异常
  3. 状态历史: 每次转换记录 timestamp 和触发原因
  4. 副作用触发: 转换到 paused 时生成等待事件
  5. 并发保护: 同一 session 两个并发状态转换 → 只有一个成功
- **验证方式**: 单元测试（合法转换 + 非法转换 + 边界情况）
- **预期证据**: 通过的状态机测试套件
- **完成条件**:
  - 所有合法转换通过测试
  - 所有非法转换正确抛出异常
  - 状态历史可追溯
  - 无并发冲突

---

### T7. Checkpoint + Session 恢复机制

- **目标**: 实现检查点写入和 session 恢复机制，包含降级恢复策略
- **依赖**: T5, T6
- **Ready When**: T5=done AND T6=done
- **初始队列状态**: pending
- **Selection Priority**: P2
- **触碰工件**:
  - `src/runtime/session-manager.ts`（更新，添加 checkpoint 方法）
  - `src/runtime/state-machine.ts`（更新，添加恢复逻辑）
  - `tests/runtime/checkpoint-recovery.test.ts`
- **测试设计种子**:
  1. 写入 checkpoint → checkpoint 文件存在且内容正确
  2. 从最新 checkpoint 恢复 → session 状态与 checkpoint 一致
  3. session.json 损坏 → 从最新 checkpoint 恢复
  4. 最新 checkpoint 损坏 → 回退到上一个有效 checkpoint
  5. 所有 checkpoint 损坏 → artifact-first 重建（扫描 artifacts/ 目录）
  6. 无任何数据 → 提示"从头开始"
  7. checksum 校验 → 损坏的数据被检测到
- **验证方式**: 单元测试 + 故障注入测试
- **预期证据**: 通过的恢复测试套件（含所有降级路径）
- **完成条件**:
  - 5 级恢复优先级链全部测试通过
  - checksum 校验机制可用
  - artifact-first 重建路径可用

---

### T8. Error Handler 实现

- **目标**: 实现错误分类、重试策略、用户介入协议
- **依赖**: T4, T6
- **Ready When**: T4=done AND T6=done
- **初始队列状态**: pending
- **Selection Priority**: P2
- **触碰工件**:
  - `src/runtime/error-handler.ts`
  - `tests/runtime/error-handler.test.ts`
- **测试设计种子**:
  1. 错误分类: network_timeout→retryable, permission_denied→user_intervention, corrupt_data→fatal, duplicate_notification→ignorable
  2. 重试策略: retryable 错误最多 3 次重试，间隔 1s/2s/4s（mock timer）
  3. 重试耗尽 → 升级为 fatal
  4. user_intervention → 触发暂停 + 通知用户
  5. fatal → 记录日志 + 停止执行
  6. ignorable → 记录日志 + 继续执行
  7. 错误日志格式验证
- **验证方式**: 单元测试（使用 mock timer 测试重试间隔）
- **预期证据**: 通过的错误处理测试套件
- **完成条件**:
  - 4 种错误类型分类正确
  - 重试策略按设计执行
  - 每种策略的行为正确

---

### T9. Artifact-Board 一致性协议实现

- **目标**: 实现 9.4 节定义的 Artifact-Board 冲突检测、解决和日志记录
- **依赖**: T5, T7
- **Ready When**: T5=done AND T7=done
- **初始队列状态**: pending
- **Selection Priority**: P2
- **触碰工件**:
  - `src/runtime/artifact-board-sync.ts`
  - `tests/runtime/artifact-board-sync.test.ts`
- **测试设计种子**:
  1. 一致状态 → 无同步操作
  2. 文件已更新但 board 未更新 → board 自动同步
  3. 文件已删除但 board 仍引用 → 标记为 orphan
  4. 文件存在但 board 未引用 → 标记为 untracked
  5. sync-log.json 格式验证
  6. 触发时机: session 恢复时 / skill 执行前 / skill 执行后
- **验证方式**: 单元测试
- **预期证据**: 通过的一致性协议测试套件
- **完成条件**:
  - 4 种比较结果分类正确处理
  - sync-log.json 正确记录
  - 冲突解决始终以文件为准

---

### M3: 知识模块

---

### T10. Knowledge Store 实现

- **目标**: 实现知识条目的 CRUD 操作、分类管理、front matter 解析
- **依赖**: T4
- **Ready When**: T4=done
- **初始队列状态**: pending
- **Selection Priority**: P3
- **触碰工件**:
  - `src/knowledge/knowledge-store.ts`
  - `src/knowledge/index.ts`
  - `tests/knowledge/knowledge-store.test.ts`
- **测试设计种子**:
  1. 创建 decision 类型知识 → 文件写入 `.garage/knowledge/decisions/` + front matter 完整
  2. 创建 pattern 类型知识 → 文件写入 `.garage/knowledge/patterns/`
  3. 创建 solution 类型知识 → 文件写入 `.garage/knowledge/solutions/`
  4. 读取知识 → front matter 正确解析 + 正文内容正确
  5. 更新知识 → version 递增 + updated_at 更新
  6. 删除知识 → 文件移除 + 索引更新
  7. 按标签/分类/日期检索 → 返回正确结果
  8. 知识条目 schema 验证 → 必需字段缺失时报错
- **验证方式**: 单元测试（CRUD + 检索）
- **预期证据**: 通过的知识存储测试套件
- **完成条件**:
  - 知识 CRUD 全部通过
  - Front matter 格式符合设计文档 10.1 节
  - 按标签/分类检索可用

---

### T11. Experience Index 实现

- **目标**: 实现经验记录的存储、索引和手动检索
- **依赖**: T4
- **Ready When**: T4=done
- **初始队列状态**: pending
- **Selection Priority**: P3
- **触碰工件**:
  - `src/knowledge/experience-index.ts`
  - `tests/knowledge/experience-index.test.ts`
- **测试设计种子**:
  1. 创建经验记录 → JSON 文件写入 `.garage/experience/records/` + schema 验证
  2. 按 task_type 检索 → 返回匹配的经验记录
  3. 按 skill_ids 检索 → 返回使用过指定 skill 的经验
  4. 按 domain 检索 → 返回匹配领域的经验
  5. 按 key_patterns 检索 → 返回包含指定模式标签的经验
  6. 更新索引 → `.garage/knowledge/.metadata/index.json` 正确更新
  7. 空知识库检索 → 返回空数组（不报错）
- **验证方式**: 单元测试
- **预期证据**: 通过的经验索引测试套件
- **完成条件**:
  - 经验记录 CRUD 通过
  - 按场景检索可用
  - 索引文件正确维护

---

### T12. 知识模块集成（Knowledge Store + Experience Index 联动）

- **目标**: 实现知识模块和经验模块的集成，支持跨模块检索和关联推荐
- **依赖**: T10, T11
- **Ready When**: T10=done AND T11=done
- **初始队列状态**: pending
- **Selection Priority**: P3
- **触碰工件**:
  - `src/knowledge/index.ts`（更新，添加集成接口）
  - `tests/knowledge/integration.test.ts`
- **测试设计种子**:
  1. 根据经验记录自动关联相关知识 → 返回关联的 decision/pattern
  2. 手动知识提取流程：创建 session → 完成任务 → 手动记录经验 → 知识入库
  3. 跨模块一致性：删除知识条目后，经验记录的引用正确处理
- **验证方式**: 集成测试
- **预期证据**: 通过的知识模块集成测试
- **完成条件**:
  - 跨模块检索可用
  - 手动知识提取流程可用
  - 数据一致性维护

---

### M4: 集成联通

---

### T13. Host Adapter + Claude Code Adapter 实现

- **目标**: 实现 Host Adapter 接口和 Claude Code 具体适配器，基于 T1 spike 结论
- **依赖**: T1, T4, T5
- **Ready When**: T1=done AND T4=done AND T5=done
- **初始队列状态**: pending
- **Selection Priority**: P3
- **触碰工件**:
  - `src/adapter/host-adapter.ts`（接口定义）
  - `src/adapter/claude-code-adapter.ts`（Claude Code 实现）
  - `src/adapter/index.ts`
  - `tests/adapter/claude-code-adapter.test.ts`
  - `tests/adapter/host-adapter.test.ts`（使用 mock adapter 测试接口）
- **测试设计种子**:
  1. invoke_skill → 正确传递参数到 skill 执行器
  2. read_file → 通过 Claude Code 读取文件内容
  3. write_file → 通过 Claude Code 写入文件
  4. get_repository_state → 返回正确的 git 状态
  5. Mock adapter 替换 → 核心逻辑无需修改（宿主无关验证）
  6. 错误传递 → host 层错误正确转换为平台错误格式
- **验证方式**: 单元测试（含 mock adapter 替换验证宿主无关性）
- **预期证据**: 通过的 adapter 测试套件 + mock 替换无变更
- **完成条件**:
  - Host Adapter 接口定义完成
  - Claude Code Adapter 实现完成
  - Mock adapter 可替代 Claude Code adapter 且核心逻辑无变更

---

### T14. Skill Executor 实现

- **目标**: 实现 Skill Executor，支持调用 AHE workflow skills、管理执行上下文、集成知识库查询
- **依赖**: T4, T5, T6, T8, T12
- **Ready When**: T4=done AND T5=done AND T6=done AND T8=done AND T12=done
- **初始队列状态**: pending
- **Selection Priority**: P4
- **触碰工件**:
  - `src/runtime/skill-executor.ts`
  - `tests/runtime/skill-executor.test.ts`
- **测试设计种子**:
  1. execute_skill（正常路径）→ 状态 idle→running→completed，artifacts 正确产出
  2. execute_skill（需要用户输入）→ 状态 running→paused，等待输入后 paused→running
  3. execute_skill（执行失败）→ 状态 running→failed，Error Handler 正确分类
  4. execute_skill（重试）→ retryable 错误后成功恢复
  5. get_skill_metadata → 返回正确的 skill 元数据
  6. list_skills → 返回 pack 内所有 skills 列表
  7. 知识库集成 → 执行时查询相关知识（可选）
- **验证方式**: 单元测试 + 集成测试
- **预期证据**: 通过的 skill executor 测试套件
- **完成条件**:
  - Skill 执行正常路径通过
  - 暂停/恢复路径通过
  - 错误处理集成通过
  - 知识库查询集成可用

---

### T15. Tool Registry + Tool Gateway 实现

- **目标**: 实现工具注册表的声明式配置和 Tool Gateway 的权限检查、调用日志
- **依赖**: T4
- **Ready When**: T4=done
- **初始队列状态**: pending
- **Selection Priority**: P3（可与 T10/T11 并行）
- **触碰工件**:
  - `src/tools/tool-registry.ts`
  - `src/tools/tool-gateway.ts`
  - `src/tools/index.ts`
  - `.garage/config/tools/registered-tools.yaml`（初始工具声明）
  - `tests/tools/tool-registry.test.ts`
  - `tests/tools/tool-gateway.test.ts`
- **测试设计种子**:
  1. 注册工具 → registered-tools.yaml 包含新工具声明
  2. 发现工具 → 按 capability 查询返回匹配的工具列表
  3. 权限检查 → 白名单工具通过，非白名单工具拒绝（100% 拒绝率）
  4. 调用日志 → 每次工具调用记录 tool_id、耗时、结果状态
  5. 工具配置验证 → config_schema 校验
  6. Phase 1 简化: 实际工具调用由 Skill Executor 通过 Host Adapter 执行
- **验证方式**: 单元测试
- **预期证据**: 通过的工具注册表测试套件
- **完成条件**:
  - 工具注册/发现接口可用
  - 权限检查正确执行
  - 调用日志正确记录

---

### T16. 端到端 Workflow 集成

- **目标**: 实现 Host Adapter → Session Manager → Skill Executor → Knowledge Store 完整链路的端到端集成
- **依赖**: T5, T6, T7, T8, T9, T13, T14, T15
- **Ready When**: 所有 M2+M3+M4 前置任务=done
- **初始队列状态**: pending
- **Selection Priority**: P5
- **触碰工件**:
  - `src/runtime/index.ts`（更新，导出集成接口）
  - `tests/integration/e2e-workflow.test.ts`
- **测试设计种子**:
  1. **完整 workflow**: 调用 skill → 创建 session → 执行 skill → 产出 artifact → 知识提取 → session 归档
  2. **中断恢复**: 执行中 kill → 恢复 session → 从 checkpoint 继续 → 完成
  3. **错误恢复**: 执行中注入 retryable 错误 → 自动重试 → 成功
  4. **知识积累**: 完成 workflow → 手动记录经验 → 下次执行查询到相关知识
  5. **Artifact-Board 一致性**: 执行前检测冲突 → 自动同步 → 执行后验证
  6. **Mock skill**: 使用 mock skill 验证完整链路无需真实 skill 执行
- **验证方式**: E2E 集成测试
- **预期证据**: 通过的端到端测试套件
- **完成条件**:
  - 完整 workflow 链路测试通过
  - 中断恢复场景测试通过
  - 错误恢复场景测试通过
  - 知识积累流程测试通过

---

### T17. Platform Contract + Version Manager 实现

- **目标**: 实现平台契约的版本管理和向后兼容检查
- **依赖**: T3, T4
- **Ready When**: T3=done AND T4=done
- **初始队列状态**: pending
- **Selection Priority**: P3（可与 M2 并行）
- **触碰工件**:
  - `src/platform/contracts.ts`
  - `src/platform/version-manager.ts`
  - `src/platform/index.ts`
  - `tests/platform/version-manager.test.ts`
- **测试设计种子**:
  1. 版本检测: 加载 v1 格式文件 → 正确识别版本
  2. 向后兼容: 使用旧 schema 数据 → 无错误加载
  3. 版本不兼容: 使用不支持的 schema 版本 → 明确报错
  4. 升级路径: v1 → v2 迁移脚本（预留）
- **验证方式**: 单元测试
- **预期证据**: 通过的版本管理测试套件
- **完成条件**:
  - 版本检测可用
  - 向后兼容测试通过
  - 不兼容版本正确报错

---

### M5: 加固验证

---

### T18. 性能基准建立

- **目标**: 建立性能基线，验证 NFR 性能要求（skill 调用 p90 < 30s，知识查询 p90 < 5s）
- **依赖**: T16
- **Ready When**: T16=done
- **初始队列状态**: pending
- **Selection Priority**: P5
- **触碰工件**:
  - `scripts/benchmark.py`（性能测试脚本）
  - `.garage/benchmark/baseline-YYYYMMDD.json`（基线数据）
- **测试设计种子**:
  1. Skill 调用响应：5 个标准 skill 各 10 次，p90 < 30s
  2. 知识查询：100/500/1000 条目各 100 次查询，p90 < 5s
  3. 退化率：100→1000 条目时 p90 增长不超过 50%
  4. Session 创建/恢复时间
- **验证方式**: 自动化性能测试脚本
- **预期证据**: 性能基线报告 + 所有 NFR 指标通过
- **完成条件**:
  - 性能测试脚本可运行
  - 所有 NFR 性能指标达标
  - 基线数据已保存

---

### T19. 安全审计 + 敏感数据验证

- **目标**: 验证 NFR 安全要求（敏感数据排除、权限检查、访问控制）
- **依赖**: T15, T16
- **Ready When**: T15=done AND T16=done
- **初始队列状态**: pending
- **Selection Priority**: P5
- **触碰工件**:
  - `scripts/security-audit.sh`（安全审计脚本）
  - `.gitignore`（验证更新）
- **测试设计种子**:
  1. 敏感数据扫描：grep -r 扫描 .garage/ 中 API key/password 模式 → 0 匹配
  2. .gitignore 覆盖：.env、*.key、credentials.* 已排除
  3. 工具权限：非白名单工具调用 → 100% 拒绝率
  4. 文件权限：session.json 不包含凭证信息
- **验证方式**: 自动化审计脚本 + 手动检查
- **预期证据**: 安全审计报告 + 所有安全检查通过
- **完成条件**:
  - 敏感数据扫描 0 匹配
  - .gitignore 覆盖完整
  - 工具权限 100% 拒绝率

---

### T20. 迁移测试 + 跨平台验证

- **目标**: 验证 FR-005 可迁移性和跨平台兼容性
- **依赖**: T16
- **Ready When**: T16=done
- **初始队列状态**: pending
- **Selection Priority**: P5
- **触碰工件**:
  - `scripts/migration-test.sh`（迁移测试脚本）
  - `tests/compatibility/migration.test.ts`
- **测试设计种子**:
  1. 仓库克隆到新环境 → 所有功能正常
  2. 路径可移植性：相对路径在 Linux/macOS/Windows 都正确
  3. 旧版本数据加载 → v1 schema 数据正确加载
  4. 空仓库初始化 → `init` 命令创建完整 .garage/ 结构
- **验证方式**: 迁移测试脚本（WSL 环境验证）
- **预期证据**: 通过的迁移测试报告
- **完成条件**:
  - 仓库克隆后功能正常
  - 跨平台路径处理正确
  - 旧数据向后兼容

---

### T21. 现有 Skills 兼容性验证

- **目标**: 验证现有 26 个 AHE skills 在新运行时下完全兼容
- **依赖**: T16
- **Ready When**: T16=done
- **初始队列状态**: pending
- **Selection Priority**: P5
- **触碰工件**:
  - `tests/compatibility/existing-skills.test.ts`
- **测试设计种子**:
  1. 逐一验证 26 个 skills 的 SKILL.md 可被正确解析
  2. 验证 skills 的目录结构未被破坏
  3. 验证 skills 的引用路径（references/、evals/ 等）仍然有效
  4. 验证 AHE workflow（specify → design → tasks）完整执行链路
- **验证方式**: 兼容性测试套件
- **预期证据**: 通过的兼容性测试报告
- **完成条件**:
  - 26 个 skills 全部兼容
  - AHE workflow 完整链路通过

---

### T22. 文档 + 用户指南

- **目标**: 编写 Garage OS 的用户文档和开发者指南
- **依赖**: T16
- **Ready When**: T16=done
- **初始队列状态**: pending
- **Selection Priority**: P5
- **触碰工件**:
  - `AGENTS.md`（更新，完善 Garage OS 部分）
  - `docs/guides/garage-os-user-guide.md`（用户指南）
  - `docs/guides/garage-os-developer-guide.md`（开发者指南）
  - `README.md`（更新，添加 Garage OS 介绍）
- **测试设计种子**:
  1. 新 Agent 按文档操作 → 5 分钟内理解约定
  2. 开发者按文档操作 → 30 分钟内添加 mock skill
  3. 文档中的代码示例 → 可执行且结果正确
- **验证方式**: 文档评审 + 可执行性验证
- **预期证据**: 完成的用户指南和开发者指南
- **完成条件**:
  - 用户指南覆盖所有用户操作
  - 开发者指南覆盖扩展开发
  - AGENTS.md 约定中心完整

---

## 6. 依赖与关键路径

### 6.1 依赖图

```
T1 (Spike) ──────────────────────────────────────────────────────────┐
  │                                                                   │
  ├──> T2 (技术栈) ──┐                                               │
  │                   ├──> T4 (存储基础) ──┬──> T5 (Session Mgr)     │
  ├──> T3 (目录+契约) ┘                    │      │    │              │
  │                                        │      │    ├──> T7 (Checkpoint) ──> T9 (A-B Sync)
  │                                        │      │    │                        │
  │                                        │      │    └──> T13 (Host Adapter) │
  │                                        │      │                             │
  │                                        ├──> T6 (State Machine) ──┐        │
  │                                        │       │                  │        │
  │                                        │       └──> T8 (Error) ──┤        │
  │                                        │                          │        │
  │                                        ├──> T10 (Knowledge) ──┐  │        │
  │                                        │                       ├──┤        │
  │                                        ├──> T11 (Experience) ──┘  │        │
  │                                        │         │                │        │
  │                                        │         └──> T12 (知识集成) ──────┤
  │                                        │                          │        │
  │                                        ├──> T15 (Tool Reg) ──────┤        │
  │                                        │                          │        │
  │                                        └──> T17 (Version Mgr)    │        │
  │                                                                   │
  │                                        T14 (Skill Executor) <─────┘        │
  │                                               │                            │
  │                                               └──> T16 (E2E 集成) <──────┘
  │                                                      │
  │                                              ┌───────┼───────┐
  │                                              │       │       │
  │                                         T18(性能) T19(安全) T20(迁移)
  │                                              │       │       │
  │                                         T21(兼容) T22(文档)
  └──────────────────────────────────────────────────────────────────┘
```

### 6.2 关键路径

```
T1 → T2 → T4 → T5 → T7 → T9 → T16 → T18/T19/T20 → T21/T22
              T4 → T6 → T8 → T14 → T16
              T4 → T10 → T12 → T14
```

**关键路径长度**: T1 → T2 → T4 → T5 → T7 → T9 → T16 → T18（8 个串行步骤）

### 6.3 可并行的任务组

| 并行组 | 任务 | 条件 |
|--------|------|------|
| 并行组 A | T3, T2 | T1 完成后 |
| 并行组 B | T5, T6, T10, T11, T15, T17 | T4 完成后 |
| 并行组 C | T7, T8, T13 | T5/T6 完成后 |
| 并行组 D | T18, T19, T20, T21, T22 | T16 完成后 |

---

## 7. 完成定义与验证策略

### 7.1 里程碑完成定义

| 里程碑 | 完成定义 | 验证方式 |
|--------|---------|---------|
| M1 | 所有契约文件就绪 + 存储基础设施测试通过 + Spike 结论明确 | 自动化测试 + spike 报告评审 |
| M2 | Session CRUD + 状态转换 + 检查点恢复 + 错误处理全部测试通过 | 自动化测试（覆盖率 > 80%） |
| M3 | 知识 CRUD + 经验记录 + 跨模块检索测试通过 | 自动化测试 + 手动知识提取验证 |
| M4 | 端到端 workflow 测试通过 + 现有 skills 兼容 | E2E 测试 + 兼容性测试 |
| M5 | NFR 指标达标 + 迁移测试通过 + 文档完成 | 性能/安全/迁移测试 + 文档评审 |

### 7.2 Phase 1 总体完成定义

Phase 1 完成需满足以下所有条件：

1. 所有 22 个任务状态为 done
2. 单元测试覆盖率 > 80%
3. 所有 NFR 指标达标（性能、安全、可靠性）
4. 现有 26 个 AHE skills 完全兼容
5. 仓库可迁移到新环境
6. 用户文档和开发者文档完成

---

## 8. 当前活跃任务选择规则

1. **首个活跃任务**: T1（Claude Code Session API 技术验证 Spike）—— 所有后续任务的前置验证
2. **后续选择规则**:
   - 若存在且仅存在一个 ready 任务，则将其锁定为 Current Active Task
   - 若存在多个同优先级 ready 任务，则按任务 ID 升序选择（T 编号小的优先）
   - 若存在不同优先级 ready 任务，则选择最高优先级（P0 > P1 > P2 > ...）
   - 关键路径上的任务优先于非关键路径任务
3. **阻塞处理**: 若当前任务阻塞（无法推进），回到 `ahe-workflow-router` 重编排

---

## 9. 任务队列投影视图 / Task Board Path

### Task Board

```markdown
# Task Board

- Source Task Plan: docs/tasks/2026-04-15-garage-agent-os-tasks.md
- Current Active Task: T1

## Task Queue

| Task ID | Status | Depends On | Ready When | Selection Priority | Milestone |
|---------|--------|------------|------------|-------------------|-----------|
| T1  | ready     | -           | 设计已批准                | P0 | M1 |
| T2  | pending   | T1          | T1=done                   | P1 | M1 |
| T3  | pending   | T1          | T1=done                   | P1 | M1 |
| T4  | pending   | T2, T3      | T2=done AND T3=done       | P1 | M1 |
| T5  | pending   | T4          | T4=done                   | P2 | M2 |
| T6  | pending   | T4          | T4=done                   | P2 | M2 |
| T7  | pending   | T5, T6      | T5=done AND T6=done       | P2 | M2 |
| T8  | pending   | T4, T6      | T4=done AND T6=done       | P2 | M2 |
| T9  | pending   | T5, T7      | T5=done AND T7=done       | P2 | M2 |
| T10 | pending   | T4          | T4=done                   | P3 | M3 |
| T11 | pending   | T4          | T4=done                   | P3 | M3 |
| T12 | pending   | T10, T11    | T10=done AND T11=done     | P3 | M3 |
| T13 | pending   | T1, T4, T5  | T1=done AND T4=done AND T5=done | P3 | M4 |
| T14 | pending   | T4-T8,T12   | M2+M3 核心=done           | P4 | M4 |
| T15 | pending   | T4          | T4=done                   | P3 | M4 |
| T16 | pending   | T5-T9,T13-T15 | 所有 M2+M3+M4 前置=done | P5 | M4 |
| T17 | pending   | T3, T4      | T3=done AND T4=done       | P3 | M4 |
| T18 | pending   | T16         | T16=done                  | P5 | M5 |
| T19 | pending   | T15, T16    | T15=done AND T16=done     | P5 | M5 |
| T20 | pending   | T16         | T16=done                  | P5 | M5 |
| T21 | pending   | T16         | T16=done                  | P5 | M5 |
| T22 | pending   | T16         | T16=done                  | P5 | M5 |
```

---

## 10. 风险与顺序说明

### 10.1 高风险任务

| 任务 | 风险 | 缓解 |
|------|------|------|
| **T1** (Spike) | Claude Code API 可能不支持 ASM-EXT-001 假设 | 回退到纯 artifact-first 文件方案；Host Adapter 仅做文件读写 |
| **T2** (技术栈) | 选型可能导致后期重构 | 选择与现有仓库（markdown/JSON）最契合的方案 |
| **T7** (Checkpoint 恢复) | 降级恢复路径复杂 | 先实现最简路径（直接恢复），逐步增加降级 |
| **T16** (E2E 集成) | 模块间接口不匹配 | 早期定义类型接口（T4），持续集成验证 |

### 10.2 顺序依赖说明

- T1 必须最先执行：所有后续设计决策依赖 spike 结论
- T2 和 T3 可并行：技术栈选型和目录结构互不依赖
- T4 是核心枢纽：存储基础设施被所有后续模块依赖
- M3（知识模块）可与 M2（运行时核心）部分并行：T10/T11 只依赖 T4
- M4（集成）必须等待 M2+M3 完成：Skill Executor 需要所有核心模块
- M5（加固）在 E2E 集成后执行：需要完整系统才能验证 NFR

### 10.3 隐藏假设与缓解

| 假设 | 依赖任务 | 缓解措施 |
|------|---------|---------|
| ASM-EXT-001: Host Adapter 能读写 Claude Code session | T1, T13 | Spike 验证；回退方案 |
| 技术栈与 Claude Code 兼容 | T2 | 选型时评估 |
| 文件系统性能在 <1000 条目时足够 | T18 | 性能基线验证；预留数据库迁移点 |
| Solo creator 场景无并发问题 | T5, T7 | 文件锁保护；单 session 限制 |

---

**文档状态**：草稿，待 ahe-tasks-review 评审

**下一步**：提交评审（ahe-tasks-review）
