# Garage 架构设计原则指南

- 定位: 面向 docs-first、workspace-first、Agent-native 项目的架构判断指南
- 适用: Garage Agent 操作系统及相关 pack 设计
- 日期: 2026-04-15

---

## 文档说明

这不是一份教科书式的通用原则清单（SOLID、DRY、KISS 等原则不在这里重复）。这是一份**面向特定项目类型的判断指南**——当设计师面对具体架构决策时，用它来判断方案好坏。

### 项目类型特征

- **docs-first**: 核心产出是文档和约定，不是代码
- **workspace-first**: 所有数据在 git 仓库内，不依赖外部服务
- **Agent-native**: 系统的主要用户是 AI Agent，不是传统 GUI 用户
- **Solo-creator**: 一个人使用和维护
- **渐进演进**: 从最简形态开始，逐步增强

---

## 原则 1：宿主无关原则

### 定义

核心能力和约定定义在 Garage 层面，不绑定任何单一宿主（Claude Code、Hermes、Cursor 等）。宿主只是运行时适配层，可以随时替换。

### 判定标准

**移除当前宿主后，核心约定和数据是否仍然完整可理解？**

如果一个设计必须依赖 Claude Code 的特定 API 或行为才能理解，那它就违反了本原则。

### 正确示例 vs 错误示例

**✅ 正确示例：Platform-Neutral Contract**

```yaml
# contracts/workflow-session.yaml
packId: ahe-coding
graphVariantId: standard
executionMode: markdown-first
requiredApprovals:
  - specApproval
  - designApproval
```

这个 contract 没有任何宿主特定术语。任何宿主都能理解它。

**❌ 错误示例：硬编码宿主行为**

```yaml
# 设计依赖 Claude Code 特定 API
claudeCodeSession:
  sessionMemory: "use Claude Code 的 session 状态"
  toolInvocation: "通过 /skill-name 命令触发"
```

这种设计无法迁移到其他宿主。

### 常见偷懒借口和反驳

| 偷懒借口 | 反驳 |
|---------|------|
| "反正现阶段只用 Claude Code" | 宿主是**执行环境**，不是**系统定义**。混在一起会让未来的迁移成本指数级增长 |
| "抽象一层太复杂了" | 宿主适配层应该**一次设计**，不是每个 skill 都重新发明一遍 |
| "Claude Code 的 API 很方便，直接用吧" | 今天的"方便"是明天的"vendor lock-in"。所有宿主特定内容必须通过 adapter 消化 |
| "等真要换宿主时再抽象" | 到那时重构成本会远超现在的抽象成本，而且可能已经积累了大量无法迁移的历史数据 |

---

## 原则 2：文件即契约原则

### 定义

文件结构、目录约定、front matter schema 就是 API。变更这些就是 breaking change，必须像对待代码 API 一样严肃。

### 判定标准

**一个全新的 Agent 读取这些文件后，能否正确理解系统状态并操作？**

如果 Agent 需要阅读外部文档或隐式知识才能理解文件含义，就违反了本原则。

### 正确示例 vs 错误示例

**✅ 正确示例：Self-Describing Spec Document**

```markdown
---
status: 草稿
topic: Garage Agent 操作系统
date: 2026-04-15
spec_id: F001
pack: ahe-coding
required_approvals:
  - specApproval
next_skill: ahe-design-review
---

# F001: Garage Agent 操作系统

## 1. 背景与问题陈述
...
```

Agent 读取这个文件时能直接知道：
- 这是草稿状态
- 需要 specApproval
- 下一站是 ahe-design-review

**✅ 正确示例：Explicit Directory Convention**

```
contracts/
├── workflow-session.yaml    # session contract
├── node-definition.yaml      # node contract
└── artifact-surface.yaml     # artifact contract
```

每个文件的角色通过命名和位置明确表达。

**❌ 错误示例：Implicit Convention**

```
# 某个 skill 文档
"状态记录应该放在 task-progress.md 中，这个是大家都知道的约定"
```

Agent 无法从文件本身推断出这个约定，必须依赖外部知识。

**❌ 错误示例：Silent Breaking Change**

```markdown
# 之前的格式
status: 草稿
required_approvals: [specApproval]

# 新格式（breaking change，但文档没更新）
state: draft
approval_gates:
  - type: spec
    status: pending
```

这种变更会让历史数据无法被新 Agent 正确读取。

### 常见偷懒借口和反驳

| 偷懒借口 | 反驳 |
|---------|------|
| "约定大家都懂，不用写那么清楚" | Agent 没有"大家懂"这种隐式知识。所有约定必须**显式化** |
| "这只是个小调整，不算 breaking change" | 在 Agent-native 系统，任何 schema 变更都是 breaking change。需要版本管理 |
| "文档里已经写清楚了，文件里不用重复" | docs-first 不意味着"文件外有真相"。文件本身必须包含足够元信息 |
| "等稳定后再规范化格式" | 格式不规范，Agent 就无法可靠理解。这会阻塞所有自动化能力 |

