# Tasks Review F010 r1 — 2026-04-24

- 评审对象: `docs/tasks/2026-04-24-garage-context-handoff-and-session-ingest-tasks.md` (草稿 r1)
- Reviewer: Independent generalPurpose subagent (read-only, hf-tasks-review SKILL)

## Verdict: **需修改** (REVISE)

骨架完整, 7 task ↔ design § 5 严格 1:1, INVEST 各维度 ≥ 6/10. 但 2 条 important findings + 4 minor 需定向回修. 全部 LLM-FIXABLE, 不需 reroute via router.

## Findings

### Important (2)

- **I-1 [TR3]**: INV-F10-2 sentinel `test_baseline_no_regression.py` 未落到任何 task. design § 4.1 显式承诺 + design-review-r1 I-4 已要求, 但 7 task 的 Test Design Seeds 均未列该文件; § 3 测试基线守门表是人工目标值, 不等价自动化 sentinel.
- **I-2 [TR2]**: T6 Acceptance 缺 `update_session(context_metadata=)` 真实 kwarg 名锚点. design ADR-D10-9 r2 显式锚定; T6 body mention `archive_session(reason=)` + `extract_for_archived_session_id` 但漏 update_session; design r1/r2 已因 API drift 反复 fix C-1/C-2, 实施期同类 drift 风险高.

### Minor (4)

- **M-1 [TR3]**: T3 Verify bash 块漏列 `test_pipeline_three_way_hash.py`
- **M-2 [TR5]**: T5 fixture 文件创建任务未显式列出 (`tests/ingest/fixtures/{claude_code,opencode}/<id>.json`)
- **M-3 [TR6]**: 缺显式 Current Active Task selection rule
- **M-4 [TA5]**: T7 缺 "Test Design Seeds" 段 (与 T1-T6 格式不一致)

## Structured Return

```json
{
  "conclusion": "需修改",
  "verdict": "REVISE (1 round, low effort)",
  "next_action_or_recommended_skill": "hf-tasks",
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_count": {"critical": 0, "important": 2, "minor": 4},
  "all_llm_fixable": true,
  "user_input_count": 0
}
```
