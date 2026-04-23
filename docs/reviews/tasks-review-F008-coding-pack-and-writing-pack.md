# F008 任务计划评审记录（hf-tasks-review）

- 评审对象: `docs/tasks/2026-04-22-garage-coding-pack-and-writing-pack-tasks.md`（草稿 r1，9 个 task：T1a/T1b/T1c + T2 + T3 + T4a/T4b/T4c + T5）
- 关联 spec: `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准 r2）
- 关联 design: `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（已批准 r2，8 ADR + 9 sub-commit + 9 INV + 4 测试文件）
- 评审日期: 2026-04-23
- 评审人: hf-tasks-review reviewer subagent
- Revision: r1

## 结论

需修改

理由：任务粒度、追溯覆盖、依赖图、Router 重选规则总体到位，但存在 1 项 **critical 级别冲突**（T2/T3 NFR-801 / INV-9 验收与上游 SKILL.md 实际内容 + CON-803 字节级 1:1 + 既有 `test_neutrality.py` 三方冲突，落地后必然让 baseline 测试退绿）；2 项 **important 级别**（T2 Files 描述与上游 layout 不一致 + family-level `prompts/` 未处置；T1c fail-first 顺序在单一 task 内未拆出明确步骤）；多项 **minor**（依赖说明歧义、acceptance 用词薄弱、NFR-803 wall-clock 验收点缺失）。

## 多维评分

| 维度 | 评分 | 说明 |
|---|---|---|
| TR1 可执行性 | 8/10 | 9 个 task 粒度合理，T1/T4 已经按 design § 10.1 拆出 sub-commit；无 "实现某模块" 大任务 |
| TR2 任务合同完整性 | 7/10 | 每个 task 都有 Acceptance / Files / Verify / 完成条件 / 测试种子；但 T2/T3 INV-9 acceptance 本身不可满足（见 critical 1）；T4b acceptance 用词偏弱 |
| TR3 验证与测试设计种子 | 7/10 | 4 个测试文件已映射到 task；T1c sentinel 测试种子写明 fail-first 期望，但单 task 内未显式拆出"先写测试 RED → 再同步 GREEN"两步 |
| TR4 依赖与顺序正确性 | 8/10 | 关键路径 7 跳清晰；T4a 显式依赖 T1+T2+T3 全部完成；T4c 依赖 T4a+T4b；T5 依赖全部前序。§6 "T2/T3 与 T1c 并行可" 与 §8 串行 priority 规则措辞冲突 |
| TR5 追溯覆盖 | 7/10 | § 4 追溯表覆盖 FR-801..807 + NFR-801..804 + CON-801..804 + 红线 1-6 + INV-1..9；但 critical 1 暴露 NFR-801 在上游内容物现实下不可满足，spec/design 未处置的冲突被 task plan 沿袭 |
| TR6 Router 重选就绪度 | 9/10 | § 8 选择规则唯一可重放；§ 9 队列投影表清晰；P=1..9 单调；T1a 起点显式锁死 |

任一关键维度 < 6 → 否则不通过。当前最低 7/10，但 critical finding 仍要求"需修改"再过。

## 发现项

### Critical（必须修订后才可进入实现）

- **[critical][LLM-FIXABLE / 需 USER-INPUT 决定修复路径][TR2 + TR5][T2 + T3 + 整体 INV-9 链]** **NFR-801 / INV-9 验收与上游 SKILL.md 实际内容 + CON-803 字节级 1:1 + 既有 `test_neutrality.py` 三方冲突，T2/T3 完成时必然让 baseline 退绿（违反 NFR-802）**。

  证据（基于实测，非推断）：
  - 既有 `tests/adapter/installer/test_neutrality.py` line 34 的 glob 是 `packs/*/skills/*/SKILL.md` 与 `packs/*/agents/*.md`（@ `tests/adapter/installer/test_neutrality.py:34-37`），用 pytest.parametrize **import 时枚举**，意味着 T2 / T3 把新文件落到 `packs/writing/skills/<id>/SKILL.md` 与 `packs/garage/skills/writing-skills/SKILL.md` 后，该测试自动新增参数化用例。
  - 上游源端实测命中：
    - `.agents/skills/write-blog/hv-analysis/SKILL.md` line 55：`检查路径 \`/mnt/.claude/skills/web-access/SKILL.md\` 是否存在`
    - `.agents/skills/writing-skills/SKILL.md` line 12：`Personal skills live in agent-specific directories (\`~/.claude/skills\` for Claude Code, \`~/.agents/skills/\` for Codex)`
  - T2 acceptance 写明 "INV-9: `grep -rE '\\.claude/|\\.cursor/|\\.opencode/|claude-code' packs/writing/` 命中 = 0"；T3 没显式列 INV-9 但 design § 11.1 INV-9 表述覆盖三个 pack。
  - CON-803 强制 SKILL.md 字节级 1:1（task plan 多处复述）。
  - 三件事同时为真则 T2 完成后 `test_neutrality.py[hv-analysis/SKILL.md]` 必然 RED，T3 完成后 `test_neutrality.py[writing-skills/SKILL.md]` 必然 RED → 直接违反 NFR-802 "测试基线零回归" 与 task plan § 1 "零回归保护"。

  spec NFR-801 仅对 README 留白名单豁免（"除 README 中作为示例字符串出现且明确标注为 '宿主目录示例'"），**SKILL.md 不在豁免范围**。因此本冲突必须在进入实现之前解决，候选解决路径需 USER-INPUT 选择：
  1. 走 hf-increment：spec NFR-801 + design ADR-D8-1/2 amendment 把 SKILL.md 内**作为 documentation example 的宿主路径字面值**纳入豁免，并显式 enumerate 这两处 SKILL.md 与 1 处 examples/CLAUDE_MD_TESTING.md，同步收紧 `test_neutrality.py` 增加 allowlist；
  2. CON-803 例外：在 design 加 ADR addendum，允许这 2 处 SKILL.md 的 search-and-replace（如 `~/.claude/skills` → `~/<host-skills>/skills` 的 placeholder），并在 task plan 加 search-and-replace sub-task；
  3. 把这 2 个 skill 整体推到 deferred backlog，本 cycle 仅落 hv-analysis + writing-skills 之外的 27 个 skill（spec FR-802 / FR-803 + § 2.1 数字派生约束被打破，不推荐）。

  无论选哪条路径，**当前 task plan 都必须更新**：要么显式 acknowledge 冲突并加 reference 到 spec/design amendment commit，要么加 search-and-replace sub-task。当前 task plan 把 INV-9 当作直接由 cp -r 自然成立的不变量，是错误前提。

