# F006: Garage Recall & Knowledge Graph — 让用户主动召回知识、把孤立 entry 连成图

- 状态: 已批准（auto-mode approval；见 `docs/approvals/F006-spec-approval.md`）
- 主题: 给 `garage` CLI 增加 3 个新子命令：`garage recommend <query>`（主动召回）、`garage knowledge link --from --to`（维护知识图边）、`garage knowledge graph --id`（1 跳邻居视图）；让 `manifesto.md` 承诺的"记得你上个月的架构决策"在产品层从被动 push 升级为主动 pull，并把 `KnowledgeEntry.related_decisions` / `related_tasks` 这两个 F001 起就存在但从未被使用的 schema 字段，第一次接通到用户面。
- 日期: 2026-04-19
- 关联:
  - F001（Garage Agent 操作系统）— `KnowledgeEntry.related_decisions` / `related_tasks` 字段早期定义
  - F002（Garage Live）— CLI surface
  - F003（Garage Memory — 自动知识提取与经验推荐）— `RecommendationService` / `RecommendationContextBuilder` 已实现
  - F005（Garage Knowledge Authoring CLI）— CLI handler 模式 + `cli:` 命名空间约定
  - `docs/soul/manifesto.md`（"记得你上个月的架构决策、能调用你积累的 50 个 skills"）
  - `docs/soul/growth-strategy.md`（Stage 3 进入信号 "识别到 5+ 个可复用模式" — 模式从知识图聚类中浮现，本 cycle 铺图衬底）

## 1. 背景与问题陈述

F003 已经把 `RecommendationService` 做出来了，逻辑也跑通了：基于 `RecommendationContext`（含 `skill_name` / `domain` / `problem_domain` / `tags`）扫描 `KnowledgeStore.list_entries()`，对每条 entry 计算 score + match_reasons 返回排序结果。F005 又把"添加知识"的门槛从必须经 session 归档触发，修到了 `garage knowledge add ...` 一行。

但**对照 `docs/soul/manifesto.md` 的承诺**，还有两条核心愿景在产品层未兑现：

1. **"记得你上个月的架构决策"** —— 今天 `RecommendationService` 只在 `garage run <skill>` 流程里被**被动**触发：用户必须先想起来要执行某个 skill，系统才在 skill 执行前展示一次推荐摘要。**用户主动想问"我以前对 X 类问题怎么决策的"是没有入口的**。`garage knowledge search` 是关键词全文搜索，不是基于 context 的 ranked recall——返回所有命中而不是"最相关的"，且不带 `match_reasons`，不能解释"为什么是这条"。
2. **"知识图"维度从未接通** —— `KnowledgeEntry.related_decisions: List[str]` 与 `related_tasks: List[str]` 这两个字段在 F001 dataclass 定义时就存在，F003 / F004 / F005 一路下来**从未被任何代码路径写入过，也从未被读取过**。结果是：每条 entry 是一个孤立点。`growth-strategy.md` 把 Stage 3 "工匠"（自动 skill 生成）的进入信号定为 "识别到 5+ 个可复用模式"——但模式不会从孤立点里自己冒出来，需要图。今天没有图，未来 Stage 3 的模式检测就没有衬底。

愿景上下文：`docs/soul/manifesto.md` 第二段写"它知道你的编码风格、记得你上个月的架构决策、**能调用你积累的 50 个 skills**、知道怎么帮你写博客"。三个并列承诺里，"记得"对应 recall 主动入口，"积累"对应图增长。`growth-strategy.md` 同时写"使用 → 积累 → 提炼 → 增强 → 使用（更强）"——Stage 2 飞轮的"提炼"环节天然依赖 entry 之间的关联（哪条 decision 引出了哪条 pattern？哪个 solution 取代了哪个旧 solution？），没有图就没有可提炼物。

如果不在下一个 cycle 把"主动召回 + 图衬底"补齐，会出现以下真实问题：

1. **F005 把"添加"路径修通后，飞轮"使用 → 看到价值 → 继续添加"的反馈环不闭合**：用户敲完 `garage knowledge add` 后，下一次需要这条知识时只能走 `garage knowledge search` 关键词搜索，得不到 ranked + reasoned 的"系统替你回忆"体验。结果："添加"只是一次性动作，不形成飞轮。
2. **F003 已经做的 RecommendationService 投入回报率被锁死在 `garage run` 单一入口**：那是一条低频路径（`garage run` 需要 Claude Code 在线 + 用户主动触发 skill）。同样的 ranked 召回逻辑应该在更高频、纯本地、无外部依赖的入口（即 `garage recommend <query>`）上服务用户。
3. **Stage 3 启动条件之一"识别到 5+ 个可复用模式"无法靠未来某次 LLM 灵感闪现完成**——必须先有"哪几条 decision 经常被一起引用、哪条 solution 被多条 decision 提到"这种**图层信号**。F006 不直接做模式检测，但**把图衬底铺好**，让未来的 Stage 3 模式检测能用 1 跳邻居 / 入度 / 社区聚类等标准图算法跑起来。

## 2. 目标与成功标准

### 2.1 核心目标

让 `.garage/knowledge/` 与 `.garage/experience/` 在以下两个维度从 F005 终态升级到 F006 终态：

```
召回 (recall) → 用户敲一行命令就能 pull 排序后的相关 entry + match_reasons
图  (graph)   → 用户能维护 entry 之间的 related 边，能查询 1 跳邻居
```

