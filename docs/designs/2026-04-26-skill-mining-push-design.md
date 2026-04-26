# F013-A Design — Skill Mining Push (技术设计)

- **状态**: 草稿 r1 (待 hf-design-review)
- **关联 spec**: `docs/features/F013-skill-mining-push.md` r2 (commit `8bcb8dc`, APPROVED 2026-04-26)
- **关联 planning**: `docs/planning/2026-04-25-post-f012-next-cycle-plan.md` § 3 Path A
- **基线**: main `65701af` (930 passed, 33 SKILL.md, 3 production agents)
- **日期**: 2026-04-26

## 0. 设计概览

实现 F013-A spec 5 部分 (A1-A5) 的端到端技术方案. 本设计文档遵循 F011/F012 同等粒度: ADR (Architectural Decision Records) + INV (Invariants) + 任务分块 (sub-commit 划分).

未显式标注的 ADR 默认 `Status: Accepted r1`.

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                  Existing F003-F006 + F010              │
│  CandidateStore   KnowledgeStore   ExperienceIndex      │
│  MemoryExtractionOrchestrator     SessionManager        │
└─────────────────────────────────────────────────────────┘
                            │ (read-only)
                            ↓
┌─────────────────────────────────────────────────────────┐
│              NEW: src/garage_os/skill_mining/           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  types.py: SkillSuggestion + Status enum        │    │
│  │  suggestion_store.py: 5 status 子目录 CRUD      │    │
│  │  pattern_detector.py: 聚类 + 评分 + 写 proposal │    │
│  │  template_generator.py: SKILL.md in-memory string│    │
│  │  pipeline.py: SkillMiningHook + audit/decay     │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            │ (write)
                            ↓
┌─────────────────────────────────────────────────────────┐
│  .garage/skill-suggestions/                             │
│    proposed/   accepted/   promoted/                    │
│    rejected/   expired/                                 │
└─────────────────────────────────────────────────────────┘
                            │ (CLI surface)
                            ↓
┌─────────────────────────────────────────────────────────┐
│  garage skill suggest    garage skill promote           │
│  garage status (skill mining 段)                        │
└─────────────────────────────────────────────────────────┘
```

模块依赖:
```
types  ←  suggestion_store  ←  pattern_detector  ←  pipeline
                              ←  template_generator  ←  promote handler
