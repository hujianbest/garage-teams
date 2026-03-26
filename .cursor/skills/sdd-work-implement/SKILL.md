---
name: sdd-work-implement
description: Execute an approved SDD task plan and implement code in a controlled way. Use when the task plan has passed review and implementation should proceed task by task with TDD, verification, review, and no skipping ahead.
---

# SDD Work Implement

Implement the approved task plan one task at a time.

## Hard Gate

Do not start implementation unless the task plan has passed review.

Do not move to the next task until the current one has been implemented, reviewed, and verified.

## Core Rule

One active task at a time.

## TDD Rule

Do not write production code without a failing test first, unless the task is explicitly non-code configuration and that exception is documented.

## Workflow

### 1. Orient

Read:

- the approved task plan
- the current progress/state record
- the relevant spec and design sections for the current task

Pick exactly one active task.

### 2. Execute With Red-Green-Refactor

For the current task:

1. write or update a failing test
2. run it and confirm the failure is meaningful
3. implement the minimum change
4. rerun and confirm pass
5. refactor while keeping tests green

### 3. Prepare Review Inputs

Before claiming task completion:

- identify what changed
- identify what tests prove it
- identify what risk areas remain

### 4. Handoff To Review And Gates

After implementation of the current task:

1. use `sdd-test-review`
2. then use `sdd-code-review`
3. then use `sdd-regression-gate`
4. then use `sdd-completion-gate`

That order is mandatory.

## Mandatory Order

```text
Implement -> test-review -> code-review -> regression-gate -> completion-gate
```

Do not skip review because the task looks simple.

## Anti-Patterns

- working on multiple tasks in parallel
- implementing before writing a failing test
- treating green tests from an older run as current evidence
- saying "done" before completion gate
- switching tasks because the current one got inconvenient

## Success Condition

This skill is complete only when the current task has gone through review and completion gating, or when a blocking issue is clearly reported.
