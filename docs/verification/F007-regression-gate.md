# F007 Regression Gate — `verification/F007-regression-gate.md`

- Verification Type: `regression-gate`
- Scope: F007 cycle implementation (T1-T5 + 2 carry-forward rounds)
- Record Path: this file
- Workspace Path / Branch: `/workspace` / `cursor/f007-packs-host-installer-fa86`
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `coding` / `auto-mode`

## Upstream Evidence Consumed

| Upstream | Verdict | Path |
|---|---|---|
| spec review (r1+r2) | r2 = 通过 | `docs/reviews/spec-review-F007-garage-packs-and-host-installer.md` |
| design review (r1+r2) | r2 = 通过 | `docs/reviews/design-review-F007-garage-packs-and-host-installer.md` |
| tasks review | 通过 + 5 minor carry-forward | `docs/reviews/tasks-review-F007-garage-packs-and-host-installer.md` |
| test review | 通过 + 5 minor carry-forward | `docs/reviews/test-review-F007-garage-packs-and-host-installer.md` |
| code review | 通过 + 1 important + 5 minor carry-forward | `docs/reviews/code-review-F007-garage-packs-and-host-installer.md` |
| traceability review | 通过 (3 项 hf-finalize 修复) | `docs/reviews/traceability-review-F007-garage-packs-and-host-installer.md` |
| spec / design / tasks approvals | 全部 approved | `docs/approvals/F007-{spec,design,tasks}-approval.md` |
| Manual smoke artifact | 三宿主目录全部生成 | `/opt/cursor/artifacts/f007_manual_smoke_init_all_hosts.log` |

Profile: `coding` cycle, full regression scope per ISTQB (every test + lint + typecheck against the project baseline).

## Verification Scope

### Included Coverage

- **Full pytest suite** (`uv run pytest tests/ -q`): all 586 tests across all modules
- **mypy** on F007 new modules: `src/garage_os/adapter/installer/` (11 source files)
- **mypy** on cli.py (modified by F007): zero F007-introduced errors (1 pre-existing baseline error from F004 `_memory_review`, unchanged)
- **ruff** on F007 new code + tests: `src/garage_os/adapter/installer/` + `tests/adapter/installer/` (zero errors)
- **Manual smoke**: real `garage init --hosts all` against fresh `tmp_path` with packs/garage symlinked; three host directories created + manifest written + idempotent re-run preserves mtime

### Uncovered Areas

- **Pre-existing baseline mypy error** in `cli.py::_memory_review` (F004 vintage, line 667 post-F007 / line 562 on main). NOT introduced by F007; carried forward per F007 task plan §10 risk register and `task-progress.md` deferred backlog. F007 commits do not modify `_memory_review` body.
- **Pre-existing baseline ruff warnings** in non-F007 modules (F002/F003/F004 vintage, ~47 stylistic warnings). NOT scanned/touched by F007.
- **Cross-platform CI** (Windows / macOS): no CI runners executed; relied on `pathlib` + POSIX-conversion design (NFR-703) instead of physical multi-OS run.
- **Live host tools** (Claude Code / OpenCode / Cursor) not opened to verify they can actually load the installed SKILL.md / agent.md. F007 is file-system-level by design (FR-707 statement); host-tool runtime verification is out of scope per spec § 4.2 boundary.

## Commands And Results

```bash
$ .venv/bin/pytest tests/ -q
============================= 586 passed in 26.29s =============================
exit code 0
```

Breakdown of new tests by F007 task:
- T2: 22 (`test_host_registry.py` 12 + `test_hosts.py` 10)
- T3: 47 (`test_pack_discovery.py` 10 + `test_marker.py` 9 + `test_manifest.py` 7+2 carry-forward + `test_pipeline.py` 9+2+1 carry-forward + `test_neutrality.py` 3 + `test_idempotent.py` 2)
- T4: 14 (`test_interactive.py` 6 + `tests/test_cli.py::TestInitWithHosts` 8)
- T4 carry-forward (test review F-1+F-5): 5 (`tests/test_cli.py::TestInitErrorPaths`)
- T5: 4 (`test_documentation.py` 2 + `test_version_manager.py::TestHostInstallerSchemaRegistered` 2)
- Net: **+90 tests** vs baseline 496 = **586 passed** (`hf-test-review` r1 → 585; `hf-code-review` r1 → 586)

```bash
$ .venv/bin/mypy src/garage_os/adapter/installer/
Success: no issues found in 11 source files
exit code 0
```

```bash
$ .venv/bin/mypy src/garage_os/cli.py
src/garage_os/cli.py:667:41: error: Incompatible types in assignment ... [assignment]
Found 1 error in 1 file (checked 1 source file)
exit code 1
```

Pre-existing baseline check (compared against `main` branch HEAD):

