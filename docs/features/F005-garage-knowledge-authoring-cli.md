# F005: Garage Knowledge Authoring CLI — 让 Stage 2 飞轮能从终端起转

- 状态: 已批准（auto-mode approval；见 `docs/approvals/F005-spec-approval.md`）
- 主题: 给 `garage` CLI 增加可被人类直接调用的 `knowledge add` / `knowledge edit` / `knowledge show` / `knowledge delete` 子命令（以及对应的 `experience add` / `experience show` / `experience delete`），让用户在没有触发 session 归档、也没有候选批次的情况下，也能用 1 行命令把一条决策 / 模式 / 解法（或一条 ad-hoc 经验）持久化到 `.garage/knowledge/`（或 `.garage/experience/`）。
- 日期: 2026-04-19
- 关联:
  - F001（Garage Agent 操作系统）— `KnowledgeStore` / `ExperienceIndex` 契约
  - F002（Garage Live）— CLI surface
  - F003（Garage Memory — 自动知识提取与经验推荐）— 候选 → 发布管道
  - F004（Garage Memory v1.1）— 发布身份解耦 + abandon 语义收敛
  - `docs/soul/manifesto.md`、`docs/soul/growth-strategy.md`（Stage 2 → Stage 3 触发条件）
  - `RELEASE_NOTES.md` "F004 — 已知限制 / 后续工作" 段（Stage 3 进入信号判断需要 ≥100 knowledge entries）

## 1. 背景与问题陈述

F003 / F004 把 Garage 推到了 Stage 2 "记忆体"：session 归档可触发候选提取、用户在 `garage memory review` 决定是否发布、`garage run` 能基于已发布知识做主动推荐。整套机器跑得通，单元 / 集成测试 414 个绿。

但 Stage 2 飞轮（使用 → 积累 → 提炼 → 增强 → 使用）今天**只有一根输入轴**：必须先发生一个 session 归档、再让自动提取生成候选、再人工 review 通过。这导致以下真实摩擦：

1. **解决方案场景缺失**：用户在终端独立解决了一个问题（"修了一个 bug"、"试出了一段架构决策"、"踩了一个坑"），手头没有 active session，候选提取也不会被触发。结果：这条经验没有任何低摩擦的入口能进 `.garage/knowledge/`。
2. **零起步问题**：当前仓库 `.garage/knowledge/decisions/`、`patterns/`、`solutions/` 全部空目录，`.garage/experience/records/` 0 条记录。`garage knowledge search` / `list` 可读但永远返回 "No knowledge entries"。`growth-strategy.md` Stage 2 → Stage 3 的进入信号是"知识库条目 >100"，**今天为 0**——飞轮甚至还没起转。
3. **"宿主无关"原则的隐性违反**：今天的"添加知识"路径必须依赖 Claude Code 触发 session → archive，等价于把"知识入库"绑定到了一个特定宿主。`design-principles.md` § 1 明确说"移除当前宿主后，核心约定和数据是否仍然完整可理解？"——读侧已经满足（`KnowledgeStore` 直接读 markdown），但写侧今天必须借宿主之手。
4. **CLI 用户契约破缺**：F002 已经把 `garage` 立成了 canonical CLI surface（`init` / `status` / `run` / `knowledge` / `memory`），但 `knowledge` 子命令今天**只读**。从用户视角，这是个"半截 CRUD"：能 list、能 search，却不能 add / edit / delete。

愿景上下文：`docs/soul/user-pact.md` 与 `manifesto.md` 反复强调"数据归你"、"宿主可换"、"渐进增强"。Stage 1 → Stage 2 的过渡不是只在 schema 层完成的；它必须在**用户能在终端里 1 行命令把一条经验存进自己的仓库**这件事上，对 solo creator 友好。F005 收敛的就是这一根缺失的输入轴。

## 2. 目标与成功标准

### 2.1 核心目标

让 `.garage/knowledge/` 和 `.garage/experience/` 在不依赖 session / 候选提取 / Claude Code 任何特殊行为的前提下，仅凭 `garage` CLI 即可完成 CRUD：

```
增 → garage knowledge add  / experience add
查 → garage knowledge show / experience show （已存在的 search/list 之外的精确读）
改 → garage knowledge edit
删 → garage knowledge delete / experience delete
```

读路径（`search` / `list`）已存在，本 cycle 不重写。

### 2.2 成功标准

