# Approval Record - F008 Tasks

- Artifact: `docs/tasks/2026-04-22-garage-coding-pack-and-writing-pack-tasks.md`
- Approval Type: `tasksApproval`
- Approver: cursor cloud agent (auto-mode policy approver)
- Date: 2026-04-22
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`（工作分支 `cursor/f008-coding-pack-and-writing-pack-bf33`；PR #22）

## Evidence

- **Round 1 review**: `docs/reviews/tasks-review-F008-coding-pack-and-writing-pack.md`（R1 段）— `需修改`
  - 0 critical / 1 critical-conflict + 2 important + 6 minor LLM-FIXABLE/部分 USER-INPUT
  - F-1 [critical][TR2+TR5] T2/T3 INV-9 vs 上游 SKILL.md 字面值 vs CON-803 vs test_neutrality.py 三方冲突
  - F-2 [important][TR2][T2] Files 描述与上游 layout 不符 + family-level prompts/ 处置缺位
  - F-3 [important][TR3+TR4][T1c] fail-first 顺序在单 task 内未拆步
  - F-4 [minor][TR4] §6 vs §8 串/并行措辞冲突
  - F-5 [minor][TR2][T1a] Verify 自相矛盾
  - F-6 [minor][TR2][T4b] AGENTS.md grep 验收过弱
  - F-7 [minor][TR3][T5] RELEASE_NOTES 占位段缺 enum
  - F-8 [minor][TR3] NFR-803 wall-clock 验收锚点缺 manual smoke 口径
  - F-9 [minor][TR2][T1c] sentinel 不依赖 .garage/ 临时目录未注明
  - 缺失项 1：NFR-801 / INV-9 pre-flight sanity check
  - 缺失项 2：pyproject.toml/uv.lock 零变更守门未入完成定义
  - 缺失项 3：T4a dogfood 残留场景下 git status 干净的硬门槛步骤
- **Round 1 follow-up commit**: `e8f1a35` "f008(tasks): r1 tasks-review 通过定向回修 (1 critical + 2 important + 6 minor)"
  - F-1 闭合：父会话选 **修复路径 (b) CON-803 例外 + search-and-replace**：spec CON-803 加例外条款 #2 + enum 2 处违反；spec NFR-801 加量化验收；T2/T3 加 search-and-replace sub-step + INV-9 验证
  - F-2 闭合：T2 Files 改写 + 上游 layout 实测基线 + family-level prompts/横纵分析法.md 搬到 packs/writing/prompts/（顶层）
  - F-3 闭合：T1c 加 Sub-acceptance Step 1 (RED) / Step 2 (GREEN) / Step 3 (commit) + Files 段补 sentinel 不依赖 .garage/
  - F-4 闭合：§ 6 + § 8 改写为 "依赖图层面互不依赖, 调度按 P 升序串行 (router 不并发)"，关键路径从 7 跳改为 9 跳
  - F-5 闭合：T1a Verify 简化为 `ls | wc -l == 22`
  - F-6 闭合：T4b 替换 trivially pass grep 为 6 个结构性 invariant
  - F-7 闭合：T5 加 5 项占位字段清单（manual_smoke_wall_clock / pytest_total_count / installed_packs_from_manifest / commit_count_per_group / release_notes_quality_chain）+ TBD ≥ 5 守门
  - F-8 闭合：§ 7 加双轨验收（自动化 pytest --durations + manual time）
  - F-9 闭合：T1c Files 段显式说明 sentinel 不依赖 .garage/
  - 缺失项 1 闭合：§ 7 验证顺序加 "T2/T3 完成后立即跑 test_neutrality 守门"
  - 缺失项 2 闭合：§ 7 完成定义加 #6 `git diff main..HEAD -- pyproject.toml uv.lock` 输出空
  - 缺失项 3 闭合：T4a 加 4 步执行顺序硬门槛（先改 .gitignore → rm → 检查 dogfood 残留 → git status 干净 → commit）
- **Round 2 review** — `需修改`
  - 1 critical：CON-803 例外 enum 仅覆盖 2 处 SKILL.md，遗漏 cp -r 整子目录带入的 4 处非-SKILL.md 命中（humanizer-zh/README.md 3 + anthropic-best-practices.md 1 + CLAUDE_MD_TESTING.md 14 + write-blog/README.md）；CLAUDE_MD_TESTING.md 14 行超 ≤3 行硬上限
  - 2 minor：§ 8 line 472 残留旧措辞、T2 prompts/ INV-2 未澄清
- **Round 2 follow-up commit**: `bb6e38f` "f008(tasks): r2 tasks-review 通过定向回修 (1 critical 收敛 + 2 minor)"
  - r2 critical 闭合：父会话选 **ADR-D8-9 分类方案**（SKILL.md/agent.md 强约束 + meta/教学文件按豁免清单 enum）
    - spec NFR-801 验收分两层：(SKILL.md/agent.md grep = 0) + (meta 文件命中 ⊆ 豁免清单)
    - spec CON-803 详细说明加 4 个豁免文件 + 理由
    - design 加 ADR-D8-9（含 candidate 对比 + 豁免清单 + Consequences + Reversibility）
    - design § 13.1 加 test_neutrality_exemption_list.py 守门（4 → 5 个新增测试）
    - tasks T2/T3 INV-9 grep 范围限定到 SKILL.md+agent.md（与 ADR-D8-9 一致）
    - tasks T4c 加 test_neutrality_exemption_list 测试 + 基线 596 → 598
  - r2 minor 闭合：§ 8 串行规则二分明确；T2 prompts/ INV-2 enumerate 范围说明
- **Round 3 review** — `需修改`
  - 1 important + 3 minor：T2/T3 Verify 命令仍是 r1 递归 grep wording 残留；design § 11.1 INV-9 表 wording 残留；task 596 vs 598 三处不一致；EXEMPTION_LIST "5 文件" 措辞精度
- **Round 3 follow-up commit**: `a1d1735` "f008(tasks): r3 tasks-review 通过定向回修 (1 important + 3 minor 全部 LLM-FIXABLE)"
  - F-r3-1 闭合：T2/T3 Verify 改为 SKILL.md/agent.md 强约束 grep + meta 豁免守门两条
  - F-r3-2 闭合：design § 11.1 INV-9 行改写为 (a)+(b) 两层守门
  - F-r3-3 闭合：测试基线统一为 ≥ 598
  - F-r3-4 闭合：EXEMPTION_LIST 改为 "4 个固定 + 1 个条件性 packs/writing/README.md"
- **Round 4 review** — **`通过`**
  - 0 critical / 0 important / 0 minor
  - r3 全部 4 条 finding 闭合（4 closed / 0 open / 0 regressed）
  - spec / design / task 三层在 grep 范围 / 测试基线 / INV-9 分层守门 / fail-first 顺序 / EXEMPTION_LIST 完全一致
  - 数字精度残留 (4 vs 5) 不阻塞 dev
  - `needs_human_confirmation=true`（reviewer 指 task 真人确认环节由 auto-mode 父会话写 record）
  - `reroute_via_router=false`
- **Auto-mode policy basis**: `AGENTS.md` 未限制 coding cycle 内 tasks 子节点 auto resolve；本 cycle 由 router 路由为 `auto`，approval step 在 record 落盘后即可解锁下游 `hf-test-driven-dev`。

## Decision

**Approved**. Tasks 状态由 `草稿` → `已批准（auto-mode approval）`。下一步 = `hf-test-driven-dev`，从 T1a (`coding/skills`) 开始。

task plan 含 9 个 task（T1a/T1b/T1c + T2 + T3 + T4a/T4b/T4c + T5）+ 9 条 INV + 5 个新增测试文件 + 4 + 1 个豁免文件 enum + 5 项占位字段清单 + 4 步 dogfood 处理硬门槛。

`hf-test-driven-dev` 阶段需按 § 8 选择规则按 P 升序串行执行 9 个 task，每个 task 完成后 commit + 跑 Verify + 守 INV，9 个 task 全部完成后跑 manual smoke walkthrough。

## Hash & 锚点

- Tasks 初稿提交: `b7fdf86` "f008(tasks): r1 任务计划草稿，9 个 task 对应 design § 10.1 9 sub-commit"
- r1 回修提交: `e8f1a35` "f008(tasks): r1 tasks-review 通过定向回修 (1 critical + 2 important + 6 minor)"
- r2 回修提交: `bb6e38f` "f008(tasks): r2 tasks-review 通过定向回修 (1 critical 收敛 + 2 minor)"
- r3 回修提交: `a1d1735` "f008(tasks): r3 tasks-review 通过定向回修 (1 important + 3 minor 全部 LLM-FIXABLE)"
- approval 提交（含 tasks 状态字段 → 已批准）: 本 commit
- 关联 spec wording 同步修订（CON-803 + NFR-801 r2）: 在 commit `bb6e38f` 内一同落地
- 关联 design ADR-D8-9 新增: 在 commit `bb6e38f` 内一同落地

## 后续 (informational, 不阻塞 approval)

- T1a 是绝对起点，hf-test-driven-dev 阶段从此开始
- T2/T3 实施时必须先做 search-and-replace 再跑 INV-9 验证
- T1c 必须先 commit RED 状态的 sentinel test，再反向同步 → GREEN
- T4c 必须落 5 个测试文件（test_skill_anatomy_drift 在 T1c 已落，故 T4c 实际新增 4 个）
- T5 RELEASE_NOTES 是占位段（5 项 TBD），实测数据由 hf-finalize 阶段填
