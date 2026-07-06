# D-EPCT+R v6 — Vague 2 : /dev refondu (niveaux, stop unique, lanceurs) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refondre `dev-workflow` en source unique adaptative (niveaux 0-4, stop humain unique au plan, RED conditionnel), absorber `/quick-fix`, réduire les commandes à des lanceurs, et purger le backlog vague 1.

**Architecture:** Le skill `dev-workflow` devient le moteur unique des trois entrées (`/dev` interactif, `/quick-fix` niveau 0 forcé, `/auto-dev` autonome avec gate de mandat). Les commandes Claude et prompts Codex deviennent des lanceurs minces. `quick-fix-workflow` est supprimé. Spec de référence : `docs/planning/specs/2026-07-05-epctr-v6-design.md` (§5, §9 vague 2 + errata §12).

**Tech Stack:** Markdown skills (Claude Code + Codex CLI), bash pour vérifications structurelles.

## Global Constraints

- Skills canoniques **en anglais** ; commandes/prompts lanceurs **en français** (commandes Claude) ou anglais (prompts Codex, convention existante) (spec §2).
- **Vague 2 change le modèle d'interaction** : mode interactif = UN SEUL stop humain (le plan, Phase 2). Les anciens checkpoints 1/3/4 disparaissent (spec §5).
- Grille des niveaux verbatim (spec §5) : 0 = typo/constante ≤3 fichiers ≤50 lignes, circuit court sans plan ni RED ni gate file ; 1 = petit bug, mini-plan ⛔ + gate 1 tour ; 2 = feature standard, flow complet ; 3 = multi-composants/surface publique, + lentilles design/SEO/a11y + filet humain ; 4 = epic/migration/auth/schéma DB, refus sans spec approuvée (`docs/planning/specs/`, frontmatter `status: approved`, `approved_by` ≠ ralph).
- **Escalade automatique** : le workflow monte de niveau en réutilisant l'acquis et le signale — jamais de « recommence avec /dev » (spec §5).
- **RED conditionnel** : seulement si niveau ≥ 2 ET `testability.harness ≠ none` dans le manifeste ; sinon vérification runtime + note `absents` dans le gate (spec §5, correction Rodin 3).
- **Filet humain niveaux 3-4** : lecture de `decisions_prises_en_ton_nom` exigée avant de proposer /ship (spec §5, correction Rodin 4).
- Mode autonome : verdict gate PASS requis, jamais CONCERNS auto-accepté ; CONCERNS structurel (aucune preuve exécutable possible) → STOP immédiat avec explication, pas d'itérations brûlées (backlog vague 1).
- Lanceurs : `dev.md` et `quick-fix.md` ≤ 15 lignes ; `auto-dev.md` ≤ 30 lignes (conserve la config de session RALPH ; le pre-flight gate de mandat migre DANS le skill, section mode autonome).
- Chemins réels : `skills/` et `commands/` sont des symlinks — éditer/stager `.claude/skills/...` et `.claude/commands/...`. Prompts Codex : `.codex/prompts/...` (tracked).
- Ne PAS toucher : `AGENTS.md` (autre chantier + vague 3), `README.md`, `GEMINI.md`, `install.sh`, `ship-workflow`, `discovery-workflow` (vague 3).
- Commits : `type(scope): description` + `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. Branche : `feature/epctr-v6-wave2`.

---

### Task 1: Purger le backlog vague 1 sur project-probe + quality-gate

**Files:**
- Modify: `.claude/skills/project-probe/SKILL.md`
- Modify: `.claude/skills/quality-gate/SKILL.md`

- [ ] **Step 1: project-probe — fingerprint portable (zsh + sha256sum)**

Remplacer le bloc bash du fingerprint :

```bash
cat package.json pnpm-lock.yaml yarn.lock Makefile justfile pyproject.toml setup.cfg \
    Cargo.toml go.mod Gemfile composer.json .github/workflows/*.yml 2>/dev/null | shasum -a 256 | cut -d' ' -f1
```

par :

```bash
ci_files=$(find .github/workflows -name '*.yml' -o -name '*.yaml' 2>/dev/null | sort)
cat package.json pnpm-lock.yaml yarn.lock Makefile justfile pyproject.toml setup.cfg \
    Cargo.toml go.mod Gemfile composer.json $ci_files 2>/dev/null \
  | (shasum -a 256 2>/dev/null || sha256sum) | cut -d' ' -f1
```

(`find` évite l'échec de glob zsh quand `.github/workflows/` est vide ; `sha256sum` couvre les conteneurs Linux minimaux sans `shasum`.)

- [ ] **Step 2: project-probe — section Runtime capabilities**

Insérer immédiatement avant la section `## Anti-patterns` :

```markdown
## Runtime capabilities

The probe procedure is identical on every runtime. Runtimes with parallel subagents may sanity-check command candidates concurrently; sequential runtimes check them one at a time. No step of this skill requires any runtime-specific tool.
```

- [ ] **Step 3: quality-gate — clarifier restart vs exception niveau 1**

Remplacer :

`A restart consumes a round from the cap; if execution evidence cannot be made green within the cap, the verdict is \`FAIL\`.`

par :

`A restart consumes a round from the cap; if execution evidence cannot be made green within the cap, the verdict is \`FAIL\`. (At level 1 the single-round exception below still applies: fixing and re-running green within that round is allowed and does not consume a second round.)`

- [ ] **Step 4: quality-gate — exception sécurité dans la contre-vérification**

Remplacer :

`Uncertain → refuted (bias against false positives).`

par :

`Uncertain → refuted (bias against false positives) — EXCEPT security findings (injection, auth bypass, secret exposure, trust-boundary violations): an uncertain security finding stays confirmed until positively disproven.`

- [ ] **Step 5: Vérifier + commit**

```bash
grep -q "sha256sum" .claude/skills/project-probe/SKILL.md && \
grep -q "Runtime capabilities" .claude/skills/project-probe/SKILL.md && \
grep -q "single-round exception below still applies" .claude/skills/quality-gate/SKILL.md && \
grep -q "EXCEPT security findings" .claude/skills/quality-gate/SKILL.md && echo OK
git add .claude/skills/project-probe/SKILL.md .claude/skills/quality-gate/SKILL.md
git commit -m "fix(skills): wave-1 backlog — portable fingerprint, runtime caps, level-1 clarifier, security tiebreak

Refs: docs/planning/plans/2026-07-06-epctr-v6-wave2-plan.md

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Réécrire `dev-workflow/SKILL.md` (moteur unique, niveaux 0-4)

**Files:**
- Rewrite (full replacement): `.claude/skills/dev-workflow/SKILL.md`

**Interfaces:**
- Consumes: `project-probe` (manifeste `.agents/verification.yaml` : `commands`, `testability.{harness,e2e,runtime_verify}`, `absents`) ; `quality-gate` (boucle, gate file `docs/quality/GATE-<date>-<slug>.yaml`, verdicts PASS/CONCERNS/FAIL/WAIVED, `decisions_prises_en_ton_nom`).
- Produces: le contrat des trois modes (`interactive` | `quick-fix` | `autonomous`) que les lanceurs de Task 3 et les prompts Codex de Task 4 référencent par nom.

- [ ] **Step 1: Remplacer intégralement le fichier par ce contenu**

````markdown
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
````

- [ ] **Step 2: Vérifier la structure**

```bash
grep -qx "name: dev-workflow" .claude/skills/dev-workflow/SKILL.md && \
grep -c "STOP" .claude/skills/dev-workflow/SKILL.md >/dev/null && \
grep -q "THE STOP" .claude/skills/dev-workflow/SKILL.md && \
grep -q "Escalation rule" .claude/skills/dev-workflow/SKILL.md && \
grep -q "Mandate gate" .claude/skills/dev-workflow/SKILL.md && \
grep -q "testability.harness" .claude/skills/dev-workflow/SKILL.md && \
grep -q "decisions_prises_en_ton_nom" .claude/skills/dev-workflow/SKILL.md && \
grep -q "Runtime capabilities" .claude/skills/dev-workflow/SKILL.md && \
! grep -q "STOP CHECKPOINT [134]" .claude/skills/dev-workflow/SKILL.md && echo OK
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/dev-workflow/SKILL.md
git commit -m "feat(dev-workflow): v6 engine — levels 0-4, single plan stop, conditional RED, three modes

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §5

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Réduire les 3 commandes Claude à des lanceurs

**Files:**
- Rewrite: `.claude/commands/dev.md`
- Rewrite: `.claude/commands/quick-fix.md`
- Rewrite: `.claude/commands/auto-dev.md`

- [ ] **Step 1: `.claude/commands/dev.md` — contenu intégral**

```markdown
---
description: Développe une feature avec le workflow adaptatif D-EPCT+R v6 (niveaux 0-4, stop unique au plan, boucle quality-gate). Usage: /dev [issue] ou /dev "description"
---

# Dev — $ARGUMENTS

Charge le skill `dev-workflow` et exécute-le en mode **interactive**.

- Tâche : **$ARGUMENTS** (issue `#NUM` → `gh issue view` en Phase 1)
- Un seul stop humain : le plan (Phase 2). Niveaux 3-4 : lecture des « décisions prises en ton nom » avant ship.
- Toute la logique (niveaux, escalade, RED, gate) vit dans le skill — ne pas improviser en dehors.

Je commence par Phase 0 (probe) puis Phase 1 (explore).
```

- [ ] **Step 2: `.claude/commands/quick-fix.md` — contenu intégral**

```markdown
---
description: Fix rapide via le circuit court du workflow v6 (niveau 0 forcé, escalade automatique si ça grossit). Usage: /quick-fix "description du problème"
---

# Quick Fix — $ARGUMENTS

Charge le skill `dev-workflow` et exécute-le en mode **quick-fix** (niveau 0 forcé).

- Problème : **$ARGUMENTS**
- Circuit court : localiser → fixer → vérifs du manifeste → présenter. Pas de plan formel, pas de gate file.
- Si le fix dépasse le niveau 0 (4ᵉ fichier, >50 lignes, dépendance), le workflow **escalade tout seul** au niveau supérieur en gardant l'acquis — ne pas demander de relancer /dev.
- Ne pas auto-commit : présenter le fix et le commit suggéré.
```

- [ ] **Step 3: `.claude/commands/auto-dev.md` — contenu intégral**

```markdown
---
description: Développe une feature en mode RALPH autonome via le workflow v6 (mandat requis, zéro stop, gate PASS obligatoire). Usage: /auto-dev #123
---

# Auto-Dev (RALPH) — $ARGUMENTS

**Session :** ${CLAUDE_SESSION_ID}

Charge le skill `dev-workflow` et exécute-le en mode **autonomous**.

- Mandat : **$ARGUMENTS** — le gate de mandat du skill s'applique (issue GitHub valide OU spec approuvée dans `docs/planning/specs/` ; sinon refus avec options). `--allow-no-spec` = prototypage uniquement, loggé comme tel.
- Zéro stop humain. Verdict gate **PASS obligatoire** (CONCERNS jamais auto-accepté ; CONCERNS structurel → STOP immédiat).
- Config RALPH : max **50** itérations (`--max N`), timeout **2h** (`--timeout Xh`), promise **"DEV COMPLETE"**, logs `docs/ralph-logs/${CLAUDE_SESSION_ID}.md`.
- Arrêt manuel : `/cancel-ralph`. Reprise : `/resume-ralph ${CLAUDE_SESSION_ID}`.

Je vérifie le mandat puis j'enchaîne Phase 0 → Phase 6 sans validation intermédiaire.
```

- [ ] **Step 4: Vérifier + commit**

```bash
for f in dev quick-fix auto-dev; do wc -l .claude/commands/$f.md; done
grep -q "mode \*\*interactive\*\*" .claude/commands/dev.md && \
grep -q "mode \*\*quick-fix\*\*" .claude/commands/quick-fix.md && \
grep -q "mode \*\*autonomous\*\*" .claude/commands/auto-dev.md && \
! grep -q "SendMessage" .claude/commands/dev.md && echo OK
git add .claude/commands/dev.md .claude/commands/quick-fix.md .claude/commands/auto-dev.md
git commit -m "refactor(commands): dev, quick-fix and auto-dev become thin launchers

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §2

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(`dev.md` et `quick-fix.md` ≤ 15 lignes ; `auto-dev.md` ≤ 30 lignes.)

---

### Task 4: Supprimer quick-fix-workflow + rafraîchir les prompts Codex

**Files:**
- Delete: `.claude/skills/quick-fix-workflow/` (entire directory)
- Rewrite: `.codex/prompts/dev.md`
- Rewrite: `.codex/prompts/quick-fix.md`

- [ ] **Step 1: Supprimer le skill absorbé**

```bash
git rm -r .claude/skills/quick-fix-workflow
```

Puis vérifier qu'aucun fichier tracké ne référence encore le skill supprimé (hors docs/planning et CHANGELOG qui sont historiques) :

```bash
grep -rn "quick-fix-workflow" --include="*.md" .claude/ .codex/ | grep -v "quick-fix-workflow/" || echo CLEAN
```

Si des références vivantes apparaissent (ex. `GEMINI.md`, `AGENTS.md` — interdits de modification en vague 2), les LISTER dans le rapport sans les modifier.

- [ ] **Step 2: `.codex/prompts/dev.md` — contenu intégral**

```markdown
---
description: 'D-EPCT+R v6 adaptive feature development: levels 0-4, single plan checkpoint, quality-gate loop'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/dev-workflow/SKILL.md`, READ its entire contents, and execute the workflow in **interactive** mode, sequentially phase-by-phase.

The user's task description follows this line. If it looks like an issue reference (`#42`, `owner/repo#42`), fetch it with `gh issue view` as your first step of Phase 1.

There is exactly ONE human checkpoint: the plan (Phase 2). Present the full single-screen plan and wait. Levels 3-4 additionally require showing `decisions_prises_en_ton_nom` before proposing ship. Never skip Phase 0 (probe) or Phase 1 (explore); follow the level circuits and the escalation rule exactly as written in the skill.
```

- [ ] **Step 3: `.codex/prompts/quick-fix.md` — contenu intégral**

```markdown
---
description: 'Quick fix via the v6 workflow short circuit (level 0 forced, automatic escalation)'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/dev-workflow/SKILL.md`, READ its entire contents, and execute the workflow in **quick-fix** mode (level 0 forced).

The user's problem description follows this line.

Short circuit: locate → fix → run the manifest's verification commands → present the fix and a suggested commit. No formal plan, no gate file. If the fix grows beyond level 0 (4th file, >50 lines, new dependency), the workflow escalates one level automatically, keeping all work — do not tell the user to restart with `/dev`. Never auto-commit.
```

- [ ] **Step 4: Vérifier + commit**

```bash
test ! -d .claude/skills/quick-fix-workflow && \
grep -q "v6 adaptive" .codex/prompts/dev.md && \
! grep -q "Review ×3" .codex/prompts/dev.md && \
grep -q "quick-fix\*\* mode\|quick-fix** mode" .codex/prompts/quick-fix.md && \
! grep -q "quick-fix-workflow" .codex/prompts/quick-fix.md && echo OK
git add -A .claude/skills/quick-fix-workflow .codex/prompts/dev.md .codex/prompts/quick-fix.md
git commit -m "refactor(codex): absorb quick-fix-workflow into dev-workflow, refresh prompts

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §2

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

Note pour le rapport : vérifier dans `install.sh` (lecture seule) que la purge par manifest supprimera `quick-fix-workflow` de `~/.claude/skills/` au prochain `update` ; sinon le signaler à l'utilisateur (suppression manuelle).

---

### Task 5: Smoke test de sortie de vague (spec §9 vague 2)

**Files:** aucun fichier du repo — scratch project jetable dans le scratchpad de session.

Test de sortie : « `/quick-fix` et `/dev` niveaux 0-3 validés en usage réel ; escalade 0→2 observée ». Exécuter `dev-workflow/SKILL.md` (version de l'arbre) à la lettre, comme un runtime naïf, sur un scratch projet Node avec harness (node:test) :

- [ ] **Step 1: Scénario A — quick-fix niveau 0.** Seeder un typo dans une string. Exécuter le mode quick-fix. Attendu : pas de plan, pas de stop, pas de gate file ; vérifs du manifeste lancées ; fix présenté avec commit suggéré, non auto-committé.
- [ ] **Step 2: Scénario B — /dev interactif niveau 2.** Demander une petite feature (ex. fonction `slugify` + intégration). Attendu : Phase 2 = UN SEUL stop (simuler la validation) ; Phase 3 RED exécutée (harness présent) avec tests qui échouent d'abord ; Phase 4 séquentielle ; Phase 5 gate file écrit avec verdict cohérent et `diff_hash` ; Phase 6 rapport avec `decisions_prises_en_ton_nom` (même vide).
- [ ] **Step 3: Scénario C — escalade 0→2 observée.** Lancer en mode quick-fix un « petit fix » qui nécessite en réalité de toucher 4 fichiers. Attendu : le workflow annonce l'escalade, monte au niveau supérieur, garde l'acquis, produit un mini-plan/plan, et NE dit JAMAIS « relance /dev ».
- [ ] **Step 4: Rapport.** Pour chaque scénario : attendu vs observé, divergences avec citation de la section du skill. Ne jamais modifier les fichiers du repo ; les faiblesses de formulation sont des findings. Nettoyer les scratch dirs.

---

## Self-Review (faite à la rédaction)

1. **Spec coverage vague 2** : §5 phases/niveaux/modes/escalade/RED conditionnel/filet 3-4 → Task 2 ; §2 lanceurs → Tasks 3-4 ; absorption quick-fix → Tasks 2-4 ; backlog vague 1 (fingerprint zsh/sha256sum, Runtime capabilities probe, clarifier niveau 1, tiebreak sécurité, CONCERNS structurel, description prompt Codex, diagrammes ASCII supprimés via réécriture des commandes) → Tasks 1-4 ; test de sortie §9 → Task 5. Hors scope respecté : ship/discovery/README/AGENTS.md/install.sh (vague 3).
2. **Placeholders** : contenu intégral fourni pour les 6 fichiers réécrits. Aucun TBD.
3. **Cohérence des contrats** : les noms de modes (`interactive`/`quick-fix`/`autonomous`) sont identiques entre Task 2 (producteur) et Tasks 3-4 (consommateurs) ; chemins manifeste/gate file identiques à la vague 1 ; grille des niveaux identique spec §5 ; bornes de gate identiques quality-gate (1→1, 2→3, 3-4→4).
