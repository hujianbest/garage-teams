---
name: long-task-requirements
description: "Use when no SRS doc and no design doc and no feature-list.json exist - elicit requirements through structured questioning and produce a high-quality SRS document aligned with ISO/IEC/IEEE 29148"
---

# Requirements Elicitation & SRS Generation

Turn raw ideas into a structured, high-quality Software Requirements Specification (SRS) through systematic elicitation, challenge, and validation — aligned with ISO/IEC/IEEE 29148 and EARS requirement syntax.

<HARD-GATE>
Do NOT invoke any design skill, implementation skill, write any code, scaffold any project, or take any design/implementation action until you have presented the SRS and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need an SRS"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The SRS can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

## Checklist

You MUST create a TodoWrite task for each of these items and complete them in order:

1. **Explore project context** — read existing docs, code, constraints; detect SRS template
2. **Structured elicitation** — ask clarifying questions one at a time, challenge each requirement
3. **Classify requirements** — functional / NFR / constraint / assumption / interface / exclusion
4. **Write requirements** — apply EARS templates, assign IDs, write acceptance criteria, generate diagrams
5. **Validate SRS** — check 8 quality attributes, detect anti-patterns, verify testability
6. **Granularity analysis** — detect oversized FRs via 6 heuristics (G1-G6), decompose candidates, user approval for non-trivial splits
7. **Scope fit & deferral** — assess current-round vs next-round, generate deferred backlog if applicable, update SRS to remove deferred items
8. **SRS Compliance Review** — dispatch srs-reviewer subagent; gate: all R/A/C/S/D/G checks PASS before proceeding
9. **Present & approve SRS** — section-by-section for non-trivial projects
10. **Save SRS & backlog** — `docs/plans/YYYY-MM-DD-<topic>-srs.md` + deferred backlog (if any) and commit
11. **Transition to UCD** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-ucd` (it auto-skips to design if no UI features in SRS)

**The terminal state is invoking long-task-ucd.** Do NOT invoke any other skill.

## Step 1: Explore Context

1. Read the user-provided requirement doc / idea description thoroughly
2. Explore existing code / repos the project will build on or integrate with
3. Identify initial constraints: tech stack, platform, integrations, regulations
4. Check for an SRS template:
   - If the user specified a template path → read and validate it
   - Else → read `docs/templates/srs-template.md` (the default template shipped with this skill)
   - **Validation**: template must be a `.md` file containing at least one `## ` heading

## Step 2: Structured Elicitation

Use `AskUserQuestion` to elicit requirements in **multi-question rounds** — each round covers one topic area with up to 4 related questions. Follow the CAPTURE → CHALLENGE → CLARIFY cycle for each area.

**How to ask:**
- **Batch by topic** — group 2-4 related questions into a single `AskUserQuestion` call per round
- **Multiple choice preferred** — provide 2-4 options per question to reduce cognitive load
- **Assume and confirm** — state your assumption, let the user correct
- **Scenario-based for edge cases** — "What should happen when [X] fails?"
- **Quantify immediately** — replace vague words with numbers in the question itself
- **Follow up within round** — if an answer in round N reveals ambiguity, address it in round N+1 before moving to the next topic

**Elicitation rounds** (adapt order and grouping to project context):

### Round 1: Purpose & Scope
Ask in a single `AskUserQuestion` call (up to 4 questions):
- What is the core problem this system solves?
- Who are the primary users? (personas, technical levels)
- What is explicitly **out of scope** for this version?
- What is the target release scope? (MVP vs full)

### Round 2–N: Functional Requirements
For each capability area, ask per round (up to 4 questions):
- What does the user do? (trigger/action)
- What does the system do in response? (observable behavior)
- What are the error / edge / boundary cases?
- Confirm a concrete Given/When/Then example

Group related capabilities into the same round when they share a workflow. Split large capability areas across multiple rounds.

### Round N+1: Non-Functional Requirements
Batch NFR probes into 1-2 rounds by relevance:

