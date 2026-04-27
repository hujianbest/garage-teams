# F016: Memory Activation — 让 garage memory pipeline 在用户工作台上真正启动

- **状态**: 草稿 r2 (回应 spec-review-F016-r1; 5 critical + 4 important + 3 minor 全部闭合; 待 r2 hf-spec-review)
- **主题**: F003-F015 投入了完整 memory pipeline (signals → candidates → review queue → KnowledgeStore + ExperienceIndex → push 信号 F013-A/F014/F015), 但 `.garage/config/platform.json` 默认 `extraction_enabled: false`. 用户必须手动编辑 platform.json — 没文档明示. 后果: 14 cycle 后, 本仓库 dogfood `.garage/{knowledge,experience,sessions}/` 仍**全是 0**, F013-A skill mining hook / F014 recall / F015 STYLE alignment 在本仓库**永远不触发**. F016 加 4 件事: (a) `garage memory {enable, disable, status}` CLI 显式控制; (b) `garage memory ingest [--from-git-log] [--from-reviews] [--style-template]` 从既有数据回填 ExperienceRecord (Cr-3 r2: 删 `--from-sessions`, F010 既有 `garage session import` 已覆盖); (c) `garage init` 默认 prompt "Enable memory extraction? [Y/n]" (Cr-1 r2: 仅 interactive 路径, 不重载 `--yes`); (d) 模板化 STYLE entry 入口让 F015 compose 第一次有数据.
- **日期**: 2026-04-27
- **关联**:
  - vision-gap 答疑 (post-F015 + 用户两轮收敛): "聚焦 garage 在个人工作台上用起来; 不做 daily / Stage 4 生态"
  - F003 — `MemoryExtractionOrchestrator` + `load_memory_config` (extraction_enabled gate; F016 user-facing 控制层)
  - F004 — `ExperienceIndex.store / list_records` + `KnowledgeStore.list_entries(KnowledgeType.STYLE)` (F016 ingest 写出端)
  - F005 — `garage knowledge add` + `garage experience add` (F016 ingest 内部复用 store API, 不重复 CRUD)
  - F010 — `garage session import --from <host>` (F016 ingest 与 F010 sibling: F010 注 host conversation 历史, F016 注 git log + review verdict 历史 + STYLE 模板)
  - F011 — `KnowledgeType.STYLE` (F016 ingest 模板化入口)
  - F013-A / F014 / F015 — 三个 push 信号闭环, 都依赖 `.garage/{knowledge,experience}/` 有数据
  - manifesto B4 "人机共生" + Stage 1-3 全部 100%; user-pact (5) "你做主"
  - 调研锚点 (基于 F015 branch + main `f1c0bd7`):
    - F003 extraction gate: `src/garage_os/memory/extraction_orchestrator.py:13-20` `load_memory_config(storage)` + `is_extraction_enabled` (L110-112)
    - F003 platform.json default: `src/garage_os/cli.py:171-184` `DEFAULT_PLATFORM_CONFIG.memory = {extraction_enabled: False, recommendation_enabled: False}` (Mi-1 r2 行号修)
    - F009 既有 `_init` `--yes` flag (`cli.py::_resolve_init_hosts` L327-364): `--yes` 仅跳过 host 安装交互, 无 `--hosts` 时等价 `--hosts none`; F016 INV-F16-3 守门: `--yes` 既有 host 行为字节级不变, F016 不重载 `--yes` 改 memory state (Cr-1 r2 修)
    - F005 `_experience_add` (`cli.py:1761-1780`): 单 summary 放入 lessons_learned + artifacts=[cli:experience-add]; F016 ingest 复用 F004 store API 而非 F005 CLI handler (Im-2 r2 修)
    - F005 `_generate_experience_id` (`cli.py:1528-1547`): exp-yyyymmdd-xxxxxx 模式; F016 ingest 用此模式生成 record_id (Mi-2 r2)
    - F004 ExperienceIndex.store: `src/garage_os/knowledge/experience_index.py:34-58`
    - F004 KnowledgeStore.store: `src/garage_os/knowledge/knowledge_store.py` (F011 既有 STYLE 子目录 `knowledge/style/`)
    - F005 cli `_experience_add` / `_knowledge_add`: 用户级 add CLI 路径
    - F010 ingest: `src/garage_os/ingest/pipeline.py` (host conversation → garage session → archive → extract)
    - F013-A SkillMiningHook: 在 archive_session 完成后触发, 但 extraction_enabled=false 时 hook 无 candidate
    - 本仓库 dogfood 状态: `find .garage/{knowledge,experience,sessions}/ -type f | wc -l` = 0 (除 .gitkeep)

