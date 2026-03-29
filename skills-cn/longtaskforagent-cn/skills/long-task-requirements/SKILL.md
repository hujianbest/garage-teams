---
name: long-task-requirements
description: "当不存在 SRS 文档、设计文档与 feature-list.json 时使用 — 通过结构化提问引导需求，产出符合 ISO/IEC/IEEE 29148 的高质量 SRS 文档"
---

# 需求获取与 SRS 生成

将原始想法通过系统化获取、质疑与校验，转化为结构化、高质量的软件需求规格说明（SRS）— 对齐 ISO/IEC/IEEE 29148 与 EARS 需求句式。

<HARD-GATE>
在已向用户展示 SRS 并获得批准之前，不得调用任何设计技能、实现技能、编写任何代码、搭建任何项目，或采取任何设计/实现动作。此规则适用于**所有**项目，无论其看似多简单。
</HARD-GATE>

## 反模式：「太简单不需要 SRS」

每个项目都必须经过本流程。待办清单、单函数工具、配置变更 — 无一例外。「简单」项目往往是未审视假设导致最多返工的地方。SRS 可以很短（真正简单的项目几句话即可），但你**必须**展示并获得批准。

## 检查清单

你必须为下列每一项创建 TodoWrite 任务并按顺序完成：

1. **探索项目上下文** — 阅读既有文档、代码、约束；识别 SRS 模板
2. **结构化获取** — 一次一个澄清问题，对每条需求进行质疑
3. **需求分类** — 功能 / NFR / 约束 / 假设 / 接口 / 排除范围
4. **撰写需求** — 应用 EARS 模板、分配 ID、写验收标准、生成图示
5. **校验 SRS** — 检查 8 项质量属性、识别反模式、验证可测试性
6. **粒度分析** — 用 6 条启发式（G1–G6）识别过大 FR、拆解候选、非平凡拆分须经用户批准
7. **范围适配与推迟** — 评估本轮 vs 下轮，必要时生成推迟待办并更新 SRS 移除推迟项
8. **SRS 合规评审** — 派发 srs-reviewer 子代理；门禁：全部 R/A/C/S/D/G 检查 PASS 后方可继续
9. **展示并批准 SRS** — 非平凡项目按小节进行
10. **保存 SRS 与待办** — `docs/plans/YYYY-MM-DD-<topic>-srs.md` + 推迟待办（若有）并提交
11. **转入 UCD** — **必选子技能：** 调用 `long-task:long-task-ucd`（若 SRS 无 UI 特性则自动跳过至设计）

**终态为调用 long-task-ucd。** 不得调用任何其他技能。

## 第 1 步：探索上下文

1. 完整阅读用户提供的需求文档 / 想法说明
2. 探索项目将基于或对接的既有代码 / 仓库
3. 识别初始约束：技术栈、平台、集成、法规
4. 检查 SRS 模板：
   - 若用户指定模板路径 → 读取并校验
   - 否则 → 读取 `docs/templates/srs-template.md`（本技能随附默认模板）
   - **校验**：模板须为含至少一个 `## ` 标题的 `.md` 文件

## 第 2 步：结构化获取

使用 `AskUserQuestion`，以**多问题轮次**获取需求 — 每轮围绕一个主题域，最多 4 个相关问题。对每个领域遵循 **CAPTURE → CHALLENGE → CLARIFY** 循环。

**提问方式：**
- **按主题分批** — 每轮一次 `AskUserQuestion`，包含 2–4 个相关问题
- **优先选择题** — 每题提供 2–4 个选项以降低认知负担
- **假设并确认** — 陈述假设，由用户纠正
- **边界用场景** — 「当 [X] 失败时应怎样？」
- **立即量化** — 在问题中把模糊词换成数字
- **轮内跟进** — 若第 N 轮答案暴露歧义，在第 N+1 轮处理后再进入下一主题

**获取轮次**（顺序与分组随项目调整）：

### 第 1 轮：目的与范围
在单次 `AskUserQuestion` 中提问（最多 4 问）：
- 本系统要解决的核心问题是什么？
- 主要用户是谁？（画像、技术水平）
- 本版本**明确不在范围内**的是什么？
- 目标发布范围？（MVP vs 完整版）

