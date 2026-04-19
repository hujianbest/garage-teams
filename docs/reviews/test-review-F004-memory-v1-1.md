# Test Review — F004 Garage Memory v1.1

- Review Skill: `hf-test-review`
- Reviewer: cursor cloud agent (subagent dispatched by `hf-test-driven-dev` parent session)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- Branch: `cursor/f004-memory-polish-1bde`
- 关联规格: `docs/features/F004-garage-memory-v1-1-publication-identity-and-confirmation-semantics.md`
- 关联设计: `docs/designs/2026-04-19-garage-memory-v1-1-design.md`
- 关联任务计划: `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md`
- 关联实现交接块:
  - `docs/verification/F004-T1-implementation-handoff.md`
  - `docs/verification/F004-T2-implementation-handoff.md`
  - `docs/verification/F004-T5-implementation-handoff.md`
- 关联 test design approvals: `docs/approvals/F004-T{1,2,3,4}-test-design-approval.md`

---

## 0. 评审范围

26 个 F004 新增测试，分布在 4 个测试文件 / 5 个测试 class：

| 文件 | Class | 数量 | 锚点 |
|------|-------|-----:|------|
| `tests/memory/test_publisher.py` | `TestPublicationIdentityGenerator` | 2 | NFR-401 / ADR-401 |
| `tests/memory/test_publisher.py` | `TestPublishCandidateEntryValidation` | 3 | FR-402 / ADR-402 |
| `tests/memory/test_publisher.py` | `TestPublishCandidateRepublication` | 6 | FR-401 / FR-405 / §10.1 / §10.1.1 / §11.2.1 |
| `tests/test_cli.py` | `TestMemoryReviewAbandonDualPaths` | 6 | FR-403a / FR-403b / ADR-403 |
| `tests/runtime/test_session_manager.py` | `TestF004T4ExtractionErrorPersistence` | 6 | FR-404 / §11.4 / ADR-404 |
| `tests/test_documentation.py`（新建） | top-level | 3 | FR-403c / NFR-401 / CON-404 |

---

## 1. 证据基线

- 全 suite 当前状态：`pytest tests/ -q` → **410 passed in 24.81s**（baseline 384 → +26 F004 新增；零回归）
- F004 新增 26 个 test 单独跑：**26 passed in 0.29s**（已逐项验证）
- 三个 implementation handoff 提供 RED/GREEN 证据（T1/T2 详尽；T5 RED 仅文字叙述）
- 4 个 test design approvals (T1~T4) 全部 auto-mode self-approved；T5 无独立 approval（lint trivial, 任务计划已显式说明）
- KnowledgeStore bug fix 配套：70 个 knowledge + memory 测试全绿（T2 handoff 记录）

---

## 2. Precheck

| 检查项 | 状态 | 证据 |
|--------|------|------|
| 实现交接块完整 | ✅ | T1 / T2 / T5 显式 handoff；T3 / T4 在 commit `feat(F004 T3 T4 T5)` 中，但 task plan 已声明，验证证据可在测试文件 + handoff T5 中冷读 |
| route / stage / profile 一致 | ✅ | task-progress 与 handoff 全部声明 `full / auto / in-place`，与 spec/design approval 一致 |
| 测试资产可定位 | ✅ | 26 个 test 全部按 grep 命中并独立跑通 |
| 全 suite 零回归 | ✅ | 410 passed（无 skip / xfail 漂移） |

Precheck 通过，进入正式 6 维评审。

---

## 3. 多维评分