## 1. 背景与问题陈述

post-F015 vision-gap 显示, 5 信念 / 5 承诺 / Stage 1-3 全部 5/5 + 100%. 但本仓库**用户工作台维度的 dogfood 启动**有断点:

### 1.1 当前断点 (post-F015)

```
F003 extraction_enabled=false (platform.json default)
       ↓
F003 archive_session 时 SkillMiningHook + WorkflowRecallHook 调用, 但 extraction skipped
       ↓
ExperienceIndex / KnowledgeStore 永远 empty (除非用户手动 garage knowledge add / experience add)
       ↓
F013-A skill mining: 0 candidate (阈值 N=5 永远不达)
F014 recall workflow: 空 advisory (bucket size=0 < threshold 3)
F015 STYLE alignment: placeholder TODO (KnowledgeType.STYLE entries 0)
       ↓
用户感知: garage 安装了, 但跑 garage status / agent compose 永远 "No data" → 不知道哪一步出错
```

### 1.2 真实摩擦量化

- 14 cycle 来 (F001-F015), 本仓库 `.garage/knowledge/`, `.garage/experience/`, `.garage/sessions/` 全部空
  - `find .garage/knowledge -type f` → 0 文件 (除 .gitkeep)
  - `find .garage/experience -type f` → 0
  - `find .garage/sessions -type f` → 0
- F013-A push 信号在本仓库**从未触发过**一次 (有 hook, 有 trigger 路径, 但 extraction_enabled=false 拦在前面)
- F015 production agents (3 个) 全部手写, 因为 STYLE entries 0 时 compose 出的 agent.md "## Style Alignment" 全 placeholder
- 用户 (含本团队) 在 14 cycle 中**没真正用过自己的 memory 系统**

### 1.3 为什么不是 F016 之前 cycle 解决?

F003-F015 各自 cycle 的范围都是"加新功能", 没有专门的 cycle 解决"用户启动":
- F003 加了 extraction_enabled gate, 但默认 false 是当时的安全默认 (因 archive 触发 LLM 调用, 早期不应静默触发)
- F010 加了 sync + ingest, 但 ingest 是手动 (`garage session import --from claude --all`)
- F013-A/F014/F015 加了 push 信号, 但都假设上游有数据

→ **F016 的核心承诺**: 用户从"安装 garage"到"看到第一条 SkillSuggestion / WorkflowAdvisory / STYLE-aligned agent compose"的路径, 从"读完 5 份 docs + 编辑 platform.json + 手动 add 14 条 ExperienceRecord"缩短到 **3 个 CLI 命令**:

```bash
garage memory enable                          # 1. 显式 opt-in extraction
garage memory ingest --from-reviews           # 2. 历史回填 ExperienceRecord
garage memory ingest --style-template python  # 3. STYLE 模板化入口
```

### 1.4 与 user-pact "你做主" 的边界 (Cr-1 r2 修订)

F016 不会:
- 默认在 `garage init` 静默打开 extraction_enabled (manifesto + user-pact 红线)
- 重载 `garage init --yes` 的语义 — 既有 `--yes` 仅跳过 host 安装, F016 不让 `--yes` 改 memory state (CON-1604 + INV-F16-3 守门)
- 自动从 git log / review verdict 抽取 ExperienceRecord 不经用户同意
- 删除 / 修改既有 KnowledgeEntry / ExperienceRecord
- 注入 STYLE entries 到 user-scope 不经用户确认

F016 只会:
- 在 `garage init` interactive 路径 (TTY 且无 `--yes`) prompt "Enable memory extraction? [Y/n]" (默认 Y, 用户可拒绝)
- `garage init --yes` 跳过 prompt **保持既有 host 行为不变, 不开 memory** (与 F007 既有 `--yes`=CI 非交互兼容; 用户后续 `garage memory enable` 显式开)
- `garage init --no-memory` 显式 opt-out (与 prompt y 路径互补)
- `garage memory ingest` 是手动命令; 默认 `--dry-run`-friendly 显示 preview
- STYLE 模板是 well-known 模板 (per-language); 用户可改 / 删

## 2. 目标与成功标准

