# Routing Evidence Examples

This file provides lightweight examples of routing evidence for MDC setups that do not rely on root-level JSON signal files.

Current MDC guidance is: do not depend on root-level JSON signal files for routing.

Prefer these evidence sources instead:

- approved spec / design / task artifacts
- progress records such as `task-progress.md`
- review records under `docs/reviews/`
- verification records under `docs/verification/`
- explicit user requests indicating change or hotfix intent

## Recommended Alternatives

### Progress Record Example

```markdown
## Current Phase

- phase: implement
- active task: TASK-003
- next skill: mdc-bug-patterns

## Approved Artifacts

- requirement spec: approved
- design doc: approved
- task plan: approved
```

### Change Request Example

```markdown
## Change Summary

- requested by:
- requested at:
- summary:

## Affected Areas

- requirement spec
- design doc
- task plan
```

### Hotfix Request Example

```markdown
## Hotfix Summary

- severity:
- summary:
- expected behavior:
- actual behavior:
- impact:
```

## Recommended Handling Rules

1. Prefer updating existing project artifacts over creating extra routing files
2. Keep routing evidence close to the deliverables it describes
3. Avoid stale side-channel trigger files that can mislead routing
