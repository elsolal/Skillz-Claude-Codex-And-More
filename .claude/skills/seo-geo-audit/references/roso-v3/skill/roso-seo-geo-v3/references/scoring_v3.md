# Scoring RosoAI V3

## Sommaire

1. Règles
2. Dimensions
3. Calcul
4. Visibilité générative
5. Restitution

## 1. Règles

- Noter uniquement ce qui est mesuré.
- Traiter `not_measured`, `unknown` et `inferred` comme des absences pour la qualité et la fraîcheur des preuves ; ils ne peuvent jamais augmenter un score, une couverture ou une confiance.
- Afficher séparément score, couverture et confiance.
- Ne pas transformer `not_measured` en zéro.
- Ne pas comparer deux runs dont périmètre, marché ou méthode diffèrent sans normalisation explicite.
- Ne jamais intégrer la qualité de la collecte au score de performance du site.
- Ne jamais compter deux fois une même métrique.

## 2. Dimensions

### F — Fondations SEO

Indexabilité, architecture, crawl, canonicals, liens internes, performance terrain, mobile, accessibilité utile aux agents, données structurées pertinentes et santé des feeds.

### V — Visibilité générative observée

Mentions spontanées, liens cités, part de citations, couverture des prompts, exactitude narrative, tonalité et stabilité. Produire des sous-scores séparés par moteur, marché, langue et type de prompt.

### O — Opportunité

Demande qualifiée, valeur commerciale, écarts de contenu, sources accessibles, difficulté et adéquation à l’offre. Un score élevé signifie une opportunité attractive, pas une bonne performance actuelle.

### E — Maturité d’exécution

Propriétaires, processus, capacité technique, production, validation, délais, gouvernance et mesure.

### M — Qualité de la mesure

Couverture, fraîcheur, reproductibilité, provenance et variance. Cette dimension qualifie les autres ; elle ne doit pas masquer leur absence.

## 3. Calcul

Pour une dimension `d` :

```text
score_d = Σ(valeur_i × poids_i) / Σ(poids_i mesurés)
couverture_d = Σ(poids_i mesurés) / Σ(poids_i attendus)
confiance_d = couverture_d × [Σ(coefficient_confiance_i × poids_i) / Σ(poids_i mesurés)]
```

Les valeurs sont bornées entre 0 et 100. Publier `score_d` seulement si `couverture_d ≥ 0,50`; en dessous, afficher « données insuffisantes ». Une décision critique requiert idéalement `confiance_d ≥ 0,70`.

Implémentation V3 fournie :

- **F** : couverture des contrôles de fondation attendus et réellement observés ; la confiance est cette couverture multipliée par la qualité moyenne des preuves concernées.
- **O** : quatre faits numériques facultatifs, bornés de 0 à 100 — `opportunity.demand_score_pct` (30 %), `opportunity.business_value_score_pct` (30 %), `opportunity.content_gap_score_pct` (20 %) et `opportunity.feasibility_score_pct` (20 %). Seuls les faits `observed` ou `client_approved` sont admis ; au moins 50 % des poids doivent être documentés. Le nombre de constats n’entre jamais dans le score.
- **E** : progression (50 %), propriété (20 %), échéances (15 %) et critères testables/rollback (15 %). Sans action, le score reste non mesuré.
- **M** : couverture des contrôles (40 %), qualité de confiance des seules preuves mesurées (30 %), fraîcheur de ces mêmes preuves (20 %) et complétion des répétitions GEO réellement distinctes (10 %). La couverture de M correspond aux poids de composantes réellement calculables ; un zéro observé reste une mesure, une absence ou une ligne `not_measured` reste `null`.

Le fichier canonique est `reports/score_v3.json`. Il inclut `as_of` avec fuseau et une empreinte SHA-256 de `client.yaml`, du manifeste, des registres et des runs GEO afin qu’un rapport ne réutilise pas silencieusement un score ou une identité obsolète.

Ne pas calculer de score global par défaut. Les cinq dimensions répondent à des questions différentes et doivent rester visibles séparément. Une vue de portefeuille peut afficher leur profil, mais ne doit pas réduire opportunité, santé actuelle et maturité d’exécution à une moyenne opaque.

## 4. Visibilité générative

Calculer séparément, dans un contexte homogène de moteur, modèle, surface, marché, langue, appareil, compte, personnalisation, accès web et conditions de session. Séparer aussi les résultats par type de requête, funnel, intention, persona, origine du prompt et criticité :

- `panel_coverage_pct` = identifiants de prompts prévus ayant au moins une réponse exploitable / identifiants du panel gelé ; le dénominateur vient de `planned_prompt_ids`, jamais des seuls prompts observés ;
- `brand_mention_rate_pct` = observations exploitables mentionnant la marque / observations exploitables ;
- `brand_cited_prompt_rate_pct` = observations exploitables citant une URL de la marque / observations exploitables ;
- `brand_citation_share_pct` = citations de la marque / toutes les citations observées ;
- `narrative_accuracy_pct` = faits corrects / faits vérifiables évalués ;
- `positive_recommendation_rate_pct` = annotations `positive` / observations explicitement évaluables (`positive`, `neutral`, `negative`, `brand_absent`) ; exclure `not_applicable`, `not_assessed`, les erreurs et les annotations incohérentes avec `brand_mentioned` ;
- `volatility` = dispersion entre répétitions et dates.

La couverture exposée pour V est la couverture du panel gelé, pas le taux de succès technique des appels. Elle vaut `null` si le plan est absent, incohérent entre répétitions ou agrégé sur plusieurs contextes. Le taux de recommandation positive vaut `null` sans annotation explicite ; ne jamais le déduire de `sentiment`, d'une simple mention ou d'une citation.

Ne pas convertir une présence en top 3 organique, une PAA ou un snippet en présence dans une réponse générative. Ne pas réunir prompts brandés et non brandés dans un seul taux.

## 5. Restitution

Pour chaque dimension, afficher : score, couverture, confiance, variation, méthode, date, périmètre et trois preuves principales. Les couleurs ne doivent jamais être le seul moyen de communiquer l’état.

Une variation est « observée » seulement si le baseline et le run actuel utilisent un protocole comparable. L’attribution à une action reste une hypothèse sauf expérience ou preuve supplémentaire.
