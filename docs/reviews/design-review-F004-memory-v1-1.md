# Design Review — F004 Garage Memory v1.1（发布身份解耦与确认语义收敛）

- 评审范围: `docs/designs/2026-04-19-garage-memory-v1-1-design.md`（草稿）
- Review skill: `hf-design-review`
- 评审者: cursor cloud agent (auto mode, reviewer subagent，由 `hf-design` 父会话派发)
- 日期: 2026-04-19
- Workflow Profile / Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- 上游证据基线:
  - 已批准规格: `docs/features/F004-garage-memory-v1-1-publication-identity-and-confirmation-semantics.md`
  - 上游 spec approval: `docs/approvals/F004-spec-approval.md`（auto-mode 已批准）
  - 上游 spec review: `docs/reviews/spec-review-F004-memory-v1-1.md`（结论：通过）
  - 现有实现: `src/garage_os/memory/publisher.py`、`src/garage_os/runtime/session_manager.py`、`src/garage_os/cli.py`、`src/garage_os/knowledge/knowledge_store.py`、`src/garage_os/knowledge/experience_index.py`
  - `task-progress.md`（Stage = `hf-design` 草稿已落盘 → 待 `hf-design-review`，profile/mode 一致）
  - `AGENTS.md` 项目约定 + `docs/soul/{manifesto,user-pact,design-principles,growth-strategy}.md`

## 1. Precheck

| 检查项 | 结果 |
|--------|------|
| 存在稳定可定位 design draft | ✓ `docs/designs/2026-04-19-...md` 草稿完整、632 行、18 章齐备，含 ADR / 接口契约 / 测试矩阵 / 失败模式 |
| 已批准规格可回读 | ✓ F004 spec 已批准（auto-mode），FR-401~405 / NFR-401/402 / IFR-401/402 / CON-401~404 / ASM-401~403 全部稳定 |
| route / stage / profile 一致 | ✓ task-progress Stage=`hf-design`，Pending=`hf-design-review`，profile=`full`，mode=`auto` |
| F004 不含 UI surface | ✓ 规格无前端/页面/组件，本评审独立可定结论，不需等待 `hf-ui-review` peer |
| 上游证据无冲突 | ✓ spec-review 3 项 minor 在 spec approval 前已经全部由 author 顺手收敛（A3 / A2 / C1），design 沿用收敛后版本 |

Precheck 通过，进入正式 rubric。

## 2. 多维 rubric 审查

### 2.1 D1 需求覆盖与追溯

**评分**: 9/10

设计 §3 提供完整 FR/NFR/IFR/CON 追溯矩阵：

| 规格条目 | 设计承接 | 验证 |
|----------|----------|------|
| FR-401 重复发布版本链 | §7.1 + §10.1 + §11.2 + ADR-401 + §13.2 测试 T1 | ✓ |
| FR-402 入口校验前置 | §7.1 + §10.2 + §11.2 + ADR-402 | ✓ |
| FR-403a confirmation 持久差异化 | §10.3 + §11.5 + ADR-403 + §13.2 | ✓ |
| FR-403b CLI 输出文案 | §11.5 + §10.3 表格 | ✓ |
| FR-403c 用户文档段 | §9 表格（user-guide.md "Memory review abandon paths" 段）+ §13.2 | ✓ |
| FR-404 session 触发证据 | §7.1 + §8.3 + §10.4 + §11.3/§11.4 + ADR-404 + §13.2 T4 | ✓ |
| FR-405 兼容性 | §3 + §13.3（145 + 384 全 suite 0 回归承诺） | ✓ |
| NFR-401 决定性发布身份 | §11.1 不变量 + §12 落地表 + §16 ADR-401 | ✓ |
| NFR-402 不退化 | §12 + §6 trade-off 列 + ASM-403 决议（§12 末尾段） | ✓ |
| IFR-401/402 复用 update | §10.1 数据流 + §11.2 contract + §9 边界 | ✓ |
| CON-401~404 | §12 落地表逐条映射 | ✓ |
| ASM-401/402/403 | §13.3 + §12 末尾段 ASM-403 决议 + §17 延后项呼应 ASM-402 | ✓ |