### Important

- **[important][LLM-FIXABLE][TR2][T2 — `Files / 触碰工件` 与 `测试设计种子`]** T2 Files 写 "新增 `packs/writing/skills/<id>/` × 4（含各自 prompts/ examples/ 子目录）"，但实测 4 个 write-blog 子 skill 的 layout 是：
  - `blog-writing/`：仅 `SKILL.md`
  - `humanizer-zh/`：`SKILL.md` + `LICENSE` + `README.md`
  - `hv-analysis/`：`SKILL.md` + `references/` + `scripts/`
  - `khazix-writer/`：`SKILL.md` + `references/`

  没有任一 skill 子目录含 `prompts/` 或 `examples/`。`prompts/` 实际位于 family-level（`.agents/skills/write-blog/prompts/横纵分析法.md`），被 family README 引用。task plan T2 没说明 family-level `prompts/横纵分析法.md` 与 `write-blog/README.md` 是否搬迁；spec FR-802 也没强约束，但落地时若不搬，hv-analysis SKILL 内的"横纵分析法" prompt 引用链断裂，且 spec § 1 表格"4 个 write-blog 子 skill" 与上游 family-level 资产关系不明。建议：
  - 修正 Files 描述（删 "含各自 prompts/ examples/ 子目录"，准确写出每个 skill 的实际 layout）
  - 在 T2 Acceptance 显式裁决 family-level `prompts/横纵分析法.md` 与 `write-blog/README.md` 是落到 `packs/writing/`（family-level 副本）还是显式 deferred（write 入 RELEASE_NOTES F008 已知限制段）

- **[important][LLM-FIXABLE][TR3 + TR4][T1c — fail-first 顺序在单 task 内未显式拆步]** T1c 测试设计种子写明"先写测试 → 在 drift 同步前跑应 RED → 同步后跑应 GREEN"，但作为单 task 调度时，router 把 T1c 当一个原子单位发给 `hf-test-driven-dev`，executor 是否真的按 "先写测试 → 跑 RED → 反向 cp → 跑 GREEN" 顺序操作，依赖 executor 自觉。task plan acceptance 仅约束最终态（diff 输出空 + 测试 GREEN）。建议二选一：
  - (a) 在 T1c acceptance 显式拆出两步 sub-acceptance：① 测试文件先 commit 一个能在反向同步前跑 RED 的版本（或在 PR walkthrough 提供 RED 截图）② 反向同步后跑 GREEN
  - (b) 把 T1c 拆为 T1c-1（写 sentinel test，期望本地手动跑 RED）+ T1c-2（反向同步 + 跑 GREEN）两个 sub-task

  对应 design § 14 F2 "未来有人修改 packs 但忘了同步根级" 的硬门槛——需要 cycle 落地时就证明 sentinel 真的能 catch drift。

### Minor

- **[minor][LLM-FIXABLE][TR4][§6 + §8 措辞矛盾]** § 6 关键路径文字写 "T2 + T3 与 T1c 并行可，但建议串行落 commit"；§ 8 选择规则又把 T1c (P=3) → T2 (P=4) → T3 (P=5) 串行排序。`router` 实际行为是串行（按 P 升序），prose 里的 "并行可" 是误导。建议把 § 6 改写为 "T2/T3 与 T1c 在依赖图层面互不依赖，但 § 8 选择规则按 P 升序串行；router 不并发"。

- **[minor][LLM-FIXABLE][TR2][T1a — Verify 内部矛盾]** T1a Verify 写 "`ls packs/coding/skills/ | wc -l` 应包含 22 项 + （可能含 docs/ templates/ 由 T1b 加，但 T1a 时不应有）"。括号内自相矛盾（"可能含" 又 "T1a 时不应有"）。在 T1a 完成时点，packs/coding/skills/ 应当 == 22 项；建议简化为 "`ls packs/coding/skills/ | wc -l` == 22"。

- **[minor][LLM-FIXABLE][TR2][T4b — AGENTS.md 验收过弱]** T4b acceptance #1 是 "`grep -A2 'Packs & Host Installer' AGENTS.md` 含 "已落地" 而不是 "候选""，但实测当前 `AGENTS.md` § "Packs & Host Installer (F007)" **根本不含 "F008 候选" 字样**（grep 仅命中 F007 相关），所以这条 grep 在 cycle 完成后非常容易 trivially pass。建议把 acceptance 提升到结构性检查：
  - "AGENTS.md `## Packs & Host Installer` 段后续表格新增包含 `coding`、`writing` 与 `garage` 三行，每行含 pack-id + status + skill 计数（或同质等价物）"
  - 加一条 "AGENTS.md grep `garage init --hosts cursor,claude` 命中 ≥ 1（onboarding 命令样板存在）"（已部分覆盖）

- **[minor][LLM-FIXABLE][TR3][T5 RELEASE_NOTES 占位段缺 enum]** T5 acceptance 仅 grep `## F008` 命中 + 段落结构 4 段。没列出哪些字段是占位（如 "manual smoke wall-clock = TBD"、"installed_packs from manifest = TBD"）、哪些是落地时即可填实。建议：
  - 在 T5 Files 备注里列出占位字段清单（≥ 3 项），让 hf-finalize 阶段对接清晰

- **[minor][LLM-FIXABLE][TR3][NFR-803 ≤ 5s wall-clock 验收点不直接]** § 4 追溯表把 NFR-803 ≤ 5s 验证落到 "T4c + walkthrough"；T4c 内部用 `pytest --durations` 抓 wall-clock，但 pytest fixture setup（创建 tmp packs/、tmp .garage/）会被计入 duration，与 design § 10.3 "manual smoke 用 `time garage init`" 测的口径不一致。建议在 T5 walkthrough 段（或 § 7 完成定义 #6）显式写明 "manual smoke 必须提交 `time garage init --hosts all` 输出且实测 wall-clock ≤ 5s"，让 NFR-803 验收锚点既包含自动化 (T4c) 又包含 manual (walkthrough)。

- **[minor][LLM-FIXABLE][TR2][T1c Files 漏列 .garage/ 副作用]** T1c 触碰 `tests/adapter/installer/test_skill_anatomy_drift.py` 与 `docs/principles/skill-anatomy.md`，但若该测试在 import 时读取 packs/coding/principles/skill-anatomy.md 路径（即 sentinel 模式），且测试 fixture 不依赖 .garage/，建议在 Files 段加一句 "测试文件不依赖 .garage/ 临时目录"，避免 hf-test-driven-dev 误把 fixture 模式套进来。design § 18 #4 已隐含此点，但 task plan 应显式继承。

