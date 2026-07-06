---
name: discovery-workflow
description: Single-thread sequential planning workflow inspired by D-EPCT+R discovery phase. Loaded by /discovery slash command in both Claude Code and Codex CLI. Use when the user has a new idea, vague project, or wants to go from an idea to actionable stories. Scales with levels 0-4 (tech-spec direct for small scopes, full Brainstorm → PRD → Architecture → Stories chain above), always ends with a consolidated approved-spec output, with validation checkpoints between phases.
---

# Discovery Workflow — Idea to Stories

This skill describes the full product planning workflow enforced by the `/discovery` command. The orchestrator (the model reading this) keeps all context across phases and never forks to subagents for the creative work — only the final GitHub issue creation can be delegated to a separate call.

**Input**: a raw idea, vague project description, or user need passed as arguments after `/discovery`.

**Output**: a coherent set of planning documents (brainstorm → PRD → architecture → stories) and optionally published GitHub issues.

---

## Core Principles

1. **The orchestrator keeps all context** — read-and-write all planning docs in the current context. Don't dispatch to skills that fork the context.
2. **Validation at every phase** — present and wait before moving on. Users may refine scope mid-flow.
3. **Level auto-detection** — the 0-4 grid decides the track (tech-spec direct vs full chain), with automatic escalation reusing acquired work. The user can override.
4. **Skill references, not skill forks** — when writing the PRD, read `.claude/skills/pm-prd/SKILL.md` for structure guidance, but write the content yourself in the current context.

---

## Phase 1 — LISTEN & ASSESS LEVEL

1. Listen to the user's need. They may speak freely (speech-to-text is OK). Don't interrupt.
2. Ask 2-3 clarifying questions only if something is genuinely ambiguous.
3. Assess the discovery level (same 0-4 scale as `dev-workflow`):

| Level | Signals | Discovery track |
|---|---|---|
| **0-1** | 1-2 features, single component, ≤2 screens, no integration, < 1 day | **Tech-spec direct**: skip to Phase 7-bis — write the consolidated spec straight away (no brainstorm, no PRD), 1-2 stories max. |
| **2-3** | 3+ features, multi-component, 3+ screens, or 1+ integration | Full chain: Brainstorm → (UX) → PRD → (UI) → Architecture → Stories. |
| **4** | epic scope, migration, auth/data handling, compliance | Full chain + a formalized **NFR & security requirements** section in the spec (these become quality-gate lens criteria during /dev). |

4. Propose the detected level. The user can override.

**Escalation rule:** if a level-0-1 tech-spec reveals bigger scope while writing it (3+ features, schema changes, multiple journeys), announce it and enter the full chain **reusing the tech-spec as the PRD's input** — never restart.

**STOP CHECKPOINT 1** — Level validated.

---

## Phase 2 — BRAINSTORM (levels 2-4)

1. Load techniques from `.claude/knowledge/brainstorming/brain-techniques.csv`.
2. Propose the 4 session approaches:
   - **[1]** User-Selected — user picks techniques
   - **[2]** AI-Recommended — suggest techniques suited to the problem
   - **[3]** Random Discovery — unexpected perspectives
   - **[4]** Progressive Flow — 4-phase creative journey
   - **[R]** Research-first — validate hypotheses before creative work
3. Facilitate interactively:
   - Target 50+ raw ideas before organization
   - Anti-bias: pivot domains every 10 ideas
   - Energy checkpoints every 4-5 exchanges
4. Synthesize: top 5 ideas, emerging themes, recommended direction.
5. Save to `docs/planning/brainstorms/BRAINSTORM-{slug}-{date}.md`.
6. Evaluate if UX/UI phases are needed (see scoring in phase 3 and 5).

Reference: `.claude/skills/idea-brainstorm/SKILL.md` for technique details.

**STOP CHECKPOINT 2** — Brainstorm validated + UX/UI score communicated.

---

## Phase 3 — UX DESIGN (if UX score ≥ 4)

Skip this phase if the project is purely backend/API or if the UX score is below threshold.

Score criteria (1 point each, trigger if ≥ 4):
- Multi-persona product
- Complex user journeys (3+ steps)
- Onboarding flows
- Forms/wizards
- First-time-user experience matters

1. Define personas based on the brainstorm.
2. Design user journeys (main flows).
3. Create textual wireframes (screen architecture).
4. Identify friction points and optimizations.
5. Save to `docs/planning/ux/UX-{slug}.md`.

Reference: `.claude/skills/ux-designer/SKILL.md`.

**STOP CHECKPOINT 3** — UX validated.

---

## Phase 4 — PRD

1. Ask the essential questions (max 3-4 at a time):
   - **Problem**: what problem? For whom? Why now?
   - **Solution**: how is it solved today? What do we propose? What's out of scope?
   - **Success**: how do we know it worked? What are the constraints?
2. Write the PRD: Overview, Users, Features, Requirements, Constraints, Metrics. Level 4 adds the NFR & security requirements section (performance, reliability, security, compliance — each testable).
3. Save to `docs/planning/prd/PRD-{slug}.md`.
4. Evaluate UI need if not already scored.

