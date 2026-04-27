# F013-A: Skill Mining Push 信号 — 系统主动建议 "pattern → skill"

- **状态**: 草稿 r2 (回应 spec-review-F013-r1; 待 r2 hf-spec-review)
- **主题**: F003-F006 投入了完整的 memory 提取管道 (signals → candidates → review queue → KnowledgeStore), 但只有 **pull 端** (用户主动 `knowledge search` / `recall`). F013-A 加 **push 端**: 当系统在 N 次会话里看见同一类 problem_domain + tag 组合反复出现时, 主动建议 "这个模式可以变成 skill", 半自动产 SKILL.md 草稿, 嵌 hf-test-driven-dev 走完 promote 流程.
- **日期**: 2026-04-25
- **关联**:
  - vision-gap planning artifact `docs/planning/2026-04-25-post-f012-next-cycle-plan.md` § 3 (F013-A Path A 单一最优)
  - F003 — `memory` 模块 (CandidateStore + **MemoryExtractionOrchestrator** + 候选生命周期)
  - F004 — ExperienceIndex + ExperienceRecord (索引 + 检索)
  - F005 — `garage knowledge add` CLI (promote 的写出端)
  - F006 — knowledge graph + `garage recommend` (候选证据链关联)
  - F008 — `packs/<pack-id>/skills/<skill>/SKILL.md` 目录契约 (promote 的目标)
  - F011 — `hf-test-driven-dev` skill (promote 后 skill writing 入口) + KnowledgeType.STYLE (candidate 标签维度)
  - F012-D — anonymize 规则 (promote 前可复用脱敏)
  - manifesto 信念 B4 "人机共生" + Stage 3 "工匠" (重复模式自动识别并建议为 skill 模板)
  - growth-strategy.md § 1.3 触发信号 第 4 行 "系统能指出 pattern → skill" — 当前唯一未达成项
  - user-pact "你做主": 所有自动化都有开关, 关键决策由用户做
  - 调研锚点 (基于实际 main `65701af` 代码 + reviewer Cr-1/Cr-2/Cr-3 修正):
    - F003 candidate 模型: `src/garage_os/memory/candidate_store.py` `store_candidate(candidate: dict[str, Any])` + `list_candidates_by_status(status)`
    - F003 extraction trigger: `MemoryExtractionOrchestrator.extract_for_archived_session_id(session_id)` (in `src/garage_os/memory/extraction_orchestrator.py`)
    - F004 experience: `ExperienceRecord` 含字段 `record_id, task_type, skill_ids[], tech_stack[], domain, problem_domain, outcome, duration_seconds, complexity, session_id, artifacts[], key_patterns[], lessons_learned[], pitfalls[], recommendations[], source_evidence_anchors[]`; `ExperienceIndex.search(task_type=None, skill_ids=None, domain=None, key_patterns=None)` (`experience_index.py:77-84`)
    - F004 KnowledgeEntry 含字段 `id, type, topic, date, tags[], content, status, version, related_decisions[], related_tasks[], source_session, source_artifact, source_evidence_anchor, confirmation_ref, published_from_candidate, front_matter`; **无 `problem_domain` 顶层字段** (仅 `front_matter` dict 可承载)
    - F006 graph: `KnowledgeStore.list_entries()` 返回 `KnowledgeEntry`
    - F008 skill anatomy: `docs/principles/skill-anatomy.md` (核心 7 原则 + When to Use / 边界 / 目录 anatomy / 章节骨架 / 演化版本管理)
    - F011 hf-test-driven-dev: `packs/coding/skills/hf-test-driven-dev/SKILL.md`
    - garage CLI `run`: `cli.py:2070-2079` 仅接受位置参数 `skill_name`, **无 `--skill` flag**

## 1. 背景与问题陈述

F012 把 garage 的 **能力分发链路** 闭环 (install ↔ uninstall ↔ update ↔ publish + 脱敏 export); F010 把 **memory 飞轮** 闭环 (sync 推 ↔ ingest 拉). 但 garage 整个 vision 还有一个仍未达成的关键能力, 直接对应 `growth-strategy.md` 第 1.3 节 Stage 3 健康表现的第 4 行:

> **系统能指出 "这个模式可以变成 skill"** — ❌ 未实现

### 1.1 当前断点 (post-F012)

