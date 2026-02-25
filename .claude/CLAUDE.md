<!-- PROJECT-RULES-START -->
# Project Rules

> **Cette section est préservée lors des updates.** Ajoutez vos règles projet ici.

```markdown
# Exemple de règles à ajouter :
# - Stack technique spécifique
# - Conventions de nommage
# - Règles métier
# - Intégrations tierces
```

<!-- PROJECT-RULES-END -->

---

# D-EPCT+R Workflow

> Skills Claude Code pour un workflow de développement structuré et professionnel.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WORKFLOW COMPLET                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PLANNING                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │   🧠     │    │   📋     │    │   🏗️     │    │   📝     │              │
│  │Brainstorm│ →  │   PRD    │ →  │  Archi   │ →  │ Stories  │ → GitHub     │
│  │ +Research│    │FULL/LIGHT│    │          │    │+Readiness│              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│        │              │                                                     │
│        ▼              ▼                                                     │
│  ┌──────────┐    ┌──────────┐   (optionnel, auto-triggered)                │
│  │   🎨     │ →  │   🖌️     │                                              │
│  │UX Design │    │UI Design │                                              │
│  │ personas │    │  tokens  │                                              │
│  │ journeys │    │components│                                              │
│  └──────────┘    └──────────┘                                              │
│                                                                             │
│  DÉVELOPPEMENT                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────┐  │
│  │   🔍     │    │   📝     │    │   💻     │    │   🧪     │    │  🔄  │  │
│  │ Explain  │ →  │  Plan    │ →  │  Code    │ →  │  Test    │ →  │Review│  │
│  │          │    │          │    │+Lint/Type│    │ATDD/Std  │    │  ×3  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  MODE MANUEL: Validation humaine (⏸️ STOP) à chaque étape                   │
│  MODE RALPH:  Autonome jusqu'à completion promise / max iter / timeout      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Commandes (16)

### Mode Manuel (avec validation)

```bash
/discovery              # Planning complet avec validation à chaque étape
/feature [issue]        # Implémentation avec validation à chaque étape
```

### Mode RALPH (autonome)

```bash
/auto-loop "prompt"     # Boucle générique sur une tâche
/auto-discovery "idée"  # Planning complet en autonome
/auto-feature #123      # Implémentation complète en autonome
/cancel-ralph           # Arrêter le mode RALPH
/resume-ralph [session-id]  # Reprendre une session RALPH interrompue
```

### Utilitaires

```bash
/status                 # État du projet (docs, issues, RALPH)
/pr-review #123         # Review une PR GitHub (3 passes)
/quick-fix "desc"       # Fix rapide sans workflow complet
/refactor <file>        # Refactoring ciblé avec review
/docs [type]            # Génère documentation (readme|api|guide|all)
/changelog [version]    # Génère CHANGELOG.md
/metrics                # Dashboard métriques projet
/init [template]        # Scaffolding projet (next|express|api|cli|lib)
/supabase-security <url> # Audit sécurité Supabase complet
/figma-setup [url]       # Configure Code Connect
/figma-to-code <url>     # Génère code depuis Figma
```

### Configuration RALPH

| Commande | Max Iter | Timeout | Completion Promise |
|----------|----------|---------|-------------------|
| `/auto-loop` | 20 | 1h | "DONE" |
| `/auto-discovery` | 30 | 1h | "DISCOVERY COMPLETE" |
| `/auto-feature` | 50 | 2h | "FEATURE COMPLETE" |

**Options :** `--max N`, `--timeout Xh`, `--promise "TEXT"`, `--no-log`, `--verbose`

---

## Skills (20)

### Phase Planning

| Skill | Rôle | Fonctionnalités clés |
|-------|------|----------------------|
| `idea-brainstorm` | Exploration créative | 61 techniques, 4 approches, anti-biais, auto-trigger UX/UI |
| `pm-prd` | Product Requirements | Mode FULL ou LIGHT, auto-détection, auto-trigger UX/UI |
| `architect` | Architecture technique | Stack, structure, data model, APIs, ADRs |
| `pm-stories` | Epics + Stories | INVEST, Given/When/Then, Readiness Check (score /15) |
| `api-designer` | Design d'API | OpenAPI 3.1, REST/GraphQL, versioning, rate limiting |
| `database-designer` | Design de BDD | ERD, migrations, indexes, Prisma/Drizzle |

### Phase Design (optionnelle, auto-triggered)

| Skill | Rôle | Fonctionnalités clés |
|-------|------|----------------------|
| `ux-designer` | Expérience utilisateur | Personas, user journeys, wireframes textuels, heuristiques Nielsen |
| `ui-designer` | Design system | Tokens (couleurs, typo, spacing), composants UI, import Figma |
| `figma-setup` | Config Code Connect | Installation, mappings .figma.tsx, publication |
| `figma-to-code` | Génération code | URL Figma → code avec composants mappés, tokens CSS |

