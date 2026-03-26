---
name: sdd-code-review
description: Review code for an implemented SDD task after test review and before regression and completion gates. Use when implementation changes are ready to be checked for correctness, readability, error handling, design alignment, and local code quality.
---

# SDD Code Review

Review the code for the current implemented task.

## Purpose

This skill checks whether the implementation is sound after test quality has been reviewed.

It does not replace specification or design review.

## Review Checklist

### 1. Correctness

- Does the code appear to satisfy the current task?
- Are obvious edge cases mishandled?

### 2. Design Alignment

- Does the implementation still fit the approved design?
- Did the task introduce accidental architecture drift?

### 3. Readability And Maintainability

- Are names understandable?
- Is the logic unnecessarily complex?
- Is the code doing too much in one place?

### 4. Error Handling

- Are likely failure paths handled appropriately?
- Did the implementation introduce brittle assumptions?

## Output Format

Use this exact structure:

```markdown
## Verdict

PASS | REVISE

## Findings

- [severity] finding

## Code Risks

- item

## Next Step

`sdd-regression-gate` | `sdd-work-implement`
```

## Decision Rules

Return `PASS` only if the current task implementation is reasonable to validate further.

Return `REVISE` if correctness, maintainability, or design alignment concerns should be addressed before moving on.

## Anti-Patterns

- Repeating spec review comments here
- Approving code only because tests are green
- Ignoring design drift because the task is small

## Success Condition

This skill is complete only when it has produced a clear verdict and a single next step.
