# 11 — Monitoring, alertes et analyse Delta

## Objectif

Détecter les changements importants, distinguer évolution réelle et variation de mesure, puis déclencher une action proportionnée. Conserver les baselines immuables.

## Entrées minimales

- Baseline approuvée, manifestes des runs et métriques versionnées.
- Périmètre stable, panel GEO gelé, calendrier et seuils d'alerte.
- Journal des implémentations, incidents, migrations et changements de plateforme.

## Procédure

1. Définir cadence par risque et volatilité : quotidien pour incidents critiques, hebdomadaire pour signaux rapides, mensuel/trimestriel pour tendances.
2. Recollecter avec la même configuration lorsque possible ; enregistrer tout changement d'outil, modèle, interface, compte, locale ou échantillon.
3. Comparer preuves, faits, constats, métriques et actions entre `baseline_run_id` et `current_run_id`.
4. Classer chaque delta :
   - amélioration ou régression observée ;
   - nouveau problème ou problème résolu ;
   - changement de contenu/technique connu ;
   - variation de plateforme ou de méthode ;
   - bruit, donnée insuffisante ou cause inconnue.
5. Pour le GEO, conserver panel et paramètres comparables, mesurer la variance et créer une rupture de série si la méthode change.
6. Pour le SEO, surveiller couverture, erreurs, templates, performance terrain, requêtes/pages et conversions sans attribuer automatiquement la causalité.
7. Comparer l'intégrité narrative aux faits actuels du Digital Twin et signaler prix, personnes, produits ou zones obsolètes.
8. Déclencher une alerte seulement avec preuve, sévérité, portée, confiance et procédure de vérification.
9. Créer une action distincte après confirmation ; conserver les faux positifs et décisions.

En cas d'échec de mesure temporaire, suivre le « Protocole en cas d'échec de mesure » de `core/00_REGLES_COMMUNES_V3.md`.

## Sorties structurées

- `delta_manifest` : runs comparés, périodes, configurations et compatibilité.
- `delta_records` : métrique/fait, avant, après, différence, preuve et classification.
- `alerts` : sévérité, portée, confiance, propriétaire, délai et procédure.
- `change_attribution` : événements connus, corrélation temporelle et niveau de preuve ; ne pas déclarer de causalité sans test.
- `delta_findings` et `delta_actions` séparés.
- `monitoring_summary` : changements majeurs, stabilité, angles morts et décisions.

## Niveaux d'alerte

- `critique` : risque immédiat de sécurité, désindexation large, panne ou rupture de conversion ; vérifier et escalader immédiatement.
- `eleve` : régression importante et confirmée sur un périmètre prioritaire.
- `modere` : tendance persistante nécessitant analyse planifiée.
- `information` : changement faible, attendu ou encore incertain.

## Vérifications

- Rejouer toute anomalie critique avant escalade, sauf risque nécessitant protection immédiate.
- Comparer avec un groupe ou échantillon non modifié lorsque possible.
- Vérifier saisonnalité, délai d'indexation, consentement analytics, changements de tracking et incidents externes.
- Ne pas traiter une absence de données comme zéro.
- Réviser périodiquement seuils, panel et périmètre avec journal de décision.

## Critères d'arrêt

- Suspendre le delta si les runs ne sont pas comparables ; produire une nouvelle baseline explicitement approuvée.
- Ne pas déclencher de correction automatique destructive.
- Ne pas conclure à un succès ou échec sur une observation isolée ou une fenêtre trop courte.
- Ne jamais promettre récupération de position, de citation ou de revenu.
