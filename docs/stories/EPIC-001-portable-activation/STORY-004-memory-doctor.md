---
epic: EPIC-001
story_id: STORY-004
title: Diagnostiquer l'activation avec memory doctor
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 44
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/44
dependencies: [STORY-002, STORY-003]
prd_requirements: [FR-004, NFR-PERF-002, NFR-REL-005, NFR-AX-001, NFR-AX-005]
architecture_decisions: [ADR-005]
---

# STORY-004 — Diagnostiquer l'activation avec `memory doctor`

## User Story

**En tant qu'** utilisateur qui reprend un projet,
**je veux** connaître rapidement l'état réel de sa mémoire et la prochaine action,
**afin de** ne pas découvrir une configuration cassée au milieu d'une tâche.

## Contexte

Le diagnostic nominal reste local et non mutatif. Les vérifications réseau ou
réparations sont toujours explicites.

## Critères d'acceptation

- [ ] **AC1** — Given manifeste, projection, pages et collection valides, When `memory doctor` est exécuté, Then le statut `ready` et une golden question de démarrage sont affichés.
- [ ] **AC2** — Given QMD absent mais des pages d'entrée valides, When le diagnostic s'exécute, Then le statut est `degraded`, les modes encore utilisables sont nommés et l'action d'installation est copiable.
- [ ] **AC3** — Given un manifeste invalide, un accès refusé ou une page essentielle absente, When le diagnostic s'exécute, Then une cause prioritaire `blocked` et un exit code distinct sont retournés.
- [ ] **AC4** — Given l'exécution nominale, When les checks terminent, Then aucun `git fetch`, `qmd update`, `qmd embed`, téléchargement ou écriture n'a été déclenché.
- [ ] **AC5** — Given `--json`, `NO_COLOR=1` ou un stdout non-TTY, When le diagnostic est rendu, Then aucune information fonctionnelle ne dépend de la couleur ou d'une invite.
- [ ] **AC6** — Given les fixtures pilotes locales, When les checks sans réseau sont mesurés, Then le p95 reste sous 2 secondes.

## Tâches techniques

- [ ] Implémenter checks manifest, projection, Git ignore, pages, QMD et fraîcheur locale.
- [ ] Définir les statuts et priorités de causes.
- [ ] Isoler le parsing de `qmd status` derrière l'adapter 0.9.x.
- [ ] Ajouter `--network`, `--fix` limité et `--explain`.
- [ ] Tester rendu, exit codes, performance et absence d'effets de bord.

## Notes

- `doctor --fix` peut corriger la projection gérée, jamais le sens d'une page wiki.
- Un index ancien est un avertissement avant d'être un blocage catégoriel.

## Definition of Done

- [ ] Matrice ready/degraded/blocked couverte.
- [ ] Budget de performance vérifié sur les deux fixtures pilotes.
- [ ] Actions correctives exactes et non ambiguës.
- [ ] Documentation d'onboarding mise à jour.