```
session ─┐
         ├→ archive_session ──→ MemoryExtractionOrchestrator ──→ candidates ──→ review queue
session ─┤    (F010 ingest)        (F003)                          (F003)         (F003)
         │                                                              │
session ─┘                                                              ↓
                                                          KnowledgeStore (F004) + ExperienceIndex (F004)
                                                                        │
                                                         ┌──────────────┼──────────────┐
                                                         ↓              ↓              ↓
                                              recall (F006)         search        sync (F010)
                                                                                       ↓
                                                                            host context surface
```

**现状**: 整条管道只有"用户主动拉"出口 (recall / search / sync 都是 pull); **缺"系统主动推"出口** — 系统对积累的 KnowledgeEntry + ExperienceRecord 没有任何"模式扫描"行为, 所以 33 个 skill 不会因为用户使用而长成 34 个.

### 1.2 真实摩擦量化

- 当前 garage 仓库自身 dogfood 中, KnowledgeEntry / ExperienceRecord 数量基线由 main `65701af` snapshot 决定 (`.garage/knowledge/`, `.garage/experience/`)
- F011/F012 cycle 中累计了 ~50 次 review verdict 写入 (test-review/code-review/traceability/regression/completion), 但 **没有一次** 触发 "这个模式 (例 'review verdict 5 段格式') 可以提到 skill"
- F008 + F011 + F012 三次 cycle 的 hf-test-driven-dev 反复迭代了 "实施 → review → 修正 → 再 review" 节奏, 但这个节奏没有从 candidate 提炼过 (用户全靠手动 commit pattern)

→ **F013-A 的核心承诺**: 当 ExperienceIndex / KnowledgeStore 里同一 (problem_domain, tag-bucket) 组合在 ≥ N 次 session 出现时, 系统在 `garage status` 显示 "💡 X 个候选模式可考虑提为 skill" + 提供 `garage skill suggest` 列表 + `garage skill promote` 半自动转换路径.

### 1.3 与 user-pact "你做主" 的边界

F013-A 不会:
- 自动 commit 任何 SKILL.md 到 packs/ (B5 user-pact 红线)
- 自动改 packs/<pack-id>/pack.json (skills[] 列表) 而不经用户确认
- 删除候选记录 (即便用户 reject, 也仅标 `status: rejected` 不物理删, 30 天后 audit decay)

F013-A 只会:
- 扫描 + 评分 + 显示候选 (read-only)
- 在用户显式 `--yes` / interactive 同意时, 把候选转成 SKILL.md 草稿 + 触发 hf-test-driven-dev 路径 (skill writing 仍由用户主导, garage 只生成骨架)

## 2. 目标与成功标准

### 2.1 范围

**A1. Pattern Detection** (FR-1301):
- 在既有 F003 `MemoryExtractionOrchestrator.extract_for_archived_session_id` 完成 (return) 后, 由 caller (例如 `SessionManager.archive_session` 链或 `garage session import` 流程) **可选** 调用新增的 `SkillMiningHook.run_after_extraction(session_id)`. 这是 callback 机制, 不修改 F003 既有 method 签名 (Im-2 修).
- Hook 内部扫描 `KnowledgeStore.list_entries()` 全部 + `ExperienceIndex.list_records()` 全部, 按 (problem_domain_key, tag-bucket) 维度聚类
- **`problem_domain_key` 来源 (Cr-3 USER-INPUT 决策)**:
  - ExperienceRecord: 直接读 `record.problem_domain` 顶层字段 (F004 既有, 无需扩 schema)
  - KnowledgeEntry: 优先读 `entry.front_matter.get("problem_domain")`; 若缺, fallback 到 `entry.topic` 第一个空格前的 token (例: topic "verdict-format design" → "verdict-format")
- **`tag-bucket` 规则**: ExperienceRecord 取 `record.key_patterns[:2]` (alpha-sorted); KnowledgeEntry 取 `entry.tags[:2]` (alpha-sorted); 两者归一化成 frozenset
- 发现某 (domain, tag-bucket) 组合在 ≥ N 次 session (按 `record.session_id` 或 `entry.source_session` 去重) 出现且当前未对应任何已有 SKILL.md 时, 生成 SkillSuggestion 写到 `.garage/skill-suggestions/proposed/<sg-id>.json`
- 阈值 N 默认 = 5, 通过 `~/.garage/skill-mining-config.json` 用户可调
- SkillSuggestion = `{id, suggested_name, suggested_description, problem_domain_key, tag_bucket[], evidence_entries[], evidence_records[], suggested_pack, score, status, created_at, expires_at}`
- status enum: `proposed | accepted | rejected | promoted | expired`
- "已对应 SKILL.md" 检测: 扫 `packs/*/skills/*/SKILL.md` 的 frontmatter `name` 与 `problem_domain_key` 做 substring match (粗略但安全; 漏判会重复建议, 误判过严会漏建议; 选漏判侧)

