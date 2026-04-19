# Traceability Review — F005 Garage Knowledge Authoring CLI

- 评审 skill: `hf-traceability-review`
- Workflow Profile / Execution Mode: `standard` / `auto`
- Workspace Isolation: `in-place`
- Branch: `cursor/f005-knowledge-add-cli-177b`
- Reviewer: cursor cloud agent (hf-traceability-review subagent)
- 评审日期: 2026-04-19
- 当次会话证据:
  - `python3 -m pytest tests/ -q` ⇒ `451 passed in 25.35s`（414 基线 + F005 新增 37）

---

## 评审范围

- topic / 任务: F005 Garage Knowledge Authoring CLI（让 Stage 2 飞轮能从终端起转）
- 相关需求: `docs/features/F005-garage-knowledge-authoring-cli.md`（FR-501..510 / NFR-501..505 / CON-501..505 / ADR none in spec — ADR-501..503 在 design 内）
- 相关设计: `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md`（D005，含 ADR-501 / 502 / 503 + §10.2.1 字段覆写表 + §13.2 30 用例）
- 相关任务: `docs/tasks/2026-04-19-garage-knowledge-authoring-cli-tasks.md`（T1..T6）
- 相关实现:
  - `src/garage_os/cli.py` 行 26–63（FMT / source 常量）、617–984（F005 helper + 7 handler）、1024–1196（build_parser knowledge/experience 子树）、1274–1347（main dispatch）
  - 文档: `docs/guides/garage-os-user-guide.md` §"Knowledge authoring (CLI)" 行 334–402；`README.md`:49；`README.zh-CN.md`:49
- 相关测试 / 验证:
  - `tests/test_cli.py` 行 1183–2066（8 个新 test class，37 个新增测试函数；含 `TestKnowledgeAdd` / `TestKnowledgeEdit` / `TestKnowledgeShow` / `TestKnowledgeDelete` / `TestExperienceAdd` / `TestExperienceShow` / `TestExperienceDelete` / `TestKnowledgeAuthoringCrossCutting`）
  - `tests/test_documentation.py` 行 65–106（2 个新 grep 测试）
- 上游 review 链:
  - spec-review r1 `需修改` → r2 `通过`
  - design-review r1 `通过`（4 minor inline 收敛）
  - tasks-review r1 `通过`
  - test-review `通过`（5 minor LLM-FIXABLE）
  - code-review `通过`（5 minor LLM-FIXABLE）
- 上游 approval 链:
  - `docs/approvals/F005-spec-approval.md`（Round 2 通过 + auto mode）
  - `docs/approvals/F005-design-approval.md`（Round 1 通过 + 4 minor 内联收敛）
  - `docs/approvals/F005-tasks-approval.md`（Round 1 通过 + §6.1/§6.2 inline 收敛）

---

## Precheck

| 检查项 | 结果 |
|--------|------|
| 上游工件稳定可定位 | ✅ spec / design / tasks / 4 个 review 记录 / 3 个 approval 全部就绪 |
| 实现交接块 | ✅ code-review record 已建立 §"设计与约束覆盖核对" 22 行交叉表锚定到 `cli.py` 行号 |
| 上游 review verdict 一致 | ✅ test-review `通过`、code-review `通过` → 准予进入 traceability review |
| route / stage / profile | ✅ standard / auto；与上游 evidence 一致 |
| 451 tests 全绿 | ✅ 当次会话 `python3 -m pytest tests/ -q` 复跑核实 |

→ Precheck 通过，进入正式审查。

---

## 多维评分