无悬空规格条目。每条 FR 都映射到具体模块 / 文件路径 / 函数 / 测试名建议，不是松散组件清单。

### 2.2 D2 架构一致性

**评分**: 9/10

- §4 模式选择给出 4 个命名（Idempotent Publication / Fail-Loud-At-Boundary / Side-Effect Discrimination / Defense-In-Depth Logging），都不是标准 GoF 名称但描述性足够冷读
- §8.1 模块依赖图显式标注 v1.1 改动点 + 不变模块；与 D003 拓扑保持一致
- §8.2 / §8.3 给出"重复发布"与"3 phase 失败"两个关键交互的 sequence diagram，覆盖正常路径与失败路径
- §9 边界表显式列出"v1.1 改 / 不改"，与 §4.2 / §17 排除项呼应
- 与现有实现核对：§9 声明"不修改 KnowledgeStore / ExperienceIndex / CandidateStore"，与代码现状一致；publisher 为唯一新增 helper class 的承载位置

### 2.3 D3 决策质量与 trade-offs

**评分**: 8/10

- §5 + §6 给出 4 组真实可比较的方案（A1/A2、B1/B2、C1/C2、D1/D2），不是稻草人：
  - A2 是合理替代（KnowledgeStore.upsert 集中语义），代价是动 F001 公开契约
  - C2 是合理替代（新字段 abandon_kind 更直观），代价是破坏 CON-403
  - D2 是合理替代（safe_call 包装器），代价是单一调用点过度抽象
  - B2 (装饰器) YAGNI 拒绝合理
- §6 trade-off 表覆盖 优点 / 主要代价 / NFR 适配 / 可逆性 4 列，可冷读
- §16 ADR 摘要逐条给出 上下文 / 决策 / 后果 / 可逆性 / 被淘汰方案，与 §5/§6 形成闭环
- 1 处可改进：§6 中 A1 vs A2 在"主要代价"列写得过简（仅"多 1 次 retrieve"），SOC 维度的关键论据需要回 §16 ADR-401 才能拼齐冷读 → minor

### 2.4 D4 约束与 NFR 适配

**评分**: 9/10

- §12 落地表逐条把 NFR-401/402 + CON-401~404 映射到具体落地点 + 验证方式
- ASM-403 在 §12 末尾段做出明确裁决：**不在 `scripts/benchmark.py` 追加 publisher 专项基准**，理由：O(1) in-memory index lookup + YAGNI；裁决可被 reviewer 挑战
- CON-403 schema 兼容硬约束被 ADR-403 承接（不引入 `abandon_kind` 新字段）
- CON-401 workspace-first 被 ADR-404 承接（错误文件写到 `.garage/sessions/archived/<id>/`）
- CON-404 文件契约可冷读：§11.4 给出 `memory-extraction-error.json` 完整 schema + 显式封闭枚举 phase

### 2.5 D5 接口与任务规划准备度

**评分**: 6.5/10 ← **本轮关键失分点**

- §11.1~§11.5 给出 5 个接口契约，覆盖发布身份生成器 / publish_candidate 入口契约 / SessionManager 持久化契约 / error JSON schema / CLI 输出常量
- §15 任务规划准备度 explicit checklist；§13.1 walking skeleton 可作为 hf-test-driven-dev T1 起点

**关键缺口（导致评分降到 6.5）**：

§10.1 数据流仅显式 carry-over `entry.related_decisions = existing.related_decisions`，未要求 publisher 在 update 路径上同时 carry-over `existing.front_matter["supersedes"]` 与 `existing.front_matter["related_decisions"]`。这构成 **supersede 链丢失隐患**：

- F003 publisher 实现中（`publisher.py:87-95`），首次以 `strategy=supersede` 发布会写：
  - `entry.related_decisions = existing + similar_entries`
  - `entry.front_matter["related_decisions"] = list(existing)`
  - `entry.front_matter["supersedes"] = list(similar_entries)`