### 第 2–N 轮：功能需求
每个能力域每轮（最多 4 问）：
- 用户做什么？（触发/动作）
- 系统如何响应？（可观察行为）
- 错误 / 边界 / 极端情况？
- 确认一条具体 Given/When/Then 示例

相关能力若共享工作流，可合并为同一轮。大型能力域可拆成多轮。

### 第 N+1 轮：非功能需求
按相关性将 NFR 探测合并为 1–2 轮：

| 类别（ISO 25010） | 探测 |
|---|---|
| **性能** | 响应时间目标？吞吐？并发用户？ |
| **可靠性** | 可用性目标？恢复时间？数据丢失容忍度？ |
| **易用性** | 无障碍要求？易学性标准？ |
| **安全** | 认证方式？授权模型？数据加密？ |
| **可维护性** | 模块化约束？测试覆盖率目标？ |
| **可移植性** | 平台限制？浏览器支持？ |
| **可扩展性** | 当前负载？目标负载？增长时间线？ |

明显无关的类别可跳过。**规则**：每条 NFR 须有**可度量准则**。「快」→「1000 并发用户下 p95 响应时间 < 200ms」。

### 第 N+2 轮：约束、假设与接口
合并为一轮（最多 4 问）：
- 硬限制（托管、预算、许可证、法规、既有系统）
- 假设为真的是什么？假设不成立会怎样？
- 要对接的外部系统？协议与数据格式？
- 需保持向后兼容的既有 API？

### 第 N+3 轮：术语表
若需要，在一轮中询问：
- 可能有歧义的领域术语？
- 需统一的同义词？需区分的同名异义？

**何时停止：** 当你能描述每个功能能力及其验收标准、所有带阈值的 NFR、所有约束与所有假设 — 且无需猜测 — 时进入第 3 步。

**规则**：每轮将相关问题打包（每轮一次 `AskUserQuestion`，2–4 问）。仅当某主题需深度顺序探测时（如复杂分支工作流）才拆成单问。

## 第 3 步：需求分类

将已捕获需求归入类别：

| 类别 | ID 前缀 | 说明 |
|---|---|---|
| Functional | FR-001 | 可观察的系统行为 |
| Non-Functional | NFR-001 | 带可度量准则的质量属性 |
| Constraint | CON-001 | 限制解空间的硬约束 |
| Assumption | ASM-001 | 假定成立的前提；记录失效风险 |
| Interface | IFR-001 | 外部系统契约 |
| Exclusion | EXC-001 | 明确排除的范围 |

## 第 4 步：用 EARS 模板撰写需求

对每条功能需求应用 EARS（Easy Approach to Requirements Syntax）模板：

| 模式 | 模板 | 使用时机 |
|---|---|---|
| **Ubiquitous** | The system shall `<action>`. | 始终生效的行为 |
| **Event-driven** | When `<trigger>`, the system shall `<action>`. | 响应用户/系统事件 |
| **State-driven** | While `<state>`, the system shall `<action>`. | 行为依赖模式/状态 |
| **Unwanted behavior** | If `<condition>`, then the system shall `<action>`. | 错误处理、容错 |
| **Optional** | Where `<feature/config>`, the system shall `<action>`. | 可配置/可选能力 |

**对每条需求另需写明：**
- **验收标准** — 至少一条具体 Given/When/Then 场景
- **优先级** — Must / Should / Could / Won't（MoSCoW）
- **来源** — 追溯到哪条干系人需要或用户故事

### 4c. 生成图示

全部需求写完后，生成两个 Mermaid 辅助图，放入 SRS 模板预留小节。

#### 用例视图（置于 SRS 第 3.1 节）

生成一个 `graph LR` 图：
- 第 3 节中所有参与者为外部节点 — 椭圆语法：`Actor((Name))`
- 所有 FR-xxx 标题作为 `subgraph System Boundary` 内的用例节点
- 按验收标准隐含的参与者–用例参与关系，每条有向边一条
- 每个参与者至少一条边；每个 FR 必须作为用例节点出现