| 维度 | 分数 | 评价 |
|------|------|------|
| `TZ1` 规格 → 设计追溯 | 9/10 | D005 §3 追溯表 22 行覆盖全部 FR-501..510 / NFR-501..505 / CON-501..505；FR-507 已在 spec 中拆为 FR-507a/b，design §3 同样独立成行；ADR-501/502/503 各自承接 ADR-501（cli.py 单文件） / FR-508（ID 时间盐） / FR-509（cli: 命名空间）。无规格条款被设计静默丢弃。 |
| `TZ2` 设计 → 任务追溯 | 9/10 | tasks plan §4 追溯表 24 行将 D005 §3 / §10.2.1 / §13.2 全部锚定到 T1..T6；§10.2.1 字段覆写表显式分配给 T2；§13.2 用例 1–30 在 T1–T6 acceptance 中逐项命中（test-review §"§13.2 用例 ↔ 测试函数交叉表" 二度验证 30/30 全覆盖）。 |
| `TZ3` 任务 → 实现追溯 | 9/10 | T1..T6 全部 acceptance 由 `cli.py` 实际 handler 承载：T1=`_knowledge_add` + `_generate_entry_id` + `_resolve_content` (cli.py:633–761)；T2=`_knowledge_edit` (cli.py:764–820)；T3=`_knowledge_show/_delete` (cli.py:823–881)；T4=`_experience_add` + `_generate_experience_id` (cli.py:693–702, 884–937)；T5=`_experience_show/_delete` (cli.py:940–984)；T6=user guide §"Knowledge authoring (CLI)" + 双 README CLI 命令清单 + `tests/test_documentation.py:72–106` + `tests/test_cli.py::TestKnowledgeAuthoringCrossCutting`（行 1974–2066）。任务边界（仅触碰 `cli.py` / `tests/test_cli.py` / `tests/test_documentation.py` / 用户指南 / 双 README）实测无溢出。 |
| `TZ4` 实现 → 验证追溯 | 9/10 | 451 passed 当次会话冷读核实；test-review §"§13.2 用例 ↔ 测试函数交叉表" 30/30 映射；CON-503（v1.1 `version+=1`）由 `test_edit_overlays_only_specified_fields_and_bumps_version` + `test_edit_monotonic_version` 双重承接；FR-507b 索引摘除由 `test_experience_delete_happy_and_prunes_index` 直接读 `.garage/knowledge/.metadata/index.json` 断言；ADR-503 cli: 命名空间由 `test_cli_source_markers_use_cli_namespace` 与 `tests/test_documentation.py::test_user_guide_documents_knowledge_authoring_cli`（grep `cli:knowledge-add` / `cli:knowledge-edit` / `cli:experience-add`）双向接住。 |
| `TZ5` 漂移与回写义务 | 8/10 | 仅一处文字-级偏离（已被 code-review 显式记录、handler 自身有 docstring 说明）：`_experience_show`（cli.py:940–968）直接 `read_text + json.loads`，design §3 traceability 表写的是 "调 `ExperienceIndex.retrieve()`"。当前 handler docstring 已显式陈述"intentionally bypasses retrieve() to preserve on-disk JSON shape"；不构成 undocumented behavior（内部已就地解释 + code-review minor finding 已建议下次接力收敛），不阻塞 traceability。无其它工件需要回写。 |
| `TZ6` 整体链路闭合 | 9/10 | 当前 spec / design / tasks / impl / tests / 文档六者状态一致；451 全绿；3 个 approval 与 5 个 review record 形成完整闸门轨迹；`pyproject.toml` 在 main..HEAD 无 diff（NFR-502 机器证据 — 见 code-review §证据表）；source-marker `cli:` 不变量在 spec / design / 代码常量 / handler 赋值 / 测试 / 用户指南五处一致。具备进入 `hf-regression-gate` 的整体一致性。 |

任一关键维度 ≥ 6，全部 ≥ 8 → 准予通过。

---

## 链接矩阵

### 1) 规格 → 设计 → 任务 → 实现 → 测试

