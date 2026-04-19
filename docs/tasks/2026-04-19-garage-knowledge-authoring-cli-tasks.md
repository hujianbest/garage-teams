# T005: Garage Knowledge Authoring CLI 任务计划

- 状态: 已批准（auto-mode approval；见 `docs/approvals/F005-tasks-approval.md`）
- 主题: F005 — Garage Knowledge Authoring CLI（让 Stage 2 飞轮能从终端起转）
- 关联规格: `docs/features/F005-garage-knowledge-authoring-cli.md`
- 关联设计: `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md`
- 关联审批:
  - `docs/approvals/F005-spec-approval.md`
  - `docs/approvals/F005-design-approval.md`
- 关联评审:
  - `docs/reviews/spec-review-F005-knowledge-authoring-cli.md` / `-r2.md`（通过）
  - `docs/reviews/design-review-F005-knowledge-authoring-cli.md`（通过，4 minor LLM-FIXABLE 内联收敛）

---

## 1. 概述

把 D005 设计拆成 6 个可独立 RED → GREEN → REFACTOR 的工程任务。任务间强弱依赖：

```
T1 (knowledge add + ID helper) ──┬─→ T2 (knowledge edit, 复用 T1 ID & content helpers)
                                  └─→ T3 (knowledge show + delete)
                                  └─→ T4 (experience add, 复用 T1 ID helper)
                                                          └─→ T5 (experience show + delete)
T1..T5 ─────────────────────────────────────────────────────→ T6 (docs + cross-cutting)
```

任务边界（与设计 §2.4 一致）：

- 仅修改 `src/garage_os/cli.py` + 文档 + `tests/test_cli.py` + `tests/test_documentation.py`
- 不修改 `KnowledgeStore` / `ExperienceIndex` / `KnowledgeEntry` / `ExperienceRecord` / 任何其他模块
- 不引入新 PyPI 依赖
- 不引入新源码模块文件

---

## 2. 里程碑

| 里程碑 | 目标 | 任务数 | 退出标准 |
|--------|------|--------|----------|
| **M1: Knowledge CRUD** | knowledge add / edit / show / delete 全部 happy path + edge cases | 3 (T1, T2, T3) | knowledge 4 个子命令的 unit tests 全绿；`KnowledgeStore` 公开 API 零修改 |
| **M2: Experience CRUD** | experience add / show / delete | 2 (T4, T5) | experience 3 个子命令的 unit tests 全绿；`ExperienceIndex` 公开 API 零修改 |
| **M3: 文档 + Cross-cutting** | 用户指南 / 双 README / FR-509 跨命令断言 / FR-510 help 自描述 / NFR-503 smoke / NFR-501 全 suite 回归 | 1 (T6) | `pytest tests/ -q` ≥ 414 + F005 新增；用户指南可 grep；help 输出含全部新子命令 |

---

## 3. 文件 / 工件影响图

### 3.1 修改的源码模块

| 文件 | 影响类型 | 任务 | 说明 |
|------|---------|------|------|
| `src/garage_os/cli.py` | 修改 | T1–T6 | 新增 7 个 handler 函数 + 7 个 sub-parser + 模块顶层 `*_FMT` 常量 + ID/content helpers |

### 3.2 修改的文档

| 文件 | 影响类型 | 任务 | 说明 |
|------|---------|------|------|
| `docs/guides/garage-os-user-guide.md` | 修改 | T6 | 新增 "Knowledge authoring (CLI)" 段，覆盖 7 个子命令最小示例 |
| `README.md` | 修改 | T6 | CLI 命令列表追加 7 个新子命令名 |
| `README.zh-CN.md` | 修改 | T6 | 同上中文版 |

### 3.3 新增 / 修改的测试

| 文件 | 影响类型 | 任务 | 说明 |
|------|---------|------|------|
| `tests/test_cli.py` | 修改 + 新增 | T1–T6 | 新增 ~30 条断言（按 D005 §13.2 用例编号）；不修改既有 414 个断言 |
| `tests/test_documentation.py` | 修改 + 新增 | T6 | 新增 7 条 grep 断言（每子命令字符串各 1 条） |

---

## 4. 需求与设计追溯

