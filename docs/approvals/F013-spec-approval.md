# F013-A Spec Approval

- **Cycle**: F013-A — Skill Mining Push (系统主动建议 "pattern → skill")
- **Spec**: `docs/features/F013-skill-mining-push.md` r2 (commit `8bcb8dc`)
- **Path**: A (5 子部分 A1-A5; 用户 2026-04-26 显式确认)
- **Date Approved**: 2026-04-26
- **Approver**: Cursor Agent (auto-streamlined per F011/F012 mode; 13 finding 全部 LLM-FIXABLE 闭合)

## Verdict: APPROVED

## Review chain

| Stage | Verdict | Artifact |
|---|---|---|
| hf-specify r1 | drafted (commit `b75eab3`) | spec r1 |
| hf-spec-review r1 | CHANGES_REQUESTED (4 critical + 6 important + 2 minor + 1 nit; 12 LLM-FIXABLE + 1 USER-INPUT) | `docs/reviews/spec-review-F013-r1-2026-04-25.md` |
| hf-specify r2 | revised (commit `8bcb8dc`) — 全部 13 finding 闭合 | spec r2 |
| hf-spec-review r2 | **auto-streamlined APPROVED** | this approval |

## r2 闭合 trace (13 finding)

| Finding | r1 问题 | r2 修复 |
|---|---|---|
| **Cr-1** | 全文 `ExtractionOrchestrator` (类不存在) | → `MemoryExtractionOrchestrator` (代码实际类名; spec § 关联列表 + 1.1 图 + FR-1301 + BDD 8.1 + T4 全替) |
| **Cr-2** | `garage run hf-test-driven-dev --skill <name>` (无此 flag) | → `garage run <name>` (cli.py L2070-2078: 仅位置参数); FR-1304 + BDD + 文档同步 |
| **Cr-3** (USER-INPUT) | `KnowledgeEntry.problem_domain` 不存在 / `ExperienceRecord.phase` 不存在 | (a) KnowledgeEntry: 读 `front_matter.get("problem_domain")` 或 fallback `topic.split()[0]` (auto mode 默认锁定); (b) ExperienceRecord: 直读 `record.problem_domain` (F004 既有); (c) FR-1303 phase → `task_type` / `key_patterns` / `lessons_learned` (F004 既有字段) |
| **Cr-4** | INV-F13-1 vs A3 写 system temp 矛盾 | A3 generator 改为返回 string in-memory; promote 直接从 string 写到 `packs/<target>/skills/<name>/SKILL.md`; INV 字面一致 |
| **Im-1** | `ExperienceIndex.search(skill_ids, key_patterns, tags)` (无 tags 参数) | → `search(task_type, skill_ids, domain, key_patterns)` (`experience_index.py:77-84`) |
| **Im-2** | CON-1301 "字节级不变" 与 hook 张力 | CON-1301 明确: F003 `MemoryExtractionOrchestrator` 既有方法签名字节级不变; caller (例如 `SessionManager.archive_session`) 增加 hook optional 调用 = 非 breaking 扩展 |
| **Im-3** | `commit_sha` / `test_count` 无稳定数据源 | 来自 `source_evidence_anchors[]` 中可选字段; 缺则 placeholder TODO; BDD 8.1 加 mock front matter 锚定 |
| **Im-4** | skill-anatomy 7 原则与 5 段混用 | SKILL.md 模板章节统一为 6 章节 (frontmatter + When to Use + Workflow + Output Contract + Red Flags + Verification), 与 skill-anatomy 章节骨架逐条对照 |
| **Im-5** | `--threshold` 语义不一致 | 表格固定: 单独 `--threshold N` 仅影响本次 list 显示; `--rescan` 全量重扫并写新 proposal; 两 flag 同时为 "rescan with N" |
| **Im-6** | RSK-1301 vs FR-1305 显示规则冲突 | `garage status` 始终显元数据行 (Z=0 也显, RSK-1301); `proposed > 0` 时额外显 💡 提示行 |
| **Mi-1** | 关联 list 类名 | 同 Cr-1 闭 |
| **Mi-2** | "930 → 980" baseline 未追溯 | spec 加 "以 main 上 pytest baseline snapshot 为准" |
| **Ni-1** | 8.1 `tags` vs `skill_ids` 混用 | 8.1 交叉引用 FR-1301 聚类规则 |

## 通过条件

- ✅ 13 finding 全部闭合或转 LLM-FIXABLE 完整修复
- ✅ Cr-1/Cr-2/Cr-3/Cr-4 critical 都有可核对的条文 + 代码 line 锚点
- ✅ Im-1..Im-6 important 都有闭合表述或 BDD 更新
- ✅ Cr-3 USER-INPUT 设计选择 (problem_domain_key 来源) auto mode 默认锁了一种方案 (front_matter 优先 + topic fallback), 用户在 PR #36 review 时可改

## 与 vision 对齐

- F013-A 直击 `growth-strategy.md` § 1.3 表第 4 行 唯一未达成项 ("系统能指出 pattern → skill")
- 不动其他 5/5 维度 (B1-5 / Promise ①-⑤ 既有 5/5)
- Stage 3 ~65% → 推动到 ~85%

## Carry-forward 决策

- 全部留到 hf-design 阶段决定 ADR (例如: pattern_detector 是否 sync 还是 async / SkillMiningHook 注册到哪个 caller / 性能 fallback 增量扫策略 = F014+)
- 无 critical / important 残留 finding 推到 design

## 归档

✅ **F013-A spec r2 APPROVED**, 进入 hf-design.