#### 流程（置于 SRS 第 4.1 节）

每个功能域生成一个 `flowchart TD`。功能域满足以下**之一**即合格：
- 3+ 顺序步骤，或
- 其验收标准中至少一个决策/分支节点

每图规则：
- 开始节点：`([Start: <trigger>])`，结束节点：`([End: <outcome>])` — 圆角体育场样式
- 决策节点：菱形 `{condition?}`，`-- YES -->` / `-- NO -->` 标注分支
- 验收标准中的每个错误/边界情况必须表现为分支路径
- 用 `####` 子标题命名各工作流（如 `#### Flow: User Registration`）

范围：若 SRS ≤4 条需求且无分支，可合并为一图；若 ≥5 条需求且跨 ≥2 个域，则每功能域一图。

## 第 5 步：校验 SRS 质量

对照 **8 项质量属性**（IEEE 830 / ISO 29148）系统化检查：

### 5a. 逐条需求检查

对**每条**需求验证：

| # | 属性 | 检查 | 红旗 |
|---|---|---|---|
| 1 | **正确** | 可追溯到已确认的干系人需要？ | 孤儿需求（镀金） |
| 2 | **无歧义** | 两名读者会写出相同测试用例？ | 含糊词：「快」「健壮」「友好」「直观」「灵活」 |
| 3 | **完整** | 输入、输出、错误、边界均已定义？ | 「包括但不限于…」、无界列表 |
| 4 | **一致** | 与其他需求无矛盾？ | 时间冲突、格式冲突 |
| 5 | **已排序** | 有 MoSCoW 优先级？ | 全是「高优先级」 |
| 6 | **可验证** | 能写通过/失败测试？ | 「系统应易于使用」（无指标） |
| 7 | **可修改** | 仅在一处陈述？ | 跨节重复 |
| 8 | **可追踪** | 有唯一 ID + 来源链接？ | 缺 ID 或孤儿 |

### 5b. 反模式检测

全文扫描以下反模式，展示前修复：

| 反模式 | 识别信号 | 修复 |
|---|---|---|
| **含糊形容词** | 「快」「大」「可扩展」「可靠」无数字 | 量化为可度量准则 |
| **复合需求** | 「and」/「or」连接两个独立能力 | 拆成多条需求 |
| **设计泄漏** | 实现词汇：「class」「table」「endpoint」「algorithm」 | 改写为可观察行为 |
| **无主体被动** | 「data shall be validated」— 谁校验？ | 明确主体：「The system shall...」 |
| **TBD / TBC** | 未决占位 | 与用户解决或标为 Open Question |
| **缺负例** | 仅正向 | 补充错误/边界/安全场景 |
| **不可测 NFR** | NFR 无度量阈值 | 补充具体指标 + 测量方法 |

### 5c. 完整性交叉检查

- 每个功能域至少一条错误/边界场景
- 所有外部接口规定数据格式 + 协议
- 所有 NFR 有测量方法，而非仅目标
- 术语表覆盖需求中所有领域专用词
- Out-of-Scope 小节明确列出推迟特性

## 第 5.5 步：粒度分析与分解

分析每条 FR 是否隐藏会在下游产生过大特性的复杂度。粒度良好的 FR 可干净映射到 `feature-list.json` 中 1–2 个特性；过大的 FR 隐藏多个可独立测试的行为。

### 5.5a. 粒度启发式

对**每条**功能需求应用以下启发式。若**任一**触发，该 FR 为**分解候选**：

| # | 启发式 | 识别信号 | 示例 |
|---|-----------|-----------------|---------|
| G1 | **多参与者** | FR 涉及 2+ 不同用户角色执行不同动作 | 「Admin 可管理用户且终端用户可查看资料」 |
| G2 | **CRUD 打包** | 单条需求描述 Create + Read + Update + Delete | 「系统应管理产品库存」（隐含 CRUD） |
| G3 | **场景爆炸** | FR 有 4+ 条验收标准（Given/When/Then）覆盖不同行为路径 | 含 happy path + 3 错误 + 2 边界 |
| G4 | **跨层关切** | FR 同时跨后端逻辑与面向用户的 UI | 「订单状态变更时显示实时通知」 |
| G5 | **多状态行为** | FR 描述 3+ 种不同系统状态或模式下的行为 | 「在 draft/review/published 状态下，系统应…」 |
| G6 | **时序耦合** | FR 将触发事件与延迟/定时后果绑在一起 | 「用户注册时发送确认邮件并创建分析画像」 |

