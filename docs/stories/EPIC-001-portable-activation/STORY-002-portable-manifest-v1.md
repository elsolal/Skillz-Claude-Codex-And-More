---
epic: EPIC-001
story_id: STORY-002
title: Valider un manifeste mémoire portable v1
priority: P0
estimation: M
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 42
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/42
dependencies: [STORY-001]
prd_requirements: [FR-001, FR-002, FR-005, NFR-PERF-001, NFR-REL-004, NFR-SEC-005]
architecture_decisions: [ADR-003, ADR-004]
---

# STORY-002 — Valider un manifeste mémoire portable v1

## User Story

**En tant que** propriétaire d'un mini-cerveau partagé,
**je veux** versionner un contrat mémoire sans chemin machine,
**afin que** chaque clone puisse reconstruire la même politique de retrieval.

## Contexte

Le manifeste `.agents/memory.yaml` utilise en V1 le sous-ensemble YAML 1.2
compatible JSON et est validé sans dépendance PyYAML obligatoire.

## Critères d'acceptation

- [ ] **AC1** — Given un repo sous un sous-répertoire, When une commande `memory` démarre, Then le manifeste le plus proche est découvert sans sortir de la racine Git.
- [ ] **AC2** — Given un manifeste v1 valide, When il est chargé, Then projet, stores, fallbacks, budgets, policies et golden paths sont exposés sous un contrat typé.
- [ ] **AC3** — Given un chemin absolu, un ID invalide ou une clé interdite, When le manifeste est validé, Then la commande retourne exit 30 avec le champ fautif et une correction copiable.
- [ ] **AC4** — Given du YAML libre non JSON-compatible, When le fichier est lu, Then l'erreur explique la contrainte V1 sans interprétation partielle.
- [ ] **AC5** — Given un `schema_version` inconnu, When le manifeste est chargé, Then aucune route n'est exécutée et la sortie JSON conserve son propre schéma public.
- [ ] **AC6** — Given un manifeste pilote valide, When parsing et décision de route sont mesurés hors processus QMD, Then leur p95 reste inférieur à 300 ms.

## Tâches techniques

- [ ] Créer les dataclasses/enums de contrat v1.
- [ ] Implémenter découverte, parsing JSON strict et validation sémantique.
- [ ] Ajouter les règles de noms, chemins relatifs, budgets et allowlists.
- [ ] Ajouter un benchmark déterministe du parsing et de la décision de route.
- [ ] Créer fixtures valides/invalides et tests de compatibilité.
- [ ] Ajouter un exemple minimal Skillz-Claude dans la documentation.

## Notes

- Le parseur ne doit accepter aucun tag, include ou interpolation YAML.
- Une évolution compatible ajoute un champ optionnel ; une rupture change la version.

## Definition of Done

- [ ] Fixtures manifest v1 versionnées.
- [ ] Tests de traversal et d'entrées hostiles verts.
- [ ] Messages humain et JSON cohérents.
- [ ] Schéma documenté pour les collaborateurs.
