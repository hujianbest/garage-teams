# F060: Garage Phase 1 Artifact And Evidence Surface

- Feature ID: `F060`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 定义 `Garage` 在 phase 1 的文件表面，明确 `artifact`、`evidence`、`session` 与 `archive` 在 `Markdown-first`、`file-backed` 形态下的目录边界、权威规则、命名方式、sidecar 角色、lineage 链接与覆盖 / 归档语义。
- 当前阶段: phase 1
- 关联文档:
  - `docs/GARAGE.md`
  - `docs/architecture/A120-garage-core-subsystems-architecture.md`
  - `docs/features/F010-shared-contracts.md`
  - `docs/architecture/A130-garage-continuity-memory-skill-architecture.md`
  - `docs/features/F110-reference-packs.md`
  - `docs/features/F050-governance-model.md`

## 1. 文档目标与范围

这篇文档只回答一个问题：

**在 phase 1 中，`Garage` 应如何用稳定、可读、可追溯的文件表面承接 `artifact` 与 `evidence`。**

本文关注：

- 目录边界
- 对象权威性
- 命名方式
- sidecar 语义
- lineage 关系
- 覆盖与归档语义

本文不展开：

- 具体 schema 字段
- CLI 行为
- 索引更新算法
- 底层存储实现

## 2. 核心术语与边界

### 2.1 `artifact`

`artifact` 是要被消费、交接、继续推进的主工件。  
它回答的是：

- 当前产出了什么

### 2.2 `evidence`

`evidence` 是说明结果为什么成立、如何验证、由谁确认的记录。  
它回答的是：

- 为什么可信
- 如何到达
- 是否通过

同一次推进通常会同时产生 `artifact` 与 `evidence`，但两者不能混写成同一类对象，也不能互相替代。

## 3. 文件表面的总体结构

`Garage` 的文件表面应按对象职责分层，而不是按入口工具或聊天历史分层。

phase 1 先冻结 5 类稳定 surface：

- `artifacts/`
- `evidence/`
- `sessions/`
- `archives/`
- `.garage/`

目录组织优先体现：

- `surface -> pack -> object`

而不是：

- `session -> everything`

因为 `session` 是协调与恢复边界，不应吞并长期 `artifact` 或 `evidence` 的权威性。

## 4. Canonical directories

| 目录 | 作用 | 权威内容 | 非权威内容 |
| --- | --- | --- | --- |
| `artifacts/` | 当前有效主工件面 | 可被下游节点或其他 pack 消费的正式工件 | 临时草稿、派生索引 |
| `evidence/` | 当前有效证据面 | 决策、验证、评审、审批、来源记录 | 主工件正文 |
| `sessions/` | 当前会话协调面 | resume 指针、handoff 状态、当前上下文快照 | 长期正式产物 |
| `archives/` | 历史归档面 | 被替换、冻结、关闭的历史对象 | 当前有效对象 |
| `.garage/` | 机器辅助面 | 索引、sidecar、路由辅助、轻量派生状态 | 面向人的主叙事内容 |

phase 1 的关键判断：

- `archives/` 应作为统一顶层归档面，而不是把归档文件散落在各活跃目录里
- pack 语义应作为子层维度进入这些 canonical surface，而不是自行长出新的顶层目录

## 5. 权威规则

phase 1 建议冻结 5 条权威规则：

1. 一个逻辑对象在任一时刻只能有一个“当前权威位”。
2. `artifact` 的权威性来自主工件文件本身。
3. `evidence` 的权威性来自证据记录本身。
4. `sidecar` 只承接机器可读标识、状态和链接，不承接人类主语义。
5. `archive` 对历史状态权威，但对“当前有效版本”不权威。

phase 1 禁止：

- 把关键事实只藏在聊天历史
- 把主语义只写在 sidecar
- 把“当前面”和“历史面”混在一起

## 6. 命名与稳定标识

文件命名应同时服务：

- 人可读定位
- 机器稳定引用

路径是 locator，不是 identity；稳定身份应由独立 `id` 承担。

### 6.1 命名建议

- 文件名统一使用 `kebab-case`
- 文件名应显式体现对象角色，而不是只用自由标题

例如：

