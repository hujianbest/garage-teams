---
name: sdd-completion-gate
description: Enforce the final completion gate for an implemented SDD task using fresh verification evidence. Use when a task has passed test review, code review, and regression checks, and the agent is about to claim completion, update status, commit progress, or move to the next task.
---

# SDD Completion Gate

Enforce evidence before completion claims.

## Iron Rule

Do not claim a task is complete without fresh verification evidence for the current state of the work.

If you did not run the verifying command in this flow, you cannot honestly claim completion.

## Apply This Skill Before

- saying the task is done
- updating progress/state to completed
- moving to the next task
- preparing commit or delivery language that implies success

## Workflow

### 1. Identify The Claim

State exactly what you are about to claim, for example:

- tests pass
- behavior works
- bug is fixed
- task is complete

### 2. Identify The Proof Command

Choose the command or commands that actually prove the claim.

Do not substitute weaker evidence.

### 3. Run Fresh Verification

Run the full verification command now.

### 4. Read The Full Result

Check:

- exit code
- failure count
- whether output really supports the claim

### 5. Gate The Claim

- If the evidence supports the claim, allow completion
- If not, report actual status and route back to `sdd-work-implement`

## Output Format

Use this exact structure:

```markdown
## Verdict

PASS | REVISE | BLOCKED

## Verified Claim

- claim

## Evidence

- command and result summary

## Next Step

`done-for-current-task` | `sdd-work-implement`
```

## Decision Rules

Return `PASS` only if the intended completion claim is directly supported by fresh evidence.

Return `REVISE` if the evidence does not support the claim or more implementation is required.

Return `BLOCKED` if the verifying command cannot be run because the environment or toolchain is broken.

## Anti-Patterns

- saying "should be done now"
- trusting old output
- treating green local intuition as evidence
- assuming review approval means execution success
- moving on because you are tired of the task

## Success Condition

This skill is complete only when it has either authorized a completion claim with fresh evidence or rejected the claim and routed work back for revision.
