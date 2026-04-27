# F015 Design — Agent Compose (技术设计)

- **状态**: 草稿 r1 (待 hf-design-review)
- **关联 spec**: `docs/features/F015-agent-compose.md` r2 (APPROVED 2026-04-26)
- **基线**: F014 branch `bb803a5` (1043 passed; F015 base on F014 since PR #38 not yet merged)
- **日期**: 2026-04-26

## 0. 设计概览

实现 F015 spec 5 部分 (A-E). 与 F013-A skill_mining template_generator + suggestion_store + CLI promote 同 pattern, 但 agent 级别.

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────┐
│  Existing F008 + F011 + F013-A (read-only, INV-F15-1)   │
│  packs/<id>/skills/<skill>/SKILL.md (frontmatter)       │
│  KnowledgeStore.list_entries(KnowledgeType.STYLE)       │
└─────────────────────────────────────────────────────────┘
                            │ (read-only)
                            ↓
┌─────────────────────────────────────────────────────────┐
│           NEW: src/garage_os/agent_compose/             │
│   ┌─────────────────────────────────────────────────┐   │
│   │  types.py: AgentDraft + ComposeResult           │   │
│   │  template_generator.py: agent.md draft string   │   │
│   │  composer.py: 主 compose 逻辑                   │   │
│   │  pipeline.py: status summary                    │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ↓ (CLI promote — 唯一写盘通道)
┌─────────────────────────────────────────────────────────┐
│  packs/<target>/agents/<name>.md (INV-F15-2 唯一目标)   │
│  packs/<id>/pack.json agents[] 不动 (INV-F15-3)         │
└─────────────────────────────────────────────────────────┘
                            │ (CLI surface)
                            ↓
┌─────────────────────────────────────────────────────────┐
│  garage agent compose <name> --skills <list> [...]      │
│  garage agent ls [--target-pack X]                      │
│  garage status (agent-compose 段)                       │
└─────────────────────────────────────────────────────────┘
```

## 2. ADR-D15-1 — 模块边界 (顶级包)

### 决策: B — 顶级包 `src/garage_os/agent_compose/`

与 sync / skill_mining / workflow_recall 平级. F015 跨 packs/<id>/skills/ + KnowledgeStore + packs/<id>/agents/ 三个数据源, 不属任何子包.

## 3. ADR-D15-2 — agent.md 模板 schema (Cr-2 r2 收窄参考)

### 决策: 严格遵 2 个 F011 agent (blog-writing + code-review) 的 schema

模板章节固定为:
1. frontmatter `name` + `description` (含适用/不适用; ≥ 50 字)
2. `# <Agent Title>` (从 name 推 — 例 `config-design-agent` → `# Config Design Agent`)
3. AI-generated 注释行
4. `## When to Use` (从 skill SKILL.md frontmatter description 抽前半段拼)
5. `## How It Composes` (列 skill 角色)
6. `## Workflow` (按用户给的 skill_ids 顺序)
7. `## Style Alignment` (若有 STYLE entries; --no-style 时省略)

**garage-sample-agent.md** (无 frontmatter, 简化 schema) **不参考** (Cr-2 r2 修订).

## 4. ADR-D15-3 — Multi-line description 切分规则 (Ni-1 r2)

```python
def _extract_skill_summary(description: str, max_chars: int = 80) -> str:
    """Take first non-empty line; truncate to first sentence terminator (。/.) or line end."""
    lines = [l.strip() for l in description.splitlines() if l.strip()]
    if not lines:
        return ""
    first = lines[0]
    # Truncate to first sentence terminator (Chinese 。 or English .) or max_chars
    for terminator in ("。", "."):
        idx = first.find(terminator)
        if 0 < idx < max_chars:
            return first[:idx + 1]
    return first[:max_chars]
```

## 5. ADR-D15-4 — Missing skill 双层语义 (Im-1 r2)

### Library 层 (`composer.py::compose`)

返回 `ComposeResult(draft, missing_skills, style_count, target_pack_exists)`:
- 即使 missing_skills > 0, 仍生成 draft (含 placeholder 段 for missing skills)
- target_pack_exists=False 仍生成 draft (但 CLI 不写)
- 用户 / 未来其他调用方可按需用 partial draft

### CLI 层 (`_agent_compose`)

严格:
- 任一 missing skill → exit 1 + stderr "Missing skills: <list>"; **不写盘**
- target_pack 不存在 → exit 1 + stderr "Target pack 'X' not installed"
- 0 skills → exit 1 + stderr "--skills required (at least one)"

## 6. ADR-D15-5 — `garage status` 集成

### 决策: inline `_print_agent_compose_status` (与 F013-A / F014 同 pattern)

`cli.py::_status` 末尾在 `_print_workflow_recall_status` 之后调用 `_print_agent_compose_status`. 对每个 first-class pack (garage / coding / writing / search) 列 agent count.

实现简单: `len(list((packs_root / pack_id / "agents").glob("*.md")))`. 不依赖 cache.json (Im-2 r2: 删 ts).

## 7. ADR-D15-6 — 任务分块 + 子提交边界 (T1-T4)

### 任务表

| 任务 | 交付 | 测试增量 | 依赖 | FR/INV/CON |
|---|---|---|---|---|
| **T1** | `agent_compose/{__init__, types, template_generator}` (AgentDraft + ComposeResult + agent.md 6-section template + multi-line desc 切分) + 10 测试 | 10 | 无 | INV-F15-2 (写仅 .garage/) + CON-1502 (零依赖) + CON-1504 (template schema) + Ni-1 切分 |
| **T2** | `agent_compose/composer.py` (主 compose: 读 SKILL.md + STYLE entries + 校验 + 双层 missing 语义) + 12 测试 | 12 | T1 | FR-1501 + FR-1502 + INV-F15-1 (read-only) + Im-1 双层 |
| **T3** | CLI `garage agent compose` + `garage agent ls` + `_print_agent_compose_status` + `pipeline.py` + 10 测试 | 10 | T1+T2 | FR-1503 + FR-1504 + FR-1505 + CON-1505 (与 sibling subcommands 独立) |
| **T4** | AGENTS / RELEASE_NOTES + manual smoke + 4 sentinel (INV-F15-5 byte / CON-1503 pack.json byte / CON-1502 零依赖 / CON-1505 sibling import) | 4 | T1-T3 | INV-F15-3 + INV-F15-5 + CON-1502 + CON-1505 |

预估总测试增量: **~36** (基线 F014 1043 → 预计 1079 passed)

## 8. INV / CON 落地

| INV | spec 要求 | 设计落地 |
|---|---|---|
| INV-F15-1 | read-only on SKILL.md + KS | T2 composer 仅调 `Path.read_text` + `KnowledgeStore.list_entries(KnowledgeType.STYLE)`; 不写不删 |
| INV-F15-2 | 写仅 packs/<target>/agents/ + .garage/agent-compose/ + platform.json 字段级 | T3 CLI 唯一写盘点; T1 template_generator 不写 |
| INV-F15-3 | compose 不动 pack.json agents[] | T3 CLI 不调 pack.json mutation; sentinel 测试: `tests/agent_compose/test_compose_no_pack_json_mutation.py` |
| INV-F15-4 | F003-F014 既有 schema 字节级 | sentinel: `git diff` should be 0 on `src/garage_os/types/__init__.py` etc. |
| INV-F15-5 | F011 既有 3 个 agent byte 不变 | sentinel 测试: `tests/agent_compose/test_f011_agents_unchanged.py` byte hash 检查; BDD 8.4 用 `demo-overwrite-agent` |

| CON | 设计守门 |
|---|---|
| CON-1501 | T2 composer 不修改 F003-F014 任何 method 签名 |
| CON-1502 | T1-T4 全 stdlib (re, pathlib, dataclasses, json) — 单测 sentinel: `git diff main..HEAD -- pyproject.toml uv.lock` = 0 |
| CON-1503 | T3 `_agent_compose` echo 提示 "Manually update pack.json"; sentinel byte test |
| CON-1504 | T1 template_generator 严格 7-section schema (Cr-2 r2 收窄); 单测每段验证 |
| CON-1505 | T3 `recall_workflow` / `skill_suggest` / `recommend` / `agent compose` handler 独立; AST sentinel `tests/agent_compose/test_no_sibling_import.py` |

## 9. 关键 dataclass

```python
# agent_compose/types.py

@dataclass
class AgentDraft:
    name: str  # kebab-case agent name
    description: str  # ≥ 50 chars, 含 适用 + 不适用
    target_pack: str  # default "garage"
    body: str  # full agent.md draft string (frontmatter + sections)

@dataclass
class ComposeResult:
    draft: AgentDraft  # always populated (even when missing_skills > 0)
    missing_skills: list[str]  # skills not found in any packs/<id>/skills/
    style_count: int  # number of STYLE entries used
    target_pack_exists: bool  # for library callers
```

## 10. 风险 + 缓解

| RSK | 描述 | 缓解 |
|---|---|---|
| RSK-D15-1 | template 质量浅 (只是 skill name 拼接) | T1 template 标 `<!-- AI-generated draft, refine via hf-test-driven-dev -->`; T3 CLI echo 提示 |
| RSK-D15-2 | INV-F15-5 误破 (不慎修改 F011 既有 agent) | T4 sentinel: F011 既有 3 个 agent byte hash; CI 红 alarm |
| RSK-D15-3 | hv-analysis 多行 description 切分错 | T1 _extract_skill_summary 单测覆盖单行/多行/句号/无句号 |
| RSK-D15-4 | 用户 compose 后忘 update pack.json | T3 echo 提示 + AGENTS 文档化 (与 F013-A skill promote 同模式) |

## 11. 验证

- 单测: 36 测试 (T1: 10, T2: 12, T3: 10, T4: 4)
- Manual smoke (T4): 4 tracks
  - Track 1: 0 skills → exit 1
  - Track 2: 3 skills + 0 STYLE → compose + Style Alignment placeholder
  - Track 3: 3 skills + 2 STYLE entries → compose + Style Alignment 列出 entries
  - Track 4: 同名 demo-overwrite-agent → prompt overwrite (Cr-1 r2 用 demo 名)
- Sentinels:
  - `test_f011_agents_unchanged.py` (INV-F15-5 byte hash)
  - `test_compose_no_pack_json_mutation.py` (CON-1503 byte hash)
  - `test_no_sibling_import.py` (CON-1505 AST)
- ruff baseline diff = 0 (与 F013-A / F014 同预算)

---

> **本文档是 design r1**, 待 hf-design-review (subagent 派发).
