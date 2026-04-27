# Traceability Review — F013-A r1 (Skill Mining Push)

- **日期**: 2026-04-26
- **审阅人**: Cursor Agent (auto-streamlined per F011/F012 mode)
- **范围**: 5 个 FR (FR-1301..1305) + 5 个 INV (INV-F13-1..5) + 5 个 CON (CON-1301..1305)

## Verdict: APPROVED

## FR ↔ 实现 ↔ 测试 矩阵

| FR | 实现位置 | 测试 |
|---|---|---|
| **FR-1301** Pattern Detection | `pattern_detector.py::detect_and_write` + `pipeline.py::SkillMiningHook.run_after_extraction` | `test_pattern_detector.py::TestDetectAndWrite` (5) + `test_pipeline.py::TestHookRunsAfterExtraction` |
| **FR-1302** `garage skill suggest` CLI | `cli.py::_skill_suggest` (含 --status / --rescan / --threshold / --purge-expired / --id) | `TestSkillSuggestCommand` 6 用例 |
| **FR-1303** Template Generator | `template_generator.py::render` + `render_minimal` | `test_template_generator.py` 13 用例 |
| **FR-1304** `garage skill promote` | `cli.py::_skill_promote` (含 --yes / --dry-run / --target-pack / --reject) | `TestSkillPromoteCommand` 5 用例 + `test_promote_no_pack_json_mutation.py` sentinel |
| **FR-1305** Audit / Decay + status display | `pipeline.py::run_audit` + `compute_status_summary` + `cli.py::_print_skill_mining_status` | `test_pipeline.py::TestAuditDecay` + `TestComputeStatusSummary` (2) |

**5 / 5 FR 全部追溯**

## INV ↔ 测试

| INV | 测试 |
|---|---|
| INV-F13-1 (写仅 .garage/skill-suggestions/) | `test_suggestion_store.py::TestCreateProposed` + `test_promote_no_pack_json_mutation.py` byte sentinel |
| INV-F13-2 (promote opt-in) | `TestSkillPromoteCommand` 5 用例 (--yes / --dry-run / --reject 全覆盖) |
| INV-F13-3 (pattern_detector read-only) | `test_pattern_detector.py::TestDetectAndWrite::test_kb_and_ei_read_only_no_mutation` |
| INV-F13-4 (skill-anatomy 6 章节) | `test_template_generator.py::TestRenderTotalUnder300Lines` + 6 个 _render_* 单测 |
| INV-F13-5 (F003-F011 字节级不变) | F003 既有 method 签名不动 (caller 改动用 try/except 包) — 由 baseline 930 → 989 + 0 regression 验证 |

**5 / 5 INV 全部覆盖**

## CON ↔ 验证

| CON | 验证 |
|---|---|
| CON-1301 (既有 schema 不动) | sentinel: `git diff main..HEAD -- src/garage_os/types/__init__.py` = 0; F003-F011 测试基线全过 |
| CON-1302 (零依赖) | `git diff main..HEAD -- pyproject.toml uv.lock` = 0 |
| CON-1303 (perf < 5s) | `test_pattern_detector_perf_100_entries.py` (100 < 0.5s) + `scripts/skill_mining_perf_smoke.py` 1000+1000 = 0.803s |
| CON-1304 (promote 不动 pack.json) | `test_promote_no_pack_json_mutation.py` byte hash 前后相等 |
| CON-1305 (echo 不自动 invoke) | code review: `_skill_promote` 末尾仅 print, 不 spawn subprocess / 不 import hf-test-driven-dev |

## 上下游 trace

- **Spec ↔ Design ↔ Tasks ↔ Impl**: spec r2 (FR-1301..1305 + 5 INV + 5 CON) → design r2 (7 ADR + 5 INV + 5 CON) → tasks T1-T5 → 实施 commits (dff14f8 / f86d53a / be8b2cd / bde1020 / TBD)
- **post-F012 carry-forward**: 闭合 growth-strategy.md § 1.3 表第 4 行 唯一未达成项
- **F003-F006 复用**: pattern_detector 复用 KnowledgeStore.list_entries + ExperienceIndex.list_records + retrieve API; template_generator 复用相同 read API
- **F010 caller pattern**: ingest/pipeline.py 改动模式与 F010 既有 ingest "best-effort archive_session" 一致 (try/except 不阻断)

## 残余项

- **None blocking**.

## 通过条件

✅ traceability review APPROVED, 进入 regression gate.