## 缺失或薄弱项

1. **NFR-801 / INV-9 与上游 SKILL.md 内容物的预飞检（pre-flight）应在 task plan 起手处加 sanity check sub-task**：建议在 T1a 之前或之内加一步 "对 `.agents/skills/{harness-flow,write-blog,find-skills,writing-skills}/` 跑 `grep -rE '\\.claude/|\\.cursor/|\\.opencode/|claude-code' --include=SKILL.md` 并归档命中清单，作为 INV-9 例外白名单或 search-and-replace 输入"。当前 task plan § 10 风险表 F1-F7 没收 NFR-801 这类风险（仅 F4 表面提了 ASM-801）。

2. **`prompts/横纵分析法.md` 与 `.agents/skills/write-blog/README.md` 这 2 个 family-level 资产的处置裁决** 在 task plan 缺位（既不在 T2 Files 也不在 § 5 deferred）。design ADR-D8-1 处理的是 hf-* family-level docs/templates/principles，未覆盖 write-blog family-level 资产。建议 T2 acceptance 加裁决条款。

3. **T4a 在 dogfood 已运行场景下的 `git status` 干净不变量保护**：design § 14 F3 已识别 "如 PR walkthrough 之前已跑过 dogfood 的话先 rm -rf .cursor/skills .claude/skills 再 commit"。task plan § 10 风险表第 3 行复述了，但 T4a verify 没加 "如本地有 dogfood 残留，先确认在 .gitignore 排除后 git status 才空" 的硬门槛步骤。建议 T4a Verify 加 "T4a commit 必须在干净 working tree（无既有 .cursor/skills/ .claude/skills/）上跑 `git status --porcelain`，或先 rm -rf 后跑"，避免 cycle 期间 dogfood 残留污染 commit 范围。

4. **find-skills 是否真有 SKILL.md 兼 family asset 副本去重检查**（INV-2 范围扩张）：T3 仅 cp `find-skills/SKILL.md`，find-skills 没有 references/ 子目录（实测仅 `SKILL.md` 单文件），不会触发 INV-2。但 task plan 应明确这一点（"find-skills 是单文件 skill，无附属"），免得 hf-test-driven-dev 困惑。

5. **`pyproject.toml` 不变（NFR 隐含的 dependency lock）**：spec § 8 写明"零依赖变更"。task plan 没显式守门 `git diff main..HEAD -- pyproject.toml uv.lock` 输出空。建议在 § 7 完成定义加一条 "`git diff main..HEAD -- pyproject.toml uv.lock` 输出空"。

## 下一步

`hf-tasks` — 按本评审 critical + important + minor findings 在 task plan 草稿上做定向修订，重点：

1. 解决 NFR-801 / INV-9 与上游内容物 + CON-803 三方冲突（critical）：先发起 USER-INPUT 决策（路径 1/2/3 三选一），若选路径 1 则同步发起 spec amendment（hf-increment）后再回 hf-tasks 落 task plan acceptance；若选路径 2 则在 task plan 加 search-and-replace sub-task + design ADR addendum 引用。
2. 修正 T2 Files 与 family-level 资产裁决（important）。
3. 拆 T1c fail-first 顺序或加 sub-acceptance（important）。
4. 收紧 §6 与 §8 措辞、T1a 与 T4b acceptance、T5 占位段 enum、NFR-803 wall-clock 验收点（minor 集合）。
5. 补 § 7 完成定义 "pyproject.toml / uv.lock 零变更"（minor）。

修订完成后重派 hf-tasks-review 复审。

## 记录位置

`/workspace/docs/reviews/tasks-review-F008-coding-pack-and-writing-pack.md`

## 交接说明

- 结论 `需修改`，不进入"任务真人确认" approval step。
- `next_action_or_recommended_skill = hf-tasks`。
- `needs_human_confirmation = false`（修订前不进入 approval）。
- `reroute_via_router = false`（不存在 route/stage/profile/上游证据冲突级阻塞——上游 spec 与 design 都已批准 r2，本评审 critical 暴露的是 spec/design/上游内容物三方一致性 gap，可在 hf-tasks 内通过 task plan 修订路径 + USER-INPUT 选择修复路径承接，必要时由 hf-tasks 触发 hf-increment 局部 amendment）。
- 不修改 spec / design / tasks 文档；不修改 task-progress.md；不 git commit / push。

---

## 复审 r2

- 复审日期: 2026-04-23
- 复审输入: 父会话 commit `e8f1a35` 对 r1 全部 finding 完成的定向回修
- 复审范围: 逐项校验 r1 critical / 2 important / 6 minor / 3 缺失项的闭合度，重点 critical 修复（CON-803 例外 + search-and-replace）的 spec / task / 测试守门三者一致性

### r2 结论

**需修改**

理由：r1 critical 修复结构上正确（CON-803 例外条款 + T2/T3 search-and-replace acceptance + INV-9 守门三者形态都已就位），但 **CON-803 例外 #2 实施清单 enum 范围实测不完整**，仅覆盖到 2 个 SKILL.md，遗漏了上游 `cp -r` 整子目录会一并搬到 packs/ 的 3 个非-SKILL.md 文件（共 18 处黑名单命中）。这意味着 T2/T3 commit 后 task plan 自身定义的 INV-9 递归 grep 必然 RED，hf-test-driven-dev 实施时即被卡住。其余 r1 finding 均已闭合或基本闭合。

### 维度评分（r2）

| 维度 | r1 评分 | r2 评分 | 备注 |
|---|---|---|---|
| TR1 可执行性 | 8 | 8 | 9 task 粒度仍合理；T1c 拆出 Step 1-3 加分 |
| TR2 任务合同完整性 | 7 | 7 | T1a/T4b/T5 acceptance 已收紧；但 T2/T3 acceptance 与 CON-803 enum 仍存在覆盖缺口 |
| TR3 测试设计种子 | 7 | 8 | T1c 显式 Step 1 RED 截图证据 + sentinel 不依赖 .garage/ 标注；NFR-803 双轨清晰 |
| TR4 依赖与顺序 | 8 | 8 | §6 措辞已澄清依赖图 vs 调度二分；§8 line 464 残留旧措辞但效果不变 |
| TR5 追溯覆盖 | 7 | 7 | spec NFR-801 / CON-803 已 amend 但 enum 不完整 |
| TR6 Router 重选就绪度 | 9 | 9 | 不变 |

无关键维度 < 6，但 critical 残留要求"需修改"再过。

### 逐条 r1 finding 闭合度判定