- v1.1 重复发布链路调用 `_to_knowledge_entry(payload, ...)` 会**重新构造**一个 entry，其 `front_matter` 仅含 `source_evidence_anchor` / `confirmation_ref` / `published_from_candidate`，**完全丢失 `supersedes` 与 `related_decisions` 历史**
- 设计 §10.1 提到 "不丢失冲突 supersede 链" 但只 carry-over `entry.related_decisions`，**未 carry-over `front_matter["supersedes"]`**，落地不全
- §18#1 已显式承认该不变量需要 publisher 层 carry-over，并指派 "task T2 实现时必须覆盖"，但**该不变量留在 §18 开放问题列表，未升格进入 §11.2 接口契约或 §10.1 数据流伪代码**

**为什么这是 D5 important（不是 minor）**：
- D5 的 pass condition 是"hf-tasks 不需要替设计补洞"。当前需要 hf-tasks 主动从 §18 拉一条额外 invariant 进 T2，且测试矩阵 §13.2 也未列对应回归测试名（"v1 已发布 + 带 supersede 链 → v1.1 重复 update 后仍含 supersedes / related_decisions"），存在跨章节漏读风险
- iron law 4 "权衡必须显式文档化"：correctness invariant 不应该落在 backlog 章节
- 修复成本极小：把 §10.1 / §11.2 各加 1-2 行明确 carry-over 列表

### 2.6 D6 测试准备度与隐藏假设

**评分**: 7.5/10

- §13.1 walking skeleton 可作为 RGR 起点，断言 version 递增可观测
- §13.2 测试矩阵覆盖 FR-401~405 / NFR-401 / 错误文件 schema，给出建议测试名
- §13.3 已知会被触动的 3 个测试列表，预测合理
- §13.4 沿用 F003 testDesignApproval 治理路径
- §14 失败模式表覆盖 5 项，主路径 + 边界路径 + 自身写盘失败均涉及

**隐藏假设 / 缺口**：
1. §13.2 缺 supersede 链 carry-over 回归测试（与 D5 finding 同根因）
2. **未显式讨论 self-conflict false-positive 假设**：重复 `accept` / `edit_accept` 同一 candidate 时，`ConflictDetector.detect(title, tags)` 完全可能把 v1 已发布的同名 entry 当作 similar entry 返回（其 id 等于 candidate_id 本身）；这会让 CLI `cli.py:485` 强制要求用户传 `--strategy=...`，与"重复 accept 走 update 链"的设计意图冲突。设计未明确 publisher / CLI 在 retrieve 命中 existing 后是否要短路 conflict detection，也未在 §14 把这种交互列为失败模式或在 §11.2 contract 中说明
3. §11.1 命名漂移：`PublicationIdentityGenerator` 暴露 `derive_knowledge_id` / `derive_experience_id` 两方法，但 §7.1 / §10.1 伪代码混用 `pub_id_generator.derive(candidate_id, type)` / `exp_id_generator.derive(candidate_id)` / `derive_id(candidate_id, "decision")` 三种写法，hf-tasks T1 拆解时容易引入命名漂移

### 2.7 Anti-Pattern 扫描

| ID | 反模式 | 命中 | 说明 |
|---|---|---|---|
| A1 无 NFR 评估 | ✗ | NFR-401/402 + CON-401~404 + ASM-403 都进入了具体落地点 |
| A2 只审 happy path | ✗ | §14 + §10.4 + §13.2 覆盖 3 phase 失败 + accept-with-abandon 退化 |
| A3 无权衡文档 | ✗ | §6 + §16 ADR 完整 |
| A4 单点故障未记录 | △ | session-触发链路是单点，但 §14#3 记录"自身写盘失败 → logger.warning 双层防护"，可接受 |
| A5 实现后评审 | ✗ | 评审在实现前 |
| A6 上帝模块 | ✗ | publisher 改动有清晰边界（仅 helper class + 入口校验 + store-or-update 决策） |
| A7 循环依赖 | ✗ | §8.1 单向依赖图 |
| A8 分布式单体 | ✗ | 不涉及 |
| A9 task planning gap | △ | §10.1 supersede carry-over invariant 下放 §18 backlog → 命中（见 D5 finding） |

