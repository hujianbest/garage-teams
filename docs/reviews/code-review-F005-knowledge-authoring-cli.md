# Code Review — F005 Garage Knowledge Authoring CLI

- 评审 skill: `hf-code-review`
- Profile: `standard`，Execution Mode: `auto`
- 评审日期: 2026-04-19
- 评审对象（实现）:
  - `src/garage_os/cli.py`
    - 行 26–58：F005 模块顶层 `KNOWLEDGE_*_FMT` / `EXPERIENCE_*_FMT` / `ERR_*` 常量与 `CLI_SOURCE_*`（NFR-504 / ADR-503）
    - 行 617–625：`_now_default()`（FR-508 / 设计 §T1 Risk 注入点）
    - 行 628–699：helper —`_parse_tags` / `_resolve_content` / `_generate_entry_id` / `_generate_experience_id` / `_require_garage`
    - 行 702–962：handler — `_knowledge_add` / `_knowledge_edit` / `_knowledge_show` / `_knowledge_delete` / `_experience_add` / `_experience_show` / `_experience_delete`
    - 行 1024–1185：`build_parser()` 内 `knowledge add/edit/show/delete` 与 `experience add/show/delete` 子树
    - 行 1252–1325：`main()` 内 `knowledge` / `experience` 命令分发
  - 文档同步：`docs/guides/garage-os-user-guide.md` §"Knowledge authoring (CLI)"、`README.md`/`README.zh-CN.md` 命令清单
- 关联工件:
  - 规格 `docs/features/F005-garage-knowledge-authoring-cli.md`
  - 设计 `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md`
  - 任务 `docs/tasks/2026-04-19-garage-knowledge-authoring-cli-tasks.md`
  - 测试评审 `docs/reviews/test-review-F005-knowledge-authoring-cli.md`（通过）
- 当次会话证据:
  - `python3 -m pytest tests/ -q` ⇒ `451 passed in 25.48s`（414 基线 + F005 新增 37）
  - `git diff main..HEAD -- pyproject.toml` ⇒ 无差（NFR-502）

---

## 结论

**通过**

实现把 F005 全部新增量限制在 `cli.py` 一个文件内（ADR-501 落地），handler 与 helper 边界清晰，
ID 算法、source_artifact 覆写、`update()` 复用、退出码契约全部对齐设计 §10.2.1 与 ADR-501/502/503；
6 维度评分均 ≥ 7/10，无 critical / important 级别问题。Findings 全部为 minor / LLM-FIXABLE，
不阻塞 traceability review，建议在后续接力或 increment 中收敛。

---

## 多维评分

