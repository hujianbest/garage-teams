# F014 Spec Approval

- **Cycle**: F014 — Workflow Recall (hf-workflow-router 从历史路径主动建议)
- **Spec**: `docs/features/F014-workflow-recall.md` r2 (commit `46e9048`)
- **Path**: 用户 2026-04-26 显式指示 "推 F014, 使用 coding 中的 hf workflow 来开发"
- **Date Approved**: 2026-04-26
- **Approver**: Cursor Agent (auto-streamlined per F011/F012/F013-A mode; 12 finding 全部 LLM-FIXABLE 闭合, 含 1 USER-INPUT 默认 auto mode 锁定方案 c)

## Verdict: APPROVED

## Review chain

| Stage | Verdict | Artifact |
|---|---|---|
| hf-specify r1 | drafted (commit `10f8d70`) | spec r1 |
| hf-spec-review r1 | CHANGES_REQUESTED (3 critical + 5 important + 3 minor + 1 nit; 11 LLM-FIXABLE + 1 USER-INPUT) | `docs/reviews/spec-review-F014-r1-2026-04-26.md` |
| hf-specify r2 | revised (commit `46e9048`) — 全部 12 finding 闭合 | spec r2 |
| hf-spec-review r2 | **auto-streamlined APPROVED** | this approval |

## r2 闭合 trace (12 finding)

| Finding | r1 问题 | r2 修复 |
|---|---|---|
| **Cr-1** (USER-INPUT) | invalidate hook 仅在 `_trigger_memory_extraction`, 但 `cli.py experience add` / `publisher.py` / `knowledge/integration.py` 直接 `experience_index.store` 不经过该路径 | auto mode 锁定**方案 c** — `WorkflowRecallHook.invalidate` 在 5 个 caller 路径末尾 try/except invoke (与 F013-A SkillMiningHook 多 caller 接入同 pattern); `--rebuild-cache` 兜底 |
| **Cr-2** | PathRecaller 拟用 `search(domain=)` 但 search domain 过滤的是 `record.domain` 而非 `record.problem_domain` | 改用 `list_records()` + Python filter on `record.problem_domain` (与 F013-A pattern_detector 同 pattern) |
| **Cr-3** | INV-F14-5 称 "7 步流程" 但 hf-workflow-router 实际编号 1-10 | INV-F14-5 + 摘要改 "既有 step 1-10, additive step 3.5 在 step 3 (支线) 与 step 4 (Profile) 之间" |
| **Im-1** | INV-F14-2 仅许 `.garage/workflow-recall/` 但 §2.2 需写 `platform.json` | INV-F14-2 例外清单含 `.garage/config/platform.json` 字段级扩展 (与 F013-A `skill_mining.hook_enabled` 同 pattern) |
| **Im-2** | INV-F14-1 措辞 "KnowledgeStore + 不读不写" 易歧义 | 改 "read-only on EI; 不读不写 KS (KS 不在 F014 数据流中)" |
| **Im-3** | CON-1404 / INV-F14-5 未指向 dogfood SHA sentinel | 显式指向 `tests/adapter/installer/test_dogfood_invariance_F009.py` + `dogfood_baseline/skill_md_sha256.json` + 三处 SKILL.md (源 + .cursor/ + .claude/) |
| **Im-4** | FR-1402 `--skill-id` 后续序列无算法契约 | 加算法: 取 Z 第一次出现位置之后子序列; Z 是序列最后一项 → 跳过 |
| **Im-5** | FR-1404 增量扫 vs 全量重算自相矛盾 | 删 §2.1 D 增量描述; 统一 lazy 全量重算 + F015+ D-1410 carry-forward |
| **Mi-1** | 调研锚点 search(domain=) 行 | 加注 "F014 不用 domain 过滤" |
| **Mi-2** | §11 测试基线 989 是声称值 | 加 "实施前再核 `uv run pytest`" |
| **Mi-3** | "24 个 hf-* skill 测试" 表述混淆 | CON-1404 改述为 3 项守门 (dogfood SHA + neutrality + 基线) |
| **Ni-1** | vision § 引用行号 | 验证正确, 无需改 |

## 通过条件

- ✅ 12 finding 全部闭合 (3 critical + 5 important + 3 minor + 1 nit; 11 LLM-FIXABLE + 1 USER-INPUT)
- ✅ Cr-1/Cr-2/Cr-3 critical 都有可核对的代码 line 锚点 (`session_manager.py` / `experience_index.py` / `hf-workflow-router/SKILL.md`)
- ✅ Im-1..Im-5 important 都有闭合表述
- ✅ Cr-1 USER-INPUT 设计选择 (invalidate caller 接入策略) auto mode 锁选项 c (与 F013-A 同 pattern), 用户在 PR #38 review 时可改

## 与 vision 对齐

- F014 直击 `growth-strategy.md` § Stage 3 第 68 行 "工作流编排从手动变成半自动" — 唯一未交付项
- 不动其他 5/5 维度 (B1-5 / Promise ①-⑤ 既有 5/5)
- Stage 3 ~85% → 推动到 ~95%

## Carry-forward 决策

- D-1410: cache 增量扫 (Im-5 r2 推 F015+; 当前全量重算 1000 record < 2s)
- D-1411: NLP-based skill_ids 序列相似度
- D-1412: agent 自动组装 (`garage agent compose`)

## 归档

✅ **F014 spec r2 APPROVED**, 进入 hf-design.
