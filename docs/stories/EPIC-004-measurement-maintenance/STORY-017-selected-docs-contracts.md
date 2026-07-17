---
epic: EPIC-004
story_id: STORY-017
title: Rechercher des docs et contrats sélectionnés séparément
priority: P1
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 57
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/57
dependencies: [STORY-004, STORY-005]
prd_requirements: [FR-005, FR-032, NFR-SEC-007]
architecture_decisions: [ADR-011]
---

# STORY-017 — Rechercher des docs et contrats sélectionnés séparément

## User Story

**En tant qu'** agent qui travaille sur un produit,
**je veux** rechercher ADR, PRD, OpenAPI et schémas courants séparément du wiki,
**afin de** utiliser les contrats actuels sans transformer le code entier en mémoire durable.

## Contexte

Le profil est une collection QMD distincte, régénérable et déclarée par allowlist.
Le repo reste la source de vérité et les extensions de code applicatif sont
refusées par défaut.

## Critères d'acceptation

- [ ] **AC1** — Given un profil `repository-contracts`, When `memory doctor` le vérifie, Then collection, includes, excludes et racine repo sont validées séparément du vault.
- [ ] **AC2** — Given un fichier ADR, Markdown, OpenAPI, schéma SQL ou JSON allowlisté, When le profil est indexé, Then il peut apparaître avec trust `current_contract`.
- [ ] **AC3** — Given `.env`, secret, credential, log, build output ou code applicatif hors allowlist, When le profil est validé, Then le fichier est refusé même si un glob large le couvre.
- [ ] **AC4** — Given un conflit entre contrat repo et mémoire durable, When les deux sont récupérés, Then le contrat courant prend priorité et STORY-013 s'applique.
- [ ] **AC5** — Given un projet qui n'active pas ce profil, When le retrieval s'exécute, Then aucun scan ou index technique n'est créé.

## Tâches techniques

- [ ] Étendre le schéma manifest avec sources typées et trust levels.
- [ ] Implémenter validation allowlist/denylist incompressible.
- [ ] Ajouter route de collection contrat distincte.
- [ ] Étendre doctor, receipts et conflits au nouveau trust level.
- [ ] Tester secrets, globs, symlinks et opt-in modulaire.

## Notes

- Graphify et l'index complet du code restent hors scope.

## Definition of Done

- [ ] Denylist de sécurité non contournable par manifest.
- [ ] Collection distincte et désactivée par défaut.
- [ ] Hiérarchie de confiance visible.
- [ ] Aucun contenu copié dans Obsidian.