| ID | 维度 | 评分 | 说明 |
|----|------|------|------|
| `TT1` | fail-first 有效性 | 8/10 | T1 / T2 / T4 都有可冷读的 RED 终端输出（含错误类型 + 失败原因）；T3 fail-first 在 handoff 中描述但实际 RED 命令输出未保留；T5 RED 仅 narrative（"会 fail"） |
| `TT2` | 行为 / 验收映射 | 9/10 | 26 个测试 docstring 全部带 FR / NFR / design §xxx 锚点；test design approvals 1:1 映射 task plan 测试种子；ad-hoc 增强（如 experience `updated_at >= first_updated_at`）有显式注释说明 |
| `TT3` | 风险覆盖 | 7/10 | 关键 invariant（FR-401 version 链 / FR-405 supersede 兼容 / §10.1.1 self-conflict 短路 / FR-404 三 phase / FR-403 abandon 双路径）全部覆盖；但有 3 处可补强（见 §4 findings 1 / 2 / 3） |
| `TT4` | 测试设计质量 | 9/10 | 大量使用 `tmp_path` + 真实 fixture（不 mock storage / publisher）；T4 用 `monkeypatch.setattr` 替换 `MemoryExtractionOrchestrator` 真实边界方法（合理）；T3 通过种入"不同 candidate_id 同 title/tags"制造真实冲突，避开 self-conflict 短路；mock 边界精确，无 over-reach |
| `TT5` | 新鲜证据完整性 | 8/10 | T1 / T2 RED+GREEN 终端输出齐全；T4 / T3 GREEN 在 handoff 末尾的全 suite 410 passed 中可核实；T5 RED 缺真实输出（lint-only，影响轻微） |
| `TT6` | 下游就绪度 | 9/10 | 26 个测试 + 410 全 suite 足以支持 `hf-code-review` 对 publisher / session_manager / cli / knowledge_store 4 处源码的可信判断；§4 findings 不阻塞下游 |

总评：6 个维度无任一 < 6。最低分 TT3=7（findings 都是补强而非缺失）。

---

## 4. Findings

### 4.1 [minor][LLM-FIXABLE][TT3 / TA2] KnowledgeStore extra-key 持久化无专项测试

**Context**：T2 修复了 F003 预 existing bug —— `KnowledgeStore._entry_to_front_matter()` 之前不持久化 dataclass 字段以外的 `entry.front_matter` extra keys（含 publisher 写入的 `supersedes`）。修复后引入 `_DATACLASS_FRONT_MATTER_KEYS` 元组 + 末尾合并 extra keys 的语义。

**Risk**：当前对该新契约的覆盖**只在 publisher 端通过端到端路径间接验证**（`test_repeated_publish_preserves_supersedes_chain_from_v1` 等）。如果未来重构 `KnowledgeStore` 内部把 extra-key 合并退回去，publisher 端测试可能仍绿（因为 `_entry_to_front_matter` 是 publisher 调 `store()` 的下游），但 KnowledgeStore 自身契约会静默回退。design §9 的 escape hatch 修复的代码层应该被自身测试锁住。

**建议**（非阻塞）：在 `tests/knowledge/test_knowledge_store.py` 新增 `test_extra_front_matter_keys_round_trip` —— store 一个含 `entry.front_matter["supersedes"] = ["k-X"]` 的 entry → retrieve 回来 → 断言 `entry.front_matter["supersedes"] == ["k-X"]`。

### 4.2 [minor][LLM-FIXABLE][TT3] experience_summary 重复发布缺 `created_at` 保留断言

**Context**：publisher.py:142 显式 `record.created_at = existing_record.created_at`，是 ExperienceIndex 路径的"version 语义弱于 knowledge"补偿机制。`test_repeated_publish_experience_summary_updates_index` 仅断言 `len(records)==1` 与 `updated_at >= first_updated_at`，未断言 `created_at` 等于第一次发布时的值。

**Risk**：如果未来 publisher 误删 `record.created_at = existing_record.created_at`，experience_summary 重复发布会把 `created_at` 改为 `now()`，破坏"原始发布时间"语义；现有测试不会捕获。

**建议**：在该测试末尾新增 `assert records[0].created_at == first_record.created_at`。

### 4.3 [minor][LLM-FIXABLE][TT3] supersede 链 + carry-over 后续 `conflict_strategy=supersede` 合并语义未直接覆盖

**Context**：design §10.1 描述：当 v1 已有 `front_matter["supersedes"] = ["k-X"]` 且 v1.1 republication 本身带 `conflict_strategy="supersede"`（命中**新的**冲突 entry "k-Y"），最终结果应是 `front_matter["supersedes"] = ["k-X", "k-Y"]`（merge_unique）。

**Code path**：publisher.py:184-192 在 supersede 分支无条件**覆盖** `entry.front_matter["supersedes"] = list(similar_entries)`；随后 update 分支的 `PRESERVED_FRONT_MATTER_KEYS` 循环再 merge_unique 历史 + 当前。代码路径完成 merge，但**未被独立测试**。