### 2.2 成功标准

1. **主动召回可用且解释性强**：用户敲 `garage recommend "auth jwt"` → CLI 返回 top-N 个相关 entry（knowledge + experience），每条带 `score` + `match_reasons`（与 F003 `RecommendationService` 完全一致的解释性字段）。当 `.garage/` 内 0 条 entry 时返回明确的 "No matching knowledge or experience" 而不是抛错。
2. **知识图边可写**：用户敲 `garage knowledge link --from <id-A> --to <id-B>` → CLI 把 `id-B` 追加到 `id-A` 的 `KnowledgeEntry.related_decisions`（默认）或 `related_tasks`（`--kind related-task` 时），磁盘 markdown front matter 可见，version+=1 走 `KnowledgeStore.update()` 路径。
3. **知识图可读**：用户敲 `garage knowledge graph --id <id-A>` → CLI 打印 `id-A` 节点 + 其全部 1 跳邻居（出边来自 `related_decisions` / `related_tasks`，入边来自全库扫描"哪些 entry 把我列为 related"）。
4. **零回归**：F005 baseline 451 个测试在 v1.3 引入后**全部继续 passed**。
5. **F005 cli: 命名空间约定延伸到 link 路径**：`garage knowledge link` 触发的 `KnowledgeStore.update()` 必须把 entry 的 `source_artifact` 覆写为 `"cli:knowledge-link"`，与 `cli:knowledge-add` / `cli:knowledge-edit` 同命名空间，让审计层面"手工链接动作"与"手工编辑动作"可分。
6. **CLI help 自描述**：`garage --help` 列出 `recommend`；`garage knowledge --help` 列出 `link` / `graph`；每个新子命令的 `--help` 列出全部参数及其语义。
7. **不引入新依赖、不引入新 schema 字段、不改既有公开 API**：复用 `RecommendationService.recommend()` / `RecommendationContextBuilder.build()`（必要时新增**非破坏性**的 query-shaped builder 方法）+ `KnowledgeStore.update()` / `retrieve()` / `list_entries()` + `ExperienceIndex.list_records()`。

### 2.3 非目标

- **不**引入语义/向量相似度（embedding）。本 cycle 完全沿用 F003 启发式 ranking。
- **不**做 Stage 3 模式检测、聚类、社区识别。本 cycle 只铺图衬底，不在图上跑算法。
- **不**自动建图：所有边都由用户显式 `link` 命令维护；不引入"系统自动建议链接"功能。
- **不**支持双向边数据结构。`A.related_decisions = [B]` 不自动生成 `B.related_decisions = [A]`；`graph` 的"入边"通过全库扫描动态计算，不持久化反向索引。
- **不**支持 `unlink` / `delete edge` 操作（候选 deferred，§ 5）。
- **不**支持加权边、边类型超过 2 种（`related-decision` / `related-task`）。
- **不**改变 F003 `RecommendationService` 已有 ranking 算法或 score 权重。
- **不**改变 F005 candidate / publisher / `garage memory review` 任何行为。
- **不**支持 experience entry 之间的 link（`ExperienceRecord` schema 没有等价 related 字段；本 cycle 不增字段）。
- **不**支持知识图 ↔ experience 跨类型 link（同样 schema 限制）。
- **不**为 `garage recommend` 引入"会话内上下文增强"——本轮严格基于 query 字符串 + 可选 `--tag` / `--domain` 过滤器。
- **不**输出 GraphViz / Mermaid / JSON 图导出（候选 deferred，§ 5）。

## 3. 用户角色与关键场景

### 3.1 主要用户角色

- **Solo Creator（主动召回方）**：知道自己以前记过相关知识，但不记得具体 ID 或精确关键词，想"问问 Garage 我大概记得什么"。期望系统给出排序结果 + 可解释的命中理由，不期望第一条就一定对。
- **Solo Creator（图维护方）**：刚 add 完一条新 decision，意识到它是上个月某条 decision 的延续 / 替代 / 关联——希望用 1 行命令显式地把这条关系记下，而不是只在 content 正文里写"参见 decision-xxx"自然语言。
- **Pack 作者 / Agent 调用方**：未来的 Stage 3 自动化路径会调用 `RecommendationService.recommend()` 做模式聚类输入；F006 引入的 `query-shaped` context 是这类调用的契约入口。期望参数稳定、score / match_reasons 字段不变。
- **运行时审计读者**：在 `git log` / `git diff` 里看到 entry 的 `related_decisions` / `related_tasks` 字段被增量修改时，能从 `source_artifact: cli:knowledge-link` 一眼分辨"这是手工建图动作"。

### 3.2 关键场景

1. **主动召回（关键词驱动）**：
   ```bash
   garage recommend "auth jwt expiry"
   ```
   → CLI 把 query 拆为 tokens `["auth", "jwt", "expiry"]`，构造 query-shaped context（`tags=tokens, skill_name=tokens[0]` 或同等映射），调 `RecommendationService.recommend(context)`，把 results 里 score>0 的 top-N 打印为人类可读列表（每条含 `[TYPE] title`、`ID:`、`Score:`、`Match: tag:auth, skill-text:jwt`）。
2. **主动召回（带过滤）**：
   ```bash
   garage recommend "rate limiting" --tag api --domain platform --top 3
   ```
   → 同上，但 context 显式带 `domain="platform"` + `tags=["rate", "limiting", "api"]`，仅返回 top-3。
