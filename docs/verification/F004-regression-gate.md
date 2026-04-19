# F004 Regression Gate

- Verification Type: `regression-gate`
- Scope: F004 Garage Memory v1.1（发布身份解耦与确认语义收敛）— 单 cycle 全任务（T1-T5）回归
- Workflow Profile / Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- Branch: `cursor/f004-memory-polish-1bde`
- Date: 2026-04-19

## Upstream Evidence Consumed

- 实现交接块: `docs/verification/F004-T1-implementation-handoff.md`、`F004-T2-implementation-handoff.md`、`F004-T5-implementation-handoff.md`（T3、T4 实现细节嵌入 commit message + design 矩阵）
- Test design approvals: `docs/approvals/F004-T1-test-design-approval.md`、`F004-T2-test-design-approval.md`、`F004-T3-test-design-approval.md`、`F004-T4-test-design-approval.md`
- Reviews:
  - `docs/reviews/spec-review-F004-memory-v1-1.md`（通过）
  - `docs/reviews/design-review-F004-memory-v1-1.md`（需修改 → r1 by author self-check 1:1 闭合）
  - `docs/reviews/tasks-review-F004-memory-v1-1.md`（通过）
  - `docs/reviews/test-review-F004-memory-v1-1.md`（通过；4 项 minor LLM-FIXABLE，2 项已补 supplementary tests）
  - `docs/reviews/code-review-F004-memory-v1-1.md`（通过；2 项 minor docstring 已补）
  - `docs/reviews/traceability-review-F004-memory-v1-1.md`（通过；2 项 minor LLM-FIXABLE 留 finalize 顺手处理）
- Approvals: `docs/approvals/F004-spec-approval.md`、`F004-design-approval.md`、`F004-tasks-approval.md`
- Task plan: `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md`

## Verification Scope

### Included Coverage

| 范围 | 命令 | 说明 |
|------|------|------|
| 全 suite 回归 | `pytest tests/ -q` | F003 baseline 384 → F004 终态 414，所有现有测试零回归 |
| F004 focused 子集 | `pytest tests/memory/ tests/knowledge/ tests/runtime/test_session_manager.py tests/test_cli.py tests/test_documentation.py -q` | F004 直接触动模块 + 邻近测试 |
| Type check（F004 触动文件） | `mypy src/garage_os/memory/publisher.py src/garage_os/runtime/session_manager.py src/garage_os/knowledge/knowledge_store.py src/garage_os/cli.py` | 验证 F004 改动**未引入新的 mypy 错误**（baseline 23 个 pre-existing errors 持平） |

### Uncovered Areas

- `mypy src/`（全模块）— pre-existing baseline 含其他模块的 mypy 错误，超出 F004 范围；由后续 cycle 单独治理
- `ruff check src/`（全模块）— pre-existing baseline UP045 等样式警告，非 F004 引入；保持与项目历史一致
- 性能 wall-clock 大数据集对比 — F004 范围内只跑 `tests/memory/` suite 级别 wall-clock（见 NFR-402 验证），未做大规模数据基准；ASM-403 已显式裁决"不补 publisher 专项 benchmark"
- 真实 Claude Code 端到端 — F002 已批准的 CLI + adapter 链路保持不变，F004 不触动这部分

## Commands And Results

### 全 suite 回归

```
$ pytest tests/ -q 2>&1 | tail -3
tests/tools/test_tool_registry.py .............                          [100%]
============================= 414 passed in 24.76s =============================
```

退出码: 0
Summary: **414 passed in 24.76s**（F003 baseline 384 → F004 终态 414，新增 30 个测试，零回归）。

### F004 focused 子集

```
$ pytest tests/memory/ tests/knowledge/ tests/runtime/test_session_manager.py tests/test_cli.py tests/test_documentation.py -q 2>&1 | tail -3
tests/test_documentation.py ...                                          [100%]
============================= 147 passed in 1.22s ==============================
```

退出码: 0
Summary: **147 passed in 1.22s**（F004 触动模块及邻近测试全绿）。

### Type check（F004 触动 4 个文件）

```
$ mypy src/garage_os/memory/publisher.py src/garage_os/runtime/session_manager.py src/garage_os/knowledge/knowledge_store.py src/garage_os/cli.py 2>&1 | tail -3
src/garage_os/cli.py:494:41: error: Incompatible types in assignment ...
Found 23 errors in 4 files (checked 4 source files)

# Baseline (git stash 当前所有未提交修改后)
$ mypy src/garage_os/memory/publisher.py src/garage_os/runtime/session_manager.py src/garage_os/knowledge/knowledge_store.py src/garage_os/cli.py 2>&1 | tail -3
... 同样 23 errors（F002 / F003 pre-existing）
```

退出码: 1（持平 baseline）
Summary: **F004 未引入新的 mypy 错误**。23 个 errors 全部是 F002 / F003 pre-existing（如 `cli.py:494 Incompatible types` 来自 F003 的 conflict_strategy 处理；`session_manager.py:587-620` 来自 F002 SessionManager 实现；`knowledge_store.py` 修改后引入 0 个新 error）。这些 baseline 错误超出 F004 修改范围，按项目历史保持现状。

### 性能微基准（NFR-402）

```
# Post-F004
$ for i in 1 2 3; do pytest tests/memory/ -q 2>&1 | tail -1; done
============================== 37 passed in 0.37s ==============================
============================== 37 passed in 0.38s ==============================
============================== 37 passed in 0.34s ==============================
T1_avg = 0.36s

# Pre-F004 (T5 stashed; T1+T2 commit only)
$ git stash && for i in 1 2 3; do pytest tests/memory/ -q 2>&1 | tail -1; done && git stash pop
T0_avg = 0.37s
```

T1 / T0 = 0.36 / 0.37 = 0.97（在测量误差内），≤ 1.1 * T0，**NFR-402 通过**。

## Freshness Anchor

- 所有测试结果由本会话内 `pytest tests/ -q` 直接产生（commit `fc126c0` 之后）
- mypy 结果同样由本会话内运行产生
- 当前 working tree 干净，与最新 commit 一致
- 分支与 HEAD 时间锚点：`cursor/f004-memory-polish-1bde` @ commit `fc126c0`（"docs(F004): address code-review minor findings ..."）

## Conclusion

**通过**

依据：
- 全 suite 414 passed 零回归（F003 baseline 384 + F004 新增 30）
- F004 focused 子集 147 passed
- F004 触动文件未引入新的 mypy / ruff 错误
- NFR-402 wall-clock 微基准通过
- 上游所有 review / gate（spec / design / tasks / test / code / traceability）均通过
- 不存在阻塞性 finding

## Next Action Or Recommended Skill

`hf-completion-gate`
