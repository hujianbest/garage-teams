# T006: Garage Recall & Knowledge Graph 任务计划

- 状态: 草稿
- 主题: F006 — Garage Recall & Knowledge Graph（主动召回 + 知识图最小可用形态）
- 关联规格: `docs/features/F006-garage-recall-and-knowledge-graph.md`
- 关联设计: `docs/designs/2026-04-19-garage-recall-and-knowledge-graph-design.md`
- 关联审批:
  - `docs/approvals/F006-spec-approval.md`
  - `docs/approvals/F006-design-approval.md`
- 关联评审:
  - `docs/reviews/spec-review-F006-recall-and-knowledge-graph.md` / `-r2.md`（通过）
  - `docs/reviews/design-review-F006-recall-and-knowledge-graph.md`（通过，3 minor LLM-FIXABLE 内联收敛）

---

## 1. 概述

把 D006 设计拆成 5 个可独立 RED → GREEN → REFACTOR 的工程任务。任务边界：

- 仅修改 `src/garage_os/cli.py` + `src/garage_os/memory/recommendation_service.py`（仅 non-breaking 新增 `build_from_query` 方法）+ 文档 + `tests/test_cli.py` + `tests/test_documentation.py`
- 不修改 `KnowledgeStore` / `ExperienceIndex` / `RecommendationService.recommend()` / `KnowledgeEntry` / `ExperienceRecord` 任何已有签名
- 不引入新 PyPI 依赖
- 不引入新源码模块文件

---

## 2. 里程碑

| 里程碑 | 目标 | 任务数 | 退出标准 |
|--------|------|--------|----------|
| **M1: 基础 helper** | `_resolve_knowledge_entry_unique` + `_recommend_experience` 两个核心 helper + 单元测试 | 1 (T1) | 两个 helper 单测全绿；为 T2-T4 提供稳定底层 |
| **M2: 主动召回** | `garage recommend` handler + sub-parser + `build_from_query` + mixed recall + 零结果归口 | 1 (T2) | FR-601/602/603 验收全部覆盖 |
| **M3: 知识图** | `garage knowledge link` + `garage knowledge graph` handlers + sub-parsers | 2 (T3, T4) | FR-604/605/606/607 验收全部覆盖 |
| **M4: Cross-cutting + 文档 + 全 suite 回归** | help 自描述、smoke perf、source-marker 跨命令断言、用户指南、双 README | 1 (T5) | `pytest tests/ -q` ≥ 451 + F006 新增；用户指南可 grep |

---

## 3. 文件 / 工件影响图

### 3.1 修改的源码模块

| 文件 | 影响类型 | 任务 | 说明 |
|------|---------|------|------|
| `src/garage_os/cli.py` | 修改 | T1–T5 | 新增 6 个 handler / helper 函数 + 3 个 sub-parser + 模块顶层 `*_FMT` / `CLI_SOURCE_KNOWLEDGE_LINK` 常量 |
| `src/garage_os/memory/recommendation_service.py` | 修改（non-breaking） | T2 | 新增 `RecommendationContextBuilder.build_from_query(query, tags, domain)` 方法；不动 `build()` / `recommend()` |

### 3.2 修改的文档

| 文件 | 影响类型 | 任务 | 说明 |
|------|---------|------|------|
| `docs/guides/garage-os-user-guide.md` | 修改 | T5 | 新增 "Active recall and knowledge graph" 段，覆盖 3 个新子命令最小示例 |
| `README.md` | 修改 | T5 | CLI 命令列表追加 3 个新子命令名 |
| `README.zh-CN.md` | 修改 | T5 | 同上中文版 |

### 3.3 新增 / 修改的测试

| 文件 | 影响类型 | 任务 | 说明 |
|------|---------|------|------|
| `tests/test_cli.py` | 修改 + 新增 | T1–T5 | 新增 4 个 test class（约 25-30 个断言）；不修改既有 451 个断言 |
| `tests/test_documentation.py` | 修改 + 新增 | T5 | 新增 2-3 条 grep 断言 |

---

## 4. 需求与设计追溯