### 5.5b. 分解流程

对每个分解候选：

1. **识别原子行为** — 每个可独立测试的行为成为子需求候选
2. **应用单一职责测试**：「能否为这条子需求写**一条**聚焦的验收测试而不测无关行为？」
3. **保持可追溯** — 子需求继承父 ID 前缀：
   - 父：`FR-003` → 子：`FR-003a`、`FR-003b`、`FR-003c`
   - 每条子需求自有 EARS 陈述、验收标准与优先级
4. **重验子项** — 每条子需求须独立通过第 5a 步 8 项检查
5. **更新图示** — 若分解改变用例视图或流程，重生成受影响图

### 5.5c. 分解决策表

| 候选数量 | 动作 |
|----------------|--------|
| 0 个候选 | 跳过 — 进入第 5.6 步 |
| 1–3 个候选 | 自动分解；内联展示理由 |
| 4+ 个候选 | 通过 `AskUserQuestion` 请用户批准后再拆分 |

**规则**：不得在用户不知情下自动拆分。1–3 个候选时内联附理由；4+ 个须显式批准轮。

## 第 5.6 步：范围适配与推迟

分解后评估**所有**子需求是否属于本轮。并非每个子需求都须本版交付 — 部分应推迟至未来增量以控制范围与聚焦。

### 5.6a. 范围适配准则

对每条子需求（及**未**分解的原始 FR）评估：

| 准则 | 保留在本轮 | 推迟至下轮 |
|-----------|----------------------|---------------------|
| **优先级** | Must / Should（MoSCoW） | Could / Won't |
| **依赖** | 被其他本轮 FR 需要 | 无本轮 FR 依赖它 |
| **完整性** | 验收标准已完整 | 需进一步获取或领域输入 |
| **风险** | 理解充分、不确定性低 | 不确定性高，需原型/尖刺先行 |
| **范围预算** | 符合目标特性数（MVP 约 10–50） | 会使总量超出可管理范围 |

### 5.6b. 推迟决策

通过 `AskUserQuestion` 向用户展示范围适配结论：

```
After granularity analysis, the SRS contains [N] functional requirements.
I recommend keeping [K] in the current round and deferring [D] to a future increment:

**Current Round** (K requirements):
- FR-001: ... (Must, no dependencies on deferred items)
- FR-003a: ... (Must, core workflow)
- FR-003b: ... (Should, needed by FR-005)
...

**Proposed Deferrals** (D requirements):
- FR-003c: Update product (Could, no current-round FR depends on it)
  → Reason: Lower priority, independent of core MVP flow
- FR-003d: Delete product (Could, soft-delete can be added later)
  → Reason: Risk — deletion policy needs business rule clarification
- FR-009: Export reports (Won't for v1)
  → Reason: Scope budget — exceeds MVP target
...

Should I proceed with this split? You can move items between rounds.
```

**规则：**
- **Must 优先级 FR 永不自动推迟** — 仅用户可推迟 Must
- **依赖完整性** — 若保留 FR-X 且其依赖 FR-Y，则 FR-Y 也必须保留
- 用户批准 0 项推迟 → 跳过待办生成，进入第 6 步
- 用户批准 ≥1 项推迟 → 进入 5.6c

### 5.6c. 生成推迟需求待办

对已批准推迟项，用推迟待办模板生成 `docs/plans/YYYY-MM-DD-<topic>-deferred.md`：

1. 检查模板：
   - 若用户指定模板 → 读取并校验
   - 否则 → 读取 `docs/templates/deferred-backlog-template.md`
2. 每条推迟需求记录：
   - 原始 FR ID 与 EARS 陈述（与 SRS 草稿完全一致）
   - 验收标准（完全一致）
   - 推迟原因（来自 5.6b 评估）
   - 对本轮需求的依赖（供未来影响分析）
   - 建议波次（下一增量或更晚）
   - 再进入条件：拾取前须满足什么