1. **零配置可用**：在一个全新仓库，`garage init && garage knowledge add ...` 一行命令就能成功写入一条 `KnowledgeEntry`，不需要任何 platform.json 改动、不需要 Claude Code 在线、不需要先有 session。
2. **CRUD 闭环**：同一条 `(type, id)` 可被 `add` → `show` → `edit` → `show` → `delete` → `show` 全链路操作，每一步退出码 0；`delete` 后 `show` 退 1 且 stdout 含 "Not found" 提示。
3. **复用既有契约零回归**：`KnowledgeStore.store/update/retrieve/delete/search/list_entries` 行为不变；F003 重复发布走 `update()` 的 v1.1 不变量不变；F003/F004 的 384 → 414 测试基线不退绿。
4. **人机两友**：CLI 既支持非交互模式（命令行参数 + stdin / `--from-file`）以便 Agent 调用，也对人类可读（清晰的 success / error 文案、统一的 stdout 标记常量）。
5. **自描述持久态**：写入磁盘的 markdown front matter 必须包含 `id` / `type` / `topic` / `date` / `tags` / `status` / `version` / `source_artifact`（来源 = `cli:knowledge-add` 或 `cli:knowledge-edit`），让任何后来 Agent 仅凭文件本身就能理解这条 entry 来自手工添加路径。
6. **CLI 文档可被冷读**：`docs/guides/garage-os-user-guide.md` 增"Knowledge authoring (CLI)"段；任何用户从 `garage knowledge --help` 出发，不需要读源码就能完成 add/edit/delete 三类操作。

### 2.3 非目标

- 不引入交互式 TUI / wizard / prompt（人类要交互式编辑可走 `--from-file` + `$EDITOR`，但 wizard UI 不在本 cycle 内）。
- 不引入新的 `KnowledgeEntry` / `ExperienceRecord` 字段；**复用 F003/F004 已有 schema**。
- 不改 `KnowledgeStore` / `ExperienceIndex` 任何行为契约；本 cycle 只在 CLI 层调用现有 store/update/retrieve/delete API。
- 不引入 LLM 自动归类（"我描述一段，AI 决定它是 decision / pattern / solution"），用户必须显式指定 `--type`。
- 不变更 F003 候选 → 发布 pipeline；`garage memory review` 仍是候选确认入口，与本 cycle 互不影响。
- 不引入 `experience edit`：`ExperienceRecord` 在 F003 设计上是不可变的执行快照（only `update_experience()` for outcome amendment 走推荐路径），手动改不属于 Stage 2 的核心使用面。

## 3. 用户角色与关键场景

### 3.1 主要用户角色

- **Solo Creator**：人类直接使用者。手头有一段刚踩出来的经验，想"快速记一笔"。期望命令直观、错误清晰、不要把简单的事情搞复杂。
- **Pack 作者 / Agent 调用方**：未来的自动化路径（不在本 cycle 内）会调用本 CLI 把"分析得到的复用模式"写进 knowledge base。期望参数稳定、退出码语义明确、stdout 可解析。
- **运行时审计读者**：在 `git log` / `git diff` 看磁盘变化的人。期望 add/edit/delete 都对应清晰的、可 review 的 markdown 改动。

### 3.2 关键场景

1. **快速记录一条决策**：用户在终端说
   ```bash
   garage knowledge add --type decision --topic "选择 SQLite over Postgres 作为本地知识索引" \
       --tags storage,decision --content "Postgres 需要 daemon, 违反 workspace-first..."
   ```
   → CLI 写入 `.garage/knowledge/decisions/decision-<id>.md`，stdout 输出 `Knowledge entry 'decision-<id>' added`，退出码 0。
2. **从文件追加一条模式**：用户先把长文本写进 `pattern.md`，然后
   ```bash
   garage knowledge add --type pattern --topic "Front-matter as schema" --tags arch --from-file pattern.md
   ```
   → CLI 把整个文件 body 当 `content` 写入 `.garage/knowledge/patterns/...`。
3. **修改已存在 entry**：用户发现某条 decision tag 漏了
   ```bash
   garage knowledge edit --type decision --id <id> --tags storage,decision,sqlite
   ```
   → CLI 调 `KnowledgeStore.update()`，front matter `version=2`，markdown 文件不变。
4. **删除一条过时 entry**：
   ```bash
   garage knowledge delete --type pattern --id <id>
   ```
   → CLI 调 `KnowledgeStore.delete()`，markdown 文件被移除，stdout `Knowledge entry '<id>' deleted`，退出码 0。
5. **精确读取一条 entry**：
   ```bash
   garage knowledge show --type solution --id <id>
   ```
   → stdout 打印 front matter + content；找不到时退 1。
6. **手动追加一条经验**：用户做完一段不在 session 内的实验
   ```bash
   garage experience add --task-type spike --skill ahe-design --domain platform \
       --outcome success --duration 1800 --complexity medium \
       --summary "试出了 SQLite 索引方案"
   ```
   → 写入 `.garage/experience/records/exp-<id>.json`。