| 维度 | 分数 | 评价 |
|------|------|------|
| `CR1` 正确性 | 9/10 | FR-501/502/503/504/505/506/507a/507b/508/509/510 全部由 handler 实现并对应 451 个 pytest 全绿；`_knowledge_edit` 选择性覆写仅在 args 显式给出时改字段、`entry.date` / publisher 元数据 (`published_from_candidate` 等) 全部留旧；`_knowledge_add` / `_experience_add` 在写盘前用 `retrieve()` 显式做碰撞探测后才落盘，避免静默覆盖。FR-508 时间盐 SHA-256 截 6 hex 与设计 ADR-502 完全一致。 |
| `CR2` 设计一致性 | 8/10 | 与设计 §3 / §10.2.1 / §9 字段表完全对齐；唯一非阻塞偏离：`_experience_show` 直接 `read_text + json.loads`（cli.py:941）而设计 §3 traceability 写的是 "调 ExperienceIndex.retrieve()"。这一偏离实际更"忠于磁盘原文"（`retrieve` 会过 `_dict_to_record`，pretty-print 会损失非 dataclass 字段），但与设计文字不严格一致，应在 design 备注或代码注释中说明。 |
| `CR3` 状态 / 错误 / 安全 | 9/10 | 错误处理完备：所有缺 `.garage/` / 缺字段 / 文件不存在 / mutex / not-found / collision 均退 1 + stderr，无静默失败。`KnowledgeStore.update()` 依赖 in-place `version+=1`，handler 在调用后读 `entry.version` 写 stdout（cli.py:806–807），与 F004 v1.1 不变量（CON-503）严密对接。`_resolve_content` 通过 `is_file()` 检查再读，TOCTOU 在 CLI 单用户语境可接受。无权限绕过、无明文凭证、无未捕获 cascade exception。 |
| `CR4` 可读性与可维护性 | 8/10 | 命名一致（`_knowledge_*` / `_experience_*` handler、`_generate_*_id` helper）；docstring 充分（每个 handler 标注对应 FR / CON / ADR）；常量与 helper 自顶向下排列；无魔法数字（"6" hex 在 `_generate_*_id` 内有明确注释指向 FR-508/ADR-502）。轻微减分：`_experience_add` 的 collision 分支复用 `KNOWLEDGE_ALREADY_EXISTS_FMT`（cli.py:901）让 stderr 文案出现"Entry with id"指代 experience record，命名空间与读者预期不匹配；`_experience_show` 的 OSError / JSONDecodeError fallback 仍用 inline f-string（cli.py:943），偏离 NFR-504 模块常量原则的精神。 |
| `CR5` 范围守卫 | 10/10 | 未引入任何超规格能力：无交互式 wizard、无 LLM 自动分类、无 `experience edit`、未改 `KnowledgeStore` / `ExperienceIndex` / `KnowledgeEntry` / `ExperienceRecord` 任何已有 schema 或方法签名（CON-501–505 全部对齐）；`pyproject.toml` 在 main..HEAD 无 diff（NFR-502 机器证据）。`build_parser()` 的子命令集合限定为 add/edit/show/delete + experience add/show/delete，与设计 §9.1 子命令树严格一致。 |
| `CR6` 下游追溯就绪度 | 9/10 | 实现交接块完整：handler 函数与 sub-parser 一一对应、命令分发可冷读，docstring 即追溯锚；测试评审已建立 30 个用例 ↔ 测试函数交叉表，traceability review 可直接对照 §10.2.1 字段表 ↔ `_knowledge_edit` 行 794–805。`source_artifact` / `artifacts[0]` 的 `cli:` 命名空间在常量、handler、user guide 三处都出现，证据闭环。 |

任一关键维度 ≥ 7，全部 ≥ 6 → 准予通过。

---

## 发现项

### Minor / LLM-FIXABLE（非阻塞，建议下次接力或 increment 收敛）

- **[minor][LLM-FIXABLE][CR4] `_experience_add` collision 分支复用 `KNOWLEDGE_ALREADY_EXISTS_FMT`**
  - 位置：`src/garage_os/cli.py:900-902`
  - 现象：experience add 与 knowledge add 共用同一个 `KNOWLEDGE_ALREADY_EXISTS_FMT`（虽然 `.format(eid=rid)` 仍可读，但读者会期望 `EXPERIENCE_ALREADY_EXISTS_FMT` 与 `EXPERIENCE_ADDED_FMT` / `EXPERIENCE_DELETED_FMT` / `EXPERIENCE_NOT_FOUND_FMT` 一致命名）。
  - 影响：用户 / Agent grep 时需要知道这个 cross-domain 复用约定；NFR-504 的"语义化"目标稍打折。
  - 建议：新增 `EXPERIENCE_ALREADY_EXISTS_FMT = "Experience record '{rid}' already exists; pass --id to override or change inputs"`，handler 改用之；或在 `KNOWLEDGE_ALREADY_EXISTS_FMT` 上方注释明示"experience 路径复用此常量是有意的"，并补一条对称测试。

