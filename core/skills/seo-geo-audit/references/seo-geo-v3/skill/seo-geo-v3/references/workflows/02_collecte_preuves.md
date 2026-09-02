# 02 — Collecte et registre de preuves

## Objectif

Constituer une base de preuves reproductible avant interprétation. Séparer strictement collecte déterministe et raisonnement.

## Entrées minimales

- `client_id`, `run_id`, périmètre validé et consentement.
- Liste des actifs et accès autorisés.
- Configuration de collecte : user-agent, appareil, locale, profondeur, cadence et limites.

## Règle de provenance

Enregistrer chaque preuve avec : `evidence_id`, source, URL ou système, méthode, horodatage UTC, portée, statut HTTP si applicable, type MIME, extrait, empreinte du brut, outil/version, locale, appareil et éventuelle erreur. Une capture sans provenance n'est pas une preuve exploitable.

Le collecteur HTTP fourni résout l’hôte avant chaque connexion, refuse toute réponse DNS non publique, puis épingle la socket à l’adresse numérique validée. Le nom d’hôte original reste utilisé pour `Host`, SNI et la validation du certificat TLS. Les proxys d’environnement, tunnels et changements d’origine sont refusés afin de bloquer les contournements SSRF et le DNS rebinding.

## Procédure

1. Résoudre l'origine canonique du domaine cible avant tout crawl : suivre les redirections initiales (`http` vers `https`, apex vers `www` ou l'inverse) et retenir l'URL finale stable comme `root_url`, en conservant chaque redirection comme preuve. Créer ensuite un manifeste de collecte immuable et enregistrer la configuration.
2. Collecter sans interpréter :
   - réponses HTTP, en-têtes, redirections et HTML brut ;
   - DOM rendu lorsque JavaScript peut modifier le contenu ;
   - `robots.txt`, sitemaps déclarés/découverts et directives robots ;
   - canonicals, hreflang, données structurées, métadonnées et liens ;
   - exports autorisés GSC, GA4, Bing, GBP, CMS, CRM et logs ;
   - résultats d'outils tiers avec paramètres et date.
3. Conserver le brut ou, si impossible, son empreinte, un extrait fidèle et la méthode de récupération.
4. Détecter login walls, consent walls, erreurs temporaires, soft 404, contenu différent brut/rendu et user-agents usurpés.
5. Vérifier les robots IA par fonction : recherche, récupération utilisateur et entraînement. Ne pas déduire qu'un blocage garantit l'absence de toute mention ou de tout lien.
6. Dédoublonner par URL normalisée et empreinte sans perdre les variantes temporelles, linguistiques ou techniques.
7. Enregistrer chaque échec comme événement, jamais comme valeur nulle favorable ou défavorable.
8. Produire un bilan de couverture avant de lancer les analyses.

En cas d'échec de mesure temporaire, suivre le « Protocole en cas d'échec de mesure » de `core/00_REGLES_COMMUNES_V3.md`.

## Sorties structurées

- `collection_manifest` : configuration, version, durée, volumes et limites.
- `evidence.jsonl` : une preuve atomique par ligne.
- `crawl_inventory` : URL, découverte, statut, indexabilité déclarée, rendu et empreinte.
- `access_matrix` : moteur/crawler, fonction, règle robots, vérification réseau éventuelle et confiance.
- `coverage_report` : attendu, observé, échantillonné, manquant, erreur et cause.
- `collection_events` : reprises, throttling, blocages, erreurs et décisions.

## Vérifications

- Rejouer un échantillon d'URL et comparer statut, contenu et empreinte.
- Vérifier plusieurs URL supposées 404 pour identifier les soft 404.
- Comparer HTML brut et rendu sur les templates importants.
- Vérifier que les exports couvrent la période et les dimensions annoncées.
- Ne jamais présenter `site:` comme un décompte fiable d'indexation ; privilégier GSC et les preuves d'URL.
- Distinguer données terrain Core Web Vitals et tests laboratoire.

## Critères d'arrêt

- Suspendre en cas de risque de surcharge, blocage explicite, dépassement du périmètre ou doute sur l'autorisation.
- Suspendre l'usage d'une intégration si ses conditions interdisent l'automatisation prévue.
- Ne pas lancer l'analyse si la couverture des templates critiques est inconnue ; compléter ou déclarer un audit partiel.
- Ne jamais modifier un actif pendant cette phase.
