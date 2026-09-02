# Inventaire exhaustif des skills AIDD v5.9.0

Source épinglée : [`ai-driven-dev/framework@3082c8ff`](https://github.com/ai-driven-dev/framework/tree/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins).

La colonne « décision » décrit l'adoption dans Skillz-Claude, pas la qualité absolue du skill
upstream. `COVERED` signifie que le besoin est déjà servi localement ; `REJECT` signifie que le
comportement contredit une décision v6.1.

## `aidd-context` — 13 skills

| Skill upstream | Décision | Destination ou raison |
|---|---|---|
| [`00-onboard`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/00-onboard/SKILL.md) | `ADAPT-P1` | Détection d'état et prochaine action dans `status-workflow`, sans exécution automatique. |
| [`01-bootstrap`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/01-bootstrap/SKILL.md) | `COVERED` | `discovery-workflow` + `architect` couvrent le cadrage brownfield/greenfield. |
| [`02-project-memory`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/02-project-memory/SKILL.md) | `ADAPT-P0` | Check-before-write, zones gérées et préservation des edits dans `llm-wiki`. |
| [`03-context-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/03-context-generate/SKILL.md) | `ADAPT-P0` | Routeur léger artefact → contrat/générateur provider. |
| [`04-skill-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/04-skill-generate/SKILL.md) | `ADAPT-P0` | Renforcer `skillz-writing-skills` avec router/actions/references/assets et tests observables. |
| [`05-rule-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/05-rule-generate/SKILL.md) | `ADAPT-P0` | Unifier dans `ProviderBuildContract`, pas créer un moteur isolé. |
| [`06-agent-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/06-agent-generate/SKILL.md) | `ADAPT-P0` | Transforms agent par runtime, avec découverte native obligatoire. |
| [`07-command-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/07-command-generate/SKILL.md) | `ADAPT-P0` | Aliases et fallbacks explicites dans le contrat provider. |
| [`08-hook-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/08-hook-generate/SKILL.md) | `ADAPT-P0` | Contrat de hooks fail-closed, trust-gated, sans reprendre les mappings non vérifiés. |
| [`09-mermaid`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/09-mermaid/SKILL.md) | `COVERED` | Les skills architecture/design peuvent déjà produire les diagrammes nécessaires. |
| [`10-learn`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/10-learn/SKILL.md) | `ADAPT-P1` | Sélection des apprentissages dans `llm-wiki` et lentille rework dans `/retro`. |
| [`11-explore`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/11-explore/SKILL.md) | `ADAPT-P0` | Inventaire runtime pour `doctor`, sans recommandations automatiques. |
| [`12-cook`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/12-cook/SKILL.md) | `WATCH` | Les recettes ne répondent pas à un gap v6.1 démontré. |

## `aidd-dev` — 11 skills

| Skill upstream | Décision | Destination ou raison |
|---|---|---|
| [`01-plan`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/01-plan/SKILL.md) | `COVERED` | Phase PLAN de `dev-workflow`. |
| [`02-implement`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/02-implement/SKILL.md) | `COVERED` | `code-implementer` + phase IMPLEMENT. |
| [`03-assert`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/03-assert/SKILL.md) | `COVERED` | `project-probe`, `quality-gate` et manifeste de vérification sont plus stricts. |
| [`04-audit`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/04-audit/SKILL.md) | `COVERED` | Auditeurs spécialisés + revue thermo-nucléaire. |
| [`05-review`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/05-review/SKILL.md) | `COVERED` | `code-reviewer`, `/pr-review` et quality gate. |
| [`06-test`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/06-test/SKILL.md) | `COVERED` | `test-runner`, `/qa` et `web-navigator`. |
| [`07-refactor`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/07-refactor/SKILL.md) | `COVERED` | `/refactor` et workflow manuel existant. |
| [`08-debug`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/08-debug/SKILL.md) | `COVERED` | `/quick-fix` + exploration par hypothèses. |
| [`09-for-sure`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/09-for-sure/SKILL.md) | `REJECT` | Boucle autonome équivalente au problème RALPH retiré en v6.1. |
| [`10-todo`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/10-todo/SKILL.md) | `COVERED` | `orchestrate`/`multi-mind` couvrent la décomposition quand disponible. |
| [`11-browser-qa`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-dev/skills/11-browser-qa/SKILL.md) | `WATCH` | Les vidéos de preuve sont utiles, mais hors socle provider-neutral v6.1. |

## `aidd-orchestrator` — 3 skills

| Skill upstream | Décision | Destination ou raison |
|---|---|---|
| [`00-async-dev`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-orchestrator/skills/00-async-dev/SKILL.md) | `REJECT` | Orchestration autonome, secrets et permissions hors architecture v6.1. |
| [`01-sdlc`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-orchestrator/skills/01-sdlc/SKILL.md) | `REJECT` | Ne remplace pas D-EPCT+R ni son checkpoint humain. |
| [`02-backlog`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-orchestrator/skills/02-backlog/SKILL.md) | `REJECT` | Pas de nouveau backlog/kanban parallèle. |

## `aidd-pm` — 10 skills

| Skill upstream | Décision | Destination ou raison |
|---|---|---|
| [`01-ticket-info`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/01-ticket-info/SKILL.md) | `COVERED` | `github-issue-reader`. |
| [`02-user-stories`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/02-user-stories/SKILL.md) | `COVERED` | `pm-stories`. |
| [`03-prd`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/03-prd/SKILL.md) | `COVERED` | `pm-prd`. |
| [`04-spec`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/04-spec/SKILL.md) | `COVERED` | Convention de spec approuvée D-EPCT+R. |
| [`05-spike`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/05-spike/SKILL.md) | `WATCH` | Bon format d'incertitude bornée, pas nécessaire au socle v6.1. |
| [`06-product-brief`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/06-product-brief/SKILL.md) | `COVERED` | Discovery/brainstorm/PRD couvrent le cadrage produit. |
| [`07-epic`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/07-epic/SKILL.md) | `COVERED` | `pm-stories` et conventions EPIC existantes. |
| [`08-three-amigos`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/08-three-amigos/SKILL.md) | `ADAPT-P1` | Trois lentilles sans spawn imposé, pour stories/plans complexes. |
| [`09-defect`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/09-defect/SKILL.md) | `COVERED` | Issues + `/quick-fix` couvrent le défaut et son exécution. |
| [`10-task`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-pm/skills/10-task/SKILL.md) | `COVERED` | Plans D-EPCT et outils de tâches runtime couvrent ce besoin. |

## `aidd-refine` — 4 skills

| Skill upstream | Décision | Destination ou raison |
|---|---|---|
| [`01-brainstorm`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-refine/skills/01-brainstorm/SKILL.md) | `COVERED` | `idea-brainstorm` + `discovery-workflow`. |
| [`02-challenge`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-refine/skills/02-challenge/SKILL.md) | `COVERED` | `rodin` et plan review. |
| [`03-shadow-areas`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-refine/skills/03-shadow-areas/SKILL.md) | `ADAPT-P1` | Taxonomie d'angles morts et diff de rapports pour plan review. |
| [`04-fact-check`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-refine/skills/04-fact-check/SKILL.md) | `ADAPT-P1` | Cascade mémoire → code → source primaire pour docs et source intake. |

## `aidd-ui` — 1 skill

| Skill upstream | Décision | Destination ou raison |
|---|---|---|
| [`01-hello`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-ui/skills/01-hello/SKILL.md) | `REJECT` | Smoke test d'un plugin alpha AIDD, sans valeur fonctionnelle pour Skillz. |

## `aidd-vcs` — 5 skills

| Skill upstream | Décision | Destination ou raison |
|---|---|---|
| [`00-repo-init`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-vcs/skills/00-repo-init/SKILL.md) | `COVERED` | `/init` et conventions projet. |
| [`01-commit`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-vcs/skills/01-commit/SKILL.md) | `COVERED` | `ship-workflow`. |
| [`02-pull-request`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-vcs/skills/02-pull-request/SKILL.md) | `COVERED` | `ship-workflow`. |
| [`03-release-tag`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-vcs/skills/03-release-tag/SKILL.md) | `COVERED` | Changelog/release existants ; pas de nouveau skill requis. |
| [`04-issue-create`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-vcs/skills/04-issue-create/SKILL.md) | `COVERED` | Publication GitHub déjà intégrée aux workflows de planning. |

## Résumé

| Décision | Nombre |
|---|---:|
| `ADAPT-P0` | 8 |
| `ADAPT-P1` | 5 |
| `COVERED` | 26 |
| `WATCH` | 3 |
| `REJECT` | 5 |
| **Total** | **47** |

Les 13 entrées `ADAPT` sont regroupées en dix fiches locales afin que les quatre générateurs
provider partagent une seule architecture et un seul contrat de test.
