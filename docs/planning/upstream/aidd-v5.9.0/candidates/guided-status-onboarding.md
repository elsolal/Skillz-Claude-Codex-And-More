---
title: "Adoption candidate — onboarding guidé par l'état"
decision: ADAPT-P1
source_sha: "3082c8ff7f862df814f15f6e669a2005b50d3459"
local_target: ".claude/skills/status-workflow/"
implementation_status: planned
---

# Onboarding guidé par l'état

## Source

- [`00-onboard/SKILL.md`](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/00-onboard/SKILL.md)
- [zones d'état](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/00-onboard/references/state/zones.md)
- [ordre de prochaine action](https://github.com/ai-driven-dev/framework/blob/3082c8ff7f862df814f15f6e669a2005b50d3459/plugins/aidd-context/skills/00-onboard/references/order/ranking.md)

## À conserver

- séparation read-only `scan → assess → present` ;
- état fondé sur des signaux disque/VCS frais ;
- une prochaine action justifiée, jamais une liste inventée ;
- distinction état manquant, drift et étape bloquée.

## À réécrire pour Skillz

- intégrer la vue dans `/status`, sans nouveau skill d'onboarding ;
- utiliser les phases D-EPCT+R, le gate courant et les capabilities provider ;
- proposer la prochaine action sans l'exécuter automatiquement.

## À rejeter

- le chemin autonome SDLC ;
- les menus AIDD et son branding ;
- tout ledger caché qui remplacerait les preuves du repo.

## Acceptation

- même snapshot = même état proposé ;
- une preuve stale n'est jamais affichée comme prête ;
- l'action suggérée cite le fichier, SHA ou rapport qui la justifie.
