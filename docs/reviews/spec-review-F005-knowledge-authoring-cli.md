# Spec Review — F005 Garage Knowledge Authoring CLI

- 评审范围: `docs/features/F005-garage-knowledge-authoring-cli.md`（草稿，338 行）
- Review skill: `hf-spec-review`
- 评审者: cursor cloud agent (auto mode, reviewer subagent，由 `hf-specify` 父会话派发)
- 日期: 2026-04-19
- Workflow Profile / Mode / Isolation: `standard` / `auto` / `in-place`
- Branch: `cursor/f005-knowledge-add-cli-177b`
- 上游证据基线:
  - `task-progress.md`（Stage = `hf-specify`，Pending = `hf-spec-review`，profile=`standard`，mode=`auto`，无冲突）
  - `RELEASE_NOTES.md` F003/F004 章（cycle precedent，v1.1 `version+=1` 不变量、stable stdout marker 模式）
  - `AGENTS.md` AHE 文档约定（`docs/features/Fxxx` 即 spec）
  - `docs/soul/{manifesto,growth-strategy}.md`（Stage 2 → Stage 3 触发条件 = "知识库条目 >100"）
  - `src/garage_os/cli.py`（已实现 init / status / run / knowledge {search,list} / memory review，FR-501~FR-510 都属于增量挂载，无回归冲突）
  - `src/garage_os/knowledge/knowledge_store.py`（store/update/retrieve/delete/search/list_entries 全部存在；`update()` 第 193-204 行执行 `entry.version += 1` 后调 `store()`，v1.1 不变量在源码可读出）
  - `src/garage_os/knowledge/experience_index.py`（`store / retrieve / search / update / delete / list_records / _update_index / _remove_from_index` 全部存在；`INDEX_PATH = "knowledge/.metadata/index.json"`）
  - `src/garage_os/types/__init__.py`（`KnowledgeEntry` 含 `id/type/topic/date/tags/content/status/version/related_decisions/related_tasks/source_session/source_artifact/source_evidence_anchor/confirmation_ref/published_from_candidate/front_matter`；`ExperienceRecord` 含 `record_id/task_type/skill_ids/tech_stack/domain/problem_domain/outcome/duration_seconds/complexity/session_id/artifacts/key_patterns/lessons_learned/...`）

## 1. Precheck

| 检查项 | 结果 |
|--------|------|
| 存在稳定可定位 spec draft | ✓ `docs/features/F005-...md` 草稿完整、338 行、章节齐备 |
| route / stage / profile 已明确 | ✓ Stage=`hf-specify`，Pending=`hf-spec-review`，profile=`standard`，mode=`auto`，无冲突 |
| 上游证据一致 | ✓ F003/F004 均在 `### 已知限制 / 后续工作` 中未与本 cycle 范围冲突；F004 v1.1 `version+=1` 不变量已在 `KnowledgeStore.update()` 落地 |
| 结构契约 | ✓ AGENTS.md 显式声明 `docs/features/` 即 spec 路径，F005 沿用 F003/F004 同款骨架；不机械套 `docs/specs/` 默认模板 |

Precheck 通过，进入正式 rubric。

## 2. 结构契约确认

F005 沿用 F003/F004 已实战验证的章节骨架：背景 → 目标与成功标准（含非目标）→ 用户角色与场景 → 当前轮范围（含/不含）→ 范围外 → FR → NFR → 外部接口与依赖 → 约束 → 假设 → 开放问题 → 术语。FR/NFR/CON/ASM 全部带 `优先级 / 来源 / 需求陈述 / 验收标准`，与 F003/F004 contract 字段一致，可被 `hf-design` 直接读为稳定输入。`standard` profile 不要求独立 ADR 或 discovery 文档；本 cycle 是 F002/F003/F004 的清晰扩展，正确未引入额外重型工件。

## 3. 正式 rubric 审查

### 3.1 Group Q: Quality Attributes

