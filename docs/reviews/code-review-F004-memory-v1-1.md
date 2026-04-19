# Code Review — F004 Garage Memory v1.1

- Review Skill: `hf-code-review`
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
- 关联 test review: `docs/reviews/test-review-F004-memory-v1-1.md`（通过；4 项 minor LLM-FIXABLE，会话已补 2 项）
- 关联 test design approvals: `docs/approvals/F004-T{1,2,3,4}-test-design-approval.md`

---

## 0. 评审范围（git diff main..HEAD 源码增量）

| 文件 | 变化点 |
|------|--------|
| `src/garage_os/memory/publisher.py` | + `PublicationIdentityGenerator` + `PRESERVED_FRONT_MATTER_KEYS` + `_merge_unique` + `_validate_conflict_strategy`；重构 `publish_candidate` store-or-update + supersede carry-over + self-conflict 短路 + experience 路径 created_at carry-over |
| `src/garage_os/runtime/session_manager.py` | 拆 `_trigger_memory_extraction` 为 3 phase try/except；新增 `_persist_extraction_error` + `MEMORY_EXTRACTION_ERROR_FILENAME` 常量 |
| `src/garage_os/cli.py` | 新增 `MEMORY_REVIEW_ABANDONED_NO_PUB` / `MEMORY_REVIEW_ABANDONED_CONFLICT` 模块常量；按 publisher 返回值区分两条 abandon stdout/状态写入 |
| `src/garage_os/knowledge/knowledge_store.py` | 新增 `_DATACLASS_FRONT_MATTER_KEYS` 元组；`_entry_to_front_matter` 改为"先 14 reserved 字段、再合并 extras"，修复 F003 预 existing 静默丢键 bug |
| `docs/guides/garage-os-user-guide.md` | + "Memory review — abandon paths" 段 |
| `docs/guides/garage-os-developer-guide.md` | + "Publisher 重复发布与 ID 生成规则" + "Session memory-extraction-error.json schema" 两段 |

---

## 1. 证据基线

- 全 suite：`pytest tests/ -q` → **414 passed in 24.94s**（test review 时 410 → +4 supplementary tests，零回归）
- 模块 mypy（仅 publisher.py）：1 个预 existing error（`publisher.py:161 "object" has no attribute "__iter__"`），与 F003 baseline 一致，T1 handoff 已声明，不在本 cycle 范围
- session_manager.py / cli.py / knowledge_store.py mypy：错误均为 F003 baseline 预 existing（`update_session **kwargs` 未注解、`MemoryExtractionOrchestrator` Optional 兼容、`Dict` 未泛型化等），无新增

---

## 2. Precheck

| 检查项 | 状态 | 证据 |
|--------|------|------|
| 实现交接块完整 | ✅ | T1/T2/T5 显式 handoff；T3/T4 实现内嵌 commit + handoff T5 RED/GREEN 段补齐链路 |
| 可定位代码变更 | ✅ | git diff main..HEAD 命中 4 个源码 + 2 份文档 |
| test review 通过 | ✅ | `docs/reviews/test-review-F004-memory-v1-1.md` 结论 = 通过 |
| route / stage / profile 一致 | ✅ | 与上游 spec/design/tasks approval 一致（full / auto / in-place） |

Precheck 通过，进入 6 维评审。

---

## 3. 多维评分

| ID | 维度 | 评分 | 说明 |
|----|------|------|------|
| `CR1` | 正确性 | 9/10 | 4 个核心改动端到端正确；store-or-update 决策、self-conflict 短路、3 phase 错误持久化、CLI 双 abandon stdout/status 联动均通过 26 个新增 + 4 个 supplementary 测试锁住，无 off-by-one / 边界遗漏 |
| `CR2` | 设计一致性 | 9/10 | 严格遵循 design § 10.1 / § 10.1.1 / § 11.1 / § 11.2 / § 11.2.1 / § 11.4；PRESERVED_FRONT_MATTER_KEYS 元组与 § 11.2.1 列出的两键 1:1 对齐；ADR-401~404 全部体现 |
| `CR3` | 状态/错误/安全 | 8/10 | 3 phase 失败均被捕获；`_persist_extraction_error` 自身写盘失败用 `try/except: pass + pragma: no cover` + logger.warning 双层防护，符合 design § 14 与失败模式表的"不再升级"裁决；存在 1 个隐含 4th 失败模式（archived session.json 读取返回 None）静默 return 无错误文件，影响极小（见 finding 4.2） |
| `CR4` | 可读性可维护性 | 8/10 | 命名清晰（`PRESERVED_FRONT_MATTER_KEYS` / `MEMORY_REVIEW_ABANDONED_*` / `MEMORY_EXTRACTION_ERROR_FILENAME`）；私有方法切分合理（3 phase 分块带 phase tag）；docstring 全部引 FR/§/ADR 锚点。仅 KnowledgeStore `_entry_to_front_matter` docstring 在"reserved key 优先级"上偏弱（见 finding 4.1） |
| `CR5` | 范围守卫 | 9/10 | `KnowledgeStore._entry_to_front_matter` 修复严格落在 design § 9 escape hatch（"测试时发现 retrieve 路径有 bug"）允许范围；CLI `--action=abandon` 仍写 confirmation 且只调字段值 = design § 10.3 表格第一行明确选择；无 undocumented behavior |
| `CR6` | 下游追溯就绪度 | 9/10 | 每个改动点都有 inline FR/§ 注释；T1/T2/T5 handoff + test review 共同提供端到端证据链；traceability review 可直接对照 spec → design → 实现 → 测试链路 |