7. **零回归保护**：F003 候选 → publisher → `KnowledgeStore.store/update` 路径在 v1.2 行为下仍走原有版本链；`pytest tests/ -q` ≥414 passed。

## 4. 当前轮范围与关键边界

### 4.1 包含

| 功能 | 描述 |
|------|------|
| `garage knowledge add` | 用 `--type` / `--topic` / `--tags` / `--content` 或 `--from-file` 构造 `KnowledgeEntry` 并调用 `KnowledgeStore.store()` |
| `garage knowledge edit` | 通过 `--type` + `--id` 定位现有 entry，按显式传入的字段覆写 + 调用 `KnowledgeStore.update()`（保持 v1.1 的 `version+=1` 不变量） |
| `garage knowledge show` | 通过 `--type` + `--id` 调用 `KnowledgeStore.retrieve()`，stdout 打印 front matter + content |
| `garage knowledge delete` | 通过 `--type` + `--id` 调用 `KnowledgeStore.delete()`，stdout 报告结果 |
| `garage experience add` | 用 `--task-type` / `--skill` / `--domain` / `--outcome` / `--duration` / `--complexity` / `--summary`（→ `lessons_learned`） / `--tags`（→ `key_patterns`）构造 `ExperienceRecord` 并调用 `ExperienceIndex.store()` |
| `garage experience show` | 通过 `--id` 读取 `.garage/experience/records/<id>.json` 并 pretty-print |
| `garage experience delete` | 通过 `--id` 删除一条 experience record（薄包装，调用 `ExperienceIndex.delete()` 或 storage 删除 + index 清理） |
| ID 生成 | 未传 `--id` 时由 CLI 生成稳定可读 ID。具体算法、可复算性边界与冲突处理见 **FR-508**（权威定义） |
| 来源标记 | front matter `source_artifact` 自动写为 `cli:knowledge-add` / `cli:knowledge-edit`，让自动路径产出物与手动路径产出物可被 grep 区分 |
| 输入校验 | `--type` 必须在 `{decision, pattern, solution}` 集合内；`--topic` 非空；`add` 必须提供 `--content` 或 `--from-file` 之一；`edit` 至少传一个可改字段 |
| 文档同步 | `docs/guides/garage-os-user-guide.md` 增 "Knowledge authoring (CLI)" 段；`README.md` / `README.zh-CN.md` 在 CLI 命令表中追加 7 个新子命令 |
| stdout 常量 | 模块常量 `KNOWLEDGE_ADDED_FMT` / `KNOWLEDGE_EDITED_FMT` / `KNOWLEDGE_DELETED_FMT` / `KNOWLEDGE_NOT_FOUND_FMT` / `EXPERIENCE_ADDED_FMT` / `EXPERIENCE_DELETED_FMT` / `EXPERIENCE_NOT_FOUND_FMT`，便于 Agent 调用方做 stdout 解析 |

### 4.2 不包含

- 任何 `KnowledgeEntry` / `ExperienceRecord` schema 变更
- 任何 `KnowledgeStore` / `ExperienceIndex` 行为改动（含 conflict 探测、相似度、推荐）
- 任何交互式 TUI / wizard / prompt
- 任何 LLM-based 自动分类 / 自动 tag 抽取
- 任何 `garage memory review` 行为改动（候选 → publisher 路径不动）
- `experience edit`（见 §2.3 非目标）
- 同名导入 / 批量导入 / `--from-csv` / `--from-jsonl`（候选 deferred，§ 5）
- `garage knowledge export` / 跨仓库共享（Stage 4 远景，§ 5）

## 5. 范围外内容

延后到后续 cycle 的真实候选（不在本规格内消化）：

- **批量导入**：`garage knowledge import --from-jsonl ...` / `--from-csv ...`，让用户可以一次性把一大段历史笔记导进来。Stage 2 → Stage 3 触发信号 "知识库条目 >100" 真实变现时再做。
- **`experience edit`**：`ExperienceRecord` 是执行快照，手改语义需要先在 F003 推荐路径里厘清"什么字段允许事后被覆盖"。
- **`garage knowledge link`**：手动维护 `related_decisions` / `related_tasks` 的入口。今天可以靠 `--from-file` 直接在 markdown 里写。
- **跨仓库同步 / pack 化分发**：Stage 4 范畴，明确不在本 cycle。
- **TUI wizard**：`garage knowledge add -i` 走交互式提问。等真出现"用户嫌命令行参数太多"的反馈再做。
- **`source_session` 自动绑定**：CLI 当前一律不绑 session（手动添加路径设计上就是 session-free）。如果未来要支持"在某个 session 里手动追加一条 entry 并自动绑定"，可独立立项。

