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
