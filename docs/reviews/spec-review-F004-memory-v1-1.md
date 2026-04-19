# Spec Review — F004 Garage Memory v1.1（发布身份解耦与确认语义收敛）

- 评审范围: `docs/features/F004-garage-memory-v1-1-publication-identity-and-confirmation-semantics.md`（草稿）
- Review skill: `hf-spec-review`
- 评审者: cursor cloud agent (auto mode, reviewer subagent，由 `hf-specify` 父会话派发)
- 日期: 2026-04-19
- Workflow Profile / Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- 上游证据基线:
  - `docs/reviews/code-review-F003-garage-memory-auto-extraction-r2.md`（4 项显式延后 minor finding 出处）
  - `RELEASE_NOTES.md` `### 已知限制 / 后续工作` 段（finalize cycle 中显式延后说明）
  - `task-progress.md`（Stage = `hf-specify`，Pending = `hf-spec-review`，profile/mode 一致）
  - `AGENTS.md` AHE 文档约定（`docs/features/` 下的 `Fxxx` 即 spec，骨架以项目模板为准）
  - 项目灵魂：`docs/soul/{manifesto,user-pact,design-principles,growth-strategy}.md`

## 1. Precheck

| 检查项 | 结果 |
|--------|------|
| 存在稳定可定位 spec draft | ✓ `docs/features/F004-...md` 草稿完整、261 行、各章节齐备 |
| route / stage / profile 已明确 | ✓ `task-progress.md` Stage=`hf-specify`，Pending=`hf-spec-review`，profile=`full`，mode=`auto`，无冲突 |
| 上游证据一致 | ✓ F003 code-review r2 的 4 项延后 finding（USER-INPUT minor + 3 项 LLM-FIXABLE minor）与 RELEASE_NOTES "已知限制 / 后续工作" 一致 |
| 结构契约 | ✓ AGENTS.md 显式声明 `docs/features/` 是项目 spec 路径，F004 遵循 F003 同款骨架；不机械套用 `docs/specs/` 默认模板 |

Precheck 通过，进入正式 rubric。

## 2. 结构契约确认

F004 沿用 F003 已实战验证的章节骨架：背景 → 目标与成功标准 → 用户角色与场景 → 范围（含/不含）→ 范围外 → 术语 → FR → NFR → 外部接口与依赖 → 约束 → 假设 → 开放问题。FR/NFR/IFR/CON/ASM 全部带 `优先级 / 来源 / 需求陈述 / 验收标准`，与 F003 的 contract 字段一致，可被 `hf-design` 直接读为稳定输入。

## 3. 正式 rubric 审查

### 3.1 Group Q: Quality Attributes

| ID | 检查 | 结论 | 证据 / 备注 |
|----|------|------|------------|
| Q1 Correct | 核心需求可回指来源 | ✓ | 每条 FR/NFR/IFR/CON 都有 `来源` 字段，分别锚定 F003 review r2 finding 5 / CR3 / CR5 / NFR-304 / F001 KnowledgeStore 实现 / 设计原则"文件即契约" |
| Q2 Unambiguous | 模糊词已量化 | ✓ | `version+=1`、"立即拒绝"、"≥384 passed"、"P90 退化 ≤10%"、"1 段话讲清"、JSON 字段集合显式声明，全部可观察 |
| Q3 Complete | 关键输入/输出/错误/边界 | ✓ | FR-402 / FR-404 各覆盖正常 + 失败 + 边界路径；FR-403 覆盖 4 种 abandon 组合 |
| Q4 Consistent | 需求间无冲突 | ✓ | FR-401（重用 update）与 IFR-401（复用 update 契约不变）一致；FR-404 与 F003 FR-307 兼容（session 层兜底文件 + orchestrator 层 batch，明确"不重复写"） |
| Q5 Ranked | 每条核心需求有优先级 | ✓ | FR-401~405 / IFR-401/402 / NFR-401 / CON-401~404 = Must；NFR-402 / ASM-401/402 = Should，分级明确 |
| Q6 Verifiable | 通过/不通过判断 | ✓ | 全部 FR 给出 Given / When / Then 验收标准；NFR-402 有 baseline 比较公式 `T1 ≤ 1.1 * T0` |
| Q7 Modifiable | 无散落重复 | ✓ | 同一概念（"重复发布走 update"）只在 FR-401 + IFR-401 提及，分别管语义和契约面 |
| Q8 Traceable | 关键需求有 ID + Source | ✓ | FR-401~405 / NFR-401/402 / IFR-401/402 / CON-401~404 / ASM-401/402，全部带 ID |

