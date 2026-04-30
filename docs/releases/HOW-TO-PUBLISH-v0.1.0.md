# How to publish v0.1.0

> Cloud agents have a read-only `gh` CLI and cannot publish a GitHub release. This runbook gives the maintainer the exact one-shot command sequence on **WSL Ubuntu 24.04 / Python 3.12** (default Garage development environment).
>
> Other environments (macOS, native Linux, conda, pyenv-shim'd `python`) are very similar — see § "Adapting to other environments" at the bottom if `python` resolves to a non-system interpreter.

## Current release state

- PR [#41](https://github.com/hujianbest/garage-agent/pull/41) (release-prep: legal + community + CI + PyPI metadata + sentinel refresh) — **MERGED** at squash commit `3e96d14` on 2026-04-29.
- PR [#42](https://github.com/hujianbest/garage-agent/pull/42) (`packs/coding/` v0.3.0 → v0.4.0 reverse-sync from harness-flow v0.1.0) — **MERGED** at merge commit `3a7565d` on 2026-04-29.
- PR [#43](https://github.com/hujianbest/garage-agent/pull/43) (release runbook + body) — **MERGED** at merge commit `d743231` on 2026-04-29.
- **PRs #44–#48** (build / pytest / CLI fixes that make the release reproducible on WSL Ubuntu) — **MERGED** on 2026-04-29:
  - [#44](https://github.com/hujianbest/garage-agent/pull/44) `fix(test): pytest pythonpath so plain pytest finds garage_os`
  - [#45](https://github.com/hujianbest/garage-agent/pull/45) `fix(test): fail fast when pytest env lacks filelock/PyYAML`
  - [#46](https://github.com/hujianbest/garage-agent/pull/46) `fix(build): PEP 621 + uv.lock so uv sync installs dependencies`
  - [#47](https://github.com/hujianbest/garage-agent/pull/47) `fix(test): subprocess PYTHONPATH for CLI smoke + NFR803 on slow FS`
  - [#48](https://github.com/hujianbest/garage-agent/pull/48) `fix(cli): FR-508 clock monkeypatch for knowledge/experience add`

The `v0.1.0` git tag was originally pushed at `d743231` (PR #43 merge) **before** PRs #44–#48 landed, so on that tag plain `pytest tests/ -q` does not start (it raises `ModuleNotFoundError: garage_os`). **No public release was created from the original tag** — no GitHub release, no PyPI upload — so we move the tag forward to current `main` HEAD before publishing. See § "Step 2 — Move the v0.1.0 tag to current main HEAD" below.

## Prerequisites (WSL Ubuntu 24.04, default Garage dev env)

You only need three tools:

| Tool | Why | How to install |
|---|---|---|
| **`uv`** | Resolves `pyproject.toml` + `uv.lock`, runs tests, builds in an isolated venv (no `pip install -e` needed) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` then `export PATH="$HOME/.local/bin:$PATH"` |
| **`gh`** (GitHub CLI, write-authenticated) | Push tag, create release, edit release body | `sudo apt install gh && gh auth login` |
| **`git`** | Standard | already installed |

> Ubuntu 24.04 ships Python 3.12 with PEP 668 ("externally-managed-environment"). Do **not** `pip install` into system Python. Use `uv` (recommended below) or `pipx`/venv. The runbook below assumes `uv`.

Verify:

```bash
uv --version       # uv 0.5+ recommended
gh --version       # gh 2.40+
git --version
python3 --version  # Python 3.11 or 3.12
```

## Step 1 — Sync to main HEAD and verify tests are green

```bash
cd /path/to/garage-agent
git checkout main
git pull origin main
git log --oneline -5
# Expected HEAD includes PR #48 merge commit:
#   84a7591  Merge pull request #48 ...

# Sync runtime + dev deps from uv.lock into a project-local .venv
uv sync

# Run the full test suite (uv run picks up the .venv automatically)
uv run pytest tests/ -q --tb=short
# Expected last line:
#   ===== 1045 passed in ~150s =====
```

If this fails, **stop**. Do not tag. The release artifact must be reproducible by anyone cloning the repo.

Verify the rest of the repo state:

```bash
# All 4 release-prep doc files
ls LICENSE CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md
ls .github/workflows/test.yml
ls docs/releases/v0.1.0.md docs/releases/HOW-TO-PUBLISH-v0.1.0.md

# packs/coding pinned at 0.4.0 (from PR #42)
grep '"version"' packs/coding/pack.json
# expected:   "version": "0.4.0",
```

## Step 2 — Move the v0.1.0 tag to current main HEAD

The original `v0.1.0` tag points at `d743231` (pre-fix). Because no GitHub release was ever published from it and no PyPI upload happened, it is safe to overwrite. Anyone who already cloned and runs `git fetch --tags --force` will get the corrected tag.

```bash
# Local: delete and recreate annotated tag at current main HEAD
git tag -d v0.1.0
git tag -a v0.1.0 -m "v0.1.0 — first public release"

# Remote: force-push the moved tag
git push origin :refs/tags/v0.1.0    # delete remote tag first
git push origin v0.1.0               # push new tag

# Verify
git tag -l v0.1.0                    # local: prints v0.1.0
git ls-remote --tags origin v0.1.0   # remote: prints new SHA matching `git rev-parse HEAD`
git rev-parse HEAD
```

> **Why force-overwrite the tag is OK here:** the original tag was never used to publish a GitHub release or a PyPI distribution (verified via `gh release view v0.1.0` → `release not found`). The only consumer of the original tag is `git tag -l` on a local clone. After publishing, **never** force-overwrite a tag that has a corresponding GitHub release or PyPI upload — bump to v0.1.1 instead.

If you'd rather avoid the force-tag and bump to v0.1.1 instead, replace `v0.1.0` with `v0.1.1` everywhere below (also bump `pyproject.toml`'s `[project] version` and `[tool.poetry] version` and re-build).

## Step 3 — Build release artifacts

Install the `build` frontend into the same `uv`-managed `.venv` you used in Step 1, then run it via `uv run` so the isolated build environment uses `uv`'s own venv backend (not the system-Python `venv` module — Ubuntu 24.04 doesn't ship `python3.12-venv` by default and `uvx --from build pyproject-build` will fail with a `python3.12-venv missing` apt hint):

```bash
uv pip install build
uv run python -m build --outdir dist

ls dist/
# expected:
#   garage_agent-0.1.0-py3-none-any.whl
#   garage_agent-0.1.0.tar.gz

sha256sum dist/garage_agent-0.1.0*
```

> **Note on naming:** the distribution / project name is `garage-agent` (PyPI: `pip install garage-agent`), but the Python import path is still `import garage_os`. Same pattern as Pillow (`pip install Pillow` / `import PIL`). PEP 427 normalizes the dist name `garage-agent` to the wheel filename prefix `garage_agent-0.1.0-...` (hyphen → underscore).

Reference SHAs (from a clean build at the rename branch `cursor/runbook-wsl-ubuntu-fix-df36`, `uv sync` + `uv run python -m build` on WSL Ubuntu 24.04 / Python 3.12):

| File | Size | SHA-256 |
|---|---|---|
| `garage_agent-0.1.0-py3-none-any.whl` | ~189 KB | `aaa925341392f1dc18e241073c758096d605dda43b21c944637176ad2501f8d0` |
| `garage_agent-0.1.0.tar.gz` | ~199 KB | `8dfb5fbc60085e45f2ada510d00e72bdb8a9706647f9994265136e68dde4245f` |

> **Why these SHAs are different from the pre-rename ones (`ee001cf3...` / `e7f4bb3f...`):**
> - The `garage-os → garage-agent` distribution rename changed `pyproject.toml` (`name = "garage-agent"`), `uv.lock`, the wheel filename prefix (PEP 427: `garage-agent → garage_agent-0.1.0-...`), and the sdist root directory (`garage_agent-0.1.0/`). Both artifacts are bit-for-bit different from the pre-rename build.
> - Exact SHA equality across machines requires identical filesystem timestamps and `pyproject.toml` byte-content; the values above are a sanity check, not a publishing precondition. The smoke test below is the real gate.

Verify the sdist metadata:

```bash
tar xzf dist/garage_agent-0.1.0.tar.gz -O garage_agent-0.1.0/PKG-INFO | head -10
# Should show:
#   Metadata-Version: 2.4
#   Name: garage-agent
#   Version: 0.1.0
#   License: Apache-2.0
#   ...
```

Smoke-test the wheel in a throwaway venv:

```bash
uv run --with ./dist/garage_agent-0.1.0-py3-none-any.whl --no-project --refresh garage --help
# Should print the garage CLI help text (no "command not found", no import errors)
```

## Step 4 — Create the GitHub Release

The release notes file is checked into the repo at `docs/releases/v0.1.0.md`:

```bash
gh release create v0.1.0 \
  --title "garage-agent v0.1.0 — first public release" \
  --notes-file docs/releases/v0.1.0.md \
  --prerelease \
  dist/garage_agent-0.1.0-py3-none-any.whl \
  dist/garage_agent-0.1.0.tar.gz
```

Flag rationale:

- `--prerelease`: matches `Development Status :: 4 - Beta` in `pyproject.toml`, and matches upstream harness-flow v0.1.0's pre-release marker. Once v0.1.x has been used in the wild without P0 issues, future patch / minor releases (v0.1.1, v0.2.0) can drop `--prerelease`.
- `--latest=true` is **not** set — pre-releases generally shouldn't be marked latest. GitHub will still surface it via the `/releases` page.

If you'd rather use the GitHub web UI:

1. https://github.com/hujianbest/garage-agent/releases/new
2. **Tag**: `v0.1.0` (already pushed)
3. **Title**: `garage-agent v0.1.0 — first public release`
4. **Description**: paste the contents of `docs/releases/v0.1.0.md`
5. **Attach binaries**: drag both files from `dist/`
6. Tick **"Set as a pre-release"**
7. Publish

## Step 5 — (optional) Publish to PyPI

This step only matters if you want `pip install garage-agent` to work directly. Skip for v0.1.0 if you want to wait for community feedback first.

Prerequisites:

- A PyPI account: https://pypi.org/account/register/
- An API token: https://pypi.org/manage/account/token/
- `~/.pypirc` configured **or** `TWINE_USERNAME=__token__` + `TWINE_PASSWORD=pypi-AgEI...` exported

```bash
# Validate metadata before upload (uvx avoids system-pip pollution)
uvx --from twine twine check dist/*

# Actual upload
uvx --from twine twine upload dist/*
```

After upload, verify in a fresh venv:

```bash
uv venv /tmp/garage-test
/tmp/garage-test/bin/pip install garage-agent==0.1.0
/tmp/garage-test/bin/garage --help     # CLI installed
```

If `pip install garage-agent` works, edit the published release body via:

```bash
gh release edit v0.1.0 --notes-file docs/releases/v0.1.0.md
```

(after updating `docs/releases/v0.1.0.md` to remove the "PyPI not yet published" caveat in step 6 below)

## Step 6 — (optional) Announce + post-release polish

- Update repo description / topics on https://github.com/hujianbest/garage-agent (settings → about)
- Pin to GitHub profile if relevant
- If PyPI upload succeeded, open a small follow-up PR to:
  - Replace "PyPI release prepared but not yet published" in `docs/releases/v0.1.0.md`
  - Replace the "PyPI 首发暂未启用" sentence in `RELEASE_NOTES.md` with `pip install garage-agent`
- Whatever channels you prefer (X / blog / mailing list)

## Rollback

Before announcing (no GitHub release published yet, no PyPI upload):

```bash
# (Local) move tag back / remove
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
# fix the issue, then re-run from Step 2
```

After GitHub release published but before PyPI upload:

```bash
gh release delete v0.1.0 --yes
git push --delete origin v0.1.0
git tag -d v0.1.0
# fix, re-tag, re-publish
```

After PyPI upload: **PyPI does not allow re-using a version number**. Bump to v0.1.1 instead.

## Adapting to other environments

| Environment | Adjustment |
|---|---|
| **macOS / native Linux with system Python** | Replace `python3` with `python` if that's your default. `uv` works identically. |
| **conda / mamba** | `conda activate <env>` first; `uv sync` will reuse the active env if you `uv sync --active`. |
| **pyenv** | `pyenv local 3.12.x` first; `uv sync` will pick up `.python-version`. |
| **No `uv`** | Substitute `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"` for `uv sync`, and drop `uv run` from `pytest`. The end behavior is identical. |
| **Ubuntu 22.04 / Python 3.10** | `uv sync` will print `requires-python: >=3.11`; install Python 3.11+ via `sudo apt install python3.11` or `uv python install 3.11` and re-run. |

## Final checklist

- [x] PR #41 merged (release-prep)
- [x] PR #42 merged (coding-pack v0.4.0; path A)
- [x] PR #43 merged (release runbook + body)
- [x] PRs #44–#48 merged (build / pytest / CLI fixes — required for reproducible release)
- [ ] Local main pulled at HEAD ≥ `84a7591`
- [ ] `uv sync && uv run pytest tests/ -q` green (expect 1045 passed)
- [ ] `v0.1.0` tag re-created at current `main` HEAD and force-pushed to origin
- [ ] `dist/garage_agent-0.1.0-py3-none-any.whl` and `dist/garage_agent-0.1.0.tar.gz` rebuilt locally with `python -m build`
- [ ] Wheel smoke-test: `uv run --with ./dist/...whl --no-project garage --help` works
- [ ] `gh release create v0.1.0 --prerelease --notes-file docs/releases/v0.1.0.md dist/*.whl dist/*.tar.gz` succeeded
- [ ] Release visible at https://github.com/hujianbest/garage-agent/releases/tag/v0.1.0
- [ ] (optional) `uvx --from twine twine upload dist/*` succeeded
- [ ] (optional) Announcement posted
