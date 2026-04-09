# AHE 平台优先 Multi-Agent Phase 1 需求规格说明

- 状态: 已批准
- 日期: 2026-04-09
- 主题: `ahe-platform-first-multi-agent-phase-1`
- 评审记录:
  - `docs/reviews/spec-review-ahe-platform-first-multi-agent-phase-1.md`
- 批准记录:
  - `docs/reviews/spec-approval-ahe-platform-first-multi-agent-phase-1.md`
- 上游输入:
  - `docs/architecture/ahe-platform-first-multi-agent-architecture.md`
- 相关文档:
  - `AGENTS.md`
  - `docs/guides/ahe-path-mapping-guide.md`
  - `docs/reviews/design-review-ahe-platform-first-multi-agent-implementation-design.md`

## 1. 背景与问题陈述

当前仓库已经形成了较完整的 `ahe-*` workflow 能力，但多 agent 运行时的入口、路由、治理、审批、归档和宿主适配职责仍大量附着在 AHE 语境中，带来以下问题：

- 平台职责与 AHE pack 私有职责边界不清，`ahe-*` 命名容易被误当成平台保留语义。
- `workflow-board`、lease、approval、archive、evidence 等对象已经被提出，但尚未形成独立、可复用、可落盘的 platform-neutral contract。
- 当前仓库缺少可回读的 requirement spec 与 progress state surface，导致设计和评审链条难以稳定恢复。
- 在没有 pack-neutral contract 的前提下，未来接入第二个非 AHE pack 会被迫继承 AHE 私有语言和流程节奏。

本轮需求规格要解决的是：在不引入数据库、常驻服务和完整控制面的前提下，为 AHE 向 multi-agent 演进定义一个 **平台优先、单 pack 启动、repo-local、file-backed** 的 Phase 1 需求基线。

## 2. 目标与成功标准

### 2.1 目标

1. 定义一个 pack-neutral 的 multi-agent 平台需求边界，使平台与 AHE coding pack 的职责分离。
2. 明确 Phase 1 只支持单 pack 启动，并把 `ahe-coding-skills/` 定位为首个 reference pack，而不是平台本体。
3. 为 session、routing、governance、evidence、approval、archive、progress state 建立稳定的需求口径和工件面。
4. 保持当前 Markdown-first、repo-local、evidence-first 的工作方式，不要求数据库或常驻服务才能成立。
5. 为未来第二个、第三个 pack 的接入保留统一 contract 和路径映射能力。

### 2.2 成功标准

- 评审者可以从规格中明确区分哪些职责属于平台，哪些职责仍属于 `ahe-coding-skills/`。
- 平台 shared contract 与目录命名不再把 `ahe-*` 当作保留字或硬编码字段。
- Phase 1 可以在仓库内通过文件化工件完成 session 启动、恢复、审批暂停、证据回读和归档。
- 仓库内存在稳定的 requirement spec 与 progress state surface，可供后续 `ahe-spec-review`、`ahe-design`、`ahe-design-review` 和 router 回读。
- 后续新增 pack 时，无需先改写平台 vocabulary 才能挂载。

## 3. 用户角色与关键场景

### 3.1 用户角色

- 平台维护者：定义和维护 platform-neutral contract、治理注入方式、运行时边界与宿主适配能力。
- Pack 维护者：维护 `ahe-coding-skills/` 的 graph variant、node contract、pack-local 文档与模板。
- 工作流操作者：发起、恢复或观察一次针对特定主题的 multi-agent session。
- Reviewer / Approver：基于 review、verification、approval 等证据判断是否允许流程继续推进。

### 3.2 关键场景

- 场景 A：操作者在当前仓库内发起一次平台优先 session，选择 `ahe-coding-skills/` 作为 pack，并开始一个可恢复的工作流。
- 场景 B：session 在 review、gate 或 closeout 之间中断后，系统可依靠仓库中的状态面和证据工件恢复，而不是依赖聊天记忆。
- 场景 C：平台需要协调 AHE pack 执行 producer / review / gate 节点，但不直接理解 AHE 私有术语。
- 场景 D：质量类节点需要做只读并行分析，但主工件写入、审批和归档仍保持安全串行。
- 场景 E：未来增加第二个 pack 时，平台仍可沿用同一套 contract 类别、状态面与治理注入方式。

