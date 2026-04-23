# Traceability Review — F008 Garage Coding Pack 与 Writing Pack

- 状态: r1 通过
- 日期: 2026-04-23
- Reviewer: hf-traceability-review subagent (独立 reviewer)
- Cycle: F008
- 关联规格: `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准 r2）
- 关联设计: `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（已批准 r2）
- 关联任务计划: `docs/tasks/2026-04-22-garage-coding-pack-and-writing-pack-tasks.md`（已批准 r4）
- 关联前置评审: spec-review r2 通过 / design-review r2 通过 / tasks-review r4 通过 / test-review r1 通过 / code-review r1 通过
- 评审 skill: `packs/coding/skills/hf-traceability-review/`（rubric: TZ1-TZ6 + ZA1-ZA4）

## Precheck

- 稳定上游工件 ✓ — spec/design/tasks 三份 r4 状态稳定批准；3 份 approval record 完整
- 实现交接块 ✓ — 9 个 sub-commit 全部落地（`git log main..HEAD --oneline` 清晰对应 T1a/T1b/T1c/T2/T3/T4a/T4b/T4c/T5）
- 上游 review 通过 ✓ — hf-test-review r1 通过 + 4 minor LLM-FIXABLE / hf-code-review r1 通过 + 5 minor LLM-FIXABLE，全部不阻塞
- route/stage/profile 一致 ✓ — `Workflow Profile=full`、`Execution Mode=auto`、stage 已稳定推进到 `hf-traceability-review`
- 测试基线确认 ✓ — `python3 -m pytest tests/adapter/installer/ -q` 实测 **120 passed in 0.23s**；test-review precheck 时全 suite 实测 633 passed
- INV-5 / 红线 6 实测 ✓ — `git diff main..HEAD -- src/garage_os/ pyproject.toml uv.lock | wc -l` = **0**
- INV-3 / 红线 3 实测 ✓ — `diff /workspace/docs/principles/skill-anatomy.md /workspace/packs/coding/principles/skill-anatomy.md` exit 0
- INV-9 layer (a) 实测 ✓ — `find packs/ \( -name 'SKILL.md' -o -path '*/agents/*.md' \) -exec grep -lE '\.claude/|\.cursor/|\.opencode/|claude-code' {} \; | wc -l` = **0**
- INV-9 layer (b) 实测 ✓ — `pytest tests/adapter/installer/test_neutrality_exemption_list.py -v` 3 passed（含 strict / exemption / sanity 三层）
- 三 pack.json 实测 ✓ — coding skills=22 agents=0 v0.1.0；writing skills=4 agents=0 v0.1.0；garage skills=3 agents=1 v0.2.0；总 N=29 / M=1
- Manual smoke 已归档 ✓ — `/opt/cursor/artifacts/` 含 5 个 artifact (dogfood + /tmp 双轨)

precheck PASS，进入正式 6 维评审。

## 链接矩阵（spec → design → tasks → impl → test）

### FR / NFR / CON 全集追溯（spec → impl）