### 3.2 Group A: Anti-Patterns

| ID | 检查 | 结论 | 备注 |
|----|------|------|------|
| A1 模糊词 | ✓（minor） | 主题行 "可治理的稳态" 与 §2.1 "v1.1 稳态" 略口号化，但紧跟 4 个量化维度（version 链 / 入口校验 / surface 单一 / 文件留痕），可接受 |
| A2 复合需求 | ⚠ 有 1 处可优化 | FR-403 把"confirmation 持久差异 + CLI 输出文案 + 用户文档段"打包；主题虽统一为"两条 abandon 路径可独立识别"，4 条验收标准独立可判，但"用户文档显式说明差异"严格说属于交付物层而非 publisher / CLI 行为，可考虑拆出独立条目（findings 见下） |
| A3 设计泄漏 | ⚠ 有 1 处边界 | §4.2 出现 `_id_generator(candidate_id, payload, version)` 这一具体函数签名，属于 publisher 层实现选择；NFR-401 引用具体文件路径 `src/garage_os/memory/publisher.py`。**判定**：IFR-401 复用 `KnowledgeStore.update()` 是接口契约约束（不是 leak）；但 §4.2 的函数签名与 NFR-401 的具体文件路径属于偏向实现的细节，可改为"publication identity 生成函数（发布 ID 生成器）"+ "publisher 层 + 开发者文档可冷读"。Severity = minor，LLM-FIXABLE |
| A4 无主体的被动表达 | ✓ | 全部 FR 主语清晰（系统 / 用户 / 调用方） |
| A5 占位/TBD | ✓ | 无 `TBD` / `待确认` / `后续补充` |
| A6 缺少负路径 | ✓ | FR-402 含 garbage 值；FR-404 含 3 个失败 phase；FR-403 含 4 种 accept/abandon × strategy 组合 |

### 3.3 Group C: Completeness And Contract

| ID | 检查 | 结论 | 证据 |
|----|------|------|------|
| C1 Requirement contract | ✓（minor 提示） | 所有 FR/NFR/IFR/CON 字段齐全；唯一弱点：NFR-402 验收标准 2 用 "若覆盖 publisher 路径" 条件式表述，建议改为无条件或在 ASM 中显式假设。Severity = minor，LLM-FIXABLE |
| C2 Scope closure | ✓ | §4.1 含 / §4.2 不含 / §5 范围外，三段闭合，不依赖聊天记忆 |
| C3 Open-question closure | ✓ | §12 列出 3 条非阻塞开放问题，全部可在 design stage 收敛，且各自给出默认建议；正文显式 "无阻塞性开放问题" |
| C4 Template alignment | ✓ | 沿用 F003 同款 spec 骨架，符合 AGENTS.md `docs/features/` 约定 |
| C5 Deferral handling | ✓ | F003 4 项延后 finding 全部映射到本 spec FR-401~404；§4.2 / §5 显式说明本 cycle 不做的事 |
| C6 Goal and success criteria | ✓ | §2.2 五条 success criteria，每条都映射到具体 FR：SC1→FR-401, SC2→FR-402, SC3→FR-403, SC4→FR-404, SC5→FR-405，覆盖完整 |
| C7 Assumption visibility | ✓ | ASM-401（KnowledgeStore.update 原子性 + index 一致）、ASM-402（重复发布场景在第一版用户量小）显式列出，含失效风险 + 缓解措施 |

### 3.4 Group G: Granularity And Scope-Fit

| ID | 检查 | 结论 | 备注 |
|----|------|------|------|
| G1 Oversized FR | ✓ | FR-401~405 各聚焦单一关注点；FR-403 / FR-404 验收标准多但主题单一（abandon 双路径 / 3 个 phase 失败点），不是 GS3 场景爆炸或 GS4 跨层打包；FR-405 的"零回归"是合理 cohesive 验证集合 |
| G2 Mixed release boundary | ✓ | §4.2 / §5 明确划掉 "schema 升级 / LLM 升级 / 异步队列 / 新顶级命令 / 改 4 类候选契约"，本轮和后续增量边界清晰 |
| G3 Repairable scope | ✓ | 即便回 `需修改`，2 项 minor finding（A3 文案改写 + C1 条件式表述）单轮可消化；不需要推倒重来 |

