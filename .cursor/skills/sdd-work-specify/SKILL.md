---
name: sdd-work-specify
description: Produce an approved requirement specification for SDD-governed software work. Use when no approved spec exists, when a project is still at the requirements/specification stage, or when the user wants to define scope, requirements, acceptance criteria, constraints, or out-of-scope items before design or implementation.
---

# SDD Work Specify

Create a requirement specification that defines WHAT must be built.

## Hard Gate

Do not design architecture, decompose tasks, scaffold, or write implementation code until the requirement spec has been reviewed and approved.

## Goals

The requirement spec must make later design and implementation possible without guessing.

It should answer:

- what problem is being solved
- who the users are
- what is in scope
- what is out of scope
- what constraints apply
- how success will be verified

## Workflow

Follow these steps in order.

### 1. Explore Context

Read only the materials needed to understand the request:

- user-provided requirement notes
- existing project docs relevant to scope
- existing system behavior if this is an enhancement

Extract initial assumptions, constraints, and unknowns.

### 2. Clarify Before Writing

Ask focused questions before drafting the spec.

Rules:

- prefer one topic at a time
- group closely related questions only when it reduces back-and-forth
- replace vague words with measurable statements
- explicitly ask for out-of-scope items if the user did not provide them

Minimum areas to clarify:

1. purpose and users
2. functional scope
3. exclusions
4. constraints and dependencies
5. acceptance criteria

### 3. Draft The Spec

Write a spec that separates requirements from design decisions.

Use this structure unless the project already has a required template:

```markdown
# <Topic> Requirement Specification

## Purpose

## Scope

## User Roles

## Functional Requirements

## Non-Functional Requirements

## Constraints

## Out Of Scope

## Acceptance Criteria

## Open Questions
```

Guidance:

- Functional requirements describe observable behavior
- Non-functional requirements describe measurable quality targets
- Constraints describe hard limits
- Out-of-scope is explicit, not implied
- Open questions remain only if they do not block review

### 4. Check For Spec Quality

Before handing off, verify:

- requirements are testable
- vague words are quantified or removed
- no design choices are mixed into requirement statements
- out-of-scope is explicit
- acceptance criteria exist for core behaviors

### 5. Handoff To Review

When the draft is ready, hand off to `sdd-spec-review`.

Your output should say:

```markdown
Requirement spec drafted and ready for review.

Next skill: `sdd-spec-review`
```

## Anti-Patterns

- Jumping from user idea straight to architecture
- Treating a brainstorm note as an approved spec
- Writing tasks in the spec
- Using design language like class, endpoint, table, framework unless it is a hard external constraint
- Leaving success criteria implicit

## Success Condition

This skill is complete only when a reviewable requirement spec draft exists and is ready for `sdd-spec-review`.
