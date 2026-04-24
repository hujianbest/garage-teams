# garage-agent

**English** | [中文](README.zh-CN.md)

`garage-agent` is a local-first home for agent skills, knowledge, and experience.

It is built for solo creators who want agent capability that starts small, grows with real work, and stays portable across hosts instead of being trapped inside one tool, one session, or one machine.

- Keep your agent capability in the repo, not in a closed cloud silo
- Move across hosts without throwing away accumulated skills and context
- Start with structured workflows and grow into runtime, memory, and reuse
- Keep humans in charge of architecture, scope, publishing, deployment, and destructive actions

## Why the name

A garage is where things start before they are polished: close to the work, shaped by iteration, and able to grow into something real. `garage-agent` carries that meaning. It is the place where your agent capability can be built by hand, compounded over time, and eventually leave the garage without losing its identity.

## What it is

`garage-agent` currently combines three layers:

- Structured AHE workflow packs for product insight and coding
- A file-first runtime foundation for sessions, knowledge, experience, and tool execution
- Repo-native conventions that both humans and agents can read, inspect, and evolve

The goal is not to hide the work behind a black box. The goal is to give your agent a stable home base that can accumulate context, artifacts, and habits over time.

## What it is not

- Not a SaaS product
- Not a host-locked wrapper around a single AI tool
- Not a generic all-in-one AI framework
- Not full autopilot that removes human judgment from important decisions

## Core Principles

- Local-first ownership: your data stays in the repo and remains readable even if the project stops moving
- Host portability: the system may prefer one host today, but it should not depend on one host forever
- Progressive enhancement: day one should be usable without a setup cliff
- Transparent and auditable behavior: files, artifacts, and conventions should explain what the system knows and why
- Human in charge: the system can assist and automate, but people keep the steering wheel

## What works today

`garage-agent` is still early, but the repository already includes:

- AHE workflow skills under [packs/product-insights/skills/](packs/product-insights/skills/) and [packs/coding/skills/](packs/coding/skills/)
- An early Python runtime package, currently named `garage-os`, under [src/garage_os/](src/garage_os/)
- A `garage` CLI with `init`, `status`, `run`, `recommend`, `knowledge search`, `knowledge list`, `knowledge add`, `knowledge edit`, `knowledge show`, `knowledge delete`, `knowledge link`, `knowledge graph`, `experience add`, `experience show`, `experience delete`, and `memory review`
- File-first runtime data under [.garage/](.garage/)
- Approved Phase 1 direction in [docs/features/F001-garage-agent-operating-system.md](docs/features/F001-garage-agent-operating-system.md) plus runtime guides in [docs/guides/garage-os-user-guide.md](docs/guides/garage-os-user-guide.md) and [docs/guides/garage-os-developer-guide.md](docs/guides/garage-os-developer-guide.md)

## Quick Start Paths

### 1. Explore the workflow packs

- If you are starting from a vague idea, begin with [packs/product-insights/skills/using-ahe-product-workflow/SKILL.md](packs/product-insights/skills/using-ahe-product-workflow/SKILL.md)
- If you already know what you want to build, begin with [packs/coding/skills/using-ahe-workflow/SKILL.md](packs/coding/skills/using-ahe-workflow/SKILL.md)
- If you want the pack overviews first, read [packs/product-insights/skills/README.md](packs/product-insights/skills/README.md) and [packs/coding/skills/README.md](packs/coding/skills/README.md)

### 2. Try the runtime CLI

From the repository root:

```bash
uv pip install -e .
garage init
garage status
```

If you already have Claude Code CLI installed and authenticated, you can also explore the current execution surface with `garage run <skill-name>`. The runtime is still early, so treat host-backed skill execution as an evolving path rather than a finished platform experience.

### 3. Read the worldview and system docs

- Soul: [docs/soul/manifesto.md](docs/soul/manifesto.md), [docs/soul/user-pact.md](docs/soul/user-pact.md), [docs/soul/design-principles.md](docs/soul/design-principles.md), [docs/soul/growth-strategy.md](docs/soul/growth-strategy.md)
- System spec: [docs/features/F001-garage-agent-operating-system.md](docs/features/F001-garage-agent-operating-system.md)
- User guide: [docs/guides/garage-os-user-guide.md](docs/guides/garage-os-user-guide.md)
- Developer guide: [docs/guides/garage-os-developer-guide.md](docs/guides/garage-os-developer-guide.md)

## Repository Map

