---
description: Orchestration complète RosoAI SEO/GEO V3.1: 21 spécialistes routés, Evidence Vault, scoring F/V/O/E/M, QA adversariale et livrables. Usage: /seo-geo-squad <cible> [--step-by-step|--all-at-once]
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - WebSearch
---

# /seo-geo-squad

Charger entièrement `.claude/skills/seo-geo-audit/SKILL.md`, puis exécuter son
parcours `--squad` pour `$ARGUMENTS`.

## Chargement obligatoire

1. `references/roso-v3/SKILL.md` ;
2. `references/roso-v3/core/00_REGLES_COMMUNES_V3.md` ;
3. `references/roso-v3/skill/roso-seo-geo-v3/SKILL.md` ;
4. `references/roso-v3/core/01_MASTER_ORCHESTRATOR_V3.md` ;
5. `references/roso-v3/core/AGENTS_MANIFEST.json` ;
6. seulement les cartes `core/agents/` et `extensions/` sélectionnées par le
   Master Orchestrator.

Les 21 spécialistes ne sont pas un pipeline fixe. `--all-at-once` signifie
uniquement « paralléliser les branches indépendantes autorisées », jamais lancer
tous les rôles ou ignorer les gates de couverture et de QA.

## Contrat

- Définir périmètre, permissions, date de coupure et livrables avant collecte.
- Créer un projet persistant uniquement dans un chemin explicitement autorisé,
  hors du skill et du dépôt Skillz-Claude.
- Préserver `source -> evidence -> fact -> finding -> action -> outcome`.
- Garder F/V/O/E/M séparés avec couverture, confiance, fraîcheur et angles morts.
- Ne jamais modifier le site audité. Toute implémentation passe par une demande
  distincte, staging, diff, approbation et rollback.
- Une livraison PDF n'est conforme qu'après QA, inspection de toutes les pages,
  fingerprint et attestation de livraison.

## Execution

```text
$ARGUMENTS
```
