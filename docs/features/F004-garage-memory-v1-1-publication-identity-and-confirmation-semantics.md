# F004: Garage Memory v1.1 — 发布身份解耦与确认语义收敛

- 状态: 已批准（auto-mode approval；见 `docs/approvals/F004-spec-approval.md`）
- 主题: 收敛 F003 显式延后的 minor 与 USER-INPUT 候选，让 Stage 2 "记忆体"在重复发布、入口校验、放弃语义、session 触发证据 4 个面达到可治理的稳态
- 日期: 2026-04-19
- 关联:
  - F001（Garage Agent 操作系统）
  - F002（Garage Live）
  - F003（Garage Memory — 自动知识提取与经验推荐）
  - `RELEASE_NOTES.md` "F003 — 已知限制 / 后续工作" 段
  - `docs/reviews/code-review-F003-garage-memory-auto-extraction-r2.md` `finding_breakdown`

## 1. 背景与问题陈述

F003 已经把 Garage 从"会存"推到了"会自动起草、用户确认后入库、相似任务主动推荐"的 Stage 2 闭环。但在 finalize 时，code-review r2 / traceability-review / completion-gate 共同显式延后了 1 项 USER-INPUT minor 与 3 项 LLM-FIXABLE 行为变更类 minor。它们没有在 F003 cycle 内强制收敛，理由都是同一个：单条修复要么涉及 `KnowledgeStore` 层的 ID 体系决策（设计层），要么涉及 CLI 行为语义差异化（产品层），不属于 r1→r2 1-2 轮可消化的代码层闭合。

如果不在下一个 cycle 把这 4 项收敛掉，会出现以下真实问题：

1. **"发布身份"与"候选身份"耦合**：`KnowledgePublisher` 当前用 `candidate_id` 直接当 `KnowledgeEntry.id` / `ExperienceRecord.record_id`；同一候选被 `accept` / `edit_accept` 重复处理时，`KnowledgeStore.store()` 会原地覆盖前一次发布，绕过 `update()` 的 `version+=1` 链路，破坏 F001 FR-002 "知识版本追踪" 不变量。
2. **入口校验不一致**：`KnowledgePublisher.publish_candidate` 仅在 `similar_entries` 非空时才校验 `VALID_CONFLICT_STRATEGIES`；调用方在无冲突路径上误传 `conflict_strategy="garbage"` 不会被拦截，调用契约不可预期。
3. **CLI "放弃" 语义重叠**：`--action=abandon` 与 `--action=accept --strategy=abandon` 都把候选状态置 `abandoned` 且不发布，但前者无视冲突探测、后者只在冲突分支生效。canonical surface 暴露两条路径但语义差异不显式，对用户和 Agent 都是噪声。
4. **session 侧 archive-time 触发证据只剩 logger**：`SessionManager._trigger_memory_extraction` 失败时只走 `logger.warning(..., exc_info=True)`，没有任何 session 级别的文件证据；FR-307 "提取失败必须安全降级" 当前完全靠 orchestrator 层 batch 文件兜底——若 orchestrator 实例化本身失败（如 `_storage` 初始化异常），整条触发链路只剩内存日志，违反 "transparent + auditable" 用户契约。

愿景上下文：`docs/soul/growth-strategy.md` Stage 2 → Stage 3 的过渡条件之一是 "用户开始期望系统自动帮我做更多"。在那之前，Stage 2 的 polish 必须先把"自动化的可审计性"打牢——否则 Stage 3 的"工匠 / 自动 skill 生成"就会建立在一个会原地覆盖、悄无声息丢证据的底座上。

## 2. 目标与成功标准

### 2.1 核心目标

让 F003 已上线的 memory pipeline 在以下 4 个维度达到 v1.1 稳态：

```
重复发布 → 走 KnowledgeStore.update() 的 version+=1，可冷读历史
入口校验 → 任何路径误传 conflict_strategy 都被立刻拒绝
abandon  → CLI surface 单一职责，文档可被冷读到差异
session  → archive-time 提取失败永远在文件层留痕
```

### 2.2 成功标准