3. **零召回的明确兜底**：在空 `.garage/` 上 `garage recommend "anything"` → exit 0、stdout `No matching knowledge or experience for query: 'anything'`（不是抛错；不是 exit 1——等同于 `garage knowledge search` 的"无结果"语义）。
4. **写一条 link**：
   ```bash
   garage knowledge link --from decision-x --to decision-y
   ```
   → CLI 调 `KnowledgeStore.retrieve(decision, x)` → 把 `decision-y` 追加到 `entry.related_decisions`（去重）→ 设 `source_artifact="cli:knowledge-link"` → 调 `KnowledgeStore.update()` → version+=1 → stdout `Linked 'decision-x' -> 'decision-y' (related-decision)`。
5. **写一条 task-link**：
   ```bash
   garage knowledge link --from decision-x --to T005 --kind related-task
   ```
   → 把 `T005` 追加到 `entry.related_tasks`，stdout `Linked 'decision-x' -> 'T005' (related-task)`。
6. **link target 不需要存在**：T005 这种 task ID 是 Garage 之外的引用，CLI 不强制 `--to` 在 `.garage/knowledge/` 内存在；`--from` 必须存在。
7. **重复 link 是幂等的**：连续两次 `link --from X --to Y` 第二次不报错、不重复追加、stdout 表明"already linked"，version 仍递增（因为 `update()` 始终递增；可接受）。
8. **看 1 跳邻居**：
   ```bash
   garage knowledge graph --id decision-x
   ```
   → 打印 `decision-x` 节点（`[DECISION] topic` + `ID:`），下面分两段：`Outgoing edges:` 列出 `decision-x.related_decisions` + `related_tasks` 全部目标；`Incoming edges:` 全库扫描列出"哪些其他 entry 把 decision-x 列为 related_decision/related_task"。
9. **零 entry 的明确兜底**：`graph --id missing` → exit 1 + stderr `Knowledge entry 'missing' not found`（与 F005 `show` / `delete` 同模式）。
10. **零回归保护**：F003 `RecommendationService` 在 `garage run` 流程的行为完全不变；F003 / F004 / F005 全部 451 个测试继续 passed。

## 4. 当前轮范围与关键边界

### 4.1 包含

| 功能 | 描述 |
|------|------|
| `garage recommend <query>` | 顶级新子命令；query 拆 tokens → 构造 query-shaped context → 调 `RecommendationService.recommend()` 拿 knowledge 半边 + 调本 cycle 新增 CLI-internal `_recommend_experience()` 拿 experience 半边 → 合并按 score 降序 → 打印 top-N |
| `--tag` / `--domain` / `--top` | `recommend` 的可选过滤器；`--tag` 可重复，`--domain` 单值，`--top` 默认 10 |
| `garage knowledge link --from --to` | 二级新子命令；写 `related_decisions`（默认）边 |
| `--kind related-decision \| related-task` | `link` 的可选边类型；默认 `related-decision` |
| 重复 link 幂等 | 同一 `(from, to, kind)` 二次调用不重复追加，stdout 显式 "already linked" |
| `garage knowledge graph --id` | 二级新子命令；打印 1 跳邻居（出边来自 entry 字段，入边来自全库扫描） |
| 来源标记 `cli:knowledge-link` | `link` 路径写入 entry 时强制 `source_artifact = "cli:knowledge-link"`（与 F005 cli: 命名空间约定延伸） |
| Query → context 映射 | 新增 `RecommendationContextBuilder.build_from_query(query, tags, domain)` 方法（**non-breaking 新增**，不动既有 `build()`） |
| stdout / stderr 常量 | 与 F005 同模式：`RECOMMEND_NO_RESULTS_FMT` / `KNOWLEDGE_LINKED_FMT` / `KNOWLEDGE_LINK_ALREADY_FMT` / `KNOWLEDGE_GRAPH_NODE_FMT` / `ERR_LINK_FROM_NOT_FOUND_FMT` 等 |
| 文档同步 | `docs/guides/garage-os-user-guide.md` 增 "Active recall and knowledge graph" 段；`README.md` / `README.zh-CN.md` CLI 列表追加 3 个新子命令 |

### 4.2 不包含

- 任何 `KnowledgeEntry` / `ExperienceRecord` / `RecommendationService` schema 变更
- `unlink` / 删除边操作（候选 deferred，§ 5）
- 双向边自动镜像（`A.related=[B]` 不自动写 `B.related=[A]`）
- 多跳图遍历（`graph --depth 2` 等；本轮严格 1 跳）
- Experience entry 之间的 link / 跨类型 link（schema 限制）
- 加权边、边时间戳、边的 source_artifact（仅 entry 级别打 `cli:knowledge-link`）
- 自动模式检测 / 聚类 / 推荐链接（Stage 3 范畴）
- LLM / embedding / 向量相似度（明确不引入）
- GraphViz / Mermaid / JSON 图导出（候选 deferred）
- `garage recommend --format json`（候选 deferred）
- `garage recommend --since` / `--type` 等高级过滤（候选 deferred）
- `garage memory recommend` 子命令（不混进 memory review 流程；recommend 是顶级命令）

## 5. 范围外内容（deferred backlog）

显式不在本 cycle 内消化：

