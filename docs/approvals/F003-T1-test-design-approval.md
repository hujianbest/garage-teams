# Approval Record - F003 T1 Test Design

- Task ID: `T1`
- Task: 建立 memory 类型与候选/确认存储契约
- Approval Type: testDesignApproval
- Resolution Mode: auto
- Approver: cursor cloud agent (auto mode)
- Date: 2026-04-18

## Based On

- Task Plan: `docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md`
- Design: `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
- Tasks Approval: `docs/approvals/F003-tasks-approval.md`

## Test Design

1. 在 `tests/memory/test_candidate_store.py` 先写 fail-first 测试，覆盖：
   - 正常写入一个 batch + 两个 candidate 并可回读
   - 非法 `candidate_type` 被拒绝
   - 待确认队列中候选数超过 5 时被拒绝
2. 实现最小 `memory` 类型与存储层，仅满足 T1 契约，不提前实现提取/发布/推荐逻辑。
3. 用 `uv run pytest tests/memory/test_candidate_store.py -q` 产生 RED 与 GREEN 新鲜证据。

## Decision

Approved. T1 may enter `hf-test-driven-dev` and start with fail-first tests.
