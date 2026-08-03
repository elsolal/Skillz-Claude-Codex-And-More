# Cœur de la Squad V3

Le noyau contient la politique partagée, le Master Orchestrator, le manifeste de routage et onze cartes d’agents.

## Ordre de lecture

1. `00_REGLES_COMMUNES_V3.md`
2. `01_MASTER_ORCHESTRATOR_V3.md`
3. `AGENTS_MANIFEST.json`
4. la carte de chaque agent activé
5. `../skill/seo-geo-v3/SKILL.md` et ses références routées

## Règle d’or

Les agents ne s’échangent pas des résumés non vérifiés comme source de vérité. Ils lisent et mettent à jour les mêmes objets structurés du projet, dans les limites de leur rôle. Le Master Orchestrator valide les handoffs et déclenche la QA indépendante avant livraison.

## Agents cœur

| ID | Agent | Responsabilité principale |
|---|---|---|
| 01 | Data Collector | Collecte autorisée et Evidence Vault |
| 02 | Stratégie et positionnement | Digital Twin, objectifs et cadrage |
| 03 | Audit On-Page | Page, proposition de valeur et parcours |
| 04 | Demande et intention | Besoins, opportunités et intentions |
| 05 | Analyse concurrentielle | Entités, écarts et sources concurrentes |
| 06 | Analyse de contenu | Inventaire, qualité, pruning et briefs |
| 07 | SEO technique | Crawl, indexabilité, rendu et JSON-LD |
| 08 | Autorité, marque et local | Graphe de sources et cohérence d’entité |
| 09 | GEO Observatory | Panel, runs, citations et narration |
| 10 | QA adversariale | Intégrité, provenance et gates de livraison |
| 11 | Master Final Report | Rapports, PDF et handoff final |

Les extensions du dossier `../extensions/` sont activées uniquement lorsqu’un besoin précis l’exige.
