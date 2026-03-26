---
name: sdd-work-increment
description: Handle requirement changes in an SDD-governed project without bypassing specification and design discipline. Use when a change-request.json exists, when the user asks to add or modify requirements in an existing workflow, or when approved scope must be updated before implementation continues.
---

# SDD Work Increment

Process a requirement change without corrupting the main SDD flow.

## Purpose

This skill handles change requests such as:

- adding a new requirement
- changing scope
- changing acceptance criteria
- reintroducing previously deferred work

It prevents ad-hoc requirement edits from leaking directly into design or implementation.

## Hard Gate

Do not jump from a change request straight into coding.

A change must first be analyzed for impact on the spec, design, and task plan.

## Preconditions

Use this skill when:

- `change-request.json` exists, or
- the user explicitly asks to modify approved scope or requirements

## Workflow

### 1. Read The Change Request

Read:

- the change request itself
- the approved requirement spec
- the approved design
- the current task plan, if it exists

Determine:

- what changed
- what remains valid
- what artifacts are affected

### 2. Perform Impact Analysis

Assess impact on:

- scope and requirements
- constraints or acceptance criteria
- architecture or interfaces
- task ordering and dependencies
- already implemented work

Classify the change:

- spec-only update
- spec + design update
- spec + design + task plan update
- implemented behavior now invalid

### 3. Update The Correct Artifacts

Apply the minimum necessary changes to keep artifacts aligned.

Rules:

- requirements changes go to the requirement spec first
- design changes follow only if the requirement change affects HOW
- task plan changes follow only if design or scope changes affect execution

### 4. Route Back To The Correct Phase

After the update:

- if the spec changed materially and needs re-review -> `sdd-spec-review`
- if the design changed materially and needs re-review -> `sdd-design-review`
- if only task sequencing changed -> `sdd-tasks-review`
- if all relevant docs remain approved -> return to the appropriate implementation phase

## Output Format

Use this exact structure:

```markdown
## Change Summary

- summary

## Impact

- affected artifact

## Required Updates

- update

## Next Step

`sdd-spec-review` | `sdd-design-review` | `sdd-tasks-review` | `sdd-work-implement`
```

## Anti-Patterns

- editing the implementation first and fixing docs later
- treating a requirement change as a task-only change
- assuming old approvals still hold after material scope changes
- leaving artifacts out of sync

## Success Condition

This skill is complete only when the change has been analyzed, the affected artifacts have been updated or identified for update, and a single correct next step has been chosen.