## 4. 范围

本规格覆盖 Phase 1 必须具备的需求：

- 定义平台优先的 multi-agent runtime 需求边界。
- 定义单 pack 启动模式下的平台与 `ahe-coding-skills/` 的职责划分。
- 定义 session、board、lease、attempt、evidence、approval、archive、progress view 等逻辑对象需要支持的最小行为。
- 定义稳定的 logical artifact surfaces，包括 requirement spec、design doc、task plan、progress state、review records、verification records、release / closeout artifacts。
- 定义治理注入、工件映射、审批暂停、恢复和兼容模式的需求。
- 定义只读并行质量 fan-out 与主工件单写的约束。

## 5. 范围外内容

- 不在 Phase 1 内实现数据库、常驻服务、Web UI 或完整控制面。
- 不在 Phase 1 内实现多用户、多仓 federation 或跨仓协作。
- 不要求 Phase 1 立即切换为 `board-first` 唯一事实源。
- 不要求在 Phase 1 同时运行多个 pack。
- 不要求在 Phase 1 重写全部现有 `ahe-*` skills。
- 不在本规格中重新定义 AHE 既有 coding quality gates 的业务判断标准。

## 6. 术语与定义

| 术语 | 定义 |
| --- | --- |
| `pack` | 一组可注册、可调度的 skill family，拥有自己的 graph variant、node 定义和 pack-local 命名。 |
| `session` | 一次可恢复的多节点工作会话，绑定特定主题、pack、graph variant 和证据上下文。 |
| `node` | pack-local 的执行单元，可是 producer、review、gate、closeout 或其他节点类型。 |
| `graphVariant` | pack 声明的流程变体标识，用于表达节点顺序与 profile 差异。 |
| `artifact surface` | 某类逻辑工件在仓库中的权威承载面。 |
| `progressView` | 面向人类与 router 的状态投影视图，用于跨会话恢复。 |
| `approval checkpoint` | 流程必须暂停并等待显式审批证据的检查点。 |
| `evidence record` | 与 review、verification、approval、outcome、archive 等相关的可回读证据记录。 |

## 7. 功能需求

### FR-001 平台中立 vocabulary 与 contract 边界

需求：

- 平台共享 contract、目录命名和运行时逻辑必须使用 pack-neutral vocabulary，不得把 `ahe-*`、AHE variant 名称或 AHE 审批别名升格为平台保留语义。
- AHE 私有语言只允许保留在 `ahe-coding-skills/` 的 pack-local 节点、映射、模板和说明文档中。

验收标准：

- Given reviewer 检查 platform-shared contract 与目录命名，When 对照 AHE pack 术语，Then 不存在要求所有 pack 复用的 AHE 前缀字段名或 AHE 专属阶段名。
- Given 平台需要解析 AHE pack 的节点和 graph variant，When 执行路由或恢复，Then 平台通过 pack metadata / mapping 解析，而不是硬编码 AHE 节点顺序。

### FR-002 单 pack 启动与注册

需求：

- Phase 1 必须支持至少一个已注册 pack 的启动与调度，首个 reference pack 为 `ahe-coding-skills/`。
- Session 在创建时必须显式绑定 `packId`、主题和 graph variant；Phase 1 不要求支持多个 pack 同时执行。

验收标准：

- Given 仓库中存在 AHE pack 的注册信息，When 操作者发起新的 session，Then 系统能解析出唯一的 pack 与 graph variant，并建立对应 session。
- Given 当前 Phase 1 仍处于单 pack 模式，When 操作者试图在同一运行面中混入第二个 pack 的执行语义，Then 系统会将其视为未支持场景，而不是静默混合两套 pack 语义。

### FR-003 Session 创建、恢复与重入

需求：

- 系统必须支持新建 session、恢复既有 session 和在中断后重入工作流。
- 恢复判断必须依赖仓库内的状态面和证据工件，而不是依赖聊天记忆作为唯一来源。

验收标准：

