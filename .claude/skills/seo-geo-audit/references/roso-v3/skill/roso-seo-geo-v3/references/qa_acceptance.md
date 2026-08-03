# Contrôles qualité et critères d’acceptation

## Gate 1 — Périmètre

- Propriété, autorisation et usage des données documentés.
- URLs, marchés, langues, appareils et dates figés dans le manifest.
- Limites d’échantillon explicites.
- Aucune donnée sensible collectée sans nécessité.

## Gate 2 — Données

- Identifiants uniques et références résolues.
- Dates au format UTC et URLs normalisées.
- Preuves brutes disponibles ou hash documenté.
- Statut `observed`, `proxy`, `client_reported`, `inferred`, `not_measured` ou `unknown` présent.
- Fraîcheur et niveau de confiance renseignés.

## Gate 3 — Raisonnement

- Chaque finding important référence au moins une preuve.
- Chaque contradiction est résolue ou visible.
- Aucune causalité affirmée à partir d’une simple corrélation temporelle.
- Aucune règle absolue sans source et condition d’application.
- Aucun score ne remplace une donnée manquante par zéro.

## Gate 4 — Actions

- Action reliée à un finding.
- Propriétaire, priorité, effort, dépendances et préconditions renseignés.
- Critère d’acceptation observable.
- Mesure avant/après définie.
- Risque et rollback présents pour les actions techniques ou externes.
- Validation humaine exigée avant publication ou communication.

## Gate 5 — GEO Observatory

- Prompt exact, moteur, modèle ou surface, date, marché, langue et contexte enregistrés.
- Brandé et non brandé séparés.
- Mention et citation séparées.
- Répétitions et variance visibles.
- Réponse brute conservée dans les limites de confidentialité et de licence.
- Aucun « intervalle de confiance » non calculé.

## Gate 6 — Livrables

- Audit, plan, tickets et dashboard issus des mêmes données.
- Manifeste au statut `qa_ready` ou `complete`, avec dernière transition cohérente dans `events.jsonl`.
- Toutes les sorties déclarées dans le manifeste existent dans le dossier projet.
- Le score canonique porte l’`audit_id`, l’`as_of` et l’`input_fingerprint` exacts de la QA de livraison.
- Chaque sortie déclarée possède une entrée `validated` dans `events.jsonl` liant son `sha256:` exact à l’`input_fingerprint`, au `score_as_of` et au `score_sha256` courants. Utiliser `record_delivery.py` après la revue réelle ; toute modification des données, de la coupure, du score ou du fichier invalide cette attestation.
- Un événement report ultérieur `rejected`, `deleted` ou `rolled_back` révoque la validation correspondante. Seule une nouvelle revue suivie d’un nouvel événement `validated` peut rétablir la livraison.
- Le rapport de QA actif reste un artefact interne (`logs/` ou sortie temporaire), pas une sortie client du même manifeste : l’auto-déclarer créerait une dépendance circulaire entre son propre hash et son verdict.
- Un audit `full` couvre les familles de contrôles attendues pour son vertical ; sinon il est requalifié ou bloqué.
- Aucun placeholder, source fictive, promesse ou statistique non sourcée.
- Date, version, couverture, limites et glossaire présents.
- Liens et sommaire fonctionnels.
- Contrastes, ordre de lecture, texte alternatif et métadonnées vérifiés.
- Livrable composé en HTML par l'Agent 11 selon `templates/Charte_PDF_RosoAI_V3.md`, puis imprimé par `tools/render_html_pdf.cjs`. Un Markdown produit par un outil de contrôle interne n'est jamais une sortie client déclarable.
- Rendu PDF inspecté page par page.
- Pour chaque PDF, la même entrée atteste l’inspection de toutes les pages et contient dans `metadata` son `page_count`, `rendered_page_review: all_pages`, le `sha256:` exact et l’`input_fingerprint` courant.

## Sévérités QA

| Niveau | Conséquence |
|---|---|
| Bloquant | Empêche la livraison ou toute action externe |
| Majeur | Livrable partiel avec avertissement ; correction requise |
| Mineur | N’empêche pas la décision ; inscrire au backlog |

Un contrôle automatique qui passe n’est pas une preuve de vérité métier. Il confirme uniquement la cohérence formelle des artefacts vérifiés.

Exécuter la gate stricte après génération et journalisation des livrables :

```bash
python3 scripts/qa_audit.py /chemin/du/projet --as-of 2026-07-15T12:00:00Z --delivery
```
