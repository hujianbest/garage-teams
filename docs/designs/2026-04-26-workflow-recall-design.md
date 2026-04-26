# F014 Design — Workflow Recall (技术设计)

- **状态**: 草稿 r2 (回应 design-review-F014-r1; 2 critical + 3 important + 1 minor + 2 nit 全部闭合; 待 r2 hf-design-review)
- **关联 spec**: `docs/features/F014-workflow-recall.md` r2 (commit `46e9048`, APPROVED 2026-04-26)
- **基线**: main `f5950b4` (989 passed, F013-A 已 merge)
- **日期**: 2026-04-26

## 0. 设计概览

实现 F014 spec 5 部分 (A-E) 的端到端技术方案. 遵循 F013-A 同等粒度: ADR + INV + 任务分块.

未显式标注的 ADR 默认 `Status: Accepted r1`.

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────┐
│       Existing F003-F013 (read-only, INV-F14-1)         │
│   ExperienceIndex.list_records() + search()             │
│   ExperienceRecord (problem_domain, task_type,          │
│                      skill_ids, key_patterns,           │
│                      lessons_learned, duration_seconds) │
└─────────────────────────────────────────────────────────┘
                            │ (read-only via list_records)
                            ↓
┌─────────────────────────────────────────────────────────┐
│           NEW: src/garage_os/workflow_recall/           │
│   ┌─────────────────────────────────────────────────┐   │
│   │  types.py: RecallResult + WorkflowAdvisory      │   │
│   │  cache.py: cache.json + last-indexed.json CRUD  │   │
│   │  path_recaller.py: 聚类 + Counter + 阈值        │   │
│   │  pipeline.py: WorkflowRecallHook + status       │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────┐
│  .garage/workflow-recall/                               │
│    cache.json     last-indexed.json                     │
└─────────────────────────────────────────────────────────┘
                            │ (CLI surface)
                            ↓
