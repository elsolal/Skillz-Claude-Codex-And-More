<!-- PROJECT-RULES-START -->
# Project Rules

> **Cette section est préservée lors des updates.** Ajoutez vos règles projet ici.

<!-- PROJECT-RULES-END -->

<!-- D-EPCT-START -->

# D-EPCT+R v5.1 — Instructions de travail

## Quel workflow utiliser ?

```
Utilisateur dit...                    → Workflow
─────────────────────────────────────────────────
"j'ai une idée / on pourrait..."      → /discovery (ou /auto-discovery)
"implémente l'issue #XX"              → /dev #XX (ou /auto-dev #XX)
"fix ce bug / ce truc est cassé"      → /quick-fix "desc"
"refactorise ce fichier"              → /refactor <file>
"review cette PR"                     → /pr-review #123
"review mon plan/PRD"                 → /plan-review <doc>
"ship cette branche"                  → /ship [branch]
"teste cette app"                     → /qa [url]
"retro de la session"                 → /retro [--since 7d]
"génère la doc"                       → /docs [type]
"crée un nouveau projet"              → /init [template]
"importe ce design Figma"             → /figma-to-code <url>
"design ça dans Figma"                → skill figma-designer
"documente le design system"          → /ds-doc
"crée/audite le design system"        → skill figma-design-system
"le composant est différent en prod"  → skill figma-design-code-sync
"quel style frontend / anti-slop"     → skill taste-router (puis taste-skill / soft-skill / etc.)
```

### Discovery (planning — orchestrateur)

```
ORCHESTRATEUR garde tout le contexte → Brainstorm → [UX] → PRD → [UI] → Architecture → Stories → GitHub (subagent)
```

Mode FULL (gros scope) : toutes les phases. Mode LIGHT (petit scope) : PRD → Stories → GitHub.
Le mode est auto-détecté. UX/UI sont optionnels et auto-triggered si pertinent.
Seule la publication GitHub est dispatchée en subagent (travail mécanique).

### Dev (développement multi-agent)

```
EXPLORE (subagent) → PLAN (orchestrateur) → IMPLEMENT (2 subagents //) → REVIEW (3 subagents //) → SHIP
```

L'orchestrateur principal garde tout le contexte et planifie. Les phases Code+Tests et Review ×3 sont dispatchées en **subagents parallèles** via `SendMessage`.

### Mode RALPH (autonome)

Préfixer avec `auto-` : `/auto-loop`, `/auto-discovery`, `/auto-dev`.
Options : `--max N`, `--timeout Xh`, `--promise "TEXT"`
Logger chaque itération dans `docs/ralph-logs/`.

---

## Commandes

```bash
# Planning
/discovery                  # Planning complet (validation à chaque étape)
/auto-discovery "idée"      # Planning autonome

# Développement
/dev [issue]                # Implémentation multi-agent guidée
/auto-dev #123              # Implémentation multi-agent autonome
/quick-fix "desc"           # Fix rapide sans workflow
/refactor <file>            # Refactoring ciblé

# Ship & QA
/ship [branch]              # Ship: merge → tests → review → changelog → PR
/qa [url]                   # QA systématique: health score, screenshots, rapport
/plan-review <doc>          # Review CEO/Founder: challenge prémisses, 3 modes
/retro [--since 7d]         # Rétrospective: sessions, streaks, tendances

# Utilitaires
/status                     # État du projet
/pr-review #123             # Review PR (3 agents parallèles)
/docs [type]                # Documentation (readme|api|guide|all)
/changelog [version]        # CHANGELOG.md
/metrics                    # Dashboard métriques
/init [template]            # Scaffolding (next|express|api|cli|lib)

# Design System & Figma
/ds-doc [--figma url]       # Documente le DS dans CLAUDE.md (scan + Figma links)
/figma-setup [url]          # Configure Code Connect
/figma-to-code <url>        # Figma → Code
# Skills auto-triggered :
# figma-designer            # Claude crée des designs dans Figma
# figma-design-system       # Gestion DS (tokens, audit, code→Figma)
# figma-design-code-sync    # Sync bidirectionnelle composants

# Frontend taste (anti-slop, premium UI) :
# taste-router              # Choisit le bon taste-skill + dials selon le brief
# taste-skill               # Default all-rounder premium frontend
# soft-skill                # Calm, expensive, smooth motion
# minimalist-skill          # Notion/Linear éditorial
# brutalist-skill           # Swiss type, raw, mechanical (BETA)
# gpt-tasteskill            # Variante stricte pour GPT/Codex
# images-taste-skill        # Image-first workflow (génère→analyse→code)
# redesign-skill            # Audit + upgrade UI existante
# output-skill              # Anti-flemme, force complétion
# stitch-skill              # Workflow Google Stitch (DESIGN.md)

# Sécurité
/supabase-security <url>    # Audit Supabase

# RALPH
/auto-loop "prompt"         # Boucle autonome générique
/auto-dev #123              # Dev autonome (alias RALPH)
/cancel-ralph               # Arrêter RALPH
/resume-ralph [session-id]  # Reprendre une session
```

---

## Règles non-négociables

### Toujours

- Explorer le codebase AVANT de planifier (subagent Explore)
- Planifier AVANT de coder (sauf fix trivial) — l'orchestrateur principal planifie directement
- Valider le plan avec l'utilisateur en mode manuel
- Utiliser TaskCreate si 2+ étapes d'implémentation
- Lint + types OK à chaque étape de code
- 3 passes de review : Correctness → Readability → Performance

### Jamais

- Commit/push directement sur main — toujours branche + PR
- Committer sans tests qui passent
- Merger sans les 3 passes de review
- Enchaîner les skills sans validation en mode manuel
- Coder sans avoir compris l'existant

---

## Conventions

### Commits

```
type(scope): description courte

Refs: #XX
```

Types : `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

### Branches

```
feature/[issue-number]-description-courte
fix/[issue-number]-description-courte
```

### PRs

- Lier à l'issue : `Closes #XX`
- Description claire + screenshots si UI

### Output docs

| Type | Emplacement |
|------|-------------|
| Planning (brainstorms, PRD, archi, UX, UI) | `docs/planning/` |
| Stories | `docs/stories/EPIC-{num}-{slug}/` |
| Logs RALPH | `docs/ralph-logs/` |

---

## Principes

- **KISS / DRY / YAGNI** — simplicité, pas d'over-engineering
- **Tests** : risk-based, P0-P3, déterministes, ATDD quand possible
- **Préférer la simplicité** à la complexité
<!-- D-EPCT-END -->