- **`garage knowledge unlink --from --to`**：删除已写入的边。延后理由：本轮先把"建图"接通；删边语义涉及"如果对方是双向/我也被引用"等问题，应在使用一段时间后看真实场景。
- **多跳图遍历**：`garage knowledge graph --id X --depth 2`。延后理由：单跳已能服务 99% 的"最近一笔关联"场景；多跳前应先决定渲染格式（树/图/Mermaid）。
- **Experience link**：`garage experience link`。延后理由：`ExperienceRecord` 没有 related 字段，做这件事必须先 schema 变更，超出本 cycle 范围。
- **跨类型 link**：knowledge ↔ experience 双向引用。同上原因。
- **图导出**：`garage knowledge graph --format mermaid|graphviz|json`。延后理由：先看真实图规模再决定渲染目标。
- **`garage recommend --format json`**：JSON 输出便于 Agent pipeline 消费。延后理由：人类可读优先；JSON pipe 真有需求时单独立项。
- **`garage recommend --include experience-only`**：只召回 experience。延后理由：本轮默认混合召回，如出现"experience 太多噪声"反馈再分。
- **embedding-based 相似度**：违反本 cycle 非目标。属于"Stage 3 范畴"。
- **自动建议链接**："你刚 add 了一条 decision，要不要 link 到 decision-old？"延后理由：自动化语义需要一定的图规模才有信号；先建图，再做自动化。

## 6. 功能需求

### FR-601 `garage recommend <query>` 的 knowledge 半边必须复用现有 RecommendationService

- **优先级**: Must
- **来源**: § 1 摩擦 1（被动 push → 主动 pull）；§ 2.1 核心目标；§ 3.2 场景 1；CON-605
- **需求陈述**: When 用户调用 `garage recommend <query>`（query 为非空字符串，可选 `--tag <t>` 可重复、`--domain <d>` 单值、`--top <N>` 整数默认 10），the system shall：
  1. 把 query 按空白拆为 tokens（保留原大小写）
  2. 构造 query-shaped context = `{skill_name: tokens[0] or "", domain: --domain, problem_domain: None, tags: tokens + (--tag values), session_topic: query, artifact_paths: [], repo_state: {}}`
  3. 实例化 `RecommendationService(KnowledgeStore, ExperienceIndex)` 并调 `service.recommend(context)` 拿到 **knowledge** 召回结果（`RecommendationService.recommend` 当前实现仅遍历 `KnowledgeStore`，与 §8 描述一致；本 FR 不修改该实现，与 CON-605 兼容）
  4. 与 FR-602 返回的 experience 召回结果合并 → 按 score 降序取 top-N
  5. stdout 打印每条 `[TYPE] title` / `ID: ...` / `Score: X.X` / `Match: <逗号分隔 match_reasons>` 块（experience 条目 type 显示为 `EXPERIENCE`），块间空行
  6. 退出码 0
- **验收标准**:
  - Given `.garage/` 已 init 且含 1 条 decision `(id=d1, topic="auth jwt", tags=["auth"])`，When `garage recommend "auth"`，Then stdout 含 `[DECISION] auth jwt`、`ID: d1`、`Score: ` 后跟非零数字、`Match: tag:auth`，exit 0
  - Given 同上但传 `--top 1` 且有 5 条命中，Then stdout 仅含 1 个 entry 块
  - Given 同上但传 `--tag api --tag rest`，Then context.tags 含 `api` 与 `rest`（除 query tokens 外）
  - Given 同上但传 `--domain platform`，Then context.domain == "platform"
  - Given query 含多个 tokens（"auth jwt expiry"），Then 每个 token 都进入 `context.tags`
  - Given 调用方未 init `.garage/`，Then exit 1 + stderr `ERR_NO_GARAGE`（与 F005 一致）

### FR-602 `garage recommend <query>` 的 experience 半边必须用 CLI-internal scorer 扫描 ExperienceIndex

- **优先级**: Must
- **来源**: § 1 摩擦 1（mixed recall 的 experience 维度）；§ 2.1 核心目标；CON-605（保护 RecommendationService 不变）
- **需求陈述**: 因 `RecommendationService.recommend()` 当前实现仅遍历 `KnowledgeStore`（见 `recommendation_service.py:69`），且 CON-605 禁止修改其算法以避免 `garage run` 路径回归，experience 半边召回必须由 `cli.py` 内新增**纯本地** helper `_recommend_experience(records, context)` 完成。该 helper：
  1. 接受 `ExperienceIndex.list_records()` 返回的全部记录与 query-shaped context
  2. 对每条 `ExperienceRecord` 计算 score：
     - `context.domain` 命中 `record.domain`（小写比较） → +0.8 + reason `"domain:<v>"`
     - `context.problem_domain` 命中 `record.problem_domain` → +0.8 + reason `"problem_domain:<v>"`
     - 任一 token (`context.tags` 元素之一) 命中 `record.task_type`（小写包含） → +0.6 + reason `"task_type:<v>"`
     - 任一 token 命中 `record.tech_stack` 任一元素（小写） → +0.6 + reason `"tech:<v>"`
     - 任一 token 命中 `record.key_patterns` 任一元素（小写） → +0.6 + reason `"pattern:<v>"`
     - 任一 token 在 `record.lessons_learned` 拼接文本中（小写包含） → +0.4 + reason `"lesson-text:<token>"`
  3. 仅返回 score>0 的条目，每条形状 = `{entry_id: record.record_id, entry_type: "experience", title: record.lessons_learned[0] if record.lessons_learned else record.task_type, score: ..., match_reasons: [...], source_session: record.session_id or None}`
  4. 与 FR-601 knowledge 结果合并到同一 list（FR-601 步骤 4）
