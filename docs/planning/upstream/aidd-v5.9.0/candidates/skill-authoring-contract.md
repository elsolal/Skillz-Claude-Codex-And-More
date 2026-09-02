---
title: "Adoption candidate — contrat d'écriture des skills"
decision: ADAPT-P0
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
local_target: ".claude/skills/skillz-writing-skills/ and core/skills/"
implementation_status: planned
---

# Contrat d'écriture des skills

## Source

- [`04-skill-generate/SKILL.md`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/04-skill-generate/SKILL.md)
- [skill authoring](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/04-skill-generate/references/skill-authoring.md)
- [skill tree](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/04-skill-generate/references/skill-tree.md)

## À conserver

- router court et progressive disclosure ;
- actions atomiques avec test observable ;
- références et assets chargés seulement au besoin ;
- un fait dans un seul foyer canonique.

## À réécrire pour Skillz

- vocabulaire français et D-EPCT+R ;
- compatibilité avec le catalog provider-neutral ;
- description/triggers conformes à `skillz-writing-skills` ;
- behavioral eval minimal pour les skills critiques.

## À rejeter

- copie textuelle du skill upstream ;
- anglais obligatoire ;
- génération simultanée dans plusieurs homes utilisateur.

## Acceptation

- le router ne duplique aucune action ;
- liens relatifs valides et assets sans instruction cachée ;
- déclenchement, non-déclenchement et output testés.
