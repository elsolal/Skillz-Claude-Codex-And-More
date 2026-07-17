---
epic: EPIC-002
story_id: STORY-006
title: Décider la suffisance et le fallback autorisé
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 46
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/46
dependencies: [STORY-005]
prd_requirements: [FR-008, FR-009, FR-010, NFR-SEC-008]
architecture_decisions: [ADR-008]
---

# STORY-006 — Décider la suffisance et le fallback autorisé

## User Story

**En tant que** propriétaire de projet,
**je veux** que la recherche s'arrête lorsqu'elle est suffisante et n'élargisse
que selon ma politique,
**afin de** protéger à la fois les tokens, la pertinence et l'isolation du vault.

## Contexte

Le gate est une fonction pure basée sur mode, catégorie, scores, couverture,
fraîcheur et provenance. Il retourne toujours ses reason codes.

## Critères d'acceptation

- [ ] **AC1** — Given un hit projet fort et frais, When le gate évalue le mode `project`, Then il retourne `sufficient` et aucune collection transverse n'est appelée.
- [ ] **AC2** — Given des résultats sous seuil ou sans provenance requise, When le fallback est autorisé pour le rôle et la catégorie, Then il est exécuté avec un reason code déterministe.
- [ ] **AC3** — Given un collaborateur ou une politique sans fallback transverse, When le contexte projet est insuffisant, Then la route transverse est refusée sans révéler son contenu.
- [ ] **AC4** — Given un cas ambigu, When le gate ne peut pas conclure, Then il retourne les preuves et attend une décision explicite sans appel LLM caché.
- [ ] **AC5** — Given un mode `historical`, When une source/synthèse sourcée manque, Then le statut ne peut pas être `sufficient` sur un simple hit faible.
- [ ] **AC6** — Given une version de seuil dans le manifeste, When les golden tests s'exécutent, Then la version et les reason codes sont reproductibles.

## Tâches techniques

- [ ] Implémenter règles par mode et catégories de tâche.
- [ ] Modéliser statuts et reason codes stables.
- [ ] Appliquer la double condition rôle local + policy partagée.
- [ ] Ajouter `--explain` et la décision explicite sur ambiguïté.
- [ ] Tester seuils, ordre projet-first et refus d'accès.

## Notes

- Les seuils initiaux sont calibrables, jamais auto-modifiés en production.
- Une insuffisance n'est pas une erreur technique QMD.

## Definition of Done

- [ ] Table de décision entièrement testée.
- [ ] Fallback impossible sans autorisation explicite.
- [ ] Reason codes présents dans les deux rendus.
- [ ] Aucun appel LLM additionnel dans le CLI.
