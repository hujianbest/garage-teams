# D020: AHE Workflow Skill Anatomy

- Design ID: `D020`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 描述 `packs/coding/skills/ahe-*/SKILL.md` 的目标态 anatomy，为 AHE workflow skills 的新增、重写和统一提供稳定的子系统设计基线。
- 关联文档:
  - `docs/README.md`
  - `docs/wiki/W140-ahe-platform-first-multi-agent-architecture.md`
  - `docs/design/D120-garage-coding-pack-design.md`
  - `docs/wiki/W120-ahe-workflow-externalization-guide.md`

## 定位

本文描述 `packs/coding/skills/ahe-*/SKILL.md` 的目标态 anatomy。

它的用途不是复述当前 AHE 的实现细节，而是为后续新增、重写和统一 `ahe-*` skills 提供一份更稳定的设计基线。当前仓库里的 live skills 可能尚未完全达标；本文应被视为 north star，而不是现状说明。

本文是维护者文档，不是 runtime 入口。

## 设计目标

AHE workflow skills 的目标态，应同时满足以下几点：

1. `Process over reference`
当前 skill 首先是可执行 workflow，而不是一篇解释概念的资料文档。

2. `Standalone + chainable`
单个 skill 既能在用户直接点名时独立工作，也能在 workflow 链路中被上游 skill 或 orchestrator 串联进入。

3. `Evidence over assumption`
skill 的完成条件应该可被证据验证，而不是依赖“应该已经完成”“看起来没问题”。

4. `One skill, one responsibility`
一个 skill 应聚焦一个节点职责，而不是把多个并列节点揉成一个“大而全”入口。

5. `Progressive disclosure`
主 `SKILL.md` 负责让 agent 做对事；长案例、矩阵、模板扩展和背景资料应按需下沉到 supporting files。

6. `Token-conscious`
如果某段内容不会改变 agent 的行为，就不应长时间占据主文件上下文。

## 文件结构

目标态目录结构如下：

```text
packs/coding/skills/
  ahe-skill-name/
    SKILL.md
    references/
      reference-file.md
    scripts/
      helper-script.py
    assets/
      template-file.ext
```

规则：

- `SKILL.md` 是唯一必需文件。
- `references/` 用于按需加载的说明材料。
- `scripts/` 只用于稳定、重复、确定性的辅助步骤。
- `assets/` 只在 skill 需要模板、样板文件或输出素材时引入。

## Frontmatter

每个 `ahe-*` skill 的 frontmatter 至少包含：

```yaml
---
name: ahe-skill-name
description: What the skill does. Use when [specific trigger conditions], including when the user names this skill directly or when the current workflow step clearly calls for it.
---
```

要求：

- `name` 必须与目录名一致。
- `description` 必须同时说明 `what` 和 `when`。
- `description` 的重点是触发语义，不是流程摘要。
- `description` 应覆盖 direct invoke 的典型触发条件，而不是只描述它在主链中的位置。
- 若 skill 很容易被误用，`description` 应加入边界或 exclusion 线索。
- 不要把大量流程步骤塞进 `description`，否则 agent 可能只读 frontmatter 而跳过正文。

## 标准章节

参考通用 `skill-anatomy.md`，AHE 的目标态 `SKILL.md` 应优先围绕以下章节组织。

```markdown
# Skill Title

## Overview
一句到两句，说明当前 skill 做什么、为什么重要。

## When to Use
- 何时使用
- 何时不要使用
- direct invoke 的常见触发信号

## Workflow
按步骤或阶段写清核心流程。

## Output Contract
说明输出、记录、handoff 和 next action。

## Common Rationalizations
列出 agent 容易用来跳步的借口，以及为什么这些借口不成立。

## Red Flags
列出能观察到的失真信号或违规信号。

## Verification
给出可验证的退出条件和证据要求。
```

以下章节按需加入：

- `Inputs / Required Artifacts`
- `Techniques / Variants`
- `Examples`
- `Supporting References`

## 章节目的

### Overview

回答两个问题：

- 这个 skill 负责什么
- 为什么应该按它的方式执行