┌─────────────────────────────────────────────────────────┐
│  garage recall workflow [--task-type/--problem-domain   │
│    /--skill-id/--top-k/--json/--rebuild-cache]          │
│  garage status (workflow-recall 段; Im-6 pattern)       │
│  hf-workflow-router/SKILL.md step 3.5 + handoff advisory│
└─────────────────────────────────────────────────────────┘
```

模块依赖:
```
types ← cache ← path_recaller ← pipeline ← CLI handler
```

新模块: `src/garage_os/workflow_recall/{types.py, cache.py, path_recaller.py, pipeline.py, __init__.py}`

CLI 改动: `cli.py` 加 `recall` subparser (`workflow` 子子命令); `_status` 末尾加 `_print_workflow_recall_status`. 注: `recall` 是新 top-level subcommand (与 `recommend` 平级), 不嵌入 `recommend` (CON-1405).

Hook 接入 (Cr-1 r2): 5 caller 末尾 try/except invoke `WorkflowRecallHook.invalidate(garage_dir)`.

## 2. ADR-D14-1 — 模块边界 (顶级包 vs experience 子包)

### 选项

- A. `src/garage_os/knowledge/workflow_recall/` (作为 knowledge 子模块, 因为 F004 ExperienceIndex 在此)
- B. `src/garage_os/workflow_recall/` (顶级包, 与 sync / skill_mining 平级)

### 决策: B — 顶级包

**理由**:
- F014 与 F013-A skill_mining 概念 sibling (都是 ExperienceIndex 的 push 信号), 应同级
- 写出端是 `.garage/workflow-recall/` (workflow_recall 自己拥有的目录), 不属 knowledge
- 与 F010 `sync/` + F013-A `skill_mining/` 同 pattern

### 影响

- 新增 `src/garage_os/workflow_recall/__init__.py` + 4 个模块文件
- `tests/workflow_recall/` 镜像目录, 与 `tests/skill_mining/` 同级

## 3. ADR-D14-2 — Cache 持久化格式 (单文件 JSON vs 多文件)

### 选项

- A. 单文件 `.garage/workflow-recall/cache.json` 含 `{(task_type, problem_domain): {...}}` (key 用 `f"{tt}|{pd}"` 字符串化)
- B. 多文件 `.garage/workflow-recall/cache/<task_type>__<problem_domain>.json`
- C. SQLite (overkill)

### 决策: A — 单文件 JSON

**理由**:
- F014 cache 总数 = bucket 数 (估几十个 task_type × problem_domain 组合); 单文件 JSON 已够
- 失效 = 删 last-indexed.json; 不需要 per-bucket 失效粒度
- 与 F013-A `.last-scan.json` 单文件 pattern 一致
- 全量重算 lazy on read (Im-5 r2 修订: 不做增量), 无并发写问题

### 影响

- `cache.py` 实现 atomic write (tempfile + os.replace)
- key 格式: `{tt}|{pd}` (空 task_type 用 `*`, 空 problem_domain 用 `*`)

## 4. ADR-D14-3 — WorkflowRecallHook 多 caller 接入 (Cr-1 r2 选项 c 落地)

### 选项

- A. 修改 ExperienceIndex.store 内部加 invalidate (改 F004 内部行为)
- B. 引入 `WorkflowRecallHook.invalidate` 在每个 caller 末尾 try/except invoke (sibling callback, 与 F013-A SkillMiningHook 同 pattern) ← spec r2 锁定
- C. 仅 SessionManager._trigger_memory_extraction (spec r1 错; reviewer Cr-1 发现遗漏)

### 决策: B — 多 caller 接入 (与 F013-A 同 pattern)

**Status: Accepted r1** (spec r2 已 USER-INPUT 锁定)

**理由**:
- F004 ExperienceIndex.store 既有方法签名字节级不变 (CON-1401 守门)
- 与 F013-A SkillMiningHook 接入模式一致, 维护成本低
- 5 个 caller 中失败任一不阻断 caller (try/except + best-effort)
- 任意遗漏路径用户 `--rebuild-cache` 兜底

### Caller 接入点 (4 处, r2 修订)

设计 r1 写 5 处, reviewer 发现 (a) 还有第 6 处 `cli.py:1172` skill 执行路径 (Cr-1); (b) `ingest/pipeline.py` 实际不直接 store, 是 publisher 间接 (Cr-2); (c) `publisher.py` 既有 store 也有 update 路径 (Im-1). r2 重新锁定 4 个真实接入点:

| # | Caller 文件 | 行号 | 接入点描述 | 备注 |
|---|---|---|---|---|
| 1 | `src/garage_os/runtime/session_manager.py` | `_trigger_memory_extraction` 末尾 (~ L268-277, F013-A SkillMiningHook 之后) | F003 archive 路径 | 注: archive 自身不直接调 EI.store; 但 archive 触发 publisher → store, 这处 hook 是冗余的 archive-level 兜底 (确保 archive 后 cache 失效). 也可省略, 因为 publisher 已有 hook (条目 3) |
| 2 | `src/garage_os/cli.py` `_experience_add` | `experience_index.store(record)` 后 (~ L1741) | 用户显式 `garage experience add` | 单行 try/except 包 |
| 3 | `src/garage_os/memory/publisher.py` | `if-else 分支末尾` (~ L143 后, 覆盖 store + update 两路径) | F003 publisher 路径 | **r2 Im-1 修订**: 不在 L138 单行挂; 改在 if-else **共同末尾** (publisher 决策 store 还是 update 之后), 覆盖 update 内部调 self.store 的间接路径 |
| 4 | `src/garage_os/knowledge/integration.py` | `experience_index.store(experience)` 后 (~ L222) | F006 integration 路径 | 单行 try/except 包 |

**r2 删除的 r1 接入点**:
- ~~`ingest/pipeline.py`~~ (Cr-2): 该文件无 `experience_index.store`; ingest 路径下游通过 publisher (条目 3) 间接触发 invalidate; 不需要重复挂

**r2 排除的 caller** (Cr-1 USER-INPUT 决策, auto mode 默认锁定方案 b):
- ~~`cli.py:1172`~~ (skill execution record path): 显式排除. **理由**: 该路径记录的是 single skill 调用本身 (例 `garage run hf-specify`), 不是 cycle-level task path. workflow recall 的 advisory 单位是 cycle-level 路径 (例 hf-specify → hf-design → hf-tasks → hf-test-driven-dev), 不是单 skill. 用户在该路径写的 record `task_type` 通常是 "skill_run" 或类似, 与 PathRecaller 的 (task_type, problem_domain) 聚类语义不匹配. 用户用 `--rebuild-cache` 兜底.

每处都是 1-3 行 try/except 包装 + 不改 caller 既有 method 签名.

### 失败语义

- hook 失败不阻断 caller (best-effort, 与 F013-A 同精神)
- log 到 stderr 但不 raise

## 5. ADR-D14-4 — Path Recaller 算法 (Counter vs Trie vs DAG)

### 选项

- A. Python collections.Counter on tuple(skill_ids) (O(N) 简单, 适合 N ≤ 1000)
- B. Trie (prefix tree, 适合 N ≫ 1000 + 子序列查询)
- C. DAG / graph 表示 (overkill 当前 cycle)

### 决策: A — Counter on tuple(skill_ids)

**Status: Accepted r1**

**理由**:
- N ≤ 1000 ExperienceRecord (CON-1403 性能预算; 全量重算 < 2s)
- Counter 实现简单 + stdlib (CON-1402 零依赖)
- top-K 用 `Counter.most_common(K)` 内置 O(N log K)
- Trie 适合 N ≫ 1000 时增量扫 + 前缀查询, 是 D-1410 F015+ carry-forward

### 实现

```python
# path_recaller.py 核心算法
from collections import Counter
def recall(records: list[ExperienceRecord], task_type, problem_domain, skill_id, top_k):
    # 1. Filter
    bucket = [r for r in records if (
        (task_type is None or r.task_type == task_type) and
        (problem_domain is None or r.problem_domain == problem_domain)
    )]
    if len(bucket) < THRESHOLD:  # default 3
        return RecallResult(advisories=[], scanned_count=len(records))
    # 2. Order by created_at desc, take top N (default 10)
    bucket.sort(key=lambda r: r.created_at, reverse=True)
    bucket = bucket[:WINDOW]
    # 3. Build sequences (handle --skill-id sub-sequence per Im-4 contract)
    seqs = []
    for r in bucket:
        seq = tuple(r.skill_ids)
        if skill_id:
            try:
                idx = seq.index(skill_id)
                seq = seq[idx + 1:]  # take after first occurrence
                if not seq:
                    continue  # empty after Z is last item; skip
            except ValueError:
                continue  # skill_id not in this record's seq; skip
        seqs.append(seq)
    # 4. Counter + top-K
    counter = Counter(seqs)
    advisories = [
        WorkflowAdvisory(skills=list(seq), count=cnt, ...)
        for seq, cnt in counter.most_common(top_k)
    ]
    return RecallResult(advisories=advisories, scanned_count=len(records))
