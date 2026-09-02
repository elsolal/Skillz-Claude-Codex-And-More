# 09 — Implémentation supervisée

## Objectif

Transformer une action approuvée en changement vérifiable, réversible et journalisé. Rester en lecture seule par défaut et exiger une validation humaine avant toute mutation externe.

## Entrées minimales

- Action approuvée, périmètre, propriétaire et critère d'acceptation.
- Baseline, dépendances, risques, sauvegarde et plan de retour arrière.
- Environnement de staging ou méthode de prévisualisation lorsque disponible.

## Procédure

1. Effectuer le preflight : accès, sauvegarde, version, dépendances, fenêtre, responsable et monitoring.
2. Produire un patch, diff, brief ou ticket sans l'appliquer.
3. Valider techniquement le changement hors production : syntaxe, liens, rendu, données structurées, accessibilité, analytics et conversion.
4. Présenter impact, fichiers/URL concernés, risques, tests et rollback à l'approbateur.
5. Obtenir une approbation explicite et horodatée pour l'action exacte.
6. Appliquer uniquement le changement approuvé. Ne jamais élargir silencieusement le périmètre.
7. Tester immédiatement le résultat publié : statut, HTML/rendu, comportement, tracking et absence de régression visible.
8. Comparer au baseline, conserver le diff et journaliser auteur, date et résultat.
9. Déclencher le rollback si un critère de sécurité ou d'acceptation échoue.
10. Programmer la mesure différée appropriée ; ne pas conclure trop tôt à un impact SEO/GEO.

## Cas courants

- Contenu : valider claims, auteur, sources, liens, métadonnées, CTA et rendu.
- Technique : tester sur échantillon/staging puis déployer progressivement.
- Données structurées : parser, valider, comparer au visible et contrôler après rendu.
- Redirections/canonicals/robots : simuler, vérifier les conflits et prévoir un rollback immédiat.
- Tracking : vérifier consentement, nomenclature, déduplication et réception des événements.
- Prospection : exiger validation humaine avant envoi et respecter opt-out/conformité.

## Sorties structurées

- `change_request` : action, périmètre, diff, risques, tests et rollback.
- `approval_record` : approbateur, version exacte, date, restrictions et expiration.
- `implementation_log` : changement, auteur, environnement, horodatage et résultat.
- `validation_results` : test, attendu, observé, preuve et statut.
- `rollback_record` : déclencheur, opération, résultat et suivi.
- `follow_up_measurement` : métrique, baseline, date minimale et responsable.

## Vérifications

- Ne jamais enregistrer secrets, tokens, cookies ou données personnelles dans les livrables.
- Vérifier que l'approbation correspond au diff appliqué.
- Tester parcours critique, mobile et analytics après publication.
- Comparer un échantillon non modifié pour détecter une régression globale.
- Maintenir séparation entre « publié correctement » et « impact obtenu ».

## Critères d'arrêt

- Arrêter sans approbation, sauvegarde ou rollback lorsqu'ils sont requis.
- Arrêter si le staging diffère trop de la production pour valider le risque.
- Rollback immédiat en cas de désindexation imprévue, rupture de conversion, erreur légale, fuite de données ou régression critique.
- Ne jamais présenter l'exécution comme garantie de résultat.
