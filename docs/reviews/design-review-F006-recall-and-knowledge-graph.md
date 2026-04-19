# Design Review — F006 Garage Recall & Knowledge Graph (D006)

- 评审对象: `docs/designs/2026-04-19-garage-recall-and-knowledge-graph-design.md`
- 关联规格: `docs/features/F006-garage-recall-and-knowledge-graph.md`（已批准；`docs/approvals/F006-spec-approval.md`）
- Reviewer: cursor cloud agent (hf-design-review subagent)
- 日期: 2026-04-19
- Workflow Profile / Execution Mode: `standard` / `auto`
- Workspace Isolation: `in-place`
- Branch: `cursor/f006-recommend-and-link-177b`
- UI Surface: NONE (pure CLI；无需 `hf-ui-review` peer)

## 结论

通过

## Precheck

- ✅ 已批准规格可回读（`F006-spec-approval.md` round-2 verdict 通过；spec 状态 `已批准`）
- ✅ 设计草稿稳定可定位（`docs/designs/2026-04-19-garage-recall-and-knowledge-graph-design.md` 单一来源，415 行）
- ✅ profile / stage / approval evidence 一致（`standard` / `auto`，task-progress 与 approval 记录无冲突）
- ✅ AGENTS.md 无新增评审约定与本评审冲突

## 多维评分

| 维度 | 评分 | 备注 |
|------|------|------|
| `D1` 需求覆盖与追溯 | 9/10 | § 3 追溯表覆盖全部 8 条 FR + 5 条 NFR + 6 条 CON；每条 → 落点明确 |
| `D2` 架构一致性 | 9/10 | "增量限制于 cli.py + 1 个 non-breaking 方法" 边界清晰；CLI 子命令树 § 9.1 一目了然 |
| `D3` 决策质量与 trade-offs | 9/10 | 3 个 ADR（顶级 vs 子树、独立 scorer、显式拒绝多 type）均含候选 + 收益 + 代价 + 可逆性 + revisit 信号 |
| `D4` 约束与 NFR 适配 | 9/10 | NFR mapping 表 § 11 + ADR-602 显式扛 CON-605；publisher 元数据保护落入 § 12 + FR-607 |
| `D5` 接口与任务规划准备度 | 9/10 | § 9 参数表 + § 10 三张时序图 + § 14 5-task 切分 + 依赖关系（T2-T4 依赖 T1）已显式 |
| `D6` 测试准备度与隐藏假设 | 8/10 | § 13 列出 26 个 test cases 对应 FR/NFR；§ 15 5 条 OD 显式判断；隐藏假设 ASM-604 已被 spec 覆盖 |

整体未触发"任一维度 < 6/10"或"任一维度 < 8/10"红线。

## 源码侧验证（设计承诺 vs 实际代码）

针对 reviewer 指令显式要求验证的三条关键承诺：

1. ✅ **`_DATACLASS_FRONT_MATTER_KEYS` 包含 `related_decisions` / `related_tasks`** — `src/garage_os/knowledge/knowledge_store.py:366-381` 元组列出全部 14 个 reserved key，`related_decisions`（line 374）+ `related_tasks`（line 375）均在内；`_entry_to_front_matter` line 410-411 显式写入；`_front_matter_to_entry` line 465-466 以 `[]` 兜底读出。设计 § 2.3 "**会持久化** `entry.related_decisions` / `entry.related_tasks`" 的承诺成立 → FR-604 落地路径无障碍。
2. ✅ **`RecommendationService.recommend()` 在 query-only context 下能基于 tags 给 score** — `src/garage_os/memory/recommendation_service.py:91-94` 显示 `for tag in tags: if tag in entry_tags: score += 0.6 + reason "tag:<v>"`；line 64 `skill_name = (context.get("skill_name") or "").lower()` 允许空 string；line 117-133 即使 results 为空，只要 `skill_name` 真值（FR-601 step 2 设 `tokens[0]`），还会走 `skill_name_only` fallback（score=0.1）。设计 ASM-604 "仅有 tags 时也能正常工作" 经源码验证成立。**轻微注意**：fallback 分支返回 score=0.1，这与 FR-602 "仅返回 score>0" 的过滤口径相容，不会被合并阶段意外丢弃。
3. ✅ **`ExperienceIndex.list_records()` 是 O(N) 全盘扫描** — `src/garage_os/knowledge/experience_index.py:160-181` 显示遍历 `RECORDS_DIR` 下全部 `*.json` 文件，逐个 `read_json` 解析。100 条 JSON 小文件的常数项远低于 1.5s（实测 F003 / F005 类似规模 < 0.1s）→ NFR-603 "< 1.5s on ≤100 records" 合理。
4. ✅ **F005 handler 模式可被干净继承** — `src/garage_os/cli.py:987-1029` 的 `build_parser()` + 模块级 `_knowledge_*` handler 函数 + `_require_garage()` 入口收敛 + 顶层 `*_FMT` 常量约定，与设计 § 4 "继承 D005 Thin CLI Handler Pattern" 完全一致；`knowledge_subparsers.add_parser("link"|"graph")` 与 `subparsers.add_parser("recommend")` 是平凡延伸。
5. ✅ **`KnowledgeEntry.related_decisions / related_tasks` 字段就位** — `src/garage_os/types/__init__.py:108-109` 两字段 dataclass 定义为 `List[str] = field(default_factory=list)`，与设计 ADR-602 "零 schema 变更" 承诺一致。