**A2. `garage skill suggest` CLI** (FR-1302):
- `garage skill suggest` (无参数): 列所有 status=proposed 的候选, 按 score 降序, 显示 id / name / N evidence / pack / score
- `garage skill suggest --id <suggestion-id>`: 显示某候选的详情 — 命中证据链 (knowledge entry id 列表 + experience record id 列表) + 估计的 SKILL.md 模板 preview
- `garage skill suggest --status all`: 列含 rejected/promoted/expired 状态的全部候选
- `garage skill suggest --status {proposed|promoted|rejected|expired|all}`: filter
- `garage skill suggest --rescan`: 触发 FR-1301 重新扫 (manual). **(Im-5 修)** `--rescan` **会重算聚类并写新 proposal** (相当于全量重跑 hook); 单独的 `--threshold N` 不重扫, 仅影响**本次 list 显示** (按 N 临时过滤已存在 proposal 的 evidence_count). 两 flag 同时给 = 用 N 重扫并写 proposal (含覆盖阈值的新 proposal, 可能比原默认多/少).
- `garage skill suggest --purge-expired`: 物理删 expired 记录 (interactive prompt unless `--yes`)

**A3. Skill Template Generator** (FR-1303):
- 输入: 一个 SkillSuggestion + 一个目标 pack-id (默认 `garage`)
- 输出: SKILL.md 草稿 **string** (in-memory). **(Cr-4 修)** generator 自身**不写文件**; promote 命令决定是否落到 packs/. preview 时 (FR-1302 `--id` 路径) 直接 print 到 stdout; 草稿不存 `.garage/skill-suggestions/.../draft` 也不存 system temp.
- 严格遵 `docs/principles/skill-anatomy.md` 核心 7 原则 + 章节骨架. 生成器必须产出的章节清单 (Im-4 修):

| 章节 | 来源 | 对应 skill-anatomy 原则 |
|---|---|---|
| frontmatter `name` | suggestion.suggested_name | 原则 1 (description 是分类器) |
| frontmatter `description` | suggestion.suggested_description, 必须含 "适用…" + "不适用…" 两段 | 原则 1 + 原则 6 (边界必须显式) |
| `## When to Use` | 从 evidence experience records 的 `task_type` + `key_patterns` 拼 | 章节骨架第 1 节 (When to Use) |
| `## Workflow` | 从 evidence experience records 的 `lessons_learned` + `key_patterns` 抽序列 | 章节骨架第 2 节 (Workflow) |
| `## Output Contract` | 从 evidence knowledge entries 的 `type` + `tags` 抽 | 章节骨架第 3 节 (Output Contract) |
| `## Red Flags` | placeholder + 列出 evidence 中 `pitfalls[]` 字段非空项 | 章节骨架第 4 节 (Red Flags) |
| `## Verification` | 从 `record.source_evidence_anchors[]` 中 (Im-3 修) 取可选字段 (如有 `commit_sha` / `test_count`); 缺省则 placeholder + 提示用户填 | 章节骨架第 5 节 (Verification) |

- 显式约束: description ≥ 50 字 (原则 1); 主文件 ≤ 300 行 (原则 2 主文件要短); 生成的草稿目标 100-150 行
- 若 evidence 中 `source_evidence_anchors` 缺 `commit_sha` / `test_count` 字段, Verification 段写 `<!-- TODO: 填 commit SHA / 测试数 (从 evidence anchor schema 取得后) -->` placeholder

**A4. `garage skill promote` 半自动流程** (FR-1304):
- `garage skill promote <suggestion-id>`: prompt 用户确认 — 显示 SKILL.md preview (来自 A3) + 候选 pack-id + 名字; 用户 `y` 后:
  1. 创建 `packs/<pack-id>/skills/<suggested-name>/SKILL.md` (使用 A3 生成的草稿)
  2. 把 SkillSuggestion status 改为 `promoted` + 记录 `promoted_to_path`
  3. **(Cr-2 修)** 提示用户 `Now run 'garage run <suggested-name>' to refine the draft` (不自动跳; 仅给路径). 若用户希望走完整 hf-test-driven-dev workflow, 手动 `garage run hf-test-driven-dev` 即可 (位置参数, 无 `--skill` flag).
  4. 不动 packs/<pack-id>/pack.json (skills[] 自动加是过度自动化; 用户用 hf-test-driven-dev 路径自己加; CON-1304 守门)
