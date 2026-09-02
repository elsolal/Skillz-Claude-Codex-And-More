---
title: "Adoption candidate — sécurité des écritures mémoire"
decision: ADAPT-P0
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
local_target: ".claude/skills/llm-wiki/"
implementation_status: planned
---

# Sécurité des écritures mémoire

## Source

- [`02-project-memory/SKILL.md`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/02-project-memory/SKILL.md)
- [action de check](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/02-project-memory/actions/03-check.md)
- [règles mémoire](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/02-project-memory/references/memory-rules.md)
- [template AGENTS avec marqueurs](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/02-project-memory/assets/templates/AGENTS.md)

## À conserver

- check-before-write et diff présenté avant mutation ambiguë ;
- zones gérées délimitées par marqueurs ;
- préservation fichier par fichier des modifications utilisateur ;
- séparation `scan`, `check`, `write`, `sync`.

## À réécrire pour Skillz

- appliquer les garde-fous aux projections `llm-wiki` existantes ;
- valider marqueurs non appariés, fences, liens/imports et drift ;
- conserver la récupération task-first, les budgets et reçus déjà supérieurs dans Skillz.

## À rejeter

- la banque mémoire AIDD parallèle ;
- la régénération complète d'un fichier non possédé ;
- les chemins et templates spécifiques à `aidd_docs/memory`.

## Acceptation

- aucune zone hors marqueurs ne change ;
- marqueur absent ou altéré = conflit explicite ;
- dry-run et apply produisent le même plan de changements.
