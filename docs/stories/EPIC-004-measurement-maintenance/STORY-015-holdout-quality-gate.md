---
epic: EPIC-004
story_id: STORY-015
title: Protéger la qualité avec holdout et rubrique
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 55
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/55
dependencies: [STORY-014]
prd_requirements: [FR-029, FR-030, FR-031]
architecture_decisions: [ADR-008]
---

# STORY-015 — Protéger la qualité avec holdout et rubrique

## User Story

**En tant qu'** utilisateur qui refuse une optimisation aveugle des tokens,
**je veux** conserver des cas hors du workflow et importer une note qualité séparée,
**afin de** bloquer un rollout qui économise du contexte en dégradant les réponses.

## Contexte

Deux cas locaux par projet constituent le holdout. La qualité est évaluée hors
du CLI de retrieval avec une rubrique versionnée, puis importée comme mesure
distincte et explicitement sourcée.

## Critères d'acceptation

- [ ] **AC1** — Given un holdout local valide, When `memory test --holdout` est exécuté, Then les cas participent aux agrégats sans être copiés dans un rapport partagé.
- [ ] **AC2** — Given une note produite avec la rubrique versionnée, When `record-quality` l'importe, Then run ID, rubric version, score et reviewer type sont conservés sans réponse brute.
- [ ] **AC3** — Given aucune note qualité importée, When le gate composite est demandé, Then son statut est `incomplete`, jamais `pass`.
- [ ] **AC4** — Given une dégradation qualité supérieure à 5 %, When le gate est calculé, Then le rollout échoue même si la réduction de contexte dépasse 50 %.
- [ ] **AC5** — Given moins de 20 % de holdout ou des cas identiques aux visibles, When le set est validé, Then la configuration est refusée.

## Tâches techniques

- [ ] Charger un holdout local explicitement ignoré par Git.
- [ ] Définir et valider la rubrique qualité v1.
- [ ] Implémenter import de scores nettoyés et provenance du reviewer.
- [ ] Calculer états pass/fail/incomplete du gate composite.
- [ ] Tester overfitting simple, données manquantes et seuil de 5 %.

## Notes

- Le CLI ne génère ni ne note lui-même la réponse LLM.

## Definition of Done

- [ ] 20 % de holdout vérifiable par projet.
- [ ] Qualité impossible à substituer par le retrieval score.
- [ ] Gate incomplet si une dimension manque.
- [ ] Aucune donnée brute de réponse partagée.
