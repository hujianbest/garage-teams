# Regression Gate F010 r1 — 2026-04-24

## Verdict: **PASS**

| 维度 | F009 baseline | F010 实施完成 | 差值 | 守门 |
|---|---|---|---|---|
| 全套 pytest | 715 passed | 824 passed | +109 | ✓ 0 退绿 |
| `ruff check src/garage_os/{sync,ingest}/` errors | (新增模块) | **0** | — | ✓ |
| `ruff check src/garage_os/cli.py` errors | (existing baseline) | unchanged | — | ✓ F010 净增 0 lint error |
| INV-F10-1..10 (含 dogfood SHA-256 sentinel + INV-F10-2 baseline sentinel) | — | all pass | ✓ | ✓ |
| Dogfood `garage init --hosts cursor,claude` stdout | F009: `Installed 62 skills, 1 agents into hosts: claude, cursor` | 同 | 字节级一致 | ✓ NFR-1001 |
| Manual smoke 4 tracks (dogfood / project / user mixed / ingest e2e) | — | all green | ✓ | ✓ NFR-1004 perf ~0.1s << 5s |
| `git diff main..HEAD -- pyproject.toml uv.lock` | — | empty | ✓ | ✓ 零依赖变更 |

## 关键守门

✅ **NFR-902 / INV-F10-2 (零退绿)**: 715 → 824 passed (+109, 0 regression)
✅ **CON-1001 (F009 字节级)**: F009 既有 init / status 行为字节级保留 (sync-manifest 不存在时 status fallback)
✅ **CON-1002 (F003-F006 0 改动)**: F003 既有 318 测试通过, ingest 走既有 archive_session + extract_for_archived_session_id public API
✅ **NFR-1001 (Dogfood)**: dogfood `garage init --hosts cursor,claude` 字节级与 F009 一致
✅ **NFR-1002 (mtime stability)**: `test_pipeline_idempotent.py` 通过
✅ **NFR-1003 (user content preserved)**: `test_pipeline_user_content_preserved.py` + IMP-2 fix 后 cursor `.mdc` fallback 路径也守门
✅ **NFR-1004 (perf)**: manual smoke ~0.1s << 5s
✅ **CON-1005 (manifest 隔离)**: sync-manifest.json 与 host-installer.json 独立模块 + 独立文件
✅ **CON-1004 (B5 user-pact)**: ingest 走 candidate review (CandidateStore items + batches), 不绕过 publisher
✅ **CON-1007 (cursor deferred)**: cursor reader stub NotImplementedError + CLI catch + stderr 友好消息

## 已知 carry-forward (hf-finalize 显式记录)

- test-review-r1 IMP-1 + traceability MIN-2: `tests/ingest/test_e2e_import_then_sync.py` SM-1002 round-trip 自动 e2e (manual smoke Track 4 已覆盖, 自动化补足留 finalize)
- test-review-r1 + code-review-r1 + traceability MIN-1..3 + 多 nit: docs 微调 + RELEASE_NOTES 5 项 TBD 占位填实测 + tasks/design 测试合并回写

## 下一步

✅ **派发 hf-completion-gate**.

## Structured Return

```json
{
  "conclusion": "通过",
  "verdict": "PASS",
  "next_action_or_recommended_skill": "hf-completion-gate",
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "test_baseline": "715 → 824 passed (+109, 0 regressions)",
  "ruff_baseline_diff": 0,
  "manual_smoke": "4/4 tracks green"
}
```
