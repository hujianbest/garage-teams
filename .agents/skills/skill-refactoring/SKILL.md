---
name: skill-refactoring
description: Restructure bloated skills into lean SKILL.md (~150-200 lines) + references/ directory architecture. Use when a skill has grown past ~300 lines, has redundant sections, or mixes orchestration logic with reference material. Follows the pattern proven by architecture-designer (117-line SKILL.md + 541 lines in 5 reference files).
version: 1.0.0
---

# Skill Refactoring — Slim SKILL.md + References Pattern

Restructure bloated skills into "lean SKILL.md + references/" architecture.

## When to Use

- A skill has grown past ~300 lines and contains repetitive or deeply detailed content
- Multiple sections say the same thing in different words (redundancy audit needed)
- The skill mixes orchestration logic with reference material that's only needed sometimes
- After evolving a skill through multiple patches and it needs a cleanup pass

## Process

### 1. Size and Structure Audit

Count lines of SKILL.md and any existing references. Compare against target: SKILL.md ~150-200 lines, details in references/.

### 2. Identify Redundancies (Three-Category Analysis)

For each section, ask: "Does this say something another section already says?"

Common redundancy patterns:
- **Overview + Quality Bar + Verification** — three sections restating the same quality criteria
- **Standalone Contract + When to Use "don't use"** — overlapping preconditions
- **Common Rationalizations + MUST NOT DO + Red Flags** — three lists of anti-patterns
- **Inputs/Required Artifacts + Output Contract** — artifact paths mentioned in both

Action: Pick ONE canonical location for each concept, delete or merge duplicates.

### 3. Identify Extractable Content

Content that belongs in `references/` (loaded on demand):
- Templates (ADR, design doc, checklists)
- Detailed tables (pattern comparison, failure modes, NFR categories)
- Examples (Mermaid diagrams, code samples)
- Step-by-step guides consulted, not memorized

Rule of thumb: If the agent only needs it for specific workflow steps, not for every invocation → extract to references/.

### 4. Add Reference Guide Table

In SKILL.md, add:

```markdown
## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| ... | `references/xxx.md` | When doing X |
```

This replaces inline content with a pointer system.

### 5. Rewrite SKILL.md

Keep always-loaded content: description, When to Use, Contracts, Constraints, Core Workflow (concise steps), Red Flags, Output Contract, Reference Guide.

### 6. Validate

- Structure is sequential (no broken numbering)
- No content lost (everything kept inline or extracted)
- References loadable (correct paths)
- Total content preserved or improved

## Metrics

Target: SKILL.md 60-70% reduction. Total 20-30% reduction from removing redundancy. references/ 5-6 files, 150-200 lines total.

## Pitfalls

- Don't extract content needed on EVERY invocation (MUST DO, Red Flags, workflow steps)
- Don't create references/ files < 20 lines — keep that inline
- Don't lose the Reference Guide table — without it, the agent won't know references exist
- Don't refactor during active use — do it between task sessions