任一关键维度均 ≥ 6，最低 8/10。可形成"通过" verdict。

---

## 4. Findings

### 4.1 [minor][LLM-FIXABLE][CR4] `_entry_to_front_matter` docstring 未显式声明"reserved 键优先级"

**Context**：`src/garage_os/knowledge/knowledge_store.py:_DATACLASS_FRONT_MATTER_KEYS` + `_entry_to_front_matter` 现在的写入顺序是：

1. 14 个 reserved 键（`id` / `type` / `topic` / `date` / `tags` / `status` / `version` / `related_decisions` / `related_tasks` / `source_session` / `source_artifact` / `source_evidence_anchor` / `confirmation_ref` / `published_from_candidate`）从 dataclass 字段重建
2. `entry.front_matter` 里的 extras 合并进来，**显式跳过** reserved 键集合中的任何同名 key

也就是说：`entry.front_matter["id"] = "X"` 不会覆盖 `entry.id`；reserved 总是 win。这是有意契约，且已被 `tests/knowledge/test_knowledge_store.py::test_extra_front_matter_keys_do_not_overwrite_dataclass_keys` 锁住。但 `_entry_to_front_matter` docstring 只描述了"extras 在末尾合并"，对"reserved 键不可被覆盖"这条优先级规则没有显眼警告，未来 caller 误把 reserved key 塞到 `front_matter` 时会沉默被吞而不易察觉。

**Risk**：低。现有测试已锁住，但未来调用方读 docstring 仍可能误解。

**建议**：在 `_entry_to_front_matter` 与 `_DATACLASS_FRONT_MATTER_KEYS` 之间补 1 句明确声明，例如：

> "Reserved-key wins: any key in `_DATACLASS_FRONT_MATTER_KEYS` present on `entry.front_matter` is silently ignored — set the corresponding dataclass attribute instead."

非阻塞；不影响代码行为或验收。

### 4.2 [minor][LLM-FIXABLE][CR3] `_trigger_memory_extraction` 的 archived session.json 读取失败属于隐含第 4 phase

**Context**：`src/garage_os/runtime/session_manager.py:248-251`：

```python
archived_session_path = f"sessions/archived/{session_id}/session.json"
archived_session = self._storage.read_json(archived_session_path)
if archived_session is None:
    return
```

设计 § 11.4 schema 定义 `phase` 是 3 值封闭枚举：`orchestrator_init` / `enablement_check` / `extraction`。但实现中在 phase 2 enablement_check 通过、进入 phase 3 之前还有一步"读取归档 session.json"——若 `_storage.read_json` 返回 `None`（文件被外部删除、I/O 错误返回 None 等），函数静默 return、不写 `memory-extraction-error.json`。这与 FR-404 "任意失败点都留痕" 的口径有 1 像素的偏差。

**Risk**：低。
- `archive_session()` 在调用 `_trigger_memory_extraction` 之前刚刚 `move + write_json` 完成 archived session.json，紧接着读理论上必然命中
- 真要触发该路径需要外部并发删除 / 文件系统瞬时故障，是极边缘场景
- 即便发生，下游 orchestrator 也无法处理 None；当前 silent return 是安全选项

**建议**（可选，不阻塞）：把读取段也包进一个 phase（命名如 `archived_session_read`），或在 `archived_session is None` 时也调一次 `_persist_extraction_error(session_id, "archived_session_read", FileNotFoundError(...))`。若不改，本身设计 § 14 失败模式表里"`_persist_extraction_error` 自身写盘失败 → 双层防护不再升级"的论证也覆盖此情况，可接受现状。

---

## 5. 独立判断点回应（用户 prompt 要求）

### 5.1 publisher.py self-conflict 短路时机