- `garage skill promote <suggestion-id> --reject`: status=rejected + reason prompt (≤ 500 字, RSK-1305 修)
- `--yes`: 跳过 confirmation prompt
- `--dry-run`: 显示将创建什么但不写
- `--target-pack <pack-id>`: 覆盖 default `garage` (例如 promote 到 packs/coding/)

**A5. Audit / Decay** (FR-1305):
- 每次 `garage status` 检查 `.garage/skill-suggestions/` 目录, 始终显示 **元数据行** "Skill mining: scanned X entries / Y records / Z proposed (last scan: <ts>)" (即便 Z=0 也显, RSK-1301 修); 仅当 `Z > 0` 时**额外**显示 "💡 Z proposed / M expired skill suggestions" 提示行 (Im-6 统一)
- proposed status 默认 30 天 expiry (`expires_at` 字段); 过期自动归 expired (不删, 用户可 `garage skill suggest --status expired` 看)
- rejected status 永久保留 (供未来 audit "为什么这个 reject"), 但不再扫到同 (domain, tag) 组合 — `_recompute_evidence` 跳过 rejected suggestion 已 cover 的 (domain, tag)
- 用户可显式 `garage skill suggest --purge-expired` 物理删 expired 记录

### 2.2 范围内变化

- 新模块 `src/garage_os/skill_mining/`:
  - `types.py`: `SkillSuggestion` dataclass + status enum + `SkillSuggestionStatus`
  - `pattern_detector.py`: 聚类 + 评分 + 写 suggestion (callback `SkillMiningHook.run_after_extraction(session_id)`)
  - `template_generator.py`: SKILL.md 草稿 in-memory 生成 (A3, 返回 string)
  - `suggestion_store.py`: `.garage/skill-suggestions/` 文件 CRUD (4 子目录: proposed/ accepted/ promoted/ rejected/ expired/)
  - `pipeline.py`: 端到端 (callback hook + audit/decay 实现)
- 新 CLI subcommand: `garage skill suggest` + `garage skill promote`
- `garage status` 加 skill-mining 段 (元数据行 + proposed 提示行)
- `~/.garage/skill-mining-config.json` 加 schema (threshold, exclude_domains, expiry_days)
- 新 .garage 目录: `.garage/skill-suggestions/{proposed/, accepted/, promoted/, rejected/, expired/}/<suggestion-id>.json`
- `RELEASE_NOTES.md` + `AGENTS.md` 同步

### 2.3 范围外 (Out of scope)

- 不做"自动 commit SKILL.md 到 packs/"(B5 user-pact 红线)
- 不做"自动 publish suggestion 到中央 registry"(F013-J 候选, 推到 F014+)
- 不做"experience export 反向 import"(F013-D 候选, 推到 F014+)
- 不做 NLP-based 模式相似度检测 (P1 启发式: 同 problem_domain_key + 至少 2 共享 tag = 一类; 复杂度留给 F014+)
- 不做"系统看着用户 review 你的 commit 习惯, 反向产 style skill"(KnowledgeType.STYLE 既有, 不重做)

## 3. 功能需求 (FR)

### FR-1301: Pattern Detection

| 字段 | 值 |
|---|---|
| **触发** | (a) caller (e.g. `SessionManager.archive_session` 链 / `garage session import` 流程) 在 `MemoryExtractionOrchestrator.extract_for_archived_session_id(session_id)` 返回后调用 `SkillMiningHook.run_after_extraction(session_id)`; (b) `garage skill suggest --rescan` 显式触发. CON-1301 修订: F003 既有 `MemoryExtractionOrchestrator` API + `extract_for_archived_session_id` 签名字节级不变; 新增 hook 是 sibling callback, 由 caller 自行接入 (Im-2 修) |
| **输入** | `KnowledgeStore.list_entries()` 全部 + `ExperienceIndex.list_records()` 全部 (read-only, INV-F13-3) |
| **聚类规则** | 按 (problem_domain_key, frozenset(tag-bucket)) 组合分组. ExperienceRecord 直接读 `record.problem_domain`; KnowledgeEntry 读 `entry.front_matter.get("problem_domain")` 或 fallback `entry.topic.split()[0]`. tag-bucket 取 `record.key_patterns[:2]` 或 `entry.tags[:2]` (alpha-sorted). 同组内成员 ≥ N (default 5, 按 session_id 去重) 即触发 SkillSuggestion |
| **去重** | 若已有 status ∈ {proposed, accepted, promoted, rejected} 的 suggestion 覆盖同组合, 不重复生成; 仅扫到 expired 时允许重生 |
| **评分** | `score = log10(N+1) + 0.3 × (unique_session_count) + 0.5 × (max(timestamp).days_since_epoch / 1000)` (近期权重 + session 多样性) |
| **输出** | `.garage/skill-suggestions/proposed/<id>.json` (id = `sg-<yyyymmdd>-<6 hex>`) |
| **BDD** | Given: 5 个 ExperienceRecord problem_domain="review-verdict" + key_patterns ⊃ {"verdict-format", "5-section"}, 各自 session_id 不同; When: trigger; Then: 生成 1 个 SkillSuggestion; And: 同组合再加 1 个 record, 不再生成新 suggestion (status=proposed 已存在) |
| **Edge** | 0 entry / 全 promoted-pack-skill 已 cover (检测 `packs/*/skills/*/SKILL.md` frontmatter `name` 与 problem_domain_key substring match) → 跳过; problem_domain_key 在 KnowledgeEntry 中既无 front_matter 也无 topic 第一 token → 跳过该 entry 不归类 |