它不是长背景说明，也不是设计论文摘要。

### When to Use

这是 skill 的第一道分流面。它至少应说明：

- 正向触发条件
- 反向边界，避免误触发
- direct invoke 时什么情况可直接进入本 skill

目标态不是要求所有 skill 都写成同一句式，而是要求使用者在读完这里后，能判断“现在该不该用它”。

### Workflow

这是 skill 的核心。要求：

- 可执行
- 有顺序
- 有决策点时给出明确判断
- 尽量避免空泛措辞

好写法是“做什么 + 如何确认做到了”，而不是“注意质量”“确保正确”。

### Output Contract

这是 AHE 相对通用 skill anatomy 的重要扩展。它应该回答：

- 本 skill 产出什么
- 产出给谁消费
- 如何表达下一步
- 什么交回 orchestrator，什么由本节点自行完成

### Common Rationalizations

这是防止 skill 被“表面执行”的关键章节。优先写那些 agent 最容易说出口的借口，例如：

- “这一步看起来很简单，可以省略”
- “当前信息不全，我先假设一个版本继续”
- “后面再补验证也不影响”

每条 rationalization 都应配一条现实反驳。

### Red Flags

Red flags 应聚焦可观察行为，而不是抽象价值判断。例如：

- 没有证据却宣称完成
- 没有写 handoff 却建议进入下一节点
- 用自然语言替代明确结论

### Verification

Verification 是 skill 的退出条件，而不是礼貌性 checklist。

每一项都应尽量对应可见证据，例如：

- 测试输出
- 评审结论
- 记录路径
- 工件状态
- 明确的 handoff

## 双模式调用设计

双模式调用是 AHE target state 的家族级要求，但不要求所有 skill 都使用完全相同的标题名称。

换句话说，要求的是语义清晰，而不是机械套标题。

当前 live family 对“什么时候走公开入口 / router、什么时候允许 direct invoke”的入口约定，集中维护在 `packs/coding/skills/docs/ahe-workflow-entrypoints.md`。

### `standalone contract`

当用户直接点名某个 `ahe-*` skill 时，skill 至少应明确：

- 何时可以直接执行
- 最少需要什么输入或工件
- 哪些前置条件不满足时不能强行继续
- 是否需要回到 orchestrator 或上游步骤

### `chain contract`

当当前 skill 作为链路节点被带入时，skill 至少应明确：

- 默认从哪些上游输入读取上下文
- 本节点消费哪些证据
- 本节点写回哪些输出
- 如何表达 canonical next action

### 设计约束

- direct invoke 不等于可以绕过前置条件。
- chain invoke 不等于可以省略 handoff。
- skill 可以完成“本节点职责”，但不应私自吞掉上下游边界。
- orchestrator skill 是双模式设计里的特殊角色，但不应成为其它 skill 不写清本地 contract 的理由。

## AHE 家族级约定

这一节只保留真正属于 family-level 的约束，不把当前仓库的实现细节固化进 anatomy。

当前 live family 的共享写法与字段约定，集中维护在 `packs/coding/skills/docs/ahe-workflow-shared-conventions.md`。

### 1. Evidence-first

所有 AHE skills 都应优先基于可见证据推进，而不是基于印象推进。

如果一个 skill 的完成判定、交接判定或 reroute 判定无法落到证据上，它的写法通常还不够成熟。

### 2. Canonical verdict

review 或 gate 类 skills 应使用一套稳定 verdict vocabulary。

默认建议值：

- `通过`
- `需修改`
- `阻塞`

如项目需要英文映射，可对应：

- `pass`
- `revise`
- `blocked`

关键不是语言，而是一致性。不要在同一 family 中随意混用一堆近义词。

### 3. Canonical handoff

如果 skill 需要表达下一步，优先使用稳定的 skill ID 或等价 canonical action，而不是含糊自然语言。

例如：

- 推荐下游 skill 时，用明确 skill 名
- workflow 结束时，用项目约定的空值或终止表达
- 不用 `done`、`继续推进`、`看情况` 一类模糊文本替代 handoff

### 4. Progress schema should be stable