```

## 6. ADR-D14-5 — `garage status` 集成

### 选项

与 F013-A ADR-D13-6 同决策 (inline 调用), 不重复推导.

### 决策: inline 调用 (与 sync / skill_mining 同 pattern)

**Status: Accepted r1**

`cli.py::_status` 末尾在 `_print_skill_mining_status` 后加 `_print_workflow_recall_status`. 实现 cache stale 时显 "(stale, will rebuild on next recall call)".

## 7. ADR-D14-6 — hf-workflow-router SKILL.md 改动策略

### 选项

- A. 重写 router workflow (大改; 破坏 INV-F14-5)
- B. additive insertion: 在 step 3 与 step 4 之间插入 step 3.5 (spec r2 Cr-3 锁定)

### 决策: B — additive step 3.5

**Status: Accepted r1**

**理由**:
- INV-F14-5 守门: 既有 step 1-10 不变, 仅插入 step 3.5
- 既有 BDD 仍过 (router workflow 文档化无运行时测试, 但有 `tests/adapter/installer/test_dogfood_invariance_F009.py` SHA sentinel)
- 改动局限 = 加约 30 行 SKILL.md 内容 (step 3.5 描述 + handoff 块 advisory 段说明)

### Im-3 r2 dogfood SHA 同步流程 (Im-2 design-r2 修订: 2 处而非 3 处)

reviewer 发现 `tests/adapter/installer/dogfood_baseline/skill_md_sha256.json` **只有** 2 个 hf-workflow-router 键 (`.claude/skills/hf-workflow-router/SKILL.md` + `.cursor/skills/hf-workflow-router/SKILL.md`), **不追踪** `packs/coding/skills/hf-workflow-router/SKILL.md` 源 hash. 与 F009 既有约定一致 (sentinel 验证的是 dogfood install 产物 byte 一致, 不是源).

T5 流程:
1. 改 `packs/coding/skills/hf-workflow-router/SKILL.md` (源, 加 step 3.5 内容)
2. 跑 `garage init --hosts cursor,claude --yes` (重生 `.claude/` + `.cursor/` mirror)
3. 计算 `.claude/skills/hf-workflow-router/SKILL.md` 与 `.cursor/skills/hf-workflow-router/SKILL.md` 的 SHA-256
4. 更新 `tests/adapter/installer/dogfood_baseline/skill_md_sha256.json` 中**这 2 个键**的 hash
5. 跑 `pytest tests/adapter/installer/test_dogfood_invariance_F009.py` 验证 PASS

## 8. ADR-D14-7 — 任务分块 (T1-T5 与 spec § 9 1:1)

### 任务表

| 任务 | 交付 | 测试增量 | 依赖 | 关键 FR/INV/CON |
|---|---|---|---|---|
| **T1** | `workflow_recall/{__init__, types, cache}` (RecallResult / WorkflowAdvisory + cache CRUD + atomic write) + 8 测试 | 8 | 无 | INV-F14-2 (写 .garage/workflow-recall/) + CON-1402 (零依赖) |
| **T2** | `workflow_recall/path_recaller.py` (Counter 算法 + 阈值 3 + window 10 + Im-4 --skill-id 子序列) + 12 测试 + 1 perf | 13 | T1 | FR-1401; INV-F14-1 (read-only on EI); CON-1403 (1000 record < 2s) |
| **T3** | `workflow_recall/pipeline.py` (`WorkflowRecallHook.invalidate` + `compute_status_summary`) + 5 caller 接入 + `garage status` 集成 + 6 测试 | 6 | T1+T2 | FR-1404 (Cr-1 多 caller invalidate); FR-1405 (status 段); CON-1401 (caller try/except 不破 method 签名) |
| **T4** | CLI `garage recall workflow` (含 --task-type / --problem-domain / --skill-id / --top-k / --json / --rebuild-cache) + 8 测试 | 8 | T1-T3 | FR-1402; CON-1405 (与 F006 recommend 独立) |
| **T5** | hf-workflow-router/SKILL.md step 3.5 + references/recall-integration.md + dogfood SHA baseline 同步更新 (**Mi-1 r2: 5 测试**) + AGENTS / RELEASE_NOTES + manual smoke | 5 | T1-T4 | FR-1403 (router 集成); INV-F14-5 (additive); CON-1404 (3 项守门: dogfood SHA + neutrality + 基线) |

预估总测试: **~40** (基线 main `f5950b4` 989 → 1029 passed; 实施前再核 Mi-2 r2)

依赖图: T1 → T2 → T3 → T4 → T5

### 任务-FR-INV trace

| FR | 任务 | INV |
|---|---|---|
| FR-1401 (PathRecaller) | T2 | INV-F14-1 (read-only on EI) + INV-F14-4 (F004 schema 不动) |
| FR-1402 (CLI recall workflow) | T4 | INV-F14-2 (写 .garage/workflow-recall/) |
| FR-1403 (router 集成) | T5 | INV-F14-3 (advisory only) + INV-F14-5 (step 1-10 不变 + dogfood SHA) |
| FR-1404 (cache + invalidate hook) | T3 | INV-F14-1 + CON-1401 (caller try/except 不改签名) |
| FR-1405 (status 段) | T3 + T5 | INV-F14-2 |

## 9. INV (Invariants 落地)

| INV | spec 要求 | 设计落地 |
|---|---|---|
| **INV-F14-1** | path_recaller / cache read-only on EI; 不读不写 KS | T2 path_recaller 仅调 `experience_index.list_records()`; T1 cache 仅写 `.garage/workflow-recall/`; sentinel 测试: KS hash 前后字节相等 |
| **INV-F14-2** | 不写 packs/ 之外用户路径; 例外 `.garage/workflow-recall/` + `.garage/config/platform.json` 字段级 | T1 cache 写仅在 `.garage/workflow-recall/`; T3 platform.json 仅加 `workflow_recall.enabled` sibling field 不破坏既有 schema |
| **INV-F14-3** | router advisory 不改 authoritative routing | T5 router SKILL.md step 3.5 显式标 "advisory only — 用户可改" |
| **INV-F14-4** | F004 ExperienceIndex/ExperienceRecord schema + API 字节级不变 | T2 不修改 `experience_index.py` / `types/__init__.py`; sentinel: `git diff main..HEAD -- src/garage_os/knowledge/experience_index.py src/garage_os/types/__init__.py` 应为 0 (除非 F015+ 显式扩) |
| **INV-F14-5** | router step 1-10 不变 + dogfood SHA baseline 同步 | T5 仅插入 step 3.5; T5 同步更 `dogfood_baseline/skill_md_sha256.json` 三处 hash; sentinel 测试: `tests/adapter/installer/test_dogfood_invariance_F009.py` 直接验证 |

## 10. CON (Constraints 守门)

| CON | spec 要求 | 设计守门方法 |
|---|---|---|
| **CON-1401** | F003-F013 既有 API + schema 字节级不变 | T3 caller 接入用 try/except 包不改 5 个 caller 既有 method 签名; T2 不改 ExperienceIndex |
| **CON-1402** (Ni-1 r2 修订) | 零依赖变更 | 无新第三方依赖 (T1-T5 仅 import garage_os 本库 + stdlib `collections.Counter` / `json` / `pathlib` / `dataclasses`); 单测 sentinel: `git diff main..HEAD -- pyproject.toml uv.lock` = 0 |
| **CON-1403** | 1000 record < 2s | T2 单测 `test_path_recaller_perf_100_records` < 0.2s; T4 finalize 前手工 `scripts/workflow_recall_perf_smoke.py` 1000 record < 2s |
| **CON-1404** | router markdown 改不破 3 项守门 | T5 显式跑 (a) `pytest tests/adapter/installer/test_dogfood_invariance_F009.py` 在更新 baseline 后 PASS; (b) `pytest tests/adapter/installer/test_neutrality_exemption_list.py` PASS; (c) 全套基线 989 → 1029 0 regression |
| **CON-1405** | recall workflow 与 F006 recommend 独立 | T4 `recall` 是新 top-level subparser, 与 `recommend` 平级; 不调用 recommend 任何 API; sentinel: `recall` handler 不 import recommend 模块 |

## 11. 关键 dataclass 设计

```python
# workflow_recall/types.py

