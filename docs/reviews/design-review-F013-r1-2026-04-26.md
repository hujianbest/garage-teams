# Design Review — F013-A r1 (Skill Mining Push)

- 日期: 2026-04-26
- 审阅人: hf-design-review reviewer subagent (Cursor Agent task)
- 范围: `docs/designs/2026-04-26-skill-mining-push-design.md` (commit `0aee630`)
- 上游 spec: `docs/features/F013-skill-mining-push.md` r2 (APPROVED; `docs/approvals/F013-spec-approval.md`)

## Verdict: APPROVE_WITH_FINDINGS

## Findings (critical → important → minor → nit)

### [critical][LLM-FIXABLE][Cr-1] 与 spec/代码不一致：`garage session import` 的 hook 接点

- **位置**: 设计 ADR-D13-3 § 4 「影响」段
- **问题**: 设计写 `SessionManager.archive_session` 在 `MemoryExtractionOrchestrator.extract_for_archived_session_id` 返回后调 hook，并写「`garage session import` 同样 caller 路径添加可选 invoke」
- **事实**: `src/garage_os/ingest/pipeline.py` 中 `archive_session` 后由 **同一 pipeline 直接** `orchestrator.extract_for_archived_session_id(...)` (L115-121); `SessionManager._trigger_memory_extraction` 在 `extraction_enabled` 默认 false 时不会跑第二次 extraction; hook 若仅加在 `session_manager._trigger_memory_extraction` 的 extraction 之后, 则 **ingest 路径不会自动触发 skill mining**, 与 spec FR-1301 触发 (a) 中「`SessionManager.archive_session` 链 **或** `garage session import` 流程」不一致
- **r2 要求**: 明确在 **ingest** 的 `extract_for_archived_session_id` 成功返回后调用 `SkillMiningHook.run_after_extraction`（与 archive 内路径二选一或两处对称），或等价的「单一 caller + 不遗漏 import」的接点图

### [important][LLM-FIXABLE][Im-1] ADR-D13-2 对 F003「同 pattern」的论证偏窄

- **位置**: 设计 § 3 ADR-D13-2 理由段
- **问题**: 设计以「与 `.garage/memory/candidates/items/` 按 status 分子目录同 pattern」支持 5 子目录 + mv
- **事实**: `src/garage_os/memory/candidate_store.py` 中 candidate **单目录** `ITEMS_DIR`, `list_candidates_by_status` 是扫目录 + `front_matter.get("status")` 过滤 (L73-85), **不是**按 status 子目录分桶
- **r2 要求**: 改为准确表述（F003 的 batches/confirmations 与「分目录」相关; items 是 front_matter 状态 + 单目录）或仅论证 skill-suggestions 自身需求（ls 子目录、audit 只扫 proposed/、mv 原子性）

### [important][LLM-FIXABLE][Im-2] spec § 2.1 "4 子目录" 笔误对齐

- **位置**: spec `docs/features/F013-skill-mining-push.md` § 2.1 行 138 写「4 子目录」; 设计 § 0 架构图、§ 2、§ 3、§ 8 任务表均正确为 **5** 子目录
- **r2 要求**: 设计明显加一句「spec § 2.1 一处笔误 4→5, 实现以 5 为准」, 避免 tasks 阶段照抄错字

### [important][LLM-FIXABLE][Im-3] `unknown` 桶与 spec FR-1301 Edge 一致性

- **位置**: 设计 ADR-D13-4 「影响」段 vs spec FR-1301 Edge
- **问题**: 设计写 `domain == "unknown"` 的 entry **不参与聚类**; spec FR-1301 Edge 写「跳过该 entry 不归类」(语义可收敛但需一致)
- **r2 要求**: 用同一句式对齐 (跳过 vs unknown 桶), 避免实现/T2 单测对「是否占用 N 的 session 计数」产生歧义

### [important][LLM-FIXABLE][Im-4] 性能与 fallback (CON-1303) 验收绑定

- **位置**: 设计 § 10 CON-1303 + R-D13-3a + ADR-D13-3
- **问题**: 设计给 100 entry / 0.5s 单测 + 外推; ADR-D13-3 已承认可能 >5s 需 fallback Option C; 但 fallback 触发条件 / 产品行为 / 验收门未钉
- **r2 要求**: 写清 T2/T4 完成定义: 是否以「单测门槛 + 手工/prof 一次 1000+1000」为 gate; 超过预算时产品行为分支 (仅 CLI / 提示用户 / 关 hook 配置) 一条明确

