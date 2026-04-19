# Tasks Review — F006 Garage Recall & Knowledge Graph

- 评审对象: `docs/tasks/2026-04-19-garage-recall-and-knowledge-graph-tasks.md`（草稿）
- 上游规格: `docs/features/F006-garage-recall-and-knowledge-graph.md`（已批准，r2 通过）
- 上游设计: `docs/designs/2026-04-19-garage-recall-and-knowledge-graph-design.md`（已批准 r1）
- 上游 approval evidence:
  - `docs/approvals/F006-spec-approval.md`
  - `docs/approvals/F006-design-approval.md`
- Workflow: profile=`standard`, mode=`auto`, isolation=`in-place`, branch=`cursor/f006-recommend-and-link-177b`
- Reviewer: hf-tasks-review subagent
- Date: 2026-04-19

---

## Precheck

| 项 | 结果 |
|----|------|
| 任务计划稳定可定位 | ✅ 单文件、`草稿` 状态、5 个任务 + queue projection 完整 |
| 上游 spec approval evidence 可回读 | ✅ `F006-spec-approval.md` 引用 r2 review 通过 |
| 上游 design approval evidence 可回读 | ✅ `F006-design-approval.md` 引用 r1 review 通过 + 3 minor 已 inline 收敛 |
| route/stage/profile 一致 | ✅ task-progress.md 显示 `Current Stage: hf-tasks`, `Next Action: hf-tasks-review` |
| 测试 baseline 451 可机器验证 | ✅ `python -m pytest tests/ -q --collect-only` 实测 451 |
| 触碰文件现实 | ✅ `src/garage_os/cli.py` 当前 1371 行（F005 完成后），新增 6 handler/helper + 3 subparser 增量 ~250 行可控 |

Precheck 通过，进入正式审查。

---

## 多维评分（每维 0-10）

| ID | 维度 | 分 | 关键依据 |
|---|---|---|---|
| TR1 | 可执行性 | 9 | 所有任务都是单一 commit 闭环；T1 略大但显式承担两个独立 helper 且每个 helper 各 5+ acceptance；无 "实现某模块" 式模糊任务 |
| TR2 | 任务合同完整性 | 9 | 每个任务都具备目标 / Acceptance / Verify / 依赖 / Risk / Files；多数 acceptance 直接到字段断言级（`version=2`、`source_artifact="cli:knowledge-link"`、stdout 文案 FMT.format 命中等） |
| TR3 | 验证与测试设计种子 | 9 | 每任务点名了具体 test class 名（`TestResolveKnowledgeEntry` / `TestRecommend` / `TestKnowledgeLink` / `TestKnowledgeGraph` / `TestRecallAndGraphCrossCutting`）+ 列出 happy / boundary / error 三类用例；T5 cross-cutting 把 8 个 `--help` 断言 / smoke / source-marker 全部预先编排 |
| TR4 | 依赖与顺序正确性 | 10 | T2/T3/T4 → T1 / T5 → T1-T4 与设计 §14 完全一致；queue projection 每行的 next-ready 集与依赖图交叉一致；无循环依赖 |
| TR5 | 追溯覆盖 | 9 | §4 trace 表覆盖 FR-601~608 / NFR-601~605 / CON-601~606 / ADR-601~603 / 设计 §10/§13.2 用例 1-26；唯一可识别的小空白见 finding F-1（OQ-607 `Source:` 行未单列 acceptance） |
| TR6 | Router 重选就绪度 | 9 | §6.1 queue projection 表显式 / §6.2 唯一 Active Task 选择规则按优先级 → 编号兜底 / §6.3 依赖图与表交叉一致，router 可冷读重选 |

无任何关键维度 < 6。

---

## 发现项

- [minor][LLM-FIXABLE][TR5] **F-1 — `recommend` 输出未声明 `Source:` 行 acceptance**：spec OQ-607 明确 "`recommend` 在 `Match:` 行后增 `Source: <session>`（仅当非空）"。T2 acceptance 列出 `[DECISION]`、`ID:`、`Score:`、`Match:` 4 个 stdout 断言但未列 `Source:` 行；建议在 T2 happy path acceptance 增 1 条 "experience entry 的 `source_session` 非空时 stdout 含 `Source: <session>`，为空时不出现"，避免实现阶段把 spec OQ-607 漏掉。可在 hf-test-driven-dev 阶段顺手补，不阻塞通过。

