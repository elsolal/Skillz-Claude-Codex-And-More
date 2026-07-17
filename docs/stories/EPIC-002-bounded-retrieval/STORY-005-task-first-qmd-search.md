---
epic: EPIC-002
story_id: STORY-005
title: Interroger QMD projet depuis la tâche
priority: P0
estimation: M
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 45
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/45
dependencies: [STORY-002, STORY-004]
prd_requirements: [FR-006, FR-007, NFR-PERF-003, NFR-REL-002, NFR-SEC-002, NFR-SEC-006]
architecture_decisions: [ADR-005, ADR-006, ADR-007]
---

# STORY-005 — Interroger QMD projet depuis la tâche

## User Story

**En tant qu'** agent qui démarre une tâche projet,
**je veux** rechercher directement les pages pertinentes dans la collection projet,
**afin de** ne pas précharger un index général avant de connaître mon besoin.

## Contexte

La route nominale appelle `qmd search --json` avec un tableau d'arguments. La
requête peut être fournie par stdin et n'est jamais persistée par `memory`.

## Critères d'acceptation

- [ ] **AC1** — Given une tâche et une collection projet valide, When `memory context` est lancé, Then la première commande de retrieval cible cette collection avec `qmd search`.
- [ ] **AC2** — Given une requête fournie par stdin, When la commande termine, Then aucun événement, reçu ou fichier temporaire ne contient le texte de la requête.
- [ ] **AC3** — Given des résultats JSON QMD 0.9.x, When ils sont parsés, Then docid, collection, chemin relatif, titre, score et ligne de snippet sont normalisés.
- [ ] **AC4** — Given résultat vide, timeout ou JSON invalide, When QMD répond, Then trois statuts distincts sont retournés et aucun n'est présenté comme un succès.
- [ ] **AC5** — Given une valeur hostile issue du manifeste, When QMD est invoqué, Then aucune interpolation shell n'est exécutée.
- [ ] **AC6** — Given une collection chaude sur les pilotes, When la recherche projet s'exécute, Then le p95 cible reste inférieur à 5 secondes.

## Tâches techniques

- [ ] Implémenter `qmd_adapter.py` et le DTO `RetrievalHit`.
- [ ] Ajouter limites de processus, timeout et taille de sortie.
- [ ] Supporter argument de requête et `--query-stdin`.
- [ ] Créer un faux binaire QMD pour les tests d'intégration.
- [ ] Ajouter fixtures QMD 0.9.x et test de non-persistance.

## Notes

- `vsearch/query` restent hors chemin nominal en V1.
- Le texte de requête peut être visible transitoirement dans le processus QMD si l'argument direct est utilisé ; stdin est la voie recommandée.

## Definition of Done

- [ ] États empty/timeout/invalid couverts.
- [ ] Aucun `shell=True` ni chaîne de commande construite.
- [ ] Test de fuite de requête vert.
- [ ] Performance pilote mesurable.
