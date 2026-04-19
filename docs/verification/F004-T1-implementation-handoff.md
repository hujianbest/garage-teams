# 实现交接块 — F004 T1

- Task ID: T1 — `PublicationIdentityGenerator` + publisher 入口校验前置
- 回流来源: 主链实现（F004 cycle 第 1 个任务）
- 触碰工件:
  - `src/garage_os/memory/publisher.py`（+ `PublicationIdentityGenerator` class、+ `_validate_conflict_strategy`、`publish_candidate` 入口前置校验、删除冗余 conflict 分支校验）
  - `tests/memory/test_publisher.py`（+ `KnowledgeType` import、+ `TestPublicationIdentityGenerator` 2 个测试、+ `TestPublishCandidateEntryValidation` 3 个测试）
  - `docs/approvals/F004-T1-test-design-approval.md`（auto-mode self-approval）
- Workspace Isolation / Worktree Path / Worktree Branch:
  - Workspace Isolation: `in-place`
  - 分支: `cursor/f004-memory-polish-1bde`

## 测试设计确认证据

`docs/approvals/F004-T1-test-design-approval.md`（auto-mode self-approval；5 个测试名 1:1 映射 task plan T1 测试种子 + design §11.1 / §11.2 contract）

## RED 证据

```
$ pytest tests/memory/test_publisher.py::TestPublicationIdentityGenerator tests/memory/test_publisher.py::TestPublishCandidateEntryValidation -v 2>&1 | tail -10
FAILED tests/memory/test_publisher.py::TestPublicationIdentityGenerator::test_publication_identity_generator_is_deterministic - ImportError: cannot import name 'PublicationIdentityGenerator' from 'garage_os.memory.publisher'
FAILED tests/memory/test_publisher.py::TestPublicationIdentityGenerator::test_publication_identity_default_returns_candidate_id - ImportError: cannot import name 'PublicationIdentityGenerator' from 'garage_os.memory.publisher'
FAILED tests/memory/test_publisher.py::TestPublishCandidateEntryValidation::test_publish_candidate_rejects_garbage_strategy_at_entry - Failed: DID NOT RAISE <class 'ValueError'>
========================= 3 failed, 2 passed in 0.13s ==========================
```

3 fail-first 测试失败原因符合预期：
1. `PublicationIdentityGenerator` 类不存在 → ImportError
2. 同上
3. 当前 publisher 仅在 conflict 分支校验 garbage strategy；无冲突路径下不抛错 → DID NOT RAISE

2 个边界测试已经在 v1 行为下通过（`test_publish_candidate_accepts_valid_strategy_without_conflict` / `test_publish_candidate_none_strategy_passes_when_no_conflict`），它们锁住的是 v1 兼容性，提前通过是正确的。

## GREEN 证据

```
$ pytest tests/memory/test_publisher.py -v 2>&1 | tail -3
tests/memory/test_publisher.py::TestPublishCandidateEntryValidation::test_publish_candidate_none_strategy_passes_when_no_conflict PASSED [100%]
============================== 16 passed in 0.20s ==============================
```

16/16 测试通过：5 个 T1 新增 + 11 个 F003 现有测试零回归。

```
$ pytest tests/ -q 2>&1 | tail -3
tests/tools/test_tool_registry.py .............                          [100%]
============================= 389 passed in 25.10s =============================
```

全 suite **389 passed**（baseline 384 + T1 新增 5 = 389），FR-405 兼容性兜底验证通过。

## 与任务计划测试种子的差异

完全一致。task plan T1 列出 5 个种子，全部实现：
- 种子 1 = `test_publication_identity_generator_is_deterministic`
- 种子 2 = `test_publication_identity_default_returns_candidate_id`
- 种子 3 = `test_publish_candidate_rejects_garbage_strategy_at_entry`
- 种子 4 = `test_publish_candidate_accepts_valid_strategy_without_conflict`
- 种子 5 = `test_publish_candidate_none_strategy_passes_when_no_conflict`

## 剩余风险 / 未覆盖项

- `PublicationIdentityGenerator` 当前仅 default 实现（candidate_id 透传），无配置注入；ADR-401 已说明这是有意为之，未来切换策略只改 `derive_*` 内部即可（未覆盖：可配置策略的注入路径）—— 不在 T1 范围。
- `_validate_conflict_strategy` 仅在 `publish_candidate` 入口调用；如果未来增加其他 publisher 公共方法（如 `republish_candidate`），需要同样调用 — design §11.2 已暗含约束 — 不在 T1 范围。
- 预 existing mypy 错误 `publisher.py:117 "object" has no attribute "__iter__"` 与预 existing ruff UP045 警告（Optional → `X | None`）不在 T1 范围；F003 baseline 同样存在，无新增。
- T1 不涉及 store-or-update 决策、supersede 链 carry-over、self-conflict 短路 — 全部归属 T2。

## Pending Reviews And Gates

T1 实现已就绪，可继续推进 T2~T5；按 task plan §6.1 选择规则，T1 完成后 router 重选 T2（P1）。F004 cycle 在所有 T1~T5 完成后统一进入 `hf-test-review` → `hf-code-review` → `hf-traceability-review` → `hf-regression-gate` → `hf-completion-gate` → `hf-finalize`。

## Next Action Or Recommended Skill

`hf-test-driven-dev` (T2 — store-or-update + supersede carry-over + self-conflict short-circuit)
