# Design Review — F014 r1 (Workflow Recall)

- 日期: 2026-04-26
- 审阅人: hf-design-review reviewer subagent (Cursor Agent task)
- 范围: `docs/designs/2026-04-26-workflow-recall-design.md` (commit `e5425ba`)
- 上游 spec: `docs/features/F014-workflow-recall.md` r2 (APPROVED) + `docs/approvals/F014-spec-approval.md`

## Verdict: CHANGES_REQUESTED

设计整体锚定已批准 F014 r2 (顶级包、lazy cache、5 点 hook 策略、step 3.5 additive、Counter 与 Im-4 子序列、INV/CON 清单), 但 ADR-D14-3 与 ADR-D14-6 与仓库事实不一致, 且 ExperienceRecord 写入点与 r2 的"5 个 caller"清单存在可验证缺口, 需在 design r2 修正或显式产品裁决 + 文档化后再过 gate.

## Findings (critical → important → minor → nit)

### Critical

**Cr-1 (USER-INPUT) — EI 写入路径多于 r2 锁定的 5 处**

- **依据**: 已批准 spec FR-1404 / Cr-1 与 `docs/approvals/F014-spec-approval.md` 均锁定 5 个写入路径; 但 `rg` 在 `src/garage_os` 中除上述路径外, **`cli.py` L1172 在 skill 执行记录路径仍调用 `experience_index.store(experience_record)`**.
- **影响**: 若仅按设计 5 点 hooks, `garage run <skill>` 后写入的 experience 不触发 `WorkflowRecallHook.invalidate`, cache 与 EI 可长期不一致 (需 `--rebuild-cache` 或别次写入才失效).
- **设计引用**: 设计 ADR-D14-3 caller 表无该路径; 与 spec "5 caller" 一一性冲突.
- **r2 USER-INPUT 决策需求**: (a) 第 6 点接入 + 同步修订 spec / approval; 或 (b) 显式排除该路径 + 用户可接受语义 (例如 skill execution record 不纳入 workflow recall, 因为它记录的是 skill 调用本身而非 cycle 级 task path).

**Cr-2 (LLM-FIXABLE) — ADR-D14-3 caller 表 `ingest/pipeline.py` 行事实错误**

- **依据**: `src/garage_os/ingest/pipeline.py` 在 SkillMining 位置 (~ L119-133) **没有** `experience_index.store`; 该段在 `orchestrator.extract_for_archived_session_id` 之后调 `SkillMiningHook`. 实际 ingest pipeline 不直接写 ExperienceRecord (依赖 archive_session 链 + extraction 经 publisher 间接写).
- **影响**: 设计 §4 表将此处写成 "experience_index.store 后" 不成立; 实现者会找错行.
- **r2**: 改为 "同 F013-A SkillMiningHook 接入点, 在 extraction 后 try/except 调 `WorkflowRecallHook.invalidate`" 或等价表述. 实际可省略本接入点 (因为 ingest 路径下游通过 publisher invalidate 自然触发, 不重复挂).

### Important

**Im-1 (LLM-FIXABLE) — ADR-D14-3 publisher.py 仅标 store 行**

- **依据**: `src/garage_os/memory/publisher.py` ~ L136-143: 新记录 `self._experience_index.store(record)` (L138), 已存在则 update; `ExperienceIndex.update` (`experience_index.py` ~ L124-137) **内部再调 `self.store(record)` (L137)**.
- **影响**: 在 publisher 138 行后挂 hook 会**漏掉 update 分支** (对已有 `record_id` 的再发布); 但因 update 内部调 store, 若我们改在 ExperienceIndex.store 末尾挂 → 会破 INV-F14-4 (改 F004 内部行为). 取舍:
  - (a) publisher 的 store + update 两分支各一处 best-effort hook
  - (b) 仅 publisher 顶层一处 hook (在 if-else 之外, 如 L143 后)
  - (c) ExperienceIndex.store 内部挂 hook (违 INV-F14-4)
- **r2 决策**: 选 (b) — publisher.py 顶层挂一处 (L143 后), 覆盖 store + update 两路径.

**Im-2 (LLM-FIXABLE) — ADR-D14-6 + Im-3 dogfood SHA "三处" 与 baseline JSON 不一致**

- **依据**: 当前 `tests/adapter/installer/dogfood_baseline/skill_md_sha256.json` **只有** 2 个 hf-workflow-router 键: `.claude/skills/hf-workflow-router/SKILL.md` + `.cursor/skills/hf-workflow-router/SKILL.md` (`grep -c 'hf-workflow-router' = 2`). **无** `packs/coding/skills/hf-workflow-router/SKILL.md` 键. `test_dogfood_invariance_F009.py` 对比的是 `install_packs` 后 `.claude` / `.cursor` 下文件, 不是 packs 源文件本身.
- **影响**: 设计 §6 / §8 T5 / Im-3 r2 写 "3 处 hash (源 + .cursor + .claude)" 与 baseline 结构不符; T5 易误操作.
- **r2**: 改述为 "改 packs 源文件后, 跑 `bash scripts/setup-agent-skills.sh` + `garage init --hosts cursor,claude` 重生 `.cursor/` + `.claude/` mirror; 然后更新 baseline JSON 中 **2 个** hf-workflow-router 键 hash. 不追踪 `packs/` 源 hash" (与 F009 既有约定一致).

