# Test Review — F008 Garage Coding Pack 与 Writing Pack

- 状态: r1 通过
- 日期: 2026-04-23
- Reviewer: hf-test-review subagent (独立 reviewer)
- Cycle: F008
- 关联规格: `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准 r2）
- 关联设计: `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md`（已批准 r2）
- 关联任务计划: `docs/tasks/2026-04-22-garage-coding-pack-and-writing-pack-tasks.md`（已批准 r4）
- 关联前置评审: spec-review r2 通过 / design-review r2 通过 / tasks-review r4 通过
- 评审 skill: `packs/coding/skills/hf-test-review/`（rubric: TT1-TT6 + TA1-TA5）

## Precheck

- 稳定实现交接块 ✓ — task-progress.md `Current Stage=hf-test-review`，`Current Active Task=无`，9/9 task commit 落地
- 9 sub-commit 与 task plan 一一对应 ✓ — `git log --oneline` 验证 T1a/T1b/T1c/T2/T3/T4a/T4b/T4c/T5 9 个 commit hash 全部在 `cursor/f008-coding-pack-and-writing-pack-bf33` 分支
- 测试资产可定位 ✓ — 5 个新增测试文件在 `tests/adapter/installer/`；1 个 carry-forward 修复在 `tests/test_cli.py:3042`
- route/stage/profile 一致 ✓ — `Workflow Profile=full`，`Execution Mode=auto`，stage 已稳定推进到 review 链路
- manual smoke 已归档 ✓ — `/opt/cursor/artifacts/` 含 5 个 artifact：`f008_dogfood_init.log`、`f008_smoke_first.log`、`f008_smoke_second.log`、`f008_smoke_manifest_excerpt.json`、`f008_smoke_claude_tree.txt`
- INV-5 守门 ✓ — `git diff main..HEAD -- src/garage_os/ pyproject.toml uv.lock` 输出 0 行
- 测试基线确认 ✓ — 本地实测 `python3 -m pytest tests/ -q` → **633 passed in 26.05s**（F007 baseline 586 + F008 增量 47, 0 退绿）
- 既有 30 个 installer 测试 0 改写 ✓ — `git log main..HEAD -- tests/adapter/installer/` 全部为 `add` 动作；既有 `test_neutrality.py` 仍 100% 通过且自动 parametrize 拾取了 28 个新加 SKILL.md

precheck PASS，进入正式 6 维评审。

## 结论

通过

**理由**：

1. 所有关键维度 ≥ 6/10，6 维均分 7.67/10
2. 9 INV 全部有覆盖（INV-5 由 git diff 守门、INV-7 由 manual smoke walkthrough 守门，design § 11.1 已显式标注，合规）
3. F008 实施期 5 个新增测试文件 (19 个新增 test function) + 现有 `test_neutrality.py` 自动 parametrize 28 个新 SKILL.md，构成完整 fail-first 守门体系
4. 633 测试本地实测全绿，0 退绿，0 改写既有 installer 测试
5. spec § 4.2 6 条红线全部有自动化或 walkthrough 守门
6. design ADR-D8-9 双层 EXEMPTION_LIST 守门到位，未来新增 meta 文件命中触发 RED 强制三层同步（ADR + spec + 测试常量）
7. 文档级提示边界 (ADR-D8-4) 在测试中正确反映：未误以为下游宿主 references/ 子文件可达

## 多维评分

| 维度 | 得分 | 评语 |
|---|---|---|
| **TT1** fail-first 有效性 | 7/10 | T1c sentinel test 的 RED 证据强度仅限于 commit message 文字记录的 sha256 对比（root=283b6dae… vs packs=9e523cbb…），缺 PR walkthrough 内独立 terminal artifact；但 commit message 详细可核实，工程上可重放（git revert 该 commit 即可重现 RED）。其它 sentinel/集成测试天然带 fail-first 性质：在 packs/ 未落齐时 INV-1 / INV-2 必 RED，T4c 测试一旦先于 T1-T3 落地必失败 |
| **TT2** 行为 / 验收映射 | 8/10 | 5 个测试文件覆盖 FR-801..806 关键 acceptance + 9 INV + 红线 1/2/3/4；FR-807 (文档同步) 主要靠人工 review + 部分自动化 (test_agents_md_packs_table_includes_coding_writing)；INV-7 (IDE 加载链) 由 manual smoke 承接（设计已显式标注），合规 |
| **TT3** 风险覆盖 | 7/10 | 9 INV 全部有测试守门；design § 14 F1-F7 失败模式覆盖 6/7（F2 由 INV-3、F3 由 INV-8、F4 由 INV-1==22 隐含、F1 由 PR 期间 grep 验证、F6 由实施期处理、F7 由 ADR-D8-4 文档级提示豁免）；**F5 (LICENSE 丢失) 没有自动化 assertion** — task plan T2 acceptance 列了 `test -f packs/writing/LICENSE` Verify 命令但未落 pytest 用例；LICENSE 物理存在但保护链条断了一环。NFR-803 wall-clock 测试用 symlink 不复制文件，与生产用户首次 cp packs/ 真实场景有偏差 |
| **TT4** 测试设计质量 | 8/10 | (a) `_link_packs` symlink fixture 复用 F007 既有 pattern (test_cli.py:3163)，简洁正确；(b) sentinel test 直接读仓库固定路径，design 已显式标注合规；(c) EXEMPTION_LIST 常量手动维护是 ADR-D8-9 by design；(d) 硬码 INV-1=29、coding=22、garage=3、writing=4 是预期 invariant（未来加 skill 强制三层同步）。代码风格清晰，命名 `*_INV1` / `*_FR806` / `*_红线_4` 显式带 traceability anchor |
| **TT5** 新鲜证据完整性 | 8/10 | 9 sub-commit 与 task plan 完全对齐 (T1a/T1b/T1c/T2/T3/T4a/T4b/T4c/T5)；commit message 详尽含 acceptance 命令、SHA-256 hash、增量数；633 测试 fresh 实测；5 个 manual smoke artifact 涵盖 dogfood 与 /tmp smoke 双轨；T1c RED 证据仅文字描述 (TT1 同源)；**`tests/test_cli.py:3042` carry-forward 混入 T1c drift-sync commit** 而非独立 commit，commit message 含"顺手修"声明缓解但偏离 NFR-804 "每组改动可独立 review" 精神 |
| **TT6** 下游就绪度 | 8/10 | (a) 633 测试 0 退绿 0 改写；(b) INV-4 字节级搬迁覆盖 (test_skill_byte_level_sample_INV4 用 hf-specify 抽样 + marker block 移除后 body byte-equal)；(c) 既有 `test_neutrality.py` 自动 parametrize 拾取 28 个新 SKILL.md (test_no_host_specific_terms 跑 29 次都通过)，与 ADR-D8-9 layer (a) 严格约束等价；(d) hf-code-review 阶段需评审的"内容物搬迁 + 文档 + 测试"三类 surface 都有自动化 baseline |

总均分：**46/60 = 7.67/10**

无关键维度 < 6，无阻塞性 finding。

## 发现项

按 severity 排列：

### important

无。

### minor

- [minor][LLM-FIXABLE][TT3/TA2] **F5 失败模式 (write-blog LICENSE 丢失) 缺自动化 assertion**：design § 14 F5 + spec FR-802 验收 #2 + task plan T2 acceptance 都要求 `packs/writing/LICENSE` 存在；LICENSE 物理存在 (`f0f2c05` commit 已落)，但 5 个新增测试文件中**无任何用例显式断言** `(packs/writing/LICENSE).exists()` 或与上游 SHA-256 相等。test_full_packs_install 跑 install_packs() 不会触及 LICENSE。建议在 hf-test-driven-dev 后续轮中给 test_full_packs_install.py 或 test_packs_garage_extended.py 加一个 `test_writing_license_preserved` 用例。当前未阻塞，因 LICENSE 文件物理存在且有 git 受控，但下次有人误删 LICENSE 不会被任何测试拦截。
- [minor][LLM-FIXABLE][TT5/TA5] **carry-forward `tests/test_cli.py:3042` 修复混入 T1c drift-sync commit**：F007 测试 hard-coded `manifest["installed_packs"] == ["garage"]` 在 packs/ 扩容到 3 后会退绿；改为 `"garage" in manifest["installed_packs"]` 是合理的 carry-forward 修复（与 test_subprocess_smoke_three_hosts:3144 的 regex-on-marker 同精神）。但该修复混在 `fa3d3fc f008(coding/drift-sync)` commit 中，commit message 末尾以"顺手修"提及；偏离 NFR-804 "git diff 可审计 / 任意一组改动可独立 review" 精神；理想做法是单独 commit `f008(test-cli/forward-compat): 解耦 F007 hard-coded installed_packs assertion`。当前 commit message 已显式声明，可追溯，不阻塞 code-review；建议下一 cycle 类似改动单独 commit。
- [minor][LLM-FIXABLE][TT1/TA1] **T1c sentinel test fail-first RED 证据弱**：commit `fa3d3fc` message 详细记录了 RED 状态的 root vs packs sha256 对比，但 PR walkthrough artifact 中**没有独立 RED 阶段的终端输出截图或 stash 状态 commit**。可重放路径存在 (git revert fa3d3fc 仅保留 sentinel test 即可重现 RED)，但 review 视角的"fresh 当次会话 fail-first 证据"严格说仅文字层。建议下次类似 sentinel test 引入时，可考虑两步 commit (Step 1 仅 sentinel test commit→ Step 2 反向同步 commit)，给 reviewer 提供 git-history 层的 RED→GREEN 证据。
- [minor][LLM-FIXABLE][TT4] **NFR-803 wall-clock 测试 fixture 用 symlink 不复制文件**：`test_install_packs_under_5_seconds_NFR803` 用 symlink 链接真实 packs/，实测 < 100ms 远低于 5s 上限；但生产场景下游用户首次 `cp -r packs/` 到自己仓库 + cold disk cache 会慢一些。manual smoke 实测 first 0.120s / second 0.107s 已是 SSD 实数据，可补足该测试的 fixture 偏差。建议在 test docstring 显式说明 fixture 用 symlink 选择的理由（避免后人误解为生产基准），但当前不阻塞。

## 缺失或薄弱项

- **F5 LICENSE 守门链条断一环**（minor，已列入 finding）：自动化保护缺失，靠 git 受控兜底
- **T1c RED 阶段独立 git artifact 缺失**（minor，已列入 finding）：可重放但需 reviewer 主动 git revert
- **carry-forward 与功能 commit 混合**（minor，已列入 finding）：commit message 显式声明缓解
- **NFR-803 自动化测试 fixture 偏离生产场景**（minor，已列入 finding）：manual smoke 实测兜底

均无阻塞性，可让 hf-code-review 在已知边界内做可信判断。

## 下一步

- **next_action_or_recommended_skill**: `hf-code-review`
- **needs_human_confirmation**: `false`（按 reviewer-return-contract.md：`hf-test-review` 在 `通过` 时默认 `false`，由父会话直接派发下一节点）
- **reroute_via_router**: `false`

父会话应直接派发独立 reviewer subagent 执行 `hf-code-review`，评审 F008 cycle 的内容物搬迁 + 测试 + 文档质量。本 review 已确认测试质量足够支持 code review 做可信判断。

## 记录位置

- review 记录: `/workspace/docs/reviews/test-review-F008-coding-pack-and-writing-pack.md`（本文件）

## 交接说明

### 给父会话

- 测试质量 r1 通过，无需回修
- 4 条 minor finding 全部 LLM-FIXABLE 但**不阻塞** hf-code-review；建议作为 carry-forward 在 hf-finalize 阶段或下次 cycle 处理
- 直接派发 hf-code-review，prompt 中可附本评审 4 条 minor finding 作为 reviewer 上下文

### 给 hf-code-review reviewer

代码评审重点应放在：

1. **5 个新增测试文件的代码质量**（fixture 复用、断言清晰度、命名规范、docstring 充分性）
2. **9 sub-commit 内容物搬迁的 git diff 可审计性**：是否每个 commit 自描述清晰、是否如 task plan 所述纯 cp -r + 最小宿主中性化替换（CON-803 例外 #2 ≤ 3 行 diff）
3. **carry-forward `tests/test_cli.py:3042` 修复的合理性**：本 review 已认定合理 (与 test_subprocess_smoke_three_hosts:3144 同精神)，code-review 可二次确认
4. **packs/{coding,writing,garage}/README.md 与 packs/coding/pack.json + packs/writing/pack.json + packs/garage/pack.json 的 schema 与文档一致性**
5. **`docs/principles/skill-anatomy.md` 反向同步后字节内容**（非测试范畴，但是 ADR-D8-3 的实施产物）
6. **AGENTS.md 局部刷新内容**（T4b commit）

### 给后续 reviewer 链

- hf-traceability-review: 关注 spec → design → tasks → 实施 → 验证 全链路追溯，特别是 ADR-D8-9 EXEMPTION_LIST 三层同步链 (ADR + spec + 测试常量)
- hf-regression-gate: NFR-802 测试基线 ≥ 633 ✓、INV-5 src/garage_os/ 零修改 ✓、INV-6 git status 干净（注：当前 workspace 有 `.claude/` 与 `.garage/config/host-installer.json` untracked，是 dogfood smoke 产物，已被 .gitignore 排除是正确状态；regression-gate 应在 clean checkout 上验证）
- hf-completion-gate: F5 LICENSE 自动化守门缺失是否需要在 cycle 内补，还是作为下个 cycle carry-forward
- hf-finalize: RELEASE_NOTES F008 段 5 个 TBD 占位字段需用 manual smoke 实测数据填充（design § 18 #2 已说明）

---

## 结构化返回

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-code-review",
  "record_path": "docs/reviews/test-review-F008-coding-pack-and-writing-pack.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][TT3/TA2] F5 失败模式 (packs/writing/LICENSE 存在) 缺自动化 assertion，物理文件存在但保护链断一环",
    "[minor][LLM-FIXABLE][TT5/TA5] tests/test_cli.py:3042 F007 hard-coded assertion carry-forward 修复混入 T1c drift-sync commit，commit message 已声明但偏离 NFR-804 单独可审计精神",
    "[minor][LLM-FIXABLE][TT1/TA1] T1c sentinel test 的 RED 阶段证据仅 commit message 文字记录的 sha256 对比，缺独立 PR walkthrough artifact (可 git revert 重放)",
    "[minor][LLM-FIXABLE][TT4] NFR-803 wall-clock 自动化测试 fixture 用 symlink 不复制文件，与生产首次 cp packs/ 场景偏差，由 manual smoke 实测兜底"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT3",
      "summary": "F5 失败模式 (packs/writing/LICENSE 存在) 缺自动化 assertion"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT5",
      "summary": "test_cli.py:3042 carry-forward 修复混入 T1c drift-sync commit，未独立 commit"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT1",
      "summary": "T1c sentinel test fail-first RED 证据仅 commit message 文字层，缺独立 PR walkthrough artifact"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TT4",
      "summary": "NFR-803 自动化测试 fixture 用 symlink 不复制文件，与生产场景偏差，依赖 manual smoke 兜底"
    }
  ]
}
```
