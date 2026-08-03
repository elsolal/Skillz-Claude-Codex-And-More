# 05 — Contenu, entités et intégrité narrative

## Objectif

Évaluer et améliorer l'utilité, l'originalité, la fiabilité et l'exploitabilité du contenu sans produire à l'échelle des pages faibles ou répétitives.

## Entrées minimales

- Digital Twin et registre des claims validés.
- Inventaire de pages, clusters de demande, données de performance et preuves de contenu.
- Contraintes éditoriales, légales, sectorielles et de marque.

## Procédure

1. Inventorier chaque contenu par URL, template, auteur, date, audience, objectif et statut.
2. Extraire les faits et claims visibles ; comparer prix, zones, personnes, offres et dates au Digital Twin.
3. Évaluer : adéquation au besoin, originalité, expérience démontrable, précision, fraîcheur, structure, lisibilité, sources, auteur, liens et conversion.
4. Vérifier que les passages importants restent accessibles dans le HTML rendu et compréhensibles hors contexte.
5. Détecter cannibalisation, doublons, contenu obsolète, contradictions, pages sans rôle et lacunes.
6. Choisir pour chaque page : conserver, mettre à jour, consolider, réécrire, rediriger, supprimer prudemment ou créer.
7. Construire les briefs à partir de faits vérifiés. Marquer tout claim manquant comme `preuve_requise`.
8. Concevoir des sections citables par leur clarté et leur valeur, sans « hack de chunking », sur-optimisation ou répétition artificielle.
9. Prévoir auteur/relecteur, sources, visuels, liens, CTA, métadonnées et validation post-publication.

## Règles éditoriales

- Employer les titres, longueurs, FAQ, tableaux et données structurées seulement lorsqu'ils servent le lecteur et le format.
- Ne pas fabriquer citation, témoignage, statistique, certification, avis, expertise ou résultat.
- Pour les sujets YMYL ou réglementés, imposer une revue experte et une date de révision.
- Déclarer l'usage d'IA lorsque les règles du client, du secteur ou de la plateforme l'exigent.
- Ne pas affirmer qu'un contenu est « optimisé IA » sans critère observable.

## Sorties structurées

- `content_inventory` : URL, rôle, audience, cluster, état, performance et décision.
- `claim_register` : claim, statut, preuve, propriétaire et date de validité.
- `narrative_conflicts` : assertion publiée, fait de référence, portée, risque et correction proposée.
- `content_findings` : constat, preuves, pages, confiance et impact plausible.
- `content_actions` : brief ou opération, dépendances, propriétaire, validation et métrique.
- `editorial_brief` : objectif, audience, besoin, faits autorisés, sources, structure et critères d'acceptation.

## Vérifications

- Faire correspondre chaque claim sensible à une preuve valide.
- Contrôler originalité et valeur ajoutée par rapport aux pages internes et résultats concurrents.
- Vérifier tous les liens, dates, auteurs, schémas et CTA avant publication.
- Relire le contenu rendu sur mobile et tester la conversion principale.
- Comparer après publication la page au brief et conserver le diff.

## Critères d'arrêt

- Bloquer la publication si une preuve essentielle manque ou si un claim contredit le Digital Twin.
- Bloquer la génération en série sans différenciation, contrôle qualité et utilité démontrée.
- Ne pas supprimer/rediriger une URL performante sans analyse, sauvegarde et plan de mesure.
- Ne pas promettre classement, citation générative ou conversion à partir de la publication d'un contenu.
