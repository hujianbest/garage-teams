# Signal File Templates

Use these templates for the root-level state and signal files that drive SDD routing.

## `workflow-state.json`

Purpose: record the current phase, approved artifacts, and next recommended skill.

```json
{
  "project": "project-name",
  "topic": "current-topic-or-feature",
  "phase": "specify|spec-review|design|design-review|tasks|tasks-review|implement|test-review|code-review|regression-gate|completion-gate|finalize",
  "approved_artifacts": {
    "requirement_spec": false,
    "design_doc": false,
    "task_plan": false
  },
  "current_task": {
    "id": "TASK-001",
    "title": "Example task",
    "status": "pending|in_progress|blocked|completed"
  },
  "next_skill": "sdd-work-specify",
  "last_updated": "2026-03-26"
}
```

Notes:

- `phase` is the main routing hint, but should not override contradictory artifact evidence
- `next_skill` is advisory, not absolute

## `change-request.json`

Purpose: trigger the increment flow for scope or requirement changes.

```json
{
  "reason": "Add a new requirement or modify approved scope",
  "requested_by": "user-or-team",
  "requested_at": "2026-03-26",
  "change_type": "new-requirement|scope-change|acceptance-change|deferred-item-return",
  "summary": "Short summary of the requested change",
  "details": [
    "Specific change detail 1",
    "Specific change detail 2"
  ],
  "affected_artifacts": [
    "requirement-spec",
    "design-doc",
    "task-plan"
  ]
}
```

Notes:

- Keep this focused on WHAT changed, not HOW to implement it
- The increment skill performs impact analysis; the request file should not pre-judge the routing outcome

## `hotfix-request.json`

Purpose: trigger the hotfix flow for urgent defects.

```json
{
  "severity": "critical|high|medium",
  "reported_at": "2026-03-26",
  "reported_by": "user-or-team",
  "summary": "Short bug summary",
  "expected_behavior": "What should happen",
  "actual_behavior": "What is happening instead",
  "impact": "Why this is urgent",
  "known_reproduction": [
    "Step 1",
    "Step 2"
  ]
}
```

Notes:

- A hotfix request should describe the defect clearly enough to reproduce
- The hotfix skill still requires reproduction, review, regression checks, and completion gating

## Recommended Handling Rules

1. Keep signal files at the project root unless the SDD contract says otherwise
2. Delete or archive signal files after they have been processed
3. Do not leave stale `change-request.json` or `hotfix-request.json` files in place, or routing will become noisy