```

新模块路径: `src/garage_os/skill_mining/{types.py, suggestion_store.py, pattern_detector.py, template_generator.py, pipeline.py}`

CLI 改动: `src/garage_os/cli.py` 加 `skill` subparser (`suggest` + `promote`); `_status` 加 skill mining 段调用.

## 2. ADR-D13-1 — 模块边界 (skill_mining 顶级包 vs knowledge/ 子包)

### 选项

- A. `src/garage_os/knowledge/skill_mining/` (作为 knowledge 子模块)
- B. `src/garage_os/memory/skill_mining/` (作为 memory 子模块)
- C. `src/garage_os/skill_mining/` (顶级包, 与 knowledge / memory / adapter 平级)

### 决策: C — 顶级包

**理由**:
- F013-A 跨 KnowledgeStore + ExperienceIndex 两源 (knowledge + memory), 不属于任一子包
- 写出端是 `packs/<pack-id>/skills/` (pack 子系统), 也不属于 knowledge / memory
- 与 F012 `knowledge/exporter.py` (单源 read knowledge) 不同, 后者天然在 knowledge/ 包内
- F010 `sync/` 也是顶级包, 因为跨 knowledge + experience 两源 → 同 pattern

### 影响

- 新增 `src/garage_os/skill_mining/__init__.py` + 5 个模块文件
- `tests/skill_mining/` 镜像目录, 与 `tests/knowledge/` / `tests/memory/` 同级

## 3. ADR-D13-2 — SkillSuggestion 持久化 (5 状态子目录 vs 单文件 + status 字段)

### 选项

- A. 5 子目录 `proposed/ accepted/ promoted/ rejected/ expired/`, 文件名 = `<sg-id>.json`, status 转换 = mv (Path → Path)
- B. 单目录 + JSON 内 status 字段, status 转换 = read-modify-write
- C. SQLite 单表 (overkill)

### 决策: A — 5 子目录 mv

**理由**:
- 与 F003 `.garage/memory/candidates/items/` (按 status 分子目录) 同 pattern
- `garage skill suggest --status promoted` 直接 ls 子目录, 无需扫所有文件读 JSON
- mv 比 read-modify-write 更原子 (单个 syscall)
- audit/decay 扫 `proposed/` 即可计 expiry, O(N proposed) 而非 O(N total)

### 影响

- `suggestion_store.py` 实现 `move_to_status(sg_id, new_status)` 用 `os.rename`
- `~/.garage/skill-suggestions/{proposed/, accepted/, promoted/, rejected/, expired/}/` 5 子目录在首次写时 lazy mkdir

## 4. ADR-D13-3 — Pattern Detector 触发 (sync vs async vs explicit hook)

### 选项

- A. **同步 hook**: caller (`SessionManager.archive_session` 链) 在 `MemoryExtractionOrchestrator.extract_for_archived_session_id` 返回后立即调用 `SkillMiningHook.run_after_extraction(session_id)`. 用户感知到 archive_session 多耗 X 秒 (CON-1303 ≤ 5s for 1000+1000)
- B. **异步 spawn**: hook 起后台线程跑 detector, archive_session 立即返回. 风险: detector 写 proposal 时 `garage status` 可能读到中间态
- C. **显式 CLI only**: hook 不自动调; 用户必须 `garage skill suggest --rescan` 手动触发. 风险: 用户感知不到 push 端, vision 触发信号不闭环

### 决策: A — 同步 hook (caller 自行调用)

**理由**:
- vision: "系统主动指出 pattern → skill" 必须在 archive 后自动跑 (Option C 等于不存在 push 端)
- Option B 异步带来的并发复杂性 (中间态 read / race 文件锁) 不值得为 5 秒延迟避免
- CON-1303 性能预算 5s 对 archive_session 路径可接受 (archive 本身就是 1-2s 量级 IO)
- caller 自行调用 = 非 breaking 扩展 (CON-1301 + Im-2 修订一致): F003 既有方法签名不动, hook 只是 sibling callback

### 影响

- `SessionManager.archive_session` 内 `extract_for_archived_session_id` 调用之后, **可选** invoke `SkillMiningHook.run_after_extraction(session_id, storage)` (try/except 包住, hook 失败不阻断 archive)
- `garage session import` 同样 caller 路径添加可选 invoke
- `SkillMiningHook` 在 `pipeline.py`, run() 内部串行: list_entries + list_records → cluster → score → 写 proposal

### 风险

- R-D13-3a: 1000+1000 entry 性能 > 5s → fallback 到 Option C (CLI only) 走 F014+ 增量扫
- R-D13-3b: archive_session 异常中断时 hook 残留状态 → try/except + log; 下次 status 自动 reconcile

## 5. ADR-D13-4 — problem_domain_key 来源 (Cr-3 USER-INPUT 落地)

### 选项

- A. KnowledgeEntry 仅认 `front_matter["problem_domain"]`, 缺则跳过该 entry 不归类
- B. KnowledgeEntry 优先 `front_matter["problem_domain"]`; fallback `topic.split()[0]` (第一个空格前 token)
- C. 加新顶层字段到 KnowledgeEntry (违 CON-1301)

### 决策: B — 优先 front_matter, fallback topic 第一 token

**理由**:
- C 违 CON-1301 (字节级不变), 直接淘汰
- A 在迁移期 (用户既有 entry 不带 front_matter) 漏判过严, 用户首次 `--rescan` 会得 0 候选, 体验差
- B 是渐进 migration: 老 entry 用 topic fallback (粗粒度) 也能命中; 新 entry 用 front_matter 精确归类
- ExperienceRecord 直读 `record.problem_domain` (F004 既有), 与 KnowledgeEntry 路径不同但归一化到同一 key

### 影响

- `pattern_detector._extract_problem_domain_key(item)` 实现:
  ```python
  if isinstance(item, ExperienceRecord):
      return item.problem_domain or "unknown"
  elif isinstance(item, KnowledgeEntry):
      key = item.front_matter.get("problem_domain")
      if not key and item.topic:
          key = item.topic.split()[0]
      return key or "unknown"
  ```
- "unknown" 桶下的 entry 不参与聚类 (评分时 `if domain == "unknown": continue`)

## 6. ADR-D13-5 — SKILL.md 模板生成 (静态拼接 vs Jinja2)

### 选项

- A. Python f-string 静态拼接 (stdlib only, 满足 CON-1302)
- B. Jinja2 模板引擎 (third-party 依赖, 违 CON-1302)
- C. `string.Template` (stdlib but 表达力弱)

### 决策: A — f-string 静态拼接

**理由**:
- CON-1302 零依赖 是硬约束
- 模板结构固定 (6 章节, 章节顺序不变), Jinja2 的循环/条件优势用不上
- f-string 多行 string + 显式 fallback if-else 已足够; 调试友好, 单测好写

### 影响

- `template_generator.py` 内每章节是一个 helper function 返回 string segment, 最后 `"\n".join(...)` 组装
- `_render_workflow_section(record_list, suggestion)` etc.

## 7. ADR-D13-6 — `garage status` skill mining 段集成

### 选项

- A. `_status()` 函数内直接 inline 调用 `SkillMiningStatus.summary()`
- B. 通过 callback 注册 `_STATUS_HOOKS: list[Callable]` 让多个子系统插入 status 段 (general)
- C. 单独 `garage skill status` subcommand (不集成进 `garage status`)

### 决策: A — inline 调用

**理由**:
- B 是过度抽象 (yagni); F010 sync 段也是 inline (`_print_sync_status` 直接 import)
- C 违 spec FR-1305 ("每次 `garage status` 检查")
- A 与 F010 既有模式一致, 修改面最小

### 影响

- `cli.py::_status()` 调用末尾加 `_print_skill_mining_status(garage_dir)` (在 sync segment 之后)
- 实现在 `cli.py` 内 (与 `_print_sync_status` 同位置), 调用 `skill_mining/pipeline.py::compute_status_summary()`

## 8. ADR-D13-7 — 任务分块 + 子提交边界 (T1-T5 与 spec § 9 1:1)

### 任务表

| 任务 | 交付 | 测试增量 | 依赖 |
|---|---|---|---|
| **T1** | `skill_mining/{__init__.py, types.py, suggestion_store.py}` | 8 (`test_suggestion_store.py`: CRUD / 5 status 子目录 / mv 状态转换 / atomic write / id 生成) | 无 (foundation) |
| **T2** | `skill_mining/pattern_detector.py` (含 ADR-D13-4 problem_domain_key 双源 + 聚类 + 评分 + 阈值 + 已 cover skill 检测) | 12 (`test_pattern_detector.py`: 聚类 / 评分 / 阈值 / 双源 problem_domain_key / unknown 桶 / 去重 / 已 cover 跳过 / score 计算公式 / unique_session_count / max_timestamp / N 调阈值) | T1 (writes SkillSuggestion) |
| **T3** | `skill_mining/template_generator.py` (6 章节 in-memory string; ADR-D13-5 f-string 拼接) | 10 (`test_template_generator.py`: frontmatter / When to Use / Workflow / Output Contract / Red Flags / Verification / source_evidence_anchors fallback / 描述 ≥ 50 字 / 主文件 ≤ 300 行 / minimal evidence robust) | T1 (reads SkillSuggestion) |
| **T4** | `skill_mining/pipeline.py` (含 `SkillMiningHook` + audit/decay) + CLI `skill suggest` (含 `--status / --rescan / --threshold / --purge-expired / --id`) + caller hook 接入 | 12 (`test_pipeline.py` 6 + `test_cli.py::TestSkillSuggestCommand` 6: hook 调用 / audit 30 天 / status 显示 / rescan 行为 / purge / --id detail) | T1 + T2 + T3 |
| **T5** | CLI `skill promote` (含 `--reject / --yes / --dry-run / --target-pack`) + `_status` 集成 + `_print_skill_mining_status` + AGENTS.md / RELEASE_NOTES + manual smoke walkthrough | 8 (`test_cli.py::TestSkillPromoteCommand` 5 + `test_dogfood_layout.py` 1 sentinel + `test_documentation.py` 2 README/AGENTS) | T1-T4 |

预估总测试增量: **~50** (基线 main `65701af` 930 → 980 passed)

依赖图: T1 → T2 / T3 → T4 → T5 (T2 + T3 可并行但 commit 顺序 T2 先, T3 后)

### 任务-FR-INV trace

| FR | 任务 | INV |
|---|---|---|
| FR-1301 (Pattern Detection) | T2 | INV-F13-3 (read-only on KnowledgeStore + ExperienceIndex) + INV-F13-5 (F003-F011 字节级不变) |
| FR-1302 (`skill suggest`) | T4 | INV-F13-1 (`.garage/skill-suggestions/` 内写) |
| FR-1303 (Template Generator) | T3 | INV-F13-4 (skill-anatomy 6 章节) |
| FR-1304 (`skill promote`) | T5 | INV-F13-1 (写 packs/ 仅在 promote) + INV-F13-2 (opt-in) |
| FR-1305 (Audit/Decay) | T4 + T5 | INV-F13-1 (mv 不删原文件) |

## 9. INV (Invariants 落地)

| INV | spec 要求 | 设计落地 |
|---|---|---|
| **INV-F13-1** | 不写 packs/ 之外用户拥有 path (除 .garage/skill-suggestions/) | `template_generator` 不写文件 (返回 string); `promote` 唯一调用 `Path.write_text` 到 `packs/<target>/skills/<name>/SKILL.md`; `suggestion_store` 只写 `.garage/skill-suggestions/` 子目录 |
| **INV-F13-2** | promote 必须 opt-in | CLI handler `_skill_promote` 默认 prompt; `--yes` 跳; `--dry-run` 不写; 同名 skill 已存在 → prompt overwrite (RSK-1304) |
| **INV-F13-3** | pattern_detector read-only | `pattern_detector.py` 仅调 `KnowledgeStore.list_entries` + `ExperienceIndex.list_records` (read API); 写出仅经 `suggestion_store.create_proposed(...)` 通道 |
| **INV-F13-4** | SKILL.md 遵 skill-anatomy 6 章节 | `template_generator._SECTIONS = [_render_frontmatter, _render_when_to_use, _render_workflow, _render_output_contract, _render_red_flags, _render_verification]` 固定 6 函数 |
| **INV-F13-5** | F003-F011 既有 API 字节级不变 | T2 不修改 `MemoryExtractionOrchestrator` / `KnowledgeStore` / `ExperienceIndex` 既有方法签名; 仅 caller (T4) 在 `SessionManager.archive_session` 链尾添加 optional `SkillMiningHook.run_after_extraction(...)` 调用 |

## 10. CON (Constraints 守门)

| CON | spec 要求 | 设计守门方法 |
|---|---|---|
| **CON-1301** | F003-F011 既有 API + schema 字节级不变 | 设计内 sentinel: T1 不动 `src/garage_os/types/__init__.py` `KnowledgeEntry` / `ExperienceRecord` 定义; T4 caller 改动用 try/except 包 (hook 失败不阻断) |
| **CON-1302** | 零依赖变更 (`pyproject.toml + uv.lock` diff = 0) | ADR-D13-5 f-string 拼接; 全 stdlib (json / collections / pathlib / dataclasses / re / os / datetime) |
| **CON-1303** | 性能 ≤ 5s for 1000+1000 entry | T2 implementation: 避免 O(N²) (聚类用 `defaultdict(list)` O(N)); 评分公式简单 (log10 + 加法); 单测 `test_pattern_detector_performance` 跑 100 entry 应 < 0.5s, extrapolate 1000 < 5s |
| **CON-1304** | promote 不动 packs/<id>/pack.json | T5 `_skill_promote` 不调用 `pack_install` 任何 mutation API; 仅 `Path("packs/...").write_text(...)`; 守门 sentinel: `tests/skill_mining/test_promote_no_pack_json_mutation.py` |
| **CON-1305** | hf-test-driven-dev 路径仅 echo 不自动 invoke | T5 `_skill_promote` print echo 后 return 0; 不 spawn subprocess / 不 import hf-test-driven-dev module |

## 11. 关键 dataclass 设计

```python
# skill_mining/types.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class SkillSuggestionStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class SkillSuggestion:
    id: str  # sg-<yyyymmdd>-<6 hex>
    suggested_name: str
    suggested_description: str  # ≥ 50 chars
    problem_domain_key: str
    tag_bucket: list[str]  # alpha-sorted, len ≤ 2
    evidence_entries: list[str]  # KnowledgeEntry.id list
    evidence_records: list[str]  # ExperienceRecord.record_id list
    suggested_pack: str  # default "garage"
    score: float
    status: SkillSuggestionStatus
    created_at: datetime
    expires_at: datetime  # default created_at + 30 days
    promoted_to_path: str | None = None
    rejected_reason: str | None = None  # ≤ 500 chars
