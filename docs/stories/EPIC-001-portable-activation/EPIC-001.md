---
epic: EPIC-001
title: Portable memory activation
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 36
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/36
priority: P0
stories: [STORY-001, STORY-002, STORY-003, STORY-004]
---

# EPIC-001 — Activation mémoire portable

## Valeur utilisateur

Un utilisateur ou collaborateur qui clone un repo activé peut installer le CLI,
résoudre ses chemins locaux, générer les pointeurs attendus et savoir si la
mémoire est prête, dégradée ou bloquée sans dépendre de la machine d'Aymeric.

## Scope

- distribution provider-neutral du CLI ;
- manifeste partagé v1 ;
- projection locale et pointeurs ignorés ;
- diagnostic local et actions correctives.

## Hors scope

- retrieval de contenu complet ;
- télémétrie d'usage ;
- création ou réparation automatique d'un vault distant.

## Stories

| Story | Titre | Priorité | Estimation | Dépendances |
|---|---|---|---|---|
| STORY-001 | Installer le CLI sans collision | P0 | M | — |
| STORY-002 | Valider un manifeste portable v1 | P0 | M | STORY-001 |
| STORY-003 | Configurer la projection locale | P0 | L | STORY-002 |
| STORY-004 | Diagnostiquer l'activation mémoire | P0 | L | STORY-002, STORY-003 |

## Critère de sortie de l'epic

Sur un clone propre de chaque pilote, `memory configure` puis `memory doctor`
produisent une configuration locale non suivie par Git et un statut explicable,
sans écraser un binaire, un pointeur ou une configuration utilisateur existants.