| r1 finding | 严重度 | 闭合判定 | 证据 |
|---|---|---|---|
| critical: NFR-801/INV-9 三方冲突 | critical | **未完全闭合**（见下面"r2 残留 critical"详细说明）| spec CON-803 例外 #2 enum 仅 2 处 SKILL.md；上游 humanizer-zh/README.md + writing-skills/anthropic-best-practices.md + writing-skills/examples/CLAUDE_MD_TESTING.md 共 18 处黑名单命中未 enum 处置 |
| important #2: T2 Files + family-level prompts/横纵分析法.md | important | **已闭合** | task plan line 201-206 补全 4 子 skill 实测 layout；line 211 + 225-226 把 prompts/横纵分析法.md 搬到 `packs/writing/prompts/`（pack 顶层），README 决定不单独搬 |
| important #3: T1c fail-first 顺序 | important | **已闭合** | task plan line 180-183 显式 Sub-acceptance Step 1/2/3；line 195 PR walkthrough 含 RED 证据要求 |
| minor #4: §6/§8 措辞冲突 | minor | **基本闭合 / 微残留** | task plan line 424-428 关键路径改为 9 跳 + 依赖图 vs 调度二分；但 § 8 line 464 仍留 "与 T1c 并行可，但建议串行" 旧措辞，与 § 6 新措辞表面冲突。效果不变（P 升序串行始终成立），不阻塞 |
| minor #5: T1a Verify 自相矛盾 | minor | **已闭合** | task plan line 126 简化为 `ls ... wc -l == 22` + 备注 T1b 后变 24 |
| minor #6: T4b AGENTS.md grep 过弱 | minor | **已闭合** | task plan line 316-321 升级到 5 个结构性 invariant；line 332-337 Verify 含 6 个 grep |
| minor #7: T5 RELEASE_NOTES 占位 enum | minor | **已闭合** | task plan line 384-389 5 项占位字段清单；line 395 `TBD ≥ 5` 守门 |
| minor #8: NFR-803 wall-clock 验收 | minor | **已闭合** | task plan line 451-454 双轨明确（pytest --durations + manual time） |
| minor #9: T1c sentinel 不依赖 .garage/ | minor | **已闭合** | task plan line 186 + 188-190 显式标注 |
| 缺失 #1: NFR-801 pre-flight | important | **部分闭合** | task plan line 450 "T2/T3 完成后立即跑 test_neutrality 守门" 已加；但与 critical 残留同因——pre-flight enumerate 不完整，依赖实施者主动发现 |
| 缺失 #2: pyproject.toml/uv.lock 零变更 | minor | **已闭合** | task plan line 444 § 7 #6 守门 |
| 缺失 #3: T4a dogfood 残留 4 步顺序 | minor | **已闭合** | task plan line 284-288 4 步硬门槛 |

### r2 残留 / 新发现 finding

#### Critical（必须修订后再复审）

- **[critical][LLM-FIXABLE / 部分 USER-INPUT][TR2 + TR5][T2 + T3 + spec CON-803 enum + design ADR]** **CON-803 例外 #2 实施清单 enum 范围实测不完整，T2/T3 commit 后 INV-9 递归 grep 必然 RED**

  实测证据（基于实际跑 grep）：

  | 上游文件（被 T2/T3 cp -r 一并带入 packs/）| 黑名单命中数 | 内容性质 | r1 CON-803 enum 是否覆盖 |
  |---|---|---|---|
  | `.agents/skills/write-blog/hv-analysis/SKILL.md` line 55 | 1 | 业务示例 | ✅ enum 已覆盖 |
  | `.agents/skills/writing-skills/SKILL.md` line 12 | 1 | 业务示例 | ✅ enum 已覆盖 |
  | `.agents/skills/write-blog/humanizer-zh/README.md` line 33/40/45 | **3** | 安装命令样板 | ❌ **未 enum** |
  | `.agents/skills/writing-skills/anthropic-best-practices.md` line 1143 | **1** | 含 `claude-code` 字面值 | ❌ **未 enum** |
  | `.agents/skills/writing-skills/examples/CLAUDE_MD_TESTING.md` 14 行 | **14** | examples 文件，全篇是 `~/.claude/skills/` 路径示例 | ❌ **未 enum** |

  与 task plan acceptance 的冲突：
  - T2 task plan line 222（Files）：`新增 packs/writing/skills/humanizer-zh/ (SKILL.md + LICENSE + README.md)` — README.md 显式被 cp 入
  - T2 task plan line 238（Verify）：`grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/writing/ | wc -l == 0` — humanizer-zh/README.md 落入 packs/writing/ 后递归 grep 命中 3 行
  - T3 task plan line 264（Files）：`新增 packs/garage/skills/writing-skills/（整子目录）` — examples/CLAUDE_MD_TESTING.md 与 anthropic-best-practices.md 都被 cp 入
  - T3 task plan line 275（Verify）：`grep -rE ... packs/garage/ | wc -l == 0` — 落入后递归 grep 命中 1 + 14 = 15 行

  与 spec 验收的冲突：
  - spec NFR-801 验收 #1：`packs/coding/ packs/writing/ packs/garage/` 三 pack 整体递归 grep 命中数 = 0；spec wording 明确"不豁免 README 内 example 字符串——除非 README 在文中显式标注为 '宿主目录示例' 段落且 design 在 ADR 内白名单 enumerate"。当前 design 没有该 ADR，README 不享豁免；examples/ 文件类型更不在豁免话术内
  - spec CON-803 不变量 (c)：`每个被改 SKILL.md 文件 git diff ≤ 3 行`。该不变量 wording 限定 "SKILL.md 文件"——但 humanizer-zh/README.md 与 anthropic-best-practices.md 是 .md 但不是 SKILL.md，CON-803 例外 #2 当前是否覆盖非-SKILL.md 文件 wording 不清；CLAUDE_MD_TESTING.md 14 行命中无论如何都超 ≤ 3 行硬上限，需要更宽口径

  与既有 `tests/adapter/installer/test_neutrality.py` 的关系：
  - 该测试 glob 是 `packs/*/skills/*/SKILL.md` + `packs/*/agents/*.md`（非递归，不扫子目录或 README） — 因此 README/examples 命中**不会让 test_neutrality.py 直接 RED**（NFR-802 baseline 不破）
  - 但 task plan T2/T3 自身写明的 `grep -rE ... packs/writing|garage/` 是递归 grep，会自检 RED
  - spec NFR-801 验收 #1 也是三 pack 整体递归 grep，会 spec-acceptance RED

  **修复路径**（critical 闭合 = spec 例外 + task acceptance + 测试守门三者一致）：

  必须同步 3 处文档：

  1. **spec CON-803 例外 #2 enum 扩充**：把 3 个新发现的违反点 enumerate 进清单；clarify 例外是否覆盖非-SKILL.md（README / examples 类）.md 文件
  2. **spec CON-803 不变量 (c) ≤ 3 行 wording 修订**：要么把限定从 "SKILL.md 文件" 拓宽到 "任意被搬迁的 .md 文件"；要么对超 3 行的 examples 类文件提供另一条例外（如 examples/ 文件允许整段重写或整文件删除，需 design ADR 显式裁决）
  3. **design 新增 ADR-D8-9（或 amend ADR-D8-1/2）**：对 humanizer-zh/README.md / writing-skills/anthropic-best-practices.md / writing-skills/examples/CLAUDE_MD_TESTING.md 三类文件分别给出处置策略——三选一：
      - (a) ≤ 3 行 search-and-replace（适合 humanizer-zh/README.md 3 行 + anthropic-best-practices.md 1 行；不适合 14 行 CLAUDE_MD_TESTING.md）
      - (b) 文件级删除（适合 examples/CLAUDE_MD_TESTING.md，因其是教学示例，删除不损 writing-skills 主干；需 design 显式裁决"删除 examples/CLAUDE_MD_TESTING.md 是否影响 writing-skills 业务语义"）
      - (c) 推到 deferred backlog（不推荐，与 spec § 2.1 "字节级 1:1 + 必要相对引用路径修复" 已列入本 cycle 收敛精神冲突）
  4. **task plan T2 / T3 acceptance + Files 同步**：T2 acceptance 加 humanizer-zh/README.md 处置 sub-step + git diff 守门；T3 acceptance 加 anthropic-best-practices.md + CLAUDE_MD_TESTING.md 处置 sub-step + 量化守门
  5. **缺失 #1 NFR-801 pre-flight 实质升级**：task plan § 7 加一步 "T2 / T3 cp -r 后立即跑 `grep -rE ... packs/writing/ packs/garage/` 全 enum 命中清单，与 spec CON-803 例外 #2 enum 比对，发现新命中点必须 PR 描述显式声明"——这条已在 spec CON-803 详细说明段以 "PR commit message 显式声明" 形式存在，但 task plan 没把它 lift 到验证流程

  分类细分：
  - humanizer-zh/README.md（3 行）→ LLM-FIXABLE（直接 ≤ 3 行 search-and-replace）
  - writing-skills/anthropic-best-practices.md（1 行 `claude-code`）→ LLM-FIXABLE
  - writing-skills/examples/CLAUDE_MD_TESTING.md（14 行）→ **USER-INPUT**（删除整文件 vs 整段重写 vs 推 deferred 三选一须人决定）

