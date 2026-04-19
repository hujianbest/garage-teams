# Test Review — F005 Garage Knowledge Authoring CLI

- 评审 skill: `hf-test-review`
- Profile: `standard`
- 评审日期: 2026-04-19
- 评审对象:
  - `tests/test_cli.py`（注释 `# F005 — Knowledge / Experience authoring CLI` 起到文件末，行 1130–2066；新增 8 个 test class，34 个测试函数）
  - `tests/test_documentation.py`（行 65–106，新增 2 个文档 grep 测试）
  - 实现承载: `src/garage_os/cli.py` 行 31–58（FMT/source 常量）、617–963（F005 helper + handler）、build_parser 中的 sub-parser 接入
- 关联工件:
  - 规格: `docs/features/F005-garage-knowledge-authoring-cli.md`
  - 设计: `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md`
  - 任务: `docs/tasks/2026-04-19-garage-knowledge-authoring-cli-tasks.md`
- 评审基线:
  - main 基线 414 测试 → F005 新增 36 → 共 450
  - `python3 -m pytest tests/ -q` ⇒ `450 passed in 25.36s`（本次会话核实）

---

## 结论

**通过**

测试在所有 6 个评审维度（TT1–TT6）上均 ≥ 8/10。FR-501～510、NFR-501/503/504/505、CON-503/504/505、ADR-502/503 与设计 §10.2.1 / §13.2 案例 1–30 全部有对应断言，错误路径与 v1.1 不变量得到结构化覆盖，下游可直接进入 `hf-code-review`。

---

## 多维评分

| 维度 | 分数 | 评价 |
|------|------|------|
| `TT1` fail-first 有效性 | 9/10 | 测试在新会话核实 `450 passed`，新增 36 个全部映射到本次实现的新 handler / 常量；通过 import `KNOWLEDGE_*_FMT` 等新常量从 `garage_os.cli` 直接耦合本次实现，旧基线下导入即失败，构成有效 GREEN 锚点。 |
| `TT2` 行为 / 验收映射 | 9/10 | 每个 test class docstring 标明 FR / CON / ADR；设计 §13.2 案例 1–30 全覆盖；test 函数名携带行为语义（`test_add_id_collision_same_second`、`test_edit_does_not_pollute_publisher_metadata`、`test_experience_delete_happy_and_prunes_index`）。 |
| `TT3` 风险覆盖 | 9/10 | 关键风险全部被显式断言：mutex (FR-502/503)、missing field (FR-503)、not-found (3 子命令)、ID collision（同秒 monkeypatch + 显式 ID collision）、index pruning (FR-507b key assertion 直接读 `index.json`)、publisher 元数据非污染（构造 `published_from_candidate` 模拟 publisher entry，验证 edit 后保留）。 |
| `TT4` 测试设计质量 | 9/10 | 全部使用 `tmp_path`，每个测试 `main(["init", "--path", str(tmp_path)])` 自起；mock 仅限于 `_now_default`（设计 §T1 Risk 显式要求的注入点）；其余通过真实 `KnowledgeStore` / `ExperienceIndex` / 真实文件系统断言；不出现 mock-的-行为-断言。CRUD loop 在单一 fixture 内顺序串联 6 步 (T6 风险点 OT-502 已正面处理)。 |
| `TT5` 新鲜证据完整性 | 9/10 | 当次会话 `python3 -m pytest tests/ -q` 输出 `450 passed`（414 基线 + 36 新增）冷读可核实；`tests/test_cli.py -q` 单独跑 64 passed；新常量名（`CLI_SOURCE_KNOWLEDGE_ADD` 等）只能由本次实现提供，旧绿不可能成立。 |
| `TT6` 下游就绪度 | 9/10 | 测试质量足以让 `hf-code-review` 判断：handler 选择性覆写、source_artifact 命名空间隔离、ID 生成可复算性、index 一致性、help 自描述全部有断言可挂；下游评审可直接对照测试 ↔ §10.2.1 字段表。 |

---

## 发现项

### Minor（非阻塞，建议在下次接力或文档化时收敛）

