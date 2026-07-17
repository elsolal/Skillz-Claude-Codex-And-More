---
epic: EPIC-004
story_id: STORY-014
title: Comparer golden retrieval et baseline index-first
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 54
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/54
dependencies: [STORY-007, STORY-011]
prd_requirements: [FR-028, FR-030, NFR-MNT-003]
architecture_decisions: [ADR-010]
---

# STORY-014 — Comparer golden retrieval et baseline `index-first`

## User Story

**En tant que** propriétaire du système mémoire,
**je veux** exécuter les mêmes questions sur la route historique et la route bornée,
**afin de** mesurer un gain de contexte apparié plutôt qu'une impression subjective.

## Contexte

Chaque projet fournit huit cas visibles avec pages/sources attendues. La baseline
et la variante utilisent le même estimateur et conservent uniquement leurs
métadonnées de run.

## Critères d'acceptation

- [ ] **AC1** — Given un fichier golden v1, When `memory test` est exécuté, Then huit cas visibles sont validés et chaque ID produit un résultat reproductible.
- [ ] **AC2** — Given un cas, When baseline et route bornée sont comparées, Then elles utilisent la même requête nettoyée, le même estimateur et les mêmes attentes.
- [ ] **AC3** — Given des pages/sources attendues, When les résultats sont évalués, Then présence sur première route, rang, fallback et contexte estimé sont calculés.
- [ ] **AC4** — Given une requête golden, When le run est persisté, Then seuls case ID, métriques et docids sont conservés dans le state dir.
- [ ] **AC5** — Given un jeu incomplet ou un schéma inconnu, When le test démarre, Then le run est refusé avant comparaison.

## Tâches techniques

- [ ] Définir schéma golden et résultat de run v1.
- [ ] Implémenter runner route bornée et adapter baseline index-first.
- [ ] Calculer retrieval hit rate, fallback rate et réduction médiane.
- [ ] Écrire fixtures déterministes et expected outputs.
- [ ] Ajouter export de résultats agrégés sans requête.

## Notes

- Cette story mesure le retrieval, pas encore la qualité finale de réponse.

## Definition of Done

- [ ] Comparaison appariée et reproductible.
- [ ] Aucune requête dans les événements de test.
- [ ] Échec clair si attentes ou baseline manquent.
- [ ] Métriques PRD calculables.