3. 更新 SRS 草稿：
   - 从第 4 节（功能需求）**删除**已推迟 FR
   - 在第 1.2 节（Out of Scope）**增加**引用：`"Deferred to future increment — see [deferred backlog](YYYY-MM-DD-<topic>-deferred.md)"`
   - **更新**图示：用例视图中移除已推迟用例，流程中移除已推迟流
   - 若编号空缺造成困惑可**重编号**（可选 — 用户偏好）
4. 与 SRS 一并提交推迟待办

### 5.6d. 待办与增量衔接

推迟待办设计为可直接进入 `long-task-increment` 技能：

- 用户准备拾取推迟需求时，创建引用该待办的 `increment-request.json`：
  ```json
  {
    "reason": "Pick up deferred requirements from wave 0",
    "scope": "See docs/plans/YYYY-MM-DD-<topic>-deferred.md",
    "changes": ["new"]
  }
  ```
- 增量技能读取待办，对已有完整 EARS + 验收标准的需求跳过重新获取，直接进入影响分析
- 增量处理后，在待办中将已拾取项标为 `status: "incorporated"` 并注明波次与日期

**规则**：推迟待办为活文档。每次拾取项的增量都会更新。全部纳入或明确放弃后归档。

## 第 6 步：SRS 合规评审

派发子代理，在面向用户展示前独立按 ISO/IEC/IEEE 29148 与图示要求校验 SRS。此步**强制** — 第 5 步自检不能替代。

### 6a. 派发 SRS 评审子代理

```
Task(
  subagent_type="general-purpose",
  prompt="""
  You are an SRS compliance reviewer aligned with ISO/IEC/IEEE 29148.
  Read the reviewer prompt at: skills/long-task-requirements/prompts/srs-reviewer-prompt.md

  Project context:
  {project_context}

  Full SRS draft (all sections):
  {srs_draft}

  Requirement ID list:
  {requirement_id_list}

  Perform the review following the prompt exactly.
  """
)
```

### 6b. 评审门禁逻辑

**全部检查须 PASS 方可进入第 7 步：**
- 组 R（R1–R8）：质量属性 — 每条需求通过全部 8 项检查
- 组 A（A1–A6）：反模式 — 全文未发现
- 组 C（C1–C5）：完整性 — 全部交叉检查确认
- 组 S（S1–S4）：结构合规 — 必选小节齐全
- 组 D（D1–D4）：图示 — 用例视图与流程存在且已填充
- 组 G（G1–G3）：粒度 — 分解/推迟后无过大 FR

**FAIL 时 — 双轨处理：**

**轨 1：USER-INPUT 项 → 立即询问**

阅读评审员「Clarification Questions」表。若有行（存在 USER-INPUT 项）：

使用 `AskUserQuestion` 做针对性问卷 — **不要**倾倒完整评审报告。格式：
```
The SRS needs clarification on a few points before I can finalize it. Please answer:

1. [FR-xxx] [Issue in plain language]
   Your requirement says "[exact phrase]". What is the correct value?
   (e.g., [example format/unit])

2. [FR-yyy] [Next issue]
   ...
```

**不要猜测或编造答案。在收到用户答复前不得继续。**

收到答复后：并入 SRS 草稿。

**轨 2：LLM-FIXABLE 项 → 自动修复**

并行修复全部 LLM-FIXABLE：拆分复合需求、补参与者、填小节、生成图、分配 ID。与轨 1 的用户答复一并应用。

**再次派发评审（第 2 轮）**

用修订稿再次派发子代理。若第 2 轮 PASS → 进入第 7 步。

**若第 2 轮仍 FAIL：**
- 发现新 USER-INPUT → 再次用相同精简格式 `AskUserQuestion`
- 两轮后仅剩 LLM-FIXABLE → 使用 `AskUserQuestion`：
  - 剩余失败表（检查 ID、位置、问题描述）
  - 已尝试修复摘要
  - 请用户指示（修复、豁免或重构）

