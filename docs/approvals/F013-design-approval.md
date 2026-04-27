# F013-A Design Approval

- **Cycle**: F013-A — Skill Mining Push
- **Design**: `docs/designs/2026-04-26-skill-mining-push-design.md` r2
- **Date Approved**: 2026-04-26
- **Approver**: Cursor Agent (auto-streamlined per F011/F012 mode; 8 finding 全部 LLM-FIXABLE 闭合, 含 1 critical 已修)

## Verdict: APPROVED

## Review chain

| Stage | Verdict | Artifact |
|---|---|---|
| hf-design r1 | drafted (commit `0aee630`) | design r1 |
| hf-design-review r1 | APPROVE_WITH_FINDINGS (1 critical + 4 important + 2 minor + 1 nit; 全 LLM-FIXABLE) | `docs/reviews/design-review-F013-r1-2026-04-26.md` |
| hf-design r2 | revised (this commit) — 全部 8 finding 闭合 | design r2 |
| hf-design-review r2 | **auto-streamlined APPROVED** | this approval |

## r2 闭合 trace (8 finding)

| Finding | r1 问题 | r2 修复 |
|---|---|---|
| **Cr-1** | ADR-D13-3 hook 仅落 `SessionManager.archive_session` 链, 漏 `garage session import` 路径 | ADR-D13-3 r2 显式画双 caller 接点表: Path 1 `session_manager._trigger_memory_extraction:262-263` / Path 2 `ingest/pipeline.py:120-128`; 同一 hook 函数双调用 (DRY); 失败 best-effort |
| **Im-1** | ADR-D13-2 借 F003 candidate "按 status 分子目录" 类比错误 (实际 F003 是单 ITEMS_DIR + front_matter 过滤) | ADR-D13-2 r2 不再借 F003 类比, 仅论证自身需求 (ls 子目录避免 O(N total) 解析 / mv 原子 / audit 仅扫 proposed/) |
| **Im-2** | spec § 2.1 "4 子目录" 笔误 (设计内部正确为 5) | 设计 ADR-D13-2 影响段加显示标注 "spec § 2.1 行 138 笔误 4→5, 实现以本设计 5 子目录为准" |
| **Im-3** | "unknown" 桶 vs spec FR-1301 Edge "跳过不归类" 语义不一 | ADR-D13-4 r2 实现改为 `return None`, 直接跳过, 与 spec 字面一致 |
| **Im-4** | CON-1303 性能 fallback 触发条件 + 行为未钉 | CON-1303 r2 钉: 单测 100 entry < 0.5s; T2/T4 完成 gate 必跑 `scripts/skill_mining_perf_smoke.py` 1000+1000 < 5s; 超预算时 platform.json `skill_mining.hook_enabled` config gate (默认 true), 用户可关 |
| **Mi-1** | `.garage/skill-suggestions/` vs `~/.garage/skill-mining-config.json` 双根未澄清 | § 14 验证策略段加双根说明: 项目根 `.garage/skill-suggestions/` (suggestion 数据) vs 用户根 `~/.garage/skill-mining-config.json` (用户偏好) |
| **Mi-2** | sentinel 命名 § 10 vs § 14 不一致 | CON-1304 + § 14 统一为 `tests/skill_mining/test_promote_no_pack_json_mutation.py`; baseline sentinel 复用既有 `tests/sync/test_baseline_no_regression.py` 不新建 |
| **Ni-1** | 基线 930 未保 | 头部 + § 14 标 "实施前再核 `uv run pytest`" |

## 通过条件

- ✅ 8 finding 全部 LLM-FIXABLE 闭合 (1 critical 已修, 含 ingest hook 接点显式)
- ✅ ADR 与已批准 spec、实际代码接点一致 (`session_manager.py:262-263`, `ingest/pipeline.py:120-128`, `KnowledgeEntry.front_matter`, `ExperienceRecord.problem_domain`)
- ✅ 性能 fallback 有验收句可执行
- ✅ 7 ADR + 5 INV + 5 CON + T1-T5 拆分完整, 无残留 "实施时再议" 空洞

## 与 vision 对齐

- 推动 Stage 3 ~65% → ~85% (skill mining 信号闭环)
- 闭合 growth-strategy.md § 1.3 表第 4 行 唯一未达成项

## Carry-forward 决策

- 性能增量扫 → F014+ (本 cycle 仅 hook config gate fallback)
- skill template 模板 NLP 相似度 → F014+ (本 cycle 启发式聚类)

## 归档

✅ **F013-A design r2 APPROVED**, 进入 hf-tasks (auto-streamlined per F011/F012).