### 2.1 范围

**A. `garage memory {enable, disable, status}` CLI** (FR-1601):
- `garage memory enable` — 设 platform.json `memory.extraction_enabled: true`; echo 提示用户接下来怎么 ingest 数据
- `garage memory disable` — 设 `memory.extraction_enabled: false`; echo 提示已暂停 (但既有数据保留)
- `garage memory status` — 显示当前 memory state: extraction_enabled / N candidates / N entries / N records / last extraction ts
- 与 F011 既有 `garage memory review` 平级 sibling

**B. `garage memory ingest [...]` CLI** (FR-1602):
- `garage memory ingest --from-reviews [--reviews-dir docs/reviews/]` — 扫 review verdict markdown, 每个 verdict 生成一条 ExperienceRecord (task_type=review-verdict, problem_domain=feature_id 例 F012, skill_ids 从文件名 hf-* 推, lessons_learned 从 verdict body 'Recommendations' 段抽)
- `garage memory ingest --from-git-log [--git-log-dir .] [--limit N]` — 扫 git log (git log --oneline -<N>), 每条 commit 生成 ExperienceRecord (task_type=commit, problem_domain=由 commit message 'fXXX:' 前缀推, skill_ids 由 commit message 'hf-*' 关键词推, duration_seconds 由 commit timestamp 间隔推)
- `garage memory ingest --style-template <lang>` — 用 well-known 模板生成 KnowledgeType.STYLE entries (lang ∈ {python, typescript, markdown}; 每个模板含 5-10 条 STYLE entries)
- `--dry-run` flag — 仅 print 将生成的 records / entries, 不写
- `--yes` flag — 跳过 confirmation prompt

**C. `garage init` 改进** (FR-1603 — Cr-1 r2 修订: 不重载 `--yes`):
- `garage init` interactive 路径 (TTY + 无 `--yes` + 无 `--no-memory`): prompt "Enable memory extraction? Garage will auto-extract knowledge from your archived sessions. [Y/n]:"
- 用户输入 `y` (默认) / 空 → platform.json `memory.extraction_enabled: true`
- 用户输入 `n` → false
- **`garage init --yes` 路径 (Cr-1 r2): 跳过 memory prompt, 保持既有 host 安装 `--yes` 行为字节级不变, memory 默认 disabled** (与 F007 既有 `--yes` = CI 非交互不装 host 兼容; 用户后续显式 `garage memory enable` 开)
- **`garage init --no-memory`** (新 flag, 显式 opt-out): 即使 interactive 也不 prompt, 默认 disabled
- non-TTY without `--yes` / `--no-memory`: 默认 disabled (与既有 init non-TTY 行为一致)
- 与 F009 既有 init `--scope` / `--hosts` flag 兼容 (F016 不动 F009 既有 args; INV-F16-3 守门)

**D. 模板化 STYLE entries** (FR-1604):
- 加 `packs/garage/templates/style-templates/{python,typescript,markdown}.md` (3 个模板; 每个含 5-10 条 STYLE entries)
- `garage memory ingest --style-template <lang>` 调用此模板, 生成 KnowledgeType.STYLE entries 写到 `.garage/knowledge/style/`
- F015 compose 时 `## Style Alignment` 段第一次能拉到真实 STYLE topics

**E. `garage status` 集成** (FR-1605):
- 修改 `_status` 显式打印 extraction_enabled state ("Memory extraction: enabled" 或 "disabled — run `garage memory enable`")
- 用户首次看到 status 即知道 memory 是否启动

### 2.2 范围内变化

- 新模块 `src/garage_os/memory_activation/`:
  - `types.py`: `MemoryStatus` + `IngestSummary` dataclass
  - `ingest.py`: from-reviews / from-git-log / from-style-template 三个 ingest 路径
  - `templates.py`: 模板化 STYLE entries 加载
- 新 CLI subcommand 扩展: `garage memory {enable, disable, status, ingest}` (与既有 `memory review` 平级)
- 修改 `_init` 增加 prompt + `--no-memory` flag
- 修改 `_status` 增加 extraction_enabled 行
- 新增 `packs/garage/templates/style-templates/{python,typescript,markdown}.md`
- platform.json schema 不变 (CON-1601: F003 既有 schema 字节级)
- **Im-4 r2 注**: ingest 第一次写 STYLE 时, F011 既有 `KnowledgeStore.store` 自动 `ensure_dir(.garage/knowledge/style/)`; F016 不需改 cli.py `GARAGE_DIRS` (`cli.py:143-157`)