**判断**：**正确**。当前实现把短路放在 `if similar_entries: if conflict_strategy is None:` 之前是 **唯一正确的位置**。

冷读链：
- v1.1 默认 `PublicationIdentityGenerator.derive_knowledge_id(c, t) = c`（ADR-401），所以 publisher 自己写过的 entry 的 `id` 永远等于该 candidate 的 `entry.id`
- ConflictDetector 按 title/tags 反查，会同时返回（a）publisher 自己之前发布的同 candidate entry 与（b）其它真实冲突 entry（不同 id 但同 title/tags）
- 短路逻辑 `[item for item in similar_entries if item != entry.id]` 仅剔除 (a)，保留 (b)
- 因此"v1 同名 entry + v1.1 真实冲突 entry 同时存在"的场景下，剔除后仍非空 → 走 require strategy 路径（正确）

测试 `test_repeated_publish_merges_v1_supersedes_with_new_supersede_target` 正是这个 adversarial 场景：v1 有 `front_matter["supersedes"]=["k-X","k-Y"]` + 新种入 `existing-zzz`（同 title/tags 不同 id），用 strategy=supersede 重发，结果 `supersedes = ["k-X","k-Y","existing-zzz"]`，无丢失、无误剔。GREEN ✅。

> 顺带一个观察（不是 finding）：publisher.py:184-192 在 supersede 分支无条件 `entry.front_matter["supersedes"] = list(similar_entries)`，随后 update 分支的 `PRESERVED_FRONT_MATTER_KEYS` 循环再 `_merge_unique` 历史 + 当前。两步合在一起语义正确，但中间这次 overwrite 在没有 update 分支兜底的"首次发布 + supersede strategy"路径上也是正确的（首次发布 PRESERVED 循环不跑、`existing` 为 None；新写入的 `supersedes` 直接被 KnowledgeStore 序列化）。

### 5.2 KnowledgeStore._entry_to_front_matter() 修复

**判断**：**修复方向正确，落在 design § 9 escape hatch 范围内**；finding 4.1 是 docstring 层面的小补强，不是 contract 缺口。

冷读链：
- F003 v1 publisher 在 strategy=supersede 路径写 `entry.front_matter["supersedes"]`，但 `_entry_to_front_matter` 不处理 dataclass 字段以外的 keys → v1 supersede 链事实上**从未** make it to disk（T2 handoff "中间发现" 段实测）
- F004 v1.1 publisher supersede 分支也走同一条 `_entry_to_front_matter` → 不修 `KnowledgeStore`，**v1.1 后写入的 supersedes 也会原样丢失**，FR-401 supersede 不变量 (§ 11.2.1) 直接 break
- design § 9 边界条款 "不修改 KnowledgeStore（**除非测试时发现 retrieve 路径有 bug**）" 显式允许此修复；T2 在调试 fail-first 测试时确认根因后再修，方向正确
- 70 个 knowledge + memory 测试 + supplementary `test_extra_front_matter_keys_round_trip` + `test_extra_front_matter_keys_do_not_overwrite_dataclass_keys` 全绿，覆盖完整

### 5.3 SessionManager `_persist_extraction_error` 自身写盘失败

**判断**：**符合 FR-307 / CON-401 + design § 14 失败模式裁决**。

冷读链：
- 当前 `try: write_json(...) except: pass` + `# pragma: no cover - defensive` + `logger.warning(..., exc_info=True)` 是**双层防护**
- design § 14 失败模式表已显式裁决："`_persist_extraction_error` 自身写盘失败 → 实践中几率低；若失败则 logger.warning 仍生效 → 双层防护，不再升级"
- 即使升级为 raise，archive_session 也不能阻塞（FR-404 验收 "archive_session() 仍返回 True"）；当前实现是该约束下的最优解
- `# pragma: no cover` 标注得当，无需进一步注释

无 finding。

### 5.4 CLI `--action=abandon` 仍走 confirmation 写入

**判断**：**与 design § 10.3 + ADR-403 一致，不应改动**。

冷读链：
- design § 10.3 表格 + 文末注释明确："当前 cli.py 总是 `store_confirmation`，包括 abandon 路径。v1.1 保留这个行为，只调整字段值；不改变'是否写 confirmation'"
- 改"是否写 confirmation" 是产品行为变更（USER-INPUT 类决策），属于 design 范围外的范围扩张；当前实现严格守住范围（CR5 = 9/10）
- 用户作为 abandon 的事后审计仍然受益于 confirmation 文件留存
- 若要 revisit 此行为，应走 `hf-increment` 路径补一条 spec/design 决策，而不是在 code review 阶段静默改

无 finding。