- **验收标准**:
  - Given `.garage/` 已 init 且含 1 条 experience `(record_id=exp-1, task_type="spike", domain="platform", tech_stack=["sqlite"], key_patterns=["indexing"], lessons_learned=["试出了 SQLite 索引方案"])`，When `garage recommend "indexing" --domain platform`，Then stdout 含 `[EXPERIENCE]`、`ID: exp-1`、`Match: domain:platform, pattern:indexing` 类似行
  - Given 同上 + 1 条 knowledge entry 同样命中，When `garage recommend "indexing" --domain platform --top 5`，Then stdout 同时含 knowledge 与 experience 两条 entry block，按 score 降序排列
  - Given experience 全部 score=0，Then experience 半边贡献空 list，与 FR-603 联动给零结果文案
  - **不**修改 `recommendation_service.py` 任何代码（CON-605）
  - **不**改变 `RecommendationContextBuilder.build()` 既有签名（CON-602；新增 `build_from_query()` 是 non-breaking 增量，不动 build()）

### FR-603 `garage recommend` 必须在零结果时给出明确兜底文案

- **优先级**: Must
- **来源**: § 3.2 场景 3
- **需求陈述**: When FR-601 knowledge 半边 + FR-602 experience 半边合并后**结果列表为空**（即两边都返回空或全 score=0），the system shall stdout 输出 `RECOMMEND_NO_RESULTS_FMT.format(query=<原始 query>)`（"No matching knowledge or experience for query: '<query>'"），退出码 0。本 FR 是 FR-601/602 的零结果共同归并出口，与 FR-601 验收行为一致；不重复在 FR-601/602 的 happy path 验收里同时声明。
- **验收标准**:
  - Given 0 条 knowledge entry + 0 条 experience record，When `garage recommend "x"`，Then stdout == `No matching knowledge or experience for query: 'x'\n`（仅一行 + 换行）
  - Given 5 条 knowledge + 3 条 experience 但 query 完全不命中两边，Then 同上行为
  - **不**抛 SystemExit 非零、**不**写 stderr

### FR-604 `garage knowledge link` 必须把 to 追加到 from 的 related 边并走 update() 递增 version

- **优先级**: Must
- **来源**: § 1 摩擦 2（图未接通）；§ 3.2 场景 4 / 5
- **需求陈述**: When 用户调用 `garage knowledge link --from <from-id> --to <to-id>`（可选 `--kind related-decision|related-task` 默认 `related-decision`），the system shall：
  1. 在 3 个 `KnowledgeType` 目录下查找 `(_, from-id)` 唯一匹配（type 不需要用户传，CLI 自动嗅探；多匹配则报错——见 FR-605）
  2. 把 `to-id` 追加到 entry 对应字段（`related-decision` → `entry.related_decisions`；`related-task` → `entry.related_tasks`），去重
  3. 设 `entry.source_artifact = "cli:knowledge-link"`
  4. 调 `KnowledgeStore.update(entry)`（自动 version+=1）
  5. stdout `KNOWLEDGE_LINKED_FMT.format(from=from-id, to=to-id, kind=<related-decision|related-task>)`
  6. 退出码 0
- **验收标准**:
  - Given `(decision, A)` 存在 `version=1` `related_decisions=[]`，When `garage knowledge link --from A --to B`，Then 磁盘 `version=2` `related_decisions=['B']` `source_artifact="cli:knowledge-link"`，stdout 含 `Linked 'A' -> 'B' (related-decision)`
  - Given 同上 `(decision, A)` 已含 `related_decisions=[B]`，When 再次 `link --from A --to B`，Then 磁盘 `related_decisions` 仍为 `[B]`（去重），stdout 含 `KNOWLEDGE_LINK_ALREADY_FMT.format(from='A', to='B', kind='related-decision')` 即 "Already linked 'A' -> 'B' (related-decision)"，退出码 0；version 仍 +1（因 `update()` 始终递增；这是已知可接受行为，§ 11 OQ-602）
  - Given `--kind related-task --to T005`，Then 写入 `entry.related_tasks=['T005']` 而非 `related_decisions`
  - Given `--from missing`，Then exit 1 + stderr `ERR_LINK_FROM_NOT_FOUND_FMT.format(eid='missing')`
  - Given `--to` 指向 `.garage/knowledge/` 之外的 ID（如 `T005`、`exp-...` 或不存在的字符串），Then 不校验 `--to` 存在性；CLI 接受任何字符串作为 `--to`（设计 §10）

### FR-605 `garage knowledge link --from` 必须在多 type 匹配时显式报错

