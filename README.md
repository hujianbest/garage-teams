# garage-agent

**English** | [中文](README.zh-CN.md)

[![Tests](https://github.com/hujianbest/garage-agent/actions/workflows/test.yml/badge.svg)](https://github.com/hujianbest/garage-agent/actions/workflows/test.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code of Conduct](https://img.shields.io/badge/code%20of%20conduct-Contributor%20Covenant-ff69b4.svg)](CODE_OF_CONDUCT.md)

`garage-agent` is a local-first home for agent skills, knowledge, and experience.

It is built for solo creators who want agent capability that starts small, grows with real work, and stays portable across hosts instead of being trapped inside one tool, one session, or one machine.

- Keep your agent capability in the repo, not in a closed cloud silo
- Move across hosts without throwing away accumulated skills and context
- Start with structured workflows and grow into runtime, memory, and reuse
- Keep humans in charge of architecture, scope, publishing, deployment, and destructive actions

## Why the name

A garage is where things start before they are polished: close to the work, shaped by iteration, and able to grow into something real. `garage-agent` carries that meaning. It is the place where your agent capability can be built by hand, compounded over time, and eventually leave the garage without losing its identity.

## What it is

`garage-agent` currently combines four layers:

- **Distributable packs** of skills + agents under [`packs/`](packs/) (Garage Coding, Garage Writing, Garage core)
- A **file-first runtime** for sessions, knowledge, experience, candidate review, and tool execution under [`src/garage_os/`](src/garage_os/)
- A **host installer + sync layer** that materializes packs into Claude Code, Cursor, OpenCode (project- or user-scoped), pushes top-N memory into each host's context surface, and ingests host conversation history back into Garage
- A **pack lifecycle** (`install` / `ls` / `uninstall` / `update` / `publish`) plus anonymized knowledge export, so capability can leave one repo and land in another

The goal is not to hide the work behind a black box. The goal is to give your agent a stable home base that can accumulate context, artifacts, and habits over time, then share what is worth sharing.

## What it is not

- Not a SaaS product
- Not a host-locked wrapper around a single AI tool
- Not a generic all-in-one AI framework
- Not full autopilot that removes human judgment from important decisions

## Core Principles

- **Local-first ownership**: your data stays in the repo and remains readable even if the project stops moving
- **Host portability**: prefer one host today, but never depend on one host forever — three first-class adapters today (Claude Code, Cursor, OpenCode)
- **Progressive enhancement**: day one should be usable without a setup cliff
- **Transparent and auditable behavior**: files, artifacts, and conventions explain what the system knows and why
- **Human in charge**: the system can assist and automate, but people keep the steering wheel — destructive / shareable operations are opt-in (`--yes` / `--anonymize` / `--force` are explicit)

## What works today (cycles F001 through F014)

Through 14 closed delivery cycles the repository now provides:

| Cycle | Capability |
|---|---|
| F001 | garage-agent foundation (`garage init` / `status` / `run` / contracts / VersionManager) |
| F002 | Session manager + StateMachine + ErrorHandler |
| F003 | Memory auto-extraction (signals → candidates → review queue) |
| F004 | Memory v1.1 (KnowledgeStore + ExperienceIndex consolidation) |
| F005 | Knowledge authoring CLI (`knowledge add` / `edit` / `show` / `delete`) |
| F006 | Recall + knowledge graph (`knowledge search` / `link` / `graph`) |
| F007 | Garage Packs + Host Installer (`garage init --hosts claude,cursor,opencode`) |
| F008 | Coding Pack + Writing Pack + dogfood layout |
| F009 | Multi-scope install (`--scope project|user` + per-host override; manifest schema 2 with auto-migration) |
| F010 | Memory Sync (`garage sync`) + Host Session Ingest (`garage session import --from <host>`) |
| F011 | `KnowledgeType.STYLE` + production agents (`code-review-agent` / `blog-writing-agent`) + `garage pack install <git-url>` + `pack ls` |
| F012 | Pack lifecycle completion (`pack uninstall` / `pack update` / `pack publish`) + `knowledge export --anonymize` + F009 carry-forward (VersionManager registry) |
| F013-A | Skill Mining Push (`garage skill suggest` / `garage skill promote`) |
| F014 | Workflow Recall (`garage recall workflow`) + `hf-workflow-router` step 3.5 historical advisory |

Concrete deliverables:

- **AHE / HF workflow skills** under [`packs/coding/skills/`](packs/coding/skills/) (24 `hf-*` skills + `using-hf-workflow`) and [`packs/writing/skills/`](packs/writing/skills/) (5 writing skills)
- **Production agents** under [`packs/garage/agents/`](packs/garage/agents/): `code-review-agent`, `blog-writing-agent`, `garage-sample-agent`
- A **Python runtime** package `garage-agent` (import path: `garage_os`) under [`src/garage_os/`](src/garage_os/) with ~1045 passing tests
- A **`garage` CLI** covering: `init`, `status`, `run`, `recommend`, `recall workflow`, `sync`, `session import`, `memory review`, `skill suggest`, `skill promote`; knowledge subcommands `knowledge search`, `knowledge list`, `knowledge add`, `knowledge edit`, `knowledge show`, `knowledge delete`, `knowledge link`, `knowledge graph`, `knowledge export`; experience subcommands `experience add`, `experience show`, `experience delete`; pack lifecycle `pack install`, `pack ls`, `pack uninstall`, `pack update`, `pack publish`
- File-first runtime data under [`.garage/`](.garage/) (sessions, knowledge entries with YAML front matter, experience records, sync manifest, host installer manifest, skill suggestions, workflow recall cache)
- Specs and reviews for every cycle under [`docs/features/`](docs/features/), [`docs/designs/`](docs/designs/), [`docs/reviews/`](docs/reviews/), [`docs/approvals/`](docs/approvals/)

## Quick Start Paths

### 1. Explore the workflow packs

- If you are starting from a vague idea, run [`packs/coding/skills/hf-product-discovery/SKILL.md`](packs/coding/skills/hf-product-discovery/SKILL.md)
- If you already know what you want to build, start with [`packs/coding/skills/using-hf-workflow/SKILL.md`](packs/coding/skills/using-hf-workflow/SKILL.md) and let `hf-workflow-router` route to the right node
- If you want pack overviews first, read [`packs/README.md`](packs/README.md), [`packs/coding/README.md`](packs/coding/README.md), [`packs/writing/README.md`](packs/writing/README.md), and [`packs/garage/README.md`](packs/garage/README.md)

### 2. Try the runtime CLI

From the repository root:

```bash
# Option A: editable install (any venv)
uv pip install -e .

# Option B: uv-managed env (installs runtime + dev tools from uv.lock)
uv sync

# Initialize Garage in this project + materialize Garage Coding/Writing/Garage packs
# into your host directories. --hosts accepts any combination of claude,cursor,opencode.
garage init --hosts claude,cursor --yes

# Inspect state
garage status

# Push top-N knowledge + recent experience into each host's context surface
# (CLAUDE.md / .cursor/rules/garage-context.mdc / .opencode/AGENTS.md)
garage sync --hosts claude,cursor

# Pull host conversation history back into Garage sessions for memory extraction
garage session import --from claude --all

# Review repeated patterns that Garage can turn into skill drafts
garage skill suggest --rescan

# Ask for historically successful workflow paths for similar work
garage recall workflow --problem-domain cli-design
```

For first-time contributors who need the cloud-agent skill mount, also run:

```bash
bash scripts/setup-agent-skills.sh    # regenerates .agents/skills/ symlinks → packs/
```

If you already have Claude Code CLI installed and authenticated, you can also run individual skills with `garage run <skill-name>`. The runtime is still early; treat host-backed skill execution as an evolving path rather than a finished platform experience.

### 3. Share or pull packs

```bash
# Install someone else's pack from a git URL
garage pack install https://github.com/<user>/<their-pack>.git

# List installed packs (shows source_url for installed-from-URL packs, "local" otherwise)
garage pack ls

# Update a previously installed pack from its source_url
garage pack update <pack-id> --yes

# Publish your pack to a fresh / existing git remote (sensitive scan + force-push prompt)
garage pack publish <pack-id> --to https://github.com/<you>/<pack-name>.git --yes

# Cleanly remove a pack from packs/ and from every host directory
garage pack uninstall <pack-id> --yes

# Export knowledge as an anonymized tarball (front matter preserved, body redacted)
garage knowledge export --anonymize
```

### 4. Read the worldview and system docs

- Soul: [`docs/soul/manifesto.md`](docs/soul/manifesto.md), [`docs/soul/user-pact.md`](docs/soul/user-pact.md), [`docs/soul/design-principles.md`](docs/soul/design-principles.md), [`docs/soul/growth-strategy.md`](docs/soul/growth-strategy.md)
- System spec: [`docs/features/F001-garage-agent-operating-system.md`](docs/features/F001-garage-agent-operating-system.md)
- User guide: [`docs/guides/garage-agent-user-guide.md`](docs/guides/garage-agent-user-guide.md)
- Skill anatomy (mandatory for any new skill): [`docs/principles/skill-anatomy.md`](docs/principles/skill-anatomy.md)

## Repository Map

| Path | Purpose |
| --- | --- |
| [`packs/`](packs/) | Distributable packs of skills + agents (single source of truth: `coding`, `writing`, `garage`, `search`) |
| [`src/garage_os/`](src/garage_os/) | Runtime: types, storage, runtime (session manager + state machine + skill executor), knowledge, adapter (host installer + sync), tools, platform (VersionManager) |
| [`.agents/skills/`](#agents-skills-mount) | Cloud-agent skill mount (relative symlinks into `packs/`; not committed — regenerate via `scripts/setup-agent-skills.sh`) |
| [`.garage/`](.garage/) | Workspace runtime state for sessions, knowledge, experience, sync manifest, host installer manifest, contracts, config |
| [`docs/`](docs/) | Soul docs, feature specs (`features/`), designs (`designs/`), reviews (`reviews/`), approvals (`approvals/`), planning (`planning/`), guides, principles, manual smoke walkthroughs |
| [`tests/`](tests/) | ~1045 unit + integration + compatibility + security + sentinel tests; mirrors `src/garage_os/` module layout |
| [`AGENTS.md`](AGENTS.md) | Agent-facing conventions + garage-agent development notes + F009-F014 feature usage |
| [`RELEASE_NOTES.md`](RELEASE_NOTES.md) | Per-cycle user-visible changes (F001 → F014) |

### `.agents/skills/` mount

Some cloud-agent runtimes resolve skills under `.agents/skills/<name>/SKILL.md`. To keep `packs/` as the single source of truth without duplication, `.agents/skills/` is a tree of relative symlinks into `packs/<pack-id>/skills/`. It is `.gitignore`-d and regenerated locally via:

```bash
bash scripts/setup-agent-skills.sh
```

See [`.agents/README.md`](.agents/README.md) for details.

## Roadmap

The following is a gap analysis between **what is built today** and the vision in [`docs/soul/manifesto.md`](docs/soul/manifesto.md). It exists to anchor what future cycles should pick up. Updated after F012 (2026-04-25).

### Snapshot

```
              vision completeness
              ┌─────────────────────────────────┐
Belief 1 Data is yours       │█████████████████████████████████│ 5/5  ✅
Belief 2 Host portability    │█████████████████████████        │ 4/5  ⚠️ 3 first-class hosts; 4th still requires source edit
Belief 3 Progressive enhance │█████████████████████████████████│ 5/5  ✅
Belief 4 Human + machine     │█████████████████████████████████│ 5/5  ✅ flywheel closed (sync ↔ ingest ↔ memory)
Belief 5 Shareable           │█████████████████████████████████│ 5/5  ✅ install / update / publish / anonymized export
              └─────────────────────────────────┘

Promise ① "becomes your agent in seconds"     ✅ 5/5
Promise ② "knows your coding style"           ✅ 5/5  ← KnowledgeType.STYLE + production agents
Promise ③ "remembers last month's decisions"  ✅ 5/5  ← garage sync pushes; garage session import pulls
Promise ④ "calls 50 accumulated skills"       ✅ 5/5
Promise ⑤ "knows how to write your blog"      ✅ 5/5

Stage 1 Toolbox    ████████████████████ 100%
Stage 2 Memory     ████████████████████ 100%   ← F010 closes the loop
Stage 3 Craftsman  █████████████         65%   ← F011 production agents shipped; skill mining still manual
Stage 4 Ecosystem  ████████              40%   ← F012 lifecycle complete; community discovery / signature still F013+
```

### Gaps and priority (F013+ candidates)

#### P1 — flywheel polish

1. **Real 3-way merge for `pack update --preserve-local-edits`** (D-1211): today the flag warns and overwrites; future work resolves local edits against upstream changes
2. **Skill mining push signal**: the system can already extract knowledge candidates, but it does not yet propose "this pattern could become a skill"; needs a candidate-promotion path from `.garage/memory/` into `packs/<pack>/skills/`
3. **Cross-device sync**: `garage sync` writes to hosts; cross-machine git-aware merging (D-707 carry-forward) still relies on manual `git push`

#### P2 — community / supply-chain

4. **Pluggable host registry** (carry-forward from F007 D-705): the fourth host adapter still requires editing `HOST_REGISTRY` literal
5. **Pack signature / GPG** (D-1212): publish + install do not yet verify pack provenance
6. **Monorepo packs** (D-1213): `pack install` assumes one `pack.json` at the repo root
7. **Pack discovery** (D-1214): no `garage pack search` or pack registry yet
8. **Reverse import + experience export** (D-1215): mirror of `knowledge export --anonymize` for experience records and import-from-tarball
9. **Publish auto-runs `hf-doc-freshness-gate`** (D-1216): close the loop between local docs/spec freshness and outbound shareability

### Recommended next cycle

With Beliefs 1-5 and Promises ①-⑤ all at 5/5 after F012, the highest-leverage next push is **Stage 3 skill mining** — turn the existing extraction pipeline into a "the system suggests a new skill from your patterns" signal. After that, **Stage 4 community / supply-chain** (D-1214 pack search + D-1212 signature) opens the door to a public pack ecosystem.

Scoring rationale: see [`docs/soul/manifesto.md`](docs/soul/manifesto.md), [`docs/soul/growth-strategy.md`](docs/soul/growth-strategy.md), [`RELEASE_NOTES.md`](RELEASE_NOTES.md) (F001-F014), and [`docs/planning/`](docs/planning/).

## Open Source

`garage-agent` is open source under the [Apache 2.0 License](LICENSE).

- **Public project name**: `garage-agent`
- **PyPI distribution name**: `garage-agent` (`pip install garage-agent`)
- **Python import path**: `import garage_os` (kept stable — same pattern as Pillow / `import PIL`)
- **CLI binary**: `garage`
- **License**: [Apache-2.0](LICENSE) — chosen for explicit patent grant + downstream-friendliness
- **Contributing**: read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a non-trivial PR
- **Code of Conduct**: [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) (Contributor Covenant 2.1)
- **Security**: report vulnerabilities via [`SECURITY.md`](SECURITY.md) — please do not open public issues for security bugs
- **CI**: GitHub Actions runs the full `pytest` suite (~1045 tests) on Python 3.11 + 3.12 for every push and PR

The most useful contributions right now are workflow quality, host portability, docs clarity, runtime hardening, and real-world examples.