延后内容必须在本规格中显式列出（INVEST G6 非目标显式化）；本 cycle 内**不**写代码、**不**写测试、**不**写 stub 占位。

## 6. 功能需求

### FR-501 `knowledge add` 必须能从 CLI 一行写入一条 entry

- **优先级**: Must
- **来源**: § 1 摩擦 1（解决方案场景缺失）；§ 3.2 场景 1
- **需求陈述**: When 用户调用 `garage knowledge add --type <decision|pattern|solution> --topic <非空字符串> --content <字符串>`（可选 `--tags <逗号分隔>` / `--id <字符串>`），the system shall 调用 `KnowledgeStore.store()` 持久化为 `<type>-<id>.md` 到 `.garage/knowledge/<type>s/`，front matter 含 `id` / `type` / `topic` / `date` / `tags` / `status="active"` / `version=1` / `source_artifact="cli:knowledge-add"`，退出码 0，stdout 输出 `Knowledge entry '<id>' added` 一行。
- **验收标准**:
  - Given 全新 `.garage/`（`garage init` 后），When `garage knowledge add --type decision --topic "X" --content "Y"`，Then `.garage/knowledge/decisions/decision-<id>.md` 被创建，front matter 含全部 § FR-501 列出字段，stdout 含 `Knowledge entry 'decision-<id>' added`，退出码 0
  - Given 同上，When 用户传 `--tags a,b,c`，Then front matter `tags: ['a', 'b', 'c']`
  - Given 用户传 `--id custom-001`，Then 文件名 = `decision-custom-001.md`
  - Given 用户**未**传 `--id`，Then CLI 走 **FR-508** 定义的 ID 生成算法（本 FR 不重复算法定义；冲突处理由 FR-508 决定）

### FR-502 `knowledge add` 必须支持 `--from-file` 作为 content 来源

- **优先级**: Must
- **来源**: § 3.2 场景 2
- **需求陈述**: When 用户传 `--from-file <path>`（不传 `--content`），the system shall 把 `<path>` 文件全部 UTF-8 文本读入作为 `KnowledgeEntry.content`；`<path>` 不存在或不可读时，CLI 退出码 1 + stderr 报错。
- **验收标准**:
  - Given `pattern.md` 存在含 100 字 body，When `garage knowledge add --type pattern --topic "T" --from-file pattern.md`，Then 写盘 entry.content == 文件全文
  - Given `--content` 与 `--from-file` 同时传，Then CLI 退 1 + stderr `--content and --from-file are mutually exclusive`
  - Given `add` 时既不传 `--content` 也不传 `--from-file`，Then CLI 退 1 + stderr `add requires --content or --from-file`
  - Given `--from-file` 指向不存在路径，Then CLI 退 1 + stderr `File not found: <path>`

### FR-503 `knowledge edit` 必须按显式传入字段更新现有 entry

- **优先级**: Must
- **来源**: § 3.2 场景 3
- **需求陈述**: When 用户调用 `garage knowledge edit --type <T> --id <I>` 加任意一个或多个 `--topic` / `--tags` / `--content` / `--from-file` / `--status`，the system shall 先 `retrieve(T, I)`，对显式传入字段做覆写（**未传字段保持不变**），把 `source_artifact` 改为 `"cli:knowledge-edit"`，调用 `KnowledgeStore.update()`（version 自动 +1），stdout 输出 `Knowledge entry '<id>' edited (version <new_version>)`。
- **验收标准**:
  - Given `(decision, k1)` 存在 `version=1` `tags=[a]`，When `garage knowledge edit --type decision --id k1 --tags a,b`，Then 磁盘 `version=2` `tags=['a','b']`，topic / content 保持不变；stdout 含 `(version 2)`
  - Given `edit` 调用未传任何可改字段（仅 `--type` `--id`），Then CLI 退 1 + stderr `edit requires at least one of --topic / --tags / --content / --from-file / --status`
  - Given `(decision, missing)` 不存在，When 调用 `edit`，Then CLI 退 1 + stderr 含 `Knowledge entry 'missing' not found`，磁盘无变化
  - Given `--content` 与 `--from-file` 同时传，Then 与 FR-502 行为一致退 1
  - Given 多次 edit 同一 entry，Then 每次 `version` 单调 +1（v1.1 FR-401 不变量在 CLI 层延伸）

### FR-504 `knowledge show` 必须精确读取一条 entry 并 pretty-print