- **优先级**: Should
- **来源**: § 11 OQ-603；不污染 `--from` 唯一定位语义
- **需求陈述**: When 在 `decision/pattern/solution` 3 个目录下找到**超过 1 条** ID 等于 `--from <X>` 的 entry，the system shall exit 1 + stderr `ERR_LINK_FROM_AMBIGUOUS_FMT.format(eid='X', types=['decision','pattern'])` 列出所有命中的 type，磁盘无变化。用户可通过显式重命名其中之一的 ID 来消歧。
- **验收标准**:
  - Given `(decision, X)` + `(pattern, X)` 同时存在，When `garage knowledge link --from X --to Y`，Then exit 1 + stderr 含 `ERR_LINK_FROM_AMBIGUOUS_FMT` 文案 + 列出至少 `decision` 与 `pattern` 两个 type，磁盘无变化
  - Given 仅 `(decision, X)` 存在，则正常按 FR-604 happy path 执行

### FR-606 `garage knowledge graph --id` 必须打印节点 + 出边 + 入边

- **优先级**: Must
- **来源**: § 3.2 场景 8
- **需求陈述**: When 用户调用 `garage knowledge graph --id <id>`，the system shall：
  1. 在 3 个 `KnowledgeType` 目录下查找 `(_, id)`；不存在则 exit 1 + stderr `KNOWLEDGE_NOT_FOUND_FMT`（复用 F005 常量）
  2. 多匹配按 FR-605 同一规则报错
  3. 打印节点头：`[<TYPE>] <topic>` 一行 + `ID: <id>` 一行
  4. 打印 `Outgoing edges:` 段：列出 `entry.related_decisions` 每条为 `  -> <target> (related-decision)`，再列出 `entry.related_tasks` 每条为 `  -> <target> (related-task)`；空时打印 `  (none)`
  5. 打印 `Incoming edges:` 段：调 `KnowledgeStore.list_entries()`，扫描每条 `other.related_decisions` / `other.related_tasks` 是否含 `<id>`，命中则列为 `  <- <other.id> (related-decision|related-task)`；空时打印 `  (none)`
  6. 退出码 0
- **验收标准**:
  - Given `(decision, A)` `related_decisions=['B']`，`(decision, B)` `related_decisions=['C']`，`(pattern, C)` `related_decisions=[]`，When `graph --id B`，Then stdout 头部 `[DECISION] <topic of B>`、`Outgoing edges:` 段含 `-> C (related-decision)`、`Incoming edges:` 段含 `<- A (related-decision)`，exit 0
  - Given `(decision, isolated)` 无任何 in/out 边，When `graph --id isolated`，Then stdout 含 `Outgoing edges:` 后跟 `(none)` 与 `Incoming edges:` 后跟 `(none)`，exit 0
  - Given `--id missing`，Then exit 1 + stderr 含 `KNOWLEDGE_NOT_FOUND_FMT.format(eid='missing')`
  - Given `--id` 在多 type 命中（`(decision, X)` + `(pattern, X)`），Then exit 1 + stderr 含 `ERR_LINK_FROM_AMBIGUOUS_FMT`（同 FR-605 共用常量）

### FR-607 link 路径必须延伸 F005 cli: 命名空间约定

- **优先级**: Must
- **来源**: § 2.2 SC-5；F005 ADR-503 cli: 前缀命名空间
- **需求陈述**: `garage knowledge link` 写盘 entry 时必须设 `source_artifact = "cli:knowledge-link"`，与 F005 已有的 `cli:knowledge-add` / `cli:knowledge-edit` / `cli:experience-add` 同命名空间。审计层面 `grep "cli:knowledge-link" .garage/knowledge/` 应能精确筛选所有手工建图动作，与 publisher 路径或 `add`/`edit` 路径产物可区分。
- **验收标准**:
  - Given `(decision, A)` `source_artifact="cli:knowledge-add"`，When `garage knowledge link --from A --to B`，Then 磁盘 `source_artifact="cli:knowledge-link"`
  - Given publisher 路径写入的 `(decision, P)` `source_artifact="published_by:F003"`，When `link --from P --to X`，Then `source_artifact` 被覆为 `"cli:knowledge-link"`（同 F005 FR-509 edit 行为：CLI 动作改写 source_artifact，但**不**触动 `published_from_candidate` 等 publisher 元数据）
  - 模块常量 `CLI_SOURCE_KNOWLEDGE_LINK = "cli:knowledge-link"` 必须存在于 `cli.py` 顶层并被 `_knowledge_link` 引用

### FR-608 CLI help 必须可冷读发现新增子命令并保留 F005 既有子命令

- **优先级**: Should
- **来源**: § 2.2 SC-6；`design-principles.md` 原则 5 "约定可发现"；F005 FR-510
- **需求陈述**:
  - `garage --help` stdout 含 `recommend`（F006 新增）
  - `garage knowledge --help` stdout 含 `link` 与 `graph`（F006 新增），且**继续**含 `search` / `list` / `add` / `edit` / `show` / `delete` 这 6 个 F005 既有子命令（保护 NFR-601 零回归）
  - `garage recommend --help` stdout 含 `query`、`--tag`、`--domain`、`--top`
  - `garage knowledge link --help` stdout 含 `--from`、`--to`、`--kind`
  - `garage knowledge graph --help` stdout 含 `--id`
- **验收标准**: 上述 5 条断言每条对应 1 个 test func（cross-cutting test class）；`knowledge --help` 断言显式覆盖 6 个 F005 既有名 + 2 个 F006 新增名共 8 个

## 7. 非功能需求

### NFR-601 零回归保护