Reference: `.claude/skills/pm-prd/SKILL.md`, `.claude/knowledge/workflows/prd-template.md`.

**STOP CHECKPOINT 4** — PRD validated.

---

## Phase 5 — UI DESIGN (if UI score ≥ 3)

Skip if not needed.

Score criteria (1 point each, trigger if ≥ 3):
- Design system required
- Brand identity matters
- Custom theming
- Visual consistency across many screens

1. Define color palette and typography.
2. Create main UI components list.
3. Establish visual guidelines.
4. Document interaction patterns.
5. Define design-audit gates for delivery: tokens, components, a11y, taste, Figma/code drift, and AI surface if relevant.
6. If the product is a public site, landing, media, e-commerce, or indexable content surface, define `seo-geo-audit` goals: keywords, SERP, content, schema, llms.txt, AI visibility, GSC KPIs.
7. Save to `docs/planning/ui/UI-{slug}.md`.

Reference: `.claude/skills/ui-designer/SKILL.md`, `.claude/skills/design-audit/SKILL.md`, `.claude/skills/seo-geo-audit/SKILL.md`.

**STOP CHECKPOINT 5** — UI validated.

---

## Phase 6 — ARCHITECTURE (levels 2-4)

1. Analyze the existing codebase (stack, patterns, structure).
2. Propose the technical stack with justifications.
3. Define project structure, data model, APIs.
4. Identify technical risks and mitigations.
5. Save to `docs/planning/architecture/ARCH-{slug}.md`.

Reference: `.claude/skills/architect/SKILL.md`.

**STOP CHECKPOINT 6** — Architecture validated.

---

## Phase 7 — STORIES

1. Identify Epics (functional groups).
2. Create User Stories in INVEST format:
   - **As a** [persona], **I want** [action], **so that** [benefit]
   - Acceptance criteria in Given/When/Then
   - Estimates: XS/S/M/L (L max = 2 days, bigger = split)
3. Save to `docs/stories/EPIC-{num}-{slug}/`.
4. Run the Implementation Readiness Check — require score ≥ 13/15 to proceed.

Reference: `.claude/skills/pm-stories/SKILL.md`.

**STOP CHECKPOINT 7** — Stories validated + Readiness OK.

---

## Phase 7-bis — CONSOLIDATED SPEC (mandatory output, every level)

Whatever the level, discovery ends by writing the consolidated spec that the dev chain consumes:

- File: `docs/planning/specs/YYYY-MM-DD-<slug>-design.md`
- Frontmatter (the `/auto-dev` mandate gate reads exactly these keys):

```yaml
---
title: <need title>
status: draft            # human flips to approved
approved_by: null        # human name — never "ralph"
approved_at: null        # ISO date, set by the human
created_at: <ISO-8601>
slug: <slug>
level: <0-4>
---
```

- Content: PRD synthesis + architecture decisions + acceptance criteria (3-5 sections max). Level 0-1: this IS the whole discovery output. Level 4: include the NFR & security section.
- **Interactive mode**: at the final checkpoint, ask the user to approve — on yes, set `status: approved`, `approved_by: <user>`, `approved_at: <today>`.
- **Autonomous mode** (`/auto-discovery`): always leave `status: draft`, `approved_by: ralph` — a human must approve before `/auto-dev` will start.

**STOP CHECKPOINT 7-bis** — Spec written (and approved in interactive mode).

---

## Phase 8 — PUBLISH TO GITHUB

Create the issues on GitHub. This is mechanical work — it can be done in a single batch.

For each epic, create the epic issue first, then the child stories linked with `Part of #epicNumber`:

```bash
gh issue create --title "[EPIC] <title>" --body "<body>" --label "epic,feature"
gh issue create --title "[STORY-001] <title>" --body "<body>" --label "story" # add "Part of #<epicNum>" in body
```

After creation, present the final summary with all issue numbers and URLs.

---

## Final Summary Format

```markdown
## Discovery Complete

### Generated documents
| Type | File | Status |
|---|---|---|
| Brainstorm | docs/planning/brainstorms/... | ✅/⏭️ |
| UX Design | docs/planning/ux/... | ✅/⏭️ |
| PRD | docs/planning/prd/... | ✅ |
| UI Design | docs/planning/ui/... | ✅/⏭️ |
| Architecture | docs/planning/architecture/... | ✅/⏭️ |
| Stories | docs/stories/EPIC-xxx/ | ✅ |

### GitHub Issues
| Type | Count | Numbers |
|---|---|---|
| Epics | X | #... |
| Stories | X | #... |

### Next step
→ `/dev #<first P0 story>`
```

---

## Anti-patterns

- ❌ Jumping to PRD without brainstorm in FULL mode
- ❌ Writing stories without architecture validation (FULL mode)
- ❌ Publishing to GitHub before the user validates the story list
- ❌ Forking context to a "pm-prd skill execution" — the skill is a reference, you write the PRD in place
