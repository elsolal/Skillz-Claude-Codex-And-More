---
title: "Adoption candidate — routeur des artefacts de contexte"
decision: ADAPT-P0
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
local_target: "tooling/upstream/ and core/catalog.yaml"
implementation_status: planned
---

# Routeur des artefacts de contexte

## Source

- [`03-context-generate/SKILL.md`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/03-context-generate/SKILL.md)

## À conserver

- routeur sans logique de génération ;
- une destination spécialisée par famille d'artefact ;
- type ambigu = clarification, jamais choix silencieux.

## À réécrire pour Skillz

- router `skill`, `rule/instruction`, `agent`, `command`, `hook`, `MCP` et `plugin` ;
- résoudre la cible via `core/catalog.yaml` et le `ProviderBuildContract` ;
- renvoyer un plan structurel avant toute écriture.

## À rejeter

- l'invocation de générateurs absents sans capability check ;
- une logique de génération dupliquée dans le routeur.

## Acceptation

- chaque type du catalog possède exactement une route ;
- un type unsupported produit un fallback explicite ;
- le routeur ne contient aucun chemin runtime codé en dur.
