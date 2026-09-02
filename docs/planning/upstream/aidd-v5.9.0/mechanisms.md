# Mécanismes AIDD non-skill retenus

Ces éléments complètent les fiches de skills. Ils sont des références d'architecture ou de test,
pas des dépendances à importer.

## P0 — Build contracts provider-neutral

Sources :

- [`ToolBuildContract`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/cli/src/domain/tools/build-contract.ts)
- [contrats par runtime](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/cli/src/application/use-cases/framework/strategies/tool-contracts.ts)
- [adaptateur Codex](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/cli/src/domain/tools/ai/codex.ts)

À retenir : une matrice symétrique par artefact, des transforms pures et des orchestrateurs qui ne
branchent pas sur chaque runtime.

À réécrire : schéma minimal compatible avec les scripts actuels de Skillz, sans importer le CLI
TypeScript ni Node `>=22.12`.

## P0 — Drift et restauration fichier par fichier

Sources :

- [`DetectPluginDriftUseCase`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/cli/src/application/use-cases/shared/detect-plugin-drift-use-case.ts)
- [`RestoreDriftEntriesUseCase`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/cli/src/application/use-cases/shared/restore-drift-entries-use-case.ts)

À retenir : comparaison par hash, décision centralisée `restore/keep/conflict`, composition plutôt
qu'une hiérarchie d'héritage.

À renforcer : ownership explicite, dry-run, backup borné et interdiction de supprimer un fichier
local non manifesté.

## P0 — Behavioral eval harness

Sources :

- [`skill-eval.mjs`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/scripts/skill-eval.mjs)
- [cas d'évaluation](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/scripts/skill-eval/cases.json)

À retenir : fixtures isolées, `filesExist`, `filesAbsent`, `filesUnchanged`, `fileContains`,
`fileMatches`, stdout, répétitions et parallélisme borné.

À rejeter : runner Claude-only et `--dangerously-skip-permissions`. Skillz doit fournir une
interface de runner multi-runtime, un sandbox par fixture et `run-result.json`.

## P0 — Plugin Codex natif

Sources :

- [PR #571](https://github.com/ai-driven-dev/framework/pull/571)
- [fixture manifest `.codex-plugin`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/cli/tests/fixtures/plugins/codex-format/sample-plugin/.codex-plugin/plugin.json)
- [fixture marketplace Codex](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/cli/tests/fixtures/plugins/codex-format/marketplace-sample/.agents/plugins/marketplace.json)

À retenir : format natif, marketplace et transformations spécifiques au runtime.

À prouver : installation, listing, chargement headless, skills, agents, hooks, MCP et résolution de
la racine du plugin. Un exit code 0 ne suffit pas.

## P1 — Lifecycle documentaire

Source : [issue #730](https://github.com/ai-driven-dev/framework/issues/730).

À retenir : `current`, `superseded`, `superseded_by`, `amended_by` et validation des liens.

À adapter : schéma léger commun aux plans, PRD, specs et architectures Skillz, sans importer un
backlog documentaire séparé.
