# D-EPCT+R v6 — Vague 1 : project-probe + quality-gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer les deux briques partagées (`project-probe`, `quality-gate`) et les brancher sur la chaîne EPCT+R existante sans changer son modèle d'interaction.

**Architecture:** Deux nouveaux skills markdown auto-découverts par `install.sh` ; la Phase 4 (REVIEW) de `/dev` et `/auto-dev` délègue à la boucle quality-gate ; toutes les vérifications en dur (`npm run lint…`) sont remplacées par la lecture du manifeste `.agents/verification.yaml`. Spec de référence : `docs/planning/specs/2026-07-05-epctr-v6-design.md` (§3, §4, §9 vague 1).

**Tech Stack:** Markdown skills (Claude Code + Codex CLI), bash pour les vérifications structurelles.

## Global Constraints

- Les skills canoniques sont rédigés **en anglais** ; les commandes (`commands/*.md`) restent **en français** (spec §2).
- Chaque skill contient une section **Runtime capabilities** : chemin Claude Code (subagents, `/code-review`, `verify`) ET fallback séquentiel Codex — un seul fichier, jamais de dépendance Claude-only (spec §2).
- **Vague 1 ne change pas le modèle d'interaction** : les STOP checkpoints existants de `/dev` restent en place (spec §9). Le stop unique arrive en vague 2.
- Manifeste : un seul fichier `.agents/verification.yaml`, pas de miroir `.claude/` (spec §3).
- Gate file : `docs/quality/GATE-<YYYY-MM-DD>-<slug>.yaml`, committé avec la branche (spec §4).
- Règle PASS verbatim (spec §4) : PASS exige tout le vert sur la preuve exécutable disponible ET zéro finding confirmé restant ET au moins une preuve exécutable réelle ; sans preuve exécutable, plafond `CONCERNS`.
- Bornes de boucle : niveau 1 → 1 tour ; niveau 2 → max 3 ; niveaux 3-4 → max 4 (spec §4).
- Ne PAS toucher : `AGENTS.md` (modifications non committées d'un autre chantier dans le working tree), `install.sh` (auto-découverte confirmée, `install.sh:1743`), `README.md` (vague 3).
- Commits : `type(scope): description` + `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. Branche de travail : `feature/epctr-v6-design`.

---

### Task 1: Créer `skills/project-probe/SKILL.md`

**Files:**
- Create: `skills/project-probe/SKILL.md`

**Interfaces:**
- Produces: le contrat du manifeste `.agents/verification.yaml` (clés `stack`, `config_fingerprint`, `commands.{lint,typecheck,test,build}`, `testability.{harness,e2e,runtime_verify}`, `absents[]`) — consommé par quality-gate (Task 2) et les workflows (Tasks 3-4).

- [ ] **Step 1: Écrire le fichier complet**

Créer `skills/project-probe/SKILL.md` avec exactement ce contenu :

````markdown
---
name: project-probe
description: Detect and cache a project's real verification commands (lint, typecheck, test, build, run) into .agents/verification.yaml. Use at the start of any dev/ship workflow (Phase 0), before running any verification, when verification commands are unknown, or when a hardcoded command fails. Works on any stack — Node, Python, Go, Rust, Ruby, PHP, monorepos.
---

# Project Probe — Verification Manifest

Make every workflow stack-agnostic: workflows never guess or hardcode verification commands, they read the manifest this skill maintains.

**Output**: `.agents/verification.yaml` at the repo root. It is committed — it is project truth, like `package.json`. One file, no `.claude/` mirror.

## When to (re)probe

1. `.agents/verification.yaml` exists → compute the current `config_fingerprint` (below). If it matches the manifest's stored value → **read the manifest and stop, do not re-probe**. If it differs → re-probe and rewrite.
2. Manifest absent → probe and write.

Fingerprint = SHA-256 of the concatenated config files that exist, in this fixed order:

```bash
cat package.json pnpm-lock.yaml yarn.lock Makefile pyproject.toml setup.cfg \
    Cargo.toml go.mod Gemfile composer.json 2>/dev/null | shasum -a 256 | cut -d' ' -f1
```

## Probe procedure

1. **Identify stack markers**: `package.json` (+ lockfile → package manager), `pyproject.toml`/`setup.cfg`, `Cargo.toml`, `go.mod`, `Gemfile`, `composer.json`, `Makefile`, `justfile`. Detect monorepo workspaces (`workspaces` key, `pnpm-workspace.yaml`, `turbo.json`).
2. **Extract real commands** — in priority order:
   - `package.json` `scripts` (or Makefile targets / pyproject tool sections): look for `lint`, `typecheck`, `check`, `test`, `test:unit`, `build`, `dev`, `start`.
   - CI workflows (`.github/workflows/*.yml`): what CI actually runs is the strongest signal.
   - Stack defaults as last resort (see fallback table in `.claude/knowledge/workflows/verification-matrix.md`): only record a default if its tool is verifiably present (config file or dependency exists).
3. **Sanity-check each candidate** with a fast, safe invocation (`--help`, `--version`, or a dry run). Never run anything destructive (`db:reset`, `deploy`, `publish`, `clean`). If a candidate can't be confirmed, leave it out and record it in `absents` with the reason.
4. **Detect testability**:
   - `harness`: the test framework actually configured (vitest, jest, pytest, go test, cargo test…) or `none`.
   - `e2e`: e2e harness (playwright, cypress…) or `none`.
   - `runtime_verify`: how to launch the app for runtime verification (`npm run dev`, `python -m app`…) or `none` for libraries.
5. **Write the manifest** (format below), then present a one-line summary: stack, commands found, absents.

## Manifest format

```yaml
# .agents/verification.yaml — generated by project-probe. Committed.
stack: node-ts                  # node-ts | node-js | python | go | rust | ruby | php | mixed
config_fingerprint: "<sha256>"
commands:                       # only commands that verifiably exist
  lint:      "npm run lint"
  typecheck: "npm run typecheck"
  test:      "npm test"
  build:     "npm run build"
testability:
  harness: vitest               # framework name or none
  e2e: none
  runtime_verify: "npm run dev" # or none
absents:                        # explicit, never silently skipped by consumers
  - "no e2e harness"
monorepo: {}                    # optional: per-package command overrides
```

## Rules for consumers (dev-workflow, ship-workflow, quality-gate)

- Run verification **only** via `commands` from the manifest — never hardcode.
- An entry missing from `commands` means the project does not have that verification: **report it** (in the checkpoint summary or the gate file `absents`), never fake a green.
- If a manifest command fails with "command not found" or similar breakage, re-run this skill (config drifted) before concluding anything.

## Anti-patterns

- Inventing a command because the stack "usually" has it — record what exists, not what should exist.
- Re-probing on every run when the fingerprint is unchanged (wasted time).
- Writing a `.claude/verification.yaml` mirror — one file only.
- Running destructive scripts during the sanity check.
````

- [ ] **Step 2: Vérifier la structure du fichier**

```bash
head -4 skills/project-probe/SKILL.md | grep -c "^---$" | grep -q 2 && \
grep -q "^name: project-probe" skills/project-probe/SKILL.md && \
grep -q ".agents/verification.yaml" skills/project-probe/SKILL.md && \
grep -q "config_fingerprint" skills/project-probe/SKILL.md && echo OK
```

Expected: `OK` (le `head -4 | grep -c "^---$"` compte 2 délimiteurs de frontmatter : ouverture ligne 1, fermeture ligne 4).

- [ ] **Step 3: Commit**

```bash
git add skills/project-probe/SKILL.md
git commit -m "feat(skills): add project-probe verification manifest skill

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §3

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Créer `skills/quality-gate/SKILL.md`

**Files:**
- Create: `skills/quality-gate/SKILL.md`

**Interfaces:**
- Consumes: le manifeste défini en Task 1 (`.agents/verification.yaml`, clés `commands`, `testability`, `absents`).
- Produces: le contrat du gate file `docs/quality/GATE-<date>-<slug>.yaml` (clés `verdict`, `niveau`, `tours`, `diff_hash`, `preuve.executable`, `preuve.opinion.findings`, `decisions_prises_en_ton_nom[]`, `absents[]`) — consommé par les workflows (Tasks 3-4) et par ship-workflow en vague 3.

- [ ] **Step 1: Écrire le fichier complet**

Créer `skills/quality-gate/SKILL.md` avec exactement ce contenu :

````markdown
---
name: quality-gate
description: Bounded agentic quality loop that replaces human code re-reading before PR. Runs execution evidence (lint/types/tests/runtime verify), multi-lens reviews in fresh contexts, adversarial counter-verification of every finding, loops until convergence, and writes a versioned gate file (PASS/CONCERNS/FAIL/WAIVED) with proof. Use after implementation in /dev, before PR in /ship, or standalone on any diff the user wants gated.
---

# Quality Gate — Convergence Loop

Replaces the one-shot "review ×3" with a bounded loop that produces an auditable verdict. The user reads the gate file instead of the diff.

**Inputs**:
- The diff to gate: `git diff main...HEAD` (or the diff the caller designates).
- The validated plan / acceptance criteria, when the caller has one.
- `.agents/verification.yaml` — if missing, run the `project-probe` skill first.
- The task level (0-4). Default: 2. The caller passes it; level 0 changes are not gated (no gate file).

**Output**: `docs/quality/GATE-<YYYY-MM-DD>-<slug>.yaml` (slug = branch name or story slug, kebab-case) + a short summary to the caller.

## Loop bounds by level

| Level | Max rounds | Review lenses |
|---|---|---|
| 1 | 1 | one generalist reviewer |
| 2 | 3 | correctness+security · readability · performance |
| 3-4 | 4 | level-2 lenses + `design-audit` / `seo-geo-audit` / `a11y-enforcer` for the surfaces the caller detected |

## One round

1. **EXECUTION EVIDENCE — always first, never skipped.**
   Run every command in the manifest's `commands`. If the harness provides the `verify` skill, drive the app's real affected flow (not just tests). Any red → fix immediately → restart the round. Record each command and its actual result; a claim without the executed command's output is worthless.
   If the diff touches only docs/config with no runtime surface, still run the manifest commands and note the limitation in `absents` — never skip silently.

2. **MULTI-LENS REVIEWS — fresh contexts.**
   Each lens reviews the diff + plan only (no session history). Findings are classified P0 (must fix) / P1 (should fix) / P2-P3 (note).
   **Runtime capabilities:**
   - *Claude Code*: use the native `/code-review` skill as the primary correctness lens (its CONFIRMED/PLAUSIBLE verdicts feed step 3 directly — CONFIRMED skips re-verification). Dispatch the remaining lenses as parallel subagents.
   - *Sequential runtimes (Codex CLI)*: run the lenses one at a time in distinct passes, with an explicit mental reset between lenses.

3. **ADVERSARIAL COUNTER-VERIFICATION — new findings only.**
   Maintain a findings registry across rounds. Stable id: `<file>:<category>:<8-char-hash-of-quoted-excerpt>`.
   - A finding already in the registry (confirmed or refuted) is not re-verified and not counted as new.
   - Each NEW finding goes to an independent verifier whose explicit job is to REFUTE it against the actual code. Uncertain → refuted (bias against false positives).
   - Confirmed → fix queue. Refuted → registry, never returns.

4. **FIX confirmed P0/P1** (the orchestrator fixes — it has context), then return to step 1. P2/P3 go to the gate file as notes, not fixes (no scope creep).

**Convergence**: two consecutive rounds with zero new confirmed findings → verdict. Cap reached without convergence → verdict `CONCERNS`, remaining findings listed. Never loop past the cap.
**Level-1 exception** (cap = 1 round): the verdict is decided on that single round — confirmed findings fixed + execution evidence re-run green → `PASS`.

## Verdict rules

- `PASS` requires ALL of: every available executable evidence green · zero confirmed findings remaining · at least one real executable proof (tests or runtime verify). A project with no executable evidence at all **caps at `CONCERNS`** — the gate cannot claim more than it knows.
- `FAIL`: confirmed P0 remaining that could not be fixed within the cap.
- `CONCERNS`: cap reached without convergence, or executable evidence too weak for PASS, or unfixed confirmed P1.
- `WAIVED`: only on explicit user request, with the reason recorded in the gate file.

## Gate file format

```yaml
# docs/quality/GATE-2026-07-05-auth-refresh.yaml
verdict: PASS                # PASS | CONCERNS | FAIL | WAIVED
niveau: 2
tours: 3
diff_hash: "<sha256 of the gated diff>"   # freshness: consumers recompute and compare
preuve:
  executable:                # the only possible basis for a PASS
    lint:   { cmd: "npm run lint", statut: vert }
    types:  { cmd: "tsc --noEmit", statut: vert }
    tests:  { cmd: "npm test", statut: "vert (47 passed)" }
    verify: { flow: "login -> refresh -> logout", statut: vert }
  opinion:
    findings: { total: 9, confirmes: 4, refutes: 5, corriges: 4, restants: 0 }
decisions_prises_en_ton_nom:
  - "refresh token stored in httpOnly cookie instead of localStorage as the issue suggested — XSS"
absents:
  - "no e2e harness"
```

Compute `diff_hash` with: `git diff main...HEAD | shasum -a 256 | cut -d' ' -f1`.

`decisions_prises_en_ton_nom` lists every autonomous deviation from the validated plan. **For levels 3-4 the calling workflow must show this section to the user before proposing ship** — it is the only careful read left to the human.

## Anti-patterns

- Claiming a command is green without showing its executed output.
- Re-verifying or re-counting registry findings (the loop never converges).
- Skipping execution evidence because "only docs changed".
- Fixing P2/P3 style findings during the loop (scope creep — note them instead).
- Looping past the cap, or emitting PASS on opinion alone.
````

- [ ] **Step 2: Vérifier la structure et la cohérence avec Task 1**

```bash
head -4 skills/quality-gate/SKILL.md | grep -c "^---$" | grep -q 2 && \
grep -q "^name: quality-gate" skills/quality-gate/SKILL.md && \
grep -q "project-probe" skills/quality-gate/SKILL.md && \
grep -q "docs/quality/GATE-" skills/quality-gate/SKILL.md && \
grep -q "diff_hash" skills/quality-gate/SKILL.md && echo OK
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/quality-gate/SKILL.md
git commit -m "feat(skills): add quality-gate convergence loop skill

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §4

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Brancher `skills/dev-workflow/SKILL.md` sur les deux briques

**Files:**
- Modify: `skills/dev-workflow/SKILL.md` (Phase 1 step ajouté, Phase 3 step 3, Phase 4 entière, section Referenced knowledge)

**Interfaces:**
- Consumes: `project-probe` (manifeste) et `quality-gate` (boucle + gate file) tels que définis en Tasks 1-2.

- [ ] **Step 1: Ajouter le probe en tête de Phase 1**

Dans `skills/dev-workflow/SKILL.md`, remplacer :

```markdown
## Phase 1 — EXPLORE

**Goal**: build a complete mental model of the codebase relevant to the task.

1. If the task argument is an issue reference
```

par :

```markdown
## Phase 1 — EXPLORE

**Goal**: build a complete mental model of the codebase relevant to the task.

0. Run the `project-probe` skill: read `.agents/verification.yaml` (create it if absent or stale). All verification in later phases uses the manifest's commands.

1. If the task argument is an issue reference
```

- [ ] **Step 2: Remplacer la vérification en dur de Phase 3**

Remplacer :

```markdown
3. **Verify lint + types + tests pass** after each step:
   ```bash
   npm run lint && npm run typecheck && npm test
   ```
   (adapt to project's actual commands — check `package.json` scripts or equivalent)
```

par :

```markdown
3. **Verify after each step** by running the `commands` from `.agents/verification.yaml` (lint, typecheck, test). A command absent from the manifest is reported as absent — never faked green, never guessed.
```

- [ ] **Step 3: Remplacer la Phase 4 (REVIEW) par la délégation à quality-gate**

Remplacer tout le bloc depuis `## Phase 4 — REVIEW (3 sequential passes)` jusqu'à la ligne `**STOP CHECKPOINT 4** — Present consolidated review + fixes applied. Wait for user validation before ship.` (incluse) par :

```markdown
## Phase 4 — REVIEW (quality-gate loop)

**Goal**: converge on proven quality instead of a one-shot review.

1. Determine the gate level: 2 by default; 3 if frontend or SEO/GEO work was detected in Phase 1 (their audit lenses join the loop).
2. Run the `quality-gate` skill on `git diff main...HEAD` with the validated plan and the manifest. It loops (bounded) through execution evidence → multi-lens reviews → adversarial counter-verification → fixes, and writes `docs/quality/GATE-<date>-<slug>.yaml`.
3. Commit the gate file with the branch.

**STOP CHECKPOINT 4** — Present the gate summary: verdict, rounds, findings (confirmed/refuted/fixed), `decisions_prises_en_ton_nom`, absents. Wait for user validation before ship.
```

- [ ] **Step 4: Mettre à jour la section Referenced knowledge & skills**

Dans la liste finale `## Referenced knowledge & skills`, ajouter ces deux lignes avant la ligne `- Testing strategy:` :

```markdown
- Verification manifest: the `project-probe` skill (`.agents/verification.yaml`)
- Quality loop & gate file: the `quality-gate` skill (`docs/quality/GATE-*.yaml`)
```

- [ ] **Step 5: Vérifier la cohérence**

```bash
grep -q "project-probe" skills/dev-workflow/SKILL.md && \
grep -q "quality-gate" skills/dev-workflow/SKILL.md && \
! grep -q "npm run lint && npm run typecheck && npm test" skills/dev-workflow/SKILL.md && \
grep -c "STOP CHECKPOINT" skills/dev-workflow/SKILL.md | grep -q 4 && echo OK
```

Expected: `OK` (les 4 STOP checkpoints sont préservés — le stop unique est vague 2).

- [ ] **Step 6: Commit**

```bash
git add skills/dev-workflow/SKILL.md
git commit -m "refactor(dev-workflow): delegate review to quality-gate, verify via manifest

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §9 vague 1

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Brancher `commands/dev.md` et `commands/auto-dev.md`

**Files:**
- Modify: `commands/dev.md` (Phase 4, Phase 4.5/4.6 conservées, Phase 5.0)
- Modify: `commands/auto-dev.md` (Phase 4, Phase 5)

- [ ] **Step 1: `commands/dev.md` — Phase 4 délègue à quality-gate**

Remplacer tout le bloc depuis `## Phase 4: REVIEW (3 subagents parallèles)` jusqu'à la ligne `3. **Relancer les tests** après corrections` (incluse, juste avant `### Phase 4.5: DESIGN AUDIT`) par :

```markdown
## Phase 4: REVIEW (boucle quality-gate)

Charger le skill `quality-gate` et le lancer sur `git diff main...HEAD` avec le plan validé :

- Niveau de gate : 2 par défaut ; 3 si FRONTEND ou SEO/GEO détecté (leurs lentilles d'audit rejoignent la boucle).
- La boucle est bornée : preuves d'exécution (commandes du manifeste `.agents/verification.yaml`) → reviews multi-lentilles en subagents frais → contre-vérification adversariale des findings nouveaux → fix des confirmés P0/P1 → re-tour, jusqu'à convergence (2 tours propres) ou cap.
- Sortie : `docs/quality/GATE-<date>-<slug>.yaml`, committé avec la branche.
```

Les sections `### Phase 4.5: DESIGN AUDIT` et `### Phase 4.6: SEO/GEO AUDIT` restent inchangées (en vague 1 elles complètent la boucle ; elles fusionneront dans les lentilles en vague 2). Le `**STOP CHECKPOINT 4**` existant reste inchangé, mais remplacer sa phrase par :

```markdown
**STOP CHECKPOINT 4** — Présenter le résumé du gate : verdict, tours, findings (confirmés/réfutés/corrigés), `decisions_prises_en_ton_nom`, absents + verdict design/SEO le cas échéant. Validation.
```

- [ ] **Step 2: `commands/dev.md` — Phase 5.0 lit le manifeste**

Remplacer le tableau de la section `### 5.0 Verification-before-completion (gate obligatoire)` :

```markdown
| Check | Commande | Statut |
|---|---|---|
| Lint | `npm run lint` (ou équivalent stack) | ✅ |
| Types | `npm run typecheck` (ou `tsc --noEmit`) | ✅ |
| Tests P0/P1 | `npm test` | ✅ |
```

par :

```markdown
| Check | Commande | Statut |
|---|---|---|
| Lint / Types / Tests | les `commands` de `.agents/verification.yaml` | ✅ |
| Gate file | `docs/quality/GATE-<date>-<slug>.yaml` — verdict PASS (ou CONCERNS explicitement accepté) | ✅ |
```

- [ ] **Step 3: `commands/auto-dev.md` — Phase 4 et Phase 5**

Remplacer le bloc `### Phase 4: REVIEW (3 subagents parallèles)` (les 8 lignes de sa liste à puces, jusqu'à `- Relancer les tests après corrections` incluse) par :

```markdown
### Phase 4: REVIEW (boucle quality-gate)
- Charger le skill `quality-gate` sur `git diff main...HEAD` (niveau 2, ou 3 si FRONTEND)
- Boucle bornée : preuves d'exécution (manifeste) → lentilles → contre-vérification → fix → re-tour
- Sortie : `docs/quality/GATE-<date>-<slug>.yaml` committé
- En autonome, un verdict FAIL = nouvelle itération RALPH ; > 3 tentatives → STOP
```

Dans `### Phase 5: FINALIZE`, remplacer les 3 premières lignes du tableau des vérifs (Lint / Types / Tests P0/P1) par :

```markdown
| Vérifs du manifeste | les `commands` de `.agents/verification.yaml` | ✅ |
| Gate file | verdict PASS requis en autonome (jamais CONCERNS auto-accepté) | ✅ |
```

(la ligne `| Log RALPH cohérent | ... |` reste inchangée)

- [ ] **Step 4: Vérifier la cohérence**

```bash
grep -q "quality-gate" commands/dev.md && grep -q "verification.yaml" commands/dev.md && \
grep -q "quality-gate" commands/auto-dev.md && grep -q "verification.yaml" commands/auto-dev.md && \
grep -q "Phase 4.5: DESIGN AUDIT" commands/dev.md && echo OK
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add commands/dev.md commands/auto-dev.md
git commit -m "refactor(commands): wire dev and auto-dev to quality-gate and manifest

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §9 vague 1

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: `verification-matrix.md` devient fallback du probe

**Files:**
- Modify: `.claude/knowledge/workflows/verification-matrix.md`

- [ ] **Step 1: Ajouter l'avant-propos manifeste**

Insérer immédiatement après le titre `# Verification Before Completion — Matrice par workflow` :

```markdown
> **Source de vérité : `.agents/verification.yaml`** (généré par le skill `project-probe`).
> Les workflows lisent le manifeste, jamais cette table directement. La table
> « Commandes par stack » ci-dessous ne sert qu'au probe comme fallback quand
> aucun script explicite n'est trouvé — et seulement si l'outil est vérifiablement présent.
```

- [ ] **Step 2: Vérifier + commit**

```bash
grep -q "verification.yaml" .claude/knowledge/workflows/verification-matrix.md && echo OK
git add .claude/knowledge/workflows/verification-matrix.md
git commit -m "docs(knowledge): make verification-matrix a probe fallback

Refs: docs/planning/specs/2026-07-05-epctr-v6-design.md §3

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Smoke test de sortie de vague (spec §9)

**Files:**
- Aucun fichier du repo — scratch projects jetables dans le scratchpad de session.

**Test de sortie de la spec** : « un `/dev` réel produit un gate file correct sur un projet Node et un projet Python ». On teste ici les deux briques en suivant leurs SKILL.md à la lettre, comme le ferait un runtime.

- [ ] **Step 1: Créer le scratch projet Node**

```bash
SCRATCH="$CLAUDE_SCRATCHPAD_DIR"  # ou le scratchpad de la session
mkdir -p "$SCRATCH/probe-node/src" && cd "$SCRATCH/probe-node"
cat > package.json <<'EOF'
{
  "name": "probe-node-smoke",
  "private": true,
  "scripts": {
    "lint": "node -e \"process.exit(0)\"",
    "test": "node --test"
  }
}
EOF
cat > src/add.test.js <<'EOF'
const test = require('node:test');
const assert = require('node:assert');
test('adds', () => { assert.strictEqual(1 + 1, 2); });
EOF
git init -q && git add -A && git commit -qm init
```

- [ ] **Step 2: Exécuter la procédure project-probe sur le scratch Node**

Suivre `skills/project-probe/SKILL.md` (le fichier du repo, pas une version installée) sur ce projet. Vérifications :

```bash
test -f .agents/verification.yaml && \
grep -q "stack: node" .agents/verification.yaml && \
grep -q 'lint:' .agents/verification.yaml && \
grep -q 'test:' .agents/verification.yaml && \
grep -q "config_fingerprint" .agents/verification.yaml && \
! grep -q "typecheck:" .agents/verification.yaml && \
grep -qi "typecheck" .agents/verification.yaml && echo OK
```

Expected: `OK` — pas de script `typecheck` dans package.json donc pas de commande inventée, mais l'absence est notée dans `absents`.

- [ ] **Step 3: Exécuter la boucle quality-gate niveau 1 sur un petit diff Node**

Créer une branche, introduire un petit changement avec un défaut évident, et suivre `skills/quality-gate/SKILL.md` en niveau 1 :

```bash
git checkout -qb feature/smoke
cat > src/div.js <<'EOF'
function div(a, b) { return a / b; }
module.exports = { div };
EOF
git add -A && git commit -qm "feat: div"
```

Suivre la boucle (1 tour : preuves d'exécution via le manifeste → 1 reviewer → contre-vérification → fix éventuel). Vérifications de sortie :

```bash
ls docs/quality/GATE-*.yaml && \
grep -q "verdict:" docs/quality/GATE-*.yaml && \
grep -q "diff_hash:" docs/quality/GATE-*.yaml && \
grep -q "executable:" docs/quality/GATE-*.yaml && echo OK
```

Expected: `OK`, et le verdict doit être cohérent avec la règle PASS (le projet a un test réel qui tourne → PASS possible si le reviewer ne confirme rien de bloquant ; la division par zéro non gérée est un finding attendu du reviewer — son sort (confirmé/réfuté) doit apparaître dans `preuve.opinion.findings`).

- [ ] **Step 4: Scratch projet Python — probe sans harness**

```bash
mkdir -p "$SCRATCH/probe-py" && cd "$SCRATCH/probe-py"
cat > pyproject.toml <<'EOF'
[project]
name = "probe-py-smoke"
version = "0.1.0"
EOF
cat > main.py <<'EOF'
def greet(name: str) -> str:
    return f"hello {name}"
EOF
git init -q && git add -A && git commit -qm init
```

Suivre `skills/project-probe/SKILL.md`. Vérifications :

```bash
test -f .agents/verification.yaml && \
grep -q "stack: python" .agents/verification.yaml && \
grep -q "harness: none" .agents/verification.yaml && \
grep -q "absents:" .agents/verification.yaml && echo OK
```

Expected: `OK` — aucun outil configuré (pas de pytest/ruff/mypy installés ni configurés) → `commands` quasi vide, absents explicites, `harness: none`.

- [ ] **Step 5: Vérifier le plafond CONCERNS sans preuve exécutable**

Sur `probe-py`, créer un petit diff (ajouter une fonction) et suivre `skills/quality-gate/SKILL.md` en niveau 1. Vérification clé :

```bash
grep -q "verdict: CONCERNS" docs/quality/GATE-*.yaml && echo OK
```

Expected: `OK` — projet sans aucune preuve exécutable → le verdict DOIT plafonner à CONCERNS même si aucun finding n'est confirmé (règle PASS de la spec §4). Si le gate émet PASS ici, la formulation du SKILL.md est trop faible : corriger le skill et rejouer.

- [ ] **Step 6: Rapport de sortie de vague**

Consigner dans le message final : résultats des 4 vérifications (probe Node, gate Node, probe Python, plafond CONCERNS Python), divergences observées entre le comportement et les SKILL.md, corrections apportées. Nettoyer les scratch dirs.

---

## Self-Review (faite à la rédaction)

1. **Spec coverage vague 1** : §3 manifeste → Tasks 1, 5 ; §4 boucle + gate file + règles de verdict → Task 2 ; §9 branchement chaîne existante → Tasks 3-4 ; §9 test de sortie Node+Python → Task 6. Le README/`AGENTS.md`/install restent hors vague 1 (conformes §9). ✅
2. **Placeholders** : aucun TBD ; le contenu intégral des deux SKILL.md est dans le plan. ✅
3. **Cohérence des types/contrats** : clés du manifeste identiques entre Task 1 (producteur), Task 2 (consommateur `commands`/`testability`/`absents`) et Tasks 3-4 (références `.agents/verification.yaml`) ; clés du gate file identiques entre Task 2 et les vérifications de Task 6 (`verdict`, `diff_hash`, `executable`). Niveaux et bornes (1→1, 2→3, 3-4→4) identiques spec §4 / Task 2. ✅
