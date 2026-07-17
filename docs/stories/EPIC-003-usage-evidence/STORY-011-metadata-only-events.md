---
epic: EPIC-003
story_id: STORY-011
title: Journaliser des événements metadata-only et purgeables
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 51
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/51
dependencies: [STORY-010]
prd_requirements: [FR-022, FR-023, FR-024, NFR-REL-003, NFR-SEC-001, NFR-SEC-003]
architecture_decisions: [ADR-009]
---

# STORY-011 — Journaliser des événements metadata-only et purgeables

## User Story

**En tant que** propriétaire du système mémoire,
**je veux** mesurer chaque récupération sans conserver la conversation,
**afin de** suivre la valeur réelle tout en limitant le risque de confidentialité.

## Contexte

Les événements JSONL vivent hors du repo, sont append-only et expirent après 30
jours. Un scanner de contrat refuse les champs et valeurs interdits avant append.

## Critères d'acceptation

- [ ] **AC1** — Given une récupération terminée, When l'événement est écrit, Then il contient ID, temps, projet, route, docids, chemins relatifs, scores, tokens, durée, fraîcheur et status uniquement.
- [ ] **AC2** — Given une requête, un snippet, une réponse, un chemin absolu ou une clé sensible injectée dans le payload, When le scanner s'exécute, Then l'append est refusé avec exit 50.
- [ ] **AC3** — Given un state dir neuf, When il est créé, Then les permissions utilisateur restrictives sont appliquées quand la plateforme le permet.
- [ ] **AC4** — Given deux processus concurrents, When ils ajoutent des événements, Then chaque ligne reste un JSON complet et les IDs restent uniques.
- [ ] **AC5** — Given une dernière ligne tronquée, When le journal est relu, Then les lignes précédentes sont conservées et la corruption est diagnostiquée.
- [ ] **AC6** — Given des événements plus vieux que la rétention, When la purge nominale ou forcée s'exécute, Then seuls les détails expirés du projet concerné sont supprimés.

## Tâches techniques

- [ ] Implémenter résolution XDG/state dir et permissions.
- [ ] Définir schéma événement v1 et scanner metadata-only.
- [ ] Ajouter verrou portable, append compact et `fsync`.
- [ ] Implémenter lecture tolérante de dernière ligne et purge.
- [ ] Tester concurrence, corruption, permissions et isolation projet.

## Notes

- Aucun hash de requête n'est activé en V1.
- Une panne de télémétrie est visible ; elle n'est jamais maquillée en mesure complète.

## Definition of Done

- [ ] 100 % des champs autorisés documentés.
- [ ] Corpus de valeurs interdites testé.
- [ ] Tests multiprocessus et rétention verts.
- [ ] State dir confirmé hors Git.