### 2.3 范围外 (Out of scope)

- 不做 daily / today / week / 时序 delta 视图 (用户两轮收敛)
- 不做 Pack 市场 / registry / cross-user (Stage 4 生态; 用户排除)
- 不做 Agent 运行时 bridge (F017 候选; 与 F016 独立)
- 不做 Personal style wizard 交互 (F018 候选)
- 不做 跨项目能力桥 (F019 候选)
- 不修改 F003-F015 既有 API + schema
- 不自动从 host conversation 历史 ingest (F010 ingest 既有, F016 不重复)
- 不在 init 时**默认隐式**打开 extraction (必须 prompt)

## 3. 功能需求 (FR)

### FR-1601: `garage memory {enable, disable, status}` CLI

| Sub-command | 行为 |
|---|---|
| `garage memory enable` | 读 platform.json, 设 `memory.extraction_enabled: true`, atomic write; echo "Memory extraction enabled. Run `garage memory ingest` to backfill historical data." |
| `garage memory disable` | 读 platform.json, 设 `memory.extraction_enabled: false`, atomic write; echo "Memory extraction disabled. Existing data preserved; will not be modified." |
| `garage memory status` | 读 platform.json + count entries / records / candidates; print 多行 status block: "Memory extraction: <enabled\|disabled> / KnowledgeEntry: N / ExperienceRecord: M / Candidate: K / Last extraction: <ts\|never>" — **Cr-5 r2: "Last extraction" 来自 `max(record.created_at for record in ExperienceIndex.list_records())`, 无 record 时 "never"** (轻量, 不加新文件 / 不依赖 orchestrator batch 内部状态) |

| BDD | Given: platform.json `extraction_enabled: false`; When: `garage memory enable`; Then: platform.json 字段变 true + stdout "Memory extraction enabled" |
| Edge | platform.json 缺失 / 损坏 → friendly error 提示用户 `garage init` |

### FR-1602: `garage memory ingest`

| Flag | 行为 |
|---|---|
| `--from-reviews [--reviews-dir <path>]` | 扫 `<path>/*.md` (默认 `docs/reviews/`); 每个 review verdict 生成一条 ExperienceRecord; 解析: task_type='review-verdict', skill_ids 从文件名 (`spec-review-f012-r1.md` → ['hf-spec-review']), problem_domain=feature_id (`f012` lowercase, Im-3 r2), lessons_learned 从 'Recommendations for r2' 段抽前 3 条, source_evidence_anchors 含原文件 path; record_id = `exp-<yyyymmdd>-<6 hex>` (复用 F005 `_generate_experience_id` 模式, Mi-2 r2) |
| `--from-git-log [--limit N]` | 跑 `git log --oneline -<N>` (默认 N=50); 每条 commit 生成一条 ExperienceRecord; 解析: task_type='commit', problem_domain 从 commit msg 'fXXX' 前缀 (lowercase, Im-3 r2 例 `f013`), skill_ids 从 'hf-*' 关键词扫, duration_seconds 默认 0; record_id 同 `exp-` 模式 |
| `--style-template <lang>` | lang ∈ {python, typescript, markdown}; 读 `packs/garage/templates/style-templates/<lang>.md`; 解析每行 `- prefix: content` 生成 KnowledgeType.STYLE entries (topic=prefix, content=full); 写到 `.garage/knowledge/style/` (F011 KnowledgeStore.store 首次自动 ensure_dir, Im-4 r2; 不需 F016 改 GARAGE_DIRS) |
| `--dry-run` | 仅 print preview, 不写 |
| `--yes` | 跳过 confirmation prompt |
| `--strict` (Cr-4 r2) | 默认 skip + log warning 损坏 / 解析失败 entries; --strict 改为 raise + exit 1 (与 F012 anonymize 既有 strict 模式同精神) |