```

## 12. CLI surface 详细

```
garage skill suggest                            # list status=proposed by score desc
garage skill suggest --status all|proposed|...  # filter
garage skill suggest --id sg-XXX                # detail + SKILL.md preview
garage skill suggest --rescan                   # full re-scan + write new proposals
garage skill suggest --threshold N              # this list filter only
garage skill suggest --rescan --threshold N     # re-scan with threshold N
garage skill suggest --purge-expired [--yes]    # physical delete expired

garage skill promote <sg-id>                    # interactive
garage skill promote <sg-id> --yes              # skip prompt
garage skill promote <sg-id> --dry-run          # preview only
garage skill promote <sg-id> --target-pack X    # default "garage"
garage skill promote <sg-id> --reject [reason]  # status=rejected

garage status                                   # 末尾加 skill mining 段
                                                # 元数据行 (always) + 💡 行 (proposed > 0)
```

## 13. 风险 + 设计缓解

| RSK | spec 风险 | 设计缓解 |
|---|---|---|
| **RSK-1301** | 小 KnowledgeStore 永不触发, 用户感觉 "系统没工作" | T5 `_print_skill_mining_status` 始终显元数据行 "Skill mining: scanned X entries / Y records / Z proposed (last scan: <ts>)" 即便 Z=0 也显 |
| **RSK-1302** | 模板生成质量浅 | T3 模板顶部添加注释 `<!-- AI-generated skeleton from F013-A skill mining; refine via 'garage run hf-test-driven-dev' -->` |
| **RSK-1303** | promote 后跳 hf-test-driven-dev 断 workflow | T5 echo 不自动 invoke; AGENTS.md 文档化 "promote 后建议先 garage run hf-workflow-router 重评估 profile" |
| **RSK-1304** | 同名 skill 已存在 | T5 `_skill_promote` 检测 `Path("packs/<target>/skills/<name>/SKILL.md").exists()` → prompt overwrite y/N (除 --yes); --dry-run 显 "would overwrite" |
| **RSK-1305** | rejected reason 滥用作长文 | T5 prompt 限 500 chars (`reason[:500]`); 警告 "brief reason" |

新增设计风险:

| RSK | 描述 | 缓解 |
|---|---|---|
| **RSK-D13-6** | hook 在 archive_session 链中失败导致 archive 中断 | T4 caller 改动用 `try: hook(...); except Exception as e: log warning, continue` 包; archive 永远 succeed |
| **RSK-D13-7** | suggestion_store 5 子目录权限问题 (用户没 .garage/ 写权限) | T1 `suggestion_store._ensure_dirs()` 失败时 raise OSError + 明确错误 msg "无法创建 .garage/skill-suggestions/, 检查目录权限" |
| **RSK-D13-8** | rescan 期间用户调 promote, 状态文件 race | T4 rescan 写入用 atomic_write (临时文件 + os.rename); promote 读取期间若文件 mv 走 → FileNotFoundError 友好提示 "suggestion 已被 rescan 重生, 请 garage skill suggest 重看" |

## 14. 验证策略

- 单测: 50 个新测试 (T1: 8, T2: 12, T3: 10, T4: 12, T5: 8)
- Manual smoke (T5): 4 tracks
  - Track 1: rescan + suggest list (空 + 5 evidence + 8 evidence)
  - Track 2: promote happy path → packs/garage/skills/<name>/SKILL.md 创建
  - Track 3: reject + reason record
  - Track 4: audit 30 days expiry + purge
- Sentinel: `tests/skill_mining/test_baseline_no_regression.py` (复用 F010 sentinel pattern)
- Performance: `test_pattern_detector_performance` 跑 100 entry < 0.5s
- ruff baseline diff = 0 (与 F012 一样的预算)

## 15. 与 vision 对照 (deliverable check)

- ✅ Stage 3 ~65% → ~85% (skill mining 信号闭环)
- ✅ growth-strategy.md § 1.3 表第 4 行 "系统能指出 pattern → skill" ❌ → ✅
- ✅ B4 5/5 维持 (具象化)
- ❌ 不动 Stage 4 (deferred 到 F013-J / F014+)

---

> **本文档是 design r1**, 待 hf-design-review (subagent 派发). r2 起草由 review verdict 驱动.
