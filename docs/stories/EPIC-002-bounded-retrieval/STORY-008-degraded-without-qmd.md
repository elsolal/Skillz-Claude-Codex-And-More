---
epic: EPIC-002
story_id: STORY-008
title: Continuer proprement sans QMD
priority: P0
estimation: M
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 48
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/48
dependencies: [STORY-007]
prd_requirements: [FR-012, NFR-PERF-004, NFR-REL-001, NFR-REL-002]
architecture_decisions: [ADR-006]
---

# STORY-008 — Continuer proprement sans QMD

## User Story

**En tant que** collaborateur dont QMD n'est pas encore prêt,
**je veux** disposer d'un contexte d'entrée clairement limité,
**afin de** pouvoir avancer sans que le système prétende couvrir l'historique.

## Contexte

Les modes `minimal/project` peuvent lire un nombre borné de pages d'entrée.
`historical` reste bloqué sans moteur de recherche opérationnel.

## Critères d'acceptation

- [ ] **AC1** — Given QMD absent et des pages d'entrée valides, When le mode `minimal` est demandé, Then une seule page bornée est émise avec statut `degraded` et exit 10.
- [ ] **AC2** — Given QMD absent, When le mode `project` est demandé, Then trois pages d'entrée maximum sont sélectionnées sous budget.
- [ ] **AC3** — Given QMD absent ou inutilisable, When le mode `historical` est demandé, Then aucun succès n'est produit et exit 31 indique la dépendance requise.
- [ ] **AC4** — Given une page d'entrée absente ou hors racine, When le fallback local s'exécute, Then elle est signalée et jamais remplacée par une lecture large implicite.
- [ ] **AC5** — Given aucun modèle local, When le mode dégradé s'exécute, Then aucun téléchargement n'est déclenché.

## Tâches techniques

- [ ] Implémenter le reader borné des pages d'entrée.
- [ ] Appliquer les caps de pages et de tokens par mode.
- [ ] Produire le statut degraded et les actions correctives.
- [ ] Tester QMD manquant, non exécutable, timeout et entry pages partielles.

## Notes

- La continuité du travail ne doit jamais masquer la réduction de couverture.

## Definition of Done

- [ ] Matrice des trois modes sans QMD couverte.
- [ ] Aucun téléchargement ou recherche large implicite.
- [ ] Limites visibles dans le reçu.
- [ ] Commande de réparation documentée.
