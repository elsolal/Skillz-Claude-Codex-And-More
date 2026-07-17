---
epic: EPIC-003
title: Observable usage evidence
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 38
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/38
priority: P0
stories: [STORY-010, STORY-011, STORY-012, STORY-013]
depends_on: [EPIC-002]
---

# EPIC-003 — Preuves d'usage et confidentialité

## Valeur utilisateur

Après chaque récupération, l'utilisateur sait ce que le CLI a trouvé et lu,
ce que l'agent déclare avoir utilisé ou cité, combien de contexte a été émis et
si une contradiction exige une réparation de la mémoire.

## Scope

- reçus humain/JSON ;
- événements locaux append-only et rétention ;
- protocole d'attestation ;
- conflits mémoire ↔ repo et dette reviewable.

## Stories

| Story | Titre | Priorité | Estimation | Dépendances |
|---|---|---|---|---|
| STORY-010 | Produire des reçus scriptables | P0 | M | STORY-007 |
| STORY-011 | Journaliser sans contenu utilisateur | P0 | L | STORY-010 |
| STORY-012 | Attester usage, citations et impact | P0 | M | STORY-011 |
| STORY-013 | Signaler les conflits et préparer la dette | P0 | L | STORY-012 |

## Critère de sortie de l'epic

Une session complète produit un événement mesuré, une attestation liée et un
reçu final vérifiable, sans prompt, réponse, secret ni chemin absolu persisté.
