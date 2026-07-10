<!-- PROJECT-MEMORY-START -->
## Local Project Memory

Before non-trivial work in this project, read the local memory pointer if it exists:

```text
.claude/project-memory.md
```

This file is the local pointer to durable project memory: related wiki page, long-term vault, QMD collection, and session-capture guidance. Read it first, then inspect the current codebase; the codebase remains the immediate source of truth.

At the end of useful sessions, capture durable decisions, conventions, solved problems, validation commands, and next steps with `/wiki-capture-session <project>`, then ingest the generated source with `/wiki-ingest raw/session-notes/<filename>.md`.

Do not store secrets, credentials, full logs, stack traces, or raw transcripts in memory.
<!-- PROJECT-MEMORY-END -->

<!-- PROJECT-RULES-START -->
# Project Rules

> **Cette section est préservée lors des updates.** Ajoutez vos règles projet ici.

<!-- PROJECT-RULES-END -->

<!-- D-EPCT-START -->

# D-EPCT+R v6 — Instructions de travail

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
"challenge ce raisonnement / plan"    → /rodin <texte|doc|url> (ou skill rodin)
"ship cette branche"                  → /ship [branch]
"teste cette app"                     → /qa [url]
"analyse ce site / récupère infos"    → skill web-navigator
"audite ce design / cette UI / DS"    → /design-audit <url|path|figma> [--quick|--full|--ship-gate]
"audit design complet squad Lyse"     → /design-audit-squad <url|path|figma> [--step-by-step|--all-at-once]
"audite le SEO / GEO d'un site"       → /seo-geo-audit <url|domaine> [--quick|--full|--geo-only]
"audit SEO/GEO complet squad"         → /seo-geo-squad <url|domaine> [--step-by-step|--all-at-once]
"retro de la session"                 → /retro [--since 7d]
"génère la doc"                       → /docs [type]
"crée un nouveau projet"              → /init [template]
"importe ce design Figma"             → /figma-to-code <url>
"design ça dans Figma"                → skill figma-designer
"documente le design system"          → /ds-doc
"crée/audite le design system"        → skill figma-design-system
"le composant est différent en prod"  → skill figma-design-code-sync
"quel style frontend / anti-slop"     → skill taste-router (puis taste-skill / soft-skill / etc.)
"audite cette UI / trouve le slop"    → skill taste-critic
"audite l'accessibilité"              → skill a11y-enforcer
"écris la copy de cette landing"      → skill landing-copy
"améliore les empty states / errors"  → skill product-microcopy
"design une UI de chat / copilot"     → skill ai-native-ui
```

### Discovery (planning en niveaux)

```
ORCHESTRATEUR garde tout le contexte → Niveau 0-1 : tech-spec directe → Niveau 2-4 : Brainstorm → [UX] → PRD → [UI] → Architecture → Stories → GitHub (subagent)
```

Niveaux 0-4 auto-détectés (même grille que `/dev`). Niveau 0-1 : tech-spec directe, pas de brainstorm ni de PRD complet. Niveau 2-4 : chaîne complète, UX/UI optionnels et auto-triggered si pertinent. Sortie obligatoire : spec consolidée et approuvée dans `docs/planning/specs/` — mandat obligatoire pour `/auto-dev` et pour `/dev` niveau 4.
Seule la publication GitHub est dispatchée en subagent (travail mécanique).

### Dev (workflow adaptatif niveaux 0-4)

```
PROBE → EXPLORE → PLAN ⛔ → RED (conditionnel) → IMPLEMENT → GATE (boucle quality-gate) → HANDOFF
```

L'orchestrateur principal garde tout le contexte. La rigueur s'adapte au niveau détecté (0 = fix trivial sans plan ni gate file, 4 = epic avec spec approuvée obligatoire). Un seul stop humain : le plan (Phase 2) ; niveaux 3-4 ajoutent la lecture des « décisions prises en ton nom » avant ship. La qualité vient de la boucle `quality-gate` (PASS/CONCERNS/FAIL), qui produit un gate file, pas d'une relecture humaine du diff.

### Mode RALPH (autonome)

Préfixer avec `auto-` : `/auto-loop`, `/auto-discovery`, `/auto-dev`.
Options : `--max N`, `--timeout Xh`, `--promise "TEXT"`
Logger chaque itération dans `docs/ralph-logs/`.

---

## Commandes

```bash
# Planning
/discovery                  # Planning niveaux 0-4 (validation à chaque étape)
/auto-discovery "idée"      # Planning autonome

# Développement
/dev [issue]                # Workflow adaptatif niveaux 0-4, stop unique au plan
/auto-dev #123              # Workflow adaptatif autonome (RALPH), gate obligatoire
/quick-fix "desc"           # Circuit court niveau 0 du moteur dev-workflow, escalade auto
/refactor <file>            # Refactoring ciblé

# Ship & QA
/ship [branch]              # Ship: merge → preuves manifeste → gate file (PASS/waiver) → changelog → PR
/qa [url]                   # QA systématique: health score, screenshots, rapport
/design-audit <target>      # Audit UI/DS: tokens, composants, a11y, taste, Figma/code, IA
/design-audit-squad <target> # Orchestration complète UI/DS: 12 agents Lyse Design Squad
/seo-geo-audit <target>     # Audit SEO/GEO: technique, contenu, SERP, autorité, visibilité IA
/seo-geo-squad <target>     # Orchestration complète SEO/GEO: 11 agents Roso SEO Squad
/plan-review <doc>          # Review CEO/Founder: challenge prémisses, 3 modes
/rodin <texte|doc|url>      # Challenge socratique anti-complaisance
/retro [--since 7d]         # Rétrospective: sessions, streaks, tendances

# Utilitaires
/status                     # État du projet
/pr-review #123             # Review PR (3 agents core + gates UI/SEO si besoin)
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

# Design audit & enforcement (gates de qualité) :
# design-audit              # Gate transversal UI/DS/agent-surface, références Lyse optionnelles, P0/P1-P3
# taste-critic              # Miroir des taste-skills : détecte le slop (P0-P3) — /pr-review pass 5
# a11y-enforcer             # WCAG 2.2 AA — /pr-review pass 6, gate /ship si Grade D/F
# landing-copy              # Copy landing premium (H1 mesurable, anti-corporate)
# product-microcopy         # Empty states, errors, tooltips, confirmations
# ai-native-ui              # Patterns AI-UI invariants (states, tool calls, citations, composer)

# SEO/GEO & visibility :
# seo-geo-audit             # Audit SEO/GEO ponctuel ou squad complète 11 agents, preuves Confirmé/Déduit/Non vérifié, roadmap 7/30/90

# QA runtime agentique :
# web-navigator             # Navigation/analyse web, extraction sourcée, preuves runtime
# playwright-cli            # Runtime recommandé: npm install -g @playwright/cli@latest && playwright-cli install --skills

# Moteur qualité (invoqués par dev-workflow/ship-workflow) :
# project-probe             # Phase 0 : sonde le projet → .agents/verification.yaml (lint/types/tests/build)
# quality-gate              # Boucle bornée → gate file docs/quality/GATE-*.yaml (PASS/CONCERNS/FAIL/WAIVED)
# thermo-nuclear-code-quality-review # Derniere lentille quality-gate : maintenabilite stricte, abstractions, fichiers geants, spaghetti

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
- Boucle quality-gate jusqu'à verdict (gate file PASS/CONCERNS/FAIL) avant de proposer /ship

### Jamais

- Commit/push directement sur main — toujours branche + PR
- Committer sans tests qui passent
- Merger sans gate file PASS (ou waiver explicite sur CONCERNS)
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
