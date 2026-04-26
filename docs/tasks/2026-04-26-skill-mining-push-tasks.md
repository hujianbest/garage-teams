# F013-A Tasks — Skill Mining Push 实施分块

- **状态**: 草稿 r1 (auto-streamlined per F011/F012 mode)
- **关联 spec**: `docs/features/F013-skill-mining-push.md` r2 APPROVED
- **关联 design**: `docs/designs/2026-04-26-skill-mining-push-design.md` r2 APPROVED (ADR-D13-7 任务表为本计划唯一来源)
- **日期**: 2026-04-26

## 0. 总览

| 任务 | 提交主题 | 测试增量 | 依赖 | FR / INV / CON 覆盖 |
|---|---|---|---|---|
| **T1** | `skill_mining/{__init__, types, suggestion_store}` + 8 测试 | 8 | 无 | INV-F13-1 (写 .garage/skill-suggestions/ 内); CON-1302 (零依赖) |
| **T2** | `skill_mining/pattern_detector.py` + 12 测试 | 12 | T1 | FR-1301; INV-F13-3 (read-only on KS+EI); INV-F13-5 (F003-F011 字节级不变); CON-1303 (perf 单测 < 0.5s + 手工 1000+1000) |
| **T3** | `skill_mining/template_generator.py` + 10 测试 | 10 | T1 | FR-1303; INV-F13-4 (skill-anatomy 6 章节); description ≥ 50 字 + ≤ 300 行 |
| **T4** | `skill_mining/pipeline.py` + `SkillMiningHook` + CLI `skill suggest` + 双 caller 接点 + 12 测试 | 12 | T1+T2+T3 | FR-1301 + FR-1302 + FR-1305; CON-1301 (双 caller try/except 包); CON-1303 (config gate `skill_mining.hook_enabled`) |
| **T5** | CLI `skill promote` + `garage status` skill-mining 段 + AGENTS.md / RELEASE_NOTES + manual smoke + 8 测试 | 8 | T1-T4 | FR-1304 + FR-1305 显示规则; INV-F13-1 (promote 唯一写 packs/ 通道); INV-F13-2 (opt-in); CON-1304 (不动 pack.json); CON-1305 (echo 不自动 invoke) |

**总测试增量**: ~50 (基线 930 → 980; T2 完成时再核基线)

## 1. T1 — `skill_mining` foundation

### 交付

- `src/garage_os/skill_mining/__init__.py`
- `src/garage_os/skill_mining/types.py` — `SkillSuggestion` dataclass + `SkillSuggestionStatus` enum
- `src/garage_os/skill_mining/suggestion_store.py` — 5 子目录 CRUD + atomic write + mv 状态转换
- `tests/skill_mining/__init__.py` + `tests/skill_mining/test_suggestion_store.py` (8 用例)

### 测试 (8)

1. `test_create_proposed_writes_to_proposed_subdir`
2. `test_id_generation_format` (sg-yyyymmdd-6hex)
3. `test_load_returns_none_for_missing`
4. `test_move_to_status_uses_os_rename` (atomic)
5. `test_list_by_status_filters`
6. `test_5_subdirs_lazy_mkdir_on_first_write`
7. `test_atomic_write_no_partial_file_on_failure` (mock IO error)
8. `test_round_trip_serialization` (写读字节一致, datetime ISO)

### 不破

- 不动 src/garage_os/types/__init__.py (CON-1301 字节级)
- 全 stdlib (CON-1302)

### Definition of Done

- 8/8 测试过
- ruff diff = 0
- `uv run pytest tests/skill_mining/test_suggestion_store.py -q` PASS

---

## 2. T2 — Pattern Detector

### 交付

- `src/garage_os/skill_mining/pattern_detector.py` — 聚类 + 评分 + 阈值 + ADR-D13-4 双源 problem_domain_key
- `tests/skill_mining/test_pattern_detector.py` (12 用例)
- `tests/skill_mining/test_pattern_detector_perf_100_entries.py` (1 用例, CON-1303 单测门)
- `scripts/skill_mining_perf_smoke.py` (手工 prof, T4 finalize 前必须跑一次)

### 测试 (12 + 1 perf)