## 3. 关键独立判断（用户指定的 supersede carry-over 重点）

用户在派发指令中要求独立判断 3 个子问题：

1. **F004 设计是否覆盖 "v1 已发布 + 带 supersede 链 → v1.1 重复发布" 的不变量保留？**
   - **部分覆盖**。§18#1 显式识别该不变量，但 §11.2 接口契约 + §10.1 数据流伪代码只 carry-over `entry.related_decisions`，未 carry-over `entry.front_matter["supersedes"]` 与 `entry.front_matter["related_decisions"]`
   - 直接证据：当前 `_to_knowledge_entry()`（publisher.py:114-147）构造 `front_matter` 时仅写入 3 个键（`source_evidence_anchor` / `confirmation_ref` / `published_from_candidate`），不含 `supersedes` 与 `related_decisions`；调用 `KnowledgeStore.update(entry)` 会以新 front_matter 整体覆盖旧文件 front_matter（参见 `knowledge_store.py:73 + 360-384`，`_entry_to_front_matter` 完全从 entry 字段重建 front_matter，不读旧文件）
   - 结论：**v1 supersede 链在 v1.1 重复发布后会被静默清空**，违反 FR-405 兼容性（F003 已发布数据的 front_matter["supersedes"] 不应在 v1.1 部署后丢失）

2. **publisher 调 update 前是否需要把 `entry.front_matter["supersedes"]` 也从 existing carry-over？**
   - **是**。同时也必须 carry-over `entry.front_matter["related_decisions"]`（虽然 entry.related_decisions carry-over 后 KnowledgeStore.store 会重新写 front_matter["related_decisions"]，但 supersedes 字段不在 dataclass 字段中，没有 store 侧自动同步）

3. **这是否构成阻塞 finding？**
   - **不构成阻塞（critical）**，但**构成 important**。理由：
     - 设计已识别（§18#1），距离 contract 化只差 1-2 行 + 1 条测试条目
     - F004 是收敛 cycle，author 已经做了细致 trade-off 分析；返回 1 轮代价低
     - 不修复就会在 v1.1 部署后产生静默数据丢失（FR-405 违反），符合 important 标准 "应在批准前修复"
     - 不到 critical 等级（不是阻塞 hf-tasks 拆解整体，只是会导致 T2 漏读 §18 时 ship regression）

## 4. 发现项

> 0 critical / 1 important / 3 minor。所有 finding 均 LLM-FIXABLE，可在一轮定向修订中收敛。

