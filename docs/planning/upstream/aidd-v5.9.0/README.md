---
title: "Catalogue d'adoption ai-driven-dev/framework v5.9.0"
status: current
created_at: 2026-09-01
source_repository: "https://github.com/ai-driven-dev/framework"
source_release: "v5.9.0"
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
license: MIT
architecture: "../../plans/2026-07-24-d-epct-v6-1-provider-neutral-hardening-plan.md"
---

# Catalogue d'adoption AIDD v5.9.0

Ce dossier transforme l'audit upstream en entrées actionnables pour D-EPCT+R v6.1. Il ne contient
pas de copie installable des skills AIDD et ne déclenche aucune récupération réseau pendant le
build ou l'installation de Skillz.

## Source épinglée

- Repository : [`ai-driven-dev/framework`](https://github.com/ai-driven-dev/framework)
- Release : [`v5.9.0`](https://github.com/ai-driven-dev/framework/releases/tag/v5.9.0)
- Commit : [`3082c8ff`](https://github.com/ai-driven-dev/framework/commit/3082c8ff7f862df814f15f6e669a2005b50d3459)
- Licence : [MIT au commit audité](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/LICENSE)
- Architecture Skillz : [plan D-EPCT+R v6.1](../../plans/2026-07-24-d-epct-v6-1-provider-neutral-hardening-plan.md)

Tout lien vers un fichier upstream pointe ce SHA. Une release future exige un nouveau catalogue ou
une révision explicitement datée ; elle ne déplace jamais silencieusement cette baseline.

## Contenu

- [Inventaire exhaustif des 47 skills](skills-inventory.md) : chaque skill a une décision et un
  équivalent local éventuel.
- [Mécanismes non-skill retenus](mechanisms.md) : plugin Codex, build contracts, drift, evals et
  lifecycle documentaire.
- [`candidates/`](candidates/) : fiches de réécriture des apports retenus.

## Statuts de décision

| Statut | Signification | Effet v6.1 |
|---|---|---|
| `ADAPT-P0` | Apport requis pour le vertical slice ou ses garde-fous. | Entre dans la spec v6.1. |
| `ADAPT-P1` | Apport utile après stabilisation du socle P0. | Fiche prête, activation différée. |
| `COVERED` | Skillz possède déjà une capacité équivalente ou supérieure. | Aucun nouveau skill ; référence ponctuelle possible. |
| `WATCH` | Idée intéressante mais non justifiée dans le périmètre v6.1. | Aucune implémentation planifiée. |
| `REJECT` | Contradictoire avec les décisions v6.1 ou trop risqué. | Ne pas importer. |

## Pipeline de récupération

```text
registry source + SHA
        │
        ▼
inventaire read-only du delta
        │
        ▼
classification des artefacts et dépendances
        │
        ▼
fiche candidat + liens + licence + preuves
        │
        ▼
décision humaine ADAPT / COVERED / WATCH / REJECT
        │
        ▼
réécriture dans core/ ou providers/
        │
        ▼
golden tests + behavioral evals + provenance locale
```

## Règles d'adoption

1. Aucun fichier upstream n'est copié directement dans `.claude/`, `core/` ou `providers/` depuis
   ce dossier.
2. Une fiche `ADAPT` définit l'intention, les invariants à conserver et ce qui doit être rejeté ;
   l'implémentation locale est réécrite dans le vocabulaire D-EPCT+R.
3. Le build de Skillz reste hermétique : aucune dépendance GitHub ou AIDD à l'exécution.
4. Toute reprise substantielle de code ou de texte doit conserver l'avis MIT requis et sa
   provenance dans le fichier concerné ou dans `THIRD_PARTY_NOTICES.md`.
5. Une source upstream ne prouve pas une capacité runtime. Les niveaux C1-C3 du plan restent
   obligatoires.
6. `REJECT` est une décision testable : l'orchestrateur autonome, les boucles de type RALPH et les
   contournements de permissions ne doivent pas réapparaître sous un autre nom.

## Fiches retenues

| Fiche | Source(s) | Priorité | Cible locale |
|---|---|---:|---|
| [Onboarding guidé par l'état](candidates/guided-status-onboarding.md) | `00-onboard` | P1 | `status-workflow` |
| [Sécurité des écritures mémoire](candidates/project-memory-write-safety.md) | `02-project-memory` | P0 | `llm-wiki` |
| [Routeur des artefacts de contexte](candidates/context-artifact-router.md) | `03-context-generate` | P0 | `tooling/upstream` + catalog |
| [Contrat d'écriture des skills](candidates/skill-authoring-contract.md) | `04-skill-generate` | P0 | `skillz-writing-skills` + `core/skills` |
| [Générateurs provider](candidates/provider-artifact-generators.md) | `05` à `08` | P0 | `providers/` + build contracts |
| [Apprentissage et rétro](candidates/learning-and-retro.md) | `10-learn` | P1 | `llm-wiki` + `/retro` |
| [Exploration des capacités runtime](candidates/runtime-capability-explorer.md) | `11-explore` | P0 | `doctor` + capability manifests |
| [Détection des angles morts](candidates/planning-shadow-areas.md) | `03-shadow-areas` | P1 | `plan-review` + `rodin` |
| [Vérification factuelle](candidates/fact-checking-cascade.md) | `04-fact-check` | P1 | source intake + docs review |
| [Lentilles Three Amigos](candidates/three-amigos-lenses.md) | `08-three-amigos` | P1 | `pm-stories` + plan review |

Ces fiches sont des entrées de spec. Elles ne sont pas des skills installables et leur statut
`ADAPT` ne vaut pas approbation d'implémentation.