| Category (ISO 25010) | Probe |
|---|---|
| **Performance** | Response time target? Throughput? Concurrent users? |
| **Reliability** | Uptime target? Recovery time? Data loss tolerance? |
| **Usability** | Accessibility requirements? Learnability criteria? |
| **Security** | Authentication method? Authorization model? Data encryption? |
| **Maintainability** | Modularity constraints? Test coverage targets? |
| **Portability** | Platform restrictions? Browser support? |
| **Scalability** | Current load? Target load? Growth timeline? |

Skip categories clearly irrelevant to the project. **Rule**: Every NFR must have a **measurable criterion**. "Fast" → "p95 response time < 200ms under 1000 concurrent users".

### Round N+2: Constraints, Assumptions & Interfaces
Combine into one round (up to 4 questions):
- Hard limits (hosting, budget, licenses, regulatory, existing systems)
- What is assumed to be true? What breaks if the assumption is wrong?
- External systems to integrate with? Protocols and data formats?
- Existing APIs to preserve backward compatibility?

### Round N+3: Glossary & Terminology
Ask in one round if needed:
- Domain terms with potential ambiguity?
- Synonyms to unify? Homonyms to distinguish?

**When to stop:** Move to Step 3 when you can describe every functional capability, its acceptance criteria, all NFRs with measurable thresholds, all constraints, and all assumptions — without guessing.

**Rule**: Batch related questions per round (2-4 per `AskUserQuestion` call). Only split into single questions when a topic requires deep sequential probing (e.g., complex workflow with branching logic).

## Step 3: Classify Requirements

Organize captured requirements into categories:

| Category | ID Prefix | Description |
|---|---|---|
| Functional | FR-001 | Observable system behaviors |
| Non-Functional | NFR-001 | Quality attributes with measurable criteria |
| Constraint | CON-001 | Hard limits that restrict the solution space |
| Assumption | ASM-001 | Beliefs assumed true; document invalidation risk |
| Interface | IFR-001 | External system contracts |
| Exclusion | EXC-001 | Explicitly out of scope |

## Step 4: Write Requirements with EARS Templates

Apply the EARS (Easy Approach to Requirements Syntax) template to each functional requirement:

| Pattern | Template | When to use |
|---|---|---|
| **Ubiquitous** | The system shall `<action>`. | Always-on behavior |
| **Event-driven** | When `<trigger>`, the system shall `<action>`. | Response to user/system event |
| **State-driven** | While `<state>`, the system shall `<action>`. | Behavior depends on mode/state |
| **Unwanted behavior** | If `<condition>`, then the system shall `<action>`. | Error handling, fault tolerance |
| **Optional** | Where `<feature/config>`, the system shall `<action>`. | Configurable/optional capability |

**For each requirement, also write:**
- **Acceptance criteria** — at least one concrete Given/When/Then scenario
- **Priority** — Must / Should / Could / Won't (MoSCoW)
- **Source** — which stakeholder need or user story this traces to

### 4c. Generate Diagrams

After all requirements are written, generate two Mermaid visual aids and place them in the SRS template sections reserved for them.

#### Use Case View (place in Section 3.1 of the SRS)

Generate one `graph LR` diagram with:
- All actors from Section 3 as external nodes — use ellipse syntax: `Actor((Name))`
- All FR-xxx titles as use case nodes inside a `subgraph System Boundary` enclosure
- One directed edge per actor-to-use-case participation implied by the acceptance criteria
- Every actor must have at least one edge; every FR must appear as a use case node

#### Process Flows (place in Section 4.1 of the SRS)

Generate one `flowchart TD` per functional area. A functional area qualifies if it has:
- 3+ sequential steps, OR
- At least one decision/branching node in its acceptance criteria

Rules per diagram:
- Start node: `([Start: <trigger>])`, End node: `([End: <outcome>])` — rounded stadium style
- Decision node: diamond `{condition?}`, with `-- YES -->` and `-- NO -->` labeled branches
- Every error/boundary case from acceptance criteria must appear as a branch path
- Use a `####` subheading naming each workflow (e.g., `#### Flow: User Registration`)

