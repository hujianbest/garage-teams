---
name: sdd-work-design
description: Produce a software implementation design from an approved SDD requirement specification. Use when the requirement spec has passed review and the project needs architecture, module boundaries, interfaces, data flow, technical decisions, and a design document before task planning or coding.
---

# SDD Work Design

Create the design document that defines HOW the approved spec will be implemented.

## Hard Gate

Do not decompose tasks or write implementation code until the design has been reviewed and approved.

## Preconditions

Use this skill only when:

- a requirement spec exists
- the spec has passed review or is explicitly approved

If the spec is still draft or under revision, go back to `sdd-spec-review` or `sdd-work-specify`.

## Goals

The design document should remove major implementation guesswork while staying at the design level.

It should answer:

- what major components or modules exist
- how responsibilities are divided
- how data and control flow through the system
- what interfaces must exist
- what constraints shape the implementation
- how the design supports testing

## Workflow

### 1. Read The Approved Spec

Extract:

- core scope
- acceptance criteria
- constraints
- non-functional requirements
- integration points

### 2. Explore Technical Context

Read the minimum relevant technical context:

- existing architecture or project layout
- current frameworks and dependencies
- deployment/runtime constraints if already known

Do not drift into implementation planning yet.

### 3. Propose 2-3 Approaches

Before committing to one design, compare at least two plausible approaches.

For each approach, briefly state:

- how it works
- key pros
- key cons
- why it does or does not fit the spec

Then recommend one approach.

### 4. Write The Design

Use this structure unless the project has a required template:

```markdown
# <Topic> Implementation Design

## Overview

## Design Drivers

## Candidate Approaches

## Chosen Approach

## Architecture

## Module Responsibilities

## Data And Control Flow

## Interfaces And Contracts

## Testing Strategy

## Risks And Open Issues
```

Guidance:

- keep requirements and design distinct
- define boundaries and responsibilities clearly
- explain why the chosen approach fits the spec
- include enough detail for task decomposition, not line-by-line coding

### 5. Self-Check Before Review

Verify:

- every major requirement is addressed by the design
- constraints and NFRs influenced decisions
- the architecture is coherent, not just a list of components
- interfaces are explicit enough for later task planning
- testing strategy exists at the design level

### 6. Handoff To Review

When ready, hand off to `sdd-design-review`.

Use:

```markdown
Design document drafted and ready for review.

Next skill: `sdd-design-review`
```

## Anti-Patterns

- Treating design as implementation pseudocode
- Copying the spec into a new file without adding design decisions
- Presenting only one approach with no trade-off discussion
- Starting task decomposition inside the design doc
- Ignoring NFRs and constraints

## Success Condition

This skill is complete only when a reviewable design document exists and is ready for `sdd-design-review`.