| BDD | Given: `docs/reviews/spec-review-f012-r1.md` 存在 (Im-3 r2 lowercase); When: `garage memory ingest --from-reviews --yes`; Then: ExperienceIndex.list_records 含 1 条 record (task_type='review-verdict', problem_domain='f012', skill_ids=['hf-spec-review']) |
| BDD | Given: 50 commits 含 'f013(t1):'/'f014(t2):' 等 prefix; When: `garage memory ingest --from-git-log --yes`; Then: 50 条 ExperienceRecord (problem_domain ∈ {f013, f014, ...}) (Im-3 r2 全小写) |
| BDD | Given: `packs/garage/templates/style-templates/python.md` 含 7 行 style entries; When: `garage memory ingest --style-template python --yes`; Then: KnowledgeStore.list_entries(KnowledgeType.STYLE) 含 7 entries |
| Edge | --from-reviews 路径不存在 → exit 1 + stderr; --style-template 不支持的 lang → exit 1; --dry-run 显 preview 不写 |

### FR-1603: `garage init` prompt (Cr-1 r2 修订: 不重载 `--yes`)

| 路径 / 输入 | 行为 |
|---|---|
| Interactive (TTY, 无 `--yes`, 无 `--no-memory`), prompt y / Y / 空 | extraction_enabled=true |
| Interactive prompt n / N | extraction_enabled=false |
| `--yes` (无论 TTY/non-TTY) | **跳过 prompt; extraction_enabled=false (默认 disabled)**; 既有 host 安装行为字节级不变 (Cr-1 r2 + INV-F16-3 守门) |
| `--no-memory` (无论 TTY) | extraction_enabled=false (显式 opt-out; 与 prompt 路径互补) |
| non-TTY 无 `--yes` 无 `--no-memory` | extraction_enabled=false (与既有 non-TTY init 行为一致) |

| BDD | Given: 全新; When: stdin `y\n` + `garage init` interactive; Then: extraction_enabled=true |
| BDD | Given: 全新; When: stdin `n\n` + `garage init` interactive; Then: extraction_enabled=false |
| BDD | Given: 全新; When: `garage init --yes` (Cr-1 修订); Then: extraction_enabled=**false** (init 既有 `--yes` 行为不变, 仅跳 host 安装 prompt) |
| BDD | Given: 全新; When: `garage init --no-memory`; Then: extraction_enabled=false |
| BDD | Given: 全新 + non-TTY (无 stdin pipe); When: `garage init`; Then: extraction_enabled=false (default) |
| Edge | 用户在 prompt 时 Ctrl-C → 按既有 input() 行为 raise; F016 不专门处理 |

### FR-1604: 模板化 STYLE entries

`packs/garage/templates/style-templates/{python, typescript, markdown}.md` 三个文件; 每个 well-known 5-10 条 STYLE entries. 例 `python.md`:

```markdown
# Python Style Templates

Each entry below becomes a KnowledgeType.STYLE entry on `garage memory ingest --style-template python`.

- `prefer-functional-python`: Prefer functional patterns (map / filter / list comp) over class-based when state is not needed.
- `type-hints-required`: All public functions must have type hints (Python 3.11+).
- `f-string-over-percent`: Prefer f-strings over `%` or `.format()` for string interpolation.
- `pathlib-over-os-path`: Use `pathlib.Path` instead of `os.path` for filesystem operations.
- `dataclass-over-tuple`: Prefer `@dataclass` over `NamedTuple` for new structured types.
- `pytest-fixture-naming`: Pytest fixtures use lowercase names; test functions use `test_<intent>_<expected>` pattern.
- `no-mutable-default-args`: Never use mutable default arguments; use `None` + sentinel pattern.
```

| BDD | Given: 模板存在; When: `garage memory ingest --style-template python --yes`; Then: KnowledgeStore.list_entries(KnowledgeType.STYLE) 含 7 entries with topics matching `-` 行 prefix |

### FR-1605: `garage status` 集成 (Im-1 r2 修订)

`_status` 加 "Memory extraction" 行 + STYLE 计数纳入 total knowledge:

- **Im-1 r2 (a)**: Memory extraction 行**始终显**, 跨过既有 "No data" 早退路径 (与 F013-A skill mining / F014 workflow recall status segments 同 pattern; 保证用户首次跑 status 即知道 memory 状态)
- **Im-1 r2 (b)**: 既有 `_status` 知识计数仅含 `decisions / patterns / solutions` (`cli.py:390-394`); F016 加 STYLE 计数到 total knowledge (`storage.list_files("knowledge/style", "*.md")`)