- Given 一次 session 已经写回 progress state、review record 和其他必要证据，When 会话中断后重新进入，Then 平台能够基于这些工件恢复当前阶段和下一步建议。
- Given 仓库内不存在足够的恢复证据，When 操作者尝试恢复 session，Then 系统应明确给出“证据不足”或更保守的回退结论，而不是伪造进度。

### FR-004 治理注入与路径映射

需求：

- 系统必须从 `AGENTS.md` 或等价权威治理工件读取路径映射、审批等价证据、并发约束和 repo-local policy。
- 平台不得复制出第二份与 `AGENTS.md` 竞争的平行治理源。

验收标准：

- Given 仓库已声明治理约束，When session 启动或恢复，Then 平台会将这些约束注入当前 session 的决策上下文。
- Given reviewer 检查治理来源，When 比对平台运行面与仓库说明，Then 能定位到单一权威治理入口，而不是多份相互冲突的规则源。

### FR-005 稳定 logical artifact surfaces

需求：

- 系统必须为至少以下逻辑工件提供稳定、可回读、可写回的承载面：requirement spec、design doc、task plan、progress state、review records、verification records、release / closeout artifacts。
- 每类逻辑工件在同一 scope 内必须有唯一的权威映射，不应依赖临时猜测或多路径并存。

验收标准：

- Given reviewer 需要读取当前主题的 spec、design、progress 和 review artifacts，When 按仓库约定回读，Then 每类逻辑工件都能定位到唯一权威入口。
- Given 某节点需要写回 review 或 verification 记录，When 它完成写回，Then 后续节点能在稳定映射面重新读取，而不是依赖聊天消息。

### FR-006 平台协调职责与 pack 执行职责分离

需求：

- 平台必须拥有 session 协调、board、lease、attempt、approval、archive、evidence 与宿主适配职责。
- Pack 负责其 domain-specific 节点逻辑、pack-local docs、templates、graph variants 和 node contracts。

验收标准：

- Given 一个 producer 或 reviewer 节点由 AHE pack 执行，When 该节点提交 outcome，Then 平台负责接收和协调状态推进，而不是把 board 或 archive 逻辑下沉到 pack 本身。
- Given reviewer 检查职责边界，When 对照平台层与 pack 层资产，Then 能明确分辨哪些对象是平台拥有，哪些是 pack-local 能力。

### FR-007 证据记录、审批与归档

需求：

- 系统必须把 review、verification、approval、outcome 和 archive snapshot 等关键事实以 repo-local、可回读的证据记录形式保存。
- 审批检查点必须等待显式 approval evidence 后才能推进到下游阶段。

验收标准：

- Given 流程到达声明了 approval checkpoint 的节点，When 尚未存在 approval evidence，Then 系统会暂停继续推进并标记待审批状态。
- Given review / verification / approval 已写回记录，When 后续 gate 或 finalize 节点回读这些记录，Then 能读取到可审计的证据链而不是口头结论。

### FR-008 人类可读的 progress state

需求：

- 系统必须提供一个人类可读的 `progressView`，用于记录当前阶段、待处理 review / gate、相关文件、证据路径和下一步推荐 skill。
- 该状态面必须能在关键节点结束后被更新，并在下一会话中被 router 或人工重新读取。

验收标准：

- Given 一个上游节点刚完成并产生新证据，When 平台或 pack 更新 progress state，Then 当前阶段与下一步推荐 skill 会同步反映最新状态。
- Given 新会话读取 progress state，When 没有新的冲突证据，Then 它能把该状态面作为恢复和派发的主要人类可读入口。

### FR-009 受控并行与主工件单写

需求：

- 系统必须允许只读质量分析节点在不竞争主工件写权限时并行执行。
- 主工件写入、审批、gate、closeout 和 archive 必须保持串行或等价的单写语义。

验收标准：

- Given 多个质量 review 节点只声明读取同一主工件，When 平台调度这些节点，Then 它可以允许并行分析但不会让它们并发改写同一主工件。
- Given 某节点声明会写入主工件或归档面，When 同时存在其他写入请求，Then 系统必须阻止冲突写入或以更保守方式串行化处理。

### FR-010 `artifact-first + board-assisted` 兼容模式

需求：

