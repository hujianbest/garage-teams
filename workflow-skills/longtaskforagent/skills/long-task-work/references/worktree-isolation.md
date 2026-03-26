# Git Worktree Isolation

## Purpose

Isolate feature implementation in a dedicated git worktree. This keeps the main branch clean, enables safe experimentation, and provides a clear merge/discard workflow.

## When to Use

- **Recommended** for all feature implementation in Worker sessions
- **Required** when multiple features may be developed in parallel
- **Optional** for single-feature sequential development if the user prefers direct branch work

## Setup Process

### Step 1: Check Existing Configuration

1. Look for existing worktree directories:
   ```bash
   ls -d .worktrees worktrees 2>/dev/null
   ```
2. Check CLAUDE.md or project docs for worktree preferences
3. If ambiguous, ask the user which directory to use

### Step 2: Create Worktree

```bash
# Determine base branch
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

# Create worktree for the feature
FEATURE_BRANCH="feature/feature-${FEATURE_ID}-${SHORT_NAME}"
WORKTREE_DIR=".worktrees/${FEATURE_BRANCH}"

git worktree add "${WORKTREE_DIR}" -b "${FEATURE_BRANCH}" "${BASE_BRANCH}"
```

### Step 3: Safety Verification

1. Ensure worktree directory is in `.gitignore`:
   ```bash
   grep -q '.worktrees' .gitignore || echo '.worktrees/' >> .gitignore
   ```

2. Run project setup in the worktree:
   ```bash
   cd "${WORKTREE_DIR}"
   # Auto-detect and run setup
   [ -f package.json ] && npm install
   [ -f requirements.txt ] && pip install -r requirements.txt
   [ -f Cargo.toml ] && cargo build
   [ -f go.mod ] && go mod download
   ```

3. Run baseline tests to verify clean state:
   ```bash
   # Run full test suite — all must pass before starting work
   ```

### Step 4: Work in Worktree

All TDD Red → Green → Refactor work happens inside the worktree directory.

## Branch Naming Convention

```
feature/feature-{ID}-{short-name}
```

Examples:
- `feature/feature-01-user-login`
- `feature/feature-15-dashboard-charts`

## Finishing a Feature Branch

After a feature is marked "passing" and code review is complete, present the user with four options:

### Option 1: Merge Locally
```bash
# Switch to base branch
git checkout "${BASE_BRANCH}"

# Merge the feature branch
git merge "${FEATURE_BRANCH}"

# Verify all tests still pass
# [run full test suite]

# Clean up worktree
git worktree remove "${WORKTREE_DIR}"
git branch -d "${FEATURE_BRANCH}"
```

### Option 2: Push and Create PR
```bash
# Push the feature branch
git push -u origin "${FEATURE_BRANCH}"

# Create PR
gh pr create --title "Feature #${FEATURE_ID}: ${TITLE}" --body "..."

# Keep worktree alive until PR is merged
echo "Worktree kept at ${WORKTREE_DIR} — remove after PR merge"
```

### Option 3: Keep As-Is
```bash
# Leave worktree and branch intact
echo "Worktree preserved at ${WORKTREE_DIR}"
echo "Branch: ${FEATURE_BRANCH}"
```

### Option 4: Discard
```bash
# SAFETY: Require explicit confirmation
echo "Type 'discard' to confirm deletion of all changes on ${FEATURE_BRANCH}"
# [wait for user input]

# Remove worktree and branch
git worktree remove --force "${WORKTREE_DIR}"
git branch -D "${FEATURE_BRANCH}"
```

## Worktree Lifecycle

```
Orient → Select Feature
  │
  ├─ Create worktree + branch
  │
  ├─ Setup environment in worktree
  │
  ├─ Run baseline tests (must pass)
  │
  ├─ TDD Red → Green → Refactor
  │
  ├─ Feature marked "passing"
  │
  └─ Finish: Merge / PR / Keep / Discard
```

## Rules

- Always verify `.gitignore` includes the worktree directory
- Always run baseline tests before starting work in a new worktree
- Never force-delete a worktree without user confirmation
- If the user declines worktree isolation, work directly on a feature branch (still isolated from main)
