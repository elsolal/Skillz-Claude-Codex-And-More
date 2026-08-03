# 08 — Priorisation et portefeuille d'actions

## Objectif

Transformer les constats validés en décisions traçables, adaptées aux contraintes et dépendances, sans score composite trompeur ni quota artificiel d'actions.

## Entrées minimales

- Registres de faits, constats et actions issus des workflows spécialisés.
- Objectifs métier, risques, ressources, coûts, calendrier et responsables.
- Baselines de mesure et niveau de confiance des preuves.

## Procédure

1. Rejeter ou renvoyer tout constat sans preuve, portée, confiance ou conséquence explicite.
2. Dédupliquer les actions et relier chaque action à un ou plusieurs `finding_id`.
3. Évaluer séparément :
   - impact métier plausible ;
   - impact SEO/GEO observable ;
   - confiance de la preuve ;
   - étendue ;
   - effort, coût, délai et disponibilité ;
   - risque, réversibilité et conformité ;
   - dépendances et capacité de validation.
4. Utiliser une matrice documentée ou une formule simple seulement si chaque composante reste visible. Ne pas masquer les dimensions derrière une note unique.
5. Identifier les bloqueurs et ordonner les dépendances en graphe.
6. Organiser les horizons selon le contexte : immédiat, 0–30, 31–60, 61–90 jours et backlog. Ne pas imposer un nombre minimal de projets.
7. Assigner propriétaire, approbateur, date cible, coût estimé, critère d'acceptation et métrique de suivi.
8. Faire valider arbitrages, ressources et risques par le client.

## Catégories à garder distinctes

- `performance_actuelle` : état observé du site ou de la visibilité.
- `couverture_donnees` : ce qui a réellement été mesuré.
- `confiance` : solidité de la preuve et reproductibilité.
- `opportunite` : gain plausible, non réalisé.
- `maturite_execution` : capacité à mettre en œuvre.

## Sorties structurées

- `action_portfolio` : action, constats, impact, confiance, effort, risque, dépendances et statut.
- `dependency_graph` : prérequis, bloqueurs et ordre recommandé.
- `roadmap` : horizon, propriétaire, approbateur, date, mesure et critère d'arrêt.
- `decision_log` : décision, alternatives, motif, auteur et date.
- `deferred_actions` : raison du report, condition de réexamen et date.

## Vérifications

- Vérifier qu'aucune action critique ne dépend d'une hypothèse non déclarée.
- Vérifier qu'un quick win n'introduit pas de dette, risque légal ou perte de données.
- Contrôler ressources et accès avant d'annoncer une date.
- Établir une baseline avant toute action censée produire un delta.
- Tester la cohérence entre roadmap client, tickets et plan de mesure.

## Critères d'arrêt

- Bloquer une action sans propriétaire, preuve, critère d'acceptation ou plan de retour arrière lorsqu'il est nécessaire.
- Ne pas prioriser uniquement selon le volume de recherche ou la facilité.
- Ne pas traduire un impact plausible en promesse de trafic, classement, leads ou revenu.