1. **同一候选 N 次发布 = 1 条 KnowledgeEntry，version=N**：用户可从 git history 或 `KnowledgeStore.list_entries()` 看到完整版本链。
2. **入口校验立即生效**：任何无效 `conflict_strategy` 在 publisher 入口处即被拒绝，不依赖冲突分支命中。
3. **CLI surface 单一职责**：用户文档（`docs/guides/garage-os-user-guide.md`）能用 1 段话讲清"主动放弃整条候选" vs "因冲突放弃发布"的差异，且 CLI help / `--action` choices 与之一致。
4. **FR-307 session 层证据零盲点**：archive-time 触发链路任意点失败（包括 orchestrator 实例化、`is_extraction_enabled()` 抛错、`extract_for_archived_session()` 抛错）都在 `sessions/archived/<id>/` 留下可机器读取的 JSON 证据。
5. **零 F003 主链回归**：`pytest tests/ -q` 在 384 测试基线上 ≥384 passed；F003 现有 145 个 memory-pipeline focused 测试不变绿。

### 2.3 非目标

- 不重新设计 `KnowledgeEntry` schema，只在 publisher 层引入"发布 ID 生成器"间接层。
- 不引入 LLM 或语义相似度算法升级 conflict 探测。
- 不为 `_trigger_memory_extraction` 引入异步队列、重试或常驻服务。
- 不改变 F003 已批准的 4 类候选契约（decision / pattern / solution / experience_summary）。
- 不引入新的 CLI 顶级命令；只在现有 `garage memory review` 上做语义收敛与文档化。

## 3. 用户角色与关键场景

### 3.1 主要用户角色

- **Solo Creator**：会重复 `accept` 同一候选（编辑后再确认、改 tag 重发）的用户。期望看到完整版本链，不是被"原地覆盖"。
- **Developer / Pack 作者**：直接调用 `KnowledgePublisher.publish_candidate(...)` 的下游（包括未来的 Stage 3 自动化路径）。期望入口契约严格、错误立即可见。
- **运行时审计读者**（用户自己 / 未来的 reviewer agent）：在某个 session 出问题时回查 `.garage/sessions/archived/<id>/` 期望"提取试过、试出了什么"全程留痕。

### 3.2 关键场景

1. **重复 accept 同一候选**：用户先 `accept` candidate `c-001` → 拼出 `KnowledgeEntry id=k-...-v1, version=1`；隔一会儿在 `edit_accept` 同一候选改 tag 后再发布 → 系统**保留 v1**、新写 `id=k-...-v1, version=2`，磁盘上仍是同一个 markdown 文件，front matter 的 `version` 字段递增。
2. **publisher 入口误传策略值**：调用方传 `conflict_strategy="garbageX"`，无论是否命中相似条目，publisher 都立刻 `ValueError` 报"Allowed: ['abandon', 'coexist', 'supersede']"。
3. **CLI 放弃路径**：用户用 `garage memory review <bid> --candidate-id c --action=abandon` 主动放弃一条候选（**与冲突无关**），候选状态 `abandoned`、不写入 publisher、不写 confirmation。用户 `--action=accept --candidate-id c --strategy=abandon` 仅在 publisher 命中相似条目时被触发，候选状态 `abandoned`、写 confirmation 留痕（说明"曾尝试发布但因冲突放弃"）。
4. **archive-time 触发链路全失败**：`_trigger_memory_extraction` 在任何点抛错，session 仍归档成功，且 `.garage/sessions/archived/<id>/memory-extraction-error.json` 含 `error_type / error_message / triggered_at / phase` 等字段，可机器读取。
5. **F003 现有路径零回归**：FR-301 ~ FR-307 / NFR-301 ~ NFR-304 在 v1.1 行为下仍全部满足，145 个 memory focused 测试 + 384 个 full suite 测试不变绿。

## 4. 当前轮范围与关键边界

### 4.1 包含

