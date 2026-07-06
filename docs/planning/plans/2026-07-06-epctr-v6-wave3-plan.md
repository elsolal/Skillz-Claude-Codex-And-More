# D-EPCT+R v6 — Vague 3 : /ship consomme le gate, /discovery en niveaux, docs & installeur — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fermer la chaîne v6 : `/ship` lit le gate file au lieu de re-reviewer, `/discovery` passe aux niveaux avec sortie spec systématique, lanceurs partout, docs racine et CLAUDE.md template à jour, installeur corrigé.

**Architecture:** Édits ciblés sur `ship-workflow` (Step 3-4) et `discovery-workflow` (Phase 1 + sortie spec), lanceurs minces pour les 3 commandes restantes + prompts Codex/Gemini/OpenCode, fix du prompt-copy d'install.sh (signature Skillz), mise à jour des 4 docs (README, AGENTS.md, GEMINI.md, `.claude/CLAUDE.md` section D-EPCT). Spec : `docs/planning/specs/2026-07-05-epctr-v6-design.md` §6, §7, §9 vague 3 + errata §12.

**Tech Stack:** Markdown skills, bash (install.sh), TOML/YAML lanceurs.

## Global Constraints

- Skills **en anglais**, commandes Claude **en français**, prompts Codex/Gemini/OpenCode en anglais (conventions en place).
- **Gate frais** = `diff_hash` du gate == hash recalculé avec la même règle d'exclusion : `git diff <base>...HEAD -- ':(exclude)docs/quality' | (shasum -a 256 2>/dev/null || sha256sum) | cut -d' ' -f1` (errata spec §12 — jamais `git diff main...HEAD` en dur).
- `/ship` reste **non-interactif** ; il ne s'arrête que pour : main branch, conflits, preuve exécutable rouge, gate FAIL, CONCERNS non explicitement accepté par l'utilisateur.
- Niveaux discovery (spec §7) : **0-1** → tech-spec courte directe (pas de PRD, 1-2 stories max) ; **2-3** → chaîne actuelle Brainstorm → (UX) → PRD → (UI) → Architecture → Stories ; **4** → chaîne complète + section NFR/sécurité formalisée. **Escalade** : la tech-spec devient l'entrée du PRD, jamais de redémarrage.
- Toute discovery (interactive comme autonome) produit la **spec consolidée** `docs/planning/specs/YYYY-MM-DD-<slug>-design.md` avec frontmatter (`status`, `approved_by`, `approved_at`) — interactive : l'humain approuve au dernier checkpoint (`status: approved`) ; autonome : toujours `status: draft`, `approved_by: ralph`.
- Les checkpoints par phase de discovery sont **conservés** en mode interactif (le planning garde l'humain dans la boucle) ; le mode autonome ne s'arrête pas.
- **Sweep de références repo-wide** comme test de sortie : `git grep` SANS scoping de dossier (leçon vague 2).
- Chemins réels : `.claude/skills/...`, `.claude/commands/...` (symlinks) ; `.codex/`, `.gemini/`, `.opencode/`, `.agents/` normaux.
- Ne PAS toucher : mécanique RALPH générique (`auto-loop`, `cancel-ralph`, `resume-ralph`), squads design/SEO, `/pr-review` (second temps), `/refactor`.
- Commits : `type(scope): description` + `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. Branche : `feature/epctr-v6-wave3`.

---

### Task 1: `ship-workflow/SKILL.md` consomme le gate file

**Files:**
- Modify: `.claude/skills/ship-workflow/SKILL.md`

**Interfaces:**
- Consumes: gate file `docs/quality/GATE-<date>-<slug>.yaml` (clés `verdict`, `diff_hash`, `preuve`, `decisions_prises_en_ton_nom`, `absents`) ; manifeste `.agents/verification.yaml` ; skills `quality-gate` et `project-probe`.

- [ ] **Step 1: Step 3 (tests) passe au manifeste**

Remplacer tout le bloc `## Step 3 — Run tests` (du titre jusqu'à la ligne `- **If all pass**: note the counts briefly and continue.` incluse) par :

```markdown
## Step 3 — Execution evidence (manifest)

Run the `project-probe` skill (read `.agents/verification.yaml`, create if absent), then run every command in the manifest's `commands` (lint, typecheck, test, build), capturing output for possible debugging.

- **If anything is red**: display the failures and **STOP**.
- **If green**: note the counts briefly and continue. Entries absent from the manifest are reported as absent — never guessed, never faked.
```

- [ ] **Step 2: Step 4 (Pre-Landing Review) devient la consommation du gate**

Remplacer tout le bloc `## Step 4 — Pre-Landing Review` (du titre jusqu'à la dernière ligne de sa section, `- **If no issues**: output "Pre-Landing Review: No issues found." and continue.` incluse) par :

```markdown
## Step 4 — Quality gate consumption

Quality is proven by the gate file, not by a fresh review. One definition of quality in the whole system: the `quality-gate` skill.

1. Find the most recent `docs/quality/GATE-*.yaml` committed on this branch.
2. Check **freshness**: recompute the diff hash with the gate's exclusion rule —
   `git diff <base>...HEAD -- ':(exclude)docs/quality' | (shasum -a 256 2>/dev/null || sha256sum) | cut -d' ' -f1`
   (`<base>` = `main`, or `master` if `main` does not exist) and compare with the gate's `diff_hash`.
3. Decide:
   - **Gate PASS and fresh** → proceed. The gate file content goes into the PR body verbatim.
   - **Gate absent, stale, FAIL, or CONCERNS** → run the `quality-gate` skill now (level from the gate file if present, else 2; the run includes design/SEO/a11y lenses when the diff touches those surfaces — they live inside the gate, not as separate ship passes). Then:
     - New verdict **PASS** → commit the new gate file and proceed.
     - **CONCERNS** → non-interactive rule exception: present the gate summary and ask the user once — accept explicitly (verdict becomes `WAIVED` with the reason recorded in the gate file) or abort. Never auto-accept.
     - **FAIL** → **STOP** and show the confirmed findings.
4. If the gate's `decisions_prises_en_ton_nom` is non-empty and the gate level is 3-4, quote it in the PR body under its own heading — it is the reviewer-facing record of autonomous decisions.
```

- [ ] **Step 3: Step 8 (PR) embarque le gate**

Dans le heredoc du `gh pr create`, remplacer :

```markdown
## Pre-Landing Review
<findings from Step 4, or "No issues found.">
```

par :

```markdown
## Quality Gate
<the gate file content (yaml), verbatim>
<if levels 3-4: the decisions_prises_en_ton_nom section quoted>
```

- [ ] **Step 4: Frontmatter + règles**

Dans le frontmatter `description:`, remplacer `merge main, run tests, design/SEO ship-gates when relevant, pre-landing review, CHANGELOG, commit, push, and create a PR in one go` par `merge main, manifest verification, quality-gate consumption (PASS required or explicit waiver), CHANGELOG, commit, push, and create a PR in one go`.
Dans `## Important rules`, remplacer la ligne `- **Never ask for confirmation** except for CRITICAL review findings, merge conflicts, frontend design-audit P1 risk acknowledgement, or seo-geo-audit P1 risk acknowledgement.` par `- **Never ask for confirmation** except for merge conflicts and an explicit CONCERNS waiver decision.`

- [ ] **Step 5: Vérifier + commit**

```bash
grep -q "Quality gate consumption" .claude/skills/ship-workflow/SKILL.md && \
grep -q ":(exclude)docs/quality" .claude/skills/ship-workflow/SKILL.md && \
! grep -q "Pre-Landing Review" .claude/skills/ship-workflow/SKILL.md && \
grep -q "verification.yaml" .claude/skills/ship-workflow/SKILL.md && \
! grep -qE "^npm test|^pytest" .claude/skills/ship-workflow/SKILL.md && echo OK
git add .claude/skills/ship-workflow/SKILL.md
git commit -m "feat(ship-workflow): consume the quality gate file instead of re-reviewing

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §6

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: `discovery-workflow/SKILL.md` passe aux niveaux + sortie spec

**Files:**
- Modify: `.claude/skills/discovery-workflow/SKILL.md`

- [ ] **Step 1: Phase 1 — la grille FULL/LIGHT devient la grille de niveaux**

Remplacer tout le bloc `## Phase 1 — LISTEN & DETECT MODE` (du titre jusqu'à `**STOP CHECKPOINT 1** — Mode validated.` inclus) par :

```markdown
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
```

- [ ] **Step 2: Remplacer les références de mode restantes**

Dans le reste du fichier, remplacer les conditions de phase :
- `## Phase 2 — BRAINSTORM (FULL mode only)` → `## Phase 2 — BRAINSTORM (levels 2-4)`
- `## Phase 6 — ARCHITECTURE (FULL mode only)` → `## Phase 6 — ARCHITECTURE (levels 2-4)`
- Dans Phase 4 (PRD), remplacer `2. Write the PRD. Size depends on mode:` / `- **FULL**: Overview, Users, Features, Requirements, Constraints, Metrics` / `- **LIGHT**: Problem, Solution, Features, Success Criteria, Out of Scope` par `2. Write the PRD: Overview, Users, Features, Requirements, Constraints, Metrics. Level 4 adds the NFR & security requirements section (performance, reliability, security, compliance — each testable).`
- Dans le principe 3 des Core Principles, remplacer `**Mode auto-detection** — small scope → LIGHT mode, large scope → FULL mode. The user can override.` par `**Level auto-detection** — the 0-4 grid decides the track (tech-spec direct vs full chain), with automatic escalation reusing acquired work. The user can override.`

- [ ] **Step 3: Nouvelle phase 7-bis — sortie spec consolidée (obligatoire, tous niveaux)**

Insérer immédiatement avant `## Phase 8 — PUBLISH TO GITHUB` :

```markdown
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
```

- [ ] **Step 4: Frontmatter du skill**

Remplacer dans la `description:` du frontmatter `Enforces Brainstorm → (UX) → PRD → (UI) → Architecture → Stories → GitHub, with automatic FULL vs LIGHT mode detection and validation checkpoints between phases.` par `Scales with levels 0-4 (tech-spec direct for small scopes, full Brainstorm → PRD → Architecture → Stories chain above), always ends with a consolidated approved-spec output, with validation checkpoints between phases.`

- [ ] **Step 5: Vérifier + commit**

```bash
grep -q "ASSESS LEVEL" .claude/skills/discovery-workflow/SKILL.md && \
grep -q "Phase 7-bis" .claude/skills/discovery-workflow/SKILL.md && \
grep -q "levels 2-4" .claude/skills/discovery-workflow/SKILL.md && \
! grep -q "FULL mode only" .claude/skills/discovery-workflow/SKILL.md && \
! grep -qE "LIGHT mode|FULL vs LIGHT" .claude/skills/discovery-workflow/SKILL.md && echo OK
git add .claude/skills/discovery-workflow/SKILL.md
git commit -m "feat(discovery-workflow): levels 0-4, tech-spec direct track, mandatory spec output

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §7

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Lanceurs ship/discovery/auto-discovery + prompts Codex

**Files:**
- Rewrite: `.claude/commands/ship.md`, `.claude/commands/discovery.md`, `.claude/commands/auto-discovery.md`
- Rewrite: `.codex/prompts/ship.md`, `.codex/prompts/discovery.md`
- Modify (mirror): `.gemini/commands/ship.toml`, `.gemini/commands/discovery.toml`, `.opencode/commands/ship.md`, `.opencode/commands/discovery.md` (lire chaque fichier, adapter au format, même contenu d'instruction)

- [ ] **Step 1: `.claude/commands/ship.md` — contenu intégral**

```markdown
---
description: Ship automatisé v6 — merge main, preuves du manifeste, consommation du gate file (PASS requis ou waiver explicite), CHANGELOG, commits bisectables, push, PR. Usage: /ship
---

# Ship — Release Engineer

Charge le skill `ship-workflow` et exécute-le intégralement, sans confirmation.

- Non-interactif : la prochaine chose que l'utilisateur voit est l'URL de la PR.
- La qualité vient du **gate file** (`docs/quality/GATE-*.yaml`) : PASS frais → PR directe ; absent/périmé/CONCERNS/FAIL → le skill relance quality-gate lui-même.
- Seuls arrêts : branche main, conflits non résolubles, preuve rouge, gate FAIL, décision de waiver CONCERNS.
```

- [ ] **Step 2: `.claude/commands/discovery.md` — contenu intégral**

```markdown
---
description: Planning v6 en niveaux 0-4 — tech-spec directe pour les petits scopes, chaîne Brainstorm → PRD → Architecture → Stories au-delà, spec consolidée approuvée en sortie. Usage: /discovery "besoin"
---

# Discovery — $ARGUMENTS

Charge le skill `discovery-workflow` et exécute-le en mode **interactif**.

- Besoin : **$ARGUMENTS** (parle librement — speech-to-text OK)
- Checkpoints de validation à chaque phase (le planning garde l'humain dans la boucle).
- Niveau 0-1 → tech-spec directe (pas de PRD) ; escalade automatique en réutilisant l'acquis.
- Sortie obligatoire : la spec consolidée `docs/planning/specs/` que tu approuves au dernier checkpoint — elle donne le mandat à /dev et /auto-dev.
```

- [ ] **Step 3: `.claude/commands/auto-discovery.md` — contenu intégral**

```markdown
---
description: Planning v6 autonome (RALPH) — mêmes niveaux 0-4, zéro stop, spec en sortie toujours status draft à faire approuver par un humain. Usage: /auto-discovery "besoin"
---

# Auto-Discovery (RALPH) — $ARGUMENTS

**Session :** ${CLAUDE_SESSION_ID}

Charge le skill `discovery-workflow` et exécute-le en mode **autonome**.

- Besoin : **$ARGUMENTS** — zéro validation intermédiaire.
- La spec de sortie reste `status: draft`, `approved_by: ralph` : un humain doit l'approuver avant tout `/auto-dev`.
- Config RALPH : max **30** itérations (`--max N`), timeout **1h** (`--timeout Xh`), promise **"DISCOVERY COMPLETE"**, logs `docs/ralph-logs/${CLAUDE_SESSION_ID}.md`. Arrêt : `/cancel-ralph`.
```

- [ ] **Step 4: `.codex/prompts/ship.md` — contenu intégral**

```markdown
---
description: 'Ship v6: merge main, manifest evidence, quality-gate consumption (PASS or explicit waiver), CHANGELOG, commit, push, PR'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/ship-workflow/SKILL.md`, READ its entire contents, and execute all steps sequentially.

NON-INTERACTIVE: the user said /ship, so DO IT — the next thing they see is the PR URL. Quality comes from the committed gate file (`docs/quality/GATE-*.yaml`): PASS and fresh → straight to PR with the gate in the body; absent/stale/CONCERNS/FAIL → the skill runs quality-gate itself. Only stop for: main branch, unresolvable merge conflicts, red execution evidence, gate FAIL, or the explicit CONCERNS-waiver decision.
```

- [ ] **Step 5: `.codex/prompts/discovery.md` — contenu intégral**

```markdown
---
description: 'D-EPCT+R v6 planning: levels 0-4, tech-spec direct track, consolidated approved spec output'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/discovery-workflow/SKILL.md`, READ its entire contents, and execute the workflow in **interactive** mode, respecting every STOP CHECKPOINT.

The user's idea or need follows this line. Start with Phase 1 (Listen & Assess Level): listen without interrupting, ask at most 2-3 clarifying questions, propose a level 0-4. Levels 0-1 go straight to the consolidated tech-spec (no PRD); escalation reuses acquired work. Every discovery ends with the consolidated spec in `docs/planning/specs/` approved by the user at the final checkpoint.
```

- [ ] **Step 6: Miroirs Gemini/OpenCode**

Lire `.gemini/commands/ship.toml`, `.gemini/commands/discovery.toml`, `.opencode/commands/ship.md`, `.opencode/commands/discovery.md` ; porter les mêmes instructions que les prompts Codex des Steps 4-5, en respectant le format de chaque fichier (TOML : description + prompt en triple-quoted string SANS `"""` interne ; OpenCode : frontmatter YAML avec description **entre quotes simples** — leçon vague 2 — et `$ARGUMENTS`). Chemins de skill : garder le style existant du fichier (`.gemini/skills/... if it exists, otherwise .claude/skills/...`).

- [ ] **Step 7: Vérifier + commit**

```bash
grep -q "ship-workflow" .claude/commands/ship.md && wc -l .claude/commands/ship.md .claude/commands/discovery.md .claude/commands/auto-discovery.md && \
grep -q "gate file" .codex/prompts/ship.md && grep -q "Assess Level" .codex/prompts/discovery.md && \
! git grep -l "Pre-Landing Review" -- .claude/commands .codex .gemini .opencode && \
python3 -c "import tomllib; [tomllib.load(open(f,'rb')) for f in ['.gemini/commands/ship.toml','.gemini/commands/discovery.toml']]; print('TOML OK')" && \
python3 -c "import yaml; [yaml.safe_load(open(f).read().split('---')[1]) for f in ['.opencode/commands/ship.md','.opencode/commands/discovery.md']]; print('YAML OK')" && echo OK
git add .claude/commands/ship.md .claude/commands/discovery.md .claude/commands/auto-discovery.md .codex/prompts/ship.md .codex/prompts/discovery.md .gemini/commands/ship.toml .gemini/commands/discovery.toml .opencode/commands/ship.md .opencode/commands/discovery.md
git commit -m "refactor(commands): ship, discovery and auto-discovery become thin launchers across runtimes

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §2

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(Les 3 commandes Claude ≤ 20 lignes chacune.)

---

### Task 4: Fix installeur — les prompts Skillz s'auto-mettent à jour

**Files:**
- Modify: `install.sh` (bloc de copie des prompts Codex, ~lignes 1223-1262)

- [ ] **Step 1: Remplacer la logique de skip**

Dans la boucle de copie des prompts, remplacer :

```bash
            if [ -e "$target" ] && [ ! -L "$target" ]; then
                # Safe to overwrite if content matches (already copied from us) OR
                # if the existing file looks like a dead symlink that got replaced.
                if ! cmp -s "$prompt_file" "$target"; then
                    echo -e "   ${YELLOW}⚠️  $name (skipped — real file with different content)${NC}"
                    prompt_skip_count=$((prompt_skip_count + 1))
                    continue
                fi
            fi
```

par :

```bash
            if [ -e "$target" ] && [ ! -L "$target" ]; then
                # Overwrite if content matches (already ours) OR if the target
                # carries the Skillz loader signature (an older Skillz-shipped
                # version that must self-update). Only genuinely foreign prompts
                # (BMad, user-authored) are preserved.
                if ! cmp -s "$prompt_file" "$target" && \
                   ! grep -q "IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND" "$target"; then
                    echo -e "   ${YELLOW}⚠️  $name (skipped — user/third-party prompt preserved)${NC}"
                    prompt_skip_count=$((prompt_skip_count + 1))
                    continue
                fi
            fi
```

- [ ] **Step 2: Vérifier + commit**

```bash
bash -n install.sh && grep -q "Skillz loader signature" install.sh && echo OK
git add install.sh
git commit -m "fix(install): let Skillz-managed Codex prompts self-update via loader signature

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Docs — README, AGENTS.md, GEMINI.md, `.claude/CLAUDE.md` (section D-EPCT)

**Files:**
- Modify: `README.md`, `AGENTS.md`, `GEMINI.md`, `.claude/CLAUDE.md`

Ces quatre fichiers décrivent encore la chaîne v5.1 (multi-agent Review ×3, FULL/LIGHT, quick-fix séparé). Les mettre à jour factuellement — **lire chaque fichier d'abord**, localiser chaque passage périmé, appliquer les faits v6 ci-dessous. Ne pas restructurer au-delà.

**Les faits v6 (source de vérité pour toutes les tables/descriptions) :**

| Sujet | Ancien texte (à traquer) | Nouveau fait |
|---|---|---|
| `/dev` | « multi-agent », « Explore → Plan → Code+Tests (subagents //) → Review ×3 (subagents //) → Ship » | « adaptatif niveaux 0-4, stop unique au plan, RED conditionnel, boucle quality-gate → gate file » |
| `/quick-fix` | « sans workflow », « max 3 fichiers/50 lignes sinon /dev » | « circuit court niveau 0 du même moteur dev-workflow, escalade automatique selon la grille » |
| `/discovery` | « FULL ou LIGHT » | « niveaux 0-4 : tech-spec directe (0-1) ou chaîne complète (2-4), spec consolidée approuvée en sortie » |
| `/ship` | « pre-landing review », « tests » | « preuves du manifeste + consommation du gate file (PASS requis ou waiver explicite) » |
| Version | « D-EPCT+R v5.1 » | « D-EPCT+R v6 » |
| Schéma Dev | `EXPLORE (subagent) → PLAN → IMPLEMENT (2 subagents //) → REVIEW (3 subagents //) → SHIP` | `PROBE → EXPLORE → PLAN ⛔ → RED → IMPLEMENT → GATE (boucle) → HANDOFF` |
| Règles « 3 passes de review » | « Merger sans les 3 passes de review » etc. | « Merger sans gate file PASS (ou waiver explicite) » |
| Nouveaux skills | (absents) | ajouter `project-probe` et `quality-gate` aux listes de skills quand une liste existe |

Notes de périmètre : dans `.claude/CLAUDE.md`, ne modifier QUE la section entre `<!-- D-EPCT-START -->` et `<!-- D-EPCT-END -->` (c'est elle qu'install.sh injecte dans le CLAUDE.md global) plus la ligne de titre de version si elle est dedans. Dans README, la section Obsidian LLM Wiki ne bouge pas.

- [ ] **Step 1: Mettre à jour les 4 fichiers selon la table des faits**
- [ ] **Step 2: Vérifier + commit**

```bash
! git grep -ln "Review ×3" -- README.md AGENTS.md GEMINI.md .claude/CLAUDE.md && \
! git grep -ln "FULL ou LIGHT\|FULL vs LIGHT\|mode FULL" -- README.md AGENTS.md GEMINI.md .claude/CLAUDE.md && \
git grep -q "quality-gate" README.md && git grep -q "v6" .claude/CLAUDE.md && echo OK
git add README.md AGENTS.md GEMINI.md .claude/CLAUDE.md
git commit -m "docs: update root docs and CLAUDE.md template to D-EPCT+R v6

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §9 vague 3

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Smoke test de sortie de vague (spec §9 vague 3)

**Files:** aucun fichier repo — scratch project.

Test de sortie : « chaîne complète issue → PR sans relecture, gate dans le corps de PR ». Sur un scratch projet Node avec harness et un remote git local (bare repo) :

- [ ] **Step 1: Chaîne complète.** Simuler : besoin niveau 1 → suivre `dev-workflow` (mini-plan ⛔ simulé validé → fix → gate 1 tour → gate file PASS committé) → suivre `ship-workflow` : le Step 4 doit LIRE le gate (frais → pas de re-review), constituer le corps de PR avec le gate yaml, et dérouler CHANGELOG → commits → push vers le bare repo. (`gh pr create` : composer la commande et la LOGGER sans l'exécuter — pas de repo GitHub scratch.)
- [ ] **Step 2: Gate périmé.** Modifier un fichier après le gate, relancer `ship-workflow` : le hash ne matche plus → le skill doit relancer quality-gate lui-même avant de continuer.
- [ ] **Step 3: Sweep repo-wide.** Dans le VRAI repo (lecture seule) : `git grep -n "Pre-Landing Review\|FULL mode\|LIGHT mode\|Review ×3"` sans scoping — tout hit hors `docs/planning/`, `CHANGELOG.md` et `docs/ralph-logs/` est un finding.
- [ ] **Step 4: Rapport.** Attendu vs observé par étape, divergences avec citations, nettoyage scratch.

---

## Self-Review (faite à la rédaction)

1. **Spec coverage vague 3** : §6 ship/gate → Task 1 ; §7 discovery niveaux + spec output → Task 2 ; §2 lanceurs → Task 3 ; backlog installeur → Task 4 ; docs racine + CLAUDE.md → Task 5 ; test de sortie §9 + leçon sweep repo-wide → Task 6. Hors scope : /pr-review + brainstorm (second temps), RALPH générique.
2. **Placeholders** : contenu intégral pour les 5 fichiers réécrits (Task 3 Steps 1-5) ; édits exacts old→new pour Tasks 1, 2, 4 ; Task 5 pilotée par table de faits (les fichiers docs sont longs et leurs passages exacts varient — le reviewer vérifie contre la table) ; Task 3 Step 6 en mode miroir avec les pièges nommés (TOML `"""`, YAML quotes).
3. **Cohérence contrats** : règle de fraîcheur du hash identique à quality-gate (`:(exclude)docs/quality`, `<base>` main/master) ; clés frontmatter spec identiques au mandate gate de dev-workflow (`status`/`approved_by`/`approved_at`) ; « Pre-Landing Review » éradiqué partout (vérifs Tasks 1, 3, 6).
