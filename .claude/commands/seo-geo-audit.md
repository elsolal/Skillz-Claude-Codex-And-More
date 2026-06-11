---
description: Audit SEO/GEO d'un site ou d'une marque: technique, contenu, SERP, autorité, local, visibilité IA, llms.txt et roadmap. Usage: /seo-geo-audit <url|domaine> [--quick|--full|--squad|--geo-only|--technical|--content|--ship-gate]
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - WebSearch
---

# /seo-geo-audit

Lance le skill `seo-geo-audit` pour auditer une surface SEO/GEO avec preuves, scores, findings P0-P3 et roadmap actionnable.

## Usage

```bash
/seo-geo-audit https://example.com --quick
/seo-geo-audit example.com --full
/seo-geo-audit example.com --squad
/seo-geo-audit https://example.com/service --ship-gate
/seo-geo-audit "marque + concurrents" --geo-only
```

## Comportement

1. Charger `.claude/skills/seo-geo-audit/SKILL.md`.
2. Lire `references/seo-squad-framework.md` si mode `--quick`, `--geo-only`, `--technical`, `--content` ou `--ship-gate`.
3. Lire le pack complet `references/seo-squad/` si mode `--full`, `--squad`, ou si l'utilisateur demande les 11 agents.
4. Identifier l'input depuis `$ARGUMENTS`: URL, domaine, marque, concurrents, mode.
5. Collecter les preuves disponibles et classer chaque fait en `Confirmé`, `Déduit` ou `Non vérifié`.
6. Double-vérifier toute affirmation négative avant de la poser comme fait.
7. Produire le rapport SEO/GEO avec scores, findings, grille GEO si pertinente et roadmap 7/30/90.
8. Ne modifier aucun fichier sauf demande explicite après l'audit.

## Sortie attendue

```markdown
## SEO/GEO Audit Report

**Input**: ...
**Mode**: quick | full | squad | geo-only | technical | content | ship-gate
**Confidence**: Élevé | Moyen | Faible
**Verdict**: Ship-ready | Fix P0/P1 first | Needs SEO/GEO loop

### Axis scores
### Findings
### GEO visibility
### Roadmap
### Non vérifié
### Next action
```

## Execution

Lire le skill `seo-geo-audit`, puis auditer:

```text
$ARGUMENTS
```
