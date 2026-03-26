---
name: sdd-work-hotfix
description: Handle urgent bug fixes in an SDD-governed project without abandoning verification discipline. Use when a hotfix-request.json exists, when the user asks for an urgent fix, or when a defect must be repaired quickly while still requiring reproduction, minimal change, regression checks, and completion gating.
---

# SDD Work Hotfix

Process an urgent defect without bypassing engineering discipline.

## Purpose

This skill is for urgent repair work where speed matters, but correctness and evidence still matter more.

It is not a shortcut around TDD or verification.

## Hard Gate

Do not apply a hotfix based only on intuition.

Reproduce first, then fix, then re-verify.

## Preconditions

Use this skill when:

- `hotfix-request.json` exists, or
- the user explicitly requests an urgent bug fix or pre-release repair

## Workflow

### 1. Read The Hotfix Request

Read:

- the bug or defect description
- the current relevant spec/design/task context if available
- any existing evidence of failure

Identify:

- expected behavior
- actual behavior
- affected area

### 2. Reproduce The Problem

Create the smallest reliable reproduction:

- failing automated test when possible
- otherwise a clear manual verification procedure that can later be automated

Do not implement before you can demonstrate the problem.

### 3. Apply The Minimum Safe Fix

Make the smallest change that resolves the reproduced failure.

Avoid opportunistic refactors unless they are necessary to complete the fix safely.

### 4. Run Review And Gates

After the fix:

1. verify the reproduction now passes
2. use `sdd-test-review` if tests changed
3. use `sdd-code-review`
4. use `sdd-regression-gate`
5. use `sdd-completion-gate`

### 5. Sync Artifacts If Needed

If the bug revealed outdated or incorrect spec/design/task information, update the affected documents after the fix is stabilized.

## Output Format

Use this exact structure:

```markdown
## Hotfix Summary

- summary

## Reproduction

- how the defect was reproduced

## Fix Scope

- what changed

## Next Step

`sdd-code-review` | `sdd-regression-gate` | `sdd-completion-gate` | `sdd-work-implement`
```

## Anti-Patterns

- patching first and trying to explain later
- claiming the bug is fixed without reproducing it first
- using urgency as a reason to skip regression checks
- mixing unrelated cleanup into the hotfix

## Success Condition

This skill is complete only when the defect has been reproduced, repaired with a minimum safe change, and routed through the appropriate downstream review and gate steps.
