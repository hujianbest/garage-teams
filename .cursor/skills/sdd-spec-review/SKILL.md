---
name: sdd-spec-review
description: Review an SDD requirement specification before design begins. Use when a requirement spec draft exists and must be checked for completeness, scope clarity, ambiguity, acceptance criteria, and readiness to become the approved input to design.
---

# SDD Spec Review

Review the requirement specification and decide whether it is ready to be approved for design.

## Purpose

This skill is the specification freeze gate.

If the spec is weak, design will drift. If the spec is approved too early, implementation will inherit avoidable ambiguity.

## Hard Gate

Do not move to `sdd-work-design` until the spec passes review or the user explicitly accepts known gaps.

## Review Method

Review only the spec and the minimum supporting context needed to judge it.

Do not redesign the system during review.

## Checklist

Check the spec against these dimensions:

### 1. Scope

- Is the problem statement clear?
- Is in-scope clear?
- Is out-of-scope explicit?

### 2. Requirement Quality

- Are core requirements observable and testable?
- Are vague words removed or quantified?
- Are requirements free from hidden design decisions?

### 3. Completeness

- Are the main user roles identified?
- Are edge cases or negative paths at least acknowledged?
- Are constraints and dependencies stated?
- Are acceptance criteria present for core behaviors?

### 4. Readiness

- Can a designer proceed without guessing the basics?
- Are blocking open questions identified clearly?

## Output Format

Use this exact structure:

```markdown
## Verdict

PASS | REVISE | BLOCKED

## Findings

- [severity] finding

## Missing Or Weak Areas

- item

## Next Step

`sdd-work-design` | `sdd-work-specify`
```

Severity guidance:

- `critical`: blocks design
- `important`: should be fixed before approval
- `minor`: does not block but should be improved

## Decision Rules

Return `PASS` only if:

- scope is clear
- requirements are usable
- acceptance criteria exist for core scope
- remaining open questions do not block design

Return `REVISE` if:

- the spec is useful but incomplete
- ambiguity remains in important areas
- acceptance criteria are weak or partial

Return `BLOCKED` if:

- the spec is too vague to support design
- the core problem or scope is still unclear
- major contradictions remain unresolved

## Approval Handling

If the spec passes, explicitly say it is ready to become the approved design input.

If it does not pass, send it back to `sdd-work-specify` with concrete revision points.

## Anti-Patterns

- Turning review into redesign
- Approving because "we can figure it out later"
- Treating implied scope as acceptable
- Ignoring missing acceptance criteria

## Success Condition

This skill is complete only when it has produced a clear verdict and a single next step.
