---
name: sdd-tasks-review
description: Review an SDD task plan before implementation begins. Use when a task plan draft exists and must be checked for granularity, sequencing, dependency correctness, verifiability, and readiness to guide implementation.
---

# SDD Tasks Review

Review the task plan and decide whether implementation can begin.

## Hard Gate

Do not move to `sdd-work-implement` until the task plan passes review or the user explicitly accepts known gaps.

## Purpose

This skill is the execution readiness gate.

If the task plan is too coarse, implementation will drift.

## Checklist

### 1. Granularity

- Are tasks small enough to execute and verify?
- Are there still tasks that hide multiple behaviors?

### 2. Sequencing

- Is the order of tasks logical?
- Are prerequisites respected?

### 3. Verification Readiness

- Does each important task have a clear verification method?
- Are done conditions explicit?

### 4. Traceability

- Can major tasks be traced back to the design and spec?
- Are risky areas represented in the plan?

## Output Format

Use this exact structure:

```markdown
## Verdict

PASS | REVISE | BLOCKED

## Findings

- [severity] finding

## Plan Weaknesses

- item

## Next Step

`sdd-work-implement` | `sdd-work-tasks`
```

## Decision Rules

Return `PASS` only if the plan:

- is sequenced coherently
- has usable task granularity
- contains explicit done conditions
- supports implementation without major guesswork

Return `REVISE` if:

- the plan is mostly usable but some tasks are too broad or underspecified

Return `BLOCKED` if:

- implementation cannot proceed safely from the current task plan

## Anti-Patterns

- Approving because "the implementer can figure it out"
- Ignoring missing verification steps
- Letting milestone labels substitute for actual tasks

## Success Condition

This skill is complete only when it has produced a clear verdict and a single next step.
