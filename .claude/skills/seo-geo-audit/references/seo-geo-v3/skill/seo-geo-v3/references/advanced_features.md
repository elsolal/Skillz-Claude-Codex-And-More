# Fonctionnalités avancées V3

Ces outils optionnels utilisent uniquement la bibliothèque standard Python. Les exécuter depuis la racine du Skill ou utiliser des chemins absolus. Ils lisent les fichiers V3 existants sans ajouter de nouveaux types aux schémas.

## Sommaire

- [Control Center multi-projets](#control-center-multi-projets)
- [Narrative Integrity Monitor](#narrative-integrity-monitor)
- [Source Graph](#source-graph)
- [Comparaison Delta](#comparaison-delta)
- [Exports de tickets](#exports-de-tickets)
- [Imports de métriques](#imports-de-métriques)
- [Veille des sources officielles](#veille-des-sources-officielles)
- [Limites communes](#limites-communes)

## Control Center multi-projets

Générer une page HTML autonome, sans JavaScript ni ressource distante :

```bash
python3 scripts/advanced/control_center.py /chemin/projets \
  --recursive \
  --output control-center.html \
  --data-output control-center.json
```

Le dashboard agrège statuts, constats ouverts, actions, scores F/E/M déjà produits et mesures descriptives des runs GEO. Chaque score publiable conserve séparément sa valeur, sa couverture et sa confiance ; la date `as_of` du snapshot est affichée dans la colonne d’actualisation et reste distincte de la date de génération du dashboard. Les taux GEO restent séparés par moteur, modèle, surface, locale, pays, appareil, état de compte, personnalisation, accès web, panel et type de requête ; aucune moyenne mixant ces contextes n’est affichée. Il n’invente pas zéro lorsqu’une donnée manque et ne calcule aucune moyenne globale. Les chemins locaux sont exclus du snapshot sauf avec `--include-paths`.

Chaque registre, preuve, score et run doit porter le même `audit_id` que le manifeste. Le Control Center recalcule l’empreinte canonique des entrées avec la même fonction que `score_v3.py` : un score sans empreinte, devenu obsolète ou dépendant d’une entrée rattachée à un autre audit est non publiable. L’artefact est exclu du dashboard et apparaît comme alerte d’intégrité, au lieu d’être attribué silencieusement au mauvais client.

Régénérer le fichier après chaque mise à jour : il s’agit d’un snapshot statique, pas d’une application synchronisée.

## Narrative Integrity Monitor

Agrèger les statuts de claims enregistrés dans `geo_runs/` :

```bash
python3 scripts/advanced/narrative_integrity.py /chemin/projet \
  --facts /chemin/projet/facts.json \
  --output narrative-integrity.json \
  --csv narrative-integrity-details.csv
```

Le rapport sépare `accurate`, `inaccurate`, `outdated` et `unverifiable`, puis signale les clés de faits comportant une erreur ou une information périmée. `--facts` enrichit le rapport avec le statut du registre, sans réévaluer la vérité.

Le taux d’exactitude utilise seulement `accurate + inaccurate + outdated` comme dénominateur. Toujours afficher séparément le volume `unverifiable`. Les statuts doivent provenir d’une revue fondée sur le Digital Twin et des preuves ; le script ne les attribue pas lui-même.

## Source Graph

Produire simultanément le graphe JSON et les occurrences CSV :

```bash
python3 scripts/advanced/source_graph.py /chemin/projet \
  --json-output source-graph.json \
  --csv-output source-paths.csv
```

Le JSON contient trois types de nœuds (`prompt`, `domain`, `url`) et deux arêtes (`prompt_cites_domain`, `domain_contains_url`). Les répétitions restent comptées afin de préserver la volatilité observée ; utiliser aussi `distinct_runs` et `distinct_prompts`.

Une citation est une occurrence enregistrée, pas une preuve de causalité, d’autorité générale ou de conversion.

## Comparaison Delta

Comparer deux projets complets, de préférence avec la même date de calcul :

```bash
python3 scripts/advanced/delta_compare.py /projets/client-t0 /projets/client-t1 \
  --as-of 2026-07-15T12:00:00Z \
  --output delta.json
```

Le script réutilise le fichier canonique `score_v3.json` lorsqu’il existe, tout en acceptant l’ancien alias `scores_v3.json` ; sinon il appelle localement `score_v3.py`. Un delta n’est produit que si la dimension est comparable : même client, URL racine complète, mode, limite de crawl, inclusions, exclusions, contrôles attendus, marchés/locales/verticale, version de scoring et méthode compatible. L’ordre des listes ne change pas leur équivalence.

Garde-fous spécifiques :

- F : mêmes catégories, contrôles attendus et limite de crawl ;
- M : mêmes contrôles et pondérations ;
- V : appariement par contexte normalisé, puis même identité de marque, moteur, modèle, surface, locale, état de compte, panel, prompts, classifications, répétitions réellement présentes et multiplicité. L’ordre des segments n’a aucun effet. Les métriques sont comparées dans `segment_deltas` uniquement pour les signatures appariées ; un contexte ajouté, retiré ou modifié est explicitement neutralisé sans contaminer un autre contexte resté compatible ;
- E : même périmètre client et méthode de score.

`--as-of` doit contenir un fuseau (`Z` ou `+02:00`) et s’applique aux deux recalculs. Avec deux fichiers de score isolés, les manifestes et signatures GEO sont absents : les deltas concernés sont neutralisés. Les registres, preuves, runs ou scores dont l’`audit_id` ne correspond pas au manifeste bloquent également les deltas et sont exposés dans `scope.blocking_reasons`. Utiliser les dossiers projets pour une comparaison défendable. Une variation ne prouve jamais qu’une action en est la cause.

## Exports de tickets

Créer un CSV générique, Jira ou Notion :

```bash
python3 scripts/advanced/export_tickets.py /chemin/projet \
  --format jira \
  --priority P0 --priority P1 \
  --output jira-import.csv
```

```bash
python3 scripts/advanced/export_tickets.py /chemin/projet \
  --format notion \
  --output notion-import.csv
```

Par défaut, les actions `done` et `cancelled` sont exclues ; utiliser `--include-terminal` pour les conserver. Dans tous les CSV avancés, les cellules textuelles commençant par `=`, `+`, `-` ou `@` sont neutralisées contre l’exécution de formules.

Ces fichiers sont des exports locaux. Aucun projet Jira, aucune base Notion et aucun ticket externe ne sont créés. Vérifier les noms de colonnes exigés par l’espace de destination avant import.

## Imports de métriques

Normaliser un export CSV local GSC, Bing ou GA4 en preuves compatibles avec `evidence.jsonl` :

```bash
python3 scripts/advanced/import_metrics.py export-gsc.csv \
  --source gsc \
  --audit-id audit_client_20260715 \
  --output gsc-evidence.jsonl
```

Pour ajouter explicitement les preuves à un projet :

```bash
python3 scripts/advanced/import_metrics.py export-bing.csv \
  --source bing \
  --project /chemin/projet \
  --append
```

L’import dans un projet vérifie la présence de `read_gsc`, `read_bing` ou `read_ga4` dans les permissions du manifeste. `--append` est obligatoire lorsque la destination canonique est le ledger `evidence.jsonl`, même si le chemin fourni contient `..` ou passe par un lien symbolique, afin d’empêcher son écrasement accidentel.

Le script reconnaît les dimensions et métriques courantes et gère les CSV séparés par virgule, point-virgule ou tabulation. `raw_hash` représente les octets du fichier CSV source. Un hash séparé décrit la ligne normalisée ; l’identifiant de preuve combine fichier, position, source et audit. Deux lignes identiques d’un même fichier restent donc distinctes, tandis qu’un réimport avec `--append` ignore les identifiants déjà présents. Il ne se connecte à aucune API et ne doit jamais être présenté comme un connecteur temps réel.

Les colonnes inconnues sont ignorées par défaut pour limiter la collecte de données non nécessaires. `--include-unknown` les conserve explicitement : vérifier alors PII, secrets, politique de rétention et autorisation client. Contrôler manuellement les unités et conventions des exports, notamment pourcentages, devises et séparateurs décimaux.

## Veille des sources officielles

Préparer le contrôle sans réseau, comportement par défaut :

```bash
python3 scripts/advanced/rule_source_check.py \
  --output official-sources-plan.json
```

Lancer les requêtes HTTPS uniquement après décision explicite de l’opérateur :

```bash
python3 scripts/advanced/rule_source_check.py \
  --network \
  --baseline official-sources-previous.json \
  --output official-sources-current.json \
  --fail-on-change
```

Sans `--input`, les URLs sont extraites de `references/product/rules_registry.md`. Seuls les domaines allowlistés sont acceptés, y compris après redirection. Ajouter exceptionnellement un domaine officiel avec `--allow-domain domaine.example`.

Le contrôle utilise un GET borné afin de relever statut HTTP, hash SHA-256 des octets reçus, `Last-Modified`, `ETag`, type et taille. Un changement de hash déclenche une revue humaine : il ne prouve pas qu’une règle a changé. Par défaut, aucune requête réseau n’est créée et le statut reste `not_checked`.

## Limites communes

- Ne jamais interpréter une absence de donnée comme une valeur nulle.
- Conserver les snapshots utilisés avec les livrables afin de rendre les conclusions auditables.
- Ne pas fusionner des clients, marchés, panels ou méthodes différents dans une évolution unique.
- Ne pas présenter une corrélation temporelle comme la causalité d’une action.
- Valider les permissions avant tout ajout au ledger et minimiser les données importées.
- Inspecter les CSV avant import dans un outil tiers ; les mappings de champs et workflows varient selon les espaces.
- Les scripts ne publient rien, ne modifient aucun CMS et n’appellent aucun service externe, à l’exception du GET explicitement autorisé par `rule_source_check.py --network`.