| 功能 | 描述 |
|------|------|
| 发布身份解耦 | `KnowledgePublisher` 引入"发布 ID 生成器（publication identity generator）"间接层；同一候选重复发布走 `KnowledgeStore.update()`，触发 `version+=1`，markdown 文件名稳定 |
| 入口校验前置 | `publish_candidate` 在入口立即校验 `conflict_strategy` 合法性（仅当 caller 显式传值时；`None` 仍按"无冲突 → 不需要"或"有冲突 → 拒绝"现有语义） |
| `abandon` 语义差异化 | CLI `--action=abandon` 与 `--action=accept --strategy=abandon` 在文档与 confirmation 留痕上可被独立识别；canonical 行为差异写入用户指南 |
| session 触发证据持久化 | `SessionManager._trigger_memory_extraction` 在任何失败点写 `sessions/archived/<id>/memory-extraction-error.json`；orchestrator 内部失败仍由 batch 文件兜底，不双写冗余 |
| 兼容性回归测试 | 同 candidate 重复 accept、入口误传值、CLI abandon 双路径、session 触发链路三段失败点，全部新增覆盖；F003 145 个 memory focused 测试 0 回归 |
| 文档同步 | `docs/guides/garage-os-user-guide.md`（CLI 用户面）+ `docs/guides/garage-os-developer-guide.md`（publisher 调用契约）+ `RELEASE_NOTES.md`（v1.1 段） |

### 4.2 不包含

- 任何 `KnowledgeEntry.id` schema 变更（仍是 string；只引入 `_id_generator(candidate_id, payload, version)` 间接层）
- 任何 `KnowledgeStore.store/update` 行为契约变更
- 任何 LLM-based 候选去重 / 相似度升级
- 任何新的 CLI 顶级命令或子命令
- 引入异步 / 队列 / 后台服务承接 `_trigger_memory_extraction`
- 改变 F003 已批准的 4 类候选 contract

## 5. 范围外内容

- 多用户共享知识 / 跨用户审计
- Stage 3 "自动 skill 生成" 任何代码路径
- 把 memory pipeline 拆到独立 pack
- `KnowledgeEntry.id` 体系层级化（如增加 namespace / scope）

## 6. 术语与定义

| 术语 | 定义 |
|------|------|
| **发布身份 (publication identity)** | `KnowledgeEntry.id` 与 `ExperienceRecord.record_id` 在磁盘 / 索引上的唯一键 |
| **候选身份 (candidate identity)** | `MemoryCandidate.candidate_id`，由 orchestrator 在批次写盘时生成 |
| **重复发布 (re-publication)** | 同一 `candidate_id` 被 publisher 处理多于 1 次（典型路径：`accept` → 用户改 tag → `edit_accept`） |
| **触发证据 (trigger evidence)** | session 归档时尝试调用 memory extraction 的可机器读取持久记录 |
| **canonical surface** | CLI 用户面对 memory pipeline 显式暴露的命令、参数、行为说明 |

## 7. 功能需求

### FR-401 重复发布必须保留版本链

- **优先级**: Must
- **来源**: F003 code-review r2 finding 5 (USER-INPUT delayed); F001 FR-002 "知识版本追踪"
- **需求陈述**: 当 `KnowledgePublisher` 处理同一 `candidate_id` 的第 N 次发布时，系统必须保证目标 `KnowledgeEntry` 仍是同一条（同一磁盘文件 / 同一 id），且 front matter 的 `version` 字段从 N-1 递增为 N。
- **验收标准**:
  - Given 同一 candidate `c-001` 已被 `accept` 一次（`KnowledgeEntry id=k-foo, version=1`），When 同一 candidate 再次被 `edit_accept` 处理，Then `KnowledgeStore` 上仍只有 1 条 `id=k-foo` 的 entry，且 `version=2`，markdown 文件名不变
  - Given 同一 candidate 已发布 2 次，When 用户 `KnowledgeStore.retrieve(type, "k-foo")`，Then 返回最新 version=2 的内容；git history 可回读 v1 → v2 的 diff
  - Given 同一 candidate 走 ExperienceRecord 路径（`experience_summary`）重复发布，When 第 2 次发布完成，Then `ExperienceIndex` 中仍只有 1 条 `record_id` 与之对应，更新动作走 `ExperienceIndex` 的现有 update 语义而非新建

### FR-402 publisher 入口必须立即校验 conflict_strategy

