# F008 Regression Gate Verification Record

- Verification Type: `regression-gate`
- Cycle: F008 — Garage Coding Pack 与 Writing Pack
- Workflow Profile: `full`
- Execution Mode: `auto`
- Workspace Isolation: `in-place`
- Worktree Path: `/workspace`（无 worktree, 工作分支 `cursor/f008-coding-pack-and-writing-pack-bf33`）
- Branch: `cursor/f008-coding-pack-and-writing-pack-bf33`
- Date: 2026-04-23

## Upstream Evidence Consumed

- `docs/reviews/test-review-F008-coding-pack-and-writing-pack.md` — `通过` (4 minor LLM-FIXABLE 不阻塞)
- `docs/reviews/code-review-F008-coding-pack-and-writing-pack.md` — `通过` (5 minor LLM-FIXABLE 不阻塞)
- `docs/reviews/traceability-review-F008-coding-pack-and-writing-pack.md` — `通过` (5 minor LLM-FIXABLE，全部 carry-forward 不阻塞)
- `docs/approvals/F008-{spec,design,tasks}-approval.md` — 三层 approval 完整
- task-progress.md — Stage `hf-test-review` → 进入 regression-gate
- 9 sub-commit (T1a/T1b/T1c + T2 + T3 + T4a/T4b/T4c + T5 + 进度同步) impl handoff
- design § 11.1 9 INV (F008 INV-1..9)
- spec § 4.2 6 红线（design reviewer 可拒标准）
- spec NFR-802（测试基线零回归）+ NFR-803（≤ 5s wall-clock）+ CON-801（D7 管道零修改）

## Verification Scope

### Included Coverage

按 `full` profile 全集 + INV-1..9 + 6 红线全覆盖：

- 全套 pytest（`tests/` 整树，含 F007 baseline 586 + F008 增量 47 = 633 用例）
- INV-3 drift 收敛 sentinel 测试
- INV-9 layer (a) SKILL.md/agent.md 强约束 + layer (b) meta 文件 EXEMPTION_LIST
- INV-5 D7 src/garage_os/ 零修改 + 零依赖变更
- INV-6 git status 干净
- discover_packs 三 pack 实测 + 总 29 skill
- Manual smoke walkthrough 双轨实测（dogfood + /tmp/f008-smoke）

### Uncovered Areas

按 design § 17 排除 + spec § 5 deferred backlog 显式不覆盖：

- D7 安装管道扩展为递归 `references/` 子目录 — D9 候选
- `garage uninstall` / `garage update` — D9 候选
- `~/.claude/skills/` 全局安装 — 单独 cycle
- 新增宿主（Codex / Gemini CLI / Windsurf）— F008+ 增量
- `packs/product-insights/` — 待真实内容物
- INV-7 IDE 加载链可重放：由 manual smoke walkthrough 验证（自动化测试 test_dogfood_layout.py 检查 layout 但不实跑 garage init dogfood）

## Commands And Results

### 1. 全套 pytest (NFR-802 测试基线零回归)

```bash
.venv/bin/pytest tests/ -q
```

- Exit code: **0**
- Result: **633 passed in 26.21s**
- 对比 F007 baseline: 586 passed → +47 增量，0 退绿
- 增量分解：
  - +5 `tests/adapter/installer/test_full_packs_install.py`（INV-1 + INV-2 + FR-806 + INV-4 + NFR-803）
  - +4 `tests/adapter/installer/test_packs_garage_extended.py`（FR-803 + ADR-D8-5 + ADR-D8-6）
  - +6 `tests/adapter/installer/test_dogfood_layout.py`（FR-805 + INV-6 + INV-8 + 红线 4 + AGENTS.md 多个 invariant）
  - +3 `tests/adapter/installer/test_neutrality_exemption_list.py`（ADR-D8-9 双层）
  - +1 `tests/adapter/installer/test_skill_anatomy_drift.py`（INV-3 sentinel）
  - +28 既有 `tests/adapter/installer/test_neutrality.py` 自动 parametrize 拾取 packs/{coding,garage,writing}/skills/<id>/SKILL.md（22 + 4 + 2 = 28）

### 2. INV-5 + 零依赖（CON-801 + 红线 6 严守）

```bash
git diff main..HEAD -- src/garage_os/ pyproject.toml uv.lock | wc -l
```

- 输出: **0**
- D7 安装管道任何代码 0 修改 ✓
- 依赖未变 ✓

### 3. INV-3 drift 收敛（spec § 4.2 红线 3）

```bash
diff /workspace/docs/principles/skill-anatomy.md /workspace/packs/coding/principles/skill-anatomy.md
```

- Exit code: **0**（输出空）
- 根级与 packs/coding/principles/ 字节级相等 ✓

### 4. INV-9 layer (a) 强约束（NFR-801）

```bash
find packs/ \( -name 'SKILL.md' -o -path '*/agents/*.md' \) -exec grep -lE '\.claude/|\.cursor/|\.opencode/|claude-code' {} \; | wc -l
```

- 输出: **0**
- 全部 28 个 SKILL.md + 1 个 agent.md 在 packs/ 下宿主中性 ✓

### 5. INV-6 git status 干净（spec § 4.2 红线 2）

```bash
git status --short
```