- `[important][LLM-FIXABLE][D5]` §10.1 数据流与 §11.2 接口契约只 carry-over `entry.related_decisions = existing.related_decisions`，未要求 publisher 在 update 路径上同时 carry-over `existing.front_matter["supersedes"]` 与 `existing.front_matter["related_decisions"]`。该不变量目前只在 §18#1 backlog 中点名，未升格进入 §11.2 contract 或 §13.2 测试矩阵。直接后果：v1 已带 supersede 链的 entry 在 v1.1 重复 `edit_accept` 后会**静默清空 front_matter["supersedes"]**，违反 FR-405 兼容性（F003 已发布数据 schema 不能丢字段）。修订建议：将 §10.1 伪代码与 §11.2 update 路径契约扩展为显式列出"必须 carry-over 的 front_matter 键集合"（至少含 `supersedes`、`related_decisions`），并在 §13.2 增加 1 条测试名 `test_repeated_publish_preserves_supersedes_chain_from_v1`。
- `[minor][LLM-FIXABLE][D6]` 重复 `accept` / `edit_accept` 同一 candidate 时，`ConflictDetector.detect(title, tags)` 可能把 v1 已发布的同名 entry 误识为 similar entry（self-conflict false-positive），导致 CLI `cli.py:485` 强制要求用户传 `--strategy=...`，与"重复 accept 自动走 update 链"的设计意图冲突。设计未在 §14 / §11.2 / §10.1 显式说明 publisher 是否要在"retrieve 命中 existing 且 similar_entries 仅含自身 id"的情况下短路 conflict 处理；该假设当前隐藏。修订建议：在 §11.2 contract 显式约束"similar_entries 中等于 derive_*_id(candidate_id) 的元素必须先剔除再判 conflict_strategy 要求"，或在 §14 列入对应失败模式。
- `[minor][LLM-FIXABLE][D5]` §11.1 接口契约暴露 `PublicationIdentityGenerator.derive_knowledge_id(candidate_id, knowledge_type)` 与 `derive_experience_id(candidate_id)`，但 §7.1 / §8.2 / §10.1 伪代码混用 `pub_id_generator.derive(candidate_id, type)` / `exp_id_generator.derive(candidate_id)` / `derive_id(c-001, "decision")` 三种写法。命名漂移使 hf-tasks T1 拆解 generator API 时可能引入与 contract 不一致的方法名。修订建议：把所有伪代码统一对齐 §11.1 的 `derive_knowledge_id` / `derive_experience_id`。
- `[minor][LLM-FIXABLE][D3]` §6 trade-off 表 A1 行"主要代价 / 风险"仅写"publisher 层多 1 次 retrieve"，未在同一行陈述与 A2 比较的 SOC（"职责切分清晰 vs F001 接口稳定性扩张"）。冷读 trade-off 时还需回 §16 ADR-401 才能拼齐被淘汰理由。修订建议：在 §6 A1 行末尾加一句"vs A2：保护 F001 KnowledgeStore 公开契约稳定性 + publisher 层职责单一"。

## 5. 缺失或薄弱项

- §13.2 缺 supersede 链 carry-over 回归测试（与 D5 important finding 同根因；列入 finding 修订建议）
- §11.4 `memory-extraction-error.json` schema 已显式 phase 封闭枚举，但未声明 `phase` 集合何时演进的版本管理规则；该 schema 是新文件可不做强约束，仅留作 minor 提示，**不写入 finding**
- 用户文档段落（§9 表中 user-guide.md "Memory review abandon paths"）只在 §9 表格列出，未在 §13.2 给出 build-time 检测策略外的 docs lint；可在 hf-tasks 阶段补，**不阻塞**

## 6. 结论

**需修改**

判断依据：
- 0 critical，但 1 项 important（D5）触发 "应在批准前修复" 红线
- 该 important finding 是 correctness invariant（FR-405 兼容性兜底，关键 supersede 不变量），现状只在 §18 backlog 中识别，未在 §11.2 contract / §10.1 伪代码 / §13.2 测试矩阵闭环；hf-tasks 跨章节漏读会让 T2 ship 静默数据丢失
- 修订成本极小（伪代码 + contract + 1 条测试名 = 1-2 行 + 1 行 + 1 个 bullet），单轮定向回修可消化
- 3 项 minor 均不阻塞，可顺手在同一轮收敛
- D1/D2/D3/D4/D6 五个维度均 ≥7.5，无 ≤6 关键失分；D5=6.5（=刚卡 important 触发线）
- 范围 / ADR / 候选方案 / 失败模式 / NFR 落地 / walking skeleton / 测试矩阵 大体完备，结构性 OK，仅一处 contract 升格 + 一处隐藏假设需要补
- route / stage / profile / 上游证据全部一致，**不需要 reroute via router**（无需求漂移、无规格冲突）

## 7. 下一步

- **`hf-design`**：用于回修上述 1 项 important + 3 项 minor finding。预期 1 轮内可完成定向修订，回修后由父会话再次派发 `hf-design-review` 复审或在 author 自查后转入 `设计真人确认`
- 不需要 reroute via router
- 因 F004 spec 不含 UI surface，不需 `hf-ui-review` peer 同步

## 8. 交接说明

- **`hf-design`**（修订）：父会话应把本评审结论 + finding 列表传回 design 起草节点；author 在 §10.1 / §11.2 / §13.2 三处定向修订即可。预期 diff < 30 行
- 复审策略建议：修订完成后由 author self-check 即可触发 `设计真人确认`，无需重新派发完整 reviewer subagent（只要 finding 列表 1:1 关闭）
- 不存在 USER-INPUT 类 finding，父会话不需要向用户发起额外问卷
- ASM-403（不补 publisher 专项 benchmark）已在 §12 显式裁决，**不需要回流 spec 阶段**

