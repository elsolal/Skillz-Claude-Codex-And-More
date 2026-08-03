# 10 — Reporting client et livrables

## Objectif

Produire des livrables lisibles, traçables et cohérents depuis une même base structurée. Préserver la séparation entre observations, interprétations, inconnues et décisions.

## Entrées minimales

- Manifeste du run, périmètre, Digital Twin et couverture.
- Registres de preuves, faits, constats, actions, décisions et limites.
- Roadmap validée, métriques, thème et identité de livraison.

## Architecture des livrables

1. Résumé exécutif : contexte, enjeux, constats majeurs, décisions et limites.
2. Audit stratégique : faits, écarts, opportunités, impacts plausibles et preuves.
3. Plan d'implémentation : actions, ordre, propriétaires, risques, validation et mesure.
4. Annexe méthodologique : périmètre, période, sources, couverture, versions et angles morts.
5. Export machine : manifestes et identifiants permettant reprise, delta et tickets.

Ne pas dupliquer manuellement une même donnée dans plusieurs sources. Générer tableaux, PDF, dashboard et exports depuis les registres communs.

## Procédure

1. Geler le `run_id`, la date de coupure et les versions des données.
2. Conserver les statuts canoniques des objets : `observed`, `proxy`, `client_reported`, `inferred`, `not_measured` ou `unknown` pour les preuves et mesures ; statuts dédiés du registre pour les faits.
3. Relier chaque constat à ses `evidence_id` et chaque action à ses `finding_id`.
4. Présenter séparément santé actuelle, couverture, confiance, opportunité et maturité.
5. Traduire le langage technique sans supprimer la nuance, les conditions ou l'incertitude.
6. Afficher les formules, tailles d'échantillon, périodes et ruptures de méthode.
7. Adapter le thème par variables ; ne pas laisser de marque, couleur, police ou exemple codé en dur.
8. Composer le livrable : l'Agent 11 **écrit lui-même le HTML** des deux documents en suivant `templates/Charte_PDF_RosoAI_V3.md`, puis l'imprime avec `tools/render_html_pdf.cjs`. Aucun script ne produit le document client. Exécuter ensuite la QA éditoriale, technique et visuelle, puis appeler `record_delivery.py` pour chaque sortie déclarée afin de lier son SHA-256 aux entrées courantes. Pour un PDF, ne confirmer `all_pages` et `page_count` qu’après rendu et inspection réels.

## Sorties structurées

- `executive_report` : synthèse client et décisions.
- `strategic_audit` : constats détaillés, preuves et limites.
- `implementation_plan` : actions, dépendances, responsables et validations.
- `technical_annex` : méthodologie, collecte, couverture et métriques.
- `delivery_manifest` : fichiers, versions, empreintes, sources et date.
- `machine_exports` : constats, actions, tickets et état de reprise.

## QA obligatoire

- Détecter contradictions, doublons, placeholders, identifiants orphelins et données périmées.
- Vérifier liens, ancres, numérotation, sommaire, tableaux, débordements et pagination.
- Rendre les PDF et inspecter visuellement toutes les pages.
- Vérifier que le score, chaque livrable et chaque événement de validation partagent la même date de coupure et le même `input_fingerprint` ; une modification impose régénération et nouvelle revue.
- Rendre en PDF chaque rapport déclaré avec `tools/render_html_pdf.cjs`, depuis le HTML composé par l'Agent 11. Le PDF est le livrable final ; un Markdown de contrôle interne n'est jamais remis au client. Si Node ou Chromium manque, proposer l'installation à l'utilisateur et attendre son accord.
- Préserver texte sélectionnable, ordre de lecture, titres, contraste, langue, texte alternatif et métadonnées ; produire un PDF balisé dès que la chaîne le permet.
- Vérifier que les exemples sont étiquetés et ne sont pas confondus avec les données client.
- Supprimer secrets, données personnelles inutiles et traces internes.

## Critères d'arrêt

- Bloquer la livraison si un constat majeur n'a pas de preuve ou si les livrables se contredisent.
- Bloquer si le périmètre, la date, la méthode ou les limites ne sont pas visibles.
- Ne pas utiliser « garanti », « assuré » ou une estimation de revenu non fondée.
- Présenter les résultats comme état daté, pas comme vérité permanente.
