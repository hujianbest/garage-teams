# MDC Contract Template

Use this file when a project needs an explicit mapping between MDC logical artifacts and the team's existing deliverables.

```markdown
# MDC Contract

## Project

- Name: <project-name>
- Status: Draft | Active
- Owner: <team-or-person>

## Artifact Mapping

| Logical Artifact | Actual Path | Approval Signal | Required |
|---|---|---|---|
| Requirement spec | `docs/specs/<file>.md` | `Status: Approved` | Yes |
| Design doc | `docs/designs/<file>.md` | `Status: Approved` | Yes |
| Task plan | `docs/tasks/<file>.md` | `Status: Approved` or tasks-review PASS | Yes |
| Progress log | `task-progress.md` | N/A | Yes |
| Release notes | `RELEASE_NOTES.md` | N/A | Recommended |
| Review records | `docs/reviews/` | PASS / REVISE / BLOCKED | Recommended |
| Verification records | `docs/verification/` | command output summary | Recommended |

## Routing Evidence

| Purpose | Path | Notes |
|---|---|---|
| Progress / current status | `task-progress.md` or equivalent | Main routing evidence source |
| Review records | `docs/reviews/` | Phase approval evidence |
| Verification records | `docs/verification/` | Regression / completion evidence |
| Release notes | `RELEASE_NOTES.md` | User-visible completion evidence |

## Phase Rules

1. No design before approved requirement spec
2. No task planning before approved design
3. No implementation before approved task plan
4. No completion claim without regression and completion gates

## Approved Means

Use these signals in this project:

- `Status: Approved`
- review record with `PASS`
- progress or verification record phase marker

## Notes

- List any project-specific exceptions here
- Document any artifact naming deviations here
```

## Usage Notes

- Keep the contract short and stable
- Update it only when artifact paths or approval rules change
- Prefer mapping existing documents over introducing duplicate deliverables