#### Minor（不阻塞，但建议本轮顺手收）

- **[minor][LLM-FIXABLE][TR4][§ 8 line 464]** § 8 选择规则正文仍写 "T1b 完成 → T1c ready；同时 T2 / T3 也 ready（与 T1c 并行可，但建议串行）"，与 § 6 新增的 "依赖图层面 vs 调度层面" 二分措辞表面冲突。建议把括号改为 "（依赖图层面 ready，调度按 P 升序选最小者）"，与 § 6 严格对齐。

- **[minor][LLM-FIXABLE][TR5][T2 prompts/横纵分析法.md vs INV-2]** T2 把 `prompts/横纵分析法.md` 搬到 `packs/writing/prompts/` 作为 family-level 资产。spec FR-804 / design INV-2 锁定的 11 项 family asset enumerate 仅含 hf-* family 4 docs + 5 templates + 2 principles，不含 writing family 资产。task plan 当前没说明 writing family `prompts/` 是否计入 INV-2 单点不变量。建议在 T2 acceptance 加一句 "writing family `prompts/` 不计入 INV-2 enumerate（INV-2 锁定 hf-* family 11 项）；但 prompts/横纵分析法.md 自身在 `packs/writing/` 内单点（`find packs -name 横纵分析法.md \| wc -l == 1`）"，避免 hf-test-driven-dev 阶段对 INV-2 范围困惑。

### 关键 r2 维度判断

| 关键问题 | 判定 |
|---|---|
| spec CON-803 例外条款 (语法层面) | ✅ wording 已闭合（三类例外 + 量化守门 + 不变量） |
| spec CON-803 例外 enum (实施清单) | ❌ 未完整覆盖 cp -r 整子目录的 3 处非-SKILL.md 命中 |
| task T2/T3 acceptance (search-and-replace sub-step) | ⚠️ 仅 enum 内 2 处 SKILL.md 显式覆盖；非 SKILL.md 命中无 acceptance |
| 测试守门 (test_neutrality + task INV-9) | ⚠️ test_neutrality.py 不会 RED（其 glob 不扫子目录），但 task INV-9 递归 grep 自检会 RED |
| spec NFR-801 / task acceptance / 测试守门三者一致 | ❌ 不一致（task INV-9 与 spec NFR-801 都会 RED；test_neutrality 不会 RED 形成假阴性） |

### 下一步

`hf-tasks` — 父会话按 r2 critical 残留 + 2 minor 做定向回修：

1. 与用户协商 USER-INPUT 决定 `writing-skills/examples/CLAUDE_MD_TESTING.md` 14 行命中处置策略（删除整文件 / 整段重写 / 推 deferred 三选一）
2. spec CON-803 例外 #2 enum 扩充 + 不变量 (c) wording 修订
3. design 新增 ADR-D8-9（或 amend）裁决 3 类文件处置
4. task plan T2 / T3 acceptance 同步加 humanizer-zh/README.md / anthropic-best-practices.md / CLAUDE_MD_TESTING.md 处置 sub-step
5. § 8 line 464 措辞 + T2 INV-2 范围注释（minor 顺手）

修订完成后重派 hf-tasks-review 复审 r3。

### 交接说明

- 结论 `需修改`，不进入"任务真人确认" approval step。
- `next_action_or_recommended_skill = hf-tasks`。
- `needs_human_confirmation = false`。
- `reroute_via_router = false`（不存在 route/stage/profile/上游证据冲突级阻塞——上游 spec/design 已批准 r2，本轮 critical 残留是 r1 修复 enum 不完整，可在 hf-tasks 内通过 spec amendment + design ADR + task acceptance 三处同步修订）。
- 不修改 spec / design / tasks 文档；不修改 task-progress.md；不 git commit / push。

---

## 复审 r3

- 复审日期: 2026-04-23
- 复审输入: 父会话 commit `bb6e38f` 对 r2 critical（ADR-D8-9 分类方案）+ 2 minor 完成的定向回修
- 复审范围: 逐项校验 r2 finding 闭合度；重点 critical 修复 spec / design / task 三层一致性