| 规格 / 设计锚点 | 覆盖任务 |
|----------------|----------|
| `FR-501` knowledge add + 设计 §3 / §9.2 / §10.1 | T1 |
| `FR-502` --content / --from-file 互斥 + 设计 §3 / §10.1 | T1 |
| `FR-503` knowledge edit selective overlay + 设计 §3 / §9.3 / §10.2 / §10.2.1 | T2 |
| `FR-504` knowledge show + 设计 §3 / §9.1 | T3 |
| `FR-505` knowledge delete + 设计 §3 / §9.1 | T3 |
| `FR-506` experience add + 设计 §3 / §9.4 | T4 |
| `FR-507a` experience show + 设计 §3 / §9.1 | T5 |
| `FR-507b` experience delete (含索引摘除) + 设计 §3 / §10.3 | T5 |
| `FR-508` ID 算法 + 设计 §3 / ADR-502 | T1 (主) + T4 (experience 分支) |
| `FR-509` source marker + 设计 §3 / ADR-503 | T1 (knowledge add) + T2 (knowledge edit) + T4 (experience add) + T6 (cross-cutting 断言) |
| `FR-510` CLI help 自描述 + 设计 §3 / §9 | T6 |
| `NFR-501` 零回归 | T6（`pytest tests/ -q` ≥ 414） + T1–T5（不修改既有测试） |
| `NFR-502` 零外部依赖 + 设计 §2.4 | T1–T6（每任务 PR 不新增 dependency） |
| `NFR-503` 写路径 < 1.0s | T6（smoke test） |
| `NFR-504` stdout 常量化 + 设计 §9.5 | T1–T5（每任务引入对应 FMT 常量）+ T6（grep 断言） |
| `NFR-505` 文档同步 | T6 |
| `CON-501` 顶级命令复用 + 设计 §3 / §9.1 | T1–T5（subparser 挂在 knowledge / experience 父下） |
| `CON-502` 不改 store/index API | T1–T5（每任务断言：被调 API 在已有公开方法名集合内） |
| `CON-503` 保持 v1.1 `version+=1` | T2（断言 edit 后 `version=N+1`） |
| `CON-504` source_artifact 取值不冲突 | T1 (cli:knowledge-add)、T2 (cli:knowledge-edit)、T4 (cli:experience-add)、T6（grep "cli:" 命名空间专属断言） |
| `CON-505` 不变形 markdown body | T1（断言写盘 body 与传入 content 字节级一致） |
| ADR-501 单文件风格 | T1–T6（不引入新 .py） |
| ADR-502 ID 时间戳秒精度 | T1 (knowledge)、T4 (experience) |
| ADR-503 `cli:` 前缀命名空间 | T1 / T2 / T4 |
| 设计 §10.2.1 edit 字段覆写表 | T2 |
| 设计 §13.2 用例 1–30 | T1–T6 全覆盖 |

---

## 5. 任务拆解

### T1. knowledge add + ID/content helpers + 来源标记

- **目标**: 在 `cli.py` 新增 `_knowledge_add(...)` handler、`_generate_entry_id(type, topic, content, now)` helper、`_resolve_content(content_arg, from_file_arg)` helper，以及 `KNOWLEDGE_ADDED_FMT` / `KNOWLEDGE_ALREADY_EXISTS_FMT` / `ERR_CONTENT_AND_FILE_MUTEX` / `ERR_ADD_REQUIRES_CONTENT` / `ERR_FILE_NOT_FOUND_FMT` / `ERR_NO_GARAGE` 常量。子命令 `garage knowledge add` 接入 sub-parser。
- **Acceptance**（对应设计 §13.2 用例 1, 2, 3, 4, 5, 6, 7, 8）:
  - `garage knowledge add --type decision --topic X --content Y` 在已 init 仓库内 → exit 0、stdout `KNOWLEDGE_ADDED_FMT.format(eid=...)`、磁盘 `.garage/knowledge/decisions/decision-<id>.md` 含 front matter `id/type/topic/date/tags/status="active"/version=1/source_artifact="cli:knowledge-add"`（FR-501、FR-509、CON-505）
  - `--tags a,b,c` → front matter `tags: ['a', 'b', 'c']`（FR-501）
  - `--from-file pattern.md` → entry.content == 文件 UTF-8 全文（FR-502 happy）
  - 同时传 `--content` + `--from-file` → exit 1 + stderr `ERR_CONTENT_AND_FILE_MUTEX`（FR-502 mutex）
  - 都不传 → exit 1 + stderr `ERR_ADD_REQUIRES_CONTENT`（FR-502 missing）
  - `--from-file 不存在路径` → exit 1 + stderr `ERR_FILE_NOT_FOUND_FMT.format(path=...)`（FR-502 not-found）
  - 未传 `--id` → ID 形如 `decision-<YYYYMMDD>-<6 hex chars>`，6 hex = `sha256(topic + "\n" + content + "\n" + iso8601_seconds).hexdigest()[:6]`（FR-508）
  - 同 topic + content + monkeypatch `datetime.now` 锁同一秒 → 第 2 次 add 退 1 + stderr `KNOWLEDGE_ALREADY_EXISTS_FMT`，磁盘第一条 entry 不被覆盖（FR-508 collision）
  - `--id custom-001` → 文件名 `decision-custom-001.md`，跳过 hash 路径（FR-508 explicit）
  - `--id custom-001` 已存在 → exit 1 + stderr `KNOWLEDGE_ALREADY_EXISTS_FMT`（FR-508 explicit collision）
  - 在无 `.garage/` 目录下调用 → exit 1 + stderr `ERR_NO_GARAGE`
