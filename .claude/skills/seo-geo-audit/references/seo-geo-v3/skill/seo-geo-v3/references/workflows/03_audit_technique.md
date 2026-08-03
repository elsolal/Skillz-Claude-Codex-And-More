# 03 — Audit technique SEO, GEO et agentique

## Objectif

Évaluer la capacité des contenus à être découverts, explorés, rendus, compris et utilisés, à partir de preuves collectées. Ne pas confondre audit d'échantillon et crawl complet.

## Entrées minimales

- Registre de preuves, inventaire de crawl et rapport de couverture.
- Digital Twin validé, périmètre, templates et conversions prioritaires.
- Données terrain et laboratoire disponibles, clairement séparées.

## Procédure

1. Transformer les preuves en faits techniques atomiques sans recommandation.
2. Analyser par template et par URL critique :
   - découverte, statut, chaînes/boucles de redirection et soft 404 ;
   - indexabilité, canonical, robots, noindex et cohérence sitemap ;
   - doublons, paramètres, facettes, pagination, profondeur et pages orphelines ;
   - liens cassés, architecture interne et distribution des liens ;
   - rendu JavaScript, contenu principal et parité brut/rendu ;
   - mobile, HTTPS, performance terrain/laboratoire et stabilité ;
   - hreflang et cohérence pays/langue ;
   - données structurées valides, visibles et conformes au contenu ;
   - accessibilité sémantique, ARIA utile, formulaires et parcours agentiques ;
   - accès des crawlers par fonction et validation des user-agents/IP lorsque pertinent.
3. Créer un `finding` seulement lorsqu'un fait établit un écart, un risque ou une opportunité.
4. Associer à chaque constat : preuves, URL/templates, sévérité, étendue, confiance et impact plausible. Étiqueter l'impact non mesuré comme hypothèse.
5. Créer les actions dans un registre distinct avec dépendances, propriétaire, effort, risque, rollback et critère de validation.

## Principes actuels à appliquer

- Ne pas recommander de balisage « spécial IA » : utiliser les données structurées pertinentes et conformes aux contenus visibles.
- Traiter `llms.txt` comme expérimentation optionnelle, jamais comme levier de classement ou priorité universelle.
- Ne pas promettre d'affichage enrichi à partir d'un balisage FAQ.
- Ne pas considérer une demande d'indexation comme une garantie d'exploration ou d'indexation.
- Ne pas appliquer de règles rigides de nombre de H2, position du mot-clé, longueur ou densité sans preuve contextuelle.

## Sorties structurées

- `technical_facts` : assertion, valeur, portée, preuve et date.
- `technical_findings` : constat, preuves, étendue, sévérité, confiance et impact.
- `technical_actions` : changement, cible, prérequis, propriétaire, effort, risque, rollback et test d'acceptation.
- `template_matrix` : couverture et état par type de page.
- `blind_spots` : zones non testées et conséquence analytique.

## Vérifications

- Reproduire chaque constat critique sur au moins une URL et vérifier son étendue.
- Tester les correctifs proposés sur un exemple ou un environnement non productif.
- Valider JSON-LD avec un parseur et les outils officiels pertinents ; vérifier aussi la concordance avec le visible.
- Vérifier les règles robots avec le user-agent concerné, sans se fier uniquement à son nom déclaré.
- Faire relire tout constat de sécurité, conformité ou migration par le responsable compétent.

## Critères d'arrêt

- Ne pas noter comme global un constat issu d'un échantillon insuffisant.
- Ne pas recommander une modification risquant désindexation, perte de données ou rupture de conversion sans plan de retour arrière.
- Suspendre si brut, rendu et données d'indexation se contredisent jusqu'à résolution ou déclaration d'incertitude.