Scope: one combined flow if the SRS has ≤4 requirements with no branching; one flow per functional area if the SRS has ≥5 requirements across 2+ areas.

## Step 5: Validate SRS Quality

Run a systematic quality check against the **8 quality attributes** (IEEE 830 / ISO 29148):

### 5a. Per-Requirement Checks

For EACH requirement, verify:

| # | Attribute | Check | Red flag |
|---|---|---|---|
| 1 | **Correct** | Traces to a confirmed stakeholder need? | Orphan requirement (gold-plating) |
| 2 | **Unambiguous** | Two readers would write the same test case? | Weasel words: "fast", "robust", "user-friendly", "intuitive", "flexible" |
| 3 | **Complete** | All inputs, outputs, error cases, boundaries defined? | "including but not limited to...", unbounded lists |
| 4 | **Consistent** | No contradiction with other requirements? | Timing conflicts, format conflicts |
| 5 | **Ranked** | Has a MoSCoW priority? | Everything is "high priority" |
| 6 | **Verifiable** | Can write a pass/fail test? | "The system shall be easy to use" (no metric) |
| 7 | **Modifiable** | Stated in exactly one place? | Duplicated across sections |
| 8 | **Traceable** | Has unique ID + source link? | Missing ID or orphan |

### 5b. Anti-Pattern Detection

Scan the full SRS for these anti-patterns and fix before presenting:

| Anti-Pattern | Detection Signal | Fix |
|---|---|---|
| **Ambiguous adjective** | "fast", "large", "scalable", "reliable" without number | Quantify with measurable criterion |
| **Compound requirement** | "and" / "or" joining two distinct capabilities | Split into separate requirements |
| **Design leakage** | Implementation vocabulary: "class", "table", "endpoint", "algorithm" | Rewrite as observable behavior |
| **Passive without agent** | "data shall be validated" — by whom? | Add explicit actor: "The system shall..." |
| **TBD / TBC** | Unresolved placeholders | Resolve with user or mark as Open Question |
| **Missing negatives** | Only positive cases specified | Add error/boundary/security cases |
| **Untestable NFR** | NFR without measurable threshold | Add concrete metric + measurement method |

### 5c. Completeness Cross-Check

- Every functional area has at least one error/boundary case
- All external interfaces have data format + protocol specified
- All NFRs have measurement method, not just target
- Glossary covers all domain-specific terms used in requirements
- Out-of-Scope section explicitly lists deferred features

## Step 5.5: Granularity Analysis & Decomposition

Analyze each FR for hidden complexity that would create oversized features downstream. A well-granulated FR maps cleanly to 1-2 features in `feature-list.json`; an oversized FR hides multiple independently testable behaviors.

### 5.5a. Granularity Heuristics

Apply these heuristics to EACH functional requirement. If ANY heuristic triggers, the FR is a **decomposition candidate**:

| # | Heuristic | Detection Signal | Example |
|---|-----------|-----------------|---------|
| G1 | **Multiple actors** | FR references 2+ distinct user roles performing different actions | "Admin can manage users and end-users can view profiles" |
| G2 | **CRUD bundle** | FR describes Create + Read + Update + Delete as a single requirement | "The system shall manage product inventory" (implies CRUD) |
| G3 | **Scenario explosion** | FR has 4+ acceptance criteria (Given/When/Then blocks) covering distinct behavioral paths | FR with happy path + 3 error cases + 2 boundary cases |
| G4 | **Cross-layer concern** | FR spans both backend logic AND user-facing UI behavior | "Display real-time notifications when order status changes" |
| G5 | **Multi-state behavior** | FR describes behavior across 3+ distinct system states or modes | "While in draft/review/published state, the system shall..." |
| G6 | **Temporal coupling** | FR bundles a trigger event with a deferred/scheduled consequence | "When user registers, send confirmation email and create analytics profile" |