| ID | 检查 | 结论 | 证据 / 备注 |
|----|------|------|------------|
| Q1 Correct | 核心需求可回指来源 | ✓ | 每条 FR/NFR/CON/ASM 都有 `来源` 字段，分别锚定 § 1 摩擦 / § 3.2 场景 / § 2.2 SC / `design-principles.md` 原则 / F004 § 11.5 模式 |
| Q2 Unambiguous | 模糊词已量化 | ✓ | NFR-503 给出 `< 1.0s` 写路径耗时上限；FR-508 给出精确的 `sha256(...).hexdigest()[:6]` 形式；NFR-501 给出 `≥ 414 passed` 的零回归阈值 |
| Q3 Complete | 关键输入/输出/错误/边界 | ✓ | FR-501~507 每条均给出 happy + 失败 + 边界（`--content` 与 `--from-file` 互斥、缺二者、不存在文件、id 冲突、entry 不存在、未传可改字段） |
| Q4 Consistent | 需求间无冲突 | **⚠ 一处直接矛盾** | **FR-501 验收第 4 条**（行 159）写 "6-hex 来自 `sha256(topic + content)[:6]`，保证可复算"；**FR-508 需求陈述**（行 230）写 "6 hex 来自 `sha256((topic + "\n" + content + "\n" + iso8601 second-precision now)...).hexdigest()[:6]`"。两条对同一字段算法定义不同（前者无时间戳、后者含秒级时间戳），且 FR-501 的"保证可复算"在含时间戳的方案下并不成立（同一 topic+content 在不同秒会得到不同 ID，正是 FR-508 验收第 1 条所要求的）。详见 § 4 finding #1 |
| Q5 Ranked | 每条核心需求有优先级 | ✓ | FR-501/502/503/505/508/509 = Must；FR-504/506/507/510 = Should；NFR-501/502/504 = Must；NFR-503/505 = Should，分级明确 |
| Q6 Verifiable | 通过/不通过判断 | ✓ | 全部 FR/NFR 给出 Given/When/Then 验收或 grep/pytest 命令级断言 |
| Q7 Modifiable | 无散落重复 | ⚠ minor | ID 生成规则同时出现在 § 4.1 表格、FR-501 验收 #4、FR-508 三处；表面是不同切面（包含表 / add 验收 / 专用 FR），但 FR-501 第 4 条与 FR-508 不一致（见 Q4），属"散落且互相矛盾"。修 Q4 即可顺手收敛 Q7 |
| Q8 Traceable | 关键需求有 ID + Source | ✓ | FR-501~510 / NFR-501~505 / CON-501~505 / ASM-501~504，全部带 ID 与 来源 |

### 3.2 Group A: Anti-Patterns

| ID | 检查 | 结论 | 备注 |
|----|------|------|------|
| A1 模糊词 | ✓ | 主题行"让 Stage 2 飞轮能从终端起转"、§ 2.2 "人机两友"略口号化，但紧跟可量化条件（命令样例、退出码、stdout 文案、front matter 字段集合） |
| A2 复合需求 | ⚠ 1 处可优化 | FR-507 把 `experience show` 与 `experience delete` 打包成 1 条 FR；主题统一为"最小 CRUD 闭环"，4 条验收独立可判，但严格按 GS2 CRUD-packing 信号可拆为 FR-507a / FR-507b。**不阻塞**，仅 traceability 粒度优化建议 |
| A3 设计泄漏 | ⚠ 边界 2 处 | (1) FR-508 在 spec 层把哈希算法精确写到 `sha256(...).hexdigest()[:6]` 与字符串拼接顺序——**判定**：因为 ID 形态决定可冷读契约（git diff、`source_artifact` grep 都依赖此格式），可保留 1 个权威定义在 FR-508，但 § 4.1 表格 / FR-501 验收 #4 应只引用 FR-508 不重写算法。 (2) NFR-502 验收 `grep -r "import " src/garage_os/cli.py` 引用具体实现文件路径——属偏向实现的检查方式，可改为"`pyproject.toml` diff 不新增 third-party 依赖" + "CLI 模块导入面 grep 由 design 阶段约束"。Severity = minor，LLM-FIXABLE |
| A4 无主体的被动表达 | ✓ | 全部 FR 主语清晰（用户 / CLI / 系统 / Agent 调用方） |
| A5 占位/TBD | ✓ | 无 `TBD` / `待确认` / `后续补充` 残留 |
| A6 缺少负路径 | ✓ | FR-501（id 已存在）/ FR-502（互斥、缺二者、文件不存在）/ FR-503（entry 不存在、未传可改字段）/ FR-504/505（不存在）/ FR-506（argparse 退 2）/ FR-508（id 冲突）全部覆盖负路径 |