## 发现项

无 critical / important 发现。以下均为 minor，不阻塞 `hf-tasks`：

- `[minor][LLM-FIXABLE][D2]` § 9.5 把 `ERR_LINK_FROM_NOT_FOUND_FMT` 注解为 `KNOWLEDGE_NOT_FOUND_FMT` 的 alias，但 spec FR-604 验收用的是前者名字。建议在 design 实现说明中显式写：`ERR_LINK_FROM_NOT_FOUND_FMT = KNOWLEDGE_NOT_FOUND_FMT`（同一字符串引用），避免实现时误以为是两条独立文案、或测试断言 import 错误名。
- `[minor][LLM-FIXABLE][D5]` § 10.1 时序图 "RS-->>H: knowledge results (score>0)" 没有提到 `RecommendationService.recommend()` 在 results 为空且 `skill_name` 真值时会触发 `skill_name_only` 0.1 fallback 分支（`recommendation_service.py:117-133`）。该分支返回的条目 `match_reasons=["skill_name_only"]` 会被 CLI 直接打印——建议在设计中显式说明 CLI 是否要为这条 reason 做 stdout 文案兜底（例如把 `skill_name_only` → 人话 `"matches skill name: <token>"`），或显式接受原 reason 字符串原样输出。当前规格未限制此细节，但任务拆解时需要一个明确决定，否则两个 task（T2 / T5）会在同一文案上来回。
- `[minor][LLM-FIXABLE][D6]` § 12 失败模式表覆盖了主要异常路径但未列入 "`graph` 入边扫描遇到磁盘损坏 entry"（即 `KnowledgeStore.list_entries()` 内部 `_rebuild_index` 的 `(ValueError, OSError)` continue 分支吃掉若干文件的情形）。NFR-601 零回归与本 cycle 无关，但为了让 T4 测试用例覆盖到 "损坏文件不导致 graph 崩溃" 这种健壮性测试点，可在 § 12 增 1 行兜底语义。不阻塞，纯加固建议。

## 薄弱或缺失的设计点

- 设计中未显式说明 `recommend` 输出排序在 score 相同时如何稳定（如 knowledge 优先 / 字典序兜底 / 插入序）。当前 `sorted(key=lambda x: x["score"], reverse=True)` 是 stable sort，所以行为可推演但未文档化；T2 的 test cases 若依赖固定顺序断言会需要写明排序策略。**轻微**，可由 task 阶段决定。
- `_resolve_knowledge_entry_unique(eid)` helper 调用 3 次 `KnowledgeStore.retrieve()` 是 3 次磁盘读，比走 `list_entries()` 的内存索引一次扫描要慢。N=100 时仍 < 1.5s，未越界 NFR-603；但若未来 entry 数上千时该 helper 是热点。**非阻塞**，§ 14 OQ-604 已类似立场处理（"未来 N>1000 再优化"）。

## 任务规划准备度（给 hf-tasks 的输入提示）

- 设计 § 14 已给出 5 任务切分（T1 helper / T2 recommend / T3 link / T4 graph / T5 文档+回归）+ 依赖关系（T2-T4 都依赖 T1 的 2 helpers）→ `hf-tasks` 可以直接基于此粒度进入 RED→GREEN→REFACTOR 拆解，不需要回头补设计。
- 26 条 test case 覆盖全部 8 FR + NFR-601/603/604/605 → 任务级 RED 阶段有现成清单可挑。
- 唯一的 design-stage decision 仍待落地是上面 D5 minor finding 提到的 `skill_name_only` reason 文案口径——属 implementation 细节，可在 T2 内部裁决，不需要回到设计阶段。

## 下一步

`通过` → 设计真人确认（`needs_human_confirmation = true`）。`auto` 模式下由父会话写 `docs/approvals/F006-design-approval.md`；`reroute_via_router = false`。

## 记录位置

`docs/reviews/design-review-F006-recall-and-knowledge-graph.md`（本文件）

## 交接说明

- 本 reviewer 不代位完成 approval step；待父会话写 approval record 后方可启动 `hf-tasks`。
- `task-progress.md` 由父会话同步：`Current Stage` → `设计真人确认` → 批准后 → `hf-tasks`。
- 不修改任何 design / spec / 源码工件，仅落本 review 记录。
