# Contributing to garage-agent

Thanks for your interest in `garage-agent`. This project exists to give solo creators a portable, file-first home for agent skills, knowledge, and experience. Contributions that strengthen that mission are very welcome.

This document covers the conventions you need to know before opening a PR.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## Before you start

`garage-agent` is built around a few non-negotiable principles, captured in [`docs/soul/`](docs/soul/):

- **Local-first ownership** — data lives in the user's git repo, never in a service we control
- **Host portability** — never lock users into one host (Claude Code / Cursor / OpenCode are first-class today)
- **Progressive enhancement** — day one must work without a setup cliff
- **Transparent and auditable** — files, conventions, and explicit `--yes` / `--force` opt-ins over hidden automation
- **Human in charge** — destructive or shareable operations are always opt-in

If a change conflicts with these, please open a discussion first.

## How to contribute

### File an issue first if the change is non-trivial

For bugs, please include:

- `garage --version` (or commit SHA), Python version, OS
- Steps to reproduce
- Expected vs actual behavior
- Relevant files under `.garage/` (sanitized) if the bug is data-shaped

For features, please link to the relevant section of [`docs/soul/`](docs/soul/) (Belief / Promise / Stage) that the feature advances.

### Small fixes are welcome as direct PRs

Typo fixes, link fixes, doc clarifications, and small bug fixes can skip the issue step.

### Larger changes follow the AHE / HF workflow

This repo dogfoods its own [HarnessFlow](packs/coding/skills/using-hf-workflow/SKILL.md) workflow:

1. Spec under [`docs/features/Fxxx-*.md`](docs/features/) (use `hf-specify`)
2. Design under [`docs/designs/<date>-*-design.md`](docs/designs/) (use `hf-design`)
3. Tasks under [`docs/tasks/`](docs/tasks/) (use `hf-tasks`)
4. Implementation + tests (use `hf-test-driven-dev`)
5. Self code review under [`docs/reviews/`](docs/reviews/) (use `hf-code-review`)
6. Finalize approval under [`docs/approvals/`](docs/approvals/) (use `hf-finalize`)

For a 30-second tour, read [`packs/coding/README.md`](packs/coding/README.md).

## Development setup

Requirements: Python 3.11+ and either [uv](https://github.com/astral-sh/uv) or [poetry](https://python-poetry.org/).

```bash
git clone https://github.com/hujianbest/garage-agent.git
cd garage-agent

# editable install
uv pip install -e .          # or: poetry install

# bootstrap the agent skill mount used by some IDE / cloud agents
bash scripts/setup-agent-skills.sh

# run all tests (currently 1044 passing in ~3 min)
pytest tests/ -q

# lint + types
ruff check src/ tests/
mypy src/
```

## Project layout

| Path | Purpose |
|---|---|
| [`packs/`](packs/) | Distributable packs (single source of truth for skills + agents) |
| [`src/garage_os/`](src/garage_os/) | Python runtime: types, storage, runtime, knowledge, adapter, tools, platform |
| [`tests/`](tests/) | Mirrors `src/garage_os/` module layout; sentinel + integration + security tests |
| [`docs/`](docs/) | Soul docs, feature specs, designs, reviews, approvals, planning, guides |
| [`AGENTS.md`](AGENTS.md) | Agent-facing conventions (the whole file is loaded into agent context) |
| [`RELEASE_NOTES.md`](RELEASE_NOTES.md) | Per-cycle user-visible changes |

## Conventions

### Skill writing

Every new skill must follow [`docs/principles/skill-anatomy.md`](docs/principles/skill-anatomy.md):

- `description` is the classifier; keep it concrete
- The main `SKILL.md` stays short (`references/` carries depth)
- Boundaries (when **not** to use) must be explicit

### Pack conventions

See [`packs/README.md`](packs/README.md) for the `pack.json` schema and the contract between a pack and a host.

### Tests

- Mirror `src/garage_os/` layout under `tests/`
- Use `tmp_path` fixture; never write to project `.garage/` from a test
- Integration tests in `tests/integration/`, security in `tests/security/`, sentinel / baseline in their own files (e.g. `tests/sync/test_baseline_no_regression.py`)
- New code should not regress the baseline; new tests are encouraged

### Commits

- Use conventional, scoped messages; cycle work uses `f0xx(stage): summary`
- One logical change per commit
- Don't force-push or amend after others have pulled

### File / data touch boundaries

The runtime is built around strict touch boundaries (e.g. `pack uninstall` only touches `packs/<id>/`, `host-installer.json`, and host directories — never `knowledge/`, `experience/`, `sessions/`, or `contracts/`). Please respect existing boundaries; if you need to broaden one, raise it in the spec / design first.

## PR checklist

Before requesting review, please verify:

- [ ] `pytest tests/ -q` passes (≥ current baseline, currently 1044)
- [ ] `ruff check src/ tests/` clean
- [ ] `mypy src/` clean
- [ ] If you added a skill, it follows `docs/principles/skill-anatomy.md`
- [ ] If you changed packs content, dogfood baseline tests still pass (`tests/adapter/installer/test_dogfood_invariance_F009.py` + sister tests; refresh baseline JSON if intentional)
- [ ] AGENTS.md / RELEASE_NOTES.md / README.md updated if user-visible behavior changed

## Reporting security issues

Please do **not** open a public issue for security-sensitive bug reports. Follow [SECURITY.md](SECURITY.md) instead.

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
