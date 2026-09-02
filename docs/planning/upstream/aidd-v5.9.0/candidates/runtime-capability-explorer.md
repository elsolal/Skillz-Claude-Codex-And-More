---
title: "Adoption candidate — exploration des capacités runtime"
decision: ADAPT-P0
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
local_target: "tooling/doctor/ and providers/*/capabilities.yaml"
implementation_status: planned
---

# Exploration des capacités runtime

## Source

- [`11-explore/SKILL.md`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/11-explore/SKILL.md)
- [AI mapping](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/11-explore/references/ai-mapping.md)

## À conserver

- détecter les outils avant de scanner leurs surfaces ;
- séparer tooling, contexte et codebase ;
- lister seulement ce qui est présent ;
- mapper sans exécuter ni prescrire.

## À réécrire pour Skillz

- alimenter `skillz doctor` et les `capabilities.yaml` ;
- enregistrer version du binaire, chemins, discovery et certification C0-C3 ;
- vérifier les chemins candidats contre les docs officielles et les smoke tests locaux.

## À rejeter

- tables de paths considérées comme vérité permanente ;
- déduction d'un runtime à partir du seul `AGENTS.md` ;
- statut supporté sans preuve de découverte.

## Acceptation

- runtime absent = `not-installed`, jamais erreur ou PASS ;
- version driftée = avertissement explicite ;
- scan read-only avec rapport JSON reproductible.