| Spec 锚点 | Design 承接（D005） | Tasks 承接（T005） | 实现锚点（`cli.py`） | 测试锚点 |
|-----------|---------------------|--------------------|----------------------|----------|
| FR-501 knowledge add | §3 行 1；§9.2 参数表；§10.1 sequence | T1 (acceptance #1) | `_knowledge_add` 行 714–761；subparser 行 1047–1072；dispatch 行 1282–1291 | `TestKnowledgeAdd::test_add_happy_path_writes_entry_with_source_marker` 等 8 例 |
| FR-502 mutex / from-file | §3 行 2；§10.1 H→H validate | T1 (acceptance #3..#6) | `_resolve_content` 行 640–670；`ERR_CONTENT_AND_FILE_MUTEX` / `ERR_ADD_REQUIRES_CONTENT` / `ERR_FILE_NOT_FOUND_FMT` 行 49–51 | `TestKnowledgeAdd::test_add_mutex_content_and_file` / `_requires_content_or_file` / `_from_file_not_found` |
| FR-503 selective edit + version+=1 | §3 行 3；§9.3 参数表；§10.2 sequence + §10.2.1 字段表 | T2 (acceptance #1..#7) | `_knowledge_edit` 行 764–820；selective overlay 行 808–815；`update()` 调用 + `entry.version` 回读 行 818–819 | `TestKnowledgeEdit::test_edit_overlays_only_specified_fields_and_bumps_version` / `_monotonic_version` / `_requires_at_least_one_field` / `_mutex_content_and_file` / `_not_found` / `_does_not_pollute_publisher_metadata` |
| FR-504 show pretty-print | §3 行 4；§9.1 子命令树；OD-504 derived 字段要求 | T3 (acceptance #1..#2, #5) | `_knowledge_show` 行 823–858（含 derived `version` / `source_artifact`） | `TestKnowledgeShow::test_show_happy` / `_not_found` |
| FR-505 delete | §3 行 5；§9.1 子命令树 | T3 (acceptance #3..#4) | `_knowledge_delete` 行 861–881 | `TestKnowledgeDelete::test_delete_happy` / `_not_found` |
| FR-506 experience add | §3 行 6；§9.4 参数表 | T4 (acceptance #1..#5) | `_experience_add` 行 884–937；`_generate_experience_id` 行 693–702；subparser 行 1135–1196 | `TestExperienceAdd::test_experience_add_happy` 等 |
| FR-507a experience show | §3 行 7；§9.1 子命令树 | T5 (acceptance #1..#2) | `_experience_show` 行 940–968（带 docstring 解释 §TZ5 偏离） | `TestExperienceShow::test_experience_show_happy` / `_not_found` |
| FR-507b experience delete + 索引摘除 | §3 行 8；§10.3 sequence | T5 (acceptance #3..#5) | `_experience_delete` 行 971–984 | `TestExperienceDelete::test_experience_delete_happy_and_prunes_index` / `_not_found` |
| FR-508 ID 时间盐 + collision | §3 行 9；ADR-502 | T1 (acceptance #7..#10) + T4 (acceptance #4) | `_generate_entry_id` 行 673–690；`_generate_experience_id` 行 693–702；retrieve()-based collision check 行 744–746 / 912–914；`_now_default` 行 622–630 | `TestKnowledgeAdd::test_add_id_collision_same_second` / `_with_explicit_id` / `_explicit_id_collision`；`TestExperienceAdd::test_generate_experience_id_format` |
| FR-509 source markers | §3 行 10；ADR-503 | T1 / T2 / T4 (source_artifact) + T6 (cross-cutting) | `CLI_SOURCE_KNOWLEDGE_ADD` / `_KNOWLEDGE_EDIT` / `_EXPERIENCE_ADD` 行 61–63；handler 赋值 行 757、816、927 | `TestKnowledgeAuthoringCrossCutting::test_cli_source_markers_use_cli_namespace`；`TestKnowledgeEdit::test_edit_does_not_pollute_publisher_metadata`；`tests/test_documentation.py::test_user_guide_documents_knowledge_authoring_cli`（grep `cli:` 三个常量） |
| FR-510 help discoverable | §3 行 11；§9 三参数表 | T6 (acceptance #4) | `build_parser()` knowledge / experience subparsers 行 1024–1196，每个 `add_argument(help=...)` 完整 | `TestKnowledgeAuthoringCrossCutting::test_knowledge_help_lists_all_subcommands` / `_experience_help_lists_all_subcommands` / `_knowledge_add_help_lists_all_args` |
| NFR-501 zero regression | §3 行 12；§11 NFR mapping | T6 acceptance #5 + T1..T5 不修改既有断言 | 既有 414 测试 0 修改；新增量限 `cli.py` 新代码块 | 当次 `pytest tests/ -q` ⇒ `451 passed`（414 + 37） |
| NFR-502 zero new dep | §3 行 13；§11 NFR mapping | T6 acceptance #4 (`pyproject.toml` git diff 空) | `cli.py` import 闭包仅 stdlib + `garage_os.*`（行 1–80） | code-review §证据表 `git diff main..HEAD -- pyproject.toml` ⇒ 无差 |
| NFR-503 < 1.0s | §3 行 14；§11 NFR mapping | T6 acceptance #4 smoke test | `_knowledge_add` O(1) IO，由 `KnowledgeStore.store()` 承担 | `TestKnowledgeAuthoringCrossCutting::test_add_smoke_under_one_second` |
| NFR-504 stdout 常量 | §3 行 15；§9.5 常量清单 | T1..T5 (每任务引入对应 FMT) + T6 grep | 模块顶层 `KNOWLEDGE_*_FMT` / `EXPERIENCE_*_FMT` / `ERR_*` 行 31–55 | 全部 success / failure 断言走 `FMT.format(...) in out/err` 风格（test-review TT2 已核） |
| NFR-505 doc sync | §3 行 16；§11 NFR mapping | T6 acceptance #1..#3 | `docs/guides/garage-os-user-guide.md`:334–402；`README.md`:49；`README.zh-CN.md`:49 | `tests/test_documentation.py::test_user_guide_documents_knowledge_authoring_cli`（11 个 token）+ `test_readmes_list_new_cli_subcommands`（双 README × 7 token） |
| CON-501 顶级命令复用 | §3 行 17（`experience` 是 garage 二级 subparser，approval-time 已澄清） | T1..T5 subparser 挂在父级 | `experience` 在 `subparsers.add_parser("experience", ...)` 行 1130；`knowledge add/edit/show/delete` 挂在 `knowledge_subparsers` 行 1029–1127 | 间接覆盖（standard profile 不要求专项断言；test-review 已标记 minor） |
| CON-502 不改 store/index API | §3 行 18 | T1..T5 仅调公开方法 | 仅调 `KnowledgeStore.{store, update, retrieve, delete}` 与 `ExperienceIndex.{store, retrieve, delete}`，方法签名 0 修改 | code-review CR5 范围守卫专项核实 |
| CON-503 v1.1 `version+=1` | §3 行 19 | T2 acceptance #6 | `_knowledge_edit` 行 818 调 `update()` → 行 819 回读 `entry.version` 写 stdout | `TestKnowledgeEdit::test_edit_monotonic_version`（连续 3 次 → 2/3/4） |
| CON-504 source_artifact 不冲突 | §3 行 20；ADR-503 | T1 / T2 / T4 / T6 | `cli:knowledge-add` / `cli:knowledge-edit` / `cli:experience-add` 三常量集中 行 61–63；与 publisher path-style artifact 命名空间分离 | `test_cli_source_markers_use_cli_namespace` 显式断言三常量都以 `"cli:"` 起头；`test_edit_does_not_pollute_publisher_metadata` 反向接住 publisher 元数据保留 |
| CON-505 不变形 markdown body | §3 行 21 | T1 acceptance #1 | `entry.content = content` 直传，无 trim / 规范化（行 754, 811） | `TestKnowledgeAdd::test_add_from_file`（断言 entry.content == 文件 UTF-8 全文） |
| ADR-501 单文件 | §3 行 17 ADR-501 落地 | T1..T6 不引入新 .py | 全部新增量在 `cli.py` 一文件内（708 → 1372 行） | code-review CR5 + `git diff` 文件清单 |
| ADR-502 ID 时间盐秒精度 | ADR-502 决策段 | T1 / T4 ID helper | `_generate_entry_id` 行 687 `now.replace(microsecond=0).isoformat()` | `TestKnowledgeAdd::test_add_id_collision_same_second`（monkeypatch `_now_default` 锁秒） |
| ADR-503 cli: 前缀命名空间 | ADR-503 决策段（含 publisher artifacts 共存澄清） | T1 / T2 / T4 / T6 cross-cutting | `CLI_SOURCE_*` 三常量；user guide 行 391–393 显式列出三个值 | `test_cli_source_markers_use_cli_namespace` + `test_user_guide_documents_knowledge_authoring_cli`（grep 三 token） |
| 设计 §10.2.1 字段覆写表 | §10.2.1 字段表 | T2 acceptance（按表逐项执行） | `_knowledge_edit` 行 808–816 与表格 11 行字段一一对应（id/type/date/published_from_candidate 等不动；topic/content/tags/status/source_artifact 受控覆写） | `test_edit_overlays_only_specified_fields_and_bumps_version` + `test_edit_does_not_pollute_publisher_metadata` |
| 设计 §13.2 用例 1–30 | §13.2 测试金字塔 | T1..T6 全覆盖 | n/a (测试侧) | test-review §"§13.2 用例 ↔ 测试函数交叉表" 30/30 |

### 2) Review 闸门链

| 阶段 | Review 记录 | Verdict | Approval |
|------|------------|---------|----------|
| Spec | `docs/reviews/spec-review-F005-knowledge-authoring-cli.md` (r1) → `-r2.md` (r2) | r1 `需修改` → r2 `通过` | `docs/approvals/F005-spec-approval.md` |
| Design | `docs/reviews/design-review-F005-knowledge-authoring-cli.md` | `通过`（4 minor inline 收敛） | `docs/approvals/F005-design-approval.md` |
| Tasks | `docs/reviews/tasks-review-F005-knowledge-authoring-cli.md` | `通过`（3 minor inline 收敛） | `docs/approvals/F005-tasks-approval.md` |
| Test | `docs/reviews/test-review-F005-knowledge-authoring-cli.md` | `通过`（5 minor LLM-FIXABLE） | n/a（standard profile 不要求 test approval） |
| Code | `docs/reviews/code-review-F005-knowledge-authoring-cli.md` | `通过`（5 minor LLM-FIXABLE） | n/a（standard profile 不要求 code approval） |
| Traceability | 本文档 | 见结论 | n/a |

### 3) Source-marker (`cli:`) 不变量端到端验证

| 层 | 锚点 | 证据 |
|----|------|------|
| Spec | FR-509 行 250–256；术语 §12 "来源标记" | spec 强制 `cli:knowledge-add` / `cli:knowledge-edit` / `cli:experience-add` |
| Design | ADR-503 行 177–200（"区分性依赖 'cli:' 前缀作为命名空间约定"） | publisher 与 CLI 路径靠前缀区分 |
| Code 常量 | `cli.py:61–63` `CLI_SOURCE_KNOWLEDGE_ADD` / `_KNOWLEDGE_EDIT` / `_EXPERIENCE_ADD` | 三常量集中定义在模块顶部 |
| Code 赋值 | `cli.py:757`（add）、`cli.py:816`（edit 强制覆写）、`cli.py:927`（experience add `artifacts=[CLI_SOURCE_EXPERIENCE_ADD]`） | 路径无遗漏 |
| Tests | `TestKnowledgeAuthoringCrossCutting::test_cli_source_markers_use_cli_namespace`；`TestKnowledgeEdit::test_edit_does_not_pollute_publisher_metadata` | 正向 + 反向（不污染 publisher）双断言 |
| 用户文档 | `docs/guides/garage-os-user-guide.md:391–393`；`tests/test_documentation.py:84–86`（grep `cli:knowledge-add` / `cli:knowledge-edit` / `cli:experience-add`） | 用户指南显式列出 + 文档测试机器接住 |

### 4) v1.1 `version+=1` 不变量端到端验证

| 层 | 锚点 | 证据 |
|----|------|------|
| Spec | CON-503 行 318；FR-503 验收 #5 | "edit 走 update()，version+=1，CLI 不可绕开" |
| Design | §3 CON-503 trace；§10.2 mermaid + §10.2.1 字段表（version 由 update() 内部 +=1） | `update()` mutates 在 §10.2 sequence 显式 |
| Tasks | T2 acceptance "多次 edit 同一 entry → version 单调 +1（CON-503 / F004 v1.1 不变量延伸）" | 任务粒度独立 |
| Code | `_knowledge_edit` 行 818 `knowledge_store.update(entry)` → 行 819 `entry.version` 回读写 stdout `KNOWLEDGE_EDITED_FMT` | handler 不绕过 store |
| Tests | `TestKnowledgeEdit::test_edit_overlays_only_specified_fields_and_bumps_version`；`test_edit_monotonic_version`（version=2/3/4） | 单调递增专项断言 |

---

## 发现项

### Minor / LLM-FIXABLE（非阻塞，下次接力或 increment 收敛即可）

- **[minor][LLM-FIXABLE][TZ5][ZA3] `_experience_show` 实现路径与 design §3 traceability 文字描述不严格一致**
  - 位置: `src/garage_os/cli.py:940–968`；design `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md` §3 行 73 / §10.3 数据流
  - 现象: design §3 / §10.3 写的是 "调 `ExperienceIndex.retrieve()`"，handler 实际为 `record_path.read_text() + json.loads()`。
  - 已就地缓解: handler docstring（cli.py:940–951）显式说明 "intentionally bypasses retrieve() to preserve raw on-disk JSON shape including `cli:experience-add` source marker"；code-review 已记录为 minor LLM-FIXABLE finding #2。
  - 影响: 不构成 undocumented behavior（已有就地解释）；不影响 451 全绿。下次接力可二选一：(a) 在 design §3 / §10.3 文字补一行 "show 直接读盘以保留 on-disk shape" 注脚；或 (b) 把 handler 改回 `ExperienceIndex.retrieve()` 路径。
  - 建议: 不阻塞 traceability review；可在后续 increment 或维护周期一并收敛。

- **[minor][LLM-FIXABLE][TZ4] CON-501 / CON-502 / NFR-502 缺机器化断言**
  - 位置: tests / `pyproject.toml` lint
  - 现象: 当前由 "全套 451 passed + design §3 trace 表 + code-review 期 git diff" 间接覆盖；test-review 已记录同名 minor finding。
  - 影响: standard profile 下不阻塞；若未来切 `full` profile 应补 1 条顶级 subcommand 集合断言 + 1 条 third-party import 黑名单 lint。
  - 建议: 不阻塞 traceability review。

### 没有发现 critical / important 级别问题

---

## 追溯缺口

无 spec 条款被设计 / 任务 / 实现 / 测试静默丢弃。
无 orphan 代码（所有新 handler / helper 在 `main()` dispatch 中均有调用，被测试覆盖；code-review CA5 已专项核实）。
仅一处文字-级偏离（`_experience_show` 实现 vs design 描述），handler docstring 已就地说明。

---

## 需要回写或同步的工件

- 无强制回写项（`_experience_show` 偏离已被 code-review minor finding 跟踪，handler docstring 内联解释充分）。

可选 / 建议（不阻塞）:

- design `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md` §3 / §10.3 中可加一行注脚说明 `_experience_show` 直接读盘的设计意图；或把 handler 改回 `ExperienceIndex.retrieve()` 二选一。
- 后续若进入 `full` profile，可补 CON-501 / CON-502 / NFR-502 的机器断言。

---

## 整体闭合判定

| 检查 | 结果 |
|------|------|
| spec→design 双向一致 | ✅ FR / NFR / CON / ADR 全部双向可追 |
| design→tasks 双向一致 | ✅ §13.2 用例 1–30、§10.2.1 字段表全部分配到任务 |
| tasks→impl 双向一致 | ✅ T1..T6 acceptance 全部由 `cli.py` handler / 文档 / 测试承载，无任务空挂 |
| impl→tests 双向一致 | ✅ 451 全绿 + 30/30 用例 ↔ 测试函数交叉映射 + source marker 跨命令断言 |
| review chain 完整 | ✅ spec(r1+r2) → design → tasks → test → code 全部 `通过` |
| approval chain 完整 | ✅ spec / design / tasks 三个 approval（standard profile 充分） |
| source-marker `cli:` 不变量 | ✅ 五层一致 |
| v1.1 `version+=1` 不变量延伸 | ✅ 五层一致 + 双重测试断言 |

→ 整体证据链闭合，可进入 `hf-regression-gate`。

---

## 下一步

`hf-regression-gate`

- 准予进入回归门：当前 `pytest tests/ -q ⇒ 451 passed` 已在本次评审会话冷读核实，但 regression gate 仍应按其自身 SOP 重跑全 suite + 复核 baseline 414 + F005 新增 37 的增量分布。
- 不需要回流到 `hf-test-driven-dev` 或 `hf-workflow-router`（无 critical / important finding，无核心断链）。

---

## 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-regression-gate",
  "record_path": "docs/reviews/traceability-review-F005-knowledge-authoring-cli.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][TZ5] _experience_show 实现 (cli.py:940-968) 直接读 JSON 文件，与 design §3/§10.3 文字 '调 ExperienceIndex.retrieve()' 不严格一致；handler docstring 已就地解释，code-review 已跟踪，不阻塞",
    "[minor][LLM-FIXABLE][TZ4] CON-501/CON-502/NFR-502 当前由间接证据覆盖，缺机器化断言；standard profile 可接受"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ5",
      "summary": "_experience_show 实现绕过 ExperienceIndex.retrieve() 直接读盘 (cli.py:940-968)，与 design §3 traceability 表文字不一致；handler docstring 已就地说明意图，建议下次接力在 design 加注脚或改回 retrieve()"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "TZ4",
      "summary": "CON-501（subparser 父级）/ CON-502（store API 不变）/ NFR-502（零第三方依赖）目前由 451 全绿 + design §3 trace 表 + git diff 间接覆盖；可补机器断言（standard profile 不阻塞）"
    }
  ]
}
```