**Risk**：`test_repeated_publish_preserves_supersedes_chain_from_v1` 只测了 `existing_supersedes ⊆ merged`（无 strategy）的弱不变量；未测 `existing ∪ new ⊆ merged`（带 strategy）的强不变量。如果未来重构破坏 merge 顺序或丢失 new supersede id，现有断言不会失败。

**建议**：新增 `test_repeated_publish_with_supersede_strategy_merges_v1_chain_with_new_targets` —— v1 entry seeded with `front_matter["supersedes"]=["k-X"]`，再种一个不同 candidate id 同 title/tags 的 entry "k-Y"，对原 candidate 跑 `accept` + `conflict_strategy="supersede"`，断言最终 `supersedes` 同时含 `["k-X", "k-Y"]`。

### 4.4 [minor][LLM-FIXABLE][TT5 / TA5] T5 RED evidence 仅 narrative

**Context**：`docs/verification/F004-T5-implementation-handoff.md` "RED 证据" 段写：`... (会 fail，因为 user-guide / developer-guide 不含 abandon / PublicationIdentityGenerator / memory-extraction-error.json 关键 token)`，没有真实 RED 终端输出。

**Risk**：低（lint-only，逻辑显然），但违反 TT5 fresh evidence 原则；未来 reviewer 不能完全冷读验证 fail-first。

**建议**：可选 —— 在 handoff 中补一段 `pytest tests/test_documentation.py -v` 的真实 RED 输出（实施前 git stash docs 段）。如果时间紧张，接受现状即可（影响极小）。

### 4.5 独立判断点回应（用户 prompt 要求）

#### A. T2 KnowledgeStore bug fix 必要性

**判断**：**必要**，但 **strict 论证** 比 handoff 描述更微妙。

**冷读链**：
- F003 v1 publisher 在 strategy=supersede 路径写入 `entry.front_matter["supersedes"]`，但因 `_entry_to_front_matter()` 不处理 dataclass 字段以外的 keys，`supersedes` **从未** make it to disk（T2 handoff "中间发现" 段实测验证）
- 因此 v1 已发布数据**事实上不存在** supersede 链丢失风险（"丢的东西本来就不存在"）
- 但 F004 v1.1 publisher 的 supersede 分支也走同一条 `_entry_to_front_matter` → `KnowledgeStore.store/update` 写入路径；如果不修 `KnowledgeStore`，**v1.1 后写入的 supersedes 也会原样丢失** → FR-401 supersede 不变量 (§11.2.1) 直接 break
- 结论：bug fix 对 v1 数据迁移 vacuously 满足；对 v1.1 forward 是**强制必需**。这是 design §9 escape hatch 显式允许的修复，方向正确，不是 over-engineering

**70 个 knowledge + memory 测试全绿是否充分**：
- 充分 ✅ —— 现有 145 个 memory focused + 70 个 knowledge focused 测试覆盖 store / retrieve / list / update 四个公共 API 全部路径
- 不充分 ⚠️ —— 缺少**针对 extra-key 持久化新契约的专项测试**（见 finding 4.1）。当前覆盖是间接的，无 KnowledgeStore 自身的回归保护

#### B. T1 删除 conflict 分支冗余校验风险

**判断**：**风险低，可接受**。

**冷读链**：
- T1 把 `_validate_conflict_strategy(value)` 提到 `publish_candidate` 第一行；该校验 reject `value not in VALID_CONFLICT_STRATEGIES`，pass `value is None` / `value in set`
- 删除原 conflict 分支的 `if conflict_strategy not in VALID:` 是合理的：等到代码走到 conflict 分支，`conflict_strategy` 必然已通过入口校验（除非未来有人把入口校验移走）
- conflict 分支保留 `if conflict_strategy is None: raise ValueError(...)` —— 这是 FR-304 "命中冲突必须显式选择" 语义，与 garbage 校验是两件事
- 风险注入路径：未来如果在 publish_candidate 入口前后插入新 logic、或重构调用顺序，导致入口校验被绕过；现有 fail-first 测试 `test_publish_candidate_rejects_garbage_strategy_at_entry` 会立即失败
- **建议**：可选小补强 —— 在测试 docstring 显式声明 "this also locks down: any future refactor that moves _validate_conflict_strategy out of entry must keep coverage for garbage values"。非必需