- **TestDesignApproval**: 必须在写实现前先列出 RED 阶段所有测试用例（每个 acceptance 至少 1 个 test func），由 `tests/test_cli.py` 新增 `TestKnowledgeAdd` test class 承载。
- **Verify**:
  - `pytest tests/test_cli.py -k TestKnowledgeAdd -q` 全绿
  - `pytest tests/ -q` ≥ 414 + 新增（NFR-501）
- **依赖**: 无（最小起点）
- **Risk**: monkeypatch `datetime.now` 在 `cli.py` 内部需要清晰的注入点（建议 helper 接受 `now: datetime` 参数，handler 用 `now=datetime.now()` 默认），避免 patch `cli.datetime`
- **Files**: `src/garage_os/cli.py`、`tests/test_cli.py`

### T2. knowledge edit (selective overlay + version+=1 延伸)

- **目标**: 在 `cli.py` 新增 `_knowledge_edit(...)` handler 与 sub-parser；新增 `KNOWLEDGE_EDITED_FMT` / `KNOWLEDGE_NOT_FOUND_FMT` / `ERR_EDIT_REQUIRES_FIELD` 常量；按 D005 §10.2.1 字段表执行选择性覆写。
- **Acceptance**（对应设计 §13.2 用例 9, 10, 11, 12, 13, 14）:
  - `(decision, k1)` 存在 `version=1` `tags=[a]`，`garage knowledge edit --type decision --id k1 --tags a,b` → 磁盘 `version=2` `tags=['a','b']`、`topic` / `content` / `date` 保持不变（FR-503 selective + 设计 §10.2.1）
  - stdout `KNOWLEDGE_EDITED_FMT.format(eid='k1', version=2)`（FR-503 + NFR-504）
  - 仅传 `--type` + `--id` 不传任何可改字段 → exit 1 + stderr `ERR_EDIT_REQUIRES_FIELD`（FR-503 missing-field）
  - 同时传 `--content` + `--from-file` → exit 1 + stderr `ERR_CONTENT_AND_FILE_MUTEX`（FR-503 mutex，复用 T1 常量）
  - `(decision, missing)` 不存在 → exit 1 + stderr `KNOWLEDGE_NOT_FOUND_FMT`，磁盘无变化（FR-503 not-found）
  - 多次 edit 同一 entry → `version` 单调 +1（CON-503 / F004 v1.1 不变量延伸）
  - edit 后 entry `source_artifact == "cli:knowledge-edit"`（FR-509）
  - edit 不污染 publisher 路径写入的 entry：先用 `KnowledgeStore.store()` 直接写一条 `source_artifact="published_by:..."` 的 entry，然后 CLI edit 改 tag → `source_artifact` 被覆为 `"cli:knowledge-edit"`，而 `published_from_candidate` 等其他 publisher 元数据**保持不变**（FR-509 + 设计 §10.2.1 表）
- **TestDesignApproval**: 同 T1 模式，新增 `TestKnowledgeEdit` test class
- **Verify**:
  - `pytest tests/test_cli.py -k TestKnowledgeEdit -q` 全绿
  - `pytest tests/ -q` ≥ T1 baseline 不退绿