### 3.3 Group C: Completeness And Contract

| ID | 检查 | 结论 | 证据 |
|----|------|------|------|
| C1 Requirement contract | ✓ | 所有 FR/NFR/CON/ASM 字段齐全（ID / Statement / Acceptance / Priority / Source） |
| C2 Scope closure | ✓ | § 4.1 含 / § 4.2 不含 / § 5 范围外，三段闭合，不依赖聊天记忆 |
| C3 Open-question closure | ✓ | § 11 列出 6 条 OQ，全部非阻塞或"阻塞→已答"；OQ-501~506 均给出当前判断，可在 design stage 直接落决议 |
| C4 Template alignment | ✓ | 沿用 F003/F004 同款 spec 骨架，符合 AGENTS.md `docs/features/` 约定 |
| C5 Deferral handling | ✓ | § 5 显式列出"批量导入 / experience edit / knowledge link / 跨仓库同步 / TUI wizard / source_session 自动绑定" 6 项 deferred；本 cycle 不写代码 / 不写 stub 显式承诺 |
| C6 Goal and success criteria | ✓ | § 2.2 6 条 success criteria（零配置可用 / CRUD 闭环 / 复用零回归 / 人机两友 / 自描述持久态 / CLI 文档可冷读），每条均映射到具体 FR/NFR（详见 § 3.6） |
| C7 Assumption visibility | ✓ | § 10 ASM-501~504 含失效影响（"CLI 退 1 + stderr 提示"、"v1.1 invariant 退化由 NFR-501 接住"、"deferred 接走 $EDITOR 期望"、"design 阶段消化 ExperienceIndex.delete fallback"） |

### 3.4 Group G: Granularity And Scope-Fit

| ID | 检查 | 结论 | 备注 |
|----|------|------|------|
| G1 Oversized FR | ✓（minor） | FR-507 是 GS2 CRUD-packing 的边界（show + delete 两件事），但主题 cohesive、验收可独立判断；FR-503 把 `--topic/--tags/--content/--from-file/--status` 5 个可选字段统一为"按显式传入字段更新"，是合理 cohesive 而非场景爆炸（GS3） |
| G2 Mixed release boundary | ✓ | § 4.2 / § 5 明确划掉"schema 变更 / 行为契约改动 / TUI / LLM 自动归类 / experience edit / 批量导入 / 跨仓库同步"，本轮与后续增量边界清晰 |
| G3 Repairable scope | ✓ | 即便回 `需修改`，1 项 important（Q4 矛盾的 1 处 wording 收敛）+ 2~3 项 minor 单轮可消化；不需要推倒重来 |

### 3.5 验证 spec 对源码与 cycle precedent 的事实一致性