- Phase 1 必须采用 `artifact-first + board-assisted` 的兼容模式。
- 当 board 推断与已落盘的 review、verification、progress 或其他权威工件冲突时，系统必须选择更保守的工件证据结果。

验收标准：

- Given board 推荐的下一节点与 review / verification 工件冲突，When 平台进行仲裁，Then 结果以更保守的已落盘工件证据为准。
- Given board 仅补充协调和恢复信息，When 主工件证据已经存在，Then board 不会覆盖或伪造这些已落盘事实。

### FR-011 未来 pack 的可接入性

需求：

- 本规格定义的平台 contract 必须允许未来新增非 AHE pack，而不要求先重命名平台 vocabulary 或复制平台治理模型。

验收标准：

- Given 未来新增一个非 AHE pack，When 它声明自己的 pack metadata、node registry 和 artifact mapping，Then 平台可以沿用同一类 contract 与治理注入机制理解它。
- Given reviewer 检查本规格的核心概念，When 移除 AHE pack 例子后，Then 这些概念仍然成立并可被其他 pack 复用。

## 8. 非功能需求

| ID | 要求 |
| --- | --- |
| `NFR-001` | Phase 1 必须在 repo-local、file-backed 条件下成立；不依赖数据库、常驻服务或 Web 控制面才能运行。 |
| `NFR-002` | 中断恢复必须依赖可回读工件完成；聊天上下文可以辅助理解，但不能成为唯一恢复源。 |
| `NFR-003` | 关键节点的 review、verification、approval、outcome 和 archive 结论必须具备可审计的证据路径。 |
| `NFR-004` | 平台层共享 contract、目录和字段命名必须保持 pack-neutral，可被未来 pack 复用。 |
| `NFR-005` | 主工件必须遵守单写安全边界；任何并发都不能降低对冲突、漂移和越权写入的防护。 |
| `NFR-006` | Phase 1 必须与当前 AHE workflow 兼容迁移，允许保留 `task-progress.md` 等现有人类可读工件作为过渡期投影视图。 |

## 9. 外部接口与依赖

- `AGENTS.md`：当前仓库的治理注入根，承载路径映射、约束和运行约定。
- `ahe-coding-skills/`：首个 reference pack，承载 pack-local skills、docs、templates 和 graph variant 语义。
- `docs/` 下的 spec / design / reviews / verification 等文档面：承载可回读的人工与 agent 协作证据。
- 平台 shared contract 的 machine-readable 承载面：用于存放 pack-neutral contract 与 schema，必须与 narrative docs 分离。
- Cursor / CLI / subagent / shell / MCP 等宿主环境：作为宿主差异来源，需要被统一适配，而不是直接让 workflow 分叉。

## 10. 约束

- 只引用当前仓库真实存在或本轮明确新建的路径，不继续依赖已废弃目录名。
- 规格必须描述“做什么、做到什么程度算完成”，不能提前把 class、service、schema 实现细节写成刚性方案。
- 平台不得把 `ahe-specify`、`ahe-test-driven-dev`、`full`、`standard`、`lightweight` 等 AHE 私有概念提升为共享 contract 关键字。
- 当前仓库没有统一构建链路；验证方式以工件可回读性、路径稳定性与后续 review 为主。
- Phase 1 不得为了平台化而破坏现有 AHE coding 质量门禁或其证据读取习惯。

## 11. 假设

- 当前仓库会继续作为 Phase 1 的主要证据存储面和恢复入口。
- interactive 模式下仍有人工参与 review / approval；auto 模式是否扩展为自动审批不在本轮规格内展开。
- `ahe-coding-skills/` 在本阶段仍是唯一需要被正式接入的平台 pack。
- 本规格通过评审后，将成为后续设计与任务拆解的 requirement authority；现有架构文档继续作为 HOW 层输入而非需求替代品。

## 12. 开放问题

当前无阻塞性开放问题。

以下议题明确留待后续增量处理，不阻塞本规格评审：

- 第二个非 coding pack 的优先级与接入顺序。
- 从 `artifact-first + board-assisted` 切换到 `board-first` 的时间点与准入条件细化。
- Phase 1 之后是否需要单独的 platform role assets 与更细粒度 policy fragments。