| 规格 / 设计锚点 | 覆盖任务 |
|----------------|----------|
| `FR-601` recommend knowledge 半边 + 设计 §3 / §10.1 | T2 |
| `FR-602` recommend experience 半边 + 设计 §3 / §10.1 | T1 (helper) + T2 (handler 串接) |
| `FR-603` recommend 零结果归口 + 设计 §10.1 | T2 |
| `FR-604` link happy + 设计 §3 / §10.2 | T3 |
| `FR-605` link/graph 多 type 命中 + 设计 §3 / §10.2 / §10.3 | T1 (resolver helper) + T3 (link 报错) + T4 (graph 报错) |
| `FR-606` graph 节点 + 出 + 入边 + 设计 §3 / §10.3 | T4 |
| `FR-607` cli: 命名空间 + 设计 §3 / §9.5 | T3 (link 路径) + T5 (cross-cutting `cli:` 断言) |
| `FR-608` help 自描述 + F005 子命令保留 + 设计 §3 / §9.1 | T2/T3/T4（每命令 sub-parser）+ T5（cross-cutting help 断言） |
| `NFR-601` 零回归 | T5（`pytest tests/ -q` ≥ 451）+ T1–T4（不修改既有测试） |
| `NFR-602` 零外部依赖 + 设计 §2.4 | T1–T5（每任务 PR 不新增 dependency） |
| `NFR-603` 召回 < 1.5s | T5（smoke test） |
| `NFR-604` stdout 常量化 + 设计 §9.5 | T2/T3/T4（每任务引入对应 FMT 常量）+ T5（grep 断言） |
| `NFR-605` 文档同步 | T5 |
| `CON-601` recommend 顶级 / link/graph 二级 + ADR-601 | T2/T3/T4（按命令位置） |
| `CON-602` 不改 store/index/recommend API | T1–T4（仅调既有公开方法 + 新增 `build_from_query` non-breaking） |
| `CON-603` `version+=1` 保持 | T3（断言 link 后 `version=N+1`） |
| `CON-604` `cli:` 命名空间 | T3 (`cli:knowledge-link`) + T5（grep 断言） |
| `CON-605` 不改 `RecommendationService.recommend` | T2（仅调，不改） |
| `CON-606` recommend/graph read-only | T2/T4（handler 仅调 retrieve / list_entries / list_records） |
| ADR-601 `recommend` 顶级偏离 | T2 |
| ADR-602 experience scorer 独立函数 | T1 |
| ADR-603 多 type 命中显式拒绝 | T1 (resolver) + T3/T4（handler 报错路径） |
| 设计 §10.1/10.2/10.3 数据流 | T2/T3/T4 |
| 设计 §13.2 用例 1–26 | T1–T5 全覆盖 |

---

## 5. 任务拆解

### T1. helper 基础：`_resolve_knowledge_entry_unique` + `_recommend_experience`

- **目标**: 在 `cli.py` 新增两个底层 helper 函数 + 对应单元测试。
  1. `_resolve_knowledge_entry_unique(storage, eid) -> tuple[Optional[KnowledgeEntry], list[str]]`：在 3 个 `KnowledgeType` 目录下 `retrieve(t, eid)`，返回 `(entry_if_unique, types_hit)`；types_hit 长度 0 = 不存在，1 = 唯一命中，>1 = 多 type 命中。
  2. `_recommend_experience(records, context) -> list[dict]`：按 spec FR-602 6 条规则计算 score；返回与 `RecommendationService.recommend()` 同形（`{entry_id, entry_type="experience", title, score, match_reasons, source_session}`）的 list；score=0 的不返回。
- **Acceptance**（对应设计 §13.2 用例 #1-3 / #11 / #13 的 helper 层验证）:
  - `_resolve_knowledge_entry_unique` happy: 仅 `(decision, A)` 存在 → 返回 `(entry, ["decision"])`
  - `_resolve_knowledge_entry_unique` not-found: 无任何匹配 → 返回 `(None, [])`
  - `_resolve_knowledge_entry_unique` ambiguous: `(decision, X)` + `(pattern, X)` → 返回 `(<decision_entry>, ["decision", "pattern"])`（types 顺序按 `KnowledgeType` 枚举顺序）
  - `_recommend_experience` 命中 domain → score≥0.8 + reason `"domain:<v>"`
  - `_recommend_experience` 命中 problem_domain → score≥0.8 + reason `"problem_domain:<v>"`
  - `_recommend_experience` 命中 task_type via tag token → score≥0.6 + reason `"task_type:<v>"`
  - `_recommend_experience` 命中 tech_stack via tag token → reason `"tech:<v>"`
  - `_recommend_experience` 命中 key_patterns via tag token → reason `"pattern:<v>"`
  - `_recommend_experience` 命中 lessons_learned 文本 → score≥0.4 + reason `"lesson-text:<token>"`
  - `_recommend_experience` 不命中任一规则 → 不出现在返回列表
  - 返回项的 `entry_type == "experience"` 且 `title` 非空（`lessons_learned[0]` 或 `task_type` 兜底）