| 项 | 结论 | 证据 |
|----|------|------|
| `KnowledgeStore.update()` 是否存在并保证 `version+=1` | ✓ | `knowledge_store.py:181-204`，`entry.version += 1` 后调 `store()`，与 FR-503 / CON-503 描述吻合 |
| `KnowledgeStore.{store,retrieve,delete,search,list_entries}` 是否存在 | ✓ | `knowledge_store.py:53/86/206/111/228`，FR-501/504/505 均落在已存在 API |
| `ExperienceIndex.{store,retrieve,delete,update,list_records}` 是否存在 | ✓ | `experience_index.py:34/59/139/124/160`；ASM-504 中"若没有 delete API"的 fallback 实际上不会触发，design 阶段可直接确认正向路径 |
| `ExperienceIndex.INDEX_PATH` 实际位置 | ⚠ minor | 实际为 `knowledge/.metadata/index.json`（`experience_index.py:23`），与 FR-507 验收第 4 条说的 `.garage/experience/records/.metadata/index.json`（行 219）路径不一致。spec 里写错了索引路径 |
| `KnowledgeEntry.front_matter` 字段是否存在并支持 extras 持久化 | ✓ | `types/__init__.py:115` + `knowledge_store.py:418-424` 已支持 extras 持久化（F004 § 11.2.1 已落地） |
| `ExperienceRecord` 是否含 `artifacts: List[str]` | ✓ | `types/__init__.py:132`，与 FR-509 第 3 句 `artifacts = ["cli:experience-add"]` 写法兼容 |
| 现有 CLI surface 是否与 F005 增量正交 | ✓ | `cli.py` 现有 `knowledge {search,list}`、`memory review`，F005 在 `knowledge` 父命令下挂 `add/edit/show/delete`、新增 `experience` 父命令挂 `add/show/delete`，无命名冲突 |
| 现有 stdout 模块常量模式（F004 § 11.5） | ✓ | `cli.py:16-21` `MEMORY_REVIEW_ABANDONED_NO_PUB` / `MEMORY_REVIEW_ABANDONED_CONFLICT`，NFR-504 列出的 `KNOWLEDGE_ADDED_FMT` 等沿用同款模式 |
| F003/F004 baseline 测试数 | ✓ | task-progress 与 RELEASE_NOTES 双源确认 414 passed；NFR-501 / SC-3 阈值取自该基线 |

### 3.6 Success criteria → FR/NFR 映射检查

| Success Criterion | 映射 | 是否可判断 |
|-------------------|------|-----------|
| SC-1 零配置可用（`garage init && garage knowledge add ...`）| FR-501 + ASM-501 | ✓ Given 全新 `.garage/` 的验收 |
| SC-2 CRUD 闭环（add → show → edit → show → delete → show）| FR-501/503/504/505 + FR-507 | ✓ 各 FR 验收串联 |
| SC-3 复用既有契约零回归 | NFR-501 + CON-503 | ✓ `pytest tests/ -q ≥ 414 passed` 命令级断言 |
| SC-4 人机两友（非交互 + stdout 标记）| NFR-504 + § 4.1 stdout 常量行 | ✓ grep + assert 风格 |
| SC-5 自描述持久态（`source_artifact` 含 cli marker）| FR-509 + CON-504 | ✓ 3 条验收覆盖 add / edit / publisher 互不污染 |
| SC-6 CLI 文档可冷读（`--help` + 用户指南）| FR-510 + NFR-505 | ✓ 4 条 help 验收 + grep 7 个字符串 |

6 条全部映射到具体 FR/NFR，**无悬空**。

### 3.7 与 F003 candidate→publisher 路径的非干涉性

CON-504 + FR-509 验收第 3 条（"经 `garage memory review --action=accept` 发布的 entry，front matter `source_artifact` **不**等于 `cli:knowledge-add`"）显式锁住"自动路径不被 CLI 手工路径污染"；§ 2.3 / § 4.2 / OQ-501 三处独立确认本 cycle 是旁路而不是合并。判定：**未引入候选/发布路径回归风险**，与 F003 design § 11.4 兼容。

## 4. 发现项

> 无 critical finding。1 项 important（Q4 spec 内部直接矛盾，应批准前修复）；其余 minor 全部 LLM-FIXABLE，不阻塞设计。