- **[minor][LLM-FIXABLE][TT3] `test_add_explicit_id_collision`（test_cli.py:1433）`for _ in range(2)` 后只断言最后一次 `rc` 与 stderr，未显式断言"第一次成功"**
  当前：循环里覆盖 `rc` 与 capsys 缓冲，第二次返回 1 即视为 collision。一旦第一次因副作用失败但 stderr 仍包含 "already exists"，断言会假阳性。
  建议在循环展开为两次显式调用：第一次 `assert rc1 == 0`，第二次 `assert rc2 == 1`，与 `test_add_id_collision_same_second` 风格对齐。

- **[minor][LLM-FIXABLE][TT3] experience add ID 生成只覆盖格式，未覆盖时间盐变化与 collision 分支**
  `_generate_experience_id` 仅由 `test_generate_experience_id_format`（test_cli.py:1817）断言 `exp-YYYYMMDD-` 前缀与 6 hex 长度，未断言"同输入不同秒 → 不同 id"以及 experience 侧 `add` 的 `(rid 已存在 → 退 1 + already-exists 文案)`。当前 cli.py 行 901 在 experience collision 分支复用了 `KNOWLEDGE_ALREADY_EXISTS_FMT`，没有专门的 `EXPERIENCE_ALREADY_EXISTS_FMT`，建议补 1 条对称测试，或在 review record 显式确认这是设计意图（experience 路径与 knowledge 共用文案）。

- **[minor][LLM-FIXABLE][TT4] `TestKnowledgeShow::test_show_happy`（test_cli.py:1657）只断言关键字段出现，未断言"前后顺序 / 空行隔开 / body 在 front matter 之后"**
  设计 §10.1（OD-504）与 FR-504 验收要求 "front matter（人类可读 key: value 块）+ 空行 + content body"。当前 `assert "Hello" in out` 不区分位置；若实现把 body 写在 front matter 之前也能通过。建议加一条 `out.index("version: 1") < out.index("\n\nHello")` 的顺序断言。

- **[minor][LLM-FIXABLE][TT2] CRUD loop 测试（test_cli.py:1956）只断言 exit code，未断言中间步 stdout 文案**
  设计 §13.2 用例 30 + §2.2 SC-2 期望 "每步退出码 0 / 1 + delete 后 show stdout 含 'Not found'"。当前测试只检查 exit code 与 `topic: T2 / version: 2`；建议在 delete 步与 final-show 步加 `KNOWLEDGE_DELETED_FMT.format(...) in out` / `KNOWLEDGE_NOT_FOUND_FMT.format(...) in err` 断言以贯通文案契约。

- **[minor][LLM-FIXABLE][TT2] CON-501 / CON-502 没有专门测试**
  CON-501（subparser 挂在 knowledge / experience 父下，不引顶级命令）与 CON-502（不改 store/index API）当前靠 "全套 450 passed + 设计 §3 追溯表" 间接覆盖。standard profile 下不阻塞；若进 `full` profile 可补一条 `argparse` 顶级 `subcommand` 集合不变断言。

- **[minor][LLM-FIXABLE][TT2] NFR-502（零第三方依赖）无自动化断言**
  当前依赖 review 期 grep 与 `pyproject.toml` 手动比对。可补一条 `tests/test_documentation.py` 风格的 lint：`assert not any(line.startswith("import click") or "typer" in line for line in cli.py.read_text().splitlines())`。standard profile 下不阻塞。

### 没有发现 critical / important 级别问题

---

## 缺失或薄弱项（已在 Minor 中点出，集中复述以便接力）

- experience add ID 生成的"时间盐变化"+"collision 分支"未直接测试（依赖 knowledge 路径同构推断）。
- `knowledge show` 输出顺序契约未断言。
- CRUD loop 中间步 stdout 文案未断言（exit code 已断言）。
- CON-501/502 与 NFR-502 缺机器断言（standard 可接受）。

---

## 维度逐项要点

### TT1 fail-first 有效性
- 36 个新测试全部 import 由本次实现新增的常量与 helper（`CLI_SOURCE_*`、`KNOWLEDGE_*_FMT`、`_generate_entry_id`、`_generate_experience_id`），任何"老仓库无新增 handler 但测试为绿"的 born-green 风险被 import 阶段直接挡掉。
- 实现层 `_now_default` 抽出（cli.py:617）使 `test_add_id_collision_same_second` 能可控复现 collision，证明 RED 是行为缺口而非时序巧合。