### Phase Développement

| Skill | Rôle | Fonctionnalités clés |
|-------|------|----------------------|
| `github-issue-reader` | Lecture d'issues | Catégorisation, ambiguïtés classifiées, Given/When/Then |
| `codebase-explainer` | Analyse du code | Impact mapping, patterns, flux de données, risques |
| `implementation-planner` | Planification | Complexité S/M/L, étapes atomiques, TaskCreate si 2+ étapes |
| `code-implementer` | Implémentation | Lint/types obligatoire par étape, hook auto-lint, TaskUpdate auto |
| `test-runner` | Tests | Mode ATDD ou Standard, priorités P0-P3, hook coverage |
| `code-reviewer` | Review (3 passes) | Correctness → Readability → Performance |
| `security-auditor` | Audit sécurité | OWASP Top 10, dépendances, secrets, scoring |
| `performance-auditor` | Audit performance | Core Web Vitals, bundle size, Lighthouse |
| `supabase-security` | Audit Supabase | RLS, buckets, auth, keys exposées, CVSS |
| `multi-mind` | Débat multi-agents | 6 IA, 5 rounds itératifs, consensus/divergences |

---

## Task System

Le système **Tasks** tracke les projets complexes et coordonne le travail multi-sessions.

**Quand utiliser :** 2+ étapes d'implémentation, dépendances entre actions, travail interruptible.
**Quand NE PAS utiliser :** Action unique, fix trivial, exploration sans code.

| Outil | Usage |
|-------|-------|
| `TaskCreate` | Créer une tâche (subject, description, activeForm) |
| `TaskList` | Lister les tâches et leur statut |
| `TaskGet` | Détails d'une tâche par ID |
| `TaskUpdate` | Mettre à jour statut (pending → in_progress → completed) |

**Intégration au workflow /feature :** `implementation-planner` crée les Tasks automatiquement si 2+ étapes, `code-implementer` met à jour le statut à chaque étape.

**Multi-sessions :** `CLAUDE_CODE_TASK_LIST_ID=mon-projet claude` pour partager les Tasks entre sessions.

> `TodoWrite` est obsolète — utiliser `TaskCreate`.

---

## Plan Mode

Pour les tâches non-triviales (feature, refactoring, archi, changement multi-fichiers), Claude DOIT utiliser Plan Mode.

```
1. Explore (agent: Explore) → Recherche dans le codebase
2. EnterPlanMode → Designer la solution
3. Validation utilisateur (⏸️ STOP)
4. Exécution avec Tasks pour tracking
```

- ✅ Toujours explorer avant de planifier
- ✅ Toujours planifier avant de coder (sauf fix trivial)
- ✅ Toujours valider le plan avec l'utilisateur
- ⛔ Ne JAMAIS coder sans avoir compris l'existant

---

## Subagents

| Agent | Usage |
|-------|-------|
| `Explore` | Recherche dans le codebase, analyse de fichiers |
| `Plan` | Conception de plans d'implémentation |

| Context Mode | Usage |
|------|-------|
| `fork` | Isolation complète (skills de planification et implémentation) |
| `default` | Contexte partagé (skills de lecture simple) |

---

## Skill Chaining

Chaque skill propose automatiquement le skill suivant après validation de son output.

| Skill actuel | Propose ensuite |
|--------------|-----------------|
| `idea-brainstorm` | `/ux-designer` (si UI) ou `/pm-prd` |
| `pm-prd` | `/ui-designer` (si design) ou `/architect` |
| `architect` | `/pm-stories` |
| `pm-stories` | `/feature` ou `/auto-feature` |
| `github-issue-reader` | `/codebase-explainer` |
| `codebase-explainer` | `/implementation-planner` |
| `implementation-planner` | `/code-implementer` |
| `code-implementer` | `/test-runner` |
| `test-runner` | `/code-reviewer` |
| `code-reviewer` | Commit/PR (fin du cycle) |

### Seuils de validation output

| Skill | Seuil minimum |
|-------|--------------|
| `idea-brainstorm` | 4/5 |
| `pm-prd` | 6/7 |
| `architect` | 5/6 |
| `pm-stories` | 13/15 |
| `implementation-planner` | 5/6 |
| `code-implementer` | 4/5 |
| `test-runner` | 4/5 |
| `code-reviewer` | Toutes passes OK |

---

## Modes de scope

**FULL** (score ≥ 3 parmi : 3+ features, archi multi-composants, 3+ écrans, intégrations externes, > 1 jour) :
```
Brainstorm → [UX Design] → PRD complet → [UI Design] → Architecture → Stories → GitHub
```