### 5.5b. Decomposition Process

For each decomposition candidate:

1. **Identify atomic behaviors** — each independently testable behavior becomes a candidate sub-requirement
2. **Apply the Single Responsibility Test**: "Can I write ONE focused acceptance test for this sub-requirement without testing unrelated behavior?"
3. **Preserve traceability** — sub-requirements inherit the parent's ID prefix:
   - Parent: `FR-003` → Children: `FR-003a`, `FR-003b`, `FR-003c`
   - Each child gets its own EARS statement, acceptance criteria, and priority
4. **Re-validate children** — each child must independently pass the 8 quality attribute checks from Step 5a
5. **Update diagrams** — if decomposition changes the Use Case View or Process Flows, regenerate affected diagrams

### 5.5c. Decomposition Decision Table

| Candidate Count | Action |
|----------------|--------|
| 0 candidates | Skip — proceed to Step 5.6 |
| 1-3 candidates | Auto-decompose; present rationale inline |
| 4+ candidates | Present candidates to user via `AskUserQuestion` for approval before splitting |

**Rule**: Never auto-split without user awareness. For 1-3 candidates, present rationale inline with the SRS; for 4+, use an explicit approval round.

## Step 5.6: Scope Fit & Deferral

After decomposition, assess whether ALL resulting sub-requirements belong in the current round. Not every sub-requirement needs to ship now — some should be deferred to a future increment for scope control and focus.

### 5.6a. Scope Fit Criteria

For each sub-requirement (and any original FR that was NOT decomposed), evaluate:

| Criterion | Keep in Current Round | Defer to Next Round |
|-----------|----------------------|---------------------|
| **Priority** | Must / Should (MoSCoW) | Could / Won't |
| **Dependency** | Required by other current-round FRs | No current-round FR depends on it |
| **Completeness** | Acceptance criteria fully defined | Needs further elicitation or domain input |
| **Risk** | Well-understood, low uncertainty | High uncertainty, needs prototype/spike first |
| **Scope budget** | Fits within the target feature count (10-50 for MVP) | Would push total beyond manageable scope |

### 5.6b. Deferral Decision

Present the scope fit assessment to the user via `AskUserQuestion`:

```
After granularity analysis, the SRS contains [N] functional requirements.
I recommend keeping [K] in the current round and deferring [D] to a future increment:

**Current Round** (K requirements):
- FR-001: ... (Must, no dependencies on deferred items)
- FR-003a: ... (Must, core workflow)
- FR-003b: ... (Should, needed by FR-005)
...

**Proposed Deferrals** (D requirements):
- FR-003c: Update product (Could, no current-round FR depends on it)
  → Reason: Lower priority, independent of core MVP flow
- FR-003d: Delete product (Could, soft-delete can be added later)
  → Reason: Risk — deletion policy needs business rule clarification
- FR-009: Export reports (Won't for v1)
  → Reason: Scope budget — exceeds MVP target
...

Should I proceed with this split? You can move items between rounds.
```

**Rules:**
- **Must-priority FRs are NEVER auto-deferred** — only the user can defer a Must
- **Dependency integrity** — if FR-X is kept and depends on FR-Y, FR-Y must also be kept
- If user approves 0 deferrals → skip backlog generation, proceed to Step 6
- If user approves 1+ deferrals → proceed to 5.6c

### 5.6c. Generate Deferred Requirements Backlog

For approved deferrals, generate `docs/plans/YYYY-MM-DD-<topic>-deferred.md` using the deferred backlog template:

1. Check for template:
   - If user specified a template → read and validate
   - Else → read `docs/templates/deferred-backlog-template.md`
2. For each deferred requirement, record:
   - Original FR ID and EARS statement (preserved exactly from the SRS draft)
   - Acceptance criteria (preserved exactly)
   - Deferral reason (from 5.6b assessment)
   - Dependencies on current-round requirements (for future impact analysis)
   - Suggested wave (next increment or later)
   - Re-entry hint: what must be true before this requirement can be picked up