### TT2 行为 / 验收映射
- 每个 test class docstring 标注 FR / CON / ADR（如 `class TestKnowledgeEdit: """T2 / FR-503 / FR-509 / CON-503 (v1.1 version+=1)."""`）。
- 设计 §13.2 案例 1–30 与测试函数交叉对应（见下表）。
- §10.2.1 edit 字段覆写表的两个关键不变量（"date 不变" "publisher 元数据不变"）由 `test_edit_overlays_only_specified_fields_and_bumps_version`（断言 topic / content 不变）+ `test_edit_does_not_pollute_publisher_metadata`（断言 `published_from_candidate` 保留）共同覆盖。

#### §13.2 用例 ↔ 测试函数交叉表

| 用例 | 测试函数 |
|------|----------|
| 1 add happy | `TestKnowledgeAdd::test_add_happy_path_writes_entry_with_source_marker` |
| 2 add --from-file | `TestKnowledgeAdd::test_add_from_file` |
| 3 mutex | `TestKnowledgeAdd::test_add_mutex_content_and_file` |
| 4 neither | `TestKnowledgeAdd::test_add_requires_content_or_file` |
| 5 file-not-found | `TestKnowledgeAdd::test_add_from_file_not_found` |
| 6 explicit --id | `TestKnowledgeAdd::test_add_with_explicit_id` |
| 7 same-second collision | `TestKnowledgeAdd::test_add_id_collision_same_second` |
| 8 source_artifact | `TestKnowledgeAdd::test_add_happy_path_writes_entry_with_source_marker` + `TestKnowledgeAuthoringCrossCutting::test_cli_source_markers_use_cli_namespace` |
| 9 edit selective | `TestKnowledgeEdit::test_edit_overlays_only_specified_fields_and_bumps_version` |
| 10 version+=1 | 同上 + `TestKnowledgeEdit::test_edit_monotonic_version` |
| 11 edit missing field | `TestKnowledgeEdit::test_edit_requires_at_least_one_field` |
| 12 edit mutex | `TestKnowledgeEdit::test_edit_mutex_content_and_file` |
| 13 edit not-found | `TestKnowledgeEdit::test_edit_not_found` |
| 14 edit source_artifact | `TestKnowledgeEdit::test_edit_overlays_...` + `TestKnowledgeEdit::test_edit_does_not_pollute_publisher_metadata` |
| 15 show happy | `TestKnowledgeShow::test_show_happy` |
| 16 show not-found | `TestKnowledgeShow::test_show_not_found` |
| 17 delete happy | `TestKnowledgeDelete::test_delete_happy` |
| 18 delete not-found | `TestKnowledgeDelete::test_delete_not_found` |
| 19 experience add multi-skill | `TestExperienceAdd::test_experience_add_happy` |
| 20 artifacts[0]="cli:experience-add" | 同上 + `test_cli_source_markers_use_cli_namespace` |
| 21 experience show happy | `TestExperienceShow::test_experience_show_happy` |
| 22 experience show not-found | `TestExperienceShow::test_experience_show_not_found` |
| 23 experience delete + index pruned | `TestExperienceDelete::test_experience_delete_happy_and_prunes_index`（断言 `index_after` 不再含 `exp-1`） |
| 24 experience delete not-found | `TestExperienceDelete::test_experience_delete_not_found` |
| 25 knowledge --help | `TestKnowledgeAuthoringCrossCutting::test_knowledge_help_lists_all_subcommands` |
| 26 experience --help | `TestKnowledgeAuthoringCrossCutting::test_experience_help_lists_all_subcommands` |
| 27 knowledge add --help | `TestKnowledgeAuthoringCrossCutting::test_knowledge_add_help_lists_all_args` |
| 28 NFR-501 既有未变 | 全套 450 passed 间接覆盖 |
| 29 add < 1.0s | `TestKnowledgeAuthoringCrossCutting::test_add_smoke_under_one_second` |
| 30 CRUD 闭环 | `TestKnowledgeAuthoringCrossCutting::test_crud_loop` |

