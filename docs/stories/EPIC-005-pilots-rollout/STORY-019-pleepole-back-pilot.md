---
epic: EPIC-005
story_id: STORY-019
title: Activer le pilote Pleepole-back
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 59
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/59
dependencies: [STORY-015]
prd_requirements: [FR-001, FR-008, FR-028, FR-029, FR-030]
architecture_decisions: [ADR-004, ADR-011]
---

# STORY-019 — Activer le pilote Pleepole-back

## User Story

**En tant que** collaborateur Pleepole autorisé,
**je veux** récupérer la mémoire équipe avant toute mémoire transverse personnelle,
**afin de** travailler sur le backend avec des décisions produit et techniques pertinentes sans fuite cross-vault.

## Contexte

Le store projet est `pleepole-wiki`. Elsolal est un fallback owner-only limité
aux catégories déclarées. Les gates existants de Pleepole-back restent la source
de vérité pour la validation du repo.

## Critères d'acceptation

- [ ] **AC1** — Given un clone Pleepole-back et son vault équipe, When il est configuré, Then `memory doctor` valide le store projet et n'exige aucun accès Elsolal pour un collaborateur.
- [ ] **AC2** — Given un rôle collaborateur, When le contexte projet est insuffisant, Then le fallback Elsolal reste refusé sans exposition de résultat ou chemin personnel.
- [ ] **AC3** — Given un rôle owner et une catégorie autorisée, When le fallback devient nécessaire, Then Pleepole est toujours interrogé en premier et la raison est journalisée.
- [ ] **AC4** — Given huit golden questions et deux holdouts, When ils sont validés, Then ils couvrent architecture, sécurité, données, produit et opérations avec pages/sources attendues.
- [ ] **AC5** — Given une contradiction avec le backend courant, When elle est détectée, Then le repo prend priorité et une dette mémoire est produite sans modifier le vault.

## Tâches techniques

- [ ] Ajouter/faire reviewer le manifeste portable dans Pleepole-back.
- [ ] Préparer golden, rubrique et holdout Pleepole nettoyés.
- [ ] Configurer les rôles et tester l'isolation Elsolal.
- [ ] Exécuter doctor, baseline et golden contre `pleepole-wiki`.
- [ ] Vérifier les commandes de validation existantes du repo pilote.

## Notes

- Cette story implique un changement coordonné dans un autre repo et une revue par son owner.

## Definition of Done

- [ ] Activation collaborateur sans Elsolal prouvée.
- [ ] Fallback owner-only testé.
- [ ] 10 cas valides dont 2 holdouts.
- [ ] Aucune donnée cross-vault dans les artefacts partagés.
