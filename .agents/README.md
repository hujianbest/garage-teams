# `.agents/skills/` — Cloud Agent Runtime Skill Mount Point

This directory exists so cloud-agent runtimes that resolve skills under `.agents/skills/<name>/SKILL.md` can find the canonical pack-owned skills without duplicating files.

## Why

`packs/` is the **single source of truth** for all distributable skills (see `packs/README.md` and AGENTS.md "Packs & Host Installer"). However, certain agent harness loaders historically resolved skills under `.agents/skills/`. F008 (`5a95b45`) removed `.agents/skills/` to prevent duplication, but cloud-agent runtimes that hard-code the `.agents/skills/<name>` lookup path then could not load the 24 `hf-*` skills, breaking the HF workflow.

## How

Each entry under `.agents/skills/` is a **relative symlink** into `packs/<pack-id>/skills/<skill-name>/`:

| Skill | Target |
|---|---|
| 24 × `hf-*` + `using-hf-workflow` | `../../packs/coding/skills/<name>` |
| `find-skills`, `writing-skills` | `../../packs/garage/skills/<name>` |
| `write-blog/blog-writing`, `humanizer-zh`, `hv-analysis`, `khazix-writer` | `../../../packs/writing/skills/<name>` |

This keeps the canonical content under `packs/` (so `packs/README.md`, `garage init`, `pack publish`, etc. all work unchanged) while making the same files reachable via `.agents/skills/<name>/SKILL.md`.

## Why not commit the symlinks?

`.agents/skills/` is in `.gitignore` (next to `.cursor/` and `.claude/` per F008 ADR-D8-2 dogfood rule):

- `packs/` is the canonical source — committing symlinks duplicates the dependency edge in version control
- Cross-platform: relative symlinks behave inconsistently on Windows; new contributors regenerate locally
- Cloud agents regenerate on every fresh clone via `scripts/setup-agent-skills.sh`

## Regenerate

```bash
bash scripts/setup-agent-skills.sh
```

If you add or rename a skill under `packs/<pack>/skills/`, re-run the script (or follow the manual `ln -sf` invocations inside it) to refresh the mount.
