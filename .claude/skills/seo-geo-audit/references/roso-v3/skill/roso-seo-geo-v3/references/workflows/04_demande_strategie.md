# 04 — Demande, marché et stratégie

## Objectif

Relier demande observable, audiences et valeur métier à une stratégie de pages et de mesure. Séparer demande observée, estimation d'outil et hypothèse.

## Entrées minimales

- Digital Twin, objectifs, conversions et marchés.
- Données GSC/site search/CRM/support, recherches associées et outils autorisés.
- Inventaire des pages, concurrents déclarés et concurrents réellement observés.

## Procédure

1. Extraire les besoins et formulations depuis les sources de première partie avant de générer des idées synthétiques.
2. Enregistrer chaque requête ou question avec source, période, marché, langue, volume éventuel et niveau de confiance.
3. Segmenter par audience, tâche, problème, étape du parcours, marque/non-marque, localité et valeur métier.
4. Regrouper par intention et besoin réel, sans supposer qu'une expression équivaut toujours à une page.
5. Cartographier les pages existantes, les chevauchements, les lacunes et les sources déjà citées par les moteurs/assistants.
6. Distinguer :
   - demande observée de première partie ;
   - demande estimée par un outil ;
   - signaux qualitatifs ;
   - hypothèses synthétiques à tester.
7. Évaluer l'opportunité sans l'intégrer au score de santé actuel du site.
8. Définir une architecture cible conditionnelle : créer, consolider, mettre à jour, rediriger, conserver ou ne rien faire.
9. Relier chaque initiative à une audience, une conversion, une preuve et un indicateur de succès.

## Sorties structurées

- `demand_signals` : formulation, source, période, segment, mesure et confiance.
- `intent_clusters` : besoin, variantes, audience, étape, marché et page cible.
- `page_map` : URL actuelle, rôle, cluster, décision et justification.
- `strategy_findings` : écart entre demande, offre et couverture, avec preuves.
- `strategy_actions` : initiative, résultat attendu formulé comme hypothèse, dépendances et validation.
- `measurement_plan` : indicateur, source, baseline, cadence et responsable.

## Vérifications

- Ne jamais inventer de volume, CPC, taux de conversion ou taille de marché.
- Vérifier les ambiguïtés linguistiques et locales avec des SERP/données propres au marché.
- Valider la valeur métier et la faisabilité avec le client avant de prioriser.
- Contrôler qu'une nouvelle page apporte une valeur distincte et ne crée pas de contenu à l'échelle sans utilité.
- Identifier explicitement les concurrents de visibilité différents des concurrents métier.

## Critères d'arrêt

- Suspendre la stratégie si l'offre prioritaire ou la conversion ne sont pas définies.
- Ne pas créer de plan international à partir d'une simple traduction automatique du marché source.
- Ne pas conclure à une absence de demande sur la seule base d'un outil ou d'une période courte.
- Ne promettre aucune position, citation, volume de trafic ou revenu.