- **优先级**: Must
- **来源**: F003 code-review r2 minor LLM-FIXABLE (CR3); 调用契约可预期性
- **需求陈述**: 当 `KnowledgePublisher.publish_candidate` 被显式传入 `conflict_strategy` 时，系统必须在入口立即校验该值是否在 `VALID_CONFLICT_STRATEGIES` 集合内，校验时机不依赖是否命中相似条目。
- **验收标准**:
  - Given 调用方显式传 `conflict_strategy="garbageX"`，When 该候选不命中任何相似条目，Then `publish_candidate` 抛 `ValueError` 含 "Allowed: ['abandon', 'coexist', 'supersede']"
  - Given 调用方显式传 `conflict_strategy="coexist"`，When 该候选不命中相似条目，Then `publish_candidate` 正常发布且行为与 v1 一致（不报错）
  - Given 调用方传 `conflict_strategy=None`，When 候选不命中相似条目，Then 行为与 v1 一致（正常发布）
  - Given 调用方传 `conflict_strategy=None`，When 候选命中相似条目，Then 行为与 F003 FR-304 一致（抛 `ValueError` 要求显式选择）

### FR-403a confirmation 持久面必须可独立识别两条 abandon 路径

- **优先级**: Must
- **来源**: F003 code-review r2 minor LLM-FIXABLE (CR5/CR4)
- **需求陈述**: 当用户使用 CLI `garage memory review` 的任一 abandon 路径时，系统必须在 confirmation 持久记录上让两条路径可被冷读区分。
- **验收标准**:
  - Given 用户运行 `--action=abandon`，When CLI 处理完成，Then 候选 `status=abandoned`；confirmation 文件 `resolution=abandon` 且 `conflict_strategy=null`
  - Given 用户运行 `--action=accept --strategy=abandon` 且 publisher 命中相似条目，When abandon 早返回，Then 候选 `status=abandoned`；confirmation 文件 `resolution=accept` 且 `conflict_strategy=abandon`
  - Given 用户运行 `--action=accept --strategy=abandon` 且 publisher 不命中相似条目，When 退化为正常 accept 发布，Then 候选 `status=published`；confirmation 文件 `resolution=accept` 且 `conflict_strategy=null`（与 F003 v1 一致）

### FR-403b CLI 输出文案必须显式区分两条 abandon 路径

- **优先级**: Must
- **来源**: F003 code-review r2 minor LLM-FIXABLE (CR5/CR4); 用户契约 "透明可审计"
- **需求陈述**: 当用户使用 CLI `garage memory review` 的两条 abandon 路径时，系统必须在 stdout 输出可被独立识别的提示语，使用户在不读 confirmation 文件的情况下就能区分。
- **验收标准**:
  - Given 用户运行 `--action=abandon`，When CLI 处理完成，Then stdout 至少包含一段含 "abandoned candidate without publication attempt" 含义的中英文之一稳定标识符
  - Given 用户运行 `--action=accept --strategy=abandon` 且命中相似条目，When abandon 早返回，Then stdout 至少包含一段含 "abandoned due to conflict" 含义的中英文之一稳定标识符
  - Given 同一 CLI 子命令的两条路径，When 用户用 `grep` 或日志搜索区分，Then 两条路径的标识字符串不重叠

### FR-403c 用户文档必须显式说明两条 abandon 路径的差异

- **优先级**: Must
- **来源**: F003 code-review r2 minor LLM-FIXABLE (CR5/CR4); 设计原则 "约定可发现"
- **需求陈述**: 当用户阅读 `docs/guides/garage-os-user-guide.md` 的 memory review 段时，系统文档必须用至少 1 段话讲清两条 abandon 路径的差异（语义、何时使用、对 confirmation 持久产物的影响）。
- **验收标准**:
  - Given `docs/guides/garage-os-user-guide.md` 含 memory review 段，When 读者搜索 "abandon"，Then 至少能命中 1 段独立说明
  - Given 该说明段，When 读者读完，Then 能正确回答 "我应该用 `--action=abandon` 还是 `--action=accept --strategy=abandon`？"
  - Given 该说明段，When 读者关心持久产物，Then 段落显式列出两条路径下 confirmation 文件的字段差异

### FR-404 archive-time 触发链路必须文件级留痕