| BDD | Given: extraction_enabled=false, 无 sessions/knowledge/experience; When: garage status; Then: stdout 仍含 "Memory extraction: disabled — run \`garage memory enable\` if you want auto-extraction" (跨过 No data 早退) |
| BDD | Given: extraction_enabled=true; When: garage status; Then: stdout 含 "Memory extraction: enabled" (无提示后缀) |
| BDD | Given: 7 STYLE entries, 0 decisions/patterns/solutions; When: garage status; Then: total knowledge count = 7 (含 STYLE) |

## 4. 不变量 (INV)

| ID | 描述 |
|---|---|
| **INV-F16-1** | F016 不修改 F003-F015 既有 API + schema 字节级 (新 MemoryStatus / IngestSummary 是 sibling type) |
| **INV-F16-2** | F016 不写文件到 packs/<id>/ 之外 (除新增 `packs/garage/templates/style-templates/`); ingest 写 `.garage/knowledge/` + `.garage/experience/` 通过既有 KnowledgeStore.store / ExperienceIndex.store API (不直接 writeText 到子目录) |
| **INV-F16-3** (Cr-1 r2 修订) | `garage init --yes` 既有 host 安装行为字节级不变; F016 不重载 `--yes` 改 memory state; F016 仅在 (a) interactive prompt 路径 + 默认 Y; (b) 显式 `garage memory enable` 这两条路径开 extraction |
| **INV-F16-4** | extraction_enabled 切换不影响既有 ExperienceRecord / KnowledgeEntry; disable 后既有数据保留, 再 enable 时 archive_session 重新 trigger extraction |
| **INV-F16-5** | F011 既有 KnowledgeType.STYLE 接口字节级 (新 ingest 路径用 KnowledgeStore.store, 不改 STYLE 类型定义) |

## 5. 约束 (CON)

| ID | 描述 |
|---|---|
| **CON-1601** | F003-F015 既有 API + schema 字节级 (CON-1601 + INV-F16-1 等价表述) |
| **CON-1602** | 零依赖变更 (`pyproject.toml + uv.lock` diff = 0); 全 stdlib (subprocess for git log; pathlib; json; re) |
| **CON-1603** | `garage memory ingest --from-reviews` 性能 ≤ 5s for 100 review verdicts; --from-git-log ≤ 5s for 1000 commits (CON-1303 同精神) |
| **CON-1604** | F009 既有 init `--scope` / `--hosts` / `--yes` flag 不动 (F016 仅加 `--no-memory`) |
| **CON-1605** | F015 既有 agent compose CLI 不动; F016 模板化 STYLE 给 F015 STYLE alignment 提供数据但不改 F015 任何代码 |

## 6. 假设 (HYP)

| ID | 描述 |
|---|---|
| **HYP-1601** | 用户接受 `garage init` 加 prompt (默认 Y, 30 字以内). 不接受用户可 `--yes` 跳 |
| **HYP-1602** | review verdict markdown 文件名 pattern 稳定 (`<type>-review-<feature>-<round>-<date>.md`), 解析 task_type / skill_ids / problem_domain 不出错 |
| **HYP-1603** | git log commit message pattern 稳定 (`fXXX(<part>): <description>`), 解析 problem_domain = fXXX |
| **HYP-1604** | python / typescript / markdown 三个 STYLE 模板覆盖用户 80% 场景; 用户后续可手动 `garage knowledge add --type style` 加 |
| **HYP-1605** (Cr-2 r2 修订) | F003 extraction 是**本地 signal-driven** 候选生成 (`MemoryExtractionOrchestrator._generate_candidates`, `extraction_orchestrator.py:194-280`), **不调 LLM**. F016 enable extraction 后, archive_session 触发本地 candidate 生成; 用户在 host (Claude Code / Cursor) 内的对话仍通过 F010 `garage session import` 显式 ingest (与 F003 默认行为一致); F016 不引入新的 LLM 调用 |

## 7. 风险 (RSK)