1. `[important][LLM-FIXABLE][Q4][Q7]` **FR-501 与 FR-508 对 ID hash 输入定义直接矛盾**。FR-501 验收第 4 条（行 159）写 "6-hex 来自 `sha256(topic + content)[:6]`，**保证可复算**"；FR-508 需求陈述（行 230）写 "6 hex 来自 `sha256((topic + "\n" + content + "\n" + iso8601 second-precision now)...).hexdigest()[:6]`"，且 FR-508 验收第 1 条要求"同一 topic + content 在不同秒被 add → 两次得到不同 ID"。两条互斥：FR-508 的算法不"可复算"（依赖墙钟）；FR-501 的算法不能产出 FR-508 验收 #1 要求的"不同秒不同 ID"。修复方向（任选其一）：(a) FR-501 验收 #4 改为"参考 FR-508 算法，含秒级时间戳"，删除"保证可复算"措辞；或 (b) FR-508 改回不含时间戳并改用 (type, id) 重复检测兜底碰撞。修复仅需 1~2 行 wording，不涉及业务事实输入 → LLM-FIXABLE。
2. `[important][LLM-FIXABLE][Q1][C1]` **FR-507 验收第 4 条索引路径写错**：写为 `.garage/experience/records/.metadata/index.json`（行 219），但源码 `experience_index.py:23` `INDEX_PATH = "knowledge/.metadata/index.json"`。spec 引用了不存在的索引路径，会导致 design 阶段沿错误锚点设计或 implementation 阶段对错文件做断言。修复：把路径改为 `.garage/knowledge/.metadata/index.json`（与 `ExperienceIndex._update_index/_remove_from_index` 实际写入路径一致）。LLM-FIXABLE。
3. `[minor][LLM-FIXABLE][A3]` **NFR-502 验收 #2 把 `grep -r "import " src/garage_os/cli.py` 写进规格层**。这是实现文件路径级断言，属偏向实现层的检查方式。可改为：`pyproject.toml` diff 不新增 third-party 依赖 +"CLI 模块导入面"由 design / code-review 阶段约束。**不阻塞**。
4. `[minor][LLM-FIXABLE][A2][G1]` **FR-507 同时定义 `experience show` 与 `experience delete`**（GS2 CRUD-packing 边界）。主题 cohesive、验收可独立判断，但拆为 FR-507a / FR-507b 会让 traceability gate 阶段逐项追溯更直接。**不阻塞**。
5. `[minor][LLM-FIXABLE][A3]` **§ 4.1 表格与 FR-501 验收 #4 各重复了一次 ID 生成规则**。除了引发 finding #1 的矛盾，也属于 Q7 散落表述。建议保留 FR-508 一处权威定义，§ 4.1 与 FR-501 改为"按 FR-508 规则生成"。修 finding #1 即可顺手收敛。**不阻塞**。

## 5. 缺失或薄弱项

- 无关键缺失。
- ASM-504 提到"若 `ExperienceIndex` 没有 `delete()` 等价 API → 在 CLI 层走 `FileStorage.delete()` + 手动 reindex"，实际上源码已有 `ExperienceIndex.delete()`（`experience_index.py:139-158`）。该 ASM 的 fallback 分支不会触发，可在 design stage 直接确认正向路径，无需写入 spec 修订。
- § 11 OQ-502 标记"阻塞→已答"，给出"`hf-design` 阶段定具体路径"的默认建议；OQ-503/504/505/506 全部非阻塞且给出当前判断，design stage 可直接落决议，不会反推规格。

## 6. 结论

**需修改**

判断依据：
- 出现 1 项 important LLM-FIXABLE finding（FR-501 vs FR-508 ID 算法直接矛盾），按 rubric"important（应批准前修复）"应进入 1 轮定向回修
- 1 项 important LLM-FIXABLE finding（FR-507 索引路径与源码不符）属事实性引用错误，会沿错误锚点污染 design 阶段
- 3 项 minor LLM-FIXABLE 不阻塞设计，可与上述 important findings 同轮收敛
- 无 USER-INPUT 类阻塞 finding（finding #1 与 #2 都不需要新业务事实）
- 无 critical / route / stage / 证据冲突
- 范围 / 范围外 / 假设 / 开放问题闭合度足以支撑 1 轮 `hf-specify` 定向回修后通过