- **Verify**:
  - `pytest tests/test_cli.py -k "TestResolveKnowledgeEntry or TestRecommendExperienceHelper" -q` 全绿
  - `pytest tests/ -q` ≥ 451（现有 baseline）
- **依赖**: 无（最小起点）
- **Risk**: `_recommend_experience` 的 token-vs-record 匹配规则较多，需要逐条断言；ADR-602 已锁定不抽公共基类
- **Files**: `src/garage_os/cli.py`、`tests/test_cli.py`

### T2. `garage recommend <query>` handler + sub-parser + `build_from_query` 扩展

- **目标**:
  1. 在 `recommendation_service.py` 给 `RecommendationContextBuilder` 加 `build_from_query(query: str, tags: list[str] | None = None, domain: str | None = None) -> dict[str, Any]` 方法；不动 `build()`
  2. 在 `cli.py` 新增 `_recommend(garage_root, query, tags, domain, top)` handler
  3. 新增顶级 sub-parser `recommend`，参数：positional `query`、`--tag` (action="append")、`--domain`、`--top` (default=10)
  4. 新增模块常量 `RECOMMEND_NO_RESULTS_FMT`
  5. handler 流程：构造 context → 调 `RecommendationService.recommend()` 拿 knowledge 半边 → 调 `_recommend_experience(ExperienceIndex.list_records(), context)` 拿 experience 半边 → 合并按 score 降序取 top → 打印 / 零结果归口
- **Acceptance**（对应设计 §13.2 用例 #1–7）:
  - `recommend` 命中 1 条 knowledge → exit 0、stdout 含 `[DECISION]`、`ID:`、`Score:`、`Match:`
  - `recommend` 命中 1 条 experience（无 knowledge） → exit 0、stdout 含 `[EXPERIENCE]`、`ID:`、`Score:`、`Match:`
  - `recommend` 同时命中 knowledge + experience，按 score 降序排列
  - `--top 1` 限制结果数为 1
  - `--tag api --tag rest` 把两个 tag 进 context.tags
  - `--domain platform` 进 context.domain
  - 零 entry → exit 0 + stdout `RECOMMEND_NO_RESULTS_FMT.format(query="x")`
  - 5+5 entry 但全部不命中 → 同上
  - 无 `.garage/` → exit 1 + `ERR_NO_GARAGE`
  - `build_from_query("auth jwt", ["api"], "platform")` 返回 dict 含 `tags=["auth","jwt","api"]`、`domain="platform"`、`session_topic="auth jwt"` 等（独立单元测试 1 个）
  - `RecommendationService.recommend()` 源码字节级未变更（grep `recommend(` 签名 / score 权重未变）
- **Verify**:
  - `pytest tests/test_cli.py -k TestRecommend -q` 全绿
  - `pytest tests/ -q` ≥ T1 baseline 不退绿
- **依赖**: T1（`_recommend_experience` helper）
- **Risk**: `RecommendationContextBuilder.build_from_query` 若错误地修改了 `build()` → CON-602 违反；测试要 spot-check `build()` 行为不变
- **Files**: `src/garage_os/cli.py`、`src/garage_os/memory/recommendation_service.py`、`tests/test_cli.py`

### T3. `garage knowledge link` handler + sub-parser

- **目标**:
  1. 新增 `_knowledge_link(garage_root, src, dst, kind)` handler
  2. 新增 `knowledge link` sub-parser，参数：`--from`、`--to`、`--kind {related-decision,related-task}` (default=related-decision)
  3. 新增模块常量 `CLI_SOURCE_KNOWLEDGE_LINK`、`KNOWLEDGE_LINKED_FMT`、`KNOWLEDGE_LINK_ALREADY_FMT`、`ERR_LINK_FROM_AMBIGUOUS_FMT`
  4. handler 流程：调 `_resolve_knowledge_entry_unique(--from)` → not-found/ambiguous 报错 → 字段 append + 去重 → set `source_artifact = "cli:knowledge-link"` → `KnowledgeStore.update()`