### r3 结论

**需修改**

理由：r2 critical（CON-803 例外 enum 不完整 + CLAUDE_MD_TESTING.md 14 行硬上限冲突）的 spec 与 design 层闭合到位（NFR-801 分两层验收 + CON-803 enum + ADR-D8-9 + 豁免清单 + 新增 sentinel 测试 5 件套），ADR-D8-9 选定的"分类方案"是合理的工程裁决，但 **task 层有 1 处 important 级 wording 不一致 + 3 处 minor wording / 数字不一致 残留**，会让 hf-test-driven-dev 阶段实际跑 task Verify 命令时撞墙；spec / design 已经分两层但 task Verify 命令仍在用 r1 递归 grep wording。

### 维度评分（r3）

| 维度 | r2 评分 | r3 评分 | 备注 |
|---|---|---|---|
| TR1 可执行性 | 8 | 8 | 不变 |
| TR2 任务合同完整性 | 7 | 7 | T2/T3 Acceptance 已分层（INV-9 SKILL.md 严格 + meta 豁免），但 Verify 命令 wording 残留 r1 递归 grep；T4c 完成条件 / § 7 #4 测试基线数字内部不一致（596 vs 598）|
| TR3 测试设计种子 | 8 | 9 | 新增 test_neutrality_exemption_list 测试 + EXEMPTION_LIST 常量同步要求清晰 |
| TR4 依赖与顺序 | 8 | 9 | § 8 完全重写 "依赖图层面互不依赖 vs 调度并发" 二分；router 串行选 T1c → T2 → T3 显式拆出 |
| TR5 追溯覆盖 | 7 | 8 | spec / design / task 在 NFR-801 主验收已三层一致；design § 11.1 INV-9 表 wording 仍残留 r1 版本递归 grep（与 ADR-D8-9 不一致） |
| TR6 Router 重选就绪度 | 9 | 9 | 不变 |

无关键维度 < 6，但 important 残留要求"需修改"再过。

### 逐条 r2 finding 闭合度判定

| r2 finding | 严重度 | 闭合判定 | 证据 |
|---|---|---|---|
| critical: CON-803 enum 不完整 + CLAUDE_MD_TESTING.md 超 ≤3 行 | critical | **基本闭合（spec/design 层完全闭合 + task acceptance 闭合 + 测试守门闭合；但 task Verify 残留 r1 递归 grep wording → important 级残留，详见下面 r3 残留 #1）** | spec NFR-801 line 344-349 分三层验收 + spec CON-803 line 410-422 enum 4 文件 + design ADR-D8-9 line 329-360 + design § 13.1 line 621 新增 test_neutrality_exemption_list + task T4c line 362-365 测试种子 |
| minor: § 8 line 464 措辞冲突 | minor | **已闭合** | task § 8 line 468-479 完整重写 + line 479 末段 "依赖图层面互不依赖 vs 调度并发是两件事" 二分 |
| minor: T2 prompts/ 是否计入 INV-2 | minor | **已闭合** | task line 216 显式 "packs/writing/prompts/ 也属 family-level，需要计入 INV-2 enumerate 范围" + 实施时 fixture 加入待检查清单 |

### r3 残留 / 新发现 finding

#### Important（必须修订后再复审）

- **[important][LLM-FIXABLE][TR2][T2 Verify line 240 + T3 Verify line 278]** **T2/T3 Verify 命令仍是 r1 版本递归 grep `wc -l == 0`，与新分层 Acceptance + spec NFR-801 验收 #1 + design ADR-D8-9 全冲突；hf-test-driven-dev 阶段按 Verify 跑必然 RED**

  实测证据：
  - T2 Acceptance line 214（已正确改为分层）：`find packs/writing/ \( -name 'SKILL.md' -o -path '*/agents/*.md' \) -exec grep -lE ... \;` 命中 = 0
  - T2 Acceptance line 215（已正确添加豁免）：humanizer-zh/README.md 等 meta 文件按 ADR-D8-9 enum 豁免
  - T2 Verify line 240（**残留 r1 wording**）：`grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/writing/ | wc -l == 0`
  - 实际跑结果：humanizer-zh/README.md 含 3 行命中（行 33、40、45 是 humanizer-zh 在 Claude Code 上的安装命令样板），递归 grep 必然命中 ≥ 3，违反 `wc -l == 0`

  T3 同样：
  - T3 Acceptance line 258（分层）+ line 259（豁免 anthropic-best-practices.md + CLAUDE_MD_TESTING.md）
  - T3 Verify line 278（**残留 r1 wording**）：`grep -rE ... packs/garage/ | wc -l == 0`
  - 实际跑结果：anthropic-best-practices.md 1 行 + CLAUDE_MD_TESTING.md 14 行 = 15 命中，违反 `wc -l == 0`

  修复方式（LLM-FIXABLE，wording-only）：
  - T2 Verify 第 5 条改为：`find packs/writing/ \( -name 'SKILL.md' -o -path '*/agents/*.md' \) -exec grep -lE '\.claude/|\.cursor/|\.opencode/|claude-code' {} \; | wc -l` == 0
  - T2 Verify 第 5 条之后追加：`grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/writing/ --include='*.md' --exclude='SKILL.md' -l` 命中行所属文件全部 ∈ ADR-D8-9 EXEMPTION_LIST（与 test_neutrality_exemption_list 同口径）
  - T3 Verify 第 4 条同样改写（packs/garage/ 范围）

  这是 r2 critical 修复时漏改的最后一公里 —— Acceptance 已分层但 Verify 还是旧 wording。dev 阶段就算实施者照 Acceptance 做，跑 Verify 命令也会撞墙，引起额外的"是 spec 错了还是我做错了"困惑。必须在 task 层闭合到 Verify 与 Acceptance 同口径。

#### Minor（不阻塞，但建议本轮顺手收）

- **[minor][LLM-FIXABLE][TR5][design § 11.1 INV-9 wording 残留]** design § 11.1 INV-9 行（`grep -rE '\.claude/|\.cursor/|\.opencode/|claude-code' packs/coding/ packs/writing/`）仍是 r1 版本递归 grep，与 ADR-D8-9 line 357 "验证手段从 整 packs/ 递归 grep = 0 拆为两层" 自相矛盾。建议同步收紧 INV-9 表述（拆 INV-9a SKILL.md/agent.md 范围 + INV-9b 整 packs/ 命中 ∈ EXEMPTION_LIST），与 ADR-D8-9 + spec NFR-801 三层一致。

