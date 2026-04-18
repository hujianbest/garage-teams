# F002: Garage Live — 引擎接入真实宿主

- 状态: 草稿
- 主题: 让 Phase 1 引擎真正跑起来
- 日期: 2026-04-16
- 关联: F001（Phase 1 引擎已完成，但未被真实使用）

## 1. 背景与问题陈述

F001 Phase 1 构建了完整的 Garage OS 引擎（Session、State Machine、Error Handler、Knowledge、Skill Executor、Host Adapter），416 个测试全部通过。但存在一个关键缺口：

**引擎还没有被真正使用过。**

具体问题：

1. **CLI 虽已存在，但链路语义未完全对齐规格**：`garage init/status/run/knowledge` 已可用，但 `run` 的 session 生命周期与规格要求仍需持续校准
2. **ClaudeCodeAdapter 已能真实调用 Claude Code，但宿主约定仍需固化**：`invoke_skill()` 已通过 `claude -p` 执行 `.agents/skills/<name>/SKILL.md`，仍需保证文档、技能布局与用户预期一致
3. **知识与 experience 已可写入，但缺少真实使用闭环验证**：`.garage/` 已能落盘真实 session / experience 数据，仍需通过稳定 demo 反复验证
4. **没有真实宿主端到端验收**：当前 E2E 主要仍依赖 mock skill / mock adapter，缺少可重复的真实 skill 执行链路验收

如果不解决这些问题，Phase 2（自动知识提取）就是在没有验证过的地基上盖楼。

## 2. 目标与成功标准

### 2.1 核心目标

让 Garage OS 引擎真正跑起来，完成一个**完整的端到端验证循环**：

```
用户输入命令 → Garage 创建 Session → 调用 Claude Code 执行 Skill →
产出 Artifact → 记录 Experience → 写入 Knowledge → 归档 Session
```

### 2.2 成功标准

1. **CLI 可用**：用户可以通过 `garage` 命令执行基本操作
2. **真实执行**：至少一个 AHE skill（如 `ahe-specify`）被真实执行并产出 artifact
3. **知识积累**：执行完成后，`.garage/` 下有真实的 session 数据和 experience 记录
4. **可重复**：同一命令可以反复执行，不报错

### 2.3 非目标

- 不追求完美的 CLI UX（Phase 3 再优化）
- 不做自动化知识提取（那是 Phase 2 / F003）
- 不引入新的架构模式（沿用 Phase 1 已有的）
- 不改 Phase 1 已有的模块接口（只补全实现）

## 3. 用户角色与关键场景

### 3.1 用户角色

- **Solo Creator**：在终端中运行 `garage` 命令，让 Garage 管理自己的工作流

### 3.2 关键场景

1. **初始化**：`garage init` — 在项目中创建 `.garage/` 目录结构
2. **执行 Skill**：`garage run ahe-specify` — 调用 Claude Code 执行指定 skill
3. **查看状态**：`garage status` — 显示当前 session 状态和知识库概要
4. **记录经验**：执行完 skill 后自动记录 experience
5. **查询知识**：`garage knowledge search <query>` — 搜索已有知识

## 4. 范围

### 4.1 包含

| 功能 | 描述 |
|------|------|
| CLI 入口 | `garage` 命令 + 子命令（init, run, status, knowledge） |
| 真实 ClaudeCodeAdapter | `invoke_skill()` 调用 `claude -p` 命令执行 skill |
| Session 管理 | run 命令创建 session，执行期间更新状态，执行完归档 |
| Experience 记录 | skill 执行后自动写入 experience record |
| 知识查询 | CLI 可搜索已有知识条目 |
| E2E Demo | 用 `ahe-specify` skill 跑通完整链路 |

### 4.2 不包含

- 自动知识提取（F003）
- Web UI
- 多宿主并行
- 性能优化（单独处理）

## 5. 功能需求

### FR-201: CLI 框架

- **FR-201a**: `garage init` — 初始化 `.garage/` 目录，创建所有子目录和配置文件
- **FR-201b**: `garage status` — 显示当前活跃 session、知识库统计、最近 experience
- **FR-201c**: `garage run <skill-name>` — 创建 session 并执行指定 skill
- **FR-201d**: `garage knowledge search <query>` — 搜索知识库

### FR-202: 真实 Claude Code 接入

- **FR-202a**: ClaudeCodeAdapter.invoke_skill() 通过 `claude -p` 调用 Claude Code
- **FR-202b**: 将 SKILL.md 内容作为 prompt 传给 Claude Code
- **FR-202c**: 捕获 Claude Code 的输出作为 skill 执行结果
- **FR-202d**: 超时和错误处理（Claude Code 进程超时、非零退出码）

### FR-203: Session 生命周期

- **FR-203a**: `garage run` 自动创建 session
- **FR-203b**: skill 执行中状态跟踪（idle → running → completed/failed）
- **FR-203c**: 执行完成后自动归档 session
- **FR-203d**: checkpoint 记录（可选，Phase 2 完善中断恢复）

### FR-204: Experience 自动记录

- **FR-204a**: skill 执行完成后，自动创建 experience record
- **FR-204b**: 记录 skill_name、耗时、状态、产出的 artifact 路径
- **FR-204c**: experience 写入 `.garage/experience/records/`

### FR-205: 知识查询 CLI

- **FR-205a**: `garage knowledge search <query>` 按关键词搜索
- **FR-205b**: `garage knowledge list` 列出所有知识条目
- **FR-205c**: 输出格式化显示（标题、类型、日期、标签）

## 6. 非功能需求

| NFR | 要求 | 验证方式 |
|-----|------|----------|
| 可用性 | CLI 命令在 5 分钟内可学会 | 新用户测试 |
| 可靠性 | Claude Code 调用失败不崩溃 | 错误注入测试 |
| 兼容性 | 不破坏 Phase 1 已有的 416 个测试 | 全量回归 |
| 依赖 | 仅依赖 Claude Code CLI（`claude` 命令可用） | 环境检查 |

## 7. 约束

- 沿用 Phase 1 的技术栈（Python 3.11+, Poetry/uv）
- CLI 框架使用 Python 标准库 `argparse`（不引入 click/tycoon）
- 真实 Claude Code 调用需要 `claude` CLI 已安装并登录
- 测试策略：mock Claude Code 调用，不依赖真实 API

## 8. 依赖

- F001 Phase 1 所有模块（已完成）
- Claude Code CLI（外部依赖，需已安装）

## 9. 开放问题

1. `claude -p` 的 token 消耗如何预估和控制？
2. skill 执行的 artifact 产出路径如何标准化？
3. 是否需要 `garage config` 命令来管理配置？
