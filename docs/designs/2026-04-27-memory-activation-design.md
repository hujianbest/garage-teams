# F016 Design — Memory Activation (技术设计)

- **状态**: r1 (auto-streamlined APPROVED per F011-F015 mode)
- **关联 spec**: `docs/features/F016-memory-activation.md` r2 (APPROVED 2026-04-27)
- **基线**: F015 branch `4aa52d7` (1103 passed; F016 base on F015 since PR #38 + #39 not yet merged)
- **日期**: 2026-04-27

## 0. 设计概览

实现 F016 spec 5 部分 (A-E). 与 F013-A/F015 同 pattern 复刻 (template + library + CLI), 但聚焦 **激活既有 pipeline** 而非新加 pipeline. 风险显著低于 F014 (F014 改 4 个 caller, F016 仅加 CLI + ingest 路径; 0 caller 修改).

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────┐
│  Existing F003-F015 (read-mostly, INV-F16-1)            │
│  MemoryExtractionOrchestrator + load_memory_config      │
│  ExperienceIndex.store / KnowledgeStore.store           │
│  KnowledgeType.STYLE                                    │
└─────────────────────────────────────────────────────────┘
                            │ (write via store API)
                            ↓
┌─────────────────────────────────────────────────────────┐
│        NEW: src/garage_os/memory_activation/            │
│   ┌─────────────────────────────────────────────────┐   │
│   │  types.py: MemoryStatus + IngestSummary         │   │
│   │  templates.py: 模板化 STYLE entries 加载        │   │
│   │  ingest.py: from-reviews / from-git-log /       │   │
│   │             from-style-template + dedup         │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │ (CLI surface)
                            ↓
┌─────────────────────────────────────────────────────────┐
│  garage memory {enable, disable, status, ingest}        │
│  garage init --no-memory + interactive prompt           │
│  garage status (Memory extraction 行 + STYLE 计数)      │
└─────────────────────────────────────────────────────────┘
```

**关键约束**: F016 只加 sibling 模块 + CLI; 不改 F003-F015 任何 method / caller (CON-1601 守门).

## 2. ADR

### ADR-D16-1 — 模块边界

**决策**: 顶级包 `src/garage_os/memory_activation/`. 与 F013-A skill_mining / F014 workflow_recall / F015 agent_compose 平级.

### ADR-D16-2 — `garage init` prompt 兼容策略 (Cr-1 r2 落地)

**决策**: F016 不重载 `--yes` 改 memory state.

实现:
```python
# cli.py::_init (modified)
def _init(garage_root, *, hosts, scope, yes, no_memory, ...):
    # ... existing flow ...
    extraction_enabled = False  # default
    if not no_memory:
        if yes:
            # Cr-1 r2: --yes does NOT enable memory (F007 既有 --yes 语义不变)
            extraction_enabled = False
        elif sys.stdin.isatty():
            # Interactive: prompt
            ans = input("Enable memory extraction? Garage will auto-extract knowledge from your archived sessions. [Y/n]: ").strip().lower()
            extraction_enabled = ans in ("", "y", "yes")
        else:
            # non-TTY without --yes: default false
            extraction_enabled = False
    
    config = dict(DEFAULT_PLATFORM_CONFIG)
    config["memory"] = {
        "extraction_enabled": extraction_enabled,
        "recommendation_enabled": False,
    }
    # ... write platform.json, etc ...
```

新增 `--no-memory` flag 与 既有 `--yes`, `--scope`, `--hosts` 兼容; 任意组合都 OK.

### ADR-D16-3 — Ingest dedup 策略

**决策**: 用 `source_evidence_anchors` 中含原文件 path / commit SHA 作 dedup key. 与 F003 publisher self-conflict pattern 同精神.

实现:
```python
# ingest.py
def ingest_from_reviews(reviews_dir, exp_index, *, dry_run, strict, yes):
    existing_anchors = set()
    for r in exp_index.list_records():
        for anchor in (r.source_evidence_anchors or []):
            if isinstance(anchor, dict) and "review_path" in anchor:
                existing_anchors.add(anchor["review_path"])
    
    new_records = []
    skipped = 0
    for md_file in sorted(reviews_dir.glob("*.md")):
        rel_path = str(md_file.relative_to(garage_root))
        if rel_path in existing_anchors:
            skipped += 1
            continue
        # parse + build ExperienceRecord
        record = _parse_review(md_file)
        if record is None:
            if strict:
                raise ValueError(f"Failed to parse {md_file}")
            else:
                skipped += 1
                continue
        new_records.append(record)
    
    if not dry_run:
        for r in new_records:
            exp_index.store(r)
    return IngestSummary(written=len(new_records), skipped=skipped, dry_run=dry_run)
```

### ADR-D16-4 — Review verdict parser

filename pattern: `<type>-review-f<NNN>-r<R>-<date>.md` (例 `spec-review-f012-r1-2026-04-25.md`):
- `<type>` ∈ {spec, design, test, code, traceability}
- `<NNN>` lowercase feature id
- `<R>` round number

提取规则:
- task_type = `f"{type}-review-verdict"` 或简化为 `'review-verdict'`
- problem_domain = `f"f{NNN}"`
- skill_ids = `[f"hf-{type}-review"]` (例 `['hf-spec-review']`)
- lessons_learned = 从 `## Recommendations for r2` / `## Recommendations` 段抽前 3 个 list 项 (regex 匹配 `^[-\d]+\. `)
- source_evidence_anchors = `[{"review_path": <rel_path>, "review_type": <type>, "round": <R>}]`

### ADR-D16-5 — Git log parser

调 `subprocess.run(["git", "log", "--oneline", f"-{limit}"], capture_output=True, text=True)`:
- 每行 `<sha> <message>` 解析
- task_type = `'commit'`
- problem_domain = 从 message regex `^(f\d{3})\(` 抽 (lowercase); 抽不到则 fallback `'unknown'`
- skill_ids = 从 message regex `\b(hf-[a-z-]+)\b` 全部抽; 抽不到则 `[]`
- duration_seconds = 0 (commit timestamp 间隔可后续 D-1610 加)
- source_evidence_anchors = `[{"commit_sha": <sha>, "commit_message": <msg>}]`

### ADR-D16-6 — 任务分块

| T | 内容 | 测试 |
|---|---|---|
| T1 | types.py + templates.py + 3 个 STYLE 模板 | 8 |
| T2 | ingest.py (3 paths + dedup + dry-run + strict) | 12 |
| T3 | CLI memory subparser + _init prompt + _status 集成 | 10 |
| T4 | sentinel + AGENTS / RELEASE_NOTES + smoke | 5 |

预估 ~35 测试. 1103 → ~1138.

## 3. INV / CON 落地

| INV/CON | 落地 mechanism |
|---|---|
| INV-F16-1 | T2 ingest 仅调 store API; 不修改 F003-F015 method 签名 |
| INV-F16-2 | T1 模板写 packs/garage/templates/; T2 ingest 写 .garage/knowledge/ + .garage/experience/ via store API |
| INV-F16-3 | T3 cli `_init` 加 `--no-memory` + prompt; **不改 `--yes` 语义** (Cr-1 r2) |
| INV-F16-4 | T3 enable/disable 仅修改 platform.json `memory.extraction_enabled`; 不删既有数据 |
| INV-F16-5 | T1 STYLE 模板用 KnowledgeStore.store + KnowledgeType.STYLE 既有 enum |
| CON-1601 | T1-T4 不动 src/garage_os 既有模块 (除 cli.py 加 subparser/handler/init prompt) |
| CON-1602 | 全 stdlib (subprocess, re, json, pathlib, dataclasses) |
| CON-1603 | T2 ingest 单测覆盖 100 review / 1000 commit < 5s; manual perf smoke 不必 (规模小) |
| CON-1604 | T3 cli 仅加 `--no-memory` 到 init parser; 既有 args 不动 |
| CON-1605 | T1 STYLE 模板 + ingest 仅经 KnowledgeStore.store 写; F015 compose 自动看到 (因为 F015 已经调 list_entries(STYLE)) |

## 4. 风险

| RSK | 缓解 |
|---|---|
| RSK-D16-1 review parser pattern 不匹配 | --strict opt-in raise; 默认 skip + log warning |
| RSK-D16-2 git log subprocess 失败 (无 git) | catch + return empty + stderr 提示 |
| RSK-D16-3 STYLE 模板格式漂移 | 模板文件 in repo; T1 单测 parse 验证 |

---

> **本文档是 design r1 (auto-streamlined APPROVED)**.
