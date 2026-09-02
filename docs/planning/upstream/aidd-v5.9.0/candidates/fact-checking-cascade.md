---
title: "Adoption candidate — cascade de vérification factuelle"
decision: ADAPT-P1
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
local_target: "tooling/upstream/ and documentation review"
implementation_status: planned
---

# Cascade de vérification factuelle

## Source

- [`04-fact-check/SKILL.md`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-refine/skills/04-fact-check/SKILL.md)
- [cascade de vérification](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-refine/skills/04-fact-check/references/verification-cascade.md)

## À conserver

- extraire les claims vérifiables ;
- cascade mémoire/docs → codebase → source primaire ;
- arrêter dès qu'une preuve suffisante résout le claim ;
- statuts verified/refuted/conflict/unverified.

## À réécrire pour Skillz

- utiliser le codebase comme vérité immédiate pour les faits projet ;
- imposer les sources officielles pour les contrats runtime ;
- alimenter les fiches d'adoption avec claim, source, date et niveau de preuve.

## À rejeter

- web comme premier réflexe pour un fait local ;
- suppression silencieuse d'un claim non vérifié ;
- persistance automatique d'une conclusion.

## Acceptation

- chaque claim du catalogue a une source ou le label `unverified` ;
- les conflits restent visibles ;
- une référence vers une branche mouvante ne peut pas certifier une adoption.
