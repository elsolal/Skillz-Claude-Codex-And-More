---
name: dev-workflow
description: Single-thread sequential feature development workflow inspired by D-EPCT+R. Loaded by /dev slash command in both Claude Code and Codex CLI. Use when the user wants to implement a feature, fix a bug described at higher level than /quick-fix, or work on a GitHub issue. Enforces Explore → Plan → Implement → Review ×3 → Ship with validation checkpoints between phases.
---

# Dev Workflow — Feature Implementation

This skill describes the full feature-development workflow enforced by the `/dev` command. It is runtime-agnostic: both Claude Code and Codex CLI execute it sequentially, without relying on parallel subagent dispatch. The rigor of D-EPCT+R (stop checkpoints, 3-pass review) is preserved — only the execution pattern changes from parallel subagents to sequential in-context phases.

**Input**: a task description, issue reference (e.g. `#42`), or feature description passed as arguments after the `/dev` invocation.

**Output**: implemented + tested + reviewed code, ready to `/ship`.

---

## Core Principles

1. **The orchestrator keeps all context** — never fork the main context to a subagent for planning or review. The model executing this workflow is the orchestrator.
2. **Stop checkpoints are mandatory** — present findings and wait for validation at each `STOP CHECKPOINT`. Do not skip ahead.
3. **Explicit phase boundaries** — even though execution is sequential, treat each phase as a distinct mental context. Between phases, summarize what was done before starting the next.
4. **Read before write** — always understand existing code before modifying it. This is non-negotiable.
5. **Lint + types pass at every step** — never leave the codebase in a broken state between phases.

---

## Phase 1 — EXPLORE

**Goal**: build a complete mental model of the codebase relevant to the task.

0. Run the `project-probe` skill: read `.agents/verification.yaml` (create it if absent or stale). All verification in later phases uses the manifest's commands.

1. If the task argument is an issue reference (`#42`, `owner/repo#42`), fetch the issue:
   ```bash
   gh issue view 42
   ```
   Extract: title, description, acceptance criteria, labels, linked PRs.