- **[minor][LLM-FIXABLE][CR2] `_experience_show` 直接读取 JSON 文件，未走 `ExperienceIndex.retrieve()`**
  - 位置：`src/garage_os/cli.py:935-945`
  - 现象：handler 调 `record_path.read_text() + json.loads()` pretty-print；设计 §3 traceability 表与 §10.3 调用栈写的是 "调 `ExperienceIndex.retrieve()`"。
  - 实际权衡：直接读盘 → pretty-print 可保留 JSON 文件中所有非 dataclass 字段；走 `retrieve()` → 经 `_dict_to_record` / `_record_to_dict` 双向映射可能丢失 extras。当前实现"忠于磁盘"是合理选择。
  - 建议二选一：(a) 在代码加 1 行注释 "intentionally bypasses retrieve() to preserve on-disk JSON shape"；或 (b) 改为 `ExperienceIndex.retrieve()` + 用 `_record_to_dict` 重新序列化。任选其一即可消除"实现-设计文字不一致"的视觉冲击。

- **[minor][LLM-FIXABLE][CR4][NFR-504] `_experience_show` 异常分支用 inline f-string**
  - 位置：`src/garage_os/cli.py:943`
  - 现象：`print(f"Failed to read experience record '{rid}': {exc}", file=sys.stderr)` 是该文件中唯一一处面向用户的 inline f-string failure 文案，偏离了 NFR-504 "模块常量化"精神。
  - 影响：极少触发（仅当磁盘 JSON 损坏或权限错误），但破坏了"所有 success/failure 文案均可 grep 自常量"的一致性约定。
  - 建议：提取 `ERR_EXPERIENCE_READ_FMT = "Failed to read experience record '{rid}': {exc}"` 到模块顶层。

- **[minor][LLM-FIXABLE][CR4] 旧 `_knowledge_search` / `_knowledge_list` 的 no-garage 行为与 F005 handler 不一致**
  - 位置：`src/garage_os/cli.py:382-385, 416-419`（pre-existing F002/F003）
  - 现象：旧 handler 在缺 `.garage/` 时 `print` 到 stdout 并 `return None`（main 视为 exit 0）；F005 新增的 `_knowledge_add` 等返回 1 + stderr `ERR_NO_GARAGE`。
  - 这是 pre-existing 行为差异（不是 F005 引入的），按 baseline 不应阻塞；但 ASM-501 的失效契约 ("退 1 + stderr") 已在 F005 handler 收敛，旧子命令仍走老路径，下次维护可顺手统一。

- **[minor][LLM-FIXABLE][CR4] `_resolve_content` 三态返回值 ((content, err) ∈ {explicit value, None+None signal-leave-unchanged, None+err})文档可强化**
  - 位置：`src/garage_os/cli.py:635-658`
  - 现象：`require_one=False` 路径返回 `(None, None)` 用于 "edit 时调用方未传 content 字段，保持原值不变"，这一约定靠 `_knowledge_edit` 的 `if content is not None`（cli.py:798）解读。docstring 仅说 "if error is non-None the caller must print"，未显式提示 `(None, None)` 的"无操作"语义。
  - 建议：在 docstring 加一句 "if both args are None and require_one is False, returns (None, None) meaning 'leave content unchanged'"，避免未来读者误以为是 silent failure。

### 没有发现 critical / important 级别问题

---

## 代码风险与薄弱项

- **`_knowledge_edit` 依赖 `KnowledgeStore.update()` 的 in-place `version+=1` 副作用**（cli.py:806–807）。设计 §10.2 已显式承认 update() 签名 mutates；这是 v1.1 既有契约，但 future code-review 时如果有人把 `update()` 改成纯函数，本 handler 的 stdout 中 `version` 会落后 1。已被 `tests/test_cli.py` 中的 `test_edit_overlays_only_specified_fields_and_bumps_version` / `test_edit_monotonic_version` 双重接住，不阻塞。
- **`_experience_add` `now` 仅在生成 ID 与 `created_at`/`updated_at` 复用**（cli.py:894, 920–921），与 `KnowledgeStore.store()` 路径无关。如果未来在 `_experience_add` 路径 monkeypatch `_now_default` 锁秒，需要确认 `ExperienceIndex.store()` 内部不会再次写入 `updated_at = datetime.now()` 覆盖（当前 `store()` 不会，只有 `update()` 会）。已隐含在测试中绿。
- **`_experience_show` 直接绕过 `ExperienceIndex` 抽象**（cli.py:935-945，见 finding #2），未来若 `ExperienceIndex` 引入 schema migration 或字段裁剪，CLI show 输出会与 `experience search/list` 不同步。
- **碰撞分支与 happy 分支的字符串复用**：knowledge 与 experience 都用 "{eid|rid} already exists" 文案，但 experience 复用 `KNOWLEDGE_ALREADY_EXISTS_FMT`，与 grep "experience" 的过滤器分裂（finding #1）。

