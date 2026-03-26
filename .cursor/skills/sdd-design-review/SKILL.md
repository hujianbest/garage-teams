---
name: sdd-design-review
description: Review an SDD implementation design before task planning begins. Use when a design document draft exists and must be checked for architectural completeness, requirement coverage, interface clarity, technical fit, and readiness for task decomposition.
---

# SDD Design Review

Review the design document and decide whether it is ready to become the approved input to task planning.

## Hard Gate

Do not move to `sdd-work-tasks` until the design passes review or the user explicitly accepts known gaps.

## Purpose

This skill prevents premature task decomposition.

If the design is vague, task planning will either guess or collapse into implementation details.

## Review Scope

Review the design against:

- the approved requirement spec
- major constraints and NFRs
- the project's technical context, if already known

Do not start writing tasks or code during review.

## Checklist

### 1. Requirement Coverage

- Does the design cover the important requirements from the spec?
- Are major behaviors mapped to components, modules, or interfaces?

### 2. Architectural Coherence

- Are responsibilities and boundaries clear?
- Is the chosen approach explained, not just named?
- Are module interactions understandable?

### 3. Constraint Fit

- Does the design reflect stated constraints?
- Are NFRs and integration points considered?

### 4. Interface Readiness

- Are key contracts explicit enough for task planning?
- Are the major data/control flows clear?

### 5. Testing Readiness

- Does the design include a testing strategy at the design level?
- Is the design testable without requiring hidden assumptions?

## Output Format

Use this exact structure:

```markdown
## Verdict

PASS | REVISE | BLOCKED

## Findings

- [severity] finding

## Weak Or Missing Design Areas

- item

## Next Step

`sdd-work-tasks` | `sdd-work-design`
```

## Decision Rules

Return `PASS` only if the design:

- is traceable to the spec
- explains a coherent implementation approach
- defines boundaries and interfaces clearly enough for planning
- addresses major constraints and testing implications

Return `REVISE` if:

- the core design is usable but incomplete
- some modules, flows, or interfaces remain underspecified
- the testing approach is weak but fixable

Return `BLOCKED` if:

- the design does not clearly support the spec
- key architectural decisions are still missing
- contradictions or unresolved technical risks prevent planning

## Anti-Patterns

- Approving because "we can figure it out during implementation"
- Turning review into low-level coding advice
- Accepting a design that repeats the spec without design choices
- Ignoring missing interfaces or module boundaries

## Success Condition

This skill is complete only when it has produced a clear verdict and a single next step.
