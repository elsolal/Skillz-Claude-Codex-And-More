---
description: Orchestration complète Roso SEO Squad: 11 agents SEO/GEO, règles communes, livrables intermédiaires, rapport fusionné et double livrable final. Usage: /seo-geo-squad <url|domaine|marque> [concurrents] [--step-by-step|--all-at-once]
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - WebSearch
---

# /seo-geo-squad

Lance le skill `seo-geo-audit` en mode `--squad` pour exécuter le workflow complet Roso SEO Squad avec les prompts dédiés des 11 agents.

## Usage

```bash
/seo-geo-squad https://example.com --step-by-step
/seo-geo-squad example.com "concurrent A, concurrent B" --all-at-once
/seo-geo-squad "marque locale + ville + concurrents" --step-by-step
```

## Comportement

1. Charger `.claude/skills/seo-geo-audit/SKILL.md`.
2. Charger les références complètes dans `.claude/skills/seo-geo-audit/references/seo-squad/`:
   - `README.md`
   - `00_REGLES_COMMUNES.md`
   - `01_MASTER_ORCHESTRATOR.md`
   - `Outils_Verification_Externes.md`
   - tous les prompts `agents/*.md`
   - les templates `templates/*.md`
3. Suivre l'ordre exact du master orchestrator:
   1. Agent 01 Data Collector
   2. Agent 02 Stratégie & Positionnement SEO/GEO
   3. Agent 03 Audit Homepage & On-page
   4. Agent 07 SEO Technique & Données Structurées
   5. Agent 04 Keyword & Intent Research
   6. Agent 05 Analyse Concurrentielle
   7. Agent 06 Content SEO/GEO
   8. Agent 08 Autorité, Brand & SEO Local
   9. Agent 09 Visibilité IA & Plan d'Action
   10. Agent 09bis Auto-Test Visibilité IA
   11. Agent 10 Master Final Report
4. Adapter les instructions Claude in Chrome au runtime disponible: browser, WebFetch, WebSearch, Playwright, MCP, captures ou collages utilisateur.
5. Classer chaque fait en `Confirmé`, `Déduit` ou `Non vérifié`.
6. Ne jamais poser une absence comme fait sans double-vérification.
7. Créer les livrables dans `audit-livrables/<nom-client>/` si le contexte autorise l'écriture; sinon les produire dans la réponse.
8. Ne pas modifier le site audité ni le code du projet audité pendant l'audit.

## Sortie attendue

- Brief Site.
- Livrables agents 02, 03, 07, 04, 05, 06, 08, 09 et 09bis.
- Rapport fusionné final.
- `Audit_<NomClient>_Note_Strategique` et `Plan_Implementation_<NomClient>` en PDF si possible, sinon Markdown/HTML exportable.
- Liste des éléments `Non vérifié` et checks manuels restants.

## Execution

Lire le skill `seo-geo-audit`, charger le dossier complet `references/seo-squad/`, puis auditer en mode `--squad`:

```text
$ARGUMENTS
```