| spec ID | design 锚点 | tasks 锚点 | impl commit | test / 验证 |
|---|---|---|---|---|
| FR-801 packs/coding/ 22 skill | ADR-D8-1 + § 10.1 T1a/T1b | T1a + T1b | `4f92b05` (T1a) + `1a86212` (T1b) | `test_full_packs_install::test_three_packs_total_29_skills` + `test_skill_byte_level_sample_INV4` |
| FR-802 packs/writing/ 4 skill + LICENSE | § 10.1 T2 | T2 | `f0f2c05` (T2) | `test_full_packs_install` writing 计数；**LICENSE 缺自动化**（test-review TT3 minor，本 review 同意但不阻塞） |
| FR-803 packs/garage/ 3 skill + version bump | ADR-D8-5 + ADR-D8-6 + § 10.1 T3 | T3 | `b81664a` (T3) | `test_packs_garage_extended.py` 4 用例（含 version=0.2.0 + skills=3 + writing-skills 子目录完整性） |
| FR-804 family-level 资产可解析（packs 源端 + 下游文档级提示） | ADR-D8-1 + ADR-D8-4 + § 10.1 T1b | T1b | `1a86212` (T1b) | `test_full_packs_install::test_family_asset_uniqueness` (INV-2) + 11 项 family asset 单点 |
| FR-805 .agents/skills/ 处置 + git status 干净 | ADR-D8-2 + § 10.1 T4a/T4b | T4a + T4b | `5a95b45` (T4a) + `907bbfb` (T4b) | `test_dogfood_layout::test_agents_skills_removed` + `test_gitignore_excludes_dogfood` |
| FR-806 端到端 smoke + walkthrough | ADR-D8-8 + § 10.3 + § 13.3 | T4c + walkthrough | `57a1efd` (T4c) + manual smoke artifacts | `test_full_packs_install::test_install_packs_three_hosts` + 5 个 `/opt/cursor/artifacts/` smoke artifact |
| FR-807 文档同步 | ADR-D8-7 + § 10.1 T5 | T5 | `6aa7587` (T5) | 人工 review（packs/README.md + user-guide + RELEASE_NOTES F008 占位段）+ `test_dogfood_layout::test_agents_md_*` 部分自动化 |
| NFR-801 宿主无关性（双层守门） | § 12 + ADR-D8-1 + ADR-D8-9 | T1a/T1b/T2/T3/T4c | T1a + T2 (search-and-replace) + T3 (search-and-replace) + T4c (sentinel) | `test_neutrality.py` (29 个 SKILL.md parametrize) + `test_neutrality_exemption_list.py` 3 用例 |
| NFR-802 测试基线 ≥ 633 | § 12 + § 13.1 | 全 PR | 全 PR | `pytest tests/ -q` → 633 passed (test-review precheck 已实测) |
| NFR-803 ≤ 5s | § 12 | T4c + walkthrough | T4c (auto-fixture) + manual smoke | `test_full_packs_install::test_install_packs_under_5_seconds_NFR803` (< 100ms) + `f008_smoke_first.log` (manual) |
| NFR-804 git diff 可审计 | § 10.1 9 sub-commit | 全 PR | 9 个 commit hash 完整对应（见 code-review 表） | `git log main..HEAD --oneline` 自然成立 |
| CON-801 不动 D7 管道 | § 12 + INV-5 | 全 PR | INV-5 守门 | `git diff main..HEAD -- src/garage_os/ \| wc -l` = 0 ✓ |
| CON-802 复用 pack.json schema | § 12 | T1b/T2/T3 | 三 pack.json 6 字段 | discover_packs 解析全过 |
| CON-803 字节级 1:1 + 例外 enum | § 12 + INV-4 + ADR-D8-9 | T1a/T2/T3 | T1a/T2/T3 commit + spec line 410-413 enum 2 处替换 | `test_skill_byte_level_sample_INV4` + 2 处 SKILL.md 替换均 ≤ 3 行 (code-review 实测) |
| CON-804 .agents/skills/ 处置收敛 | ADR-D8-2 + INV-6 | T4a | `5a95b45` (T4a) | `test_dogfood_layout::test_agents_skills_removed` |

### § 4.2 6 条 Design Reviewer 可拒红线追溯

| 红线 | spec 起源 | design ADR | impl commit | test/验证 |
|---|---|---|---|---|
| 红线 1 family asset 去重不变量 | spec § 4.2 #1 + FR-804 验收 #5 | ADR-D8-1 候选 A 选定 | `1a86212` (T1b) | `test_full_packs_install::test_family_asset_uniqueness` + INV-2 |
| 红线 2 .agents/skills/ 处置后 git status 干净 | spec § 4.2 #2 + FR-805 验收 #4 | ADR-D8-2 候选 C 选定 | `5a95b45` (T4a) | `test_dogfood_layout::test_agents_skills_removed` + `test_gitignore_excludes_dogfood` + INV-6 |
| 红线 3 drift 收敛 | spec § 4.2 #3 + FR-804 验收 #6 | ADR-D8-3 反向同步选定（HF 副本权威源） | `fa3d3fc` (T1c) | `test_skill_anatomy_drift::test_root_and_packs_principles_byte_equal` + INV-3 |
| 红线 4 AGENTS.md 5 分钟冷读链 | spec § 4.2 #4 + FR-807 验收 #1 | ADR-D8-3 + ADR-D8-7 局部刷新 | `907bbfb` (T4b) | `test_dogfood_layout::test_agents_md_skill_anatomy_path` |
| 红线 5 本仓库自身 IDE 加载链 | spec § 4.2 #5 + FR-805 验收 #2 | ADR-D8-2 候选 C dogfood + INV-7 | `5a95b45` + `907bbfb` (T4a/T4b) + manual smoke | `f008_dogfood_init.log` + `f008_smoke_claude_tree.txt` |
| 红线 6 F007 管道不动 | spec § 4.2 #6 + CON-801 | § 12 INV-5 + ADR-D8-4 文档级提示路径选 | INV-5 守门 | `git diff main..HEAD -- src/garage_os/ \| wc -l` = 0 |