### FR-1302: `garage skill suggest` CLI

| Sub-command | 行为 |
|---|---|
| `garage skill suggest` | 列 status=proposed 候选, 按 score desc, table 含 id / name / N-evidence / score / pack |
| `garage skill suggest --id <sg-id>` | 显示该候选完整 detail: name + description + evidence_entries + evidence_records + SKILL.md preview (A3 in-memory 生成, 不写文件) |
| `garage skill suggest --status {proposed,accepted,promoted,rejected,expired,all}` | filter 状态 |
| `garage skill suggest --rescan` | 触发 FR-1301 全量重新扫 (manual, **会写新 proposal**); 与 `--threshold N` 组合时按 N 重算 |
| `garage skill suggest --threshold N` | 临时阈值 (本次 list 显示用, 不重扫不写); 与 `--rescan` 组合则触发重扫且按 N 写新 proposal |
| `garage skill suggest --purge-expired` | 物理删 expired 记录 (interactive prompt unless `--yes`) |

| BDD | Given: 3 proposed + 1 promoted; When: `garage skill suggest`; Then: 仅显示 3 行; And: `--status all` 显示 4 行 |
| Edge | empty proposed → "No skill suggestions yet (threshold N=5; try --threshold 3 to lower)"; --id 不存在 → exit 1 + stderr |

### FR-1303: Skill Template Generator

| 输入 | suggestion-id + target-pack-id (default "garage") |
| 输出 | string (SKILL.md draft) — 不写文件 (A3 修, Cr-4 闭) |
| 模板章节 (skill-anatomy 章节骨架, Im-4 修) | (1) frontmatter name+description (2) `## When to Use` (3) `## Workflow` (4) `## Output Contract` (5) `## Red Flags` (6) `## Verification` (`source_evidence_anchors` 中字段缺则 placeholder, Im-3) |
| 显式约束 | description ≥ 50 字 (原则 1); 主文件 ≤ 300 行 (原则 2); 生成草稿 100-150 行 |

| BDD | Given: SkillSuggestion (5 evidence in problem_domain="review-verdict", tag_bucket={"verdict-format", "5-section"}, evidence_records 各含 source_evidence_anchors=[{"commit_sha": "abc1234", "test_count": 12}]); When: generate template; Then: SKILL.md 草稿含 frontmatter name="verdict-format" / description "适用…verdict 5 段格式…不适用…", `## When to Use` 段含 task_type 列表, `## Verification` 段含 `commit_sha=abc1234, test_count=12` (Im-3 BDD) |
| Edge | suggestion 无 evidence → 不应到这步 (FR-1301 ≥ N 守门); generator robust handle: 输出 minimal 模板 + warning. source_evidence_anchors 中无 commit_sha → Verification 段写 placeholder TODO |

### FR-1304: `garage skill promote` 半自动

| Flow | 1. Read suggestion + generate template (A3 in-memory) <li>2. Show preview + target_path; prompt `[y/N]` (除非 --yes) <li>3. y → write `packs/<target-pack>/skills/<suggested-name>/SKILL.md` + suggestion status=promoted <li>4. Echo `Created skill at packs/<target>/skills/<name>/SKILL.md. Run 'garage run <name>' to test, or 'garage run hf-test-driven-dev' to refine via the workflow.` (Cr-2 修: 无 `--skill` flag) <li>5. n → suggestion 状态不变 (仍 proposed); 用户可下次再 promote |
| `--reject` | status=rejected + 提示输入 reason (≤ 500 字, RSK-1305 修); reason 入 suggestion 文件 |
| `--yes` | 跳 prompt |
| `--dry-run` | 仅显示 preview + target_path, 不写 |
| `--target-pack <id>` | 覆盖 default "garage" |

