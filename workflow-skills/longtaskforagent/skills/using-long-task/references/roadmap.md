# Roadmap — Future Enhancements

## P2: Parallel Agent Dispatch (R8)

**Status**: Documented, not yet implemented

**Goal**: Enable parallel dispatch of independent feature implementations.

**Requirements**:
- R8.1: Identify features with no mutual dependencies for parallel execution
- R8.2: Dispatch implementer subagents in parallel using the Task tool
- R8.3: Merge results, detect conflicts, run full test suite after parallel completion

**Design Notes**:
- Only parallelize truly independent tasks (no shared files, no dependencies)
- Always run full test suite after parallel completion
- If conflicts found, resolve sequentially
- See `subagent-development.md` for parallel dispatch section

## P2: Plugin Discovery System (R12)

**Status**: Documented, not yet implemented

**Goal**: Support skill discovery, frontmatter metadata, and priority shadowing.

**Requirements**:
- R12.1: Support YAML frontmatter in SKILL.md for skill name and trigger conditions
- R12.2: Support skill priority shadowing (project-level > user-level > default)
- R12.3: Consider `.claude-plugin` packaging format for marketplace distribution

**Design Notes**:
- Current SKILL.md already has frontmatter — extend with discovery metadata
- Shadowing enables users to customize the workflow without forking
- Marketplace format would enable one-click installation

## P2: Auto-Update Mechanism (R13)

**Status**: Documented, not yet implemented

**Goal**: Check for new versions when the skill is loaded.

**Requirements**:
- R13.1: Add version number to SKILL.md frontmatter or a VERSION file
- R13.2: On skill load, check remote repository for newer version
- R13.3: Notify user if update available (never auto-update)

**Design Notes**:
- Git-based checking: `git ls-remote` against origin
- Compare local vs remote HEAD or tag
- User notification only — never auto-apply updates

## P3: Multi-Platform Support (R18)

**Status**: Future consideration

**Goal**: Support Codex (OpenAI) and OpenCode platforms.

**Requirements**:
- R18.1: Evaluate Codex adaptation (native skill discovery via symlink)
- R18.2: Evaluate OpenCode adaptation (JS plugin system)
- R18.3: Create platform-specific README docs

**Design Notes**:
- Codex: Symlink to `~/.agents/skills/long-task-agent/`
- OpenCode: JavaScript plugin wrapper
- Core workflow is platform-agnostic; only skill discovery differs

## P2: Integration Testing (R16)

**Status**: Documented, not yet implemented

**Goal**: Test the skill workflow itself in real Claude Code sessions.

**Requirements**:
- R16.1: Create `tests/` directory with skill workflow integration tests
- R16.2: Add token usage analysis tool
- R16.3: Add session transcript verification (verify skill invocations, subagent dispatches)

**Design Notes**:
- Test framework should run real Claude Code sessions
- Verify: skill loads, phases execute in order, artifacts are created
- Token analysis helps optimize prompt size