| ID | 描述 | 缓解 |
|---|---|---|
| **RSK-1601** | extraction_enabled 默认 true 在 host 已 active 时触发 LLM extraction → 隐性成本 / 隐私 | F016 仅设 platform.json flag, 不主动调 LLM; 实际 trigger 路径 (archive_session → orchestrator.extract) 仍按 F003 既有逻辑; user-pact (5) 'opt-in' 通过 prompt 兼容 |
| **RSK-1602** | --from-git-log 在 large repo (10k+ commits) 慢或卡 | CON-1603 1000 commit < 5s; --limit 默认 50; 用户可加 `--limit 100` 显式控制 |
| **RSK-1603** | review verdict 解析失败 (filename pattern 不匹配) → silent skip 还是 error? | 默认 skip + log warning; --strict flag 时改为 raise; 与 F012 既有 anonymize 模式一致 |
| **RSK-1604** | STYLE 模板写错语言导致用户产生不准 STYLE entries | 模板内容中性 (per-language well-known 实践); 每条 entry 标 prefix 让用户 review; --dry-run 显 preview |
| **RSK-1605** | --from-reviews 重复跑产生重复 ExperienceRecord | ingest 检测 source_evidence_anchors 含 review file path; 同 path 已存在跳过 (与 F003 publisher 既有 self-conflict pattern 同精神) |

## 8. 验收 BDD (Acceptance)

### 8.1 Happy path: enable + ingest reviews + ingest style + status (Mi-3 r2: N 个 verdict; Cr-1 r2: --yes 不开 memory)

```
Given: 全新 workspace; docs/reviews/ 含 N 个 review verdict (实际 N 依 repo); packs/garage/templates/style-templates/python.md 含 7 entries

When: garage init --yes
Then: platform.json memory.extraction_enabled = false (Cr-1 r2: --yes 不开 memory)
And: stdout 含 "Initialized Garage OS in /workspace/.garage"

When: garage memory enable
Then: platform.json memory.extraction_enabled = true

When: garage memory status
Then: stdout 含
  Memory extraction: enabled
  KnowledgeEntry: 0
  ExperienceRecord: 0
  Candidate: 0
  Last extraction: never

When: garage memory ingest --from-reviews --yes
Then: stdout "Ingested N ExperienceRecord from docs/reviews/"
And: ExperienceIndex.list_records returns N records (problem_domain ∈ {f011, f012, ..., f015} 全小写)

When: garage memory ingest --style-template python --yes
Then: stdout "Ingested 7 KnowledgeType.STYLE entries from python template"
And: KnowledgeStore.list_entries(knowledge_type=KnowledgeType.STYLE) returns 7 entries

When: garage status
Then: stdout 含
  Memory extraction: enabled
  KnowledgeEntry: 7 (含 STYLE; Im-1 r2)
  ExperienceRecord: N
  Last extraction: <ts of max created_at; Cr-5 r2>
```

### 8.2 Disabled state + opt-out path (Cr-1 r2: --yes 不开 memory)

```
Given: 全新 workspace
When: garage init --yes (Cr-1 r2: --yes 默认 disabled)
Then: platform.json memory.extraction_enabled = false (与 init --yes --no-memory 等价)

When: garage status
Then: stdout 含 "Memory extraction: disabled — run `garage memory enable` if you want auto-extraction" (Im-1 r2: 跨 No data 早退)

When: garage memory enable
Then: platform.json extraction_enabled = true

# Alternative path: explicit --no-memory
Given: 全新 workspace
When: garage init --no-memory (interactive 也跳 prompt)
Then: extraction_enabled = false
```

### 8.3 Dry-run + dedup (Mi-3 r2: N 个 verdict)

```
Given: N review verdicts already ingested (from 8.1)

When: garage memory ingest --from-reviews --dry-run
Then: stdout "Would ingest 0 ExperienceRecord from docs/reviews/ (N already exist)"
And: ExperienceIndex.list_records 仍 N

When: 添加 1 个新 review verdict, garage memory ingest --from-reviews --yes
Then: stdout "Ingested 1 new ExperienceRecord from docs/reviews/ (N already existed)"
And: ExperienceIndex 含 N+1 records (RSK-1605 dedup ✓)
```

### 8.4 git-log ingest (Im-3 r2: lowercase fXXX)

```
Given: git log 最近 50 commits 含 fXXX 前缀 (例 'f013(t1):', 'f014(t2):', 'f015(spec):' 全小写)
When: garage memory ingest --from-git-log --yes
Then: stdout "Ingested ~50 ExperienceRecord from git log"
And: ExperienceRecord problem_domain ∈ {f013, f014, f015}; skill_ids 从 commit msg 'hf-*' 抽
And: record_id 全 exp- 模式 (Mi-2 r2 复用 F005 _generate_experience_id)
```

### 8.5 F015 compose 后第一次有 STYLE alignment