- **优先级**: Should
- **来源**: § 3.2 场景 5；CRUD 闭环对称性
- **需求陈述**: When 用户调用 `garage knowledge show --type <T> --id <I>`，the system shall 调用 `KnowledgeStore.retrieve(T, I)`；找到时 stdout 打印 front matter（人类可读 key: value 块）+ 空行 + content body，退出码 0；未找到时退 1 + stderr `Knowledge entry '<id>' not found`。
- **验收标准**:
  - Given `(decision, k1)` 存在 `topic="X" version=2 tags=['a']`，When `garage knowledge show --type decision --id k1`，Then stdout 含 `topic: X`、`version: 2`、`tags: a, b`（或可读等价）+ 空行后为 content body
  - Given `(decision, missing)` 不存在，Then 退 1 + stderr 含 `Knowledge entry 'missing' not found`
  - Given JSON-friendly 输出需求未来再考虑（不在本 cycle）；本轮仅人类可读

### FR-505 `knowledge delete` 必须能移除一条 entry

- **优先级**: Must
- **来源**: § 3.2 场景 4；CRUD 闭环对称性
- **需求陈述**: When 用户调用 `garage knowledge delete --type <T> --id <I>`，the system shall 调用 `KnowledgeStore.delete(T, I)`，磁盘文件被移除，stdout `Knowledge entry '<id>' deleted`，退出码 0；entry 不存在时退 1 + stderr `Knowledge entry '<id>' not found`，磁盘无副作用。
- **验收标准**:
  - Given `(pattern, p1)` 存在，When 调用 `delete`，Then 文件被删除，`KnowledgeStore.retrieve(pattern, p1)` 返回 None，stdout 含 `Knowledge entry 'p1' deleted`
  - Given `(pattern, missing)` 不存在，Then 退 1 + stderr 含 `Knowledge entry 'missing' not found`，磁盘无变化

### FR-506 `experience add` 必须能从 CLI 写入一条经验记录

- **优先级**: Should
- **来源**: § 3.2 场景 6；§ 1 摩擦 1（与 knowledge add 同源）
- **需求陈述**: When 用户调用 `garage experience add --task-type <T> --skill <S>(...重复) --domain <D> --outcome <success|failure|partial> --duration <int seconds> --complexity <low|medium|high> --summary <字符串>`（可选 `--id` / `--problem-domain` / `--tech` / `--tags`），the system shall 构造 `ExperienceRecord`，把 `--summary` 作为 `lessons_learned=[summary]`、`--tags` 作为 `key_patterns`、未传 `--problem-domain` 时取 `--task-type`、未传 `--id` 时生成 `exp-<YYYYMMDD>-<6 hex chars>`，调用 `ExperienceIndex.store()`，stdout `Experience record '<id>' added`，退出码 0。
- **验收标准**:
  - Given `garage init` 后，When `garage experience add --task-type spike --skill ahe-design --skill ahe-tasks --domain platform --outcome success --duration 1800 --complexity medium --summary "..."`，Then `.garage/experience/records/exp-<id>.json` 被创建，含 `task_type=spike`、`skill_ids=['ahe-design','ahe-tasks']`、`outcome="success"`、`duration_seconds=1800`、`complexity="medium"`、`lessons_learned=["..."]`，stdout 含 `Experience record 'exp-<id>' added`
  - Given `--outcome` 不在合法集合，Then `argparse` 退 2 + stderr 报错（标准 argparse 行为）
  - Given `--duration` 非整数，Then 同上 argparse 行为

### FR-507a `experience show` 必须能精确读取一条经验记录

- **优先级**: Should
- **来源**: § 4.1（CRUD 对称性）；§ 2.2 SC-2
- **需求陈述**: When 用户调用 `garage experience show --id <I>`，the system shall 调用 `ExperienceIndex.retrieve(I)`（等价于读取 `.garage/experience/records/<I>.json`），stdout pretty-print JSON，退出码 0；不存在则退 1 + stderr `Experience record '<I>' not found`。
- **验收标准**:
  - Given `exp-1.json` 存在，When `garage experience show --id exp-1`，Then stdout 是合法 JSON 且 keys 含 `record_id`、`task_type`、`outcome`
  - Given `exp-missing.json` 不存在，Then `show` 退 1 + stderr 含 `Experience record 'exp-missing' not found`

### FR-507b `experience delete` 必须能移除一条经验记录及其索引引用