- 输出（清理 dogfood 残留 + 补 .gitignore 后）：
  ```
   M .gitignore
  ?? docs/reviews/code-review-F008-coding-pack-and-writing-pack.md
  ?? docs/reviews/test-review-F008-coding-pack-and-writing-pack.md
  ?? docs/reviews/traceability-review-F008-coding-pack-and-writing-pack.md
  ```
- 解释：4 行均为 regression-gate 阶段产生的合法工件（review records + .gitignore 修订排除 .cursor/ + .claude/ 整目录 + .garage/config/host-installer.json，统一 dogfood 排除范围）。这些将在 regression-gate commit 内统一提交，提交后 git status 应为空。

### 6. discover_packs 三 pack 实测

```bash
python3 -c "from garage_os.adapter.installer.pack_discovery import discover_packs; ..."
```

输出：
```
discover_packs: [('coding', 22, 0, '0.1.0'), ('garage', 3, 1, '0.2.0'), ('writing', 4, 0, '0.1.0')]
total skills: 29
```

- INV-1 总 29 skill ✓
- 3 pack version: coding 0.1.0 / garage 0.2.0 / writing 0.1.0 ✓
- packs/garage/ agents = 1（ADR-D8-5 garage-sample-agent 保留）✓

### 7. Manual smoke walkthrough（INV-7 IDE 加载链）

参见 walkthrough artifacts:

- `/opt/cursor/artifacts/f008_dogfood_init.log` — Garage 仓库自身 dogfood: `Installed 58 skills, 1 agents into hosts: claude, cursor`
- `/opt/cursor/artifacts/f008_smoke_first.log` — `/tmp/f008-smoke/`: `Installed 87 skills, 2 agents into hosts: claude, cursor, opencode`，real 0m0.120s
- `/opt/cursor/artifacts/f008_smoke_second.log` — 二次幂等 0m0.107s
- `/opt/cursor/artifacts/f008_smoke_manifest_excerpt.json` — manifest schema_version=1 + 3 packs + content_hash
- `/opt/cursor/artifacts/f008_smoke_claude_tree.txt` — 29 skill 全部落到 .claude/skills/

NFR-803 wall-clock 实测：120ms（首次） + 107ms（幂等），远低于 5s 上限（40× margin）。

NFR-702 mtime stability 实测：二次运行 mtime = 1776952954（与首次相等），严格幂等 ✓。

## Freshness Anchor

- 当前会话内运行：所有 6 项命令在本 regression-gate verify 阶段当场执行
- 工作目录：`/workspace`（branch `cursor/f008-coding-pack-and-writing-pack-bf33` HEAD = 3002215 + 4 个本会话产生的工件）
- 测试结果时间戳：2026-04-23（本评审会话同日）
- Manual smoke artifacts：本 PR walkthrough 期间产生（同分支同会话）
- 没有使用任何历史/缓存结果

## Conclusion

- **conclusion**: `通过`
- **next_action_or_recommended_skill**: `hf-completion-gate`
- **needs_human_confirmation**: `false`
- **reroute_via_router**: `false`

### 通过依据

1. **测试基线零回归** ✓ — 633 passed (F007 586 + F008 47 增量), 0 退绿
2. **CON-801 严守** ✓ — `git diff main..HEAD -- src/garage_os/` = 空
3. **零依赖变更** ✓ — `git diff main..HEAD -- pyproject.toml uv.lock` = 空
4. **INV-3 drift 收敛** ✓ — sentinel 测试 + diff 命令双重验证
5. **INV-9 强约束** ✓ — SKILL.md/agent.md 黑名单 grep 0 命中
6. **INV-6 git status 干净** ✓（regression-gate commit 落地后）
7. **NFR-803 ≤ 5s** ✓ — 120ms / 107ms 实测
8. **NFR-702 严格幂等** ✓ — mtime stability 实测
9. **三 pack 一致性** ✓ — discover_packs 实测 N=29
10. **9 sub-commit 完整** ✓ — task plan 9 task 一一对应
11. **三 review 通过** ✓ — test/code/traceability review 均 verdict 通过

### 非阻塞 carry-forward 项（已在 traceability-review minor 段记录）

5 条 minor LLM-FIXABLE finding 全部从 hf-test-review / hf-code-review 透传到 traceability-review，建议 hf-finalize 阶段顺手清理或归档至 RELEASE_NOTES F008 段：

1. F5 packs/writing/LICENSE 缺自动化 assertion（物理文件存在 + git 受控兜底）
2. tests/test_cli.py:3042 carry-forward 修复混入 T1c commit（commit message 已声明）
3. T1c sentinel test fail-first RED 证据仅 commit message 文字层（可 git revert 重放）
4. NFR-803 fixture 用 symlink 不复制文件（manual smoke 兜底）
5. packs/coding/README.md 类目计数标题与表格行数轻漂移
6. task plan T4c EXEMPTION_LIST 数字精度 5 → 7 残留（traceability-review 新增）

均不影响 regression 通过判定。

### 关键 Profile 适用性

`full` profile 要求 traceability 识别的所有区域：本 cycle traceability-review 识别的全部 spec FR/NFR/CON + INV 1-9 + 6 红线均在上面 7 项命令覆盖范围内 ✓。

### Next Action

进入 `hf-completion-gate` — 判断本 cycle 是否可以宣告完成（含 finalize 准备度检查）。
