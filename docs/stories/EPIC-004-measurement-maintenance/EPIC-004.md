---
epic: EPIC-004
title: Quality-protected measurement and maintenance
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 39
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/39
priority: P0
stories: [STORY-014, STORY-015, STORY-016, STORY-017]
depends_on: [EPIC-003]
---

# EPIC-004 — Mesure protégée par la qualité et maintenance

## Valeur utilisateur

Aymeric peut comparer la route historique et la route bornée, conserver des cas
non optimisés, importer une évaluation de qualité indépendante et concentrer la
maintenance hebdomadaire sur sept arbitrages réellement utiles.

## Scope

- golden retrieval et baseline appariée ;
- holdout et rubric qualité ;
- gate composite ;
- digest hebdomadaire ;
- profil séparé de docs et contrats P1.

## Stories

| Story | Titre | Priorité | Estimation | Dépendances |
|---|---|---|---|---|
| STORY-014 | Comparer golden retrieval et baseline | P0 | L | STORY-007, STORY-011 |
| STORY-015 | Protéger la qualité avec holdout et rubrique | P0 | L | STORY-014 |
| STORY-016 | Générer une revue hebdomadaire actionnable | P1 | L | STORY-013, STORY-015 |
| STORY-017 | Rechercher docs et contrats séparément | P1 | L | STORY-004, STORY-005 |

## Critère de sortie de l'epic

Le gate calcule séparément activation, retrieval, contexte, qualité, usage,
maintenance et confidentialité ; aucune économie de tokens ne suffit à elle
seule pour autoriser le rollout.