### 9 INV 责任 commit 完整性追溯（design § 11.1 → impl）

| INV | 责任 commit (design § 11.1 declared) | impl commit hash | 实测验证状态 |
|---|---|---|---|
| INV-1 三 pack.json 总 skills[] = 29 | T4c | `57a1efd` | 实测 22+4+3=29 ✓ |
| INV-2 family asset 单点 | T1b | `1a86212` | code-review 抽样实测 ≤1 ✓ |
| INV-3 drift 收敛 | T1c | `fa3d3fc` | 实测 diff exit 0 ✓ |
| INV-4 字节级 1:1 搬迁 | T1a/T2/T3 | `4f92b05` + `f0f2c05` + `b81664a` | `test_skill_byte_level_sample_INV4` GREEN ✓ |
| INV-5 D7 src/garage_os 零修改 | 全 PR | 全 PR | 实测 `git diff` = 0 ✓ |
| INV-6 git status 干净 | T4a | `5a95b45` | `test_dogfood_layout` GREEN ✓ |
| INV-7 IDE 加载链可重放 | walkthrough（基于 T4a 落地后 dogfood） | manual smoke | 5 个 artifact 归档 ✓ |
| INV-8 .gitignore 排除 dogfood 产物 | T4a | `5a95b45` | `test_gitignore_excludes_dogfood` GREEN ✓ |
| INV-9 NFR-801 分层守门（双层） | T1a/T1b/T2/T3/T4c | 全部 + `57a1efd` (sentinel) | 双层 GREEN ✓ |

### 5 个新增测试文件覆盖映射（design § 13.1 → impl）

| 测试文件 | design § 13.1 declared | impl 落地 commit | 实测 |
|---|---|---|---|
| `test_skill_anatomy_drift.py` | T1c | `fa3d3fc` | 1 passed ✓ |
| `test_full_packs_install.py` | T4c | `57a1efd` | 全 GREEN（test-review 实测 633 全过中含此文件全部用例） |
| `test_packs_garage_extended.py` | T4c | `57a1efd` | 4 passed ✓ |
| `test_dogfood_layout.py` | T4c | `57a1efd` | 全 GREEN |
| `test_neutrality_exemption_list.py` | T4c (ADR-D8-9 r2 追加) | `57a1efd` | 3 passed ✓ |

## 跨阶段反向修订追溯（F008 cycle 特殊点）

### 修订 1：design ADR-D8-4 触发的 spec wording 反向同步（D7 工程边界对齐）

**事实链**:
- design-review r1 finding F-1 [important][USER-INPUT][D1] 识别 spec FR-804 验收 #1 / § 2.2 验收 #2 字面"装到 .claude/skills/ 后必须 resolve"与 D7 实际管道（只复制 SKILL.md 单文件）冲突
- 父会话评估后选择 reviewer 提供二选一中的"等价 LLM-FIXABLE 路径 (a)"，把 spec 字面口径分两层（packs 源端 + 下游宿主端）下调至与 D7 实际能力一致
- 修订 commit `994883e` 同时修改 spec FR-804 / § 2.2 / § 3.2 + design ADR-D8-4
- design-review r2 reviewer 独立评估，5 维评估全过（无新业务事实、spec/design wording 已一致、无 drift、不破坏已批准 spec 核心范围、design 整份签字时自然吸收），**收回 r1 USER-INPUT 标记**
- design-approval evidence 段显式记录这条反向修订路径与 USER-INPUT → LLM-FIXABLE 收回理由