- **Acceptance**（对应设计 §13.2 用例 #8–14）:
  - `link --from A --to B`（A 存在）→ exit 0、磁盘 `version=2`、`related_decisions=['B']`、`source_artifact="cli:knowledge-link"`、stdout `Linked 'A' -> 'B' (related-decision)`
  - 重复 `link --from A --to B` → exit 0、`related_decisions` 仍 `['B']`（去重）、stdout `Already linked 'A' -> 'B' (related-decision)`、version 仍 +1
  - `link --kind related-task --to T005` → 写 `related_tasks=['T005']`，stdout `Linked 'A' -> 'T005' (related-task)`
  - `link --from missing` → exit 1 + stderr 含 `KNOWLEDGE_NOT_FOUND_FMT.format(eid='missing')`
  - `link --to <任意外部 ID>` → 接受，不校验
  - `link` 多 type 命中 (`(decision, X)` + `(pattern, X)`) → exit 1 + stderr 含 `ERR_LINK_FROM_AMBIGUOUS_FMT` 列出 `decision` + `pattern`
  - `link` 不污染 publisher 元数据：先用 `KnowledgeStore.store()` 直写一条 `published_from_candidate="cand-x"` 的 entry，然后 link → publisher 字段保持，仅 `source_artifact` 被覆为 `cli:knowledge-link`
- **Verify**:
  - `pytest tests/test_cli.py -k TestKnowledgeLink -q` 全绿
  - `pytest tests/ -q` 不退绿
- **依赖**: T1（`_resolve_knowledge_entry_unique`）
- **Risk**: 字段去重必须用 `if dst not in field`（保序），不要 `set()` 转换打乱 history
- **Files**: `src/garage_os/cli.py`、`tests/test_cli.py`

### T4. `garage knowledge graph` handler + sub-parser

- **目标**:
  1. 新增 `_knowledge_graph(garage_root, eid)` handler
  2. 新增 `knowledge graph` sub-parser，参数：`--id`
  3. 新增模块常量 `KNOWLEDGE_GRAPH_NODE_FMT`（节点头格式）+ 段标题字符串（`Outgoing edges:` / `Incoming edges:` / `(none)` 也走常量化）
  4. handler 流程：`_resolve_knowledge_entry_unique` → not-found/ambiguous 报错 → 打印节点头 → 出边读 entry 字段 → 入边走 `KnowledgeStore.list_entries()` 全库扫描
- **Acceptance**（对应设计 §13.2 用例 #15–18）:
  - `graph` 节点 + 出边 + 入边 happy: `(decision, A)` `related_decisions=['B']`，`(decision, B)` `related_decisions=['C']` → `graph --id B` → stdout 头部 `[DECISION]`、`Outgoing edges:` 段含 `-> C (related-decision)`、`Incoming edges:` 段含 `<- A (related-decision)`
  - 孤立节点：`graph --id isolated`（无任何 in/out）→ `Outgoing edges:` 后 `(none)`、`Incoming edges:` 后 `(none)`
  - `graph --id missing` → exit 1 + `KNOWLEDGE_NOT_FOUND_FMT`
  - `graph --id` 多 type 命中 → exit 1 + `ERR_LINK_FROM_AMBIGUOUS_FMT`（共用 T3 常量）
  - `related_tasks` 也被打印为 `-> T005 (related-task)`
  - `Incoming edges` 同时来自 `related_decisions` 与 `related_tasks` 时双向显示（OD-605 不去重）
- **Verify**:
  - `pytest tests/test_cli.py -k TestKnowledgeGraph -q` 全绿
  - `pytest tests/ -q` 不退绿
- **依赖**: T1（`_resolve_knowledge_entry_unique`）
- **Risk**: 入边扫描的 ordering 要稳定（按 `KnowledgeStore.list_entries()` 自然序，避免测试 flake）
- **Files**: `src/garage_os/cli.py`、`tests/test_cli.py`

### T5. 文档同步 + cross-cutting 断言 + smoke + 全 suite 回归

