---
title: "Adoption candidate — apprentissage durable et retrospective"
decision: ADAPT-P1
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
local_target: ".claude/skills/llm-wiki/ and retro workflow"
implementation_status: planned
---

# Apprentissage durable et rétrospective

## Source

- [`10-learn/SKILL.md`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/10-learn/SKILL.md)
- [assessment](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/10-learn/references/assessment.md)
- [destinations](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/10-learn/references/destinations.md)

## À conserver

- source → gather → assess → write ;
- distinguer décision, convention, pitfall, workflow et finding ;
- proposer la bonne destination au lieu de tout envoyer en mémoire ;
- confirmation avant persistance.

## À réécrire pour Skillz

- intégrer aux receipts et budgets de `llm-wiki` ;
- ajouter à `/retro` délai évitable, rework, contexte manquant et automatisation utile ;
- router vers mémoire, ADR, rule ou skill sans duplication.

## À rejeter

- nouvelle memory bank ;
- capture automatique d'une conversation entière ;
- écriture dans la mémoire globale sans demande explicite.

## Acceptation

- aucun secret/log brut capturé ;
- les doublons sont détectés avant écriture ;
- l'utilisateur voit et valide les candidats durables.
