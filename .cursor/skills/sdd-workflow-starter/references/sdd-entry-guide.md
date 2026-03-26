# SDD Entry Guide

Use this guide when a project adopts the SDD skills set but has not yet standardized its artifact layout or state files.

## Recommended Artifact Layout

Use these paths by default unless the project already has approved equivalents:

| Logical Artifact | Recommended Path | Notes |
|---|---|---|
| Requirement spec | `docs/specs/YYYY-MM-DD-<topic>-srs.md` | Defines WHAT |
| Design doc | `docs/designs/YYYY-MM-DD-<topic>-design.md` | Defines HOW |
| Task plan | `docs/tasks/YYYY-MM-DD-<topic>-tasks.md` | Defines execution order |
| Progress log | `task-progress.md` | Cross-session continuity |
| Release notes | `RELEASE_NOTES.md` | User-visible changes |
| Review records | `docs/reviews/` | Optional but recommended |
| Verification records | `docs/verification/` | Optional but recommended |

## Minimum State Files

Use these root-level files for routing:

- `workflow-state.json`
- `change-request.json`
- `hotfix-request.json`

If the project already has equivalent files, map them in the SDD contract instead of duplicating them.

## Recommended Routing Inputs

At session start, `sdd-workflow-starter` should inspect only:

1. `workflow-state.json`
2. `change-request.json`
3. `hotfix-request.json`
4. the SDD contract
5. the existence and approval state of spec/design/task artifacts

Avoid broad code exploration before phase routing is complete.

## Approval Signals

Prefer explicit approval markers such as:

- `Status: Approved`
- a review section with a pass verdict
- a phase marker in `workflow-state.json`

If approval is ambiguous, route to the upstream review skill rather than assuming approval.

## Mainline Flow

```text
workflow-starter
-> sdd-work-specify
-> sdd-spec-review
-> sdd-work-design
-> sdd-design-review
-> sdd-work-tasks
-> sdd-tasks-review
-> sdd-work-implement
-> sdd-test-review
-> sdd-code-review
-> sdd-regression-gate
-> sdd-completion-gate
-> sdd-work-finalize
```

## Side Flows

- `change-request.json` -> `sdd-work-increment`
- `hotfix-request.json` -> `sdd-work-hotfix`

Both side flows must return the project to the correct review or implementation phase instead of bypassing the mainline discipline.