- **优先级**: Must
- **来源**: § 2.2 SC-4；F004 NFR-301 / F005 NFR-501 同模式
- **需求陈述**: F005 已通过的 451 个测试在 v1.3 引入后必须**全部继续 passed**；任何回归必须先回 `hf-specify` 或 `hf-increment`。
- **验收标准**: `pytest tests/ -q` ≥ 451 passed；F006 新增测试单独计数。

### NFR-602 默认零外部依赖

- **优先级**: Must
- **来源**: § 2.3 非目标；F005 NFR-502 同模式
- **需求陈述**: F006 引入的 CLI 路径只允许 stdlib + 现有 `garage_os.*` 模块；不引入新 third-party 依赖。
- **验收标准**: `pyproject.toml` 在本 F006 cycle 不新增 runtime dependency；本 cycle 完成时 `git diff main..HEAD -- pyproject.toml`（HEAD = F006 终态 commit）为空 diff。

### NFR-603 召回耗时上限

- **优先级**: Should
- **来源**: 用户可感知性
- **需求陈述**: `garage recommend <query>` 在已 init 仓库 + ≤100 条 entry 下，从 process start 到 exit 总耗时 < 1.5s。理由：`RecommendationService.recommend` 当前是 O(N) 全库扫描；100 条 entry 的常数项已远低于 1.5s。`graph` 命令同上限（也是 O(N) 入边扫描）。
- **验收标准**: 1 个 wall-clock smoke 断言（`time.monotonic()` 包一次 recommend 调用）。

### NFR-604 错误输出语义化

- **优先级**: Must
- **来源**: F005 NFR-504 同模式
- **需求陈述**: 所有 success / failure stdout / stderr 文案必须由 `cli.py` 模块顶层常量产出（`RECOMMEND_*` / `KNOWLEDGE_LINKED*` / `KNOWLEDGE_GRAPH_*` / `ERR_LINK_*`）；不允许内联 f-string 散写。
- **验收标准**: 测试用 `assert FMT.format(...) in stdout` 风格断言；`grep "Linked '" src/garage_os/cli.py` 仅命中常量定义。

### NFR-605 文档同步

- **优先级**: Should
- **来源**: F005 NFR-505 同模式
- **需求陈述**: `docs/guides/garage-os-user-guide.md` 必须新增 "Active recall and knowledge graph" 段，覆盖 3 个新子命令的最小可执行示例；`README.md` / `README.zh-CN.md` 在 CLI 命令列表追加 3 个新子命令名。
- **验收标准**: 新增 grep 断言能找到 `garage recommend`、`garage knowledge link`、`garage knowledge graph` 三个字符串。

## 8. 外部接口与依赖

- **依赖既有模块**：`garage_os.cli`（F005 handler 模式）、`garage_os.memory.recommendation_service.{RecommendationService, RecommendationContextBuilder}`、`garage_os.knowledge.{KnowledgeStore, ExperienceIndex}`、`garage_os.types.{KnowledgeEntry, KnowledgeType}`、`garage_os.storage.FileStorage`。
- **不引入新 third-party 依赖**（NFR-602）。
- **不依赖** `ClaudeCodeAdapter` / `SessionManager` / `MemoryExtractionOrchestrator` / `KnowledgePublisher`（与 F005 一致）。
- **`recommendation_enabled` flag 不影响 `garage recommend`**：该 flag 只控制 `garage run` 的被动推荐；`garage recommend` 是用户主动 pull，**始终启用**。理由：用户主动调用即视为主动同意，再加 flag 是反模式（同 F005 `garage knowledge add` 不设 flag）。

## 9. 约束与兼容性要求

- **CON-601**：CLI 入口仍是 `garage` 顶级命令；新增 `recommend` 是顶级、`link` / `graph` 挂在现有 `knowledge` 父命令下，符合 F005 CON-501 "复用 / 不增顶级命令" 精神（此处 `recommend` **是新顶级**，因为它跨 knowledge + experience 两个域，不适合挂任一子树下；这是与 F005 CON-501 的有意义偏离，design ADR 中显式说明）。
- **CON-602**：`KnowledgeStore` / `ExperienceIndex` / `RecommendationService` 公开 API 不可变更；本 cycle 仅在 CLI 层调用其现有方法，且对 `RecommendationContextBuilder` 仅做**non-breaking 增量扩展**（新增 `build_from_query()` 方法，不动 `build()`）。
- **CON-603**：F005 v1.2 不变量保持：`link` 走的 `KnowledgeStore.update()` 必须仍然 `version+=1`；CLI 不可绕开 store/update 直接写文件。
- **CON-604**：`source_artifact` 取值 `"cli:knowledge-link"` 不与 publisher 路径已用值冲突（与 F005 CON-504 同 cli: 命名空间约定）。
- **CON-605**：不修改 `RecommendationService.recommend` 的 ranking 算法、score 权重、match_reasons 文案，避免 `garage run` 路径行为变化。
- **CON-606**：`recommend` 不写入 `.garage/`（pure read-only command）；`graph` 同样 read-only；只有 `link` 是写命令。

## 10. 假设与失效影响

