---
epic: EPIC-005
story_id: STORY-021
title: Calculer et documenter le verdict de rollout
priority: P0
estimation: M
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 61
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/61
dependencies: [STORY-016, STORY-020]
prd_requirements: [FR-031, FR-032]
architecture_decisions: [ADR-011]
---

# STORY-021 — Calculer et documenter le verdict de rollout

## User Story

**En tant que** décideur du système mémoire,
**je veux** un verdict fondé sur qualité, efficacité, usage, maintenance et confidentialité,
**afin de** conserver seulement les modules qui créent de la valeur avant d'équiper d'autres repos.

## Contexte

Le verdict peut être globalement bloqué tout en conservant un sous-module utile.
Il ne déclenche aucune installation automatique sur les autres repos.

## Critères d'acceptation

- [ ] **AC1** — Given les métriques des deux pilotes, When le gate est calculé, Then chaque dimension affiche valeur, cible, preuve et pass/fail/incomplete.
- [ ] **AC2** — Given une dégradation qualité > 5 %, une réduction médiane < 50 %, moins de 40 usages, une maintenance > 10 minutes ou un incident privacy, When le verdict est rendu, Then le rollout global est bloqué.
- [ ] **AC3** — Given un module utile malgré un échec global, When la décision est documentée, Then il reçoit séparément `keep`, `calibrate`, `defer` ou `stop` avec justification.
- [ ] **AC4** — Given un verdict complet, When le rapport durable est généré, Then il contient uniquement des agrégats, références de preuve et prochaines décisions.
- [ ] **AC5** — Given un verdict `pass`, When il est approuvé humainement, Then il propose un rollout modulaire futur sans modifier automatiquement les 51 autres repos.

## Tâches techniques

- [ ] Implémenter le calcul final et la matrice des dimensions.
- [ ] Générer un rapport Markdown durable et metadata-only.
- [ ] Documenter décisions par module et calibrations restantes.
- [ ] Faire valider le verdict par l'owner avant tout nouvel epic de rollout.
- [ ] Préparer, sans exécuter, la recommandation de prochaine vague.

## Notes

- Le nombre exact de repos restant est réévalué au moment du verdict ; il n'est pas une constante produit.

## Definition of Done

- [ ] Toutes les dimensions ont une preuve ou sont explicitement incomplete.
- [ ] Aucun pass si une condition bloquante échoue.
- [ ] Rapport partageable sans données brutes.
- [ ] Décision humaine enregistrée avant suite.
