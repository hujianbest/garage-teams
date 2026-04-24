# Regression Gate — F009 `garage init` 双 Scope 安装 + 交互式 Scope 选择 (r1)

- **日期**: 2026-04-23
- **Gate Owner**: hf-regression-gate (in-cycle, agent mode)
- **关联 PR**: #24 (`cursor/f009-init-scope-selection-bf33`)
- **前序 reviews**:
  - test-review-F009-r1: APPROVE_WITH_FINDINGS (0 critical)
  - code-review-F009-r1: APPROVE_WITH_FINDINGS (0 critical, I-3+I-4 in-cycle fix)
  - traceability-review-F009-r1: APPROVE_WITH_FINDINGS (0 critical, 3 important hf-finalize carry-forward)

## Verdict: **PASS**

## Regression 数据

| 维度 | F008 baseline | F009 实施完成 | 差值 | 守门 |
|---|---|---|---|---|
| 全套 pytest | 633 passed | 713 passed | +80 | ✓ 0 退绿 |
| `ruff check src/` 错误数 | 51 | 51 | 0 | ✓ NFR-902 |
| Sentinel 测试 (43 用例: dogfood + drift + neutrality + neutrality_exemption) | all pass | all pass | — | ✓ |
| F007/F008 既有 installer 测试 (test_pipeline + test_idempotent + test_full_packs_install + test_packs_garage_extended, 23 用例) | all pass | all pass | — | ✓ CON-901 |
| Manual smoke walkthrough | F008 4 tracks all green | F009 4 tracks all green | — | ✓ NFR-901 dogfood |
| `git diff main..HEAD -- pyproject.toml uv.lock` 输出 | — | empty | — | ✓ 零依赖变更 |

## 关键守门

✅ **NFR-902 (零退绿)**: 633 → 713 passed, 0 regression
✅ **CON-901 (F007/F008 字节级兼容)**: F007/F008 既有 installer 测试 23/23 通过; manual smoke Track 1 dogfood `Installed 58 skills, 1 agents into hosts: claude, cursor` 与 F008 baseline 字节级一致
✅ **CON-902 (D7 phase 1+3 字节级)**: 既有 phase 1 + phase 3 算法分支结构未动 (test_pipeline 等通过), 守门偏弱由 hf-finalize carry-forward (I-1)
✅ **NFR-901 (Dogfood 不变性)**: `test_dogfood_invariance_F009` sentinel 通过 (59 文件 SHA-256 与 baseline 一致); `test_dogfood_layout` (F008 sentinel) 通过
✅ **NFR-903 (perf)**: Manual smoke `garage init --hosts all --scope user` wall_clock 0.11s << 5s 上限
✅ **CON-904 (Manifest migration 安全语义)**: `test_corrupted_manifest_not_overwritten` (SHA-256 + mtime 严格守门) 通过
✅ **NFR-904 (commit 可审计)**: 8 cycle commits (T1-T6 + manual smoke + post-code-review), 每 commit 改动范围在 design § 11 估算内

## 已知 carry-forward (hf-finalize approval 显式记录)

- **I-1 / F-1 (CON-902 phase 1+3 body 守门)**: F010 candidate
- **I-2 / F-3 (VersionManager host-installer migration 链注册)**: F010 candidate, 与 garage uninstall/update --scope 同 cycle
- **F-2 (3 处用户面文档 schema_version=1 wording)**: hf-finalize 阶段同步小修

## 下一步

✅ **派发 `hf-completion-gate`**.

## Structured Return

```json
{
  "conclusion": "通过",
  "verdict": "PASS",
  "next_action_or_recommended_skill": "hf-completion-gate",
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "测试基线": "713 passed (+80 from F008 baseline 633, 0 regressions)",
  "ruff_baseline_diff": 0,
  "manual_smoke": "4/4 tracks green (dogfood + project + user + mixed)"
}
```
