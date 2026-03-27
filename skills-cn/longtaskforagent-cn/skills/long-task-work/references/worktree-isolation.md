# Git Worktree 隔离

## 目的

在专用 git worktree 中隔离特性实现。保持主分支干净，支持安全试验，并提供清晰的合并/丢弃工作流。

## 何时使用

- **推荐**：Worker 会话中所有特性实现
- **必需**：可能并行开发多条特性时
- **可选**：单特性顺序开发时，若用户偏好直接在分支上工作

## 设置流程

### 步骤 1：检查既有配置

1. 查找既有 worktree 目录：
   ```bash
   ls -d .worktrees worktrees 2>/dev/null
   ```
2. 检查 CLAUDE.md 或项目文档中的 worktree 偏好
3. 若不明确，询问用户使用哪个目录

### 步骤 2：创建 Worktree

```bash
# Determine base branch
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

# Create worktree for the feature
FEATURE_BRANCH="feature/feature-${FEATURE_ID}-${SHORT_NAME}"
WORKTREE_DIR=".worktrees/${FEATURE_BRANCH}"

git worktree add "${WORKTREE_DIR}" -b "${FEATURE_BRANCH}" "${BASE_BRANCH}"
```

### 步骤 3：安全校验

1. 确保 worktree 目录在 `.gitignore` 中：
   ```bash
   grep -q '.worktrees' .gitignore || echo '.worktrees/' >> .gitignore
   ```

2. 在 worktree 中运行项目安装：
   ```bash
   cd "${WORKTREE_DIR}"
   # Auto-detect and run setup
   [ -f package.json ] && npm install
   [ -f requirements.txt ] && pip install -r requirements.txt
   [ -f Cargo.toml ] && cargo build
   [ -f go.mod ] && go mod download
   ```

3. 运行基线测试验证干净状态：
   ```bash
   # Run full test suite — all must pass before starting work
   ```

### 步骤 4：在 Worktree 中工作

全部 TDD 红 → 绿 → 重构工作均在 worktree 目录内进行。

## 分支命名约定

```
feature/feature-{ID}-{short-name}
```

示例：
- `feature/feature-01-user-login`
- `feature/feature-15-dashboard-charts`

## 结束特性分支

特性标为 "passing" 且代码评审完成后，向用户提供四种选项：

### 选项 1：本地合并
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

### 选项 2：推送并创建 PR
```bash
# Push the feature branch
git push -u origin "${FEATURE_BRANCH}"

# Create PR
gh pr create --title "Feature #${FEATURE_ID}: ${TITLE}" --body "..."

# Keep worktree alive until PR is merged
echo "Worktree kept at ${WORKTREE_DIR} — remove after PR merge"
```

### 选项 3：保持原状
```bash
# Leave worktree and branch intact
echo "Worktree preserved at ${WORKTREE_DIR}"
echo "Branch: ${FEATURE_BRANCH}"
```

### 选项 4：丢弃
```bash
# SAFETY: Require explicit confirmation
echo "Type 'discard' to confirm deletion of all changes on ${FEATURE_BRANCH}"
# [wait for user input]

# Remove worktree and branch
git worktree remove --force "${WORKTREE_DIR}"
git branch -D "${FEATURE_BRANCH}"
```

## Worktree 生命周期

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

## 规则

- 始终确认 `.gitignore` 包含 worktree 目录
- 在新 worktree 开始工作前始终运行基线测试
- 未经用户确认切勿强制删除 worktree
- 若用户拒绝 worktree 隔离，直接在特性分支上工作（仍与 main 隔离）
