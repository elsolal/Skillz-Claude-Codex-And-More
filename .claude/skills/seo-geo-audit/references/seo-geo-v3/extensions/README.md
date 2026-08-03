# Extensions et agents spécialisés V3

Ces agents complètent le noyau. Ils sont activés par `core/01_MASTER_ORCHESTRATOR_V3.md` uniquement lorsque le périmètre et les données le justifient.

Ils appliquent toujours `core/00_REGLES_COMMUNES_V3.md` et `skill/seo-geo-v3/SKILL.md`.

| Agent | Usage |
|---|---|
| 12 Rédacteur | Produire ou réviser un contenu approuvé |
| 13 Audit Express | Diagnostic public borné |
| 14 Page unique | Audit d’une URL précise |
| 15 Delta Re-audit | Comparer deux états compatibles |
| 16 GEO International | Segmenter langues, marchés et entités |
| 17 Générateur llms.txt | Produire un artefact expérimental sans promesse SEO |
| 18 Compagnon d’implémentation | Appliquer des actions approuvées avec rollback |
| 19 Tracker mensuel | Organiser le suivi récurrent |
| 20 Acquisition de sources | Développer des sources externes pertinentes et éthiques |
| 21 Connecteurs et mesure | Importer des données first-party et documenter leur qualité |

Une extension ne doit jamais créer une preuve manquante par inférence. Si une mesure optionnelle manque, elle la marque `not_measured` avec l'impact et la prochaine méthode de collecte. Si une entrée d'activation obligatoire manque, elle renvoie un paquet `blocked` ou `partial` selon ce qui reste exploitable ; l'orchestrateur passe le run à `paused` lorsque cette lacune empêche la décision ou le livrable annoncé.