- `artifact`：`design--session-routing--a42.md`
- `evidence`：`verification--design-a42--e17.md`

### 6.2 sidecar 约定

- sidecar 与主文件共享 basename
- sidecar 强调从属关系，而不是形成第二套命名宇宙

## 7. Sidecar 的职责边界

sidecar 的目的，是给 `Garage Core` 提供机器可读的：

- identity
- status
- lineage pointer
- route metadata

sidecar 不应：

- 复制主文档完整正文
- 复制完整理由链
- 复制完整评审内容

当主文档与 sidecar 冲突时：

- 叙事内容以 Markdown 主文档为准
- 稳定标识与链接锚点以 sidecar 为准

phase 1 中，sidecar 是轻量增强层，不是隐藏数据库。

## 8. Lineage linking 与跨面关联

`Garage` 需要显式表达：

- `session -> node -> artifact -> evidence -> archive`

而不是依赖目录邻接或命名猜测。

phase 1 建议先冻结一组最小关系语义：

- `produced-by`
- `derived-from`
- `reviews`
- `verifies`
- `approves`
- `supersedes`
- `archived-from`

跨 pack handoff 必须优先通过显式 `artifact` 与相关 `evidence` 引用完成，而不是依赖隐式聊天上下文。

## 9. Archive placement 与生命周期

归档的目标不是隐藏旧文件，而是把：

- 当前面
- 历史面

明确分离。

`archives/` 应镜像活跃 surface 的主分类，使归档后仍保留原始对象语义，而不是只按日期堆放。

进入归档面意味着：

- 对象失去当前权威位
- 但保留历史可查性
- 保留 lineage 连续性
- 保留审计价值

归档动作本身也应形成可引用记录。

## 10. Overwrite 与变更语义

### 10.1 `artifact`

`artifact` 可以被新版本替换，但“替换”应被视为受控版本推进，而不是静默覆盖。

覆写只适用于：

- 同一逻辑对象
- 同一权威位
- 新修订

若对象角色、用途或归属发生变化，应视为新对象，而不是覆盖。

### 10.2 `evidence`

`evidence` 默认采用追加式语义。

错误修正应通过新的证据记录声明：

- 补充
- 取代

而不是回写抹除旧记录。

phase 1 不允许无 lineage 的 destructive overwrite。

## 11. Phase 1 的 file-backed 约束

phase 1 以本地文件系统为主事实源，不引入：

- 数据库优先
- 对象存储优先
- 图数据库优先

主工件与主证据默认以 Markdown 表达。  
机器增强信息使用轻量 sidecar 即可。

phase 1 不处理：

- 实时多人并发写入
- 分布式锁
- 跨设备强一致同步
- 复杂权限模型

对二进制和富媒体内容：

- 只承接引用位与关联证据
- 不做完整媒体资产管理

## 12. 非目标与主要风险

### 12.1 非目标

- 不先做完整数据库控制面
- 不先做多租户治理
- 不先做富媒体资产平台
- 不先做复杂自动版本图

### 12.2 主要风险

- `artifact` 与 `evidence` 混桶
- sidecar 过重，反过来替代主文档
- 归档散落在活跃目录中
- 把重命名误当新对象，或把新对象误当覆写

## 13. 遵循的设计原则

- 平台中立：core 只理解中立对象与关系，不理解 pack 内部领域名词。
- 一对象一当前权威位：任何逻辑对象在任一时刻只能有一个当前 authoritative slot。
- `Markdown-first`：面向人的主语义写在 Markdown，而不是隐藏在 sidecar 或运行时状态里。
- `File-backed`：phase 1 以可见文件面为事实源，避免过早服务化。
- Sidecar as support, not source：sidecar 是辅助层，不是主语义来源。
- Archive instead of silent overwrite：历史应被显式归档和链接，而不是悄悄消失。
- Traceability by default：lineage、验证、审批和替换关系默认可追溯。
- Session is coordination, not authority：会话负责协调与恢复，不吞并长期工件权威。
- Pack-extensible surface：新增 pack 应复用同一套 surface 规则，而不是自造顶层文件宇宙。
- phase 1 克制：先把小而稳的 phase 1 文件表面冻结，再考虑更重的服务化能力。

