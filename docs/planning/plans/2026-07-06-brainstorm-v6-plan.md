# Brainstorm v6 — Implementation Plan (second temps)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Livrer l'Advanced Elicitation (skill + /elicit), l'anti-consensus room de multi-mind, le pressure-test [P] de /discovery, et purger le vocabulaire FULL/LIGHT des skills PM.

**Architecture:** Un nouveau skill `elicitation` (canonique EN) + CSV de lentilles + lanceurs (commande FR, prompt Codex signé) ; édits ciblés sur multi-mind, discovery-workflow, rodin, idea-brainstorm ; substitution de vocabulaire dans 4 skills. Spec : `docs/planning/specs/2026-07-06-brainstorm-v6-design.md`.

**Tech Stack:** Markdown skills, CSV knowledge.

## Global Constraints

- Skill canonique **en anglais** ; commande `/elicit` **en français** ; prompt Codex en anglais avec la signature loader `IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND` (elle déclenche l'auto-update installeur).
- Une lentille à la fois ; la lentille **révèle, elle ne réécrit pas** (spec §2).
- Anti-consensus : règle dure — pas de consensus déclaré sans objection Contrarian traitée (spec §3).
- Points d'accroche = références légères (1-3 lignes), pas de refonte de discovery/rodin/idea-brainstorm.
- Chemins réels : `.claude/skills/...`, `.claude/commands/...`, `.claude/knowledge/...` (symlinks racine).
- Ne PAS toucher : `/pr-review`, ship/dev workflows, `AGENTS.md`/`GEMINI.md`/`README.md` racine (pas de nouveau contenu doc cette vague — le catalogue sera rafraîchi plus tard), `.codex/hooks*`.
- Sweep de sortie **repo-wide et case-insensitive** (leçon vagues 2-3).
- Commits : `type(scope): description` + `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. Branche : `feature/brainstorm-v6`.

---

### Task 1: Créer le CSV des lentilles + le skill `elicitation`

**Files:**
- Create: `.claude/knowledge/brainstorming/elicitation-methods.csv`
- Create: `.claude/skills/elicitation/SKILL.md`

- [ ] **Step 1: Écrire le CSV complet**

Créer `.claude/knowledge/brainstorming/elicitation-methods.csv` avec exactement ce contenu :

```csv
lens_id,name,description,core_question,best_for
premortem,Pre-mortem,"Assume the plan shipped and failed catastrophically 6 months from now. Work backwards to the causes.","It failed — what killed it?","Plans, PRDs, architectures before commitment"
inversion,Inversion,"Instead of asking how to succeed, enumerate everything that would guarantee failure, then check the target against that list.","How would we guarantee this fails?","Strategies, processes, quality criteria"
first-principles,First Principles,"Strip every assumption inherited by analogy or habit; rebuild the reasoning from verifiable base facts only.","What do we actually know to be true here?","Inherited designs, 'we've always done it this way'"
red-blue,Red Team vs Blue Team,"Split into an attacker seeking to break the proposal and a defender patching each attack; alternate until attacks repeat.","How would an adversary exploit this?","Security decisions, APIs, trust boundaries, incentives"
steelman,Steelman-then-attack,"Build the strongest possible version of the opposing position before criticizing the target; only then compare.","What is the best case AGAINST our choice?","Contested decisions, technology choices"
chesterton,Chesterton's Fence,"For every element the proposal removes or replaces, explain why it existed before touching it.","Why was the old thing there?","Refactors, process changes, deletions"
ten-ten-ten,10-10-10,"Evaluate the decision's consequences at 10 minutes, 10 months and 10 years.","How does this look in 10 minutes / 10 months / 10 years?","Trade-offs between speed and durability"
second-order,Second-Order Effects,"Ignore the direct effect; enumerate what the effect causes next — who adapts, what breaks, what incentives shift.","And then what happens?","Pricing, incentives, public APIs, policies"
occam,Occam's Razor,"Find the simplest explanation or design that accounts for all the hard requirements; flag every element the simple version lacks.","What is the simplest thing that could work?","Over-engineered designs, complex architectures"
constraint-removal,Constraint Removal,"Pick the binding constraint (budget, stack, deadline, team) and redesign as if it vanished; harvest what transfers back.","What would we do without constraint X?","Stuck designs, incremental thinking"
persona-shift,Persona Shift,"Re-read the target as a novice, then as a domain expert, then as a hostile user; log what each one trips on.","What does a novice / expert / adversary see?","Docs, UX flows, onboarding, error messages"
cost-of-delay,Cost of Delay,"Quantify what waiting costs per week versus what shipping imperfect costs; make the time dimension explicit.","What does one more week cost us?","Prioritization, scope debates, perfectionism"
```

- [ ] **Step 2: Écrire le skill complet**

Créer `.claude/skills/elicitation/SKILL.md` avec exactement ce contenu :

````markdown
---
name: elicitation
description: Re-examine an existing output (PRD, plan, spec, code, decision, doc) through ONE named reasoning lens — Pre-mortem, Inversion, First Principles, Red/Blue Team, Steelman, Chesterton's Fence and more — instead of a vague "make it better". Loaded by /elicit. Use after any phase output, before validating a checkpoint, or whenever a second structured look would beat a rewrite.
---

# Elicitation — Named Reasoning Lenses

A lens is a disciplined second pass over something that already exists. It reveals; it does not rewrite.

**Inputs**: a target (file path, or the conversation's latest phase output) and a lens id — or no lens, in which case present the menu.
**Output**: findings under that single lens + proposed revisions. The user arbitrates; nothing is applied without their pick.

## Protocol

1. **Load the lens** from `.claude/knowledge/brainstorming/elicitation-methods.csv` (columns: `lens_id,name,description,core_question,best_for`). No lens given → show the menu as a numbered table (name + core question + best_for) and let the user pick; suggest the 2-3 best fits for the target type.
2. **Re-read the target under that single lens.** Hold the `core_question` against every section. Do not mix lenses; do not drift into general review.
3. **Produce the findings**, structured:
   - **Lens**: name + core question
   - **Findings**: 3-8 bullets — each one names the section/claim it hits and what the lens reveals
   - **Proposed revisions**: concrete, minimal edits or additions (quote what would change) — proposals, not applied changes
   - **Verdict**: does the target survive this lens as-is, with revisions, or not at all?
4. **The user arbitrates**: apply some/all revisions, run another lens, or stop. One lens per pass — chaining lenses is fine, blending them is not.

## Rules

- One lens at a time. The value comes from the discipline of the single question.
- The lens reveals — it never rewrites the target itself. Revisions are proposals.
- Findings must point at specific sections/claims, never "overall it could be better".
- Actionable output over essay: every finding either triggers a proposed revision or names an accepted risk.
- If the target survives a lens with nothing found, say so plainly — an empty pass is information, not failure.

## Where this plugs in

- `discovery-workflow` checkpoints: offer `[E] apply a lens before validating`.
- `rodin` (socratic challenge): distinct gesture — rodin argues against the position; elicitation re-reads it under one question. Use rodin for "challenge this", a lens for "re-examine this under X".
- `idea-brainstorm` synthesis: offer a lens pass on the top ideas before closing.
- `multi-mind`: the Contrarian persona may pick any lens as its weapon.

## Anti-patterns

- Blending several lenses in one pass (produces generic review soup)
- Rewriting the target instead of proposing revisions
- Running a lens on nothing (the target must exist first — this is not ideation)
- Treating the menu as a checklist to run entirely (2-3 well-chosen lenses beat 12 mechanical ones)
````

- [ ] **Step 3: Vérifier + commit**

```bash
python3 -c "import csv; rows=list(csv.DictReader(open('.claude/knowledge/brainstorming/elicitation-methods.csv'))); assert len(rows)==12 and all(r['lens_id'] and r['core_question'] for r in rows); print('CSV OK')" && \
grep -q "^name: elicitation" .claude/skills/elicitation/SKILL.md && \
grep -q "elicitation-methods.csv" .claude/skills/elicitation/SKILL.md && \
grep -q "It reveals; it does not rewrite" .claude/skills/elicitation/SKILL.md && echo OK
git add .claude/knowledge/brainstorming/elicitation-methods.csv .claude/skills/elicitation/SKILL.md
git commit -m "feat(skills): add elicitation skill with 12 named reasoning lenses

Refs: docs/planning/specs/2026-07-06-brainstorm-v6-design.md §2

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Lanceurs `/elicit` (Claude + Codex)

**Files:**
- Create: `.claude/commands/elicit.md`
- Create: `.codex/prompts/elicit.md`

- [ ] **Step 1: `.claude/commands/elicit.md` — contenu intégral**

```markdown
---
description: Ré-examine une sortie existante (PRD, plan, spec, code, doc) sous UNE lentille de raisonnement nommée (Pre-mortem, Inversion, First Principles, Red/Blue…). Usage: /elicit [lentille] [cible]
---

# Elicit — $ARGUMENTS

Charge le skill `elicitation` et exécute-le.

- Arguments : **$ARGUMENTS** — une lentille (`premortem`, `inversion`, `first-principles`, `red-blue`, `steelman`, `chesterton`, `ten-ten-ten`, `second-order`, `occam`, `constraint-removal`, `persona-shift`, `cost-of-delay`) et/ou une cible (chemin de fichier). Sans lentille : présente le menu et suggère les 2-3 plus adaptées.
- Sans cible explicite : la dernière sortie de phase de la conversation.
- Une lentille à la fois ; findings + révisions proposées — rien n'est appliqué sans mon arbitrage.
```

- [ ] **Step 2: `.codex/prompts/elicit.md` — contenu intégral**

```markdown
---
description: 'Re-examine an existing output through ONE named reasoning lens (Pre-mortem, Inversion, First Principles, Red/Blue…)'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/elicitation/SKILL.md`, READ its entire contents, and execute the protocol.

The user's arguments follow this line: a lens id and/or a target file path. No lens given → present the menu from the CSV and suggest the 2-3 best fits. No target given → the conversation's latest phase output.

One lens at a time. The lens reveals; it does not rewrite — findings and proposed revisions only, the user arbitrates.
```

- [ ] **Step 3: Vérifier + commit**

```bash
grep -q "skill \`elicitation\`" .claude/commands/elicit.md && wc -l .claude/commands/elicit.md && \
grep -q "IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND" .codex/prompts/elicit.md && \
python3 -c "import yaml; yaml.safe_load(open('.codex/prompts/elicit.md').read().split('---')[1]); print('YAML OK')" && echo OK
git add .claude/commands/elicit.md .codex/prompts/elicit.md
git commit -m "feat(commands): add /elicit launchers (Claude + Codex)

Refs: docs/planning/specs/2026-07-06-brainstorm-v6-design.md §2

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(`elicit.md` Claude ≤ 15 lignes.)

---

### Task 3: Anti-consensus room dans multi-mind

**Files:**
- Modify: `.claude/skills/multi-mind/SKILL.md`
- Modify: `.claude/knowledge/multi-mind/agent-personalities.md`

- [ ] **Step 1: Ajouter le persona Contrarian**

LIRE `.claude/knowledge/multi-mind/agent-personalities.md` pour adopter son format exact (structure des personas existants), puis ajouter à la fin un persona **Contrarian** au même format, avec ce mandat (adapter la mise en forme, pas le fond) :

- Nom : **Contrarian** (« l'anti-consensus »)
- Spécialité : produire la plus forte objection au consensus émergent, quel que soit le sujet.
- Règles propres : il n'a PAS le droit d'être d'accord ; si le débat converge, son travail commence ; il peut s'armer d'une lentille d'elicitation (`.claude/knowledge/brainstorming/elicitation-methods.csv`) — typiquement Pre-mortem, Inversion ou Steelman-then-attack ; il vise la meilleure objection, pas la plus nombreuse ; jouable par Claude si aucun agent externe n'est disponible.

- [ ] **Step 2: La règle dure dans multi-mind/SKILL.md**

LIRE la structure des rounds du skill, puis :
1. Dans la liste `Règles STRICTES`, ajouter après la ligne `- ⛔ Ne JAMAIS forcer un consensus artificiel` :
```markdown
- ⛔ Ne JAMAIS déclarer un consensus tant que le **Contrarian** n'a pas produit sa meilleure objection au round final ET que celle-ci n'a pas reçu une réponse explicite (réfutée avec raison, ou intégrée). Sinon : divergence documentée, pas de consensus.
```
2. Ajouter une section `## Anti-consensus room` (avant la section de rapport final, à localiser en lisant le fichier) :
```markdown
## Anti-consensus room

Le **Contrarian** (voir `agent-personalities.md`) siège dans chaque débat. Au round de convergence, il produit LA plus forte objection au consensus émergent — armé au besoin d'une lentille d'elicitation (Pre-mortem, Inversion, Steelman). Le consensus n'existe que si son objection est explicitement réfutée (avec raison) ou intégrée ; sinon le rapport documente la divergence.

**Déclenchement en cours de workflow** : `multi-mind --room anti-consensus <cible>` invoque une session courte (Contrarian + 2 agents) sur une décision en cours — mid-brainstorm, mid-PRD, mid-plan — sans casser le fil du workflow appelant : le rapport court revient dans la conversation, le workflow reprend où il en était.
```

- [ ] **Step 3: Frontmatter multi-mind (nettoyage FULL inclus)**

Dans la `description:` du frontmatter, remplacer `Utiliser pour obtenir des perspectives diverses sur des décisions critiques, après un PRD en mode FULL, ou après une code review de code critique.` par `Utiliser pour obtenir des perspectives diverses sur des décisions critiques, après un PRD de niveau 2+, ou après une code review de code critique. Inclut l'anti-consensus room (Contrarian).`

- [ ] **Step 4: Vérifier + commit**

```bash
grep -q "Contrarian" .claude/knowledge/multi-mind/agent-personalities.md && \
grep -q "Anti-consensus room" .claude/skills/multi-mind/SKILL.md && \
grep -q "Ne JAMAIS déclarer un consensus tant que" .claude/skills/multi-mind/SKILL.md && \
! grep -q "mode FULL" .claude/skills/multi-mind/SKILL.md && echo OK
git add .claude/skills/multi-mind/SKILL.md .claude/knowledge/multi-mind/agent-personalities.md
git commit -m "feat(multi-mind): add Contrarian anti-consensus room

Refs: docs/planning/specs/2026-07-06-brainstorm-v6-design.md §3

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Pressure-test [P] dans discovery + accroches rodin/idea-brainstorm

**Files:**
- Modify: `.claude/skills/discovery-workflow/SKILL.md`
- Modify: `.claude/skills/rodin/SKILL.md` (si présent dans le repo ; sinon noter au rapport)
- Modify: `.claude/skills/idea-brainstorm/SKILL.md`

- [ ] **Step 1: Option [P] + [E] dans discovery-workflow**

Dans `## Phase 1 — LISTEN & ASSESS LEVEL`, après le point `2.` (clarifying questions), insérer :

```markdown
2-bis. **Offer the pressure-test**: `[P] Pressure-test the idea first` — before any brainstorm, challenge the idea socratically (rodin posture) armed with 2-3 elicitation lenses picked for the idea (typically Pre-mortem, Inversion, First Principles — see the `elicitation` skill). Output: `docs/planning/forge/FORGE-<slug>-<date>.md` — tested thesis, strongest objections, surviving kernel (problem / for whom / central bet), verdict continue / pivot / drop. The kernel feeds Phase 2 (or the level 0-1 tech-spec directly). Skip silently if the user declines.
```

Et à la fin de la ligne du STOP CHECKPOINT 1, après `**STOP CHECKPOINT 1** — Level validated.` ajouter sur la même ligne : ` At this and every later checkpoint, `[E] apply an elicitation lens` is available before validating (see the `elicitation` skill).`

- [ ] **Step 2: Accroche rodin**

LIRE `.claude/skills/rodin/SKILL.md`. Dans sa section Boundaries (ou équivalente), ajouter une ligne :
```markdown
- Pour un ré-examen méthodique sous UNE lentille nommée (Pre-mortem, Inversion, First Principles…), utiliser le skill `elicitation` (/elicit) — rodin argumente contre la position ; la lentille la relit sous une seule question.
```

- [ ] **Step 3: Accroche idea-brainstorm**

LIRE `.claude/skills/idea-brainstorm/SKILL.md`, localiser l'étape de synthèse finale, y ajouter une ligne proposant : appliquer une lentille d'elicitation (`/elicit`) sur le top 5 avant de clore — typiquement Pre-mortem ou Second-Order Effects.

- [ ] **Step 4: Vérifier + commit**

```bash
grep -q "Pressure-test the idea first" .claude/skills/discovery-workflow/SKILL.md && \
grep -q "docs/planning/forge/FORGE-" .claude/skills/discovery-workflow/SKILL.md && \
grep -q "elicitation" .claude/skills/rodin/SKILL.md && \
grep -qi "elicit" .claude/skills/idea-brainstorm/SKILL.md && echo OK
git add .claude/skills/discovery-workflow/SKILL.md .claude/skills/rodin/SKILL.md .claude/skills/idea-brainstorm/SKILL.md
git commit -m "feat(discovery): [P] pressure-test option + elicitation hooks in rodin and idea-brainstorm

Refs: docs/planning/specs/2026-07-06-brainstorm-v6-design.md §4

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Nettoyage FULL/LIGHT de pm-prd, pm-stories, ux-designer

**Files:**
- Modify: `.claude/skills/pm-prd/SKILL.md`, `.claude/skills/pm-stories/SKILL.md`, `.claude/skills/ux-designer/SKILL.md`

LIRE chaque fichier ; remplacer le vocabulaire de mode FULL/LIGHT par la logique de niveaux v6 ou un vocabulaire neutre, SANS refondre les skills :
- `pm-prd` : le menu de choix `[F]/[L]` et les sections « Mode FULL »/« Mode LIGHT » deviennent « PRD complet (niveaux 2-4) » / « PRD synthétique (niveaux 0-1) » — mêmes contenus, nouveaux noms ; la description frontmatter suit.
- `pm-stories` : les références FULL/LIGHT (frontmatter + corps) deviennent des références aux niveaux (« niveau 2+ » / « niveau 0-1 »).
- `ux-designer` : idem sur ses mentions de mode.
- (multi-mind déjà traité en Task 3.)

- [ ] **Step 1: Appliquer les substitutions dans les 3 fichiers**
- [ ] **Step 2: Vérifier + commit**

```bash
! git grep -qiE "mode full|mode light|full mode|light mode|\[F\]/\[L\]" -- .claude/skills/pm-prd .claude/skills/pm-stories .claude/skills/ux-designer .claude/skills/multi-mind && \
grep -qi "niveau" .claude/skills/pm-prd/SKILL.md && echo OK
git add .claude/skills/pm-prd/SKILL.md .claude/skills/pm-stories/SKILL.md .claude/skills/ux-designer/SKILL.md
git commit -m "refactor(skills): align pm-prd, pm-stories, ux-designer on v6 levels vocabulary

Refs: docs/planning/specs/2026-07-06-brainstorm-v6-design.md §5

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Smoke test de sortie (spec §6)

**Files:** aucun fichier repo — scratch dans le scratchpad.

- [ ] **Step 1: `/elicit` en conditions réelles.** Créer un mini-PRD scratch volontairement optimiste (2-3 features, zéro risque mentionné). Suivre `elicitation/SKILL.md` à la lettre avec la lentille `premortem` : vérifier que les findings restent sous la seule lentille, pointent des sections précises, proposent des révisions sans réécrire, et donnent un verdict. Puis un second passage sans lentille : le menu doit s'afficher avec 2-3 suggestions adaptées.
- [ ] **Step 2: Anti-consensus structurel.** Vérification textuelle (pas d'appel API) : dans multi-mind, dérouler mentalement un débat convergent — le texte du skill doit rendre IMPOSSIBLE la déclaration de consensus sans objection Contrarian traitée ; vérifier que `--room anti-consensus` est documenté avec retour au workflow appelant.
- [ ] **Step 3: Forge dans discovery.** Suivre la Phase 1 de `discovery-workflow` sur une idée scratch : l'option [P] doit être proposée, produire un forge-report conforme (thèse/objections/kernel/verdict) dans le scratch, et le kernel doit nourrir la phase suivante.
- [ ] **Step 4: Sweep repo-wide.** `git grep -inE "mode full|mode light|full mode|light mode"` sans scoping — tout hit opératoire hors docs/planning, CHANGELOG.md, docs/ralph-logs est un finding.
- [ ] **Step 5: Rapport** : attendu vs observé par étape, divergences citées, nettoyage scratch.

---

## Self-Review (faite à la rédaction)

1. **Spec coverage** : §2 elicitation → Tasks 1-2 ; §3 anti-consensus → Task 3 ; §4 forge + accroches → Task 4 ; §5 nettoyages → Tasks 3 (multi-mind) + 5 ; §6 test de sortie → Task 6. Hors scope respecté : /pr-review, docs racine.
2. **Placeholders** : contenu intégral pour CSV, skill, 2 lanceurs ; édits guidés avec contenu exact pour discovery ; Tasks 3-5 en mode « lire d'abord, adapter au format » avec le fond imposé (les fichiers cibles ont des formats internes que le plan ne fige pas — le reviewer vérifie le fond).
3. **Cohérence** : lens_ids du CSV = ceux listés dans `/elicit` (12) ; chemins CSV identiques partout (`.claude/knowledge/brainstorming/elicitation-methods.csv`) ; le Contrarian référence le même CSV ; forge path `docs/planning/forge/` unique.