- **[minor][LLM-FIXABLE][TR2][task 测试基线数字内部不一致]** task plan 内 596 / 598 两个数字混用：
  - T4c Acceptance line 367 + Verify line 386：`≥ 598`（正确，对应 5 个新测试文件）
  - T4c "完成条件" line 388：`≥ 596`（残留旧值；应同步为 ≥ 598）
  - § 7 完成定义 #4 line 451：`≥ 596 passed（586 baseline + 4 个新文件 sentinel/集成测试 + 若干）`（残留旧值；应同步为 ≥ 598 + 5 个新文件）
  
  hf-test-driven-dev / hf-completion-gate 看 task 完成条件时会困惑究竟是 596 还是 598。

- **[minor][LLM-FIXABLE][TR2][EXEMPTION_LIST 数字 4 vs 5 措辞不准]** task line 364 写 "EXEMPTION_LIST 常量（5 文件）"，但 spec CON-803 详细说明 enum + design ADR-D8-9 表都是**4 行**实测（其中 `packs/writing/README.md` 是条件性 "（如 T2 决策搬迁）"——而 T2 Files line 230 是新写 `packs/writing/README.md`，新写的内容默认不会含宿主字面值，所以这条豁免实际可能用不上）。建议把"5 文件"改为"4 文件（packs/writing/README.md 视 T2 实际撰写内容可选加入）"或"≤ 5 文件"；并在 EXEMPTION_LIST 测试加注 "若 packs/writing/README.md 不含宿主字面值，则不需进入豁免清单"。这是 wording 精度问题，不阻塞 dev。

### 关键 r3 维度判断

| 关键问题 | 判定 |
|---|---|
| spec NFR-801 / CON-803 enum 已 amend | ✅ 完全闭合 |
| design ADR-D8-9 候选对比 + 选定 + 豁免清单 + 守门测试 | ✅ 完全闭合 |
| design § 11.1 INV-9 wording 与 ADR-D8-9 一致 | ❌ 残留 r1 递归 grep wording（minor） |
| design § 13.1 测试文件 4 → 5 件套 | ✅ 闭合（含 test_neutrality_exemption_list） |
| task T2/T3 Acceptance 分层 (SKILL.md 严格 + meta 豁免) | ✅ 闭合 |
| task T2/T3 Verify 命令同步分层 | ❌ 残留 r1 递归 grep（important，必修） |
| task T4c 测试种子（含 EXEMPTION_LIST 常量同步要求）| ✅ 闭合（数字 5 与 spec/design 4 微差） |
| task § 7 完成定义 / T4c 完成条件 测试基线数字 | ❌ 596/598 内部不一致（minor） |
| task § 8 / § 9 router 重选规则 | ✅ 完全闭合，二分清晰 |
| task INV-2 范围扩展到 writing family prompts/ | ✅ 闭合 |

### 下一步

`hf-tasks` — 父会话按 r3 1 important + 3 minor 做最后定向回修：

1. **(important)** T2 Verify line 240 + T3 Verify line 278 改为 `find ... SKILL.md/agent.md ... | wc -l == 0` + 追加豁免清单 grep 守门
2. **(minor)** design § 11.1 INV-9 表行同步收紧（拆 INV-9a + INV-9b 或加 ADR-D8-9 注脚）
3. **(minor)** task plan T4c line 388 完成条件 + § 7 line 451 完成定义 #4 数字同步为 ≥ 598 + "5 个新文件"
4. **(minor)** task plan T4c line 364 EXEMPTION_LIST "5 文件" 措辞精度收紧

修订完成后重派 hf-tasks-review 复审 r4，预期 r4 通过率高，可一轮闭合。

### 交接说明

- 结论 `需修改`，不进入"任务真人确认" approval step。
- `next_action_or_recommended_skill = hf-tasks`。
- `needs_human_confirmation = false`。
- `reroute_via_router = false`（不存在 route/stage/profile/上游证据冲突级阻塞——上游 spec/design 已批准 r2，本轮 important 残留是 r2 修复时 task Verify 没同步收紧的 wording-only gap）。
- 不修改 spec / design / tasks 文档；不修改 task-progress.md；不 git commit / push。

---

## 复审 r4

- 复审日期: 2026-04-23
- 复审输入: 父会话 commit `a1d1735` 对 r3 1 important + 3 minor 完成的定向回修
- 复审范围: 逐项校验 r3 4 项 finding 闭合度；判断 spec / design / task 三层在 grep 范围 + 测试数量 + EXEMPTION_LIST 是否一致

### r4 结论

**通过**

理由：r3 1 important（T2/T3 Verify wording）+ 3 minor（design § 11.1 INV-9 / 596 vs 598 / EXEMPTION_LIST 数字精度）已**全部闭合**或 wording 已收紧到不阻塞 dev；spec / design / task 三层在 grep 范围、测试数量基线、INV-9 分层守门、EXEMPTION_LIST 文件路径上语义完全一致；从 r1 到 r4 共 4 轮迭代，task plan 已稳定到可进入"任务真人确认" approval step + hf-test-driven-dev 实施。

### 维度评分（r4）

| 维度 | r3 评分 | r4 评分 | 备注 |
|---|---|---|---|
| TR1 可执行性 | 8 | 8 | 不变 |
| TR2 任务合同完整性 | 7 | 9 | T2/T3 Acceptance + Verify 同口径分层；T4c 完成条件 / § 7 完成定义 数字统一为 ≥ 598 |
| TR3 测试设计种子 | 9 | 9 | 不变 |
| TR4 依赖与顺序 | 9 | 9 | 不变 |
| TR5 追溯覆盖 | 8 | 9 | design § 11.1 INV-9 与 ADR-D8-9 三层一致 |
| TR6 Router 重选就绪度 | 9 | 9 | 不变 |

无关键维度 < 6；最低 8/10，所有维度 ≥ 8 — 通过门槛。

### 逐条 r3 finding 闭合度判定