**追溯结论**: 反向修订完整闭合 — spec 字面、design ADR、approval record、impl wording 四方一致。无残留 spec drift。

### 修订 2：tasks-review r2 critical 触发的 ADR-D8-9 升级（NFR-801 分类策略）

**事实链**:
- tasks-review r1 critical F-1 [TR2+TR5] 发现 T2/T3 INV-9 vs 上游 SKILL.md 字面值 vs CON-803 vs test_neutrality.py 三方冲突
- r1 父会话选 "修复路径 (b) CON-803 例外 + search-and-replace"
- tasks-review r2 进一步发现 cp -r 整子目录会带入 4 处非-SKILL.md 命中（含 CLAUDE_MD_TESTING.md 14 行超 ≤3 上限）
- r2 父会话选 ADR-D8-9 分类方案：spec NFR-801 分两层 + spec CON-803 加 4 个豁免 + design 加 ADR-D8-9 + tests 加 test_neutrality_exemption_list.py + tasks T2/T3 INV-9 grep 范围限定到 SKILL.md+agent.md
- tasks-review r3-r4 进一步收敛 wording 一致性（grep 范围 / 测试基线 / EXEMPTION_LIST 数字精度）
- T4c 实施时（commit `57a1efd`）EXEMPTION_LIST 又扩展 3 项（packs/README + packs/garage/README + packs/coding/README），并在 design ADR-D8-9 表 + spec NFR-801 详细说明同步扩到 7 项

**EXEMPTION_LIST 三层同步实测**（code-review 已验证）:
- spec § CON-803 详细说明: **7** 项 enum（spec line 415-425）
- design ADR-D8-9 表: **7** 项 enum（design line 343-353）
- `tests/adapter/installer/test_neutrality_exemption_list.py` `EXEMPTION_LIST: frozenset[str]` 常量: **7** 项

三层完全同步，本 review 独立交叉核验确认 ✓。

**追溯结论**: 完整闭合，三层同步守门到位。"未来 packs/<new-pack>/README.md 触发 RED → 强制 amend 三层" 机制由 spec § CON-803 line 425（"任何后续发现的同类豁免必须先 amend 本清单 + design ADR-D8-9 + tests/adapter/installer/test_neutrality_exemption_list.py 的 EXEMPTION_LIST 常量"）显式约束 + sentinel test 自动守门。

### 修订 3：CON-803 例外 #2 enum 实施期间扩展（spec line 410-413）

**事实链**:
- spec CON-803 例外 #2 详细说明（line 410-413）显式 enum 2 处需要 search-and-replace 的 SKILL.md：
  - `packs/writing/skills/hv-analysis/SKILL.md` line 55
  - `packs/garage/skills/writing-skills/SKILL.md` line 12（spec 中描述为"writing-skills/SKILL.md line 12"）
- code-review 实测两处替换均 ≤ 1 行 diff（CON-803 量化 ≤ 3 行守门通过）
- spec / design / tasks / impl 四层 wording 一致

**追溯结论**: 完整闭合，spec enum 与 impl 完全对应。

## 占位字段追溯（finalize 阶段填）

**事实链**:
- task plan T5 acceptance 显式 enum 5 项占位字段（line 396-400）：`manual_smoke_wall_clock` / `pytest_total_count` / `installed_packs_from_manifest` / `commit_count_per_group` / `release_notes_quality_chain`
- T5 acceptance 加 "TBD ≥ 5 守门"（grep 命中 ≥ 5；finalize 后该 grep 应 = 0）
- design § 18 #2 显式说明"实施期间放占位段、finalize 时填实测数据"协调成本
- tasks-approval 后续 informational 段重申 "T5 RELEASE_NOTES 是占位段（5 项 TBD），实测数据由 hf-finalize 阶段填"
- impl commit `6aa7587` (T5) 落地 RELEASE_NOTES F008 段，实测 `grep -nE "TBD" RELEASE_NOTES.md` 在 F008 段含 4 行 TBD（line 51/55/56/57）；外加 line 59 段尾"占位字段 5 项"声明 — 总 5 项占位明确

**追溯结论**: 完整闭合，占位字段在 spec/design/tasks/impl 四方都有锚点；finalize 阶段承接路径清晰。

