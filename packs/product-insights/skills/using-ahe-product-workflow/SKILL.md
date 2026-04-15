---
name: using-ahe-product-workflow
description: 适用于用户有模糊产品想法或已上线产品感觉平庸、需要判断应进入哪个 product insight 节点的场景。不适用于已有稳定规格只需继续实现（→ ahe-coding-skills）或只需回答局部技术问题的场景。
---

# Using AHE Product Workflow

负责作为 product insight family 的公开入口——判断当前更缺问题定义、外部信号、机会排序、概念方向、验证探针还是 spec bridge。不替代任何具体 insight 节点，也不替代 coding family。

## When to Use

**正向触发：**
- 用户只有一个模糊产品想法，不知道真正的机会在哪里
- 项目已经做完，但"很一般""没吸引力"，需要重写问题定义
- 用户说"先别写代码，先帮我想清楚产品洞察"
- 需要判断现在该进入哪一个 product insight 节点
- 想把上游创造性工作和 `ahe-coding-skills` 实现链路分开

**不适用：**
- 已经有稳定需求规格，当前只是要继续写设计、任务或实现
- 当前只是要求 `ahe-coding-skills` 节点级工作
- 当前只是回答一个局部技术问题

**Direct invoke：** 用户首次提及 product insight 相关需求，或从 `ahe-coding-skills` 回退到产品层面。

**相邻边界：** 与 `ahe-coding-skills` 的分界线：本 family 负责"产品洞察"，coding family 负责"精确实现"。一旦 insight 足够清晰并需要正式 spec，应通过 `ahe-spec-bridge` 交接。

## Workflow

### 1. 先读取用户当前已有的项目材料

检查项目中已有的 insight 文档、spec、设计文档等，判断当前 state。

### 2. 根据 state 选择目标节点

按以下规则判断：

#### 进入 `ahe-outcome-framing`

满足任一条件即可：

- 用户的描述仍停留在"我要做一个 X"
- 还说不清 desired outcome、目标用户、当前替代方案或非目标
- 项目"为什么不吸引人"还停留在感觉层

#### 进入 `ahe-insight-mining`

满足任一条件即可：

- 已经有想法，但缺真实外部信号来判断是否 commodity
- 需要从 web、GitHub、社区、替代品和现有材料中提取证据
- 需要形成 insight pack，而不是直接想 feature

#### 进入 `ahe-opportunity-mapping`

满足任一条件即可：

- 已有一定 evidence，需要收敛 JTBD / opportunity / wedge 视图
- 需要判断"先打哪个机会，而不是先做哪个功能"

#### 进入 `ahe-concept-shaping`

满足任一条件即可：

- 已选机会，但解决方向仍然平庸
- 需要产生多个概念方向，并选出更有吸引力的 wedge

#### 进入 `ahe-assumption-probes`

满足任一条件即可：

- 方向看起来不错，但关键成败假设还没暴露
- 需要在写 spec 前先设计便宜验证

#### 进入 `ahe-spec-bridge`

只有在以下条件都满足时才进入：

- desired outcome、目标用户和优先机会已经清楚
- 已形成一个候选概念或 wedge
- 关键假设至少被列出来
- 当前需要把这些内容压缩成 `ahe-specify` 可消费输入

**决策点：** 若用户的问题完全不属于 product insight 范畴（如纯技术问题），明确说明不在本 family scope 内，不强行路由。

### 3. 输出路由结果

使用 3 行快路径格式。

## Output Contract

- **写什么：** 路由判断（entry classification + target skill + why）
- **写到哪里：** 无需落盘，直接在对话中输出路由结果
- **状态同步：** 使用标准 3 行格式
- **下一步：** 被选中的目标 skill

推荐快路径格式：

1. `Entry Classification`：直接写当前更缺的东西（如 `framing-first`、`research-first`、`bridge-ready`）
2. `Target Skill`：canonical skill 名
3. `Why`：只保留 1-2 条关键原因

## Shared References

按需读取：

- `../docs/product-insight-shared-conventions.md`
- `../docs/product-debate-protocol.md`
- `../docs/product-insight-foundations.md`
- `../README.md`

## Default Debate Expectation

当路由到下面节点时，默认按多 agent 讨论 / PK 方式执行：

- `ahe-insight-mining`
- `ahe-opportunity-mapping`
- `ahe-concept-shaping`

## Red Flags

- 一开始就把"做什么功能"当成唯一讨论对象
- 明明没有任何外部信号，却直接下结论说机会很大
- 还没形成差异化，就急着让 `ahe-coding-skills` 开始写规格
- 把 product insight family 用成"创意文案生成器"

## 和其他 Skill 的区别

| 对比项 | using-ahe-product-workflow | ahe-outcome-framing | ahe-spec-bridge |
|--------|---------------------------|--------------------|-----------------|
| 核心任务 | 入口路由判断 | 重写模糊 idea 为锋利问题 | 压缩为 spec 输入 |
| 输入 | 用户模糊需求 | 用户模糊 idea | 所有上游工件 |
| 输出 | 路由判断（target skill） | problem/outcome frame | spec-bridge |
| 在链路中的位置 | 最先执行（入口） | 被路由到时执行 | product 最后一站 |

本 skill 与 `ahe-workflow-router`（coding pack）的区别：本 skill 路由的是 product insight family 内部节点，`ahe-workflow-router` 路由的是 coding family 内部节点。

## Reference Guide

| 材料 | 路径 | 用途 |
|------|------|------|
| 家族 README | `../README.md` | product-insights pack 总览 |
| 产品洞察共享约定 | `../docs/product-insight-shared-conventions.md` | 家族级术语和约定 |
| 产品辩论协议 | `../docs/product-debate-protocol.md` | 多 agent 讨论规范 |
| 产品洞察基础 | `../docs/product-insight-foundations.md` | 方法论背景 |

## Verification

- [ ] 已读取用户当前项目材料
- [ ] 路由判断使用 3 行快路径格式输出
- [ ] Target Skill 是合法的 product insight 节点名
- [ ] 路由理由清楚（1-2 条关键原因）
- [ ] 若问题不在 product insight scope 内，已明确说明
