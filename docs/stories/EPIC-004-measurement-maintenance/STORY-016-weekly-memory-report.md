---
epic: EPIC-004
story_id: STORY-016
title: Générer une revue hebdomadaire actionnable
priority: P1
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 56
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/56
dependencies: [STORY-013, STORY-015]
prd_requirements: [FR-025, FR-026, FR-027, NFR-SEC-009, NFR-MNT-004]
architecture_decisions: [ADR-009]
---

# STORY-016 — Générer une revue hebdomadaire actionnable

## User Story

**En tant qu'** Aymeric,
**je veux** recevoir seulement les problèmes mémoire qui ont affecté du travail réel,
**afin de** maintenir les mini-cerveaux en moins de dix minutes par semaine.

## Contexte

Le rapport agrège uniquement le projet courant et classe les arbitrages par
risque puis impact observé, jamais par ancienneté seule.

## Critères d'acceptation

- [ ] **AC1** — Given une semaine d'événements, When `memory report --weekly` est exécuté, Then efficacité, qualité, fallback, fraîcheur et funnel d'usage sont agrégés par projet.
- [ ] **AC2** — Given plus de sept dettes, When le rapport est généré, Then sept arbitrages maximum apparaissent dans le chemin nominal et le reste est résumé en annexe.
- [ ] **AC3** — Given une dette, When l'utilisateur choisit `fix`, `ignore --reason` ou `snooze --until`, Then l'action est enregistrée sans modifier automatiquement la page wiki.
- [ ] **AC4** — Given des événements contenant un autre project ID, When le rapport courant est généré, Then ils sont exclus avant agrégation.
- [ ] **AC5** — Given une exportation Markdown, When le scanner metadata-only s'exécute, Then aucun contenu interdit ou chemin absolu ne peut être écrit.
- [ ] **AC6** — Given les données pilotes, When Aymeric suit le chemin nominal, Then la revue peut être terminée en dix minutes ou moins.

## Tâches techniques

- [ ] Implémenter agrégations et ranking des arbitrages.
- [ ] Ajouter actions fix/ignore/snooze append-only.
- [ ] Générer rendu terminal et Markdown partageable.
- [ ] Appliquer isolation projet et scanner d'export.
- [ ] Tester cap de sept et scénario chronométré pilote.

## Notes

- Le rapport peut mentionner docids et chemins relatifs utiles à la maintenance.

## Definition of Done

- [ ] Cap de sept garanti.
- [ ] Isolation cross-vault testée.
- [ ] Export metadata-only validé.
- [ ] Revue pilote chronométrée <= 10 minutes.