## 9. 结构化返回

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "hf-design",
  "record_path": "docs/reviews/design-review-F004-memory-v1-1.md",
  "key_findings": [
    "[important][LLM-FIXABLE][D5] §10.1/§11.2 仅 carry-over entry.related_decisions，未要求 publisher 在 update 路径同时 carry-over existing.front_matter['supersedes'] 与 ['related_decisions']；不变量只在 §18 backlog 点名，未升格进入 contract / 测试矩阵；导致 v1 已带 supersede 链的 entry 在 v1.1 重复 edit_accept 后静默清空 supersedes，违反 FR-405",
    "[minor][LLM-FIXABLE][D6] 重复 accept 同一 candidate 时 ConflictDetector 可能把 v1 已发布同名 entry 误识为 similar entry（self-conflict），与'重复 accept 自动走 update 链'设计意图冲突；§14/§11.2/§10.1 未显式说明 publisher 是否要在 retrieve 命中 existing 后短路 conflict 要求",
    "[minor][LLM-FIXABLE][D5] §11.1 contract 暴露 derive_knowledge_id/derive_experience_id，但 §7.1/§8.2/§10.1 伪代码混用 pub_id_generator.derive(...)、exp_id_generator.derive(...)、derive_id(...) 三种命名，hf-tasks T1 拆解 generator API 时易引入命名漂移",
    "[minor][LLM-FIXABLE][D3] §6 trade-off 表 A1 行'主要代价'仅写'多 1 次 retrieve'，未陈述与 A2 比较的 SOC 维度论据，冷读需回 §16 ADR-401 才能拼齐"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "D5",
      "summary": "§10.1/§11.2 supersede chain carry-over 仅覆盖 entry.related_decisions，未覆盖 entry.front_matter['supersedes']/['related_decisions']；不变量只在 §18 backlog 点名未升格 contract，导致 FR-405 兼容性兜底缺口"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D6",
      "summary": "重复 accept 同一 candidate 时 ConflictDetector self-conflict false-positive 假设隐藏，未在 §14/§11.2/§10.1 显式说明 publisher 短路策略"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D5",
      "summary": "PublicationIdentityGenerator 命名在 §11.1 contract 与 §7.1/§8.2/§10.1 伪代码间漂移（derive_knowledge_id vs derive_id vs pub_id_generator.derive）"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "D3",
      "summary": "§6 trade-off 表 A1 行'主要代价'缺与 A2 比较的 SOC 维度论据，冷读 trade-off 不闭环"
    }
  ],
  "rubric_scores": {
    "D1_requirement_coverage_traceability": 9,
    "D2_architecture_consistency": 9,
    "D3_decision_quality_tradeoffs": 8,
    "D4_constraints_nfr_fit": 9,
    "D5_interface_task_planning_readiness": 6.5,
    "D6_test_readiness_hidden_assumptions": 7.5
  },
  "independent_judgment_supersede_carryover": {
    "design_covers_v1_supersede_to_v1_1_invariant": "partial — §18#1 identifies but §10.1/§11.2 do not codify; front_matter['supersedes']/['related_decisions'] not in carry-over list; v1 supersede chain will be silently dropped on v1.1 repeated edit_accept",
    "publisher_must_carry_over_front_matter_supersedes": true,
    "is_blocking": false,
    "severity": "important",
    "evidence": "publisher.py:114-147 _to_knowledge_entry 构造的 front_matter 仅含 source_evidence_anchor/confirmation_ref/published_from_candidate；KnowledgeStore.update 调用 store→_entry_to_front_matter 完全从 entry 字段重建 front_matter，不保留旧文件 front_matter；故必须由 publisher 在 update 前手动 carry-over"
  }
}
```

---

**记录位置**: `docs/reviews/design-review-F004-memory-v1-1.md`
