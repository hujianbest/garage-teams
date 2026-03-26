---
name: sdd-work-tasks
description: Turn an approved SDD design into an executable task plan and task breakdown. Use when the design has passed review and the project needs milestones, task ordering, dependencies, definition of done, and implementation-ready work items before coding starts.
---

# SDD Work Tasks

Create the task plan that translates the approved design into executable work.

## Hard Gate

Do not start implementation until task planning is complete and ready for review.

## Preconditions

Use this skill only when:

- the requirement spec is approved
- the design is approved

If design is still draft or under revision, go back to `sdd-design-review` or `sdd-work-design`.

## Goals

The task plan must make implementation predictable.

It should define:

- milestones
- ordered tasks
- dependencies
- task-level done conditions
- verification expectations

## Workflow

### 1. Read The Approved Inputs

Read:

- approved requirement spec
- approved design
- current project context if relevant

Extract:

- major workstreams
- dependencies and sequencing
- testing implications
- risky or uncertain areas

### 2. Define Milestones

Group work into milestones that produce meaningful progress.

Each milestone should have:

- purpose
- included tasks
- exit criteria

### 3. Break Work Into Tasks

Tasks must be small enough to execute and verify without ambiguity.

Prefer task shapes like:

- write failing test
- run and confirm fail
- implement minimum behavior
- run and confirm pass
- refactor and re-run
- update status and records

Avoid vague task items like:

- implement module
- finish feature
- polish later

### 4. Record Dependencies And Done Conditions

For each task, define:

- prerequisites
- artifacts to touch
- verification method
- done condition

### 5. Write The Task Plan

Use this structure unless the project requires another template:

```markdown
# <Topic> Task Plan

## Overview

## Milestones

## Task Breakdown

## Dependencies

## Definition Of Done

## Verification Strategy

## Risks And Sequencing Notes
```

### 6. Handoff To Review

When the plan is ready, hand off to `sdd-tasks-review`.

Use:

```markdown
Task plan drafted and ready for review.

Next skill: `sdd-tasks-review`
```

## Anti-Patterns

- Turning the task plan into a copy of the design
- Using tasks that are too large to verify
- Omitting dependencies
- Omitting done conditions
- Deferring verification to the end of the entire feature

## Success Condition

This skill is complete only when a reviewable task plan exists and is ready for `sdd-tasks-review`.