| r3 finding | 严重度 | 闭合判定 | 证据 |
|---|---|---|---|
| important: T2/T3 Verify 仍是 r1 递归 grep | important | **已闭合** | T2 Verify line 240 改为 `find packs/writing/ \( -name 'SKILL.md' -o -path '*/agents/*.md' \) -exec grep -lE ... \; \| wc -l == 0` + line 241 meta 文件豁免守门 ⊆ ADR-D8-9 EXEMPTION_LIST；T3 Verify line 279-280 同口径改造 + 显式 enum 预期豁免命中（anthropic-best-practices.md + CLAUDE_MD_TESTING.md）|
| minor: design § 11.1 INV-9 wording 残留 | minor | **已闭合** | design § 11.1 INV-9 行改为 (a) 强约束 SKILL.md/agent.md grep + (b) meta 豁免守门 整 packs/ 命中 ⊆ ADR-D8-9 EXEMPTION_LIST；责任 commit 扩到 T1a/T1b/T2/T3/T4c |
| minor: 596 vs 598 不一致 | minor | **已闭合** | task § 7 完成定义 #4 line 453 改为 `≥ 598 passed（586 baseline + 5 个新文件）`；T4c 完成条件 line 390 改为 `4 测试文件全部 GREEN + 整体测试基线 ≥ 598 + commit 落地`；全文 grep 596 = 0 命中 |
| minor: EXEMPTION_LIST "5 文件" 措辞精度 | minor | **基本闭合**（wording 收紧 + 不阻塞 dev；存在 1 处数字精度小偏差） | task T4c line 366 改为 "EXEMPTION_LIST 常量（4 个固定豁免文件 + 1 个条件性 `packs/writing/README.md`，T2 实施时若决策搬迁则启用）"；spec/design enum 实际是 4 行（3 固定 + 1 条件性）—— task 写 "4 + 1 = 5" 与 spec/design "4 行（含 1 条件性）" 之间存在数字偏差但语义清晰（条件性的含义已显式给出），dev 实施时按 ADR-D8-9 权威源维护 frozenset 不会困惑 |

### 三层一致性判定（r4 重点）

| 维度 | spec | design | task | 一致性 |
|---|---|---|---|---|
| **NFR-801 grep 范围** | NFR-801 验收 #1：`find packs/coding/ packs/writing/ packs/garage/ \( -name 'SKILL.md' -o -path '*/agents/*.md' \) ...` | INV-9 (a)：同 spec | T2/T3 Verify line 240/279：同 spec（按 pack 范围分别跑）| ✅ 三层一致 |
| **meta 豁免守门** | NFR-801 验收 #3：命中行所属文件必须 ∈ design ADR-D8-9 enumerate 的豁免清单 | INV-9 (b)：整 packs/ 命中 ⊆ EXEMPTION_LIST | T2 Verify line 241 + T3 Verify line 280：同 design（按 pack 范围检查）| ✅ 三层一致 |
| **测试文件数** | （不在 spec 直接约束，由 design 派生）| § 13.1 表：5 个测试文件（drift + full_packs_install + packs_garage_extended + dogfood_layout + neutrality_exemption_list）| § 7 #4：5 个新文件；T4c Acceptance：4 个新文件（T4c 内）+ T1c sentinel（独立 task）= 整 cycle 5 | ✅ 三层一致（视角差异已由 § 7 整 cycle 视角解释）|
| **测试基线数字** | （不在 spec）| § 13.1：≥ 586 baseline + 5 = 至少 591；具体测例数派生自实施 | § 7 #4：≥ 598；T4c 完成条件：≥ 598；T4c Verify：≥ 598 | ✅ 三层一致 |
| **EXEMPTION_LIST 文件路径** | CON-803 详细说明 line 416-419：4 行 enum（含 1 条件性）| ADR-D8-9 line 347-350：4 行表（含 1 条件性）| T4c line 366：4 固定 + 1 条件性 = 5 路径；EXEMPTION_LIST 常量与 design 表手动同步 | ⚠️ 数字精度偏差 1（spec/design 4 行 = 3 固定 + 1 条件；task 写 "4 固定 + 1 条件 = 5"）；语义已显式给出"条件性"含义；dev 按 ADR-D8-9 权威源维护 frozenset 即可，不阻塞 |
| **§ 8 router 串行规则** | （不在 spec）| （不在 design）| § 8 + § 9：依赖图层面互不依赖 vs 调度并发二分；router 串行选 T1c → T2 → T3 | ✅ task 内一致 |
| **fail-first sentinel 顺序** | （由 design § 14 F2 + § 11.1 INV-3 派生）| § 14 F2 + § 11.1 INV-3 | T1c Sub-acceptance Step 1/2/3 + PR walkthrough RED 截图证据要求 | ✅ 三层一致 |

### r4 残留 finding（不阻塞）

无 critical / important 残留。剩余 1 个 minor 数字精度偏差（EXEMPTION_LIST 4 vs 5 表述），不阻塞 dev：实施者按 spec CON-803 enum + design ADR-D8-9 表（权威源）维护 frozenset，4 个文件路径足够（含 1 条件性的 packs/writing/README.md）；如果 dev 阶段实测 packs/writing/README.md 不含黑名单字面值，frozenset 可不收录该路径，对 sentinel 测试效果无影响。建议在 hf-test-driven-dev 实施 T4c `test_neutrality_exemption_list.py` 时顺手把数字描述统一（task → spec/design 同步），但作为 r4 阻塞理由不成立。

### 关键 r4 通过判断

| 关键问题 | 判定 |
|---|---|
| spec NFR-801 / CON-803 amend 内部一致 | ✅ |
| design ADR-D8-9 + INV-9 + § 13.1 测试 5 件套内部一致 | ✅ |
| task T2/T3 Acceptance 与 Verify 同口径 | ✅ |
| task § 7 完成定义 / T4c 完成条件 数字一致 | ✅ |
| spec / design / task 三层在 grep 范围 / 测试基线 / EXEMPTION_LIST 语义一致 | ✅（EXEMPTION_LIST 数字精度偏差 1，语义清晰，不阻塞） |
| router 重选规则唯一可重放 | ✅ |
| critical 红线（CON-801 / CON-803 / NFR-801 / NFR-802）守门齐备 | ✅ |
| fail-first / sentinel 测试设计种子充分 | ✅ |

满足 hf-tasks-review 通过条件。task plan 可进入"任务真人确认" approval step，approval 后由 router 派发 T1a 进入 hf-test-driven-dev 实施。

### 下一步

`任务真人确认` — 通过 approval step（auto 模式下父会话写 `docs/approvals/F008-tasks-approval.md`；interactive 模式下等待真人）；approval 落地后由 hf-workflow-router 派发 T1a 进入 hf-test-driven-dev。

### 交接说明

- 结论 `通过`，进入"任务真人确认" approval step。
- `next_action_or_recommended_skill = 任务真人确认`。
- `needs_human_confirmation = true`（auto 模式下父会话承接写 approval record，interactive 模式下等真人确认）。
- `reroute_via_router = false`。
- 不修改 spec / design / tasks 文档；不修改 task-progress.md；不 git commit / push。
- 留 1 minor 数字精度偏差（EXEMPTION_LIST 4 vs 5）作为 hf-test-driven-dev T4c 实施时顺手收尾项，不在本评审作为阻塞理由。
