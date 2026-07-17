---
epic: EPIC-002
story_id: STORY-007
title: Assembler un contexte mémoire sous budget
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 47
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/47
dependencies: [STORY-006]
prd_requirements: [FR-010, FR-011, FR-013, FR-015, FR-016]
architecture_decisions: [ADR-010]
---

# STORY-007 — Assembler un contexte mémoire sous budget

## User Story

**En tant qu'** utilisateur d'un agent,
**je veux** que seules les sections nécessaires soient chargées sous une enveloppe visible,
**afin de** réduire le contexte inutile sans couper silencieusement une preuve importante.

## Contexte

L'assembleur résout chaque résultat dans sa racine locale, sélectionne la
section Markdown autour du hit et utilise `utf8_bytes_div_4_v1` pour comparer
baseline et nouvelle route.

## Critères d'acceptation

- [ ] **AC1** — Given des hits dédupliqués, When le contexte est assemblé, Then seules les sections émises sont comptées `read` et tous les candidats restent `retrieved`.
- [ ] **AC2** — Given un budget cible `minimal/project/historical`, When une section ferait dépasser la cible sans améliorer la couverture, Then elle n'est pas chargée.
- [ ] **AC3** — Given un dépassement du hard cap sans `risk_reason`, When l'assemblage atteint la limite, Then il s'arrête avec un statut insuffisant ou partiel explicite.
- [ ] **AC4** — Given une raison de risque autorisée, When le hard cap est dépassé, Then la raison et le coût réel apparaissent dans le reçu et l'événement.
- [ ] **AC5** — Given une URI contenant `..` ou un symlink hors racine, When le document est résolu, Then la lecture est refusée avant ouverture.
- [ ] **AC6** — Given une route suffisante avant consommation totale, When le contexte est prêt, Then le solde du budget n'est pas utilisé artificiellement.

## Tâches techniques

- [ ] Implémenter résolution sûre des URI QMD vers racines locales.
- [ ] Extraire section, frontmatter utile, lignes et provenance.
- [ ] Implémenter estimateur versionné et limites cible/hard.
- [ ] Modéliser déduplication, couverture et arrêt anticipé.
- [ ] Tester Unicode, gros fichiers, symlinks et paragraph truncation.

## Notes

- Le compteur est une estimation comparative, pas une facture provider.
- `wiki/index.md` complet ne peut entrer que comme fallback observé.

## Definition of Done

- [ ] Aucun accès hors racine possible.
- [ ] Budgets 800/2 500/6 000 et hard caps testés.
- [ ] `retrieved` et `read` séparés dans le contrat.
- [ ] Baseline et variante utilisent le même estimateur.
