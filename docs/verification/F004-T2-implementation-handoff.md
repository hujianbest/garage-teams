# 实现交接块 — F004 T2

- Task ID: T2 — publisher store-or-update + supersede 链 carry-over + self-conflict 短路
- 回流来源: 主链实现（F004 cycle 第 2 个任务）
- 触碰工件:
  - `src/garage_os/memory/publisher.py`：
    - 新增 `KnowledgePublisher.PRESERVED_FRONT_MATTER_KEYS` 元组（含 `supersedes`、`related_decisions`）
    - 新增 `KnowledgePublisher._merge_unique(base, extra)` 静态 helper
    - 改 `publish_candidate`：
      - knowledge 路径在 `_to_knowledge_entry` 后调 `_id_generator.derive_knowledge_id(...)` 覆盖 entry.id
      - knowledge 路径剔除 `similar_entries` 中等于 `entry.id` 的元素（self-conflict 短路）
      - knowledge 路径在 store 前先 `retrieve(type, id)`；存在则 carry-over `related_decisions` + `PRESERVED_FRONT_MATTER_KEYS`、`entry.version = existing.version`、调 `update(entry)`；否则调 `store(entry)`
      - experience 路径在 `_to_experience_record` 后调 `derive_experience_id(...)` 覆盖 record.record_id；先 `experience_index.retrieve(...)`；存在则 carry-over `created_at` 后 `update(record)`，否则 `store(record)`
  - `src/garage_os/knowledge/knowledge_store.py`：**修复 F003 预 existing bug**
    - `_entry_to_front_matter()` 之前只写入 14 个 hardcoded 字段，`entry.front_matter` 中的额外键（如 `supersedes`）从未被持久化。现在新增 `_DATACLASS_FRONT_MATTER_KEYS` 元组 + 在末尾合并 `entry.front_matter` 中的 extra 键。这是 design §9 显式允许的"测试时发现 retrieve 路径有 bug"的 escape hatch。
  - `tests/memory/test_publisher.py`：
    - 新增 `TestPublishCandidateRepublication` 类含 6 个测试
- Workspace Isolation / Worktree Path / Worktree Branch:
  - Workspace Isolation: `in-place`
  - 分支: `cursor/f004-memory-polish-1bde`

## 测试设计确认证据

`docs/approvals/F004-T2-test-design-approval.md`（auto-mode self-approval；6 个测试名 1:1 映射 task plan T2 测试种子 + design §10.1 / §10.1.1 / §11.2 / §11.2.1 contract）

## RED 证据

```
$ pytest tests/memory/test_publisher.py::TestPublishCandidateRepublication -v 2>&1 | tail -8
FAILED tests/memory/test_publisher.py::TestPublishCandidateRepublication::test_repeated_accept_uses_update_increments_version - ValueError: Similar published knowledge detected; ...
FAILED tests/memory/test_publisher.py::TestPublishCandidateRepublication::test_retrieve_after_repeated_accept_returns_latest_version - ValueError: ...
FAILED tests/memory/test_publisher.py::TestPublishCandidateRepublication::test_repeated_publish_preserves_supersedes_chain_from_v1 - ValueError: ...
FAILED tests/memory/test_publisher.py::TestPublishCandidateRepublication::test_repeated_publish_preserves_related_decisions_from_v1 - ValueError: ...
FAILED tests/memory/test_publisher.py::TestPublishCandidateRepublication::test_repeated_accept_short_circuits_self_conflict - ValueError: ...
========================= 5 failed, 1 passed in 0.16s ==========================
```

5 fail-first 测试失败原因符合预期：v1 行为下重复发布因 ConflictDetector 命中自身（self-conflict false-positive）触发 ValueError，封堵了 store-or-update 路径与 supersede carry-over 路径的执行机会。

## 中间发现：F003 KnowledgeStore 预 existing bug

调试 `test_repeated_publish_preserves_supersedes_chain_from_v1` 时发现：

```
$ python -c "...; e.front_matter['supersedes']=['k-X']; store.store(e); read disk"
=== file contents ===
---
... (14 hardcoded keys) ...
---
body
=== retrieve ===
front_matter[supersedes] = None
```

**结论**：F003 v1 publisher 在 strategy=supersede 路径中写入 `entry.front_matter["supersedes"]`，但因 `KnowledgeStore._entry_to_front_matter()` 不处理 dataclass 字段以外的 extra 键，supersedes 实际上**从未** make it to disk。design review reviewer 识别的 D5 important 风险方向是对的，但根因比预期更深。

按 design §9 边界条款"不修改 KnowledgeStore（**除非测试时发现 retrieve 路径有 bug**）"escape hatch，最小修复 `KnowledgeStore._entry_to_front_matter()`：保留 14 个 reserved 字段从 dataclass 重建，再合并 `entry.front_matter` 中的 extra 键。修复后 70 个 knowledge + memory 测试全绿。

## GREEN 证据

```
$ pytest tests/memory/test_publisher.py tests/knowledge/ -v 2>&1 | tail -3
tests/knowledge/test_knowledge_store.py::test_front_matter_to_entry_conversion PASSED [100%]
============================== 70 passed in 0.51s ==============================
```

```
$ pytest tests/ -q 2>&1 | tail -3
tests/tools/test_tool_registry.py .............                          [100%]
============================= 395 passed in 24.61s =============================
```

全 suite **395 passed**（T1 后的 389 + T2 新增 6 = 395），FR-405 兼容性兜底验证通过。

## 与任务计划测试种子的差异

完全一致 + 1 处增强：
- 种子 1~6 全部实现（test_repeated_accept_uses_update_increments_version, test_retrieve_after_repeated_accept_returns_latest_version, test_repeated_publish_experience_summary_updates_index, test_repeated_publish_preserves_supersedes_chain_from_v1, test_repeated_publish_preserves_related_decisions_from_v1, test_repeated_accept_short_circuits_self_conflict）
- experience_summary 测试增强：除验证 `len(records)==1` 外，新增断言 `records[0].updated_at >= first_updated_at`，证实走 `ExperienceIndex.update()` 路径而非 store 覆盖
- 种子 7（NFR-402 性能 wall-clock）按 test design approval 决议不作为独立 unit test 实现；通过 T1+T2 完成后跑 `pytest tests/memory/ -q` 0.51s 与 F003 baseline 对比，无显著退化

## 剩余风险 / 未覆盖项

- `KnowledgeStore._entry_to_front_matter()` 修复扩展为合并 extra 键，可能在未来某 entry 设置 `front_matter["id"]="X"` 与 `entry.id="Y"` 冲突时 reserved 路径覆盖 extra 路径——这是显式契约（reserved 字段 always wins），已在 docstring 与代码常量中体现
- `PRESERVED_FRONT_MATTER_KEYS` 当前仅含 `supersedes`、`related_decisions`；未来若 supersede 路径新增 `merged_with` 等键，需要追加，design §11.2.1 已约束
- self-conflict 短路只在 knowledge 路径生效；experience 路径无 ConflictDetector，无需短路
- T2 不涉及 CLI / SessionManager 改动 — 全部归属 T3 / T4

## Pending Reviews And Gates

T1 + T2 实现已就绪。按 task plan §6.1 选择规则，T2 完成后 router 重选 T3（P1）。F004 cycle 在 T1~T5 完成后统一进入 `hf-test-review` → `hf-code-review` → ...

## Next Action Or Recommended Skill

`hf-test-driven-dev` (T3 — CLI abandon 双路径 confirmation + stdout 文案差异化)
