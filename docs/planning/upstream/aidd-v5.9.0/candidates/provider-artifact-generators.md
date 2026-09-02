---
title: "Adoption candidate — générateurs d'artefacts provider"
decision: ADAPT-P0
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
local_target: "providers/ and tooling/build/"
implementation_status: planned
---

# Générateurs d'artefacts provider

## Sources

- [`05-rule-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/05-rule-generate/SKILL.md)
- [`06-agent-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/06-agent-generate/SKILL.md)
- [`07-command-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/07-command-generate/SKILL.md)
- [`08-hook-generate`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/08-hook-generate/SKILL.md)

## À conserver

- une source canonique, rendue selon le runtime ;
- tables explicites de paths, formats et capacités ;
- capture → transform → validate ;
- skip explicite pour une capacité absente.

## À réécrire pour Skillz

- un `ArtifactContract` commun plutôt que quatre moteurs ;
- transforms pures dans `providers/<runtime>` ;
- build report `emitted/transformed/unsupported/skipped/failed` ;
- validation contre le runtime épinglé et sa documentation officielle.

## À rejeter

- les mappings upstream non certifiés, particulièrement hooks/agents Codex ;
- toute écriture directe dans `~/.claude`, `~/.codex` ou un autre home pendant le build ;
- l'affirmation qu'un fichier généré prouve la découverte native.

## Acceptation

- même entrée = mêmes hashes ;
- chaque capacité non supportée a une raison et un fallback ;
- les golden tests couvrent ajouts, transforms et suppressions.