```
Given: 7 STYLE entries (从 python template ingest); packs/garage/skills/hf-specify/SKILL.md 存在

When: garage agent compose new-agent --skills hf-specify --yes
Then: agent.md "## Style Alignment" 段第一次有真实数据 (包含前 6 个 STYLE entries 的 topic + id)
And: 不再是 placeholder TODO
```

## 9. 实施分块预览

| 任务 | 描述 | 测试增量 | 复用 |
|---|---|---|---|
| **T1** | `memory_activation/{__init__, types, templates}` (MemoryStatus + IngestSummary + style-template loader) + 4 packs/garage/templates/style-templates/*.md + 8 测试 | 8 | F011 KnowledgeType.STYLE; F005 knowledge_store.store |
| **T2** | `memory_activation/ingest.py` (from-reviews / from-git-log / from-style-template + dedup + dry-run + Cr-4 --strict) + 12 测试 | 12 | F004 store API (`ExperienceIndex.store` / `KnowledgeStore.store`) — Im-2 r2: 复用 store 而非 F005 CLI handler; subprocess `git log --oneline -<N>`; F005 `_generate_experience_id` 模式 (Mi-2 r2: exp- 不用 sg-) |
| **T3** | CLI `garage memory enable / disable / status / ingest` + `_init` prompt + `_status` 集成 + 10 测试 | 10 | F009 既有 init flags; F015 既有 status segments |
| **T4** | AGENTS / RELEASE_NOTES + manual smoke + 5 sentinel | 5 | F015 sentinel pattern |

预估增量测试: ~35 (基线 1103 → ~1138). 无新依赖.

## 10. 与 vision 的对照

| 维度 | F016 推动后 |
|---|---|
| **Stage 3 工匠** | ~100% (维持; 不动) |
| **growth-strategy.md § Stage 3 健康表现 第 2 项 "知识条目增长随使用自然"** | ⚠️ 之前 0 条 → ✅ 用户工作台启动后 ≥ 14 条 |
| **B4 人机共生** | 5/5 (维持; F016 是 B4 既有 5/5 的具象化 — 系统能在用户工作台真正启动而不是只在测试中工作) |
| **个人工作台 dogfood gap** | ⚠️ 14 cycle 来 0 数据 → ✅ F016 解决 |

## 11. 测试基线

F016 base on F015 branch (PR #39 not yet merged) — 实际基线由 tasks 阶段实施前 `uv run pytest tests/ -q --ignore=tests/sync/test_baseline_no_regression.py` 确认 (Mi-2 r2 模式).

---

> **本文档是 spec r2** (回应 spec-review-F016-r1 的 5 critical + 4 important + 3 minor; 全部 12 finding 已闭合).
>
> r2 关键修订:
> - **Cr-1** (USER-INPUT 选项 a): F016 不重载 `garage init --yes` — `--yes` 既有 host 安装行为字节级不变, memory 默认 disabled (与 F007 既有 `--yes`=CI 非交互兼容); enable 路径仅 (1) interactive prompt y; (2) `garage memory enable`
> - **Cr-2**: HYP-1605 改写为 "本地 signal-driven 候选生成, 不调 LLM" (与 `MemoryExtractionOrchestrator._generate_candidates:194-280` 实际行为一致)
> - **Cr-3**: 删 FR-1602 `--from-sessions` flag (F010 既有 `garage session import` 已覆盖)
> - **Cr-4**: 加 `--strict` flag 到 FR-1602 (默认 skip + log warning; --strict raise + exit 1)
> - **Cr-5**: "Last extraction" 来源 = `max(record.created_at for record in ExperienceIndex.list_records())` (轻量, 不加新文件)
> - **Im-1**: FR-1605 显式说 (a) Memory extraction 行跨 No data 早退路径; (b) STYLE 计数加入 total knowledge
> - **Im-2**: ingest "复用 F004 store API (`ExperienceIndex.store` / `KnowledgeStore.store`)" (不复用 F005 CLI handler 整段)
> - **Im-3**: problem_domain / fXXX 全 lowercase
> - **Im-4**: STYLE 子目录 lazy mkdir 由 F011 KnowledgeStore.store 自动处理 (F016 不改 GARAGE_DIRS)
> - **Mi-1**: 锚点行号 cli.py 171-184
> - **Mi-2**: ingest record_id 复用 F005 `exp-yyyymmdd-xxxxxx` 模式 (不引入 F013-A `sg-` 模式)
> - **Mi-3**: BDD 8.x 改 "given N 个文件" (实际数依 repo)
