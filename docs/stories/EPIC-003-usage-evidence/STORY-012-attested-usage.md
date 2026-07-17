---
epic: EPIC-003
story_id: STORY-012
title: Attester usage, citations et impact
priority: P0
estimation: M
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 52
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/52
dependencies: [STORY-011]
prd_requirements: [FR-017, FR-018, FR-022]
architecture_decisions: [ADR-009]
---

# STORY-012 — Attester usage, citations et impact

## User Story

**En tant qu'** utilisateur qui veut comprendre l'influence de la mémoire,
**je veux** que l'agent déclare séparément les pages utilisées et citées,
**afin de** ne pas confondre une page trouvée avec une décision réellement influencée.

## Contexte

`memory finish` ajoute un événement `usage_attested` lié au contexte parent ; il
ne modifie jamais la ligne mesurée d'origine.

## Critères d'acceptation

- [ ] **AC1** — Given un événement contexte valide, When `memory finish --used ... --cited ...` est exécuté, Then une attestation immuable est ajoutée avec le parent correct.
- [ ] **AC2** — Given un docid absent de `retrieved`, When il est déclaré `used` ou `cited`, Then l'attestation est refusée et nomme le docid invalide.
- [ ] **AC3** — Given une citation, When elle est acceptée, Then son docid appartient aussi à `used` ou une justification structurée indique `citation_only`.
- [ ] **AC4** — Given aucun impact observé, When la session est finalisée, Then `impact_codes: []` est accepté sans être présenté comme une réussite produit.
- [ ] **AC5** — Given le reçu final, When il est rendu, Then les champs CLI sont libellés `Measured` et ceux de l'agent `Attested`.

## Tâches techniques

- [ ] Implémenter commande `finish` et lookup du parent.
- [ ] Définir taxonomie d'impact versionnée.
- [ ] Valider relations retrieved/read/used/cited.
- [ ] Ajouter rendu final consolidé sans mutation JSONL.
- [ ] Tester doublons, parent absent et attestation vide.

## Notes

- L'agent reste une source déclarative ; le rapport ne transforme pas cette attestation en mesure technique.

## Definition of Done

- [ ] Relations d'état couvertes par tests.
- [ ] Mesure et attestation visuellement distinctes.
- [ ] Append-only préservé.
- [ ] Taxonomie d'impact documentée.