---

## 范围守卫与 Anti-Pattern 检查

| ID | Anti-Pattern | 状态 |
|----|--------------|------|
| `CA1` silent failure | 未触发：每条 1 路径都打 stderr + 退 1 |
| `CA2` magic numbers | 未触发：6 hex 长度有 FR-508/ADR-502 注释；NFR-503 1.0s 阈值在测试侧而非 handler |
| `CA3` undocumented behavior | 未触发：所有子命令在 spec/design/tasks 三层都列入；user guide 同步 |
| `CA4` design boundary leak | 未触发：handler 仅做 (1) 解析校验 (2) 委托 store/index (3) 输出，无业务逻辑沉积 |
| `CA5` dead code | 未触发：所有新增 handler / helper 在 `main()` dispatch 中均有调用；测试覆盖 451/451 |

---

## 设计与约束覆盖核对

| 锚点 | 覆盖状态 |
|------|---------|
| FR-501 knowledge add | ✅ `_knowledge_add` cli.py:702–749 |
| FR-502 mutex / from-file / not-found | ✅ `_resolve_content` cli.py:635–658 + `ERR_*` 常量 |
| FR-503 selective overlay | ✅ `_knowledge_edit` cli.py:752–808；§10.2.1 字段表逐项命中 |
| FR-504 show pretty-print | ✅ `_knowledge_show` cli.py:811–846 含 derived `version` / `source_artifact` |
| FR-505 delete | ✅ `_knowledge_delete` cli.py:849–869 |
| FR-506 experience add | ✅ `_experience_add` cli.py:872–925 |
| FR-507a experience show | ⚠ 行为对齐但绕开 `ExperienceIndex.retrieve()`（finding #2） |
| FR-507b experience delete | ✅ `_experience_delete` cli.py:949–962 调 `ExperienceIndex.delete()`，索引级联清理由 store 承担 |
| FR-508 ID algorithm + collision | ✅ `_generate_entry_id` / `_generate_experience_id` + retrieve()-based collision check |
| FR-509 source markers | ✅ `CLI_SOURCE_*` + `_knowledge_add`/`_knowledge_edit`/`_experience_add` 显式赋值；edit 强制覆写 source_artifact 而保留 `published_from_candidate` 等元数据 |
| FR-510 help discoverable | ✅ `build_parser()` 每个 sub-parser 提供 `help` + 完整 `add_argument(help=...)` |
| NFR-501 zero regression | ✅ 451 passed 全绿；既有 414 测试零修改 |
| NFR-502 zero new dep | ✅ `git diff main..HEAD -- pyproject.toml` 空；`cli.py` import 闭包仅 stdlib + `garage_os.*` |
| NFR-503 < 1.0s | ✅ 由 `tests/test_cli.py::test_add_smoke_under_one_second` 保护（test review 已核） |
| NFR-504 stdout 常量 | 主体满足；`_experience_show` 异常分支与 `_experience_add` collision 分支有 minor 偏离（finding #1, #3） |
| NFR-505 doc sync | ✅ user guide §"Knowledge authoring (CLI)" + 双 README CLI 命令表均含 7 个新命令 |
| CON-501 顶级命令复用 | ✅ `experience` / `knowledge` 仅作为 garage 的二级 subparser；与 design §3 / §9.1 一致 |
| CON-502 不改 store/index API | ✅ 仅调 `store/update/retrieve/delete`，方法签名零修改 |
| CON-503 v1.1 `version+=1` | ✅ 走 `update()`；`test_edit_monotonic_version` 锚点 |
| CON-504 source_artifact 不冲突 | ✅ `cli:knowledge-add|edit` / `cli:experience-add` 命名空间与 publisher 路径分离 |
| CON-505 不变形 markdown body | ✅ `entry.content = content` 直传 |
| ADR-501 单文件 | ✅ 全部新增量在 `cli.py`（行数从 ~728 → 1349，符合 ADR-501 阈值） |
| ADR-502 ID 时间盐秒精度 | ✅ `now.replace(microsecond=0).isoformat()` 入 hash |
| ADR-503 `cli:` 前缀 | ✅ 三个 `CLI_SOURCE_*` 常量集中在模块顶部 |
| 设计 §10.2.1 字段覆写表 | ✅ `_knowledge_edit` 行 794–805 与表格逐项一致 |

