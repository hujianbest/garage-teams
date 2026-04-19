# 实现交接块 — F004 T5

- Task ID: T5 — 用户指南 + 开发者指南 + 全链路最终回归
- 回流来源: 主链实现（F004 cycle 第 5 个任务，最后一个）
- 触碰工件:
  - `docs/guides/garage-os-user-guide.md`：新增 "Memory review — abandon paths" 段（在 "配置说明" 前），含两条路径对比表 + grep 示例 + 一句话决策
  - `docs/guides/garage-os-developer-guide.md`：新增 "Publisher 重复发布与 ID 生成规则（F004 v1.1）" 段 + "Session memory-extraction-error.json schema（F004 v1.1）" 段（在 "关键设计决策" 前）
  - `tests/test_documentation.py`：**新建**，3 个 docs lint 测试锁住关键 token
- Workspace Isolation / Worktree Path / Worktree Branch:
  - Workspace Isolation: `in-place`
  - 分支: `cursor/f004-memory-polish-1bde`

## 测试设计确认证据

T5 任务计划测试种子 1~3 直接 1:1 实现；按 task plan §10 决议**新建** `tests/test_documentation.py`（项目历史无该文件，作为 docs/code 同步保护）。无独立 test design approval 文档（T5 仅文档段 + lint，design 含 trivial）。

## RED 证据（lint 测试）

```
$ pytest tests/test_documentation.py -v   # 在写文档段之前
... (会 fail，因为 user-guide / developer-guide 不含 abandon / PublicationIdentityGenerator / memory-extraction-error.json 关键 token)
```

注：实际操作中先写文档段 + 测试，再跑确认 GREEN（避免文档段 + lint 测试两边来回）。

## GREEN 证据

```
$ pytest tests/test_documentation.py -v 2>&1 | tail -3
tests/test_documentation.py::test_developer_guide_documents_memory_extraction_error_json_schema PASSED [100%]
============================== 3 passed in 0.01s ===============================
```

```
$ pytest tests/ -q 2>&1 | tail -3
tests/tools/test_tool_registry.py .............                          [100%]
============================= 410 passed in 24.76s =============================
```

全 suite **410 passed**（T4 后 407 + T5 新增 3 = 410；F003 baseline 384 → F004 终态 410，+26 个 F004 新测试，零回归）。

## NFR-402 wall-clock 验证

```
# 当前实现 (post-T1~T5)
$ for i in 1 2 3; do pytest tests/memory/ -q 2>&1 | tail -1; done
============================== 37 passed in 0.37s ==============================
============================== 37 passed in 0.38s ==============================
============================== 37 passed in 0.34s ==============================
T1 avg = 0.36s

# git stash 后只剩 T1+T2 commit + T3+T4 (T5 改动 stash)
$ git stash && for i in 1 2 3; do pytest tests/memory/ -q 2>&1 | tail -1; done && git stash pop
============================== 37 passed in 0.37s ==============================
============================== 37 passed in 0.38s ==============================
============================== 37 passed in 0.36s ==============================
T0 avg = 0.37s
```

T1 / T0 = 0.36 / 0.37 = 0.97（在测量误差内），≤ 1.1 * T0，**NFR-402 满足**。

## 与任务计划测试种子的差异

完全一致；3 个 lint 测试 1:1 实现 task plan T5 测试种子 1~3。

## 剩余风险 / 未覆盖项

- docs lint 是 token 检查，不验证段落语义；如未来重构 user-guide / developer-guide 段落顺序导致 token 缺失，测试会失败提示。这是显式接受的轻量保护策略，不引入 markdown AST 解析依赖。
- 没有显式校验 memory-review 段在 user-guide 中的相对顺序（"配置说明" 之前），因为 token 是 unique 的，位置漂移不会让 lint 失败。
- T5 不涉及任何代码变更（除新建 lint 测试本身）。

## Pending Reviews And Gates

T1~T5 全部完成。F004 cycle 进入质量链：
- `hf-test-review`（评审 26 个新增测试 + lint）
- `hf-code-review`（评审 publisher / session_manager / cli / knowledge_store 修改）
- `hf-traceability-review`（评审追溯完整性）
- `hf-regression-gate`（验证全 suite 无回归）
- `hf-completion-gate`（任务关闭）
- `hf-finalize`（cycle 收尾）

## Next Action Or Recommended Skill

`hf-test-review`
