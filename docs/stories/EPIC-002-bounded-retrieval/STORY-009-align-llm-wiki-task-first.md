---
epic: EPIC-002
story_id: STORY-009
title: Aligner llm-wiki sur le workflow task-first
priority: P0
estimation: S
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 49
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/49
dependencies: [STORY-007, STORY-008]
prd_requirements: [FR-007, FR-010, FR-013]
architecture_decisions: [ADR-001]
---

# STORY-009 — Aligner `llm-wiki` sur le workflow task-first

## User Story

**En tant qu'** utilisateur de plusieurs agents,
**je veux** recevoir les mêmes règles de mémoire dans chaque runtime,
**afin de** ne plus alterner entre un workflow index-first coûteux et un workflow projet ciblé.

## Contexte

Le workflow canonique, les commandes wiki et les templates de pointeur doivent
désigner `memory context` comme route nominale et réserver l'index complet au
fallback observable.

## Critères d'acceptation

- [ ] **AC1** — Given le skill `llm-wiki` installé, When une requête projet est décrite, Then les instructions demandent la tâche puis la collection projet avant tout index complet.
- [ ] **AC2** — Given QMD absent, When les instructions sont suivies, Then elles utilisent uniquement les pages d'entrée bornées prévues par l'architecture.
- [ ] **AC3** — Given les loaders Claude, Codex/OpenCode et Gemini générés, When ils sont comparés, Then aucun ne réintroduit `index-first` comme étape obligatoire.
- [ ] **AC4** — Given un vault non activé par manifeste, When `/wiki-query` est utilisé, Then le workflow historique reste disponible mais sa consommation n'est pas attribuée au pilote `memory`.

## Tâches techniques

- [ ] Mettre à jour `query-workflow.md`, `SKILL.md` et README.
- [ ] Adapter les commandes/source-command skills concernées.
- [ ] Mettre à jour les templates de pointeur et la documentation cross-tool.
- [ ] Ajouter un test statique contre les instructions contradictoires.

## Notes

- La migration conserve la compatibilité des vaults non activés.

## Definition of Done

- [ ] Une seule route canonique pour les projets activés.
- [ ] Compatibilité explicite des anciens vaults.
- [ ] Install/update multi-runtime vérifié.
- [ ] Aucune instruction index-first obligatoire restante.