- **ASM-601**：用户已运行过 `garage init`。**失效**：CLI 退 1 + `ERR_NO_GARAGE`。
- **ASM-602**：用户使用 `garage knowledge add` / candidate publisher 写入的 ID 在 3 个 `KnowledgeType` 目录中**全局唯一**（即同名 ID 不会跨 type 同时存在）。F005 ID 生成器 `<type-prefix>-<YYYYMMDD>-<6 hex>` 天然带 type 前缀避免碰撞，但用户可显式 `--id custom` 跨 type 重名。**失效**：FR-605 通过 `ERR_LINK_FROM_AMBIGUOUS_FMT` 显式拒绝；用户必须重命名其中一个。
- **ASM-603**：`KnowledgeEntry.related_decisions` / `related_tasks` 在所有现有 entry 上都是 `List[str]`（默认空 list；F001 dataclass 默认 `field(default_factory=list)`）。**失效**：若历史磁盘 entry 这两字段为 `None`（理论上 `_front_matter_to_entry` 已用 `fm.get(...)` 默认 `[]` 兜底，见 `knowledge_store.py` `_front_matter_to_entry` 中 `related_decisions=fm.get("related_decisions", [])` 与 `related_tasks=fm.get("related_tasks", [])` 两行），CLI 仍能安全 append；本 cycle 不专门测试这条边界但相信兜底。
- **ASM-604**：`RecommendationService.recommend(context)` 在 `context.skill_name` / `context.domain` / `context.problem_domain` 全为空字符串、仅有 `tags` 时也能正常工作并基于 tag 命中给 score。验证：源码 `recommendation_service.py:64-95` 逻辑允许 `skill_name=""`，仅基于 `tags` / `domain` 也能产生命中。**失效**：若实测 query-only path 始终返回空，则需要在 `_recommend()` handler 内 fallback 到 `KnowledgeStore.search(query=query)` 路径——但本 cycle 不预先实现，等 design / build 阶段实测决定。
- **ASM-605**：`RecommendationService.recommend()` 返回的 score 在小数据集（≤100 条 entry）下 1.5s 内可计算完成。**失效**：NFR-603 wall-clock smoke 测试会立刻发现并触发 design 修订。

## 11. 开放问题

| 编号 | 问题 | 阻塞 / 非阻塞 | 当前判断 |
|------|------|---------------|---------|
| OQ-601 | `garage recommend` 是否要支持 `--include knowledge-only|experience-only`？ | 非阻塞 | 否。本 cycle 默认混合召回；过滤候选 deferred（§ 5）。 |
| OQ-602 | `link` 重复调用时 `version` 仍 +1 是否合理？ | 非阻塞 | 是。`KnowledgeStore.update()` 始终 `version+=1` 是 F004 v1.1 不变量。如果 `link` 想"幂等无 version 变化"，需要绕开 update 直写文件——这违反 CON-603。代价是 git 历史会出现"无实质 diff 的 version bump"——可接受。 |
| OQ-603 | `link --from` 在多 type 命中时报错而非自动选 type 优先级，会不会让用户困惑？ | 非阻塞 | 优先显式拒绝（FR-605）。理由：自动选优先级是隐式行为，违反原则 5 "约定可发现"；显式报错让用户立刻知道问题。如果未来出现高频投诉，可加 `--type` 参数让用户消歧。 |
| OQ-604 | `graph` 的入边扫描是 O(N) 全库扫描，N 大时是否性能问题？ | 非阻塞 | 否。N=100 时 < 1.5s，远低于 NFR-603 阈值。如果未来 N>1000，可在 KnowledgeStore 加反向索引（属 design 层独立立项）。 |
| OQ-605 | `garage recommend` 是否要在 zero-result 时给 hint（"试试 `garage knowledge add`"）？ | 非阻塞 | 否。简短 `RECOMMEND_NO_RESULTS_FMT` 一行就好；hint 文案是 productization，不进规格。 |
| OQ-606 | `--to` 是否要校验"形如 ID 的格式"？ | 非阻塞 | 否。`--to` 接受任意字符串（FR-604 验收）。理由：`related_tasks` 经常引用 Garage 之外的 task ID（T005 这类），强校验会反过来阻塞使用。 |
| OQ-607 | `recommend` 是否输出 source_session？| 非阻塞 | 是。`RecommendationService` 已经在每条 result 里返回 `source_session`，CLI 在 `Match:` 行后增 `Source: <session>`（仅当非空），与 stdout 模板一致。 |

## 12. 术语与定义

| 术语 | 定义 |
|------|------|
| **主动召回 (active recall)** | 用户通过 `garage recommend <query>` 主动 pull 推荐结果，与 F003 在 `garage run` 内被动 push 推荐相对 |
| **知识图边 (knowledge edge)** | `KnowledgeEntry.related_decisions` / `related_tasks` 字段中的 ID 字符串，表示从 entry A 到 ID B 的有向引用 |
| **出边 (outgoing edge)** | 节点 A 的 `related_decisions` / `related_tasks` 字段直接列出的目标 |
| **入边 (incoming edge)** | 全库扫描发现的"哪些其他 entry 把节点 A 列为 related" |
| **1 跳邻居 (1-hop neighborhood)** | 节点 A + 其全部出边目标 + 全部入边来源；不递归 |
| **query-shaped context** | 由 `garage recommend` 命令行 query 构造的 `RecommendationContext`，与 `garage run` 构造的 skill-shaped context 形状一致但 token 含义不同（query tokens 落到 tags） |
| **link 路径** | 通过 `garage knowledge link` 写入 entry 的代码路径，`source_artifact = "cli:knowledge-link"` |
| **图衬底** | 知识图的 minimum viable 数据结构（节点 + 边），为未来 Stage 3 模式检测/聚类算法提供输入 |