from dataclasses import dataclass, field

@dataclass
class WorkflowAdvisory:
    """Single advisory: a (skills sequence) frequency hit.

    Im-3 r2: avg_duration_seconds is **per-sequence mean** (mean of records
    whose skill_ids match this advisory's skills sequence; subset of bucket).
    """
    skills: list[str]                    # ordered skill_ids sequence
    count: int                           # frequency in bucket (records matching this skills sequence)
    avg_duration_seconds: float          # **per-sequence** mean duration_seconds (not bucket-wide)
    top_lessons: list[tuple[str, int]]   # [(lesson, freq)] top 3 from records matching this sequence
    task_type: str | None
    problem_domain: str | None

@dataclass
class RecallResult:
    """Returned by PathRecaller.recall."""
    advisories: list[WorkflowAdvisory]   # sorted by count desc, len ≤ top_k
    scanned_count: int                   # total records scanned (across all buckets)
    bucket_size: int = 0                 # records in matched bucket
    threshold_met: bool = False          # bucket_size >= THRESHOLD
```

## 12. CLI surface 详细

```
garage recall workflow                                   # error: at least one filter required
garage recall workflow --task-type X                     # filter by task_type
garage recall workflow --problem-domain Y                # filter by problem_domain
garage recall workflow --skill-id Z                      # take subseq after Z first occurrence
garage recall workflow --task-type X --problem-domain Y  # combined filter
garage recall workflow --top-k N                         # default 3
garage recall workflow --json                            # for router consumption
garage recall workflow --rebuild-cache                   # force full recompute