- **依赖**: T1（复用 `_resolve_content` helper、`ERR_CONTENT_AND_FILE_MUTEX`）
- **Risk**: KnowledgeEntry 字段较多，覆写逻辑要严格按 §10.2.1 表，否则容易污染 publisher 元数据
- **Files**: `src/garage_os/cli.py`、`tests/test_cli.py`

### T3. knowledge show + delete

- **目标**: 在 `cli.py` 新增 `_knowledge_show(...)` / `_knowledge_delete(...)` handler 与 sub-parsers；新增 `KNOWLEDGE_DELETED_FMT` 常量（`KNOWLEDGE_NOT_FOUND_FMT` 复用 T2 常量）。
- **Acceptance**（对应设计 §13.2 用例 15, 16, 17, 18）:
  - `(decision, k1)` 存在 `topic="X" version=2 tags=['a']`，`garage knowledge show --type decision --id k1` → exit 0、stdout 含 `topic: X`、`version: 2`、`tags: a, b`（人类可读）+ 空行后为 content body（FR-504）
  - `(decision, missing)` `show` → exit 1 + stderr `KNOWLEDGE_NOT_FOUND_FMT`（FR-504 not-found）
  - `(pattern, p1)` 存在，`delete` → 文件被移除、`KnowledgeStore.retrieve()` 返回 None、stdout `KNOWLEDGE_DELETED_FMT`、exit 0（FR-505）
  - `(pattern, missing)` `delete` → exit 1 + stderr `KNOWLEDGE_NOT_FOUND_FMT`，磁盘无副作用（FR-505 not-found）
  - `show` 输出含 derived 字段 `version` 与 `source_artifact`（设计 OD-504）
- **TestDesignApproval**: 新增 `TestKnowledgeShow` + `TestKnowledgeDelete` test classes
- **Verify**:
  - 子集测试全绿
  - `pytest tests/ -q` 不退绿
- **依赖**: T1（基本 CLI 框架、`ERR_NO_GARAGE` 常量）
- **Risk**: show 文案格式如何定（人类可读 vs JSON）。本 cycle 选人类可读（key: value 块），JSON 输出 deferred（OQ-505）
- **Files**: `src/garage_os/cli.py`、`tests/test_cli.py`

### T4. experience add (含 ID helper experience 分支)

- **目标**: 在 `cli.py` 新增 `experience` 父 subparser + `_experience_add(...)` handler + `_generate_experience_id(now)` helper；新增 `EXPERIENCE_ADDED_FMT` 常量；写入 `record.artifacts = ["cli:experience-add"]`。
- **Acceptance**（对应设计 §13.2 用例 19, 20）:
  - `garage experience add --task-type spike --skill ahe-design --skill ahe-tasks --domain platform --outcome success --duration 1800 --complexity medium --summary "..."` → exit 0、`.garage/experience/records/exp-<id>.json` 含 `task_type=spike`、`skill_ids=['ahe-design','ahe-tasks']`、`outcome="success"`、`duration_seconds=1800`、`complexity="medium"`、`lessons_learned=["..."]`、`artifacts=["cli:experience-add"]`、`problem_domain="spike"`（默认 = task_type）
  - 多个 `--tech` → `tech_stack` 含全部值
  - `--tags a,b,c` → `key_patterns=['a','b','c']`
  - `--id` 未传 → `exp-<YYYYMMDD>-<6 hex chars>`，hash 输入 = `task_type + "\n" + summary + "\n" + iso8601_seconds`
  - `--outcome` 不在 `{success, failure, partial}` → argparse exit 2（标准行为）
  - `--duration` 非整数 → argparse exit 2
  - 写盘 record 在 `ExperienceIndex` 中央索引内可被找到（间接验证 `ExperienceIndex.store()` 调用成功）
- **TestDesignApproval**: 新增 `TestExperienceAdd` test class
- **Verify**:
  - 子集全绿
  - `pytest tests/ -q` 不退绿
- **依赖**: T1（ID helper 命名约定 / `ERR_NO_GARAGE`）
- **Risk**: `ExperienceRecord` 字段较多，确保未传字段都用 dataclass 默认值（empty list / 空 string / None）
- **Files**: `src/garage_os/cli.py`、`tests/test_cli.py`

### T5. experience show + delete (含中央索引摘除断言)