| BDD | Given: proposed sg-001 (suggested_name="verdict-format"); When: `promote sg-001 --yes`; Then: `packs/garage/skills/verdict-format/SKILL.md` 创建 + suggestion status=promoted + stdout 含 "Created skill at packs/garage/skills/verdict-format/SKILL.md" 和 "Run 'garage run verdict-format' to test"; And: `packs/garage/pack.json` skills[] 不变 (CON-1304 守门; 用户自己 run hf-test-driven-dev 后加) |
| Edge | target pack 不存在 → exit 1 + "pack 'X' not installed"; 同名 skill 已存在于 packs/<target>/skills/ → prompt overwrite y/N (B5 user-pact 兜底, RSK-1304) |

### FR-1305: Audit / Decay

| Trigger | 每次 `garage status` 调用; 后台 daily expire scan (后续可加, F013-A 仅 manual) |
| Expiry | proposed → expired after `expires_at` (default created_at + 30 days) |
| Status 转换 | proposed → promoted / rejected / expired; rejected 永久; promoted 永久; expired 可被 purge |
| `garage status` 显示 | **始终显示** "Skill mining: scanned X entries / Y records / Z proposed (last scan: <ts>)" 元数据行 (Z=0 也显, RSK-1301 修); **额外** 当 Z > 0 时显示 "💡 Z proposed / M expired skill suggestions" 提示行 (Im-6 统一规则) |
| `garage skill suggest --purge-expired` | 物理删 expired 记录 (prompt unless --yes) |

| BDD | Given: 3 proposed (1 created 31 days ago); When: `garage status`; Then: 输出含 "Skill mining: scanned X entries / Y records / 3 proposed" 元数据行 (X/Y 实际数), 和 "💡 2 proposed / 1 expired skill suggestions" 提示行 |
| Edge | 用户改系统时钟 → expiry 仍按文件 mtime 兜底; 0 proposed 时仅显元数据行不显 💡 |

## 4. 不变量 (INV)

| ID | 描述 |
|---|---|
| **INV-F13-1** | F013-A 不写任何文件到 packs/ 之外的"用户拥有 path"; 唯一例外是 `.garage/skill-suggestions/` (F013-A 自己拥有). **Cr-4 修订: 不再使用 system temp; A3 generator 输出 string in-memory; promote 直接从 string 写到 packs/<target>/skills/<name>/SKILL.md** |
| **INV-F13-2** | promote 必须 opt-in: 默认 prompt; --yes 跳 prompt; --dry-run 不写 (B5 user-pact) |
| **INV-F13-3** | pattern_detector 是 read-only 在 KnowledgeStore + ExperienceIndex 上 (不写不删原数据; 只追加 SkillSuggestion 到 .garage/skill-suggestions/) |
| **INV-F13-4** | Skill template 必须遵 docs/principles/skill-anatomy.md 核心 7 原则 + 章节骨架 (frontmatter + When to Use + Workflow + Output Contract + Red Flags + Verification) |
| **INV-F13-5** | F003-F006 + F010 + F011 既有 API + 数据 schema 字节级不变 (新增 SkillSuggestion 是 sibling type; SkillMiningHook 是 sibling callback, F003 `MemoryExtractionOrchestrator` 既有方法签名不动) |

## 5. 约束 (CON)

| ID | 描述 |
|---|---|
| **CON-1301** | F003-F006 + F010 + F011 既有 API + 数据 schema 字节级不变. **Im-2 修订**: 允许在 caller 侧 (例如 `SessionManager.archive_session`) 增加对新 hook 的 optional 调用 (call site addition, 非 breaking 扩展); 不修改 `MemoryExtractionOrchestrator.extract_for_archived_session_id` 既有签名或返回值 |
| **CON-1302** | F013-A 不引入新 third-party 依赖 (`pyproject.toml + uv.lock` diff = 0); 全部用 stdlib (json / collections / pathlib / dataclasses / re) |
| **CON-1303** | 性能: 1000 个 KnowledgeEntry + 1000 个 ExperienceRecord 的 pattern_detector 扫一次 ≤ 5 秒 (本地 SSD); 否则 fallback 增量扫 (F014+) |
| **CON-1304** | promote 不动 packs/<pack-id>/pack.json (skills[] 列表); 用户用 hf-test-driven-dev 路径自己加. 这条 deliberate, 防止 F013-A 误碰 F011 既有 invariant |
| **CON-1305** | hf-test-driven-dev 路径在 promote echo 中提示, 但不自动 invoke (B5: 关键决策由用户做) |

