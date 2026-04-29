# How to publish v0.1.0

> Cloud agents have a read-only `gh` CLI and cannot publish a GitHub release. This runbook gives the maintainer the exact one-shot command sequence.
>
> **Current state** (as of this commit):
>
> - PR [#41](https://github.com/hujianbest/garage-agent/pull/41) (release-prep: legal + community + CI + PyPI metadata + sentinel refresh) — **MERGED** at squash commit `3e96d14` on 2026-04-29 04:23 UTC.
> - PR [#42](https://github.com/hujianbest/garage-agent/pull/42) (`packs/coding/` v0.3.0 → v0.4.0 reverse-sync from harness-flow v0.1.0) — **MERGED** at merge commit `3a7565d` on 2026-04-29.
> - PR [#43](https://github.com/hujianbest/garage-agent/pull/43) (this PR — release runbook + body refresh, including bringing back `docs/releases/*` that PR #41's squash dropped) — pending merge before tagging v0.1.0.
>
> Path A (v0.1.0 includes coding-pack v0.4.0) is now the de-facto reality: PR #42 is already on main. Only PR #43 (this PR) remains.

## Step 1 — Merge this PR

```bash
# Make sure you're on a clean main and synced with origin
git checkout main && git pull origin main

# Merge this runbook PR — gives you docs/releases/v0.1.0.md so the
# `gh release create --notes-file` call in Step 4 has its input ready.
gh pr ready 43
gh pr merge 43 --squash --delete-branch

# Pull the merged commit down
git checkout main && git pull origin main
git log --oneline -5         # confirm #43 squash commit at HEAD
```

Verify the final main HEAD:

```bash
# 1045 tests pass on main (1044 baseline + 1 from #42's
# test_skill_anatomy_drift rewrite)
pytest tests/ -q --tb=no
# expected: ===== 1045 passed =====

# All 4 release-prep doc files are present + release docs from this PR
ls LICENSE CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md
ls .github/workflows/test.yml
ls docs/releases/v0.1.0.md docs/releases/HOW-TO-PUBLISH-v0.1.0.md

# packs/coding pinned at 0.4.0 (from PR #42)
grep '"version"' packs/coding/pack.json
# expected:   "version": "0.4.0",
```

## Step 2 — Tag v0.1.0

```bash
git tag -a v0.1.0 -m "v0.1.0 — first public release"
git push origin v0.1.0
```

Verify:

```bash
git tag -l v0.1.0                       # should print: v0.1.0
git ls-remote --tags origin v0.1.0      # should print the SHA
```

## Step 3 — Build release artifacts

The release-prep cloud agent built and saved the artifacts twice during this work — once on PR #41's branch (now stale; not described here) and once on main HEAD `3a7565d` (post-#42-merge). The SHAs below are from the latter build, which matches the state v0.1.0 will tag once PR #43 is merged:

| File | Size | SHA-256 |
|---|---|---|
| `garage_os-0.1.0-py3-none-any.whl` | 189011 bytes | `ec7b9a137445a35654e2b74de0ffc2295159b39cd8b1cb46e7c10dc2a93953b3` |
| `garage_os-0.1.0.tar.gz` | 198287 bytes (post-#42) | `c48e4599aadd49ec9e9930f17b7108136d0d7c4b2fcd4f3492ae7fbe668e8f28` |

> The wheel SHA is stable across PR #41 + #42 + #43 because the wheel only ships `src/garage_os/**` (PR #41 set this in `pyproject.toml`; #42 / #43 don't touch `src/`).
>
> The sdist SHA shifts whenever `pyproject.toml`'s `include = [LICENSE, AGENTS.md, RELEASE_NOTES.md]` files change content. PR #42 changed `AGENTS.md` + `RELEASE_NOTES.md`; PR #43 also changes `RELEASE_NOTES.md` (cross-reference link); so after merging #43 the sdist SHA will shift one more time. **Always rebuild locally after the final merge** to be safe:

```bash
# from a fresh checkout of main at v0.1.0
#
# Build tool: pick ONE (Debian/Ubuntu system Python is PEP 668 — do not
# `pip install` onto it without a venv).
#
#   pipx install build          # then: ~/.local/bin is usually on PATH → build
#   uv tool install build       # then: build (same idea as pipx)
#   python3 -m venv .venv && . .venv/bin/activate && pip install build
#
python -m build --outdir dist   # or: python3 -m build … if your `python` is py3
ls dist/
# expected:
#   garage_os-0.1.0-py3-none-any.whl
#   garage_os-0.1.0.tar.gz

# Compare with cloud-agent SHAs above; they should match
sha256sum dist/garage_os-0.1.0*
```

Verify the sdist metadata:

```bash
tar xzf dist/garage_os-0.1.0.tar.gz -O garage_os-0.1.0/PKG-INFO | head -10
# Should show:
#   Metadata-Version: 2.4
#   Name: garage-os
#   Version: 0.1.0
#   License: Apache-2.0
#   ...
```

## Step 4 — Create the GitHub Release

The release notes file is checked into the repo at `docs/releases/v0.1.0.md`:

```bash
gh release create v0.1.0 \
  --title "garage-agent v0.1.0 — first public release" \
  --notes-file docs/releases/v0.1.0.md \
  --prerelease \
  dist/garage_os-0.1.0-py3-none-any.whl \
  dist/garage_os-0.1.0.tar.gz
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

This step only matters if you want `pip install garage-os` to work directly. Skip for v0.1.0 if you want to wait for community feedback first.

Prerequisites:

- A PyPI account: https://pypi.org/account/register/
- An API token: https://pypi.org/manage/account/token/
- `~/.pypirc` configured **or** `TWINE_USERNAME=__token__` + `TWINE_PASSWORD=pypi-AgEI...` exported

```bash
# Twine: same PEP 668 story — use pipx / uv tool / venv, not system pip.
#   pipx install twine
#   uv tool install twine
#
python -m twine check dist/*           # validate metadata before upload
python -m twine upload dist/*          # actual upload
```

After upload, verify in a fresh venv:

```bash
python -m venv /tmp/garage-test
/tmp/garage-test/bin/pip install garage-os==0.1.0
/tmp/garage-test/bin/garage --help     # CLI installed
```

If `pip install garage-os` works, edit the published release body via:

```bash
gh release edit v0.1.0 --notes-file docs/releases/v0.1.0.md
```

(after updating `docs/releases/v0.1.0.md` to remove the "PyPI not yet published" caveat in step 6 below)

## Step 6 — (optional) Announce + post-release polish

- Update repo description / topics on https://github.com/hujianbest/garage-agent (settings → about)
- Pin to GitHub profile if relevant
- If PyPI upload succeeded, open a small follow-up PR to:
  - Replace "PyPI release prepared but not yet published" in `docs/releases/v0.1.0.md`
  - Replace the "PyPI 首发暂未启用" sentence in `RELEASE_NOTES.md` with `pip install garage-os`
- Whatever channels you prefer (X / blog / mailing list)

## Rollback

Before announcing:

```bash
gh release delete v0.1.0 --yes
git push --delete origin v0.1.0
git tag -d v0.1.0
# fix the issue, then re-run from Step 2
```

After PyPI upload: **PyPI does not allow re-using a version number**. Bump to v0.1.1 instead.

## Final checklist

- [x] PR #41 merged (release-prep)
- [x] PR #42 merged (coding-pack v0.4.0; path A)
- [ ] PR #43 (this runbook + release docs) reviewed and merged
- [ ] Local main pulled; `pytest tests/ -q` green at the merged commit (expect 1045 passed)
- [ ] Final artifacts rebuilt locally (`python -m build` after `build` is on PATH via pipx/uv/venv)
- [ ] `v0.1.0` tag created and pushed
- [ ] `gh release create v0.1.0 --prerelease --notes-file docs/releases/v0.1.0.md dist/*.whl dist/*.tar.gz` succeeded
- [ ] Release visible at https://github.com/hujianbest/garage-agent/releases/tag/v0.1.0
- [ ] (optional) `twine upload dist/*` succeeded
- [ ] (optional) Announcement posted