## 多维评分

按 `references/review-checklist.md` 6 维 0-10 评分：

| 维度 | 得分 | 评语 |
|---|---|---|
| **TZ1 规格 → 设计追溯** | 9/10 | spec 7 FR + 4 NFR + 4 CON + 4 ASM + § 4.2 6 红线全部在 design 9 ADR 双向闭合：FR-801/802/803 → ADR-D8-1 + ADR-D8-5 + ADR-D8-6；FR-804 → ADR-D8-1 + ADR-D8-4（双向口径同步）；FR-805 → ADR-D8-2；FR-806 → ADR-D8-8；FR-807 → ADR-D8-7；NFR-801 → ADR-D8-9（r2 critical 升级新增）；CON-801..804 → § 12 + INV-5/4/6 + ADR-D8-2。9 ADR 每条都能反向追溯到 spec 锚点，特别 ADR-D8-9 是 spec NFR-801 双层守门设计的实施承接，三方完全 enum 同步。spec drift 可控（修订 1 双向同步，修订 2 三层 enum 同步）|
| **TZ2 设计 → 任务追溯** | 9/10 | design § 10.1 9 sub-commit + § 11.1 9 INV + § 13.1 5 测试文件全部在 task plan 9 task 中有承接：T1a 对应 § 10.1 T1a + INV-9 layer (a)；T1b 对应 § 10.1 T1b + INV-2；T1c 对应 § 10.1 T1c + INV-3 + sentinel test；T2/T3 对应 § 10.1 T2/T3 + ADR-D8-9 search-and-replace；T4a/T4b/T4c 对应 § 10.1 T4a/T4b/T4c + INV-1/6/7/8 + 4 个测试文件；T5 对应 § 10.1 T5 + 占位字段 enum。task plan § 4 追溯表 (line 82-104) 把每条 spec ID + design 锚点 + task + 验证用例完整建立四元映射，是本 cycle 最强的追溯证据 |
| **TZ3 任务 → 实现追溯** | 9/10 | 9 个 sub-commit 与 9 个 task 一一对应（code-review 已验证 commit hash 表完整）：T1a→`4f92b05` / T1b→`1a86212` / T1c→`fa3d3fc` / T2→`f0f2c05` / T3→`b81664a` / T4a→`5a95b45` / T4b→`907bbfb` / T4c→`57a1efd` / T5→`6aa7587`。每个 commit message 都含 `f008(<scope>)` 前缀 + 详尽 acceptance 命令 + SHA-256 hash + 增量数。Files 段全部对应 task plan § 5 declared。**carry-forward `tests/test_cli.py:3042` 修复混入 T1c commit** 是已知 minor（test-review TT5 + code-review CR6 同源），commit message 已声明"顺手修"可追溯，本 review 同意不阻塞 |
| **TZ4 实现 → 验证追溯** | 9/10 | 5 个新增测试文件全部 GREEN（实测 120 passed）+ 633 测试 baseline 0 退绿 + INV-1..9 全部有自动化或 walkthrough 守门（INV-5 由 git diff、INV-7 由 manual smoke walkthrough 承接，design § 11.1 已显式标注合规）+ § 4.2 6 红线全部有自动化 / walkthrough 实测（红线 1/2/3/4 自动化、红线 5 manual smoke + dogfood、红线 6 git diff）+ 5 个 manual smoke artifact 归档完整覆盖 INV-7 + FR-806 三家宿主全装。**F5 LICENSE 缺自动化 assertion** 是已知 minor (test-review TT3 + code-review CR6)，物理文件存在 + git 受控兜底，不阻塞 |
| **TZ5 漂移与回写义务** | 8/10 | 三类反向修订（D7 边界对齐 / ADR-D8-9 升级 / CON-803 enum 扩展）全部在 spec/design/tasks/impl 四方同步落地，所有 approval record 完整记录 USER-INPUT → LLM-FIXABLE 收回理由 + 实施期 enum 扩展归因（T4c 把 EXEMPTION_LIST 从 4 → 7 项是"r2 reviewer 罗列原 4 项时漏掉的同类项，不属于实施阶段单方面新增"，design line 355 显式 ack）。**残留 anchor drift**: tasks T4c acceptance line 366 仍写"4 个固定豁免文件 + 1 个条件性 packs/writing/README.md"（共 5 项），与 spec/design/test 三层最终落地的 7 项有数字精度差。tasks-review r3 已识别"数字精度残留 (4 vs 5) 不阻塞 dev"，但 T4c 实施期间从 5 → 7 后未回写 tasks 文档；属于 LLM-FIXABLE minor，不阻塞 traceability，但应 carry-forward 同步 |
| **TZ6 整体链路闭合** | 9/10 | spec/design/tasks/impl/test/approval 六方完整闭合：3 份 approval record 详尽记录每轮 finding closure；review record 链路完整（spec r1+r2 / design r1+r2 / tasks r1+r2+r3+r4 / test r1 / code r1）；633 测试 0 退绿；INV-5 src/garage_os 零修改实测 0；零依赖变更实测 0。当前批准工件与代码状态完全一致，可安全进入 hf-regression-gate。少量 minor LLM-FIXABLE finding（test-review 4 + code-review 5 + 本 review 1，去重后约 9 条）全部不阻塞，建议在 hf-completion-gate 集中收敛分类（cycle 内补 vs carry-forward） |