## 6. 假设 (HYP)

| ID | 描述 |
|---|---|
| **HYP-1301** | 用户的 .garage/knowledge/ + .garage/experience/ 中确实有重复模式可挖. 若 N=5 阈值在用户首次跑时无候选, 用户会主动 `--threshold 3` 试. UX 给出明确提示 |
| **HYP-1302** | skill-anatomy 7 原则足以指导 SKILL.md 模板生成. 模板生成的 description / Workflow 段质量 ≥ 用户手写 baseline 的 60% (足以省 50% 起步时间) |
| **HYP-1303** | 用户接受"系统建议 + 半自动 promote"模式; 不会因为模板质量不完美而拒绝整个 F013-A |
| **HYP-1304** | promote 后用户会 follow up 跑 hf-test-driven-dev (即接受 echo 提示而非直接 commit). 若用户跳过, F013-A 不阻止 (但 README 应文档化) |
| **HYP-1305** | rejected suggestion 永久保留不会爆量 — 一年内 < 100 条 reject (基于个人使用频率估算) |

## 7. 风险 (RSK)

| ID | 描述 | 缓解 |
|---|---|---|
| **RSK-1301** | pattern_detector 对小 KnowledgeStore (< 10 entry) 永远不触发, 给用户"系统好像没工作"的错觉 | `garage status` **始终**显示 "Skill mining: scanned X / Y / Z" 元数据行, 即便 Z=0 也告诉用户管道在工作 (Im-6 统一; FR-1305 兜底) |
| **RSK-1302** | 模板生成的 description 不准 (只是 evidence 的浅层拼接), 用户嫌 promote 后还得大改 | A3 生成的草稿明确标 "AI-generated skeleton, refine via hf-test-driven-dev"; 不假装是 production-ready |
| **RSK-1303** | F011 既有 hf-test-driven-dev 入口期望"任务计划获批"前置, F013-A promote 后直接跳过去会断节点 | promote echo 不自动跳, 仅给路径 + 用户自己决定怎么走 (走 hf-workflow-router 重新评估 profile / 直接 hf-test-driven-dev); 文档化在 AGENTS.md |
| **RSK-1304** | 同名 skill 已存在 (用户手动写过同名) | promote 时 prompt overwrite y/N; --dry-run 显示 "would overwrite existing"; B5 user-pact 兜底 |
| **RSK-1305** | rejected reason 字段被滥用作"详细技术评论"导致文件膨胀 | reason 字段限制 ≤ 500 字符; CLI prompt 提示 "brief reason" |

## 8. 验收 BDD (Acceptance)

### 8.1 Happy Path: 5 evidence → suggest → promote (Cr-1/Cr-2/Cr-3 修)

```
Given:
  .garage/experience/records/ 含 5 个 ExperienceRecord, 全部 problem_domain="review-verdict",
    key_patterns ⊃ {"verdict-format", "5-section"}, session_id 各异
  .garage/knowledge/decisions/ 含 3 个 KnowledgeEntry, front_matter["problem_domain"]="review-verdict",
    tags ⊃ {"verdict-format", "5-section"}

When:
  caller (e.g. SessionManager) 在 MemoryExtractionOrchestrator.extract_for_archived_session_id 返回后
    调用 SkillMiningHook.run_after_extraction(session_id)
  garage status

Then:
  stdout 含元数据行 "Skill mining: scanned 3 entries / 5 records / 1 proposed (last scan: ...)"
  stdout 含 "💡 1 proposed / 0 expired skill suggestions"
  .garage/skill-suggestions/proposed/sg-*.json 出现 1 个

When:
  garage skill suggest

Then:
  stdout table 含 1 行: name "verdict-format" / N=8 evidence (5 record + 3 entry) / score >0.5

When:
  garage skill suggest --id sg-XXX

Then:
  stdout 含 evidence_entries (3 ID) + evidence_records (5 ID) + SKILL.md preview (含 6 章节)

When:
  garage skill promote sg-XXX --yes

Then:
  packs/garage/skills/verdict-format/SKILL.md 创建 (含 frontmatter + 6 章节)
  packs/garage/pack.json skills[] 不变 (CON-1304)
  .garage/skill-suggestions/promoted/sg-XXX.json 出现 (proposed/ 中删除)
  stdout 含 "Created skill at packs/garage/skills/verdict-format/SKILL.md.
            Run 'garage run verdict-format' to test, or
            'garage run hf-test-driven-dev' to refine via the workflow."
```