1. `test_extract_problem_domain_key_experience_record_top_level` (read `record.problem_domain` 直接)
2. `test_extract_problem_domain_key_knowledge_entry_front_matter` (read `entry.front_matter["problem_domain"]`)
3. `test_extract_problem_domain_key_knowledge_entry_topic_fallback` (no front_matter → topic.split()[0])
4. `test_skip_entry_with_no_domain_key` (Im-3: 返回 None 直接跳)
5. `test_cluster_by_domain_and_tag_bucket` (frozenset 归一化)
6. `test_threshold_n_5_default`
7. `test_dedup_session_id_across_evidence` (按 session_id 去重计 N)
8. `test_skip_already_covered_skill` (扫 packs/ frontmatter name substring match)
9. `test_score_formula_components` (log10 + session_count + max_ts)
10. `test_existing_status_proposed_no_dup` (不重复生成)
11. `test_expired_status_allows_regeneration`
12. `test_kb_and_ei_read_only_no_mutation` (sentinel: KS/EI hash 前后字节相同)
13. (perf) `test_pattern_detector_perf_100_entries` < 0.5s

### 不破

- 不动 KnowledgeStore / ExperienceIndex (INV-F13-3)
- 不动 F003 candidate_store / orchestrator (INV-F13-5)

### Definition of Done

- 13/13 测试过
- `uv run python scripts/skill_mining_perf_smoke.py` 输出 1000+1000 < 5s (T4 finalize gate)
- ruff diff = 0

---

## 3. T3 — Template Generator

### 交付

- `src/garage_os/skill_mining/template_generator.py` — 6 章节 in-memory string (Im-4: frontmatter + When to Use + Workflow + Output Contract + Red Flags + Verification)
- `tests/skill_mining/test_template_generator.py` (10 用例)

### 测试 (10)

1. `test_render_frontmatter_name_and_description`
2. `test_render_when_to_use_from_task_types`
3. `test_render_workflow_from_lessons_and_patterns`
4. `test_render_output_contract_from_knowledge_types`
5. `test_render_red_flags_includes_pitfalls` (evidence record `pitfalls[]`)
6. `test_render_verification_with_evidence_anchor` (Im-3: source_evidence_anchors[].commit_sha + test_count 命中)
7. `test_render_verification_placeholder_when_anchors_missing` (TODO comment)
8. `test_description_min_50_chars`
9. `test_total_output_under_300_lines`
10. `test_robust_minimal_evidence` (1 entry warning + minimal template)

### 不破

- 仅返回 string, 不写文件 (INV-F13-1)
- 全 stdlib (CON-1302)

### Definition of Done

- 10/10 测试过
- ruff diff = 0

---

## 4. T4 — Pipeline + Hook + CLI `skill suggest`

### 交付

- `src/garage_os/skill_mining/pipeline.py` — `SkillMiningHook.run_after_extraction(session_id, storage)` + audit/decay + `compute_status_summary()`
- 修改 `src/garage_os/runtime/session_manager.py` `_trigger_memory_extraction` 末尾追加 hook (try/except 包)
- 修改 `src/garage_os/ingest/pipeline.py:120-128` extract 调用后追加同一 hook (try/except 包)
- 修改 `src/garage_os/cli.py` 加 `skill` subparser + `skill suggest` handler (含 --status / --rescan / --threshold / --purge-expired / --id)
- 加 `platform.json` schema: `skill_mining.hook_enabled: bool` (默认 true), `skill_mining.threshold: int` (默认 5), `skill_mining.expiry_days: int` (默认 30)
- `tests/skill_mining/test_pipeline.py` (6 用例)
- `tests/test_cli.py` 加 `TestSkillSuggestCommand` (6 用例)

### 测试 (6 + 6 = 12)

**Pipeline (6)**:
1. `test_hook_run_after_extraction_writes_proposal`
2. `test_hook_idempotent_repeat_session` (同 session 短时间重跑不重生 proposal)
3. `test_hook_failure_does_not_block_caller` (mock pattern_detector raise → caller 仍正常)
4. `test_audit_decay_30_days_marks_expired`
5. `test_compute_status_summary_with_zero_proposed`
6. `test_config_gate_hook_enabled_false_skips_pattern_detector` (CON-1303 fallback)

**CLI (6)**:
1. `test_skill_suggest_lists_proposed`
2. `test_skill_suggest_filter_by_status`
3. `test_skill_suggest_id_shows_detail_with_template_preview`
4. `test_skill_suggest_rescan_writes_new_proposals`
5. `test_skill_suggest_threshold_only_filters_display_no_rescan`
6. `test_skill_suggest_purge_expired_with_yes`

### 不破

