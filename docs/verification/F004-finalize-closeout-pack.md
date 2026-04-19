# F004 Finalize — Closeout Pack

## Closeout Summary

- Closeout Type: `workflow-closeout`
- Scope: F004 Garage Memory v1.1（发布身份解耦与确认语义收敛）— cycle 内全部任务（T1-T5）已完成；F003 显式延后的 4 项 finding 全部端到端关闭；无剩余 approved tasks
- Conclusion: **F004 cycle 正式关闭**
- Based On Completion Record: `docs/verification/F004-completion-gate.md`（结论：通过）
- Based On Regression Record: `docs/verification/F004-regression-gate.md`（结论：通过）

## Evidence Matrix

| Artifact | Record Path | Status |
|----------|-------------|--------|
| Spec | `docs/features/F004-garage-memory-v1-1-publication-identity-and-confirmation-semantics.md` | 已批准（auto-mode r1） |
| Spec approval | `docs/approvals/F004-spec-approval.md` | Applied |
| Spec review | `docs/reviews/spec-review-F004-memory-v1-1.md` | 通过 |
| Design (r1) | `docs/designs/2026-04-19-garage-memory-v1-1-design.md` | 已批准（auto-mode r1） |
| Design approval | `docs/approvals/F004-design-approval.md` | Applied |
| Design review | `docs/reviews/design-review-F004-memory-v1-1.md` | 需修改 → r1 by author self-check 1:1 闭合 |
| Tasks plan | `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md` | 已批准（auto-mode r1） |
| Tasks approval | `docs/approvals/F004-tasks-approval.md` | Applied |
| Tasks review | `docs/reviews/tasks-review-F004-memory-v1-1.md` | 通过 |
| Test design approvals (T1-T4) | `docs/approvals/F004-T1-test-design-approval.md` ~ `F004-T4-test-design-approval.md` | Applied |
| Implementation handoffs | `docs/verification/F004-T1-implementation-handoff.md`、`F004-T2-implementation-handoff.md`、`F004-T5-implementation-handoff.md`（T3+T4 嵌入 commit message） | 完整 |
| Test review | `docs/reviews/test-review-F004-memory-v1-1.md` | 通过（4 项 minor，2 项已补 supplementary tests） |
| Code review | `docs/reviews/code-review-F004-memory-v1-1.md` | 通过（2 项 minor docstring 已补） |
| Traceability review | `docs/reviews/traceability-review-F004-memory-v1-1.md` | 通过（2 项 minor LLM-FIXABLE 留 finalize 顺手处理） |
| Regression gate | `docs/verification/F004-regression-gate.md` | 通过 |
| Completion gate | `docs/verification/F004-completion-gate.md` | 通过 |
| Release notes | `RELEASE_NOTES.md` `## F004 — Garage Memory v1.1` 段 | Updated |
| Finalize closeout pack | `docs/verification/F004-finalize-closeout-pack.md`（本文件） | This file |
| User guide doc section | `docs/guides/garage-os-user-guide.md` "Memory review — abandon paths" 段 | Updated |
| Developer guide doc sections | `docs/guides/garage-os-developer-guide.md` "Publisher 重复发布与 ID 生成规则" + "Session memory-extraction-error.json schema" 段 | Updated |

## State Sync

- Current Stage: `closed`
- Current Active Task: `null`（cycle 已关闭，无活跃任务）
- Workspace Isolation: `in-place`
- Worktree Path: `N/A`（never created worktree）
- Worktree Branch: `cursor/f004-memory-polish-1bde`（PR branch；未来如需修订，可继续在该分支 work）
- Worktree Disposition: `branch retained on origin/cursor/f004-memory-polish-1bde`

## Release / Docs Sync

- Release Notes Path: `RELEASE_NOTES.md`（F004 段为最新条目，置顶 F003 条目之上）
- Updated Docs:
  - `docs/guides/garage-os-user-guide.md`（新增 "Memory review — abandon paths" 段）
  - `docs/guides/garage-os-developer-guide.md`（新增 "Publisher 重复发布与 ID 生成规则" + "Session memory-extraction-error.json schema" 两段）
  - `docs/features/F004-...md`（状态 = 已批准 auto-mode）
  - `docs/designs/2026-04-19-...md`（状态 = 已批准 auto-mode r1）
  - `docs/tasks/2026-04-19-...md`（状态 = 已批准 auto-mode r1）