---

## Precheck 状态

- 实现交接块：稳定，可定位到 `cli.py` 7 个 handler + helper 块 + build_parser/main 改动
- route/stage/profile：standard / auto，与上游 evidence 一致
- test review verdict：通过（含 5 minor LLM-FIXABLE 已记录）
- 上游证据：spec / design / tasks / test review 全部 approved
- 准予正式 review

---

## 下一步

`hf-traceability-review`

代码质量足以支持下游追溯评审。Findings 全部为 minor LLM-FIXABLE，可在后续 increment 或维护周期一并收敛，不阻塞工作流推进。

---

## 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-traceability-review",
  "record_path": "docs/reviews/code-review-F005-knowledge-authoring-cli.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][CR4] _experience_add 复用 KNOWLEDGE_ALREADY_EXISTS_FMT 输出 collision，建议加 EXPERIENCE_ALREADY_EXISTS_FMT 或显式注释复用约定",
    "[minor][LLM-FIXABLE][CR2] _experience_show 直接读 JSON 文件而设计 §3 traceability 写的是调 ExperienceIndex.retrieve()，建议加注释说明或改回 retrieve()",
    "[minor][LLM-FIXABLE][CR4][NFR-504] _experience_show 异常分支使用 inline f-string，偏离 NFR-504 常量化精神，建议提取 ERR_EXPERIENCE_READ_FMT",
    "[minor][LLM-FIXABLE][CR4] _resolve_content (None,None) 三态返回的 'leave-unchanged' 语义在 docstring 中未显式说明",
    "[minor][LLM-FIXABLE][CR4] 旧 _knowledge_search/_knowledge_list 的 no-garage 行为退出码与 F005 handler 不一致（pre-existing，不阻塞）"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR4",
      "summary": "_experience_add collision 分支复用 KNOWLEDGE_ALREADY_EXISTS_FMT (cli.py:900-902)，与 EXPERIENCE_* 常量命名空间不对称"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR2",
      "summary": "_experience_show 绕过 ExperienceIndex.retrieve() 直接读 JSON (cli.py:935-945)，与设计 §3 traceability 文字不严格一致；当前实现更忠于磁盘原文，建议加注释或回归 retrieve()"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR4",
      "summary": "_experience_show OSError/JSONDecodeError 分支使用 inline f-string (cli.py:943)，偏离 NFR-504 模块常量化原则"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR4",
      "summary": "_resolve_content (None, None) 三态返回的 'leave-unchanged' 语义在 docstring 未显式说明 (cli.py:635-658)"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "CR4",
      "summary": "pre-existing 旧 _knowledge_search/_knowledge_list 的 no-garage 行为返回 None+stdout，与 F005 handler 退 1+stderr 不一致；不是 F005 引入，不阻塞"
    }
  ]
}
```