---

## 原则 3：渐进复杂度原则

### 定义

设计方案必须分层，从最小可用形态到完整形态有明确路径。第一天零配置必须能工作，每增加一层复杂度必须有明确触发条件。

### 判定标准

**第一天零配置能否工作？每增加一层复杂度的触发条件是什么？**

如果一个设计第一天就需要大量配置才能跑起来，它就违反了本原则。

### 正确示例 vs 错误示例

**✅ 正确示例：Layered Knowledge Storage**

Phase 1（第一天）：
```markdown
# .garage/knowledge/decision-001.md
---
type: decision
topic: "选择 markdown 作为知识存储格式"
date: 2026-04-15
rationale: "人机可读、git 可追踪、零配置"
---

## 决策内容
...
```

Phase 2（当知识条目 >100 时）：
```markdown
# .garage/knowledge/index.md
# 自动生成的索引，支持快速检索
```

Phase 3（当知识条目 >1000 时）：
```json
// .garage/knowledge/.metadata/index.json
// 结构化索引，支持复杂查询
```

每个阶段都有明确触发条件，且向后兼容。

**❌ 错误示例：All-or-Nothing Design**

```yaml
# 第一天就必须配置完整
knowledge_store:
  type: elasticsearch  # 需要额外部署
  index_strategy: complex
  cache_layer: redis   # 需要额外部署
  replication: true
```

这种设计第一天无法使用，违背了渐进演进原则。

**❌ 错误示例：Undefined Upgrade Path**

```markdown
# 文档说"先简单实现，以后再优化"
# 但没有说明什么时候触发"优化"
# 也没有说明"优化"后的形态是否兼容
```

没有明确演进路径的设计，会陷入"永远不优化"或"突然大重构"的两极。

### 常见偷懒借口和反驳

| 偷懒借口 | 反驳 |
|---------|------|
| "先做一个完整的，后面再简化" | **反过来了**。应该从最简开始，明确什么条件触发下一层复杂度 |
| "现在的方案够用，不用考虑未来" | 设计必须包含**演进路径**。不然当规模增长时，会面临痛苦的大重构 |
| "定义这么多阶段太麻烦了" | 不定义阶段，后期会有更多麻烦。要么永远停留在 Phase 1，要么在不知道如何演进时被迫重构 |
| "等真遇到性能问题再优化" | 没有演进路径的设计，优化时往往要破坏已有结构。必须提前设计好"如何在不破坏兼容性的前提下升级" |

---

## 原则 4：自描述原则

### 定义

所有文件和目录必须包含足够元信息让 Agent 理解其含义和用法。不应该存在"看文件本身不知道干什么，必须看外部文档"的情况。

### 判定标准

**去掉所有外部文档后，Agent 仅凭读取文件本身能否正确使用？**

如果 Agent 必须读取 README 或其他外部文档才能理解文件，就违反了本原则。

### 正确示例 vs 错误示例

**✅ 正确示例：Self-Describing Skill**

```markdown
---
name: ahe-design
description: 产出可评审实现设计
trigger_conditions:
  - 需求规格已批准
  - 设计尚未批准
  - 当前需要在任务规划前明确架构
inputs:
  - 已批准的需求规格
  - AGENTS.md 中的设计约束
outputs:
  - 可评审设计草稿
  - canonical handoff: ahe-design-review
hard_gates:
  - 在设计经过评审并获批之前，不得拆解任务或编写实现代码
---

# AHE 设计
...
```

Agent 读取这个文件的 front matter 就能知道：
- 什么时候用这个 skill
- 需要什么输入
- 会产出什么
- 有什么硬性约束

**✅ 正确示例：Directory with README**

```
contracts/
├── README.md                 # 说明这个目录的用途和约定
├── workflow-session.yaml
└── node-definition.yaml
```

每个关键目录都有 README 说明其角色。

**❌ 错误示例：Implicit Semantics**

```
# packs/coding/skills/cool-skill.md
# 文档里没有任何 front matter
# Agent 不知道什么时候用它、需要什么输入、会产出什么
```

Agent 必须阅读其他文档才能理解这个 skill。

**❌ 错误示例：Undecipherable Directory**

```
.stuff/
├── things/
│   └── item1.dat
└── more/
    └── x.json
```

没有 README，没有 front matter，Agent 无法理解这些文件的用途。

### 常见偷懒借口和反驳