3. Update the SRS draft:
   - **Remove** deferred FRs from Section 4 (Functional Requirements)
   - **Add** a reference in Section 1.2 (Out of Scope): `"Deferred to future increment — see [deferred backlog](YYYY-MM-DD-<topic>-deferred.md)"`
   - **Update** diagrams: remove deferred use cases from Use Case View, remove deferred flows from Process Flows
   - **Renumber** remaining FRs if gaps are confusing (optional — user preference)
4. Commit the deferred backlog alongside the SRS

### 5.6d. Backlog-to-Increment Bridge

The deferred backlog is designed to feed directly into the `long-task-increment` skill:

- When the user is ready to pick up deferred requirements, they create `increment-request.json` referencing the backlog:
  ```json
  {
    "reason": "Pick up deferred requirements from wave 0",
    "scope": "See docs/plans/YYYY-MM-DD-<topic>-deferred.md",
    "changes": ["new"]
  }
  ```
- The increment skill reads the backlog, skips re-elicitation for requirements that already have complete EARS + acceptance criteria, and proceeds directly to impact analysis
- After increment processing, mark picked-up items in the backlog as `status: "incorporated"` with the wave number and date

**Rule**: The deferred backlog is a living document. Each increment that picks up items updates it. When all items are incorporated or explicitly dropped, the backlog is archived.

## Step 6: SRS Compliance Review

Dispatch a subagent to independently verify the SRS against ISO/IEC/IEEE 29148 standards and diagram requirements before presenting to the user. This is mandatory — self-validation in Step 5 is not a substitute.

### 6a. Dispatch SRS Reviewer Subagent

```
Task(
  subagent_type="general-purpose",
  prompt="""
  You are an SRS compliance reviewer aligned with ISO/IEC/IEEE 29148.
  Read the reviewer prompt at: skills/long-task-requirements/prompts/srs-reviewer-prompt.md

  Project context:
  {project_context}

  Full SRS draft (all sections):
  {srs_draft}

  Requirement ID list:
  {requirement_id_list}

  Perform the review following the prompt exactly.
  """
)
```

### 6b. Review Gate Logic

**ALL checks must PASS to proceed to Step 7:**
- Group R (R1-R8): quality attributes — every requirement passes all 8 checks
- Group A (A1-A6): anti-patterns — none found in the full SRS
- Group C (C1-C5): completeness — all cross-checks confirmed
- Group S (S1-S4): structural compliance — all required sections present
- Group D (D1-D4): diagrams — Use Case View and Process Flows present and populated
- Group G (G1-G3): granularity — no oversized FRs remain (post-decomposition/deferral)

**On FAIL — two-track resolution:**

**Track 1: USER-INPUT items → ask immediately**

Read the reviewer's "Clarification Questions" table. If any rows are present (USER-INPUT items exist):

Use `AskUserQuestion` with a targeted questionnaire — do NOT dump the full review report. Format:
```
The SRS needs clarification on a few points before I can finalize it. Please answer:

1. [FR-xxx] [Issue in plain language]
   Your requirement says "[exact phrase]". What is the correct value?
   (e.g., [example format/unit])

2. [FR-yyy] [Next issue]
   ...
```

**Do NOT guess or invent answers. WAIT for the user's response before proceeding.**

After receiving answers: incorporate them into the SRS draft.

**Track 2: LLM-FIXABLE items → auto-fix**

Fix all LLM-FIXABLE items in parallel: split compound requirements, add actors, populate sections, generate diagrams, assign IDs. Apply these together with any user answers from Track 1.

**Re-dispatch reviewer (Cycle 2)**

Re-dispatch the subagent with the revised draft. If Cycle 2 PASS → proceed to Step 7.

**If Cycle 2 still fails:**
- New USER-INPUT items found → use `AskUserQuestion` again with the same targeted format
- Only LLM-FIXABLE items remain after 2 cycles → use `AskUserQuestion` with:
  - Table of remaining failures (check ID, location, issue description)
  - Summary of fixes attempted
  - Request for user direction (fix, waive, or restructure)

