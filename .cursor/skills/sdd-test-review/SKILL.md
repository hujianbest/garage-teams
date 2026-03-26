---
name: sdd-test-review
description: Review tests for an implemented SDD task before code review and completion gating. Use when a task implementation includes new or changed tests and those tests must be checked for meaningful failure-first behavior, behavioral coverage, and usefulness.
---

# SDD Test Review

Review the tests for the current implemented task.

## Purpose

This skill checks whether the tests actually validate behavior instead of merely decorating the task with shallow coverage.

## Review Checklist

### 1. Failure-First Discipline

- Was there a failing test before the implementation?
- Did the failure represent the intended missing behavior?

### 2. Behavioral Value

- Do the tests check behavior rather than implementation trivia?
- Are assertions meaningful?

### 3. Coverage Shape

- Is there at least basic unhappy-path or edge-path coverage where relevant?
- Are important task behaviors represented?

### 4. Test Quality Risks

- Overuse of mocks
- weak assertions
- vague names
- tests coupled too tightly to implementation details

## Output Format

Use this exact structure:

```markdown
## Verdict

PASS | REVISE

## Findings

- [severity] finding

## Test Quality Gaps

- item

## Next Step

`sdd-code-review` | `sdd-work-implement`
```

## Decision Rules

Return `PASS` only if the tests are meaningfully useful for the current task.

Return `REVISE` if test quality is too weak to trust the task result yet.

## Anti-Patterns

- Approving tests because they exist
- Ignoring the lack of a failing-test-first signal
- Accepting shallow assertions as sufficient evidence

## Success Condition

This skill is complete only when it has produced a clear verdict and a single next step.