预计回修工作量：1 轮，<10 分钟（5 处 wording 收敛），不需要重写任何 FR 主体，不需要新增业务事实。

## 7. 下一步

- **`hf-specify`**：父会话回流 `hf-specify` 节点，针对 § 4 列出的 5 项 finding 做定向回修：
  1. 解决 FR-501 vs FR-508 ID 算法矛盾（保留 FR-508 一处权威定义）
  2. 修正 FR-507 索引路径为 `.garage/knowledge/.metadata/index.json`
  3. NFR-502 验收 #2 去 implementation 文件路径
  4. （可选）FR-507 拆为 507a/507b
  5. § 4.1 / FR-501 引用 FR-508 而不是重写算法
- 修订完成后重新派发 `hf-spec-review` 复审
- 不需要 reroute via router

## 8. 交接说明

- `hf-specify`（auto mode）：父会话直接进入回修；本批 finding 全部 LLM-FIXABLE，无需向用户发起额外问卷
- LLM-FIXABLE 类 finding **不**转嫁给用户，只在父会话向用户的 plain-language 摘要中提示"spec 内有 1 项算法定义矛盾 + 1 项索引路径事实错误，已自动回修"
- 无 USER-INPUT finding，父会话不需要发起最小定向问题
- `规格真人确认` 步骤暂不进入；待 r2 review `通过` 后再启动

## 9. 结构化返回

```json
{
  "conclusion": "需修改",
  "next_action_or_recommended_skill": "hf-specify",
  "record_path": "/workspace/docs/reviews/spec-review-F005-knowledge-authoring-cli.md",
  "key_findings": [
    "[important][LLM-FIXABLE][Q4] FR-501 验收 #4 与 FR-508 对 ID 哈希输入定义直接矛盾（前者无时间戳且声称可复算，后者含秒级时间戳并要求不同秒不同 ID）",
    "[important][LLM-FIXABLE][Q1] FR-507 验收 #4 索引路径 .garage/experience/records/.metadata/index.json 与源码 experience_index.py:23 实际路径 knowledge/.metadata/index.json 不一致",
    "[minor][LLM-FIXABLE][A3] NFR-502 验收 #2 用 grep -r 'import ' src/garage_os/cli.py 实现文件路径级断言，应抽象为依赖面约束",
    "[minor][LLM-FIXABLE][A2/G1] FR-507 同时定义 experience show 与 delete，可拆为 507a/507b 提升 traceability 粒度",
    "[minor][LLM-FIXABLE][A3] § 4.1 表格与 FR-501 验收 #4 重复 ID 生成规则，应统一引用 FR-508 一处权威定义"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q4",
      "summary": "FR-501 vs FR-508 对 ID 哈希输入定义直接矛盾"
    },
    {
      "severity": "important",
      "classification": "LLM-FIXABLE",
      "rule_id": "Q1",
      "summary": "FR-507 验收 #4 索引路径与 ExperienceIndex.INDEX_PATH 实际路径不一致"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "A3",
      "summary": "NFR-502 验收 #2 把实现文件 grep 写进规格层"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "A2",
      "summary": "FR-507 打包 experience show + delete，可拆为 507a/507b"
    },
    {
      "severity": "minor",
      "classification": "LLM-FIXABLE",
      "rule_id": "A3",
      "summary": "§ 4.1 与 FR-501 重复 ID 生成规则，应统一引用 FR-508"
    }
  ],
  "success_criteria_to_fr_mapping": {
    "SC-1": "FR-501 + ASM-501",
    "SC-2": "FR-501/503/504/505 + FR-507",
    "SC-3": "NFR-501 + CON-503",
    "SC-4": "NFR-504",
    "SC-5": "FR-509 + CON-504",
    "SC-6": "FR-510 + NFR-505"
  }
}
```
