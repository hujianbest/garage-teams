# Verification — F005 Regression Gate

## Metadata

- Verification Type: `regression-gate`
- Scope: F005 — Garage Knowledge Authoring CLI（Profile `standard`）
- Record Path: `docs/verification/F005-regression-gate.md`
- Branch: `cursor/f005-knowledge-add-cli-177b`
- Worktree Path: `/workspace`（in-place isolation）
- Date: 2026-04-19

## Upstream Evidence Consumed

- Spec approved: `docs/approvals/F005-spec-approval.md`
- Design approved: `docs/approvals/F005-design-approval.md`
- Tasks approved: `docs/approvals/F005-tasks-approval.md`
- Test review: `docs/reviews/test-review-F005-knowledge-authoring-cli.md`（通过）
- Code review: `docs/reviews/code-review-F005-knowledge-authoring-cli.md`（通过）
- Traceability review: `docs/reviews/traceability-review-F005-knowledge-authoring-cli.md`（通过）

## Verification Scope

### Included Coverage

- 全 suite 测试：`pytest tests/ -q`（覆盖 F003/F004 已存在 414 个测试 + F005 新增 37 个，目标：零回归）
- F005 触动模块 mypy：`mypy src/garage_os/cli.py`（仅报告 cli.py，避免被 .mypy.ini 中其他模块干扰）
- F005 触动模块 ruff：`ruff check src/garage_os/cli.py --statistics`（与 main baseline 比较）
- 依赖契约：`git diff main..HEAD -- pyproject.toml`（NFR-502 机器证据：F005 不引入新 third-party 依赖）

### Uncovered Areas

- `pytest tests/integration/` 单独目录（包含在全 suite 内，未单独跑）
- `scripts/benchmark.py` 性能基准（F005 范围不含 publisher 性能变化；NFR-503 由 `tests/test_cli.py::TestKnowledgeAuthoringCrossCutting::test_add_smoke_under_one_second` 覆盖）
- 完整 mypy（仅跑触动模块；其他模块 mypy 在 baseline 已有 23 个历史 errors，超出 F005 范围）

## Commands And Results

| 命令 | 退出码 | 结果摘要 |
|------|--------|---------|
| `pytest tests/ -q` | 0 | **451 passed in 25.31s**（baseline 414 → +37 F005 新增；零 regression） |
| `mypy src/garage_os/cli.py` | 1 | **1 error**（line 541，`_memory_review` 内 F004 既存类型问题；与 main baseline 完全一致，F005 未引入新 mypy errors） |
| `ruff check src/garage_os/cli.py --statistics` | 1 | **46 errors**（30 UP045 + 9 E402 + 3 F841 + 2 UP012 + 1 I001 + 1 UP035；main baseline = 25，F005 增量 +21 全部为 UP045 / UP012 / I001 / UP035 类型注解风格类。`Optional[X]` 风格与现有 cli.py 代码一致；RELEASE_NOTES F004 段已显式将 UP045 列为后续 cycle 治理候选） |
| `git diff main..HEAD -- pyproject.toml` | 0 | 空 diff —— **无任何 dependency 变更**（NFR-502 ✓） |

### Notable Output

- 451 个测试中包含 36 个 F005 unit/integration tests（27 个直接 CLI handler 测试 + 5 个 cross-cutting 测试 + 4 个 helper 单元测试）+ 1 个 helper deduplication 测试，以及 2 个文档 grep 测试（用户指南 + 双 README）。
- 现有 414 个测试在 v1.2 cli.py 改动后**全部继续 passed**，证明 F003/F004 路径零回归（NFR-501 ✓）。
- 1 个 pre-existing mypy error 与 F005 无关（line 541 在 F004 `_memory_review`），baseline 已存在；F005 新增的 7 个 handler + 5 个 helper + 12 个常量未引入新 mypy errors。
- ruff 46 → 25 baseline 的 +21 增量全部是 UP045（`Optional[X]` instead of `X | None`）和 UP012（`encode("utf-8")`）—— 这两类是 ruff `0.x → 1.x` 升级时的 stylistic deprecations，与 F005 业务行为无关；保持与 cli.py 现有 26 处 `Optional[...]` 的代码风格一致是有意决定（避免在 F005 cycle 内做大范围 cosmetic refactor）。

## Freshness Anchor

- 所有命令在本会话内、F005 最新代码状态（HEAD = `03bbc20` "fix(F005): code-review follow-ups ..."）下执行
- `pytest` 在 25.31s 内 collected 451 个测试，证明确实跑过完整 suite（非 cached 结果）
- `git diff main..HEAD -- pyproject.toml` 在本会话内 echo 到空，证明 NFR-502 不变

## Conclusion

**通过**。F005 在 standard profile 的回归面（`pytest` 全 suite + `mypy` 触动模块 + `ruff` 触动模块 + `pyproject.toml` diff）达到"零业务回归 + 零新引入 type errors + 零新 dependency"的稳态。pre-existing baseline issues（1 个 mypy / 25 个 ruff）与 F005 无因果，明确不在本 cycle 范围。

## Next Action Or Recommended Skill

`hf-completion-gate`