---

## 5. 缺失或薄弱项

| 项 | 严重度 | 关联 finding |
|----|--------|-------------|
| KnowledgeStore extra-key 持久化无自身回归测试 | minor | 4.1 |
| experience_summary `created_at` 保留无断言 | minor | 4.2 |
| supersede merge with v1 chain + new targets 路径未直接测试 | minor | 4.3 |
| T5 RED evidence 仅 narrative | minor | 4.4 |

无 critical / important 缺失。所有 findings 都是**补强建议**而非阻塞缺口。

---

## 6. Anti-pattern 检查

| ID | Anti-pattern | 状态 |
|----|--------------|------|
| `TA1` born-green | ❌ 未发现 —— T1 / T2 / T4 RED 证据明确 |
| `TA2` happy-path-only | ⚠️ 部分 —— finding 4.1 / 4.2 / 4.3 反映"部分边界路径未直接覆盖"，但都是 minor |
| `TA3` mock overreach | ❌ 未发现 —— monkeypatch 仅用于 orchestrator 真实边界方法（合理） |
| `TA4` no acceptance link | ❌ 未发现 —— 全部 docstring 带 FR / NFR / design 锚点 |
| `TA5` stale evidence | ⚠️ 仅 T5 narrative RED（finding 4.4），其它 OK |

---

## 7. 结论

**通过**

- 所有 6 维度评分 ≥ 7
- fail-first 真实证据齐全（T1 / T2 / T4 终端输出 + T3 在 handoff 描述）
- 26 个新增测试覆盖 F004 全部 FR / NFR 验收点 + design 关键不变量
- 全 suite 410 passed 零回归
- T2 KnowledgeStore bug fix 路径正确，是 design §9 escape hatch 显式允许
- T1 删除 conflict 分支冗余校验风险低，已被 fail-first 测试锁住

4 个 minor LLM-FIXABLE findings 是**强化建议**，不阻塞下游。建议在 `hf-code-review` 阶段顺手讨论 finding 4.1 / 4.2 / 4.3（特别是 4.1 KnowledgeStore extra-key 自身契约保护），4.4 接受现状。

---

## 8. 下一步

- **next_action_or_recommended_skill**: `hf-code-review`
- **needs_human_confirmation**: false
- **reroute_via_router**: false
- **rationale**: test review 通过，可进入 code review 评审 publisher.py / knowledge_store.py / session_manager.py / cli.py 4 处源码 + docs guides 增量

---

## 9. 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-code-review",
  "record_path": "docs/reviews/test-review-F004-memory-v1-1.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][TT3] KnowledgeStore extra-key 持久化无专项测试（仅 publisher 端间接覆盖）",
    "[minor][LLM-FIXABLE][TT3] experience_summary 重复发布缺 created_at 保留断言",
    "[minor][LLM-FIXABLE][TT3] supersede 链 + strategy=supersede merge 未直接覆盖",
    "[minor][LLM-FIXABLE][TT5] T5 RED evidence 仅 narrative，无真实终端输出"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT3",
      "summary": "KnowledgeStore _entry_to_front_matter extra-key 合并是 T2 修复的新契约，但只通过 publisher 端到端测试间接覆盖；建议 tests/knowledge/test_knowledge_store.py 新增 round-trip 专项测试"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT3",
      "summary": "test_repeated_publish_experience_summary_updates_index 仅断言 updated_at 进展，未锁 created_at 保留；publisher.py:142 的 carry-over 无回归保护"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT3",
      "summary": "v1 supersede 链 + v1.1 strategy=supersede 同时引入新 target 时的 merge 语义未直接测试；现有 test_repeated_publish_preserves_supersedes_chain_from_v1 只覆盖弱不变量"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT5",
      "summary": "F004-T5-implementation-handoff.md RED 段落仅 narrative；docs lint 类测试 fail-first 应保留真实终端输出（建议补，非阻塞）"
    }
  ]
}
```

---

**文档状态**: 已落盘。父会话可基于本记录继续 `hf-code-review`。