- **目标**: 在 `cli.py` 新增 `_experience_show(...)` / `_experience_delete(...)` handler 与 sub-parsers；新增 `EXPERIENCE_DELETED_FMT` / `EXPERIENCE_NOT_FOUND_FMT` 常量。
- **Acceptance**（对应设计 §13.2 用例 21, 22, 23, 24）:
  - `exp-1.json` 存在，`garage experience show --id exp-1` → exit 0、stdout 是合法 JSON（`json.loads` 不抛错）且 keys 含 `record_id`、`task_type`、`outcome`（FR-507a）
  - `exp-missing` `show` → exit 1 + stderr `EXPERIENCE_NOT_FOUND_FMT`（FR-507a not-found）
  - `exp-1.json` 存在 + `.garage/knowledge/.metadata/index.json` 含 `exp-1` 引用，`delete` → 文件被删 + 索引中**不再含** `exp-1` key、stdout `EXPERIENCE_DELETED_FMT`、exit 0（FR-507b 关键断言）
  - `exp-missing` `delete` → exit 1 + stderr `EXPERIENCE_NOT_FOUND_FMT`，磁盘 / 索引无副作用（FR-507b not-found）
  - delete → show 紧跟 → exit 1（CRUD 闭环对称性）
- **TestDesignApproval**: 新增 `TestExperienceShow` + `TestExperienceDelete` test classes
- **Verify**:
  - 子集全绿
  - `pytest tests/ -q` 不退绿
- **依赖**: T4（先有 add 才能测 show / delete）
- **Risk**: 中央索引路径 `.garage/knowledge/.metadata/index.json` 是 ExperienceIndex 内部约定；测试断言要去读这个路径，而非依赖 ExperienceIndex 私有字段
- **Files**: `src/garage_os/cli.py`、`tests/test_cli.py`

### T6. 文档同步 + cross-cutting 断言 + smoke test + 全 suite 回归

- **目标**:
  1. `docs/guides/garage-os-user-guide.md` 新增 "Knowledge authoring (CLI)" 段，覆盖 7 个子命令的最小可执行示例（含 add / edit / show / delete + experience 3 个）
  2. `README.md` / `README.zh-CN.md` 在 CLI 命令列表追加 7 个新子命令名（不要求详细示例）
  3. `tests/test_documentation.py` 新增 grep 断言：用户指南或 README 中能找到 `garage knowledge add`、`garage knowledge edit`、`garage knowledge show`、`garage knowledge delete`、`garage experience add`、`garage experience show`、`garage experience delete` 共 7 个字符串
  4. `tests/test_cli.py` 新增跨命令断言：
     - `garage knowledge --help` stdout 含 `add` / `edit` / `show` / `delete` / `search` / `list`（FR-510 用例 25）
     - `garage experience --help` stdout 含 `add` / `show` / `delete`（FR-510 用例 26）
     - `garage knowledge add --help` stdout 含 `--type` / `--topic` / `--tags` / `--content` / `--from-file` / `--id`（FR-510 用例 27）
     - CRUD 闭环测试：add → show → edit → show → delete → show 全链路 6 步 exit code 符合预期（设计 §13.2 用例 30；§2.2 SC-2）
     - smoke test：`time.monotonic()` 包一次 `add` 调用断言 < 1.0s（NFR-503，设计 §13.2 用例 29）
     - source-marker 跨命令断言：CLI add 写入的 `source_artifact` 命名空间以 `"cli:"` 开头；publisher 路径写入的不以 `"cli:"` 开头（FR-509 + ADR-503，设计 §13.2 用例 8 + 14 + 20 的整合）
  5. 运行 `pytest tests/ -q` 验证 ≥ 414 + F005 新增数（NFR-501）
- **Acceptance**:
  - `tests/test_documentation.py` 全绿（含 7 条新增 grep）
  - `tests/test_cli.py` 全绿（含 cross-cutting 断言）
  - `pytest tests/ -q` 全绿，passed 数 = 414 + F005 总新增数（无任何 fail / error）
  - `pyproject.toml` `git diff main..` 无 dependency 行变化（NFR-502）
  - 用户指南中能 grep 到 7 个子命令字符串
- **TestDesignApproval**: 文档断言列表 + cross-cutting 断言列表先列在测试文件 docstring 中
- **Verify**:
  - `pytest tests/ -q` final
  - `git diff main -- pyproject.toml` 输出空
  - `grep "garage knowledge add" docs/guides/garage-os-user-guide.md` 命中