### 3.5 F003 延后 finding 收敛验证（用户指定的重点）

| F003 r2 finding | classification | F004 收敛位置 | 收敛度 |
|------------------|---------------|---------------|--------|
| publisher 用 `candidate_id` 当 `KnowledgeEntry.id`，重复 accept 静默覆盖 | minor / USER-INPUT / CR2 | **FR-401** + IFR-401 + IFR-402 + NFR-401 | ✓ 完整：定义"重复发布 = update + version 递增"、约束接口面、要求生成规则可冷读 |
| publisher VALID_CONFLICT_STRATEGIES 仅在 similar_entries 非空时校验 | minor / LLM-FIXABLE / CR3 | **FR-402** | ✓ 完整：4 条验收覆盖 garbage / coexist / None × 命中/不命中 4 种正交组合 |
| CLI `--action=abandon` 与 `accept --strategy=abandon` 语义重叠 | minor / LLM-FIXABLE / CR5/CR4 | **FR-403** | ✓ 完整：confirmation 持久 + CLI 输出 + 用户文档三个面让差异可被独立识别（仅 A2 提示可拆分） |
| `SessionManager._trigger_memory_extraction` 仅 logger.warning | minor / LLM-FIXABLE / CR3 | **FR-404** + CON-401 + CON-404 | ✓ 完整：3 个 phase 失败点全覆盖、文件路径可冷读、与 orchestrator batch 显式不重复写 |

> 备注：F003 r2 finding 列表里的"`extraction_orchestrator.py:68 # pragma: no cover` stale 注释"已在 F003 finalize 时顺手清理（见 `RELEASE_NOTES.md` 第 53 行），F004 不再需要承接，正确忽略。

四项 F003 延后 finding 在 F004 内全部得到结构化收敛，**无遗漏**。

### 3.6 Success criteria → FR 映射检查

| Success Criterion | 映射 FR | 是否可判断 |
|-------------------|---------|-----------|
| SC1 同一候选 N 次发布 = 1 条 KnowledgeEntry, version=N | FR-401 | ✓ Given/When/Then 三条 |
| SC2 入口校验立即生效 | FR-402 | ✓ 4 条验收正交覆盖 |
| SC3 CLI surface 单一职责，文档可冷读差异 | FR-403 | ✓ 4 条验收（含文档段） |
| SC4 FR-307 session 层证据零盲点 | FR-404 | ✓ 3 phase + 1 happy path 验收 |
| SC5 零 F003 主链回归（≥384 passed） | FR-405 | ✓ 3 条 pytest 命令级验收 |

5 条全部映射到具体 FR，**无悬空**。

### 3.7 关于 IFR-401 是否构成"设计泄漏"的独立判断

用户在派发指令中提示："`KnowledgeStore.update()` 是否构成 implementation leak？"

**reviewer 独立判断**：**不构成 leak**。理由：
1. F001 已批准 `KnowledgeStore` 接口（含 `store / update`）作为公开数据契约，不是新决策；F004 的 IFR-401 只是约束"不修改 F001 已有签名 / 行为"
2. spec 章节 §9 "外部接口与依赖" 的本来定位就是 expose external interface contracts，引用已发布契约名是合理的
3. 若把 IFR-401 改成"系统须保证发布身份与候选身份解耦"这种纯 WHAT 表述，反而会丢失"必须复用而不是新建"的关键约束，导致 design 阶段可能选错路径
4. 设计原则 "文件即契约" 决定了 KnowledgeStore 接口本身就是用户可见契约面

但 §4.2 中 `_id_generator(candidate_id, payload, version)` 的具体函数签名与 NFR-401 引用 `src/garage_os/memory/publisher.py` 文件路径属于"实现细节泄漏"（见 A3）。

## 4. 发现项

> 无 critical / important finding。以下 minor 均不阻塞进入设计；可在 design stage 顺手收敛或忽略。