若 workflow 依赖状态工件或 progress 记录驱动，字段名应稳定，且模板与 live skills 保持一致。

anatomy 文档应定义字段语义，不应绑定某个当前模板的临时写法。

### 5. Artifact types beat hard-coded paths

anatomy 更适合定义“规格文档”“设计文档”“评审记录”“验证记录”“进度记录”这类工件类型，而不是把当前仓库的具体路径直接写成不可动摇的结构真理。

路径映射、模板路径和项目级目录约定，优先放在：

- 项目级配置
- supporting references
- 专门的 adoption / setup 文档

而不是塞进 family anatomy 主文。

## 技能原型

目标态 anatomy 不应与当前技能清单一一绑定，但可以按常见 archetype 提供写作偏重。

### Orchestrator

例如当前由 `ahe-workflow-router`（runtime 恢复与编排）与 `using-ahe-workflow`（公开家族入口）分工承担、合起来覆盖的旧式单一 orchestrator 角色。

写作重点：

- 路由判断
- 进入条件
- 恢复编排
- 什么时候把控制权交给节点 skill

### Producer

负责产出规格、设计、任务或实现结果的技能。

写作重点：

- 输入要求
- 产出形态
- 下游消费方式
- 本节点完成标准

### Reviewer

负责发现问题、给出 verdict 和形成评审记录的技能。

写作重点：

- 评审范围
- 发现项结构
- verdict 规则
- 什么时候 reroute 而不是继续判断

### Gate

负责合并证据、判断是否可继续推进的技能。

写作重点：

- 消费哪些证据
- 什么叫 pass / revise / blocked
- 哪些缺口必须阻塞

### Finalizer

负责收口、交付、closeout 的技能。

写作重点：

- 需要收敛哪些状态
- 需要汇总哪些证据
- 交付包或 closeout 输出长什么样

### Branch / Re-entry

负责增量、热修或回流节点的技能。

写作重点：

- 从哪里分岔
- 满足什么条件后重新并回主链
- 对上游和下游的边界约束

## Supporting files

只有在 supporting content 会明显改善主文件可读性时，才拆到 `references/`、`scripts/` 或 `assets/`。

优先留在主 `SKILL.md` 的内容：

- 触发条件
- 关键 workflow
- 输出 / handoff 规则
- verification
- 红旗与 rationalizations

优先下沉到 supporting files 的内容：

- 长案例
- 大型矩阵
- 详细模板说明
- 领域变体
- 重复执行的辅助脚本

经验规则：

- 主 `SKILL.md` 最好保持紧凑，接近 500 行时就应考虑分层
- 超长 reference file 应带目录或清晰导航
- 不要把“真正影响行为的规则”全丢进 supporting files

## 写作原则

1. 解释 why，而不只是堆砌 MUST。
2. 用流程驱动行为，而不是用口号驱动行为。
3. 具体胜过抽象，证据胜过印象。
4. 对容易被跳过的关键步骤，优先写进 rationalizations 或 verification。
5. 尽量引用其它 skill 或 supporting file，而不是跨文件重复复制。
6. 不要让 anatomy 被当前实现偶然性反向绑架。

## 目标态检查清单

在新增或重写 `ahe-*` skill 时，至少检查：

- `description` 是否同时说明了 what 与 when
- `When to Use` 是否覆盖正向触发和反向边界
- direct invoke 的前置条件是否清楚
- chain invoke 的输入与 handoff 是否清楚
- `Workflow` 是否足够具体，能真正执行
- `Output Contract` 是否明确写出产物与 next action
- `Common Rationalizations` 是否覆盖最可能的跳步借口
- `Red Flags` 是否可观察
- `Verification` 是否以证据为中心
- supporting files 是否真正承担了 progressive disclosure，而不是藏关键规则
- 文档是否定义了工件类型，而不是被当前路径结构绑死

## 一句话约束

AHE 的目标态 anatomy，不是把所有 skill 写成同一个模板，也不是把当前实现原样上升为标准；它要做的是定义一套更稳定的 skill 设计语言，让每个节点都既能独立被正确调用，也能在链路中被稳定编排。
