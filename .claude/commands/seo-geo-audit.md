---
description: Route SEO/GEO V3.1: audit express/complet/page, technique, contenu, visibilité IA, autorité/local, Delta, suivi ou implémentation supervisée. Usage: /seo-geo-audit <cible> [--quick|--full|--geo-only|--technical|--content|--ship-gate]
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - WebSearch
---

# /seo-geo-audit

Charger entièrement `.claude/skills/seo-geo-audit/SKILL.md`, puis router
`$ARGUMENTS` vers le plus petit parcours SEO/GEO V3 qui répond à la demande.

## Contrat

1. Pour un audit, une QA, une review ou `--ship-gate`, rester read-only : aucune
   modification du site, du code, des comptes ou des systèmes externes.
2. Lire les règles communes et la méthode V3 indiquées par le skill ; ne jamais
   charger l'ancien corpus 11 agents.
3. En `--full`, charger le Master Orchestrator et uniquement les cartes des
   spécialistes routés. Ne jamais lancer les 21 rôles mécaniquement.
4. Préserver les statuts `observed`, `proxy`, `client_reported`, `inferred`,
   `not_measured` et `unknown`, avec date, couverture et confiance.
5. Publier F/V/O/E/M séparément et relier chaque finding important à ses preuves.
6. Une mission persistante, un connecteur, une installation ou une écriture
   externe exige une demande et une approbation explicites.

## Exemples

```text
/seo-geo-audit https://example.com --quick
/seo-geo-audit https://example.com/service --ship-gate
/seo-geo-audit example.com --full
/seo-geo-audit "marque + marché FR" --geo-only
/seo-geo-audit "re-audit du projet client X" --delta
```

## Execution

```text
$ARGUMENTS
```