## Handoff

- Remaining Approved Tasks: 无（T1-T5 全部 done）
- Next Action Or Recommended Skill: `null`（workflow 已关闭）
- PR / Branch Status: `cursor/f004-memory-polish-1bde` 推送至 `origin`，对应 PR #15（draft），将在本 finalize 后更新 PR 描述
- Limits / Open Notes:
  - **Trace 矩阵措辞补强（TZ5 minor）**：design § 3 / § 9 trace 矩阵未显式登记 KnowledgeStore extra-key 修复（已在 design § 9 escape hatch + 4 处文档化，仅措辞机会）。本次 finalize 不强制回流 design；后续 cycle 启动时由 router 视情况判断是否纳入。
  - **T5 implementation handoff RED 段仅 narrative**（TT5 minor）：lint-only 测试已接受现状，不强制回流。
  - **Pre-existing baseline mypy 23 errors / ruff UP045 警告**：F002 / F003 历史，非 F004 引入；由后续 cycle 单独治理。
  - **`scripts/benchmark.py` 不补 publisher 专项基准**：ASM-403 已裁决；如未来用户大量重复发布出现性能或 git diff 噪声升级，可独立立项。
  - **CLI `--action=abandon` 仍写 confirmation**：与 design § 10.3 + ADR-403 一致；如要 revisit 应走 `hf-increment`。

## 触动文件清单

源代码（4 个）:
- `src/garage_os/memory/publisher.py`（+ `PublicationIdentityGenerator` + 入口校验 + `_merge_unique` + `PRESERVED_FRONT_MATTER_KEYS` + store-or-update 决策 + supersede carry-over + self-conflict 短路）
- `src/garage_os/runtime/session_manager.py`（+ 三 phase try/except + `_persist_extraction_error` + `MEMORY_EXTRACTION_ERROR_FILENAME`）
- `src/garage_os/cli.py`（+ `MEMORY_REVIEW_ABANDONED_NO_PUB` / `MEMORY_REVIEW_ABANDONED_CONFLICT` 模块常量 + abandon 双路径 stdout/status 差异化）
- `src/garage_os/knowledge/knowledge_store.py`（修复 `_entry_to_front_matter` 不持久化 extra keys 的预 existing bug；新增 `_DATACLASS_FRONT_MATTER_KEYS` 元组 + extra keys merge）

测试（30 个新增）:
- `tests/memory/test_publisher.py`：`TestPublicationIdentityGenerator`(2) + `TestPublishCandidateEntryValidation`(3) + `TestPublishCandidateRepublication`(8 = 6 主测试 + 2 supplementary: supersede merge / experience created_at)
- `tests/test_cli.py`：`TestMemoryReviewAbandonDualPaths`(6)
- `tests/runtime/test_session_manager.py`：`TestF004T4ExtractionErrorPersistence`(6)
- `tests/test_documentation.py`：3 个 docs lint
- `tests/knowledge/test_knowledge_store.py`：+ 2 个 supplementary tests（`test_extra_front_matter_keys_round_trip` + `test_extra_front_matter_keys_do_not_overwrite_dataclass_keys`）

文档:
- `docs/features/F004-...md`（spec）
- `docs/designs/2026-04-19-...md`（design r1）
- `docs/tasks/2026-04-19-...md`（tasks plan）
- `docs/guides/garage-os-user-guide.md`（新增 abandon paths 段）
- `docs/guides/garage-os-developer-guide.md`（新增 2 段）
- `RELEASE_NOTES.md`（F004 cycle 段）
- 6 个 reviews + 3 个 approvals + 4 个 test design approvals + 3 个 implementation handoffs + 1 个 regression gate + 1 个 completion gate + 本 closeout pack

## Verification

```
$ pytest tests/ -q
============================= 414 passed in ~25s ==============================
```

零回归；F003 baseline 384 → F004 终态 414，新增 30 个测试。

## Workflow Closeout 决议

按 `hf-finalize` § 3A：本会话是 `auto` mode，按项目 auto 规则在写完 closeout pack 后即把 workflow 视为已关闭。Current Stage 设为 `closed`，Next Action 设为 `null`。