### 8.2 Reject path

```
Given: 1 proposed sg-001
When: garage skill promote sg-001 --reject
Then: prompt for reason (≤ 500 chars); user types "naming conflicts with existing pattern"
And: .garage/skill-suggestions/rejected/sg-001.json 出现 (含 reason)
And: 重新扫 (FR-1301) 不会在同 (problem_domain_key, tag_bucket) 上再生成新 suggestion
```

### 8.3 Audit / Decay

```
Given: 3 proposed (1 created 31 days ago)
When: garage status
Then: stdout 含 "Skill mining: scanned X entries / Y records / 3 proposed (last scan: ...)"
And: stdout 含 "💡 2 proposed / 1 expired skill suggestions"
And: expired/ 目录含 1 个 sg-*.json (从 proposed/ 移过去)

When: garage skill suggest --purge-expired --yes
Then: .garage/skill-suggestions/expired/ 清空
```

### 8.4 Dry-run + Custom target pack

```
Given: 1 proposed sg-002 (default target = garage)
When: garage skill promote sg-002 --target-pack coding --dry-run
Then: stdout 含 "DRY RUN: would create packs/coding/skills/<name>/SKILL.md"
And: packs/coding/skills/ 不变
And: suggestion status 仍 proposed
```

### 8.5 0 proposed 仍显元数据行 (RSK-1301 + Im-6 守门)

```
Given: 0 proposed (空 .garage/skill-suggestions/proposed/)
When: garage status
Then: stdout 仅含 "Skill mining: scanned X entries / Y records / 0 proposed (last scan: ...)"
And: 不显 "💡" 提示行
```

## 9. 实施分块预览 (草拟; 真正分块由 hf-design + hf-tasks 决定)

| 任务 | 描述 | 复用 |
|---|---|---|
| **T1** | `skill_mining/{types.py, suggestion_store.py}` (SkillSuggestion + CRUD; 5 子目录 proposed/accepted/promoted/rejected/expired) + 8 测试 | F005 KnowledgeStore CRUD pattern |
| **T2** | `skill_mining/pattern_detector.py` (FR-1301 聚类 + 评分 + 阈值 + problem_domain_key 双源 ExperienceRecord/KnowledgeEntry.front_matter) + 12 测试 | F003 candidate_store + F004 ExperienceIndex.list_records / KnowledgeStore.list_entries |
| **T3** | `skill_mining/template_generator.py` (FR-1303 SKILL.md in-memory 草稿, 6 章节, source_evidence_anchors fallback) + 10 测试 | docs/principles/skill-anatomy.md schema |
| **T4** | `skill_mining/pipeline.py` + `SkillMiningHook` callback (端到端 hook + audit/decay) + CLI `skill suggest` (含 --rescan / --threshold / --purge-expired 语义) + 12 测试 | F003 MemoryExtractionOrchestrator caller hook |
| **T5** | CLI `skill promote` (含 --reject / --yes / --dry-run / --target-pack) + `garage status` skill-mining 段 (元数据行 + 💡 提示行) + AGENTS.md / RELEASE_NOTES + manual smoke + 8 测试 | F011 hf-test-driven-dev echo + F012 RELEASE_NOTES pattern |

预估增量测试: ~50 个 (基线 main `65701af` snapshot 后 → +50; 实际基线由 tasks 阶段定). 无新依赖 (CON-1302).

## 10. 与 vision 的对照

| 维度 | F013-A 推动后 |
|---|---|
| **Stage 3 工匠** | ~65% → **~85%** (skill mining 信号闭环, growth-strategy 触发信号 4/4 全过) |
| **Stage 4 生态** | 40% (维持; F013-A 不直接动生态层) |
| **B4 人机共生** | 5/5 (维持; F013-A 是 B4 既有 5/5 的具象化) |
| **growth-strategy 健康表现 第 4 行** | ❌ → ✅ (vision 上 F013-A 唯一闭环条目) |

---

> **本文档是 spec r2** (回应 spec-review-F013-r1 的 4 critical + 6 important + 2 minor + 1 nit; 全部 13 finding 已闭合或落到代码 anchor). 待 r2 hf-spec-review.
