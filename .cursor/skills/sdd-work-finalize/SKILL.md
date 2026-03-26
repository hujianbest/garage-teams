---
name: sdd-work-finalize
description: Finalize an SDD work cycle after implementation and completion gating have passed. Use when the current work item is complete and you need to update progress records, release notes, review evidence, and prepare a clean handoff to the next task or session.
---

# SDD Work Finalize

Close out the current SDD work cycle cleanly.

## Purpose

This skill turns completed work into durable project state.

It exists so the next session does not have to rediscover:

- what was done
- what evidence supports completion
- what changed for users
- what should happen next

## Preconditions

Use this skill only after the current task has passed completion gating.

## Workflow

### 1. Update Progress State

Update the project's progress record with:

- completed task or scope item
- date or session marker
- current status
- next recommended task

### 2. Update Release Notes

If the completed work changed user-visible behavior, update release notes with a concise description of:

- what changed
- why it matters

### 3. Record Evidence Links

Capture where the supporting evidence lives:

- tests run
- review outcomes
- regression result
- completion gate result

The record can be concise, but it must make later auditing possible.

### 4. Prepare Handoff

State:

- what is complete
- what remains
- what the next correct skill should be, if another session resumes

## Output Format

Use this exact structure:

```markdown
## Finalized Work

- completed item

## Updated Records

- record updated

## Evidence Summary

- evidence item

## Next Step

`sdd-work-implement` | `sdd-work-increment` | `sdd-work-hotfix` | `workflow-complete`
```

## Anti-Patterns

- declaring completion without updating project state
- leaving the next task implicit
- forgetting release notes for user-visible changes
- mixing new implementation work into finalization

## Success Condition

This skill is complete only when project state, release communication, and handoff information have been updated clearly enough for the next session to resume without guesswork.