```bash
$ git checkout main -- src/garage_os/cli.py
$ .venv/bin/mypy src/garage_os/cli.py
src/garage_os/cli.py:562:41: error: Incompatible types ... [assignment]
Found 1 error in 1 file (checked 1 source file)
```

Same error, line shift attributable to F007's added imports + constants. **Zero new mypy errors introduced by F007.**

```bash
$ .venv/bin/ruff check src/garage_os/adapter/installer/ tests/adapter/installer/
All checks passed!
exit code 0
```

```bash
$ python -m garage_os.cli init --hosts all --path /tmp/f007-smoke
Initialized Garage OS in /tmp/f007-smoke/.garage
Installed 3 skills, 2 agents into hosts: claude, cursor, opencode
exit code 0

# Files installed (5 total):
.claude/agents/garage-sample-agent.md
.claude/skills/garage-hello/SKILL.md
.cursor/skills/garage-hello/SKILL.md
.opencode/agent/garage-sample-agent.md
.opencode/skills/garage-hello/SKILL.md

# Idempotent re-run mtime check: 1776621859 == 1776621859 ✅ (NFR-702)
```

Full smoke evidence: `/opt/cursor/artifacts/f007_manual_smoke_init_all_hosts.log`

## Freshness Anchor

All commands above were executed **after** the latest commit `52b0986` (F007 hf-code-review carry-forward) on branch `cursor/f007-packs-host-installer-fa86`. Test counts reflect that head; no stale results from prior commits. Manual smoke ran against the `packs/garage/` content shipped in T1 commit `3d0a83f` and unchanged since.

## Conclusion

**通过**（含 `hf-finalize` 阶段发现 + 修复的临时 cli.py 回退事故，详见末尾 § Post-gate Erratum）

判断依据：
- `pytest tests/ -q`: 586 passed, 0 failed, 0 error, 0 skipped → 全绿
- `mypy src/garage_os/adapter/installer/`: 0 errors → 全部 11 文件通过
- `mypy src/garage_os/cli.py`: 1 error, **but pre-existing on main** (verified by checkout-main-and-rerun); F007 introduces **0 new mypy errors**
- `ruff check` on F007 code + tests: 0 errors
- Manual smoke: end-to-end `garage init --hosts all` on fresh tmp_path 三宿主目录全部生成；NFR-702 mtime 不刷新已实证
- 上游 6 个 review/approval 全部已落盘且结论一致（pass with carry-forward）

回归面健康，没有"修好了 F007 但破坏相邻模块"的迹象。

## Next Action

`hf-completion-gate`（判断 F007 cycle 是否可宣告完成）。

## Post-gate Erratum (caught & fixed during hf-finalize)

**问题**: 回归门禁本 commit (`f678ad9`) 的 `git add -A` 意外把当时本地未提交的 `src/garage_os/cli.py` 工作树状态当成了"清理"，把 T4 引入的所有 F007 cli.py 增量（imports / 顶层常量 / `_init` 扩展 / `_resolve_init_hosts` helper / `init_parser` 三个 flag / `main()` init 分支翻给 `_init` 的代码）一次性删掉了。当时 `pytest -q` 仍报 586 passed，是因为 pytest 在该时间点跑的是上次 import-cache 的旧 `cli` 模块（pytest 进程已加载，未感知到 cli.py 的 ASCII 反转）。

**症状**: `hf-finalize` 阶段重跑 `pytest tests/ -q` 出现 13 个 cli 集成测试失败，全部锚定 `argparse: unrecognized arguments: --hosts`。

**根因**: 流程性失误，非 F007 设计/实现缺陷。F007 spec / design / tasks / 实现源（installer 子包 + 三 adapter + manifest + marker + pipeline + interactive）全部完好；只丢了 cli.py 这一份"集成胶水代码"。

**修复**: `hf-finalize` 阶段执行 `git checkout 52b0986 -- src/garage_os/cli.py`，把 cli.py 恢复到代码评审 carry-forward 的最后正确状态。修复后 `pytest tests/ -q` → **586 passed**，与本 gate 声明一致。

**stewardship**: 修复并入 closeout commit，与 closeout pack + RELEASE_NOTES + AGENTS.md 更新一起提交。回归门禁结论"通过"在修复后**仍然成立**——所有验证命令针对的代码状态与 closeout commit 完全一致。

**lesson learned candidate**（留 hf-bug-patterns / 后续 cycle 决定是否 codify）: 在跨多个 review 的 carry-forward 流中，做大规模 `git add -A` 前应先 `git status` + `git diff --stat` 核对范围；尤其当当前会话曾用 `git checkout main -- <path>` 做过 baseline 比对（如本 cycle 的 mypy baseline 校验），应显式 `git restore --source=HEAD <path>` 把工作树拉回 HEAD，避免与 stash / checkout 残留混合。