**最多 2 次再派发循环。** 未经用户输入不得尝试第 3 轮。

全部组 PASS 后，在 SRS 页眉记录评审结果：
```markdown
<!-- SRS Review: PASS after N cycle(s) — YYYY-MM-DD -->
```

## 第 7 步：展示并批准 SRS

非平凡项目按小节展示并逐节批准：

1. **目的、范围与排除** — 边界与**未**包含内容
2. **术语表与用户画像** — 共同词汇与用户理解
3. **功能需求** — 核心能力与验收标准
4. **非功能需求** — 带指标的质量属性
5. **约束、假设与接口** — 硬限制与外部契约

每节展示后等待反馈，纳入修改后再进下一节。

**简单项目**（< 5 条功能需求）：所有小节合并为一次批准。

## 第 8 步：保存 SRS 文档与推迟待办

将已批准 SRS 保存至 `docs/plans/YYYY-MM-DD-<topic>-srs.md`。

### 模板使用

读取第 1 步确定的模板（用户指定或默认 `docs/templates/srs-template.md`）：
1. 保留模板标题结构
2. 用已批准内容替换各标题下引导文字
3. 若尚无元数据，在文首补充（`Date`、`Status`、`Standard`、`Template` 路径）
4. 模板未覆盖小节：标 `"[Not applicable]"`
5. 已批准但无对应模板小节的内容：追加为「Additional Notes」

### 推迟待办（若在第 5.6 步生成）

若生成了推迟待办，与 SRS 一并保存：
- 路径：`docs/plans/YYYY-MM-DD-<topic>-deferred.md`
- 同一提交中同时提交两文件

## 第 9 步：转入 UCD

SRS 文档（及若有推迟待办）保存并提交后：

1. 总结下一阶段所需关键输入：
   - 功能需求数量与优先级分布
   - 影响架构选择的关键约束
   - 影响技术选型的 NFR 阈值
   - SRS 是否含 UI 相关功能需求（决定运行 UCD 或自动跳过）
   - 是否存在推迟待办（预示未来增量可能）
2. **必选子技能：** 调用 `long-task:long-task-ucd` 生成 UCD 风格指南（无 UI 特性时自动跳过至设计）

## 需求阶段规模

| 项目规模 | 功能需求数 | 深度 |
|---|---|---|
| Tiny | 1–5 | 单页 SRS，合并批准 |
| Small | 5–15 | 标准 SRS，2–3 个批准小节 |
| Medium | 15–50 | 完整 SRS 全小节，按节批准 |
| Large | 50–200+ | 完整 SRS + 接口规约 + 领域模型 |

## 红旗

| 自我合理化 | 正确应对 |
|---|---|
| 「太简单不需要 SRS」 | 跑轻量 SRS（单次批准） |
| 「用户已经说清要做什么」 | 用户描述是原始输入；SRS 提供结构、完整性与可测试性 |
| 「设计时再弄清需求」 | 需求是 WHAT；在 HOW 阶段发现会导致返工 |
| 「本项目不适用 NFR」 | 每个项目至少有隐式性能/可靠性需求 — 显式化 |
| 「术语表显而易见」 | 对谁显而易见？定义用户与开发者可能理解不同的每个词 |
| 「先从 happy path 开始」 | 错误、边界与负例须**现在**捕获 |
| 「这条 FR 作为一条大需求没问题」 | 应用 6 条粒度启发式（G1–G6）— 隐藏复杂度会产生过大特性 |
| 「所有需求都应在本轮」 | 第 5.6 步范围适配保证聚焦 — 低优先级项推迟以保持可管理范围 |
| 「推迟项写进 Out-of-Scope 就行」 | Out-of-Scope 是叙述；推迟待办保留 EARS + 验收标准以便增量无缝拾取 |

## 集成

**由…调用：** using-long-task（无 SRS、无设计文档、无 feature-list.json 时）  
**链接至：** long-task-ucd（SRS 批准后；无 UI 特性时自动跳过至设计）  
**产出：** `docs/plans/YYYY-MM-DD-<topic>-srs.md`，可选 `docs/plans/YYYY-MM-DD-<topic>-deferred.md`