总均分：**53/60 = 8.83/10**

无关键维度 < 6，无阻塞性 finding。

## 发现项

按 severity 排列（评 1 项 minor LLM-FIXABLE 不阻塞 + 复述 5 条上游已识别但与追溯相关的 minor）：

### critical / important

无。

### minor (本 review 新增)

- [minor][LLM-FIXABLE][TZ5/ZA1] **task plan T4c acceptance EXEMPTION_LIST 数字精度残留**：tasks 文档 line 366 写"4 个固定豁免文件 + 1 个条件性 `packs/writing/README.md`"（共 5 项），与 spec § CON-803 详细说明（7 项）+ design ADR-D8-9 表（7 项）+ `test_neutrality_exemption_list.py` `EXEMPTION_LIST` 常量（7 项）三层最终状态不一致。tasks-review r3 已识别此残留为"数字精度残留 (4 vs 5) 不阻塞 dev"，但 T4c 实施期间 EXEMPTION_LIST 从 5 → 7 项扩展后（design line 355 显式 ack 是 "r2 reviewer 罗列原 4 项时漏掉的同类项"）未回写 tasks 文档。当前不构成 spec/design/test 三层 drift（三方仍是 7），但 tasks 文档作为 spec→design→tasks→impl 链路的中间环节，与最终状态有微小 anchor 漂移。建议作为 carry-forward 在 hf-finalize 阶段把 tasks T4c acceptance 的"4 + 1"刷新为"7"（4 skill 内 meta + 3 pack-level README），保持四层完全一致。当前可读追溯链未断（reviewer 顺 spec → design → test 三层都能定位到 7 项 enum），不阻塞 hf-regression-gate。

### minor (上游已识别，本 review 同意，与追溯相关的复述)

- [minor][LLM-FIXABLE][TZ4/ZA4] **F5 失败模式 (packs/writing/LICENSE 存在) 缺自动化 assertion** — 与 test-review TT3 / code-review 同源；spec FR-802 验收 #2 + design § 14 F5 + tasks T2 acceptance 全部要求 LICENSE 存在，但无 pytest 用例守门。LICENSE 物理存在 (`f0f2c05` 已落)，git 受控兜底。追溯链 spec → design → tasks 完整，仅 impl → test 一环弱化。建议作为 cycle 内补 (在 `test_full_packs_install.py` 加 `test_writing_license_preserved`) 或下个 cycle carry-forward
- [minor][LLM-FIXABLE][TZ3/ZA3] **carry-forward `tests/test_cli.py:3042` 混入 T1c commit** — 与 test-review TT5 / code-review CR6 同源；NFR-804 "任意一组改动可独立 review"轻微偏离，commit message 已声明可追溯。追溯链未断 (commit message 显式 anchor)，但下次类似改动建议单独 commit
- [minor][LLM-FIXABLE][TZ4] **T1c sentinel test fail-first RED 证据弱** — 与 test-review TT1 / code-review 同源；commit message 含 sha256 文字证据但缺独立 PR walkthrough artifact。可重放 (git revert fa3d3fc 即可重现 RED) 但 review 视角"fresh 当次会话 fail-first 证据"严格说仅文字层。追溯链未断
- [minor][LLM-FIXABLE][TZ5] **`packs/coding/README.md` 类目计数标题与表格行数轻漂移** — 与 code-review CR4 同源；Authoring（4）实际 5 / Review（6）实际 8（注释已 ack）。不影响 22 总数（1+5+8+2+4+2=22）；属 cosmetic 文档精度，不影响追溯