- **优先级**: Must
- **来源**: F003 code-review r2 minor LLM-FIXABLE (CR3); FR-307 安全降级 + 用户契约 "透明可审计"
- **需求陈述**: 当 `SessionManager._trigger_memory_extraction` 在 archive-time 任何阶段（orchestrator 实例化、`is_extraction_enabled` 调用、`extract_for_archived_session` 调用）抛出异常时，系统必须在 `sessions/archived/<session_id>/` 写入 `memory-extraction-error.json`，记录 `phase` / `error_type` / `error_message` / `triggered_at`，且 session 归档结果保持 `archive_session()=True`。
- **验收标准**:
  - Given orchestrator 实例化抛错（如 `MemoryExtractionOrchestrator(...)` 构造异常），When `_trigger_memory_extraction` 调用，Then `archive_session()` 仍返回 `True`；磁盘 `sessions/archived/<id>/memory-extraction-error.json` 存在且 `phase="orchestrator_init"`
  - Given `is_extraction_enabled()` 抛错，When `_trigger_memory_extraction` 调用，Then 同上文件存在且 `phase="enablement_check"`
  - Given `extract_for_archived_session()` 抛错，When `_trigger_memory_extraction` 调用，Then 同上文件存在且 `phase="extraction"`；orchestrator 自身的 batch-level 错误证据（`evaluation_summary=extraction_failed`）仍按 F003 行为写入，但 session 侧错误文件**不重复写**冗余信息（仅留 session-level summary）
  - Given 触发链路成功完成（无异常），When 归档结束，Then `memory-extraction-error.json` 不存在；行为与 F003 一致

### FR-405 兼容现有 F003 契约

- **优先级**: Must
- **来源**: F003 NFR-304 "与 Phase 1/2 现有能力兼容"
- **需求陈述**: 当本轮 v1.1 修改部署后，F003 已批准的 FR-301 ~ FR-307 / NFR-301 ~ NFR-304 的所有验收标准必须仍然通过。
- **验收标准**:
  - Given F003 现有 `tests/memory/` 测试集与 145 个 memory focused 测试，When `pytest tests/memory/ -q`，Then 全部仍 passed
  - Given F003 完整 384 个测试基线，When `pytest tests/ -q`，Then ≥384 passed
  - Given 本轮新增测试，When `pytest tests/ -q`，Then 新增用例与 F003 现有用例无互相干扰

## 8. 非功能需求

### NFR-401 发布身份生成必须可冷读

- **优先级**: Must
- **来源**: 设计原则 "文件即契约"
- **需求陈述**: 当 publisher 把 candidate 转成 publication identity 时，系统必须保证生成规则在 publisher 模块代码或开发者文档中可被独立读懂，且不依赖运行时随机性（同一 input 多次调用生成同一 id）。
- **验收标准**:
  - Given 同一 candidate payload 与 confirmation_ref，When 调用发布身份生成器 N 次，Then 返回值完全相同
  - Given 开发者读 publisher 模块与开发者文档，When 想知道某条已发布知识的 id 是怎么生成的，Then 能在不跑代码的情况下复现规则
  - Given 任意已发布 entry，When 沿用同一份 candidate payload + confirmation_ref 再次调用发布身份生成器，Then 得到与已发布 entry 完全相同的 id（保证 update 路径可命中）

### NFR-402 不引入运行时性能退化

- **优先级**: Should
- **来源**: F003 NFR-303 Stage 2 性能门槛
- **需求陈述**: 当 v1.1 修改部署后，单 session 候选生成与单次 publish_candidate 调用的运行时长不应较 F003 baseline 退化超过 10%。
- **验收标准**:
  - Given F003 baseline `pytest tests/memory/ -q` 总时长 T0，When v1.1 部署后同一 suite 跑 N 次取均值 T1，Then `T1 ≤ 1.1 * T0`

## 9. 外部接口与依赖

### IFR-401 KnowledgeStore.update 现有契约

- **优先级**: Must
- **来源**: F001 KnowledgeStore 现有 `update()` 实现 (`version += 1`)
- **需求陈述**: 系统必须复用 `KnowledgeStore.store/update` 现有契约（包括 `_remove_from_index` + `store` 的 incremental index 路径），不修改其签名或行为。
- **验收标准**:
  - Given v1.1 publisher 走重复发布路径，When 调用 KnowledgeStore，Then 调用顺序为 `retrieve` → 若存在 `update` 否则 `store`，签名与 F001 一致
  - Given KnowledgeStore 单元测试，When `pytest tests/knowledge/ -q`，Then 全绿无回归

