---
name: dev-workflow
description: Adaptive single-source feature development workflow (D-EPCT+R v6). Loaded by /dev, /quick-fix and /auto-dev in both Claude Code and Codex CLI. Scales rigor to task levels 0-4 (typo fix → epic) with automatic escalation, a single human checkpoint at the plan, conditional acceptance-test-first (RED), and a bounded quality-gate loop replacing human code re-reading. Use for any implementation task: bug fix, feature, GitHub issue.
---

# Dev Workflow — Adaptive Feature Implementation

One engine, three entry modes. The caller (slash command / prompt) sets the mode; everything else lives here.

| Mode | Entry | Human checkpoints |
|---|---|---|
| `interactive` | `/dev` | ONE: the plan (Phase 2). Levels 3-4 add the handoff read (Phase 6). |
| `quick-fix` | `/quick-fix` | None below level 1; starts at level 0 and may escalate. |
| `autonomous` | `/auto-dev` (RALPH) | None; the mandate gate (below) replaces the plan stop. |

**Inputs**: task description or issue reference, plus the mode.
**Output**: implemented + tested + gated code, ready to `/ship`, with a gate file as proof.

## Core principles

1. **The orchestrator keeps all context** — planning is never delegated.
2. **One human stop** (interactive mode): everything the user must judge is on one screen at Phase 2.
3. **Rigor scales with the level** — never run level-2 ceremony on a typo, never run a typo circuit on a migration.
4. **Escalate, never restart** — if scope grows, move up a level reusing all acquired work, and say so.
5. **Verification comes from the manifest** (`.agents/verification.yaml`) — never guess commands.
6. **Quality is proven by the gate file, not by the user re-reading the diff.**

## Phase 0 — PROBE (silent)

Run the `project-probe` skill: read `.agents/verification.yaml`, create or refresh it if absent/stale. Read repo conventions (CLAUDE.md / AGENTS.md, local project memory pointer if present).

## Phase 1 — EXPLORE

1. If the task is an issue reference (`#42`, `owner/repo#42`): `gh issue view 42` — extract title, description, acceptance criteria, labels, Figma URLs.
2. Explore the codebase: architecture, impacted files, patterns to follow, dependencies, risks.
3. **Surface detection** (feeds gate lenses and level scoring):
   - *Frontend*: impacted files `.tsx/.jsx/.vue/.svelte/.css`, `components/CLAUDE.md` or `components.json` present, Figma URL in issue, UI keywords. If detected: read the components inventory; fetch Figma design context when available.
   - *SEO/GEO*: public indexable surfaces — homepage/landing/blog, `.mdx`, `metadata`, schema/JSON-LD, `robots.txt`, `sitemap.*`, `llms.txt`, title/meta/H1/canonical/FAQ, SEO keywords in issue.
4. **Assess the level**:

| Level | Signals | Circuit |
|---|---|---|
| **0** | typo, constant, style; ≤3 files, ≤50 lines, zero risk | Fix → manifest verify → present. No plan, no RED, no gate file. |
| **1** | small localized bug or adjustment, 1 file cluster | Light explore → mini-plan ⛔ (interactive) → fix → gate, 1 round, 1 reviewer. |
| **2** | standard feature, one component | Full flow below. |
| **3** | multi-component, public surface, rich UI | Full flow + design/SEO/a11y lenses in the gate + human handoff read. |
| **4** | epic, migration, auth, DB schema, data handling | REFUSE to start without an approved spec (`docs/planning/specs/*-design.md`, frontmatter `status: approved`, `approved_by` set and ≠ `ralph`, `approved_at` non-empty). Route the user to `/discovery`. Then execute per story at level 2-3 with the human handoff read. |

State the detected level and why. In interactive mode the user can override it at the Phase 2 stop.

**Escalation rule (applies in every phase):** the moment reality exceeds the level (4th file touched at level 0, schema change discovered at level 2, 10+ plan steps...) — announce it, move up one level, keep everything already produced (explore synthesis, partial plan, code). A quick-fix that grows becomes a level-1/2 run mid-flight; it never aborts.

## Phase 2 — PLAN

Skip at level 0 (go straight to Phase 4 with a one-line intent statement).

Build the plan: numbered atomic steps — each with what / where (absolute paths) / how (pattern to follow) / constraints (what NOT to touch) / **acceptance criteria** (testable) / test strategy (P0-P3). If frontend: components to reuse, tokens (never hardcoded values), Figma mapping. If SEO/GEO: impacted public files, facts that stay `Non vérifié` without preview/GSC.