garage status                                            # 末尾加 workflow-recall 段
                                                         # "Workflow recall: scanned X / Y / Z (stale|fresh)"
```

## 13. 风险 + 设计缓解

| RSK | spec 风险 | 设计缓解 |
|---|---|---|
| **RSK-1401** | 小 EI 永不触发, 用户感觉 "系统没工作" | T3 `_print_workflow_recall_status` 始终显元数据行 (Z=0 也显; 与 F013-A status 同模式) |
| **RSK-1402** | advisory 序列质量取决于 record 质量 | T2 标 "based on N similar cycles"; T5 router 文档化 "advisory only — 用户可改" |
| **RSK-1403** | router 改动破坏既有 hf-* skill 编排 | T5 INV-F14-5 sentinel + dogfood SHA + neutrality test; 改动仅 step 3.5 additive |
| **RSK-1404** | cache 与 EI 漂移 | T3 5 caller 接入 + `--rebuild-cache` 兜底; status 段显示 stale |
| **RSK-1405** | 用户不希望看 advisory | router step 3.5 文档化 "若 EI 空 跳过"; 用户可显式 CLI 自查 |

新增设计风险:

| RSK | 描述 | 缓解 |
|---|---|---|
| **RSK-D14-6** | hook 在 5 个 caller 中失败导致 caller 中断 | T3 全 try/except + log warn; caller 永远 succeed |
| **RSK-D14-7** | cache.json 损坏 (用户手改) → recall workflow 红 | T1 cache.load() 包 try/except; 损坏时返回空 + 提示 "rebuild via --rebuild-cache" |
| **RSK-D14-8** | T5 dogfood SHA baseline 更新错误 → CI 红 | T5 manual smoke 跑 `pytest tests/adapter/installer/test_dogfood_invariance_F009.py` 前必须先 `bash scripts/setup-agent-skills.sh` 重生 .agents/ + 计算所有 3 处 hash 后批量更 JSON |

## 14. 验证策略

- 单测: 40 个新测试 (T1: 8, T2: 13, T3: 6, T4: 8, T5: 5)
- Manual smoke (T5): 4 tracks
  - Track 1: 0 record → "No workflow advisory yet"
  - Track 2: 5 record → recall 1 advisory + status 段显
  - Track 3: cache invalidation (write 第 6 条 record → cache stale → recall 重算)
  - Track 4: --skill-id 子序列 (Im-4 算法契约)
- Sentinel:
  - `tests/sync/test_baseline_no_regression.py` (复用 F010 sentinel)
  - `tests/workflow_recall/test_recall_no_recommend_import.py` (CON-1405 sentinel)
- Performance:
  - `tests/workflow_recall/test_path_recaller_perf_100_records.py` (单测 < 0.2s)
  - `scripts/workflow_recall_perf_smoke.py` (手工 1000 record < 2s)
- ruff baseline diff = 0 (与 F013-A 同预算)

## 15. 与 vision 对照 (deliverable check)

- ✅ Stage 3 ~85% → ~95% (workflow 半自动编排闭环)
- ✅ growth-strategy.md § Stage 3 第 68 行 "工作流编排从手动变成半自动" ❌ → ✅
- ✅ B4 5/5 维持 (具象化)
- ❌ 不动 Stage 4 (deferred 到 F015+)

---

> **本文档是 design r2** (回应 design-review-F014-r1 的 2 critical + 3 important + 1 minor + 2 nit; 全部 8 finding 已闭合, 详见 `docs/reviews/design-review-F014-r1-2026-04-26.md`).
>
> r2 关键修订:
> - **Cr-1** (USER-INPUT 选项 b 锁定): 显式排除 `cli.py:1172` skill execution path; advisory 单位是 cycle-level task path, 不是 single skill record. r2 caller 表从 5 处缩为 4 处真实接入点
> - **Cr-2**: 删除 r1 的 `ingest/pipeline.py` 接入点 (该文件无 `experience_index.store`; 通过 publisher 间接 invalidate)
> - **Im-1**: publisher.py hook 从 L138 (仅 store 分支) 改为 if-else 末尾 (~ L143 后, 覆盖 store + update 两路径)
> - **Im-2**: dogfood SHA 同步从 "3 处 hash" 改为 "**2 处** hash" (与 F009 baseline JSON 实际只追踪 .claude/ + .cursor/ mirror 一致, 不追源 hash)
> - **Im-3**: `WorkflowAdvisory.avg_duration_seconds` 语义明确为 per-sequence mean (advisory 是 skills 序列粒度, 不是桶级)
> - **Mi-1**: T5 测试数 5 (与 §14 验证策略一致); spec §9.1 的 6 是 preview, 不需 backport
> - **Ni-1**: CON-1402 改 "无新第三方依赖" (不是 "全 stdlib", 因为新模块必然 import garage_os 本库)