**Im-3 (LLM-FIXABLE) — FR-1401 "平均耗时" 与 WorkflowAdvisory.avg_duration_seconds 语义**

- **依据**: spec FR-1401 (~ L151) 写 "桶内所有 record 的 `duration_seconds` 平均"; 设计 §11 `WorkflowAdvisory` (~ L275-298) 为**每条 advisory 一个** `avg_duration_seconds`.
- **影响**: 多 advisory 时是否共用同一桶均值, 还是 per-sequence mean 不同 → 实现 / 验收口径歧义.
- **r2 决策**: per-sequence mean (即每个 advisory 是 "桶内匹配该 skills 序列的 record 子集"的平均). 这与 spec FR-1401 一致 (因为 advisory 本身就是序列粒度), 只是设计需明确.

### Minor

**Mi-1 — T5 测试数量 spec § 9.1 写 6 vs 设计 §8 表写 5**

- **依据**: spec §9.1 (~ L327-329) "T5: ... + 6 测试" vs 设计 §8 表 "T5: ... + 5 测试". 实施前在 hf-tasks 与 design r2 统一即可.
- **r2**: 设计 §8 改为 5 测试 (与设计内 §14 验证策略一致); spec §9.1 是 preview, 不必 backport.

### Nit

**Ni-1 — CON-1402 "T1-T5 全 stdlib" 表述**

- 设计 §10 CON-1402 守门 (~ L268-269): "T1-T5 全 stdlib"
- **问题**: 新模块必然 import 本库 `garage_os`; 严格说不算 stdlib
- **r2**: 改为 "无新第三方依赖; `pyproject.toml + uv.lock` diff = 0" (与 spec CON-1402 一致)

**Ni-2 — Verdict 计数元数据**

- 本记录 Critical/Important/Minor 为上述编号独立计数; Critical 项含 1 USER-INPUT + 1 LLM-FIXABLE.

## Recommendations for r2

1. **Cr-1**: auto mode 默认锁选项 (b) — 显式排除 `cli.py:1172` (skill 执行 record), 因为它记录的是 skill 调用本身, 不是 cycle 级 task path; advisory 应基于 cycle-level ExperienceRecord (来自 publisher / cli experience add / archive session). 同步修订 spec FR-1404 caller 表 + approval trace.
2. **Cr-2**: ADR-D14-3 caller 表 `ingest/pipeline.py` 行删除该接入点 (因为 ingest 路径下游通过 publisher invalidate 自然触发); 或保留并写明 "同 F013-A SkillMiningHook 接入点, 在 extraction 后 try/except".
3. **Im-1**: ADR-D14-3 publisher.py 改为 "在 publisher.py L143 后挂顶层 hook (覆盖 store + update 两路径)"; 不在 138 / 137 行重复挂.
4. **Im-2**: ADR-D14-6 + Im-3 改述为 "更新 baseline JSON 中 2 个 hf-workflow-router 键 (`.claude/`, `.cursor/`); 不追踪 packs/ 源 hash"; 与 F009 既有约定一致.
5. **Im-3**: WorkflowAdvisory.avg_duration_seconds 语义明确为 per-sequence mean (advisory 是 skills 序列粒度).
6. **Mi-1**: 设计 §8 T5 测试数 5 (与 §14 一致).
7. **Ni-1/Ni-2**: 措辞调整.

## 通过条件

- 无对已批准 F014 spec 的不知情偏离 (尤其 Cr-1 多 caller 与 F009 dogfood 真实流程)
- ADR-D14-3 每行可用 grep 在目标文件复现 (或脚注 "无直写 EI 时以 XXX 为锚")
- INV/CON: 在修订 caller 与 publisher 后, CON-1401 仍为 "不改 ExperienceIndex 签名的 try/except 外挂" 可成立
- design r2 通过评审后可进入 hf-tasks

## 计数

- **Critical: 2** (1 USER-INPUT + 1 LLM-FIXABLE)
- **Important: 3** (全 LLM-FIXABLE)
- **Minor: 1**
- **Nit: 2**

总计 **8 finding**, 7 LLM-FIXABLE + 1 USER-INPUT.

## ADR 交叉验证记录 (供审计)

| ADR | 结论 | 证据 |
|-----|------|------|
| D14-1 顶级包 | 与现有布局一致 | `knowledge/`, `memory/`, `sync/`, `skill_mining/` 平级子包 |
| D14-2 cache 单文件 JSON | 与 F013-A `.last-scan.json` 同 pattern | `src/garage_os/skill_mining/pipeline.py` |
| D14-3 多 caller hook | **需修订** caller 表 | spec / 代码 grep 多于 5 处 (Cr-1) + ingest/pipeline 行错 (Cr-2) + publisher 漏 update 分支 (Im-1) |
| D14-4 Counter on tuple(skill_ids) | 成立 | `collections.Counter` stdlib; tuple hashable; --skill-id 子序列 BDD 8.6 一致 |
| D14-5 inline status | 与 F013-A 一致 | `cli.py::_print_skill_mining_status` |
| D14-6 step 3.5 additive | 成立 | `hf-workflow-router/SKILL.md` ### 1-10 步 |
| D14-6 dogfood SHA "三处" | **需修订** | baseline JSON 仅 2 keys (Im-2) |
| D14-7 T1-T5 拆分 | 与 spec § 9 1:1 | 数字微调 (Mi-1) |