### [minor][LLM-FIXABLE][Mi-1] 配置路径与图中「项目 .garage」

- **位置**: 设计 § 0 图与多处 `.garage/skill-suggestions/`; spec 同写 `~/.garage/skill-mining-config.json`
- **r2 要求**: 标「跨两处 runtime」(项目 `.garage/skill-suggestions/` vs 用户 `~/.garage/skill-mining-config.json`) 或统一为单根, 避免 T4 找错文件

### [minor][LLM-FIXABLE][Mi-2] 测试 sentinel 命名一致性

- **位置**: 设计 § 10 CON-1304 写 `test_promote_no_pack_json_mutation.py`; § 14 写 `test_baseline_no_regression.py`
- **r2 要求**: 与 hf-tasks 阶段统一最终文件名

### [nit][LLM-FIXABLE][Ni-1] 基线测试数

- **位置**: 设计 § 0 / § 8 写基线 930
- **r2 要求**: 以 merge 时 `uv run pytest` 为准在 r2 更新 (实施前再核)

## Recommendations for r2

1. **Cr-1**: 重画/重写 FR-1301 触发链: `archive_session` 内 `_trigger_memory_extraction` 完成点 **与** `ingest/pipeline.py` 在 `extract_for_archived_session_id` 后的点; 说明 hook 是否复用同函数、失败策略与 spec 一致 (不阻断 import/archive)
2. **Im-1**: 修正 ADR-D13-2 对 F003「同 pattern」依据 (或去掉该句, 只保留 product 理由)
3. **Im-2**: 设计明显标 spec § 2.1「4 子目录」笔误
4. **Im-3**: 对齐 unknown / skip entry 与 spec FR-1301 Edge 一句子
5. **Im-4**: 钉死 CON-1303 超预算时的系统行为与验收步骤
6. **Mi-1**: 澄清 `.garage` 双根 (项目 vs `~/.garage`) 下 `skill-mining-config.json` 的解析规则
7. **Mi-2**: 统一 sentinel 命名

## 通过条件

- 无未解决的 critical (当前 critical 为 ingest hook 接点, 修文档或实现策略说明即可在 r2 关闭)
- ADR 与已批准 spec、实际代码接点 (`session_manager.py`, `ingest/pipeline.py`) 一致
- 性能 fallback 有验收句可执行、无「实现时再议」的触发条件空洞

## 计数

- Critical: **1** (LLM-FIXABLE)
- Important: **4** (LLM-FIXABLE)
- Minor: **2** (LLM-FIXABLE)
- Nit: **1** (LLM-FIXABLE)

总计 **8 finding**, 全部 LLM-FIXABLE.

## ADR 交叉验证记录 (供审计)

| ADR | 结论 | 证据 |
|-----|------|------|
| D13-1 顶级 `skill_mining` | 与现有布局一致 | `knowledge/`, `memory/`, `sync/`, `adapter/` 平级子包; `sync/` 跨源顶级包, 设计类比成立 |
| D13-2 5 子目录 + mv | 与 F003「items 分状态子目录」表述不符; 产品理由仍成立 | `candidate_store.py`: 单 `ITEMS_DIR`, status 在 front_matter |
| D13-3 同步 hook + caller | **需补 ingest 接点** | `session_manager._trigger_memory_extraction` L261-265 调 `extract_for_archived_session`; `ingest/pipeline.py` L115-121 另径直接 `extract_for_archived_session_id` |
| D13-4 双源 problem_domain | 与类型一致 | `types/__init__.py`: `KnowledgeEntry` 无顶层 `problem_domain`, `front_matter: dict`; `ExperienceRecord` 有 `problem_domain: str` |
| D13-5 无 Jinja2 | 成立 | `pyproject.toml` 无 jinja 依赖 |
| D13-6 `garage status` inline | 与 F010 一致 | `cli.py`: `_status` L374+ 末尾调 `_print_sync_status` L462 |
| D13-7 T1-T5 | 与 spec § 9 表 1:1 | 设计 § 8 任务表与 spec 实施分块一致 |
