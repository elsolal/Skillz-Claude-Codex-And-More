---
epic: EPIC-001
story_id: STORY-003
title: Configurer la projection locale et les pointeurs
priority: P0
estimation: L
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 43
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/43
dependencies: [STORY-002]
prd_requirements: [FR-003, NFR-SEC-003, NFR-SEC-004]
architecture_decisions: [ADR-004]
---

# STORY-003 — Configurer la projection locale et les pointeurs

## User Story

**En tant que** collaborateur qui vient de cloner un projet,
**je veux** associer les stores logiques aux vaults présents sur ma machine,
**afin de** rendre la mémoire utilisable sans committer mes chemins personnels.

## Contexte

`memory configure` produit `.agents/memory.local.json` et les deux pointeurs
Markdown actuels. Le module Python devient la source de vérité ; le script shell
historique reste un wrapper de compatibilité.

## Critères d'acceptation

- [ ] **AC1** — Given un manifeste valide et un vault accessible, When `memory configure --store project=<path>` est exécuté, Then la projection locale et les deux pointeurs sont créés avec les valeurs résolues.
- [ ] **AC2** — Given un repo Git, When les fichiers locaux sont créés, Then ils sont ajoutés à `.git/info/exclude` et `git status` ne les propose pas au commit.
- [ ] **AC3** — Given une projection déjà valide, When la commande est relancée avec les mêmes valeurs, Then aucun changement sémantique n'est produit.
- [ ] **AC4** — Given un pointeur utilisateur divergent, When la commande détecte un contenu non géré, Then elle refuse l'écrasement sans `--replace-managed`.
- [ ] **AC5** — Given une racine qui ne contient pas les pages déclarées, When la configuration est tentée, Then le fichier peut être préparé mais le statut est `degraded` avec les pages manquantes.

## Tâches techniques

- [ ] Implémenter lecture/écriture atomique de la projection locale.
- [ ] Générer les pointeurs depuis un seul modèle de données.
- [ ] Porter la logique `.git/info/exclude` dans `projection.py`.
- [ ] Adapter le script existant en wrapper compatible.
- [ ] Tester worktree, repo simple, idempotence et refus d'écrasement.

## Notes

- La projection locale ne doit jamais devenir une preuve d'autorisation distante.
- Les sorties par défaut masquent les chemins absolus ; `--explain-local-paths` les autorise localement.

## Definition of Done

- [ ] Configuration testée sur repo normal et worktree.
- [ ] Aucun fichier machine-specific suivi par Git.
- [ ] Permissions locales restrictives quand supportées.
- [ ] Migration du script documentée.
