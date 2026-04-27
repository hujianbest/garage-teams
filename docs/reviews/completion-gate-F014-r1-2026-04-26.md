# Completion Gate — F014 r1 (Workflow Recall)

- **日期**: 2026-04-26
- **审阅人**: Cursor Agent (auto-streamlined per F011/F012/F013-A mode)

## Verdict: COMPLETE

## 通过条件 checklist

- [x] using-hf-workflow → hf-workflow-router (entry decision applied; full profile + auto-streamlined review)
- [x] hf-spec-review APPROVED (r2; 2026-04-26)
- [x] hf-design-review APPROVED (r2; 2026-04-26)
- [x] hf-tasks-review auto-streamlined (per F011/F012/F013-A mode)
- [x] hf-test-driven-dev T1-T5 完成 (5 task commits, 1043 passed +54, 0 regression)
- [x] hf-test-review APPROVED (`docs/reviews/test-review-F014-r1-2026-04-26.md`)
- [x] hf-code-review APPROVED (`docs/reviews/code-review-F014-r1-2026-04-26.md`)
- [x] hf-traceability-review APPROVED — 5/5 FR + 5/5 INV + 5/5 CON (`docs/reviews/traceability-review-F014-r1-2026-04-26.md`)
- [x] hf-regression-gate PASS — 1043 passed + ruff baseline diff 0 + 依赖 diff 0 + perf 0.064s (`docs/reviews/regression-gate-F014-r1-2026-04-26.md`)
- [x] Manual smoke 5 tracks 全绿 (`docs/manual-smoke/F014-walkthrough.md`)

## 用户可见交付物

| | |
|---|---|
| **新 CLI** | `garage recall workflow` |
| **flag 总数** | 6 个新 flag (--task-type / --problem-domain / --skill-id / --top-k / --json / --rebuild-cache) |
| **新模块** | `src/garage_os/workflow_recall/` 顶级包 (4 模块: types / cache / path_recaller / pipeline) |
| **测试基线** | 989 → 1043 passed (+54) |
| **零依赖变更** | pyproject.toml + uv.lock 无 diff |
| **新 .garage 数据** | `.garage/workflow-recall/{cache.json, last-indexed.json}` |
| **新 platform.json schema** | `workflow_recall.enabled: bool` (默认 true) |
| **router 集成** | hf-workflow-router/SKILL.md step 3.5 (additive) + references/recall-integration.md |
| **status 显示** | `garage status` 末尾加 workflow recall 段 (始终显; cache stale 附后缀) |

## 风险残余

- D-1410..D-1414 deferred to F015+ (RELEASE_NOTES 已记录)
- 当前 dogfood `.garage/experience/` 为空 (vision-gap § 3 已注), F014 hook 在本仓库不会触发; 其他用户跑后会触发
- F003-F013 既有 API + schema 字节级不变 (CON-1401 守门), 4 caller 加 try/except hook 调用 = 非 breaking 扩展
- HOST_REGISTRY 仍 hardcoded (B2 4/5; 未在 F014 范围内)

## 归档评估

✅ F014 cycle 可关闭, 进入 hf-finalize.