## 追溯缺口

无核心追溯断链。1 个本 review 新增 minor（tasks T4c EXEMPTION_LIST 数字精度残留）+ 4 条上游 minor 复述均可定向补齐或 carry-forward 处理。

**spec/design/tasks/impl/test 五元组 anchor 完整性核验**：
- 7 FR + 4 NFR + 4 CON + 4 ASM + 6 红线全部追溯链端到端
- 9 ADR 每条都能反向追溯到 spec 锚点
- 9 INV 每条都有责任 commit + 自动化 / walkthrough 守门
- 5 个新增测试文件覆盖完整（含 ADR-D8-9 r2 升级追加的 test_neutrality_exemption_list.py）
- 9 sub-commit 与 9 task 一一映射，commit message anchor 详尽
- 3 份 approval record 完整记录每轮 finding closure 与反向修订理由

## 需要回写或同步的工件

- 工件: `docs/tasks/2026-04-22-garage-coding-pack-and-writing-pack-tasks.md` line 366
  - 原因: T4c acceptance EXEMPTION_LIST 描述"4 + 1 = 5"与最终状态"7"不一致
  - 建议动作: 在 hf-finalize 阶段刷新为"7（4 skill 内 meta + 3 pack-level README）"，保持 spec / design / tasks / test 四层完全一致 — 当前不阻塞 hf-regression-gate

- 工件: `RELEASE_NOTES.md` F008 段 5 项 TBD 占位
  - 原因: design § 18 #2 + tasks T5 acceptance + tasks-approval 后续段已显式 declared finalize 阶段填充
  - 建议动作: 保持 finalize 阶段承接路径不变；当前 T5 commit `6aa7587` 已落占位段，符合预期

## 下一步

- **next_action_or_recommended_skill**: `hf-regression-gate`
- **needs_human_confirmation**: `false`（按 reviewer-return-contract.md：`hf-traceability-review` 在 `通过` 时默认 `false`，由父会话直接派发下一节点）
- **reroute_via_router**: `false`

父会话应直接派发独立 reviewer subagent 执行 `hf-regression-gate`，验证 NFR-802 测试基线 ≥ 633 + 0 退绿 + INV-5 src/garage_os/ 零修改 + INV-6 git status 干净。本 review 已确认追溯链完整性足够支持 regression gate 做可信判断。

## 记录位置

- review 记录: `/workspace/docs/reviews/traceability-review-F008-coding-pack-and-writing-pack.md`（本文件）

## 交接说明

### 给父会话

- 追溯链 r1 通过，无需回修
- 1 条新增 minor LLM-FIXABLE（tasks T4c EXEMPTION_LIST 数字精度残留 5 → 7）+ 4 条上游 minor 复述全部不阻塞 hf-regression-gate
- 累计 cycle 内 minor finding 约 9 条（test-review 4 + code-review 5 + traceability-review 1 [其中 4 条与上游同源去重]），建议 hf-completion-gate 集中决定哪些 cycle 内补 / 哪些 carry-forward

### 给 hf-regression-gate reviewer

regression gate 重点应放在：

1. **NFR-802 测试基线 ≥ 633 + 0 退绿**：在 clean checkout 上跑 `uv run pytest tests/ -q` 实测验证（test-review precheck 已实测 633 passed）
2. **INV-5 src/garage_os/ + pyproject.toml + uv.lock 三方零修改**：`git diff main..HEAD -- src/garage_os/ pyproject.toml uv.lock` 输出空（本 review 实测 = 0）
3. **INV-6 git status 干净**：在 clean checkout 上跑（注：当前 workspace 有 `.claude/` + `.garage/config/host-installer.json` untracked，是 dogfood smoke 产物，已被 .gitignore 排除是正确状态）
4. **120 个 installer 测试 + 633 全 suite 0 退绿**：本 review 实测 installer 120 passed in 0.23s
5. **零依赖变更守门**：spec § 8 + tasks § 7 完成定义 #6 已显式约束