- **interactive** → ⛔ **THE STOP**: present ONE screen = explore synthesis + detected level + full plan + acceptance criteria + test strategy. The user validates, adjusts, or changes the level. This is the only stop before Phase 6.
- **quick-fix (level 1 after escalation)** → present the mini-plan as the stop.
- **autonomous** → no stop. **Mandate gate instead** (checked before Phase 1): a valid GitHub issue OR an approved spec (criteria above). No mandate → refuse with the exact remediation options (`/discovery`, `gh issue create`, or `--allow-no-spec` for prototyping only, logged as such). Track iterations in `docs/ralph-logs/<session>.md` per RALPH conventions; `/cancel-ralph` stops the loop.

## Phase 3 — RED (conditional)

Run only if **level ≥ 2 AND `testability.harness ≠ none`** in the manifest.

Write the acceptance tests derived from the plan's acceptance criteria — and run them to prove they FAIL for the right reason before any implementation. These tests encode what the user validated; the gate will prove they turned green.

If skipped (no harness): acceptance criteria will be verified at runtime in the gate (manifest `testability.runtime_verify`, or the `verify` skill when the runtime offers it) and the gate file records `absents: ["no test harness — acceptance verified at runtime"]`.

## Phase 4 — IMPLEMENT

Execute plan steps **sequentially**. For each step: code + its unit tests together → run the manifest's `commands` (lint, typecheck, test) → green before the next step. Follow repo conventions; no unrequested refactoring; no out-of-scope edits.

Parallelizing two steps is allowed ONLY if their file sets are disjoint — and with worktree isolation when the runtime provides it. Sequential is the default, not the fallback.

## Phase 5 — GATE

Level 0: run the manifest commands, present the fix (no gate file). Done — Phase 6.

Levels 1-4: run the `quality-gate` skill on the default-branch diff with the validated plan and the manifest. Gate level = task level (1 → 1 round; 2 → ≤3; 3-4 → ≤4 + design-audit / seo-geo-audit / a11y-enforcer lenses for the surfaces detected in Phase 1). Commit the gate file with the branch.

**Autonomous mode**: verdict PASS required — CONCERNS is never auto-accepted. If the CONCERNS is *structural* (the project offers no executable evidence at all), STOP immediately with the explanation — iterating cannot change it. FAIL → one more iteration to fix; >3 attempts → STOP with a clear report.

## Phase 6 — HANDOFF

Present the final report: verdict + rounds + findings summary, **`decisions_prises_en_ton_nom`** (every deviation from the validated plan), `absents`, diff stats, and the RED→GREEN evidence when Phase 3 ran.

- Levels 0-2 (interactive): propose **[S] `/ship`** | **[C] commit only** | **[R] re-run the gate**.
- Levels 3-4 (interactive): require the user to read `decisions_prises_en_ton_nom` (quote it in full) before proposing the same options. This is the only careful read left to the human.
- Frontend + new components: propose `/ds-doc --update` before ship.
- Autonomous: chain `/ship` directly when the gate is PASS; the PR body carries the gate file.

## Runtime capabilities

- **Claude Code**: dispatch Phase 1 exploration to an Explore subagent; use TaskCreate for 2+ plan steps; quality-gate uses native `/code-review` as primary lens with parallel lens subagents; parallel implementation only for disjoint-file steps, preferably in worktrees.
- **Sequential runtimes (Codex CLI, OpenCode)**: run every phase inline in order; quality-gate lenses run one at a time with an explicit reset between lenses. Same phases, same rules, same gate file.

## Anti-patterns

- ❌ Running the full ceremony on a level-0 task, or a level-0 circuit on risky scope
- ❌ Restarting from scratch when scope grows — escalate and reuse
- ❌ More than one human stop in interactive mode (the plan is THE stop; Phase 6 levels 3-4 is a read, not a re-plan)
- ❌ Hardcoding verification commands instead of reading the manifest
- ❌ Writing RED tests that can't fail, or skipping the failing run
- ❌ Accepting CONCERNS in autonomous mode, or iterating on a structural CONCERNS
- ❌ Shipping levels 3-4 without surfacing `decisions_prises_en_ton_nom`

## Referenced knowledge & skills

- Verification manifest: `project-probe` skill (`.agents/verification.yaml`)
- Quality loop & gate file: `quality-gate` skill (`docs/quality/GATE-*.yaml`)
- Testing strategy: `.claude/knowledge/testing/test-levels-framework.md`, `test-priorities-matrix.md`
- Design/SEO gates: `design-audit`, `seo-geo-audit`, `a11y-enforcer` skills
- Design system docs: `ds-doc` skill