- 双 caller try/except 包 (Cr-1 + RSK-D13-6)
- F003 既有方法签名不动 (INV-F13-5)
- platform.json 既有字段不动, 仅新增 `skill_mining` block (CON-1301)

### Definition of Done

- 12/12 测试过
- ruff diff = 0
- `uv run python scripts/skill_mining_perf_smoke.py` 输出 1000+1000 < 5s

---

## 5. T5 — CLI `skill promote` + `garage status` 段 + 文档 + smoke

### 交付

- 修改 `src/garage_os/cli.py` 加 `skill promote` handler (含 --reject / --yes / --dry-run / --target-pack)
- 修改 `src/garage_os/cli.py` `_status` 末尾加 `_print_skill_mining_status` 调用 (与 `_print_sync_status` 同位置)
- 实现 `_print_skill_mining_status` (元数据行始终显; 💡 行 proposed > 0 时显)
- 修改 `AGENTS.md` 加 "Skill Mining Push (F013-A)" 段 (CLI usage + workflow + 配置 + carry-forward)
- 修改 `RELEASE_NOTES.md` 加 F013-A cycle entry
- 写 `docs/manual-smoke/F013-A-walkthrough.md` (4 tracks)
- `tests/skill_mining/test_promote_no_pack_json_mutation.py` (1 sentinel, CON-1304)
- `tests/test_cli.py` 加 `TestSkillPromoteCommand` (5 用例)
- `tests/test_dogfood_layout.py` 加 1 sentinel (skill_mining 模块结构存在)
- `tests/test_documentation.py` 加 1 sentinel (README/AGENTS 含 `skill suggest` + `skill promote`)

### 测试 (5 + 1 + 1 + 1 = 8)

**CLI promote (5)**:
1. `test_skill_promote_yes_writes_skill_md`
2. `test_skill_promote_dry_run_no_write`
3. `test_skill_promote_reject_with_reason`
4. `test_skill_promote_target_pack_override`
5. `test_skill_promote_existing_skill_prompt_overwrite` (RSK-1304)

**Sentinels (3)**:
6. `test_promote_no_pack_json_mutation` (写 SKILL.md 后 packs/garage/pack.json 字节相同)
7. `test_dogfood_skill_mining_module_exists`
8. `test_readmes_mention_skill_mining_cli`

### Manual smoke (T5)

`docs/manual-smoke/F013-A-walkthrough.md`:
- Track 1: `garage skill suggest` (空 → rescan with low threshold → 5 evidence proposal 出现)
- Track 2: `garage skill promote sg-XXX --yes` → packs/garage/skills/<name>/SKILL.md 创建 + status=promoted
- Track 3: `garage skill promote sg-YYY --reject` → reason prompt → status=rejected
- Track 4: 模拟 31 天前 created → `garage status` 显 expired → `--purge-expired --yes` 清

### 不破

- INV-F13-1 (promote 唯一通道写 packs/)
- INV-F13-2 (默认 prompt; --yes opt-in)
- CON-1304 (不动 pack.json) — sentinel 守
- CON-1305 (echo 不自动 invoke hf-test-driven-dev) — code review 守

### Definition of Done

- 8/8 测试过 + 4 tracks smoke 全绿
- ruff diff = 0
- 全套 `uv run pytest tests/ -q --ignore=tests/sync/test_baseline_no_regression.py` 应 ~980 passed
- `uv run pytest tests/sync/test_baseline_no_regression.py` PASS (sentinel)
- AGENTS.md / RELEASE_NOTES.md F013-A 段完整

---

## 6. 任务依赖图

```
T1 ─┬─→ T2 ─┐
    │       │
    └─→ T3  ├─→ T4 ─→ T5
            │
            └────────┘
```

T2 + T3 可并行起步 (依赖 T1), 但 T4 必须等两者; T5 必须等 T4.

## 7. Commit 边界

每个 T 一个 commit, 主消息格式: `f013(<part>): T<N> <description>`. T2 含 perf script, T4 含 platform.json schema 扩展, T5 含 docs + smoke. 所有 commit 含 spec/design/INV trace.

## 8. 与 vision 对齐 (任务级 deliverable)

- T1-T4 完成后 = pattern detection + suggest CLI + audit 闭环 (技术能力到位)
- T5 完成后 = promote 完整 + 文档 + smoke (用户感知 + Stage 3 ~85%)

---

> **本任务计划是 r1 (auto-streamlined per F011/F012 mode); 直接进入 hf-test-driven-dev T1**.
