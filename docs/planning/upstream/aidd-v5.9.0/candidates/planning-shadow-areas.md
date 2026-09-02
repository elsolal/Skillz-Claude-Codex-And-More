---
title: "Adoption candidate — détection des angles morts"
decision: ADAPT-P1
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
local_target: "plan-review and rodin"
implementation_status: planned
---

# Détection des angles morts de planification

## Source

- [`03-shadow-areas/SKILL.md`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-refine/skills/03-shadow-areas/SKILL.md)
- [taxonomie](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-refine/skills/03-shadow-areas/references/categories.md)
- [rubrique de sévérité](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-refine/skills/03-shadow-areas/references/severity-rubric.md)

## À conserver

- analyse read-only d'un artefact ;
- chaque gap possède catégorie, sévérité, preuve et question directe ;
- diff closed/still-open/new entre deux passages.

## À réécrire pour Skillz

- devenir une lentille de `plan-review`/`rodin`, pas un workflow concurrent ;
- utiliser les risques D-EPCT P0-P3 et le lifecycle documentaire ;
- citer les sections exactes du plan ou de la spec.

## À rejeter

- modification automatique de la source ;
- taxonomie verrouillée sans validation sur les artefacts Skillz.

## Acceptation

- zéro finding sans source ;
- identifiants stables entre deux scans ;
- un rapport clean n'approuve jamais automatiquement une spec.