### IFR-402 ExperienceIndex update 路径

- **优先级**: Must
- **来源**: F001 ExperienceIndex 现有实现
- **需求陈述**: 系统必须复用 ExperienceIndex 现有"已存在 record_id 时的更新语义"；如该路径不存在，则在 v1.1 内新增最小补丁，不破坏 F003 现有验收。
- **验收标准**:
  - Given 重复发布 `experience_summary` candidate，When publisher 调 ExperienceIndex，Then 索引中仅 1 条 record_id；行为可被读测试断言

## 10. 约束

### CON-401 Workspace-first

- **优先级**: Must
- **来源**: F003 CON-301
- **需求陈述**: `memory-extraction-error.json` 与所有版本链都必须存在 `.garage/` 内、git 可追踪。

### CON-402 不引入外部依赖

- **优先级**: Must
- **来源**: F003 CON-304
- **需求陈述**: 不新增 PyPI 包、不引入数据库、不引入常驻服务。

### CON-403 schema 演进可兼容

- **优先级**: Must
- **来源**: F003 CON-303
- **需求陈述**: `confirmation_ref` 与 `KnowledgeEntry.front_matter` 在 v1.1 后旧版数据仍可读；新增字段只追加、不删除已有字段。

### CON-404 文件契约可被冷读

- **优先级**: Must
- **来源**: 设计原则 "文件即契约"
- **需求陈述**: 任何新增 JSON 持久产物（`memory-extraction-error.json`）必须 schema 显式声明字段集合，并在用户/开发者文档中可被检索。

## 11. 假设

### ASM-401 KnowledgeStore.update 已经原子且 incremental-index 可用

- **优先级**: Should
- **来源**: F001 实现现状
- **失效风险**: 若 update 实现中存在已知 race / index 漂移，重复发布场景会触发新问题
- **缓解措施**: 在 design stage 复检 `KnowledgeStore.update` 路径与索引一致性测试

### ASM-402 同 candidate 重复发布场景在第一版用户量小

- **优先级**: Should
- **来源**: F003 finalize 时对 finding 5 的延后理由
- **失效风险**: 若用户大量"先 accept 后改"，性能与 git diff 噪声会显著
- **缓解措施**: 文档显式建议用户在 `edit_accept` 前优先用 `--action=defer`

### ASM-403 性能基准脚本可能尚未覆盖 publisher 路径

- **优先级**: Should
- **来源**: NFR-402 验收标准的可执行性
- **需求陈述**: 假设当前 `scripts/benchmark.py` 不一定覆盖 publisher 重复发布路径；如需性能验收的第二条独立证据，由 design / tasks stage 决定是否补 publisher 专项基准。
- **失效风险**: 如果 design stage 不补该基准，NFR-402 只能用 `pytest tests/memory/ -q` 的 wall-clock 作为唯一验收口径，对 publisher 局部回归的 perf 可见度有限。
- **缓解措施**: design stage 显式裁决是否在 `scripts/benchmark.py` 中追加 publisher 专项；不追加亦可，但需在 design 文档中说明为什么 wall-clock suite 已经够用。

## 12. 开放问题

非阻塞、可在 design stage 收敛：

1. 发布 ID 生成器是否需要暴露给配置（如 `platform.json` 的 `memory.publication_id_strategy`），还是写死为单一规则？默认建议**写死**，由 design 决定。
2. `memory-extraction-error.json` 是否需要在每次新错误时累加为 array（保留历史），还是只保留最近一次？默认建议**只保留最近一次**，因为设计上 archive-time 触发对每个 session 只发生一次。
3. CLI `--action=abandon` 是否需要在用户文档中标记为"建议优先于 reject"（前者表达用户意图，后者表达系统判断不通过）？由 design 决定文档措辞。

无阻塞性开放问题。

---

**文档状态**: 草稿，待 `hf-spec-review`。

**下一步**: 派发 reviewer 执行 `hf-spec-review`。