- **优先级**: Should
- **来源**: § 4.1（CRUD 对称性）；§ 2.2 SC-2；OQ-502
- **需求陈述**: When 用户调用 `garage experience delete --id <I>`，the system shall 调用 `ExperienceIndex.delete(I)`（该 API 已在 F003 内提供，见 `experience_index.py` `delete()`，会同时删除 `.garage/experience/records/<I>.json` 并从中央索引 `.garage/knowledge/.metadata/index.json` 中摘除该条）；不存在则退 1 + stderr `Experience record '<I>' not found`，磁盘无副作用。
- **验收标准**:
  - Given `exp-1.json` 存在，When `delete`，Then 文件被删，紧跟 `show` 退 1
  - Given `exp-1` 已被中央索引（`.garage/knowledge/.metadata/index.json`）引用，When `delete`，Then 索引中不再引用 `exp-1`
  - Given `exp-missing` 不存在，Then `delete` 退 1 + stderr 含 `Experience record 'exp-missing' not found`

### FR-508 ID 生成必须时间敏感且不冲突

- **优先级**: Must
- **来源**: § 4.1 ID 生成；§ 2.2 SC-1
- **需求陈述**: 当用户未传 `--id` 时，the system shall 用 `<type-prefix>-<YYYYMMDD>-<6 hex chars>` 模式生成 ID。6 hex = `sha256((topic + "\n" + content + "\n" + iso8601_second_precision_now).encode("utf-8")).hexdigest()[:6]`，**时间戳是输入的一部分**（精度到秒，本地时区或 UTC 由设计层定）。这意味着：
  - **复算性边界**：仅在 `topic + content + 时间戳到秒` 三元组完全一致时可复算（用于测试与审计场景，不假设跨调用复算）。
  - **碰撞处理**：若生成的 `(type, id)` 已存在（最坏情况：同一秒同一 topic+content 重复 add），CLI 退 1 + stderr `Entry with id '<id>' already exists; pass --id to override or change inputs`，不覆盖现有文件。
- **验收标准**:
  - Given 同一 topic + content 在不同秒被 `add`，Then 两次得到不同 ID（时间戳不同 → hash 不同）
  - Given 同一 topic + content + 同一秒（测试可 monkeypatch `datetime.now` 锁秒），连续 `add` 两次，Then 第 1 次成功；第 2 次退 1 + stderr 含 `already exists`，磁盘第一条 entry 不被覆盖
  - Given 用户传 `--id custom`，Then ID 直接使用 `custom`，不走 hash 路径
  - Given 用户传 `--id custom` 且 `(type, custom)` 已存在，Then `add` 退 1 + stderr 含 `already exists`；FR-503 `edit` 路径不受影响

### FR-509 来源标记必须区分手工 vs 自动

- **优先级**: Must
- **来源**: § 2.2 SC-5；§ 1 摩擦 4（CLI 用户契约破缺）；F004 § 11.5（stable stdout marker 模式）
- **需求陈述**:
  - `knowledge add` 写盘 entry `source_artifact = "cli:knowledge-add"`
  - `knowledge edit` 把 entry `source_artifact` 覆写为 `"cli:knowledge-edit"`
  - `experience add` 写盘 record `artifacts = ["cli:experience-add"]`（或等价的 source 标记字段；若 `ExperienceRecord` 无独立 source 字段，则用 `artifacts` 列表头位）
- **验收标准**:
  - Given 通过 CLI 添加一条 entry，When 读取 markdown front matter，Then `source_artifact == "cli:knowledge-add"`
  - Given 同 entry 后续被 CLI edit，When 读取 front matter，Then `source_artifact == "cli:knowledge-edit"`，且 v1.1 publisher 路径写入的 entry 仍保持原 `source_artifact`（CLI 不污染自动路径）
  - Given 经 `garage memory review --action=accept` 发布的 entry，When 读取 front matter，Then `source_artifact` **不**等于 `"cli:knowledge-add"`（仍保留 publisher 写入的值）

### FR-510 CLI help 必须可冷读发现全部 7 个新子命令

- **优先级**: Should
- **来源**: § 2.2 SC-6；`design-principles.md` 原则 5 "约定可发现"
- **需求陈述**: When 用户调用 `garage knowledge --help` 或 `garage experience --help`，the system shall 列出全部新子命令（含本 cycle 引入的 add / edit / show / delete），并对每个子命令的 `--help` 输出列出全部参数及其语义。
- **验收标准**:
  - Given `garage knowledge --help`，Then stdout 含 `add` / `edit` / `show` / `delete` / `search` / `list` 6 个子命令名
  - Given `garage experience --help`，Then stdout 含 `add` / `show` / `delete` 3 个子命令名
  - Given `garage knowledge add --help`，Then stdout 含 `--type` / `--topic` / `--tags` / `--content` / `--from-file` / `--id`
  - Given `garage experience add --help`，Then stdout 含 `--task-type` / `--skill` / `--domain` / `--outcome` / `--duration` / `--complexity` / `--summary`