- **目标**:
  1. `docs/guides/garage-os-user-guide.md` 新增 "Active recall and knowledge graph" 段（覆盖 3 个新子命令最小示例）
  2. `README.md` / `README.zh-CN.md` CLI 命令列表追加 3 个新子命令
  3. `tests/test_documentation.py` 新增 grep 断言：能找到 `garage recommend`、`garage knowledge link`、`garage knowledge graph` 3 个字符串
  4. `tests/test_cli.py` 新增 `TestRecallAndGraphCrossCutting` test class:
     - `garage --help` stdout 含 `recommend` (FR-608 用例 #22)
     - `garage knowledge --help` stdout 含 `add` / `edit` / `show` / `delete` / `search` / `list` / `link` / `graph` 共 8 个名 (FR-608 用例 #23)
     - `garage recommend --help` 含 `query` / `--tag` / `--domain` / `--top` (FR-608 用例 #19)
     - `garage knowledge link --help` 含 `--from` / `--to` / `--kind` (FR-608 用例 #20)
     - `garage knowledge graph --help` 含 `--id` (FR-608 用例 #21)
     - source-marker 跨命令断言：`CLI_SOURCE_KNOWLEDGE_LINK` 以 `"cli:"` 开头 (FR-607)
     - smoke test：`recommend` 单次调用 < 1.5s (NFR-603 用例 #24)
  5. 运行 `pytest tests/ -q` 验证 ≥ 451 + F006 新增数（NFR-601）
- **Acceptance**:
  - `tests/test_documentation.py` 全绿（含 ≥3 条新增 grep）
  - `tests/test_cli.py` 全绿（含 cross-cutting 断言）
  - `pytest tests/ -q` 全绿，passed 数 = 451 + F006 总新增数
  - `pyproject.toml` `git diff main..` 无 dependency 行变化（NFR-602）
  - 用户指南中能 grep 到 3 个新子命令字符串
- **Verify**:
  - `pytest tests/ -q` final
  - `git diff main -- pyproject.toml` 输出空
  - `grep "garage recommend" docs/guides/garage-os-user-guide.md` 命中
- **依赖**: T1–T4（需要全部子命令 handler 已就位）
- **Files**: `docs/guides/garage-os-user-guide.md`、`README.md`、`README.zh-CN.md`、`tests/test_documentation.py`、`tests/test_cli.py`

---

## 6. Task Queue Projection 与 Active Task Selection

### 6.1 Queue Projection

| 当前完成任务 | next-ready 候选集 | hard blockers |
|------------|-----------------|--------------|
| (未开始) | T1 | 无 |
| T1 完成 | T2, T3, T4 | 无（三者互不依赖，都依赖 T1） |
| T1 + T2 完成 | T3, T4 | 无 |
| T1 + T3 完成 | T2, T4 | 无 |
| T1 + T2 + T3 + T4 完成 | T5 | 无 |
| T1–T5 完成 | (none, → `hf-test-review`) | 无 |

### 6.2 Active Task Selection Priority

按以下优先级选唯一 Current Active Task：

1. **风险驱动**：`_recommend_experience` 多规则 + 多 helper 是 F006 最高新颖度（T1）；多 type 报错路径耦合 T1 / T3 / T4
2. **依赖广度**：T1 被 T2/T3/T4 全部依赖 → 优先
3. **顺序兜底**：同优先级按 T 编号

建议线性序列：**T1 → T2 → T3 → T4 → T5**（T2/T3/T4 在 T1 完成后理论可并行，但 solo 模式按编号顺序更稳，且 T2 触动 `recommendation_service.py`，单独完成可立刻验证 CON-605 不变）。

### 6.3 实现顺序与依赖图

```
T1 (helpers) ──┬─→ T2 (recommend handler + build_from_query)
               ├─→ T3 (knowledge link handler)
               └─→ T4 (knowledge graph handler)
                                              └─→ T5 (docs + cross-cutting + regression gate)
```

每任务作为独立 commit。建议 commit message 模板：`feat(F006-T<N>): <summary>`。

---

## 7. 任务计划评审前自检

- [x] 每任务独立可验证（INVEST Independent + Testable）
- [x] 任务粒度均匀（T1 略大但承担两个独立 helper；T2-T4 各 1 命令；T5 收尾）
- [x] 强弱依赖标注清楚（T2/T3/T4 → T1；T5 → T1-T4）
- [x] 每任务覆盖至少 1 个 FR / NFR / CON / 设计章节
- [x] 设计 §13.2 用例 1-26 全覆盖
- [x] 不引入未在设计范围内的工件 / 模块 / 依赖
- [x] 退出标准可机器判定（pytest 退出码 + grep）
- [x] 风险点显式标注（去重保序 / ordering 稳定 / `build()` 不动 spot-check）
- [x] task plan 文档已落盘到约定路径

下一步：派发 `hf-tasks-review` reviewer subagent。

---

## 8. 开放问题

| 编号 | 问题 | 阻塞 / 非阻塞 | 当前判断 |
|------|------|-------------|---------|
| OT-601 | T1 `_recommend_experience` 是否要为权重微调留可配置入口？ | 非阻塞 | 否。spec FR-602 已固定权重；可调性 deferred。 |
| OT-602 | T5 文档段是否要补 `garage memory review` 与 `garage recommend` 的对比说明？ | 非阻塞 | 是（轻）。在 user guide 段尾顺手加一段 "When to use which"，避免用户混淆。 |
| OT-603 | T2 `build_from_query` 的 unit test 是否要单独建 test class？ | 非阻塞 | 否（OD-602 已答）。挂在 `TestRecommend` class 即可。 |
