---
epic: EPIC-005
story_id: STORY-018
title: Activer le pilote Skillz-Claude
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 58
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/58
dependencies: [STORY-015]
prd_requirements: [FR-001, FR-028, FR-029, FR-030]
architecture_decisions: [ADR-001, ADR-006]
---

# STORY-018 — Activer le pilote Skillz-Claude

## User Story

**En tant qu'** Aymeric,
**je veux** éprouver `memory` sur le repo qui distribue mes workflows agentiques,
**afin de** valider la portabilité multi-runtime et les questions transverses sur un cas réel.

## Contexte

Le pilote utilise `elsolal-wiki` comme store projet sans fallback supplémentaire.
Il doit préserver les fichiers utilisateur `.codex/hooks*` et tout WIP hors scope.

## Critères d'acceptation

- [ ] **AC1** — Given un clone Skillz-Claude, When le manifeste versionné et la projection locale sont configurés, Then `memory doctor` retourne ready ou un degraded explicitement accepté.
- [ ] **AC2** — Given huit golden questions visibles et deux holdouts locaux nettoyés, When ils sont validés, Then ils couvrent installation, D-EPCT, llm-wiki, QMD et mémoire projet sans contenir de secret.
- [ ] **AC3** — Given la baseline index-first, When le premier run apparié est exécuté, Then contexte, pages attendues, sources et fallback sont calculables.
- [ ] **AC4** — Given les runtimes installés, When un smoke test Claude/Codex-compatible est exécuté, Then le même manifest et le même schéma JSON sont consommés.
- [ ] **AC5** — Given les changements pilote, When `git status` est inspecté, Then aucun hook utilisateur, pointeur local ou holdout n'est ajouté au commit.

## Tâches techniques

- [ ] Ajouter le manifeste Skillz-Claude et les fichiers golden/rubric partagés.
- [ ] Préparer la projection et le holdout locaux sans les committer.
- [ ] Exécuter doctor, baseline, golden et smoke multi-runtime.
- [ ] Documenter les limites spécifiques au store Elsolal.
- [ ] Vérifier la liste exacte des fichiers partageables.

## Notes

- Le pilote ne constitue pas encore le verdict de rollout.

## Definition of Done

- [ ] Activation reproductible sur clone propre.
- [ ] 10 cas valides dont 2 holdouts.
- [ ] Baseline et premier run enregistrés.
- [ ] Aucun WIP utilisateur touché.
