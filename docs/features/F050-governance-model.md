# F050: Garage Phase 1 治理模型

- Feature ID: `F050`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 `Garage` 在 phase 1 的治理模型，明确规则分层、优先级、门禁语义、审批与归档边界，以及其与 `evidence`、`reference packs` 的关系。
- 当前阶段: phase 1
- 关联文档:
  - `docs/GARAGE.md`
  - `docs/architecture/A110-garage-extensible-architecture.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F010-shared-contracts.md`
  - `docs/architecture/A130-garage-continuity-memory-skill-architecture.md`
  - `docs/features/F110-reference-packs.md`
  - `docs/features/F040-session-lifecycle-and-handoffs.md`

## 1. 文档目标与范围

这篇文档只回答一个问题：

**`Garage` 在 phase 1 应该如何用统一治理模型约束 `session` 推进、工件写入、交接、审批与归档。**

本文覆盖：

- `global / core / pack / node` 四层治理
- `gate` 类型与结果语义
- `approval / review / archive / exception` 的边界
- 它们与 `Evidence`、`reference packs` 的关系

本文不覆盖：

- 复杂策略 DSL
- 组织级 RBAC
- 数据库控制面
- 具体 pack 内部 prompt 细则

## 2. 治理模型在总体架构中的位置

`Governance` 是 `Garage Core` 的稳定子系统之一。

它负责回答的问题是：

- 当前动作可不可以发生
- 还缺什么
- 谁需要确认
- 何时能进入 closeout 或 archive

它不负责：

- 生成内容
- 注册角色
- 决定工件路径

这些职责分别属于 `Session`、`Registry`、`Artifact Routing`。

`Garage` 在 phase 1 坚持：

**Governance as artifacts**

也就是说，规则、门禁、审批与归档语义应先写成工件，而不是藏在 prompt 或聊天习惯里。

## 3. 治理分层与优先级

phase 1 建议固定 4 层治理：

| 层级 | 作用 | 典型内容 |
| --- | --- | --- |
| `global` | 仓库级、系统级通用约束 | 关键动作需显式确认、关键推进必须可追溯 |
| `core` | `Garage Core` 的统一治理语义 | `session` 转移、artifact 权威写入、evidence 最小要求 |
| `pack` | 某个能力包的治理 overlay | `Coding Pack` 的 verification，`Product Insights Pack` 的 bridge 完整性 |
| `node` | 某个节点或阶段的局部门禁 | 进入条件、完成条件、handoff 条件 |

### 3.1 优先级规则

治理层级的生效方式应是：

- 从广到窄叠加
- 下层默认只能细化或收紧
- 不能静默削弱上层约束

如果出现冲突：

- 默认取更严格、要求更多显式确认或证据的一侧
- 若必须放宽，必须通过显式 `exception`

## 4. `gate` 类型与触发语义

phase 1 建议至少固定 5 类 gate：

### 4.1 准入 gate

判断是否允许进入某个 pack、节点或阶段。

### 4.2 转移 gate

判断是否允许从当前节点进入下一节点，或触发 handoff。

### 4.3 写入 gate

判断是否允许创建、覆盖、提升某个工件为权威版本。

### 4.4 交接 gate

判断是否允许把输出作为 `bridge artifact` 提供给其他 pack。

### 4.5 归档 gate

判断是否允许 session 或工件进入 `closeout / archive-ready / closed`。

### 4.6 gate 结果语义

phase 1 建议统一使用：

- `allow`
- `hold`
- `need-review`
- `need-approval`
- `need-evidence`
- `block`

核心目标不是“自动判得很聪明”，而是把“何时必须停下来确认”写清楚。

## 5. `approval`、`review`、`archive` 的边界

这 3 个词不能混用。

### 5.1 `approval`

人类对继续推进、发布或归档的放行决定。  
它回答的是：

- 可不可以继续

### 5.2 `review`

对工件质量、完整性、风险、适配性的复查。  
它回答的是：

- 做得够不够好

### 5.3 `archive`

把某个版本或阶段结果冻结为可回看、可引用、可追溯的权威快照。  
它回答的是：

- 哪个历史结果应被正式保留下来

### 5.4 三者关系

- `review` 可以先于 `approval`
- `archive` 通常要求已有足够 `evidence`
- 关键收尾可要求 `review + approval` 同时满足

## 6. `exception` 的语义

`exception` 不是口头放行，而是显式、有限范围、带原因、带时效的临时豁免。

一个最小有效的 `exception` 至少应说明：

- 适用对象
- 被豁免规则
- 产生原因
- 批准者
- 补偿动作
- 失效条件

`exception` 不会抹掉原规则，而是记录：

- 为什么偏离默认治理

## 7. 治理与 `Evidence` 的关系

`Evidence` 既是治理输入，也是治理输出。

### 7.1 治理依赖 evidence

放行前，要看证据是否足够。

### 7.2 治理生成 evidence

放行后，下列内容都应继续沉淀为新 evidence：

- gate 判断
- review verdict
- approval 结果
- archive 结论
- exception 豁免

phase 1 要形成的不是重型审计系统，而是最小证据链：

- 人能读
- 系统能指向
- 后续能复查

## 8. 治理与 reference packs 的关系

`Garage Core` 只提供统一治理语汇。  
具体 pack 通过 overlay 写入自己的质量要求、审批点、交接条件和归档标准。

### 8.1 `Product Insights Pack`

治理重点更偏向：

- 问题收敛
- 判断依据
- 假设验证
- bridge 完整性

### 8.2 `Coding Pack`

治理重点更偏向：

- 方案复查
- 实现验证
- 完成状态
- closeout 质量

不同 pack 可以有不同细则，但必须通过同一 `global / core / pack / node` 结构表达。

## 9. Phase 1 收敛范围

phase 1 治理模型只做这些事：

- 以 Markdown 工件表达主规则
- 强人工确认
- 确定性 gate 语义
- 验证 `Coding Pack` 与 `Product Insights Pack` 两个 `reference packs` 的治理 shape

phase 1 不做这些事：

- 不做组织级 RBAC
- 不做多租户权限继承
- 不做策略 DSL
- 不做自动信任评分
- 不做重型合规系统

## 10. 对后续开发的意义

这份文档的价值不在于把所有规则写得很多，而在于先把这几个问题说清楚：

- 哪些规则属于平台
- 哪些规则属于 pack overlay
- 哪些动作必须停下来 review
- 哪些动作必须有人 approval
- 哪些结果才有资格进入 archive

只有这些边界先稳定，后面拆开发任务时才不会一边开发一边重发明治理语义。

## 11. 遵循的设计原则

- 治理工件化：规则、审批、评审、归档、例外都应先成为显式工件。
- `Markdown-first`：先保证人可读、可讨论、可复查，再考虑机器执行便利性。
- 分层优先级明确：`global / core / pack / node` 的覆盖关系必须可解释、可追踪。
- 默认收紧而非放松：下层默认细化和加严，放宽必须显式豁免。
- 人负责最终裁决：phase 1 的关键审批和例外处理由人承担最终责任。
- `Evidence-linked governance`：所有关键治理动作都应留下可回指的证据链。
- Pack 语义留在 pack：核心治理只定义中立语汇，不吸收领域细则进入 `Garage Core`。
- phase 1 克制：先把治理语义写稳，再决定是否需要更重实现。

