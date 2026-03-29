# Long-Task Agent — Codex (OpenAI) Setup

## Overview

long-task-agent can run on Codex via its native skill discovery system. The core workflow (Brainstorming → Initializer → Worker) is platform-agnostic; only the skill loading mechanism differs.

## Installation

### Option 1: Symlink (Linux/macOS)

```bash
# Clone the repository
git clone <repo-url> ~/long-task-agent

# Create the skills directory if it doesn't exist
mkdir -p ~/.agents/skills

# Symlink the skill
ln -s ~/long-task-agent/long-task-agent ~/.agents/skills/long-task-agent
```

### Option 2: Junction (Windows)

```powershell
# Clone the repository
git clone <repo-url> C:\Users\<user>\long-task-agent

# Create the skills directory
mkdir -Force ~\.agents\skills

# Create junction
cmd /c mklink /J "$HOME\.agents\skills\long-task-agent" "C:\Users\<user>\long-task-agent\long-task-agent"
```

## Skill Discovery

Codex discovers skills by scanning `~/.agents/skills/` for directories containing `SKILL.md`. The YAML frontmatter in SKILL.md provides:

- `name`: Skill identifier (`long-task-agent`)
- `description`: Trigger conditions for automatic invocation

## Limitations on Codex

- **No hooks system**: The `hooks/` directory is Claude Code-specific. On Codex, context injection must be done manually or via the SKILL.md description.
- **No Skill tool**: Skill invocations (e.g., `long-task:long-task-init`) are Claude Code-specific. On Codex, invoke the skill by describing the task.
- **Subagent dispatch**: Codex uses its own task dispatch mechanism. Adapt the `agents/prompts/*.md` templates to Codex's agent API.

## Verification

After installation, verify the skill is discoverable:

```
# In a Codex session, the skill should appear when you ask:
"What skills are available?"
```

## Updates

```bash
cd ~/long-task-agent && git pull
```

The symlink ensures the latest version is always used.