- **依赖**: T1–T5（需要全部子命令 handler 已就位）
- **Risk**: 文档 grep 断言要避免与已存在 README 内容冲突；CRUD 闭环测试要在同一个 `tmp_path` fixture 内顺序执行
- **Files**: `docs/guides/garage-os-user-guide.md`、`README.md`、`README.zh-CN.md`、`tests/test_documentation.py`、`tests/test_cli.py`

---

## 6. Task Queue Projection 与 Active Task Selection

### 6.1 Queue Projection（每任务完成后的下游候选）

| 当前完成任务 | next-ready 候选集 | hard blockers |
|------------|-----------------|--------------|
| (未开始) | T1 | 无 |
| T1 完成 | T2, T3, T4 | 无 |
| T1 + T2 完成 | T3, T4 | 无 |
| T1 + T3 完成 | T2, T4 | 无 |
| T1 + T4 完成 | T2, T3, T5 | 无 |
| T1 + T2 + T3 + T4 + T5 完成 | T6 | 无 |
| T1–T6 完成 | (none, → `hf-test-review`) | 无 |

### 6.2 Active Task Selection Priority（router 重选规则）

当多个任务进入 next-ready 集合时，按以下优先级选唯一 Current Active Task：

1. **风险驱动**：优先 Risk 字段非空的任务（先解决高不确定性）
2. **依赖广度**：被更多下游任务依赖的优先（T1 > T2 / T3 / T4 > T5 / T6）
3. **体量平衡**：同优先级时选体量较大的（避免最后留下大任务）
4. **顺序兜底**：以上仍并列时按 T 编号小者优先

按本规则，建议线性序列：**T1 → T2 → T3 → T4 → T5 → T6**。
（T2 优先于 T3 / T4 是因为 T2 触及 v1.1 不变量延伸，风险层级更高；T3 / T4 / T5 互不依赖可并行，但 solo 模式下按编号顺序更稳。）

### 6.3 实现顺序与依赖图

```
T1 (~day 1-equivalent unit, 最大体量)
 ├─→ T2 (复用 helper)
 ├─→ T3 (轻)
 └─→ T4 (复用 ID helper 命名约定)
       └─→ T5 (复用 add 写盘做断言)

T6 (last, 全 suite 回归门 + 文档)
```

每任务作为独立 commit。建议 commit message 模板：`feat(F005-T<N>): <summary>` for green commits，`test(F005-T<N>): <summary>` for RED-only commits（如果按严格 TDD）。

---

## 7. 任务计划评审前自检

- [x] 每任务独立可验证（INVEST Independent + Testable）
- [x] 任务粒度均匀（T1 / T4 略大，T3 / T5 较小，整体在 1-2 commit 内可消化）
- [x] 强弱依赖标注清楚（T2/T3 → T1，T5 → T4，T6 → T1-T5）
- [x] 每任务覆盖至少 1 个 FR / NFR / CON / 设计章节
- [x] 设计 §13.2 用例 1-30 全覆盖
- [x] 不引入未在设计范围内的工件 / 模块 / 依赖
- [x] 退出标准可机器判定（pytest 退出码 + grep）
- [x] 风险点显式标注（monkeypatch 注入点 / publisher 元数据保护 / 中央索引路径）
- [x] task plan 文档已落盘到约定路径

下一步：派发 `hf-tasks-review` reviewer subagent。

---

## 8. 开放问题

| 编号 | 问题 | 阻塞 / 非阻塞 | 当前判断 |
|------|------|-------------|---------|
| OT-501 | T1 是否要在同一任务内覆盖 ID generator 的 SHA-256 算法 unit test（独立于 add handler）？ | 非阻塞 | 是。`_generate_entry_id(...)` 作为 helper 应有独立 test，避免只能通过 add 路径间接覆盖。 |
| OT-502 | T6 CRUD 闭环测试 fixture 是否要 monkeypatch `datetime.now`？ | 非阻塞 | 否。CRUD 闭环用真实时间即可（每步耗时远 < 1 秒，但 add 与 edit 分别在不同秒，不会撞 ID 碰撞分支）。如果 CI 跑得太快导致同秒，再加 patch。 |
| OT-503 | 是否要为 `knowledge edit` 加 dry-run 模式？ | 非阻塞 | 否。本 cycle 严格遵守 spec § 4.2 不包含项；若用户期望，由后续 increment 立项。 |
