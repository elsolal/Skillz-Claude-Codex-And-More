---
epic: EPIC-005
title: Pilot evidence and rollout decision
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 40
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/40
priority: P0
stories: [STORY-018, STORY-019, STORY-020, STORY-021]
depends_on: [EPIC-001, EPIC-002, EPIC-003, EPIC-004]
---

# EPIC-005 — Pilotes et décision de rollout

## Valeur utilisateur

Les deux environnements représentatifs — l'outillage Skillz-Claude et le produit
Pleepole-back — prouvent ou invalident l'efficacité du système avant que la
configuration soit propagée aux autres repos.

## Scope

- activation et jeux de test des deux pilotes ;
- 20 récupérations réelles minimum par pilote ;
- gate composite et décision modulaire ;
- documentation durable du verdict.

## Stories

| Story | Titre | Priorité | Estimation | Dépendances |
|---|---|---|---|---|
| STORY-018 | Activer le pilote Skillz-Claude | P0 | L | STORY-015 |
| STORY-019 | Activer le pilote Pleepole-back | P0 | L | STORY-015 |
| STORY-020 | Observer 20 récupérations par pilote | P0 | M | STORY-018, STORY-019 |
| STORY-021 | Calculer et documenter le verdict | P0 | M | STORY-016, STORY-020 |

## Critère de sortie de l'epic

Un verdict sourcé indique pour chaque module `keep`, `calibrate`, `defer` ou
`stop`. Le rollout global reste bloqué si l'une des dimensions obligatoires du
PRD échoue ou manque.
