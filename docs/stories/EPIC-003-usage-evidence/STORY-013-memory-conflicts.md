---
epic: EPIC-003
story_id: STORY-013
title: Signaler les conflits et préparer une dette mémoire
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 53
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/53
dependencies: [STORY-012]
prd_requirements: [FR-019, FR-020, FR-021, FR-027]
architecture_decisions: [ADR-011]
---

# STORY-013 — Signaler les conflits et préparer une dette mémoire

## User Story

**En tant qu'** utilisateur confronté à une mémoire périmée,
**je veux** continuer avec la preuve actuelle du repo tout en préparant une correction reviewable,
**afin de** ne pas bloquer le travail ni laisser la contradiction invisible.

## Contexte

Le repo et les contrats exécutables ont priorité opérationnelle. Les conflits à
risque produit, architecture, sécurité ou données exigent un arbitrage humain
avant toute modification du sens partagé.

## Critères d'acceptation

- [ ] **AC1** — Given une contradiction entre une page et une preuve courante du repo, When elle est déclarée, Then la precedence `repository` et les deux références relatives apparaissent dans le reçu.
- [ ] **AC2** — Given un conflit `high` sur produit, architecture, sécurité ou données, When la session est finalisée, Then exit 21 et `requires_human: true` sont retournés.
- [ ] **AC3** — Given un conflit faible sans effet sur la tâche, When l'agent continue, Then une dette peut être enregistrée sans bloquer le contexte courant.
- [ ] **AC4** — Given une demande de préparation, When le CLI génère un brouillon, Then il n'édite aucune page partagée et n'inclut aucun transcript ou secret.
- [ ] **AC5** — Given une dette ouverte, When elle est revue, Then l'utilisateur peut choisir `fix`, `ignore --reason` ou `snooze --until`.

## Tâches techniques

- [ ] Modéliser risques, precedence et références de preuve.
- [ ] Étendre `finish` avec l'événement de conflit/dette.
- [ ] Ajouter sortie interactive et JSON non interactive.
- [ ] Préparer un brouillon local metadata-only sans auto-write wiki.
- [ ] Tester catégories bloquantes et actions de résolution.

## Notes

- Le CLI ne juge pas la vérité sémantique ; il applique la hiérarchie de sources validée.

## Definition of Done

- [ ] Matrice de risques testée.
- [ ] Aucune modification automatique du vault partagé.
- [ ] Exit 21 réservé aux arbitrages réels.
- [ ] Trois actions de maintenance persistables.