**LIGHT** (feature isolée, petit scope, < 1 jour) :
```
PRD simplifié → Stories → GitHub
```

UX/UI sont auto-triggered après Brainstorm ou PRD selon des critères de score (écrans, composants, parcours). L'utilisateur peut toujours skip ou déclencher manuellement.

---

## Checkpoints obligatoires

### Planning

| Checkpoint | Skill | Validation |
|------------|-------|------------|
| Brainstorm validé | `idea-brainstorm` | Synthèse acceptée |
| *UX Design validé* | `ux-designer` | *(optionnel)* Personas et journeys approuvés |
| PRD validé | `pm-prd` | Mode choisi, scope défini |
| *UI Design validé* | `ui-designer` | *(optionnel)* Tokens et composants approuvés |
| Architecture validée | `architect` | Stack et structure approuvés |
| **Readiness Check** | `pm-stories` | Score ≥ 13/15 |

### Développement

| Checkpoint | Skill | Validation |
|------------|-------|------------|
| Code expliqué | `codebase-explainer` | Architecture comprise |
| Plan validé | `implementation-planner` | Étapes approuvées |
| Code implémenté | `code-implementer` | Lint ✅ Types ✅ |
| Tests passent | `test-runner` | 100% pass, 3 runs |
| Review OK | `code-reviewer` | 3 passes complètes |

---

## Templates disponibles

| Template | Emplacement | Usage |
|----------|-------------|-------|
| Git hooks (pre-commit, commit-msg) | `.claude/templates/git-hooks/` | `cp` vers `.git/hooks/` |
| DevContainer (Docker) | `.claude/templates/devcontainer/` | `cp` vers `.devcontainer/` |
| GitHub Issues | `.claude/templates/github/ISSUE_TEMPLATE/` | `cp` vers `.github/` |
| GitHub Actions (CI, deploy, security) | `.claude/templates/github-actions/` | `cp` vers `.github/workflows/` |
| PR Template | `.claude/templates/github/PULL_REQUEST_TEMPLATE.md` | `cp` vers `.github/` |

---

## Knowledge Base

Fichiers de référence chargés progressivement par les skills dans `.claude/knowledge/` :

| Dossier | Contenu |
|---------|---------|
| `testing/` | 32 fragments (levels, priorities, quality, fixtures, healing...) |
| `workflows/` | Templates PRD, archi, stories, UX, UI + estimation, risques |
| `brainstorming/` | 61 techniques en 10 catégories |
| `multi-mind/` | Personnalités des 6 agents, templates 5 rounds |
| `supabase-security/` | Checklist audit, matrice CVSS, patterns RLS, remédiation |
| `figma/` | Guide Code Connect, référence MCP, mapping tokens |

**Chargement :** core (auto avec le skill) → advanced (si complexe) → debugging (si problème).

---

## Principes

- **KISS / DRY / YAGNI** — simplicité, pas de répétition, pas d'over-engineering
- Tout code doit être testé
- 3 passes de review obligatoires
- **Tests** : risk-based, P0-P3, déterministes, ATDD quand possible

### Documentation

| Type | Emplacement |
|------|-------------|
| Brainstorms | `docs/planning/brainstorms/` |
| UX Design | `docs/planning/ux/` |
| PRD | `docs/planning/prd/` |
| UI Design | `docs/planning/ui/` |
| Architecture | `docs/planning/architecture/` |
| Stories | `docs/stories/EPIC-{num}-{slug}/` |
| Logs RALPH | `docs/ralph-logs/` |

---

## Conventions

### Commits

```
type(scope): description courte

Description détaillée si nécessaire

Refs: #XX
```

**Types:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

### Branches

```
feature/[issue-number]-description-courte
fix/[issue-number]-description-courte
```

### Pull Requests

- Lier à l'issue avec "Closes #XX"
- Description claire du changement
- Screenshots si UI

---

## Règles globales

### Mode Manuel

- ⛔ Ne JAMAIS enchaîner sans validation explicite
- ⛔ Ne JAMAIS skip le Readiness Check
- ✅ Attendre "ok", "continue", "validé" avant de continuer
- ✅ En cas de doute, demander clarification

### Mode RALPH

- ⛔ Ne JAMAIS ignorer les erreurs (s'auto-corriger)
- ✅ Travailler en boucle jusqu'à completion promise
- ✅ Logger chaque itération dans `docs/ralph-logs/`
- ✅ S'arrêter sur : completion promise, max iterations, ou timeout

### Tous modes

- ⛔ Ne JAMAIS commit/push directement sur main (toujours utiliser une branche dédiée + PR)
- ⛔ Ne JAMAIS committer sans tests qui passent
- ⛔ Ne JAMAIS merger sans les 3 passes de review
- ✅ Respecter les conventions du projet existant
- ✅ Préférer la simplicité à la complexité
