---
name: sdd-workflow-starter
description: Route SDD-governed software work to the correct phase before any other action. Use at the start of any software delivery request involving requirements, specs, design, task planning, implementation, changes, bug fixes, or when the user says continue/start/推进/继续开发 in a project following SDD.
---

# SDD Workflow Starter

Use this skill before any SDD phase work.

## Purpose

Your job is not to implement. Your job is to determine the current phase, identify the correct next skill, and prevent out-of-order work.

This skill is the entry gate for an SDD workflow:

`work-specify -> spec-review -> work-design -> design-review -> work-tasks -> work-implement -> test/code/regression/completion gates`

Change requests and hotfixes are routed to dedicated side flows.

## Iron Rule

Do not clarify requirements, inspect code deeply, design, plan, or implement until you have routed the session to the correct phase.

If there is any doubt, resolve the phase first.

## What To Read First

Read only the minimum needed to route:

1. `workflow-state.json` if it exists
2. `change-request.json` if it exists
3. `hotfix-request.json` if it exists
4. The mapped artifact locations from the project's SDD contract, if present
5. Existing approved spec/design/task artifacts only as needed to determine whether they exist and whether they are approved

Do not start broad codebase exploration during routing.

## Additional Resources

Read these references when the project has no established SDD contract yet, or when signal/state file formats are unclear:

- `references/sdd-entry-guide.md`
- `references/sdd-contract-template.md`
- `references/signal-file-templates.md`

Use them to standardize artifact locations and state files before the workflow grows inconsistent.

## Routing Order

Check in this exact order:

1. If `hotfix-request.json` exists -> route to `sdd-work-hotfix`
2. Else if `change-request.json` exists -> route to `sdd-work-increment`
3. Else if there is no approved requirement spec -> route to `sdd-work-specify`
4. Else if there is no approved implementation design -> route to `sdd-work-design`
5. Else if there is no approved task plan -> route to `sdd-work-tasks`
6. Else if there are unfinished planned tasks -> route to `sdd-work-implement`
7. Else if implementation exists but lacks fresh verification evidence -> route to `sdd-completion-gate`
8. Else route to `sdd-work-finalize`

## Approved Means

Do not assume approval from chat history alone. Prefer explicit evidence in artifacts:

- `Status: Approved`
- an approval section or review record
- a state marker in `workflow-state.json`

If status is unclear, treat the artifact as not approved.

## Output Contract

After routing, report:

1. Current detected phase
2. Evidence used for the decision
3. The single next skill to use
4. What artifact is missing or blocking, if any

Use concise wording. Example:

```markdown
Current phase: requirements not yet approved.

Evidence:
- No approved requirement spec found
- No change or hotfix signal file found

Next skill: `sdd-work-specify`
```

## Red Flags

- User says "continue" and you jump into code
- A spec exists but is still draft, and you treat it as approved
- You start reading implementation files before deciding the phase
- You route to implementation because it feels faster

## Handoff

Once routing is complete, immediately use the routed skill and follow it exactly.
