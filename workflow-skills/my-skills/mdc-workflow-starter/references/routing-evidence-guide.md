# MDC Routing Evidence Guide

Use this guide when a project adopts the MDC skills set but has not yet standardized its artifact layout or routing evidence.

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

## Minimum Routing Evidence

Prefer existing project artifacts over introducing dedicated root-level JSON signal files.

Recommended routing evidence:

- requirement spec, design doc, and task plan approval state
- progress log such as `task-progress.md`
- review records under `docs/reviews/`
- verification records under `docs/verification/`
- explicit user request indicating a change request or hotfix

## Recommended Routing Inputs

At session start, `sdd-workflow-starter` should inspect only:

1. the MDC contract
2. the existence and approval state of spec/design/task artifacts
3. progress, review, and verification records
4. the user's current request

Avoid broad code exploration before phase routing is complete.

## Approval Signals

Prefer explicit approval markers such as:

- `Status: Approved`
- a review section with a pass verdict
- a phase marker in a progress or verification record

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

- explicit change request -> `mdc-increment`
- explicit hotfix request -> `mdc-hotfix`

Both side flows must return the project to the correct review or implementation phase instead of bypassing the mainline discipline.
