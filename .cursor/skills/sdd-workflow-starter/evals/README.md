# SDD Workflow Starter Evals

This directory contains eval prompts for `sdd-workflow-starter`.

## Purpose

These evals are designed to test routing quality, not implementation quality.

They check whether the starter skill:

- triggers first
- reads the right routing evidence
- chooses the correct downstream SDD skill
- avoids phase skipping

## Important

Several evals depend on project state, not just the prompt text.

Before running an eval, prepare the required artifact situation described in:

- `workflow-skills/sdd-skills-eval-prompts.md`

Examples:

- approved spec exists, but approved design does not
- `change-request.json` exists
- `hotfix-request.json` exists

If the preconditions are missing, the routing result may be different for the right reason.

## Eval Structure

- `id`: stable identifier
- `prompt`: realistic user prompt
- `expected_output`: human-readable expected routing outcome
- `files`: empty for now, because these evals rely on project artifact state rather than bundled files
- `expectations`: review checklist for grading

## Suggested Grading Focus

When grading these evals, check:

1. Was `sdd-workflow-starter` used first?
2. Did the answer cite routing evidence?
3. Was the downstream skill correct?
4. Did the answer avoid premature design, tasks, or code work?
