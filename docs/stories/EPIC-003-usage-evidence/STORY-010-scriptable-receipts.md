---
epic: EPIC-003
story_id: STORY-010
title: Produire des reçus initiaux et finaux scriptables
priority: P0
estimation: M
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 50
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/50
dependencies: [STORY-007]
prd_requirements: [FR-014, FR-015, FR-016, NFR-AX-001, NFR-AX-002, NFR-AX-003, NFR-AX-004, NFR-MNT-002]
architecture_decisions: [ADR-009]
---

# STORY-010 — Produire des reçus initiaux et finaux scriptables

## User Story

**En tant qu'** utilisateur qui délègue une tâche à un agent,
**je veux** voir la route prévue puis le contexte réellement chargé,
**afin de** comprendre le coût et les limites de la mémoire sans lire des logs techniques.

## Contexte

Les renderers humain et JSON consomment le même objet métier. stdout porte la
donnée, stderr uniquement la progression et les diagnostics.

## Critères d'acceptation

- [ ] **AC1** — Given un démarrage de récupération, When la route est connue, Then le reçu initial affiche projet, mode, catégorie, route et budget sans inclure la requête.
- [ ] **AC2** — Given un contexte suffisant, When la commande termine, Then le reçu final sépare `retrieved`, `read`, tokens estimés, durée, fraîcheur et fallback.
- [ ] **AC3** — Given un résultat insuffisant, dégradé ou bloqué, When il est rendu, Then aucun libellé de succès ne masque cet état.
- [ ] **AC4** — Given `--json`, When la sortie est consommée, Then `schema_version`, status, event id, data, warnings et errors suivent un ordre et un type stables.
- [ ] **AC5** — Given `NO_COLOR=1` ou non-TTY, When le rendu humain est utilisé, Then toute l'information fonctionnelle reste présente.
- [ ] **AC6** — Given un diagnostic sur stderr, When stdout est parsé comme JSON, Then aucun caractère parasite ne casse le document.

## Tâches techniques

- [ ] Créer l'objet résultat commun et les deux renderers.
- [ ] Implémenter reçus initial, retrieval et final.
- [ ] Stabiliser ordre, labels, exit codes et séparation stdout/stderr.
- [ ] Ajouter snapshots contractuels humain/JSON.
- [ ] Tester TTY, non-TTY, NO_COLOR et erreurs.

## Notes

- Les attestations ne sont pas encore produites dans cette story, seulement leur emplacement final.

## Definition of Done

- [ ] Fixtures expected outputs ajoutées.
- [ ] Parité fonctionnelle humain/JSON prouvée.
- [ ] Aucun contenu de requête rendu par défaut.
- [ ] États de non-succès non ambigus.