- [minor][LLM-FIXABLE][TR5] **F-2 — T3 重复 link 路径未显式断言 `source_artifact` 仍被覆写**：design §10.2 mermaid 显示重复 link 分支也走 `update(entry)` 且 set `source_artifact="cli:knowledge-link"`；T3 acceptance 在 "重复 link" 用例只断言 `Already linked` 与 version +1，未断言 `source_artifact` 在重复路径同样被设为 `cli:knowledge-link`。FR-607 spec 验收是基于 happy path 的，但实现若两条分支分别处理 source_artifact 容易遗漏一边。建议在 hf-test-driven-dev 阶段补一条断言，不阻塞通过。

- [minor][LLM-FIXABLE][TR5] **F-3 — T1 `_recommend_experience` 返回项未对 `source_session` 字段单列断言**：spec FR-602 形状契约含 `source_session: record.session_id or None`。T1 acceptance 只到 `entry_type == "experience"` 与 `title 非空`，未对 `source_session` 字段做断言。combined 与 F-1 一并补即可。

- [minor][LLM-FIXABLE][TR3] **F-4 — T2 未显式列出 `skill_name_only` fallback 的统一打印断言**：design §10.1 mermaid Note 明确说 `RecommendationService.recommend()` 可能返回 `match_reasons=["skill_name_only"]` + `score=0.1` 的 fallback 项，CLI 应 "uniformly" 打印为同一 `[TYPE] title / ID / Score / Match` 块。T2 acceptance 未单列这条用例。属于 hf-test-driven-dev 阶段补 1 条单测即可解决。

- [minor][LLM-FIXABLE][TR2] **F-5 — NFR-602 verify 用 `git diff main..` 在当前 branch 不严谨**：T5 verify 写 `git diff main -- pyproject.toml`，但当前实际工作分支 `cursor/f006-recommend-and-link-177b` 与 `main` 之间可能含 F005 commits（已合入主线后无碍；若未合入则会引入 noise）。建议在 hf-test-driven-dev 阶段把比较锚点改为 "本 cycle 起点 commit" 或 "F005 终态 commit"，不阻塞通过。

---

## 缺失或薄弱项

- 上述 5 条均为 minor LLM-FIXABLE，可在实现阶段（hf-test-driven-dev 的测试设计种子展开时）一并吸收，不需要回 hf-tasks 重写。
- F006 task plan 未要求每任务前置 TestDesignApproval 步骤——此处与 F005 task plan（每任务有 `TestDesignApproval` 段）略有差异，但 standard profile 不强制；plan 已在每任务 acceptance 内列出测试用例清单，等同于 inline test design seed。符合 SKILL.md "F006 task plan handles test-design inline (per F005 precedent), do not demand per-task test design approvals"。

---

## 结论

**通过**

理由：

1. 6 个评审维度均 ≥ 9/10，全部高于通过阈值 6。
2. INVEST 全部满足：每任务 Independent（依赖图清晰，T2/T3/T4 互不耦合）、Estimable（单 commit 闭环 + 行数可估）、Small（每任务触碰文件 ≤ 4 个）、Testable（acceptance 直接到字段 / stdout / exit-code）。
3. 追溯矩阵覆盖所有 FR / NFR / CON / ADR / 设计 §10 / §13.2 用例 1-26，无 orphan task。
4. 依赖图正确无环；queue projection 表与 §6.2 active task 选择规则唯一，router 可稳定重选。
5. 5 条 minor finding 全部 LLM-FIXABLE 且可在 hf-test-driven-dev 阶段吸收，不影响计划本身可执行性。

---

## 下一步

`任务真人确认`（auto mode 下 reviewer 设 `needs_human_confirmation=true`，由编排层在 approval step 写 approval record；通过后可进入 `hf-test-driven-dev` 起 T1）。

---

## 记录位置

- 本评审记录: `docs/reviews/tasks-review-F006-recall-and-knowledge-graph.md`

---

## 交接说明

- `任务真人确认`：本结论为 `通过`；auto mode 下编排层在 approval step 写 approval record（建议路径 `docs/approvals/F006-tasks-approval.md`），随后进入 `hf-test-driven-dev` 实现 T1（`_resolve_knowledge_entry_unique` + `_recommend_experience` 两个 helper）。
- 5 条 minor finding 在 hf-test-driven-dev 阶段的测试设计展开里顺手吸收即可，无需回 `hf-tasks`。
