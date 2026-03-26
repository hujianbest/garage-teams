---
name: sdd-regression-gate
description: Run the regression gate for an implemented SDD task after code review and before final completion claims. Use when the current task appears implemented and reviewed, and you need to verify that related behavior, broader tests, builds, or checks were not broken by the change.
---

# SDD Regression Gate

Run the minimum regression evidence required before the task can be considered complete.

## Purpose

This skill protects the codebase from local fixes that quietly break nearby behavior.

Green tests for the new task are not enough by themselves.

## Inputs

Use:

- the current implemented task
- the task plan's verification expectations
- the project's normal validation commands

## Workflow

### 1. Identify The Relevant Regression Surface

Determine what must still be true after this change:

- related tests
- impacted modules
- build or type-check status
- local integration points

### 2. Run Fresh Checks

Run the relevant verification commands now.

Do not rely on earlier runs unless they were run for this exact task state in the current flow.

### 3. Read Actual Results

Check:

- exit status
- failure count
- whether the scope tested matches the regression surface

### 4. Decide The Gate Result

If the regression surface is still healthy, the next step is `sdd-completion-gate`.

If not, the next step is `sdd-work-implement`.

## Output Format

Use this exact structure:

```markdown
## Verdict

PASS | REVISE | BLOCKED

## Evidence

- command and result summary

## Regression Risks

- item

## Next Step

`sdd-completion-gate` | `sdd-work-implement`
```

## Decision Rules

Return `PASS` only if the relevant regression checks were run fresh and their results support moving forward.

Return `REVISE` if checks fail or coverage is insufficient.

Return `BLOCKED` if the correct regression command cannot be run yet because the environment or validation setup is broken.

## Anti-Patterns

- Assuming nearby behavior still works
- Using stale test output
- Running only the new test and calling that regression coverage
- Ignoring failed build or type-check results because unit tests passed

## Success Condition

This skill is complete only when it has produced a clear gate result with fresh evidence and a single next step.