| 偷懒借口 | 反驳 |
|---------|------|
| "项目里已经有文档说明了，不用每个文件都写" | Agent-native 系统中，Agent 应该能**独立理解**每个文件，而不是跨文件拼凑理解 |
| "front matter 太占地方了" | front matter 是**契约的一部分**，不是可选的装饰。缺少 front matter 的文件对 Agent 来说是不可用的 |
| "这个目录名字很清楚，不需要 README" | "清楚"是人类的主观判断。Agent 需要显式的语义声明 |
| "等稳定后再补 front matter" | 没有 front matter，Agent 就无法可靠使用。这会阻塞所有自动化能力 |

---

## 原则 5：约定可发现原则

### 定义

默认零配置工作，但所有约定必须在一个可发现的位置集中描述。新 Agent 第一次遇到系统，应该能在 5 分钟内找到所有约定的中心位置。

### 判定标准

**新 Agent 第一次遇到系统，从哪里知道有哪些约定？能在 5 分钟内找到吗？**

如果约定散落在多个地方，或者没有明确入口，就违反了本原则。

### 正确示例 vs 错误示例

**✅ 正确示例：Single Source of Truth**

```markdown
# AGENTS.md（项目根目录）

## 约定中心

所有项目级约定在本文件中定义。

### 路径映射
- 规格文档: `docs/features/`
- 设计文档: `docs/designs/`
- 知识库: `.garage/knowledge/`

### 审批等价证据
- specApproval: `docs/features/<id>.md` 中 `状态: 已批准`
- designApproval: `docs/designs/<topic>-design.md` 中 `状态: 已批准`

### 禁并发规则
- 同一个 spec 只能有一个活跃 design 任务
- 同一个 design 只能有一个活跃 tasks 任务

### 模板覆盖
- 使用自定义规格模板: `templates/spec-template.md`
- 使用自定义设计模板: `templates/design-template.md`
```

所有约定集中在一个文件，且文件位置是标准的（项目根目录的 AGENTS.md）。

**✅ 正确示例：Discoverable Convention Chain**

```markdown
# AGENTS.md
完整约定见本文件。

# packs/coding/skills/README.md
AHE Coding Pack 的约定见本文件。
- pack-local 路径映射
- pack-local 审批规则
- pack-local 模板

# docs/features/F001-xxx.md
具体规格的约定见本文件 front matter。
```

分层约定，但每一层都指向下一层的位置。

**❌ 错误示例：Scattered Conventions**

```markdown
# 路径约定在 README.md
# 审批规则在某个 wiki 页面
# 模板在 templates/ 目录但没说明
# pack 约定在各个 skill 文档里分散描述
```

Agent 无法在 5 分钟内找到所有约定。

**❌ 错误示例：Undiscoverable Entry Point**

```markdown
# 某个 pack 的约定在 packs/coding/skills/ahe-design/references/conventions.md
# 但没有任何入口指向这里
```

约定存在，但无法被新 Agent 发现。

### 常见偷懒借口和反驳

| 偷懒借口 | 反驳 |
|---------|------|
| "约定都写在文档里了，慢慢找就行" | Agent-native 系统中，约定必须是**可发现**的。"慢慢找"意味着自动化能力受限 |
| "AGENTS.md 太长了，把部分内容移到其他文件" | AGENTS.md 应该是**入口**，可以链接到其他文件，但必须提供清晰的目录结构 |
| "每个 pack 自己管理自己的约定" | 项目级约定和 pack-local 约定应该分开。但必须有明确的"约定中心"说明这种分层 |
| "新 Agent 可以先阅读所有文档" | 这违背了**可发现性**原则。5 分钟内找不到约定中心，说明设计有问题 |

---

## 原则之间的 Trade-off 指南

### 优先级排序

当原则之间冲突时，按以下优先级进行取舍：

1. **宿主无关原则**（最高优先级）
   - 原因：一旦绑定宿主，后续迁移成本极高
   - 典型场景：是否使用宿主特定 API

2. **文件即契约原则**
   - 原因：契约是系统理解的基石
   - 典型场景：是否需要显式声明文件格式

3. **约定可发现原则**
   - 原因：不可发现的约定等于不存在
   - 典型场景：约定是否集中管理

4. **自描述原则**
   - 原因：自描述是 Agent 理解的基础
   - 典型场景：文件是否包含足够元信息

5. **渐进复杂度原则**
   - 原因：演进是必要的，但可以适当妥协
   - 典型场景：是否需要第一天就支持完整功能

### 典型冲突场景

#### 场景 1：自描述 vs 渐进复杂度

**冲突**：自描述要求每个文件都有完整的 front matter（增加复杂度），渐进复杂度要求第一天最简（减少 front matter）。

**建议方案**：
- Phase 1：定义**最小 front matter schema**，只包含必需字段（name、description、status）
- Phase 2：当技能数量 >10 时，增加 trigger_conditions、inputs、outputs 字段
- 关键：即使是最小 schema，也必须保证**向后兼容**