## 7. 非功能需求

### NFR-501 零回归保护

- **优先级**: Must
- **来源**: § 2.2 SC-3；F004 NFR-301（同模式）
- **需求陈述**: F003/F004 已存在的 414 个测试在 v1.2 引入后必须**全部继续 passed**；任何回归（哪怕新增了"等价但更好"的行为）都必须先回 `hf-specify` 或显式申请 `hf-increment`。
- **验收标准**: `pytest tests/ -q` ≥ 414 passed；F005 新增测试单独计数。

### NFR-502 默认零外部依赖

- **优先级**: Must
- **来源**: § 2.3 非目标；`design-principles.md` 原则 3 渐进复杂度
- **需求陈述**: F005 引入的 CLI 路径只允许使用 stdlib + 现有 `garage_os.*` 模块；不引入新的 third-party 依赖（不引入 click / typer / prompt-toolkit / rich 等）。
- **验收标准**:
  - `pyproject.toml` 在本 cycle 不新增 runtime dependency
  - F005 引入的所有新源码模块（CLI 子命令处理器及其直接被调用的 helper）的 `import` 闭包仅包含 Python stdlib + `garage_os.*` 内部模块；评审时按依赖面校验（不绑定具体文件路径），任何新引入的 third-party import 视为违反 NFR-502

### NFR-503 写路径耗时上限

- **优先级**: Should
- **来源**: 用户可感知性（"快速记一笔"）
- **需求陈述**: `garage knowledge add` / `edit` / `delete` 单次调用在已 init 仓库下，从 process start 到 exit 总耗时 < 1.0s（不含 cold Python import 之外的额外 IO）。
- **验收标准**: 新增 1 个 wall-clock smoke 断言（`time.monotonic()` 包一次 add 调用，断言 < 1.0s）；不在 NFR 内做完整 benchmark。

### NFR-504 错误输出语义化

- **优先级**: Must
- **来源**: § 2.2 SC-4；F004 § 11.5（同模式：stable stdout markers）
- **需求陈述**: 所有 success / failure stdout / stderr 文案必须由 `cli.py` 模块顶层常量产出（`KNOWLEDGE_ADDED_FMT` 等），便于 Agent 调用方做 stdout 解析；不允许在内联 f-string 散写。
- **验收标准**: `grep "Knowledge entry " src/garage_os/cli.py` 仅命中 fmt 常量定义；测试用 `assert FMT.format(...) in stdout` 风格断言。

### NFR-505 文档同步

- **优先级**: Should
- **来源**: § 2.2 SC-6；F003 / F004 同模式
- **需求陈述**: `docs/guides/garage-os-user-guide.md` 必须新增 "Knowledge authoring (CLI)" 段，覆盖 add / edit / show / delete 4 个子命令的最小示例 + experience 3 个子命令；`README.md` / `README.zh-CN.md` 在 CLI 命令列表里追加新命令名（不要求详细示例）。
- **验收标准**: 新增/编辑后的 markdown 中能 grep 到 `garage knowledge add`、`garage knowledge edit`、`garage knowledge show`、`garage knowledge delete`、`garage experience add`、`garage experience show`、`garage experience delete` 7 个字符串。

## 8. 外部接口与依赖

- **依赖既有模块**：`garage_os.cli`、`garage_os.storage.FileStorage`、`garage_os.knowledge.KnowledgeStore`、`garage_os.knowledge.ExperienceIndex`、`garage_os.types.{KnowledgeEntry, KnowledgeType, ExperienceRecord}`。
- **不引入新 third-party 依赖**（NFR-502）。
- **不依赖** `ClaudeCodeAdapter` / `SessionManager` / `MemoryExtractionOrchestrator` / `KnowledgePublisher`。本 cycle 的 CLI 子命令独立于 F002 的 `garage run` 路径与 F003/F004 的 candidate → publisher 路径。

## 9. 约束与兼容性要求

- **CON-501**：CLI 入口仍是 `garage` 顶级命令；新增子命令必须挂在现有 `knowledge` / `experience` 父命令下，不引入新顶级命令。
- **CON-502**：`KnowledgeStore` / `ExperienceIndex` 行为契约不可变更；本 cycle 仅在 CLI 层调用其现有公开 API（`store/update/retrieve/delete/search/list_entries` 与 `ExperienceIndex` 等价方法）。
- **CON-503**：F004 v1.1 不变量必须保持：CLI `edit` 走的 `KnowledgeStore.update()` 必须仍然 `version+=1`；CLI 不可绕开 store/update 直接写文件。
- **CON-504**：`source_artifact` 取值不可与 publisher 路径已使用的取值冲突；本 cycle 取 `"cli:knowledge-add"` / `"cli:knowledge-edit"`，与 publisher 在 F003 的 `published_from_candidate=<candidate_id>` 同位但语义独立。
- **CON-505**：CLI 不可在写盘前对 markdown body 做语义性变形（不 trim、不规范化换行、不强制结尾换行变更）；如有变形必须由 `KnowledgeStore` 现有路径承担。