---

## 6. 代码风险与薄弱项

| 项 | 严重度 | 关联 finding | 备注 |
|----|--------|-------------|------|
| KnowledgeStore reserved-key 优先级 docstring 偏弱 | minor | 4.1 | 行为已被测试锁住，文档可补强 |
| archived_session.json 读取 None 静默 return | minor | 4.2 | 极边缘场景，实践上无法触发，可接受现状 |
| publisher.py mypy `object has no attribute __iter__` | trivial | — | F003 baseline 预 existing，T1 handoff 已声明，不在 F004 范围 |

无 critical / important 风险。

---

## 7. Anti-pattern 检查

| ID | Anti-pattern | 状态 |
|----|--------------|------|
| `CA1` silent failure | ⚠️ 仅 `_persist_extraction_error` 自身写盘 swallow（design 已裁决，双层防护）；其它路径无 swallow |
| `CA2` magic numbers | ❌ 未发现 — phase 名 / stdout 文案 / 文件名全部常量化 |
| `CA3` undocumented behavior | ❌ 未发现 — KnowledgeStore 修复在 design § 9 escape hatch；CLI 双 abandon 在 design § 10.3 |
| `CA4` design boundary leak | ❌ 未发现 — publisher 层管发布身份、KnowledgeStore 管存储、CLI 管 surface 表达，边界清晰 |
| `CA5` dead code / premature optimization | ❌ 未发现 — `PRESERVED_FRONT_MATTER_KEYS` 当前 2 键，design § 11.2.1 显式允许追加；`_merge_unique` 在 supersede 与 PRESERVED 路径双用，无重复抽象 |

---

## 8. 结论

**通过**

理由：
- 6 个维度评分全部 ≥ 8，无低于 6 的关键维度
- 4 个核心改动端到端正确：
  - publisher store-or-update 决策 + supersede chain carry-over + self-conflict 短路 → FR-401 + FR-405 锁住
  - publisher 入口 `_validate_conflict_strategy` → FR-402 锁住
  - KnowledgeStore 预 existing extra-key 丢失 bug 修复 → § 11.2.1 不变量得以兑现
  - SessionManager 3 phase + `_persist_extraction_error` → FR-404 锁住
  - CLI 双 abandon 路径 stdout + confirmation 字段差异化 → FR-403a/b/c 锁住
- 严格守住 design 边界（§ 10.1 / § 10.1.1 / § 11.1 / § 11.2 / § 11.2.1 / § 11.4 全部对齐；ADR-401~404 全部体现）
- KnowledgeStore 修复 = design § 9 escape hatch 显式允许范围
- CLI abandon 不删 confirmation 写入 = design § 10.3 明确指令
- 2 项 minor LLM-FIXABLE finding 都是补强（docstring + 1 像素的隐含 phase），非阻塞
- 414 passed 全 suite 零回归，下游 traceability review 可直接消费

可进入 `hf-traceability-review`。findings 4.1 / 4.2 可在 traceability review 后顺手收敛或在下一 cycle 处理。

---

## 9. 下一步

- **next_action_or_recommended_skill**: `hf-traceability-review`
- **needs_human_confirmation**: false
- **reroute_via_router**: false
- **rationale**: code review 通过，所有维度 ≥ 8/10，无 critical / important findings；2 项 minor 是 docstring 与边缘失败 phase 的补强，不阻塞下游 traceability review

---

## 10. 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-traceability-review",
  "record_path": "docs/reviews/code-review-F004-memory-v1-1.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][CR4] KnowledgeStore._entry_to_front_matter docstring 未显式声明 reserved-key 优先级（行为已被 test_extra_front_matter_keys_do_not_overwrite_dataclass_keys 锁住，仅文档薄弱）",
    "[minor][LLM-FIXABLE][CR3] SessionManager._trigger_memory_extraction 中 archived session.json 读取返回 None 静默 return，属隐含第 4 失败模式（极边缘，可接受现状）"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR4",
      "summary": "_entry_to_front_matter docstring 应明确声明 _DATACLASS_FRONT_MATTER_KEYS 中的 reserved 键不能被 entry.front_matter 同名 key 覆盖；行为已锁住，docstring 偏弱"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR3",
      "summary": "_trigger_memory_extraction 在 phase 2 通过、phase 3 之前的 archived_session.json 读取若返回 None 会静默 return，FR-404 phase 枚举只覆盖 3 值；可选地把读取段也作为 phase=archived_session_read 持久化错误，或接受现状（design § 14 双层防护已覆盖）"
    }
  ]
}
```

---

**文档状态**: 已落盘。父会话可基于本记录继续 `hf-traceability-review`。
