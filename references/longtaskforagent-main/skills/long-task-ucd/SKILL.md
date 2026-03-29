---
name: long-task-ucd
description: "Use when SRS doc exists but no UCD doc and no design doc and no feature-list.json - generate UI Component Design style guide with text-to-image prompts based on approved SRS"
---

# UI Component Design (UCD) Style Guide Generation

Take the approved SRS as input. Analyze UI-related requirements, define visual style direction, and produce a UCD style guide containing text-to-image model prompts — so that all frontend features share a unified visual language.

<HARD-GATE>
Do NOT invoke any design skill, implementation skill, write any code, scaffold any project, or take any implementation action until you have presented the UCD style guide and the user has approved it. This applies to EVERY project with UI features.
</HARD-GATE>

## When This Phase Applies

This phase runs **after SRS approval** and **before design**. It applies when:
- The approved SRS contains UI-related functional requirements (FR-xxx with user-facing screens, pages, or components)
- No UCD document (`*-ucd.md`) exists in `docs/plans/`

**If the SRS has NO UI features**: announce "No UI features detected in SRS — skipping UCD phase" and immediately chain to design via `long-task:long-task-design`.

## Checklist

You MUST create a TodoWrite task for each of these items and complete them in order:

1. **Read the approved SRS** — from `docs/plans/*-srs.md`
2. **Extract UI scope** — identify all UI-related requirements and user personas
3. **Define visual style direction** — propose 2-3 style options with mood boards
4. **Generate component-level prompts** — text-to-image prompts for each UI component type
5. **Generate page-level prompts** — text-to-image prompts for each key page/screen
6. **Define style tokens** — color palette, typography, spacing, iconography
7. **Present & approve UCD** — section-by-section for non-trivial projects
8. **Save UCD document** — `docs/plans/YYYY-MM-DD-<topic>-ucd.md` and commit
9. **Transition to design** — **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-design`

**The terminal state is invoking long-task-design.** Do NOT invoke any other skill.

## Step 1: Read SRS & Extract UI Scope

1. Read the approved SRS document from `docs/plans/*-srs.md`
2. Extract UI-relevant inputs:
   - **User personas** — technical level, accessibility needs, device preferences
   - **Functional requirements with UI** — screens, pages, forms, dashboards, data visualizations
   - **NFR usability requirements** — accessibility standards (WCAG level), responsive breakpoints, internationalization
   - **Constraints** — brand guidelines, platform restrictions, browser support
   - **Interface requirements** — external UI components, design systems to integrate with
3. Build a **UI inventory** — list every distinct screen/page/component type implied by the SRS
4. If the SRS lacks sufficient UI detail → ask user via `AskUserQuestion` before proceeding

## Step 2: Define Visual Style Direction

Present **2-3 visual style options** to the user:

```markdown
## Style A: [Name] (e.g., "Clean Corporate", "Bold Modern", "Soft Minimal")
**Mood**: [1-2 sentences describing the visual feel]
**Color direction**: [primary palette tendency — warm/cool/neutral, high/low contrast]
**Typography direction**: [serif/sans-serif, geometric/humanist, density]
**Layout direction**: [card-based/list-based, dense/spacious, fixed/fluid]
**Target persona fit**: [which SRS user personas this serves best]
**Reference style**: [existing design language this draws from — Material, Ant, Apple HIG, etc.]

## Style B: [Name]
...

## Recommendation: Style [X]
**Reason**: [why this fits the SRS personas, constraints, and NFRs best]
```

Wait for user to choose or provide direction. Incorporate feedback before proceeding.

## Step 3: Generate Style Tokens

Define the concrete design tokens that anchor the entire style system:

### 3.1 Color Palette

```markdown
| Token | Hex | Usage | Contrast Ratio |
|-------|-----|-------|----------------|
| --color-primary | #XXXXXX | Primary actions, links, active states | >= 4.5:1 on white |
| --color-primary-hover | #XXXXXX | Hover state for primary | |
| --color-secondary | #XXXXXX | Secondary actions, accents | >= 4.5:1 on white |
| --color-bg-primary | #XXXXXX | Main background | |
| --color-bg-secondary | #XXXXXX | Card/section background | |
| --color-text-primary | #XXXXXX | Body text | >= 4.5:1 on bg-primary |
| --color-text-secondary | #XXXXXX | Captions, hints | >= 3:1 on bg-primary |
| --color-success | #XXXXXX | Success states | |
| --color-warning | #XXXXXX | Warning states | |
| --color-error | #XXXXXX | Error states, destructive actions | |
| --color-border | #XXXXXX | Default borders | |
```

- All contrast ratios MUST meet WCAG AA at minimum (4.5:1 for normal text, 3:1 for large text)
- If SRS specifies WCAG AAA, ratios must be 7:1 / 4.5:1

### 3.2 Typography Scale

```markdown
| Token | Font Family | Size | Weight | Line Height | Usage |
|-------|-------------|------|--------|-------------|-------|
| --font-heading-1 | [family] | [size] | [weight] | [lh] | Page titles |
| --font-heading-2 | [family] | [size] | [weight] | [lh] | Section headings |
| --font-heading-3 | [family] | [size] | [weight] | [lh] | Card titles |
| --font-body | [family] | [size] | [weight] | [lh] | Body text |
| --font-body-small | [family] | [size] | [weight] | [lh] | Captions, hints |
| --font-label | [family] | [size] | [weight] | [lh] | Form labels, buttons |
| --font-code | [family] | [size] | [weight] | [lh] | Code snippets |
```

### 3.3 Spacing & Layout

```markdown
| Token | Value | Usage |
|-------|-------|-------|
| --space-xs | [value] | Tight inner padding |
| --space-sm | [value] | Default inner padding |
| --space-md | [value] | Section gaps |
| --space-lg | [value] | Page section margins |
| --space-xl | [value] | Major layout breaks |
| --radius-sm | [value] | Buttons, inputs |
| --radius-md | [value] | Cards |
| --radius-lg | [value] | Modals, dialogs |
| --shadow-sm | [value] | Subtle elevation |
| --shadow-md | [value] | Cards, dropdowns |
| --shadow-lg | [value] | Modals, overlays |
```

### 3.4 Iconography & Imagery

```markdown
- **Icon style**: [outlined/filled/duotone] [rounded/sharp] [stroke weight]
- **Icon library**: [recommended library with version, e.g., Lucide Icons 0.263.0]
- **Illustration style**: [flat/isometric/3D/hand-drawn] [color treatment]
- **Photography treatment**: [if applicable — filters, overlays, cropping rules]
```

## Step 4: Generate Component-Level Prompts

For each UI component type in the inventory, produce a **text-to-image prompt** that a generative image model (Midjourney, DALL-E, Stable Diffusion, etc.) can use to visualize the component.

### Prompt Structure

Each component prompt follows this template:

```markdown
### Component: [Component Name]
**SRS Trace**: [FR-xxx, NFR-xxx]
**Variants**: [list variants — default, hover, active, disabled, error, loading]

#### Base Prompt
> [Detailed text-to-image prompt describing the component's visual appearance in the approved style. Include: layout structure, color tokens by name, typography tokens, spacing, border treatment, shadow, state indicators. Be specific about proportions, alignment, and visual hierarchy.]

#### Variant Prompts
> **Hover state**: [prompt delta from base]
> **Error state**: [prompt delta from base]
> **Loading state**: [prompt delta from base]
> **Dark mode** (if applicable): [prompt delta from base]

#### Style Constraints
- [Constraint 1 — e.g., "Button height must be exactly 40px for touch targets"]
- [Constraint 2 — e.g., "Error text must appear below the input, never as tooltip"]
```

### Required Component Types

Generate prompts for at least these component types (skip only if truly absent from the UI inventory):

| Category | Components |
|----------|-----------|
| **Navigation** | Header/navbar, sidebar, breadcrumb, tabs, pagination |
| **Input** | Text input, textarea, select/dropdown, checkbox, radio, toggle, date picker |
| **Action** | Primary button, secondary button, icon button, link button, FAB |
| **Feedback** | Alert/toast, modal/dialog, progress bar, skeleton loader, empty state |
| **Data Display** | Table, card, list item, badge/tag, avatar, tooltip |
| **Layout** | Page shell, form layout, grid/masonry, divider |

## Step 5: Generate Page-Level Prompts

For each key page/screen identified in the UI inventory, produce a **full-page text-to-image prompt**.

### Page Prompt Structure

```markdown
### Page: [Page Name]
**SRS Trace**: [FR-xxx]
**User Persona**: [primary persona for this page]
**Entry Points**: [how users arrive at this page]

#### Layout Description
[Describe the page layout: header placement, content zones, sidebar (if any), footer. Specify grid structure, responsive behavior at key breakpoints.]

#### Full-Page Prompt
> [Detailed text-to-image prompt for the complete page. Reference component names defined in Step 4. Describe spatial relationships, visual hierarchy, content flow, key interactions. Include responsive notes for mobile/tablet if applicable.]

#### Key Interactions
- [Interaction 1 — e.g., "Clicking row in table opens detail panel on right"]
- [Interaction 2 — e.g., "Form validates on blur, shows inline errors"]

#### Responsive Behavior
- **Desktop (>= 1024px)**: [layout description]
- **Tablet (768-1023px)**: [layout changes]
- **Mobile (< 768px)**: [layout changes]
```

## Step 6: Present & Approve UCD

For non-trivial projects, present section by section:

1. **Visual style direction** — mood, color tendency, typography direction
2. **Style tokens** — color palette, typography scale, spacing, iconography
3. **Component prompts** — one or two representative components for approval before generating the rest
4. **Page prompts** — key pages for approval

Present each section. Wait for user feedback. Incorporate changes before moving to the next.

**For simple projects** (< 3 UI pages): combine all sections into a single approval step.

## Step 7: Save UCD Document

Save the approved UCD style guide to `docs/plans/YYYY-MM-DD-<topic>-ucd.md`.

Document structure:

```markdown
# <Project Name> — UCD Style Guide

**Date**: YYYY-MM-DD
**Status**: Approved
**SRS Reference**: docs/plans/YYYY-MM-DD-<topic>-srs.md

## 1. Visual Style Direction
[Chosen style, rationale]

## 2. Style Tokens
### 2.1 Color Palette
### 2.2 Typography Scale
### 2.3 Spacing & Layout
### 2.4 Iconography & Imagery

## 3. Component Prompts
### 3.1 [Component Name]
...

## 4. Page Prompts
### 4.1 [Page Name]
...

## 5. Style Rules & Constraints
[Cross-cutting rules: accessibility, animation, responsive, dark mode]
```

## Step 8: Transition to Design

Once the UCD document is saved and committed:

1. Summarize key inputs the design phase will need:
   - **From SRS**: functional requirements, NFRs, constraints
   - **From UCD**: style tokens, component catalog, page layouts → informs UI/UX section and frontend architecture in design doc
2. **REQUIRED SUB-SKILL:** Invoke `long-task:long-task-design` to begin design

## Scaling the UCD Phase

| Project Size | UI Pages | Depth |
|---|---|---|
| Tiny | 1-3 | Style tokens + 3-5 core component prompts + page prompts; single approval step |
| Small | 3-8 | Full style tokens + component prompts for used components + all page prompts |
| Medium | 8-20 | Full UCD with all component variants + responsive page prompts |
| Large | 20+ | Full UCD + interaction state matrices + animation spec + dark mode variants |

## Red Flags

| Rationalization | Correct Response |
|---|---|
| "The UI is simple, skip UCD" | Even simple UIs need a consistent style — run lightweight UCD |
| "I'll define styles during implementation" | Ad-hoc styling causes visual inconsistency across features |
| "The user will pick a UI library, that's enough" | UI libraries need configuration — UCD provides those values |
| "Style tokens are premature" | Tokens are cheaper to define now than to retrofit across 20 components |
| "Let me just use default Material/Ant styles" | Defaults are a valid starting point but must be documented as the explicit choice |
| "The SRS doesn't mention colors" | SRS defines WHAT; UCD defines the visual HOW; both are needed for UI projects |

## Prompt Writing Rules

1. **Be specific, not vague** — "a rounded-corner card with 8px radius, 1px solid #E5E7EB border, 16px padding, white background with 0 2px 4px rgba(0,0,0,0.05) shadow" beats "a nice card"
2. **Reference tokens, not raw values** — use token names in prompts so design changes propagate: "using --color-primary for the button fill"
3. **Include spatial relationships** — "the icon is 16px, positioned 8px left of the label text, vertically centered"
4. **Describe states, not just defaults** — every interactive element needs hover, active, disabled, error states
5. **Specify responsive intent** — how the component/page adapts at each breakpoint
6. **Anchor to SRS personas** — prompts should serve the defined user types (e.g., larger touch targets for mobile-primary users)

## Integration

**Called by:** using-long-task (when SRS exists, no UCD doc, no design doc, no feature-list.json — and SRS contains UI features) or long-task-requirements (Step 8 chains here)
**Requires:** Approved SRS at `docs/plans/*-srs.md`
**Chains to:** long-task-design (after UCD approval)
**Produces:** `docs/plans/YYYY-MM-DD-<topic>-ucd.md`
**Referenced by:**
- long-task-design (UI/UX section references UCD style tokens and component catalog)
- long-task-work (frontend features reference UCD for style consistency)
- Inline Check (UCD token grep in Worker Step 10)