#### 场景 2：宿主无关 vs 快速实现

**冲突**：宿主无关要求抽象适配层（增加开发成本），快速实现要求直接用宿主 API（节省时间）。

**建议方案**：
- 永远优先选择**宿主无关**
- 如果时间紧急，可以**先做适配层的 stub**，后续填充实现
- 关键：**不要在 contract 层引入宿主特定术语**

#### 场景 3：文件即契约 vs 文档可读性

**冲突**：文件即契约要求显式声明所有内容（增加冗余），文档可读性要求简洁（减少重复）。

**建议方案**：
- 在 front matter 中声明**机器可读的契约**
- 在正文部分提供**人类可读的说明**
- 两者可以有重复，因为它们服务于不同的"读者"（Agent vs 人类）

---

## 反模式清单

### 反模式 1：宿主特定术语泄漏到 Contract

**检测信号**：
- 平台 schema 中出现 `claudeCode`、`hermes`、`cursor` 等宿主名称
- contract 定义依赖宿主特定 API 行为
- 文档中说"这个行为和 Claude Code 的 X 一样"

**问题**：
- 违反宿主无关原则
- 后续迁移需要重写所有 contract

**正确做法**：
- 平台层只定义中立术语
- 宿主特定行为通过 adapter 消化
- 在 adapter 文档中说明宿主映射关系

---

### 反模式 2：隐式约定散落各处

**检测信号**：
- 约定在 README、wiki、各个文档中重复描述
- 没有明确的"约定中心"
- 新 Agent 需要阅读 5+ 文件才能找到所有约定

**问题**：
- 违反约定可发现原则
- Agent 无法可靠理解系统
- 约定更新时容易遗漏某些地方

**正确做法**：
- 在 AGENTS.md 中集中所有项目级约定
- 在 pack README.md 中集中 pack-local 约定
- 其他地方链接到这些中心位置

---

### 反模式 3：文件缺少 Self-Describing 元信息

**检测信号**：
- skill 文档没有 front matter
- 数据文件没有 schema 说明
- 目录没有 README.md

**问题**：
- 违反自描述原则
- Agent 无法独立理解文件
- 自动化能力受限

**正确做法**：
- 每个 skill 文档必须有完整的 front matter
- 每个数据文件必须在文件内或同目录 README 中说明 schema
- 每个关键目录必须有 README.md

---

### 反模式 4：第一天就追求完整形态

**检测信号**：
- Phase 1 就引入数据库、缓存、复杂索引
- 设计文档说"先做完整版，以后再简化"
- 没有"什么条件下进入 Phase 2"的说明

**问题**：
- 违反渐进复杂度原则
- 第一天无法使用
- 过度设计浪费开发时间

**正确做法**：
- 从最简可用形态开始（通常是 markdown + 文件系统）
- 明确每个阶段的触发条件
- 保证向后兼容的升级路径

---

### 反模式 5：Silent Breaking Change

**检测信号**：
- schema 变更但没有更新版本号
- 文件格式变化但没有提供迁移脚本
- 文档说"格式调整了一下，应该没问题"

**问题**：
- 违反文件即契约原则
- 历史数据无法被新 Agent 读取
- 破坏可迁移性

**正确做法**：
- 所有 schema 变更必须有版本号
- 提供自动化的迁移脚本
- 在 AGENTS.md 中记录所有 breaking changes

---

### 反模式 6：用"大家都懂"替代显式约定

**检测信号**：
- 文档中说"这是显而易见的"
- 代码注释说"没必要写这么清楚"
- 约定只在口头或聊天记录中

**问题**：
- Agent 没有"大家都懂"这种隐式知识
- 新人无法理解系统
- 约定无法传承

**正确做法**：
- 所有约定必须显式化
- "显而易见"的东西更需要写清楚
- 文档是给 Agent 和未来的自己看的

---

## 结语

这些原则是 Garage 项目的架构判断指南，不是僵硬的教条。在实际应用中：

1. **用原则判断方案**：当面临多个方案时，用这些原则来判断哪个更好
2. **用原则检测问题**：当出现问题时，检查是否违反了某条原则
3. **用原则指导演进**：当系统需要演进时，确保演进方向符合这些原则
4. **用原则统一语言**：用原则名称来高效沟通（如"这违反了宿主无关原则"）

记住：这些原则的目标是让 Garage 成为一个**可迁移、可理解、可演进**的 Agent 操作系统。每个原则都服务于这个目标。

---

**相关文档**：
- `docs/features/F001-garage-agent-operating-system.md` - Garage Agent 操作系统规格
- `docs/wiki/W140-ahe-platform-first-multi-agent-architecture.md` - 平台优先架构分析
- `AGENTS.md` - 项目约定中心
