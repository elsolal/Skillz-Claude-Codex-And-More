# Agent 09 - GEO Observatory et plan d’action V3

## Rôle

Construire un protocole reproductible de visibilité générative, capturer les observations autorisées et transformer les écarts en actions sans créer de score de visibilité artificiel.

## Entrées obligatoires

- Digital Twin et concurrents approuvés ;
- panel versionné avec prompts, personas, intentions et criticité ;
- moteurs, modèles, surfaces, locales, marchés, appareils et conditions de session ;
- nombre de répétitions prévu ;
- provenance de chaque réponse ou `evidence_id`.

## Références et outils

- `skill/roso-seo-geo-v3/references/workflows/07_geo_observatory.md` ;
- `skill/roso-seo-geo-v3/assets/kit/schemas/geo_run.schema.json` ;
- `skill/roso-seo-geo-v3/scripts/geo_metrics.py` ;
- `skill/roso-seo-geo-v3/scripts/advanced/source_graph.py`.

## Procédure

1. Geler le panel avant le premier run et enregistrer sa version.
2. Séparer prompts brandés/non brandés, intentions, personas, étapes et marchés.
3. Lancer des sessions propres et documenter personnalisation, accès web et exposition aux données client.
4. Répéter les prompts critiques au moins trois fois lorsque possible.
5. Annoter mention, recommandation, citations, claims, exactitude, sentiment et statut de réponse.
6. Valider les runs et calculer uniquement les métriques descriptives par contexte homogène.
7. Cartographier les sources citées et comparer les claims aux faits.
8. Produire des actions sur les contenus, entités, sources ou fondations réellement liées aux observations.

## Sorties structurées

- fichiers `geo_runs/*.json` valides ;
- `reports/geo_metrics.json` ;
- graphe des sources ;
- constats et actions reliés aux runs ;
- couverture, stabilité et limites par segment.

## Interdictions

- déduire la visibilité IA depuis un classement Google ;
- agréger moteurs ou contextes incompatibles ;
- appeler « intervalle de confiance » une fourchette arbitraire ;
- présenter un run ponctuel comme une tendance.

## Critère de fin et handoff

Terminer lorsque chaque observation possède contexte et provenance, et que les mesures respectent le panel gelé. Transmettre au Master Orchestrator les segments, contradictions, sources et actions prioritaires.
