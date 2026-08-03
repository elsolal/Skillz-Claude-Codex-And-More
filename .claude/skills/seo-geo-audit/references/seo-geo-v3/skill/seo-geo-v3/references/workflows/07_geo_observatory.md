# 07 — GEO Observatory

## Objectif

Mesurer de façon reproductible la présence, les sources et l'exactitude narrative dans les expériences génératives. Ne jamais transformer un test ponctuel en vérité générale.

## Entrées minimales

- Digital Twin et claims de référence.
- Panel de questions issu de données première partie, recherche observée et hypothèses synthétiques étiquetées.
- Marchés, langues, personas, étapes du parcours et concurrents.
- Liste des moteurs/assistants accessibles selon leurs conditions d'utilisation.

## Construction du panel

1. Séparer questions `spontanees_non_marque`, `aidees_marque`, comparatives, locales, informationnelles et transactionnelles.
2. Enregistrer pour chaque question : origine et référence, formulation, persona, intention, marché, langue, criticité et date.
3. Éviter les questions orientées destinées uniquement à faire apparaître le client.
4. Geler une version du panel pour rendre les deltas comparables ; versionner toute modification.

## Exécution

1. Enregistrer moteur, modèle/version visible, mode web, compte/personnalisation, locale, appareil et date/heure. Documenter la session avec un identifiant, l'état du contexte (`new`, `cleared`, `continuing`, `unknown`), l'exposition éventuelle aux documents du client et la complétude de cette documentation.
2. Utiliser une session non contaminée par les documents du client lorsque le test vise la visibilité spontanée.
3. Répéter au moins trois fois les questions critiques lorsque le coût et les règles le permettent ; conserver toutes les réponses.
4. Capturer réponse, liens, citations, ordre, extrait, erreurs et statut de l'exécution. Relier chaque observation à une empreinte SHA-256 de la réponse ou à un `evidence_id` existant.
5. Annoter séparément : mention, recommandation (`positive`, `neutral`, `negative`, `brand_absent`, `not_applicable`, `not_assessed`), lien cité, source utilisée, position observable, tonalité et exactitude des faits. Une tonalité positive ne constitue pas une recommandation positive.
6. Comparer les assertions au Digital Twin pour détecter erreurs, obsolescence, confusion d'entité et claims non autorisés.
7. Distinguer métriques observées, proxies et données indisponibles. Un échec d'outil n'est pas une absence de visibilité.
8. Conserver une seule observation par `prompt_id`, contexte de panel et numéro de répétition. Une duplication dans le même slot est invalide et ne compte jamais comme répétition distincte.

En cas d'échec de mesure temporaire, suivre le « Protocole en cas d'échec de mesure » de `core/00_REGLES_COMMUNES_V3.md`.

## Métriques

- Couverture V/panel : prompts prévus ayant au moins une réponse exploitable / `planned_prompt_ids` du panel gelé. Ne pas lui substituer le taux de réponses réussies. Renvoyer `null` si ce dénominateur est absent, incohérent ou mélange plusieurs contextes.
- Taux de mention spontané et aidé, calculés séparément.
- Taux de lien/citation, part des citations et diversité des sources.
- Exactitude narrative, erreurs critiques et obsolescence.
- Tonalité annotée avec règle explicite et possibilité `indetermine`.
- Volatilité entre répétitions, moteurs, marchés et dates.
- Données première partie : impressions génératives disponibles, referrals IA, conversions et pipeline, sans double comptage.

Ne pas produire d'intervalle de confiance arbitraire. Afficher taille d'échantillon, variance et méthode. Ne pas fusionner ces métriques avec la santé technique dans un score opaque.

## Sorties structurées

- `prompt_panel` : version, origine, segment, criticité et statut.
- `geo_runs/*.json` : paramètres, session documentée, plan de prompts, réponse brute/empreinte, citations, annotations et erreurs.
- `geo_metrics` : formule, numérateur, dénominateur, période, segment et limites.
- `narrative_alerts` : fait attendu, assertion observée, sévérité, preuves et action proposée.
- `source_influence_graph` : question, réponse, source, page et conversion éventuelle.
- `geo_findings` et `geo_actions` dans des registres séparés.

## Vérifications et arrêt

- Faire relire un échantillon d'annotations par un second évaluateur ; documenter les désaccords.
- Vérifier les liens et sources dans la réponse réelle, pas seulement le texte généré.
- Respecter conditions d'utilisation, quotas et restrictions d'automatisation.
- Suspendre la comparaison si modèle, interface ou méthode change ; créer une rupture de série.
- Ne promettre ni inclusion, ni citation, ni stabilité d'un résultat génératif.
