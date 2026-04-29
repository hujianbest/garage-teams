# How to publish v0.1.0

> Cloud agents have read-only `gh` and cannot publish a GitHub release. This file gives the maintainer the exact one-shot command sequence.

## Prerequisites

- You are logged into `gh` as a user with write access to `hujianbest/garage-agent`
- PR [#41](https://github.com/hujianbest/garage-agent/pull/41) has been reviewed
- Both pytest checks (Python 3.11 + 3.12) on PR #41 are ✅
- You are on a clean working tree

## Step 1 — Merge PR #41

```bash
gh pr ready 41                                    # mark draft → ready (if still draft)
gh pr merge 41 --squash --delete-branch           # or --merge / --rebase per your preference
git fetch origin && git checkout main && git pull origin main
```

After merge, `git log --oneline -1` should show the v0.1 release-prep commit at HEAD.

## Step 2 — Tag v0.1.0

```bash
git tag -a v0.1.0 -m "v0.1.0 — first public release"
git push origin v0.1.0
```

Verify:

```bash
git tag -l v0.1.0           # should print: v0.1.0
git ls-remote --tags origin v0.1.0   # should print the SHA
```

## Step 3 — Build release artifacts

The release-prep agent already built and saved both artifacts to `/opt/cursor/artifacts/` (you'll find them attached to PR #41 cloud-agent run). To rebuild locally:

```bash
# from a fresh checkout of main at v0.1.0
python -m pip install --upgrade build
python -m build --outdir dist
ls dist/
# expected:
#   garage_os-0.1.0-py3-none-any.whl
#   garage_os-0.1.0.tar.gz
```

Verify the sdist metadata:

```bash
tar tzf dist/garage_os-0.1.0.tar.gz | head
tar xzf dist/garage_os-0.1.0.tar.gz -O garage_os-0.1.0/PKG-INFO | head -30
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
  dist/garage_os-0.1.0-py3-none-any.whl \
  dist/garage_os-0.1.0.tar.gz
```

Optional flags:

- `--draft` — create as draft so you can preview before going live
- `--prerelease` — flag as pre-release (recommended if you want extra signal that v0.1 is `Development Status :: 4 - Beta`)
- `--latest=true` — explicitly mark as the "Latest" release on the repo home page

If you want to do it through the GitHub web UI instead:

1. https://github.com/hujianbest/garage-agent/releases/new
2. **Tag**: `v0.1.0` (already pushed)
3. **Title**: `garage-agent v0.1.0 — first public release`
4. **Description**: paste the contents of `docs/releases/v0.1.0.md`
5. **Attach binaries**: drag both files from `dist/`
6. Tick "Set as the latest release" if desired
7. Publish

## Step 5 — (optional) Publish to PyPI

This step is only needed if you want `pip install garage-os` to work directly. Skip it for v0.1 if you'd rather wait for community feedback first.

Prerequisites:

- A PyPI account (https://pypi.org/account/register/)
- An API token scoped to a project (or all-account during first publish): https://pypi.org/manage/account/token/
- `~/.pypirc` configured, **or** the token exported as `TWINE_PASSWORD=pypi-AgEI...` with `TWINE_USERNAME=__token__`

```bash
python -m pip install --upgrade twine
python -m twine check dist/*           # validate metadata before upload
python -m twine upload dist/*          # actual upload
```

After upload, verify:

```bash
pip install garage-os==0.1.0
garage --version || garage status      # confirm CLI installed
```

If `pip install garage-os` works, edit `RELEASE_NOTES.md` (and the published release body via `gh release edit v0.1.0 --notes-file ...`) to replace the "PyPI release prepared but not yet published" sentence with `pip install garage-os`.

## Step 6 — (optional) Announce

- Repo description / topics on https://github.com/hujianbest/garage-agent (settings → about)
- Pin to GitHub profile if relevant
- Whatever channels you prefer (X / blog / mailing list)

## Rollback

If anything goes wrong after publishing the release but before announcing:

```bash
gh release delete v0.1.0 --yes
git push --delete origin v0.1.0
git tag -d v0.1.0
# fix the issue, then re-run Step 2 onward
```

If something goes wrong after PyPI upload, **you cannot delete a published release** — bump to v0.1.1 instead.

## Checklist

- [ ] PR #41 reviewed and merged into `main`
- [ ] Both pytest checks green on the merge commit
- [ ] `v0.1.0` tag pushed
- [ ] `dist/garage_os-0.1.0-py3-none-any.whl` + `dist/garage_os-0.1.0.tar.gz` built locally
- [ ] `gh release create v0.1.0 --notes-file docs/releases/v0.1.0.md ...` succeeded
- [ ] (optional) `twine upload dist/*` succeeded
- [ ] (optional) Release notes updated to remove "PyPI not yet published" caveat
- [ ] Announcement posted (if planned)