### TT3 风险覆盖
- mutex / missing-field / not-found / file-not-found / no-garage-dir / collision（hash & explicit）全部覆盖。
- v1.1 不变量（`version+=1`）双重覆盖：`test_edit_overlays_only_specified_fields_and_bumps_version`（一次 → version=2）+ `test_edit_monotonic_version`（连续 3 次 → 2/3/4）。
- publisher 元数据保护：`test_edit_does_not_pollute_publisher_metadata` 直接构造 `KnowledgeEntry(source_artifact="published_by:F003", published_from_candidate="cand-x")` 写盘后走 CLI edit，证明 `source_artifact` 被覆写而 `published_from_candidate` 保留。
- ADR-503 命名空间：`test_cli_source_markers_use_cli_namespace` 显式断言三个常量都以 `"cli:"` 起头；`test_experience_add_happy` 第二条 assert 同样断言 `data["artifacts"][0].startswith("cli:")`。

### TT4 测试设计质量
- 隔离：所有测试用 `tmp_path` 起新 `.garage/`，无共享状态污染。
- mock 边界：仅 `monkeypatch.setattr("garage_os.cli._now_default", lambda: fixed)`（设计 §T1 Risk 推荐的注入点），其余真跑文件系统 + KnowledgeStore + ExperienceIndex。
- 命名：`test_<command>_<scenario>` 一致；`TestKnowledgeAuthoringCrossCutting` 名实相符。
- 复用：`TestKnowledgeEdit._add` 私有 helper 减少重复，但仍保持 happy-path 在 add 测试本身覆盖（无双层间接）。

### TT5 新鲜证据完整性
- 本次会话核实命令: `python3 -m pytest tests/ -q` ⇒ `450 passed in 25.36s`；`python3 -m pytest tests/test_cli.py -q` ⇒ `64 passed`。
- F005 新增测试 36 个 = 414 → 450 增量与任务工件声明一致。

### TT6 下游就绪度
- 测试覆盖足够支持 `hf-code-review` 判断：handler 行为、字段覆写表、source_artifact 命名空间、ID 生成可复算性、index 一致性、help 自描述全部有断言挂钩。
- Minor 项不会污染 code review 判断（属于补强建议，不属于"代码可能错但测试没接住"的情形）。

---

## Anti-Pattern 检查

| Pattern | 状态 |
|---------|------|
| TA1 born-green | 未触发：新常量/helper 由本次实现首次引入，旧仓库 import 即失败 |
| TA2 happy-path-only | 未触发：mutex / missing / not-found / collision / publisher 元数据保护均覆盖 |
| TA3 mock overreach | 未触发：仅 `_now_default` 注入；其余真跑 |
| TA4 no acceptance link | 未触发：每个 test class docstring 标注 FR / CON / ADR；§13.2 案例全映射 |
| TA5 stale evidence | 未触发：当次会话 `pytest tests/ -q` 重跑确认 450 passed |

---

## 下一步

`hf-code-review`

测试基线已稳定，36 个新增测试与 414 个回归共 450 passed；进入 code review 评审 cli.py 实现质量、命名一致性、复用边界与 KnowledgeStore/ExperienceIndex 调用规范性。

---

## 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-code-review",
  "record_path": "docs/reviews/test-review-F005-knowledge-authoring-cli.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][TT3] test_add_explicit_id_collision 仅断言最后一次 rc，可补显式 rc1==0 / rc2==1",
    "[minor][LLM-FIXABLE][TT3] experience add 缺 ID 时间盐变化 & collision 分支专项断言",
    "[minor][LLM-FIXABLE][TT4] knowledge show 输出顺序（front matter→空行→body）未断言",
    "[minor][LLM-FIXABLE][TT2] CRUD loop 仅断言 exit code，未断言中间步 stdout 文案",
    "[minor][LLM-FIXABLE][TT2] CON-501/502 与 NFR-502 缺机器断言（standard profile 可接受）"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT3",
     "summary": "test_add_explicit_id_collision 循环写法只断言末次 rc，可拆为两次显式调用以排除假阳性"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT3",
     "summary": "experience add ID 生成缺时间盐变化与 collision 分支专项测试，依赖 knowledge 路径同构推断"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT4",
     "summary": "TestKnowledgeShow.test_show_happy 未断言 front matter 与 body 的相对顺序与空行隔开"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT2",
     "summary": "CRUD loop 测试在 delete 与 final-show 步未断言 KNOWLEDGE_DELETED_FMT / NOT_FOUND_FMT 文案"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT2",
     "summary": "CON-501（subparser 父级）/ CON-502（store API 不变）/ NFR-502（零第三方依赖）目前由间接证据覆盖，可补机器断言"}
  ]
}
```