2. Explore the codebase:
   - Identify the architecture (framework, main directories, entry points)
   - List files likely to be impacted (use `Grep` + `Glob`)
   - Identify existing patterns to follow (conventions, naming, test layout)
   - Identify dependencies (what imports what, what's shared)
   - Identify risks (tightly coupled code, shared state, migration needs)

3. If the task mentions UI/frontend work (keywords: "screen", "page", "component", "UI", "design", "form", "layout") OR files to modify are `.tsx`/`.jsx`/`.vue`/`.css`, detect frontend context:
   - Check if `components/CLAUDE.md` or `components/AGENTS.md` exists → read it for components inventory
   - Check if `components.json` exists (shadcn) → note the convention
   - If a Figma URL is in the issue body → note it, fetch the design context if possible
   - Load `design-audit` and run a quick read-only audit on the target path/Figma/preview when available; P0/P1 findings become planning constraints

4. If the task touches public SEO/GEO surfaces (homepage, landing, blog, `.mdx`, `metadata`, `schema`, `robots.txt`, `sitemap.*`, `llms.txt`, title/meta/H1/canonical/FAQ), load `seo-geo-audit` and run a quick read-only audit when a URL/path is available; P0/P1 findings become planning constraints.

5. Produce an EXPLORE synthesis with these sections:
   - **Requirements** (from issue or description)
   - **Files to modify/create** (absolute paths + purpose)
   - **Patterns to follow** (reference to existing similar code)
   - **Risks** (what could break)
   - **Frontend context** (if applicable)

**STOP CHECKPOINT 1** — Present the synthesis. Wait for user validation before planning.

---

## Phase 2 — PLAN

**Goal**: break the task into atomic, reviewable steps before touching code.

1. Using the EXPLORE context, produce a numbered implementation plan. Each step must specify:
   - **What**: precise description of the change
   - **Where**: absolute file paths to create/modify
   - **How**: pattern to follow, reference to existing code
   - **Constraints**: what NOT to touch
   - **Test strategy**: what should be tested (P0-P3 priority)

2. If the plan has 3+ steps, consider tracking progress with tasks/todos.

3. If frontend work is detected, add to the plan:
   - Which existing components to reuse (reference `components/CLAUDE.md` inventory)
   - Which CSS tokens/variables to use (never hardcoded hex/spacing)
   - If Figma provided: map Figma elements → code components
   - Which `design-audit` P0/P1 findings must be fixed before ship
   - If new components created: note that the design system doc will need updating

4. If SEO/GEO work is detected, add to the plan:
   - Which public pages/meta/schema/content files are impacted
   - Which `seo-geo-audit` P0/P1 findings must be fixed before ship
   - Which facts remain `Non vérifié` without preview URL, GSC or external checks

**STOP CHECKPOINT 2** — Present the plan. Wait for user validation before implementing.

---

## Phase 3 — IMPLEMENT

**Goal**: write the code AND its tests together.

Execute each step of the plan sequentially. For each step:

1. **Code the change**
   - Follow the project conventions (CLAUDE.md / AGENTS.md at repo root)
   - Respect existing file structure
   - No unrequested refactoring
   - No out-of-scope edits

2. **Write the tests**
   - Priority-based (P0 for happy path + critical edge cases, P1-P3 for completeness)
   - Arrange-Act-Assert pattern
   - Naming: `should_[behavior]_when_[condition]`
   - No hard waits, no flaky patterns
   - Deterministic (fixed seeds, frozen time)

3. **Verify after each step** by running the `commands` from `.agents/verification.yaml` (lint, typecheck, test). A command absent from the manifest is reported as absent — never faked green, never guessed.

4. If a step breaks the build, fix before moving to the next step.

**STOP CHECKPOINT 3** — Summary of what was implemented. Tests green. Wait for user validation before review.

---

## Phase 4 — REVIEW (quality-gate loop)

**Goal**: converge on proven quality instead of a one-shot review.

1. Determine the gate level: 2 by default; 3 if frontend or SEO/GEO work was detected in Phase 1 (their audit lenses join the loop).
2. Run the `quality-gate` skill on `git diff main...HEAD` with the validated plan and the manifest. It loops (bounded) through execution evidence → multi-lens reviews → adversarial counter-verification → fixes, and writes `docs/quality/GATE-<date>-<slug>.yaml`.
3. Commit the gate file with the branch.

**STOP CHECKPOINT 4** — Present the gate summary: verdict, rounds, findings (confirmed/refuted/fixed), `decisions_prises_en_ton_nom`, absents. Wait for user validation before ship.

---

## Phase 5 — SHIP

**Goal**: propose next action.

Present the options:
- **[S]** Run `/ship` — automated merge main + tests + final review + CHANGELOG + PR
- **[C]** Commit only — stage + commit, no push/PR
- **[R]** Review again — go back to Phase 4
- **[D]** (if frontend + new components) Update design system docs first, then ship

Wait for the user's choice.

---

## Anti-patterns to avoid

- ❌ Skipping Phase 1 (EXPLORE) because "the task seems simple"
- ❌ Merging Phase 2 (PLAN) and Phase 3 (IMPLEMENT) — always plan first
- ❌ Doing review passes in parallel mentally — they must be distinct contexts
- ❌ Fixing review issues and skipping the re-test
- ❌ Not presenting at each STOP CHECKPOINT — rigor requires validation

---

## Referenced knowledge & skills

When useful, load these for deeper guidance:

- Verification manifest: the `project-probe` skill (`.agents/verification.yaml`)
- Quality loop & gate file: the `quality-gate` skill (`docs/quality/GATE-*.yaml`)
- Testing strategy: `.claude/knowledge/testing/test-levels-framework.md`, `test-priorities-matrix.md`
- Error handling: `.claude/knowledge/testing/error-handling.md`
- Frontend components: `components/CLAUDE.md` or `components/AGENTS.md` if present
- Design system: the `ds-doc` skill for documenting new components
- Design audit gate: the `design-audit` skill for tokens, components, a11y, taste, Figma/code drift, and AI surface evidence
- SEO/GEO audit gate: the `seo-geo-audit` skill for public pages, content, metadata, schema, llms.txt, SERP and AI visibility evidence
