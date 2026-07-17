---
epic: EPIC-002
title: Bounded task-first retrieval
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 37
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/37
priority: P0
stories: [STORY-005, STORY-006, STORY-007, STORY-008, STORY-009]
depends_on: [EPIC-001]
---

# EPIC-002 — Retrieval borné depuis la tâche

## Valeur utilisateur

Une tâche obtient d'abord la mémoire du projet, s'arrête dès que le contexte est
suffisant et ne consomme un fallback ou un dépassement qu'avec une raison
explicable et autorisée.

## Scope

- adapter QMD lexical et privé par défaut ;
- sufficiency gate déterministe ;
- cascade projet puis transverse ;
- assemblage par sections et budgets ;
- comportement dégradé et alignement du workflow `llm-wiki`.

## Stories

| Story | Titre | Priorité | Estimation | Dépendances |
|---|---|---|---|---|
| STORY-005 | Interroger QMD depuis la tâche | P0 | M | STORY-002, STORY-004 |
| STORY-006 | Décider la suffisance et le fallback | P0 | L | STORY-005 |
| STORY-007 | Assembler un contexte sous budget | P0 | L | STORY-006 |
| STORY-008 | Continuer proprement sans QMD | P0 | M | STORY-007 |
| STORY-009 | Aligner `llm-wiki` sur task-first | P0 | S | STORY-007, STORY-008 |

## Critère de sortie de l'epic

Les modes `minimal`, `project` et `historical` produisent un contexte borné ou
un non-succès explicite ; aucun workflow installé ne demande encore de lire
`wiki/index.md` complet avant de connaître la tâche.