## 10. 假设与失效影响

- **ASM-501**：用户已运行过 `garage init`（`.garage/` 目录与 platform.json 已存在）。**失效**：CLI 退 1 + stderr 提示 `No .garage/ directory found. Run 'garage init' first.`（与现有 `_status` / `_run` 行为一致）。
- **ASM-502**：`KnowledgeStore.update()` 在 v1.1 之后稳定遵守 `version+=1` 不变量。**失效**：F005 edit 路径会泄漏 v1.1 不变量缺陷；通过 NFR-501 零回归 + 显式 `version` 断言提前接住。
- **ASM-503**：用户能用命令行参数提供 `content`（短）或用 `--from-file` 提供（长）。**失效**：用户期望交互式编辑器（`$EDITOR`）→ 由 § 5 deferred backlog 接走，本 cycle 不消化。
- **ASM-504**：`ExperienceIndex.delete(record_id)` 已在 F003 内提供（`experience_index.py:139`），同时移除磁盘 JSON 与中央索引引用。**失效**：若 F003 的该方法在未来被改为不再级联清理索引，F005 `experience delete` 会留索引悬挂引用——通过 NFR-501 零回归 + FR-507b 索引摘除断言提前接住。

## 11. 开放问题

| 编号 | 问题 | 阻塞 / 非阻塞 | 当前判断 |
|------|------|---------------|---------|
| OQ-501 | 本 cycle 是否要把 `garage knowledge add` 同时加进 `garage memory review` 的 candidate 路径（让用户也能用一行命令直接跳过候选 → 写入正式知识库）？ | 非阻塞 | 否。F003 candidate-then-publish 是经过 spec/design 评审的核心 invariant；F005 = 旁路而不是合并。两者在 source_artifact 字段上可被冷读区分。 |
| OQ-502 | `experience` 删除是否会破坏 `RecommendationService` 索引一致性？ | 已答 | 不阻塞。`ExperienceIndex.delete(record_id)` 在 F003 已实现（见 `src/garage_os/knowledge/experience_index.py:139`），同时移除磁盘 JSON 与中央索引引用。CLI 直接调用该 API，不重新发明删除路径。 |
| OQ-503 | 是否要在 `add` 时校验 `--type` 对应的目录是否真的存在？ | 非阻塞 | 否。`KnowledgeStore.store()` 内部已通过 `ensure_dir()` 兜底（见 `knowledge_store.py:66`）。CLI 不重复校验。 |
| OQ-504 | `tags` 是否大小写敏感？ | 非阻塞 | 维持现状：`KnowledgeStore` 在搜索路径上做 `.lower()` 索引但 store 路径保留原大小写。CLI 透传，不做规范化。 |
| OQ-505 | `garage knowledge show` 是否要支持 JSON 输出？ | 非阻塞 | 不在本 cycle。作为 deferred 候选写入 § 5。 |
| OQ-506 | 应该把 `garage knowledge show` 写成 `garage knowledge get` 还是 `show`？ | 非阻塞 | 用 `show`，与 `garage memory review <bid>`（无 action 时也是 show 行为）保持术语一致；`get` 容易让人以为有 stdout-to-pipeline 的 JSON 行为。 |

## 12. 术语与定义

| 术语 | 定义 |
|------|------|
| **手工添加路径 (CLI authoring path)** | 用户通过 `garage knowledge add` / `experience add` 等 CLI 命令直接写入 `.garage/` 的入口；与 F003 候选 → publisher 路径并列、互不依赖 |
| **来源标记 (source marker)** | front matter `source_artifact` 字段或 `ExperienceRecord.artifacts[0]` 的取值；用于区分 CLI 手工路径产出物与 publisher 自动路径产出物 |
| **CRUD 闭环 (CRUD loop)** | 同一 `(type, id)` 可被 `add` → `show` → `edit` → `show` → `delete` → `show` 6 步全链路操作，每步退出码符合 § 3.2 场景定义 |
| **零回归 (zero regression)** | F003/F004 已通过的 414 个测试在 v1.2 上线后全部继续 passed |