**Maximum: 2 re-dispatch cycles.** Never attempt Cycle 3 without user input.

After all groups PASS, record the review outcome in the SRS header:
```markdown
<!-- SRS Review: PASS after N cycle(s) — YYYY-MM-DD -->
```

## Step 7: Present & Approve SRS

For non-trivial projects, present section by section and get approval per section:

1. **Purpose, Scope & Exclusions** — boundaries and what's NOT included
2. **Glossary & User Personas** — shared vocabulary and user understanding
3. **Functional Requirements** — core capabilities with acceptance criteria
4. **Non-Functional Requirements** — quality attributes with metrics
5. **Constraints, Assumptions & Interfaces** — hard limits and external contracts

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

**For simple projects** (< 5 functional requirements): combine all sections into a single approval step.

## Step 8: Save SRS Document & Deferred Backlog

Save the approved SRS to `docs/plans/YYYY-MM-DD-<topic>-srs.md`.

### Template usage

Read the template found in Step 1 (user-specified or default `docs/templates/srs-template.md`):
1. Preserve the template's heading structure
2. Replace guidance text under each heading with approved SRS content
3. Add metadata at top if not already present (`Date`, `Status`, `Standard`, `Template` path)
4. For uncovered template sections: mark "[Not applicable]"
5. For approved content without matching template section: append as "Additional Notes"

### Deferred backlog (if generated in Step 5.6)

If a deferred backlog was generated, save it alongside the SRS:
- Path: `docs/plans/YYYY-MM-DD-<topic>-deferred.md`
- Commit both files together in the same commit

## Step 9: Transition to UCD

Once the SRS document (and deferred backlog, if any) is saved and committed:

1. Summarize key inputs the next phase will need:
   - Functional requirement count and priority distribution
   - Key constraints that affect architecture choices
   - NFR thresholds that affect technology selection
   - Whether the SRS contains UI-related functional requirements (determines if UCD runs or auto-skips)
   - Whether a deferred backlog exists (signals future increment potential)
2. **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-ucd` to generate UCD style guide (auto-skips to design if no UI features)

## Scaling the Requirements Phase

| Project Size | Functional Reqs | Depth |
|---|---|---|
| Tiny | 1-5 | Single-page SRS, combined approval step |
| Small | 5-15 | Standard SRS, 2-3 approval sections |
| Medium | 15-50 | Full SRS with all sections, per-section approval |
| Large | 50-200+ | Full SRS + interface specs + domain model |

## Red Flags

| Rationalization | Correct Response |
|---|---|
| "This is too simple for an SRS" | Run lightweight SRS (single approval step) |
| "The user already described what they want" | User descriptions are raw input; SRS adds structure, completeness, testability |
| "I can figure out the requirements during design" | Requirements define WHAT; discovering them during HOW causes rework |
| "NFRs don't apply to this project" | Every project has at least implicit performance/reliability needs — make them explicit |
| "The glossary is obvious" | Obvious to whom? Define every term the user and developer might interpret differently |
| "I'll just start with the happy path" | Error cases, boundaries, and negatives must be captured NOW |
| "This FR is fine as one big requirement" | Apply the 6 granularity heuristics (G1-G6) — hidden complexity creates oversized features |
| "All requirements belong in this round" | Scope fit assessment (Step 5.6) ensures focus — defer lower-priority items to maintain manageable scope |
| "Deferred items can just go in Out-of-Scope" | Out-of-Scope is prose; the deferred backlog preserves EARS + acceptance criteria for seamless increment pickup |

## Integration

**Called by:** using-long-task (when no SRS doc, no design doc, and no feature-list.json)
**Chains to:** long-task-ucd (after SRS approval; auto-skips to design if no UI features)
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-srs.md`, optionally `docs/plans/YYYY-MM-DD-<topic>-deferred.md`
