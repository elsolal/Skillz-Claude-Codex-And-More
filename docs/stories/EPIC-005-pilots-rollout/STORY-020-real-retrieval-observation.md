---
epic: EPIC-005
story_id: STORY-020
title: Observer vingt récupérations réelles par pilote
priority: P0
estimation: M
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 60
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/60
dependencies: [STORY-018, STORY-019]
prd_requirements: [FR-022, FR-031]
architecture_decisions: [ADR-009]
---

# STORY-020 — Observer vingt récupérations réelles par pilote

## User Story

**En tant qu'** Aymeric,
**je veux** observer le système pendant de vraies tâches nettoyées,
**afin de** distinguer un bon benchmark de laboratoire d'un outil effectivement utilisé.

## Contexte

Le seuil est 20 événements `context_completed` valides par pilote. Les tâches
restent dans leurs conversations d'origine ; seuls catégorie, route, pages et
métriques autorisées sont conservés.

## Critères d'acceptation

- [ ] **AC1** — Given les deux pilotes activés, When 20 récupérations réelles valides sont atteintes sur chacun, Then le compteur affiche 40 événements éligibles sans doublon.
- [ ] **AC2** — Given une commande test, un échec de parsing ou un événement incomplet, When les usages réels sont comptés, Then il est exclu ou classé séparément avec une raison.
- [ ] **AC3** — Given un échantillon d'événements, When le scanner privacy est exécuté, Then aucun prompt, réponse, snippet, secret ou chemin absolu n'est présent.
- [ ] **AC4** — Given les attestations finales, When le funnel est calculé, Then retrieved/read/used/cited restent séparés et les absences d'attestation sont visibles.
- [ ] **AC5** — Given un fallback index complet, When il se produit, Then sa fréquence et sa reason code participent à la cible < 10 %.

## Tâches techniques

- [ ] Définir les règles d'éligibilité d'un usage réel.
- [ ] Ajouter compteur et audit de complétude par pilote.
- [ ] Exécuter le scanner privacy sur l'échantillon complet.
- [ ] Produire les agrégats intermédiaires sans publier les événements bruts.
- [ ] Documenter anomalies et décisions de calibration.

## Notes

- La story peut nécessiter plusieurs sessions réelles, mais ne doit pas être remplacée par 40 appels artificiels.

## Definition of Done

- [ ] 20 événements éligibles par pilote.
- [ ] 100 % des événements pilotes présents ou écarts expliqués.
- [ ] Audit privacy à zéro incident.
- [ ] Agrégats prêts pour le gate composite.