### 给 hf-completion-gate reviewer

completion gate 应集中收敛累计 9 条 minor LLM-FIXABLE finding 的处置：

| 来源 | finding | 建议处置 |
|---|---|---|
| test-review TT3 / code-review / traceability TZ4 | F5 LICENSE 守门缺自动化 | cycle 内补（推荐）or carry-forward |
| test-review TT5 / code-review / traceability TZ3 | test_cli.py:3042 carry-forward 混 commit | carry-forward（commit message 已声明可追溯） |
| test-review TT1 / code-review / traceability TZ4 | T1c sentinel RED 证据弱 | carry-forward（下次 sentinel test 引入用两步 commit 模式） |
| test-review TT4 | NFR-803 fixture 用 symlink 不复制 | carry-forward（manual smoke 实测兜底） |
| code-review CR4 / traceability TZ5 | packs/coding/README.md 类目计数轻漂移 | cycle 内补（推荐，文档精度） |
| code-review CR4 | packs/garage/README.md version 行说明文字略冗长 | carry-forward |
| code-review CR6 | RELEASE_NOTES F008 测试增量分解口径不严谨 | hf-finalize 阶段重写 |
| code-review CR6 | review-record-template.md 7 副本设计意图未在 README 显式分层说明 | carry-forward |
| **traceability TZ5 (本 review 新增)** | **tasks T4c EXEMPTION_LIST 数字精度 5 → 7 残留** | **hf-finalize 阶段顺手刷新（推荐）** |

### 给 hf-finalize reviewer

finalize 阶段重点应放在：

1. **RELEASE_NOTES F008 段 5 项 TBD 占位字段**用 manual smoke 实测数据填充（design § 18 #2 已说明）
2. **测试增量分解描述精度**同步刷新（code-review CR6 minor）
3. **可选**：tasks T4c EXEMPTION_LIST 数字精度从"4 + 1"刷新为"7"（本 review 新增 minor）+ packs/coding/README.md 类目计数标题刷新（code-review CR4 minor）+ F5 LICENSE 自动化 assertion 补 (test-review TT3 minor)
4. workflow closeout pack 归档

---

## 结构化返回

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-regression-gate",
  "record_path": "docs/reviews/traceability-review-F008-coding-pack-and-writing-pack.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][TZ5] task plan T4c acceptance EXEMPTION_LIST 数字精度残留：tasks 写 '4 + 1 = 5'，与 spec/design/test 三层最终状态 7 项有 anchor 漂移 (T4c 实施期间 5→7 扩展未回写 tasks)，不阻塞但建议 hf-finalize 顺手同步",
    "[minor][LLM-FIXABLE][TZ4/ZA4] F5 失败模式 (packs/writing/LICENSE 存在) 缺自动化 assertion (与 test-review/code-review 同源)，物理文件存在 + git 受控兜底",
    "[minor][LLM-FIXABLE][TZ3/ZA3] tests/test_cli.py:3042 carry-forward 混入 T1c commit (与 test-review/code-review 同源)，commit message 声明缓解",
    "[minor][LLM-FIXABLE][TZ4] T1c sentinel test fail-first RED 证据仅 commit message 文字层 (与 test-review 同源)，可 git revert 重放",
    "[minor][LLM-FIXABLE][TZ5] packs/coding/README.md 类目计数标题与表格行数轻漂移 (与 code-review 同源)，不影响 22 总数与追溯链"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": "task plan T4c acceptance EXEMPTION_LIST 数字精度残留 5 → 7 (本 review 新增)"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ4",
      "summary": "F5 LICENSE 守门缺自动化 (上游同源)"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ3",
      "summary": "tests/test_cli.py:3042 carry-forward 混入 T1c commit (上游同源)"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ4",
      "summary": "T1c sentinel RED 证据弱 (上游同源)"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": "packs/coding/README.md 类目计数标题与表格行数轻漂移 (上游同源)"
    }
  ]
}
```