| Path | Purpose |
| --- | --- |
| [packs/](packs/) | Reference workflow packs, pack-local docs, and related agent assets |
| [src/garage_os/](src/garage_os/) | Runtime package and CLI implementation |
| [.garage/](.garage/) | Workspace runtime state for sessions, knowledge, experience, contracts, and config |
| [docs/](docs/) | Soul docs, specs, guides, reviews, and design artifacts |
| [tests/](tests/) | Module, integration, compatibility, and security coverage |
| [AGENTS.md](AGENTS.md) | Agent-facing conventions and Garage OS developer reference |

## Roadmap

The following is a gap analysis between **what is built today** and the vision in [docs/soul/manifesto.md](docs/soul/manifesto.md). It exists to anchor what future cycles should pick up.

### Snapshot

```
              vision completeness
              ┌─────────────────────────────────┐
Belief 1 Data is yours       │█████████████████████████████████│ 5/5  ✅
Belief 2 Host portability    │███████████████████              │ 3/5  ⚠️ no plug-in point
Belief 3 Progressive enhance │█████████████████████████████████│ 5/5  ✅
Belief 4 Human + machine     │███████████████████              │ 3/5  ⚠️ flywheel not closed
Belief 5 Shareable           │████████████                     │ 2/5  ⚠️ git clone only
              └─────────────────────────────────┘

Promise ① "becomes your agent in seconds"     ⚠️ 3/5  ← P0 no auto context handoff
Promise ② "knows your coding style"           ❌ 0/5  ← P1 style dimension missing
Promise ③ "remembers last month's decisions"  ⚠️ 4/5  ← P0 recall is pull, not push
Promise ④ "calls 50 accumulated skills"       ✅ 5/5
Promise ⑤ "knows how to write your blog"      ✅ 5/5

Stage 1 Toolbox    ████████████████████ 100%
Stage 2 Memory     ████████████          60%   ← session context handoff missing
Stage 3 Craftsman  █                      5%   ← agent composition + skill mining ~0
Stage 4 Ecosystem  ░                      0%
```

### Gaps and priority

#### P0 — hard blockers on delivering the vision

1. **Automatic context handoff pipeline**: when a user opens a new conversation in their host, `.garage/knowledge/` and `.garage/experience/` are not loaded by the host. The whole memory subsystem (F003-F006) is invisible in the user's real workflow. Likely shape: each host adapter exposes a context-injection path (Claude Code → `CLAUDE.md`, Cursor → `.cursor/rules/`, OpenCode → equivalent), driven by `garage sync` that compiles top-N knowledge + recent experience into that file.
2. **Host session ingestion**: F003's extraction trigger is `SessionManager.archive_session()`, but day-to-day conversations in Cursor / Claude Code never become Garage sessions, so the "the more you use it, the stronger it gets" flywheel never closes. Likely shape: `garage session import --from <host-history>`, or a host-side rule that triggers archival when a conversation ends.

#### P1 — vision completeness

3. **Personal style / preference dimension**: the 4 candidate types (decision / pattern / solution / experience_summary) have no style dimension, so promise ② "knows your coding style" is 0% implemented.
4. **Agent composition layer is empty**: `packs/garage/` ships 1 placeholder `garage-sample-agent`. The "code-review agent / blog-writing agent" pattern from the vision has not started. This is the core Stage 3 capability.
5. **Pack sharing flow**: no `garage pack install <git-url>` / `garage pack publish` / knowledge anonymized export / cross-user merge tooling. Belief 5 "shareable" only works via `git clone` today.

#### P2 — long-term debt

6. **Host extension point is not pluggable**: `HOST_REGISTRY` is a hardcoded literal table; the fourth host requires editing Garage source.
7. **Cross-device consistency relies on manual git**: no `garage sync` to handle git push/pull + conflict merging.
8. **Memory flywheel lacks the push side**: the whole loop is pull today; the "system proactively suggests 'this pattern could become a skill'" signal in growth-strategy has no implementation path.

### Recommended path

If only one thing can be done next, do **P0-1 (automatic context handoff)** — it has the highest leverage, simultaneously revives promises ① ② ③, and turns the existing memory subsystem from dormant into something hosts see in every conversation. Add **P0-2 (host session ingestion)** after that to keep feeding the context that P0-1 injects.

P1 items come after P0; P2 items are long-term debt and can wait until their triggering signals arrive.

Scoring rationale: see [docs/soul/manifesto.md](docs/soul/manifesto.md) + [docs/soul/growth-strategy.md](docs/soul/growth-strategy.md) + [RELEASE_NOTES.md](RELEASE_NOTES.md) F001–F008.

## Open Source Direction

`garage-agent` is being prepared for public open-source release.

- Public project name: `garage-agent`
- Current Python package and CLI names in the repo: `garage-os` and `garage`
- A formal `LICENSE` file has not been added yet, so reuse terms are not final
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` are also still to be defined
- The most useful contributions right now are workflow quality, portability, docs clarity, runtime hardening, and examples