- `[minor][LLM-FIXABLE][A3]` §4.2 "包含" 表格出现具体函数签名 `_id_generator(candidate_id, payload, version)`；NFR-401 验收标准 2 引用具体文件路径 `src/garage_os/memory/publisher.py`。建议改为"发布 ID 生成器（publication identity generator）"与"publisher 模块 + 开发者文档可冷读"，让 spec 保持 WHAT 抽象层。**不阻塞**。
- `[minor][LLM-FIXABLE][A2]` FR-403 把 confirmation 持久 + CLI 输出文案 + 用户文档说明三件事打包成 1 条 FR；主题虽 cohesive，但若拆为 FR-403a（confirmation 差异化）/ FR-403b（CLI 输出可被独立识别）/ FR-403c（用户文档显式说明）会更利于 traceability gate 阶段逐项追溯。仅样式建议，**不阻塞**。
- `[minor][LLM-FIXABLE][C1]` NFR-402 验收标准 2 用 "若覆盖 publisher 路径" 这种条件式表述，建议改为：要么把 `scripts/benchmark.py` 是否覆盖 publisher 升级为前置检查（无条件验收），要么把"benchmark 是否覆盖 publisher"沉到 ASM 中作为 Should 假设。**不阻塞**。

## 5. 缺失或薄弱项

- 无关键缺失。
- §12 三条开放问题已带默认建议（写死单一规则 / 只保留最近一次 error / 文档措辞），design stage 可在 §11.4 / §14.2 段直接落决议，不会反推规格。

## 6. 结论

**通过**

判断依据：
- F003 4 项延后 finding 全部在 FR-401~404 得到结构化收敛，且新增 FR-405 锁住"零主链回归"
- 5 条 success criteria 全部映射到具体 FR
- 无 critical / important finding；3 项 minor 全部 LLM-FIXABLE 且不阻塞设计
- 范围 / 范围外 / 术语 / 假设 / 开放问题闭合度足以支撑 `hf-design` 进入
- 不存在 USER-INPUT 类阻塞 finding（F003 finding 5 是 USER-INPUT，但已在本 spec 内由 FR-401 给出业务语义定义"重复发布必须保留 version 链"，已具备业务事实输入）
- route / stage / profile / 上游证据全部一致，无 reroute 必要

## 7. 下一步

- **`规格真人确认`**：`hf-spec-review` 通过后由父会话 `hf-specify` 进入 approval step，写入 `docs/approvals/F004-spec-approval.md`，再切到 `hf-design`
- 不需要 reroute via router
- 3 项 minor 建议作为 design stage 顺手收敛（不强制；可在 design 评审时再裁决是否回流 spec）

## 8. 交接说明

- `规格真人确认`：interactive 下等真人确认；本会话是 `auto` mode，可由父会话写入 approval record
- LLM-FIXABLE 类 minor finding 不转嫁给用户，只在父会话 plain-language 摘要中可选提示"3 条样式建议可在 design stage 顺手处理"
- 无 USER-INPUT finding，父会话不需要向用户发起额外问卷

## 9. 结构化返回

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "规格真人确认",
  "record_path": "docs/reviews/spec-review-F004-memory-v1-1.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][A3] §4.2 出现 _id_generator(candidate_id, payload, version) 具体函数签名；NFR-401 验收引用 src/garage_os/memory/publisher.py，建议抽象为 publication identity generator + publisher 模块",
    "[minor][LLM-FIXABLE][A2] FR-403 把 confirmation 持久 + CLI 输出 + 用户文档说明三件事打包，可拆为 403a/403b/403c 提升 traceability 粒度",
    "[minor][LLM-FIXABLE][C1] NFR-402 验收标准 2 用 \"若覆盖 publisher 路径\" 条件式表述，建议改为无条件或沉到 ASM"
  ],
  "needs_human_confirmation": true,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "A3",
      "summary": "§4.2 出现 _id_generator 具体函数签名；NFR-401 引用具体文件路径，属偏实现表述"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "A2",
      "summary": "FR-403 打包 confirmation/CLI/文档三件事，可拆为 403a/403b/403c"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "C1",
      "summary": "NFR-402 验收标准 2 条件式表述，建议无条件化或沉到 ASM"
    }
  ],
  "deferred_findings_coverage": {
    "F003_r2_finding_5_USER_INPUT_publisher_id": "FR-401 + IFR-401 + IFR-402 + NFR-401 完整收敛",
    "F003_r2_minor_LLM_FIXABLE_validate_strategy_at_entry": "FR-402 完整收敛",
    "F003_r2_minor_LLM_FIXABLE_cli_abandon_overlap": "FR-403 完整收敛",
    "F003_r2_minor_LLM_FIXABLE_session_logger_warning": "FR-404 + CON-401 + CON-404 完整收敛"
  },
  "success_criteria_to_fr_mapping": {
    "SC1": "FR-401",
    "SC2": "FR-402",
    "SC3": "FR-403",
    "SC4": "FR-404",
    "SC5": "FR-405"
  }
}
```
