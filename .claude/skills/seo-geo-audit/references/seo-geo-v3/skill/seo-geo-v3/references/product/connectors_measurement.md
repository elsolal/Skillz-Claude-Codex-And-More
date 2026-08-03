# Connecteurs et mesure V3

Référence datée du **15 juillet 2026**. Un connecteur mesure une surface définie ; aucun connecteur ne représente à lui seul « la visibilité IA ».

## Sommaire

- [Principes de mesure](#principes-de-mesure)
- [Matrice de connecteurs](#matrice-de-connecteurs)
- [Contrat de données](#contrat-de-données-minimal)
- [Cadre de métriques](#cadre-de-métriques)
- [GEO Observatory](#geo-observatory--protocole-reproductible)
- [Scoring V3](#scoring-v3)
- [Contrôles par connecteur](#contrôles-par-connecteur)
- [Alertes](#alertes-recommandées)
- [QA avant reporting](#qa-avant-reporting)

## Principes de mesure

- Utiliser exclusivement les statuts canoniques `observed|proxy|client_reported|inferred|not_measured|unknown` ; l’origine outil/client est portée par la provenance, pas par un statut supplémentaire.
- Conserver les données brutes, la méthode, l’horodatage et la couverture.
- Ne jamais convertir l’absence d’un rapport ou d’un droit d’accès en valeur zéro.
- Ne pas moyenner des dimensions hétérogènes en un score opaque.
- Relier les signaux de visibilité aux comportements puis aux résultats métier, avec limites d’attribution.
- Utiliser la lecture seule par défaut et documenter la révocation des accès.

## Matrice de connecteurs

| Connecteur | Mesure | Maturité au 15/07/2026 | Accès minimal | Fallback |
|---|---|---|---|---|
| Google Search Console — Performance | Clics, impressions, requêtes, pages, pays, appareils | Stable | Lecture de la propriété exacte | Export fourni par le client ; signaler limites de rétention/échantillonnage applicables. |
| GSC — Generative AI performance | Impressions issues des fonctionnalités génératives de Google Search, pages, pays, appareils | Déploiement à un **sous-ensemble** de propriétés | Lecture si le rapport existe | `not_measured` si le rapport n’est pas accessible dans le run ; documenter la cause connue ou `unknown`, sans inférer zéro visibilité. |
| Bing Webmaster Tools — AI Performance | Citations, URLs citées, activité et requêtes de grounding selon disponibilité | **Public Preview** | Lecture | Export manuel ou panel SEO/GEO Squad qualifié de test. |
| Google Analytics 4 | Sessions, événements, conversions et sources référentes | Stable, dépend du marquage et du consentement | Lecture | Logs serveur/CRM agrégés ; sinon `not_measured` ou `unknown` selon la cause documentée. |
| CRM / ventes | Leads, qualité, pipeline, ventes et revenu | Variable | Lecture limitée aux champs utiles | Export anonymisé avec dictionnaire de champs. |
| Logs serveur/CDN/WAF | Crawl réel, statuts, fréquence, bot et blocages | Stable mais sensible | Lecture filtrée | Tests HTTP ponctuels ; signaler absence de preuve historique. |
| Collecteur léger SEO/GEO Squad | Échantillon HTTP/HTML brut, robots, canonicals, langue, comptage JSON-LD et liens | Contrôlé par SEO/GEO Squad | Domaine et limites autorisés | Ne rend pas JavaScript ; compléter avec un outil spécialisé lorsque nécessaire. |
| PageSpeed Insights / CrUX | Données de terrain et diagnostics labo | Stable selon couverture | Public/API | Lighthouse local, qualifié de lab. |
| Google Business Profile | Découverte et actions locales | Stable, disponibilité selon API/rôle | Lecture établissement | Observation publique, sans métriques privées. |
| Merchant Center / flux | Produits, erreurs, prix, stock et diffusion | Stable | Lecture compte/flux | Crawl du catalogue public, sans prétendre couvrir la diffusion. |
| Panel GEO Observatory | Mentions, citations, sources, narration sur prompts définis | Mesure propriétaire expérimentale | Compte/sessions conformes aux conditions des plateformes | Recherche manuelle documentée. |
| Search interne / support | Langage, besoins et échecs réels | Variable et potentiellement personnel | Export minimisé | Entretiens et échantillon anonymisé. |

Sources officielles :

- GSC Generative AI : https://support.google.com/webmasters/answer/16984139
- Bing AI Performance : https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview
- Search Console API : https://developers.google.com/webmaster-tools
- Google Analytics : https://developers.google.com/analytics
- PageSpeed Insights API : https://developers.google.com/speed/docs/insights/v5/get-started
- Chrome UX Report : https://developer.chrome.com/docs/crux
- IndexNow : https://www.indexnow.org/documentation

## Contrat de données minimal

Chaque observation doit inclure :

```json
{
  "observation_id": "obs_...",
  "tenant_id": "client_...",
  "source": "gsc|bing|ga4|crm|logs|crawl|geo_panel",
  "source_version": "...",
  "observed_at": "2026-07-15T10:00:00+02:00",
  "period_start": "2026-06-15",
  "period_end": "2026-07-14",
  "scope": {
    "property": "https://example.com/",
    "country": "FR",
    "locale": "fr-FR",
    "device": "mobile"
  },
  "metric": "citation_rate",
  "dimension": "V",
  "value": 0.24,
  "unit": "ratio",
  "measurement_state": "observed|proxy|client_reported|inferred|not_measured|unknown",
  "evidence_ids": ["ev_..."],
  "limitations": ["panel de 25 prompts"]
}
```

Définition stricte des statuts :

- `observed` : valeur collectée directement dans une source ou un run, avec preuve ;
- `proxy` : signal observé utilisé pour approximer une autre réalité, avec relation explicitée ;
- `client_reported` : valeur communiquée par le client mais non vérifiée directement ;
- `inferred` : conclusion dérivée de preuves, non observée telle quelle ;
- `not_measured` : mesure volontairement non exécutée, hors périmètre ou indisponible pendant le run ;
- `unknown` : état impossible à déterminer en raison d’un manque, conflit ou contexte ambigu.

Ne jamais remplir `0` lorsque `measurement_state` vaut `not_measured` ou `unknown`. Ne pas remplacer `client_reported` ou `inferred` par `observed` sans nouvelle preuve directe.

## Cadre de métriques

### F — Fondations

- couverture crawlée et couverture connue ;
- URLs indexables, exclues, en erreur et orphelines ;
- canonicals, hreflang, redirections, liens cassés et profondeur ;
- Core Web Vitals de terrain, séparés des scores labo ;
- accessibilité crawler et rendu ;
- données structurées valides/éligibles ;
- santé des flux locaux et marchands.

### V — Visibilité observée

Pour un panel donné :

- **Mention rate** = réponses mentionnant l’entité / réponses valides ;
- **Citation rate** = réponses contenant au moins une citation vers le domaine / réponses valides ;
- **Citation share** = citations du domaine / citations de tous domaines dans le panel ;
- **Prompt coverage** = prompts avec au moins une présence / prompts valides ;
- **Source diversity** = nombre de domaines sources uniques, accompagné de la distribution ;
- **Narrative accuracy** = faits testés correctement restitués / faits testés ;
- **Sentiment/tonalité** = catégorie annotée avec protocole et vérification humaine ;
- **Volatility** = variation entre runs comparables.

Toujours afficher le dénominateur et le panel. Séparer prompts brandés/non brandés, informationnels/commerciaux et étapes du funnel. L’exactitude narrative est une sous-métrique de **V**, jamais une sixième dimension autonome.

### O — Opportunité

- demande first-party non couverte par une page ou une preuve adaptée ;
- prompts commerciaux où concurrents/sources tierces dominent ;
- sources influentes pertinentes mais absentes du graphe d’autorité ;
- écarts par persona, funnel, marché, langue, produit ou établissement ;
- valeur métier potentielle, documentée par données client ou hypothèse explicite ;
- faisabilité et horizon de l’opportunité, sans les confondre avec la qualité actuelle du site.

Un score O élevé signifie **potentiel d’opportunité élevé**, pas « mauvaise performance ». Ne jamais convertir une opportunité en prévision de revenu sans modèle et hypothèses validés.

### E — Exécution

- part des actions avec propriétaire, échéance et critère d’acceptation ;
- dépendances, accès et capacité technique disponibles ;
- état canonique `backlog|ready|in_progress|in_review|done|blocked|cancelled` des actions ; les décisions `approved`, `rejected` et `validated` sont des événements append-only dans `events.jsonl`, pas des statuts d'action ;
- couverture staging, sauvegarde, QA et rollback ;
- délai de traitement et taux d’actions validées ;
- charge, budget et gouvernance réellement confirmés.

E mesure la maturité et l’avancement d’exécution, pas l’impact Search ou business.

### M — Qualité de mesure

- couverture des sources attendues ;
- fraîcheur des données ;
- répétitions et variance ;
- proportion de preuves directes ;
- répartition des statuts `observed|proxy|client_reported|inferred|not_measured|unknown` ;
- nombre de conflits détectés/résolus ;
- version des connecteurs et erreurs de collecte.

M accompagne chaque lecture de F, V, O et E. Une faible qualité M interdit une conclusion précise, même si une autre dimension contient un chiffre.

### Suivi des résultats métier — hors scoring et hors performance F/V/O/E/M

- trafic référent des assistants ;
- conversions directes et assistées ;
- leads qualifiés, pipeline et revenus ;
- appels, réservations, achats ou abonnements ;
- coût et délai d’implémentation.

Présenter ces résultats comme indicateurs d’outcome séparés, avec statut de mesure, attribution et limites. Ils ne composent aucun score SEO/GEO Squad, aucune dimension de performance F/V/O/E/M et ne sont pas une sixième dimension. L’exactitude ou l’erreur narrative reste dans **V** ; le coût et le délai peuvent éclairer **E** mais les résultats business bruts restent hors scoring.

Pour ChatGPT, OpenAI indique l’ajout de `utm_source=chatgpt.com` dans les URLs référentes. Vérifier les dimensions GA4, les redirections et la conservation du paramètre : https://help.openai.com/en/articles/12627856-publishers-and-developers-faq

## GEO Observatory : protocole reproductible

### Construire le panel

Alimenter les prompts depuis : GSC, recherche interne, support, CRM, appels sales, People Also Ask, études clients et hypothèses synthétiques clairement marquées.

Pour chaque prompt, enregistrer :

- identifiant stable et texte exact ;
- langue, marché, persona et étape du funnel ;
- brandé ou non brandé ;
- origine `first_party|search_data|research|synthetic` ;
- priorité métier et fait(s) à vérifier ;
- date d’ajout et propriétaire.

### Exécuter

Enregistrer pour chaque run :

- plateforme et produit exact ;
- modèle/version lorsqu’affiché ;
- date, heure et fuseau ;
- pays, locale et langue ;
- type de compte et état de connexion ;
- conversation neuve ou historique ;
- personnalisation/mémoire activée ou non ;
- recherche web activée ou non ;
- texte exact de la réponse ;
- liens, domaines, extraits cités et ordre visible ;
- captures ou export autorisé ;
- erreurs, refus et latence.

Répéter au moins trois fois les prompts critiques lorsque le budget et les conditions des plateformes le permettent. Ce nombre améliore l’observation de variance mais ne crée pas, à lui seul, un intervalle de confiance statistique.

### Neutralité

- Ne pas tester dans un projet/conversation préchargé avec les documents du client pour mesurer une visibilité spontanée.
- Séparer session propre, test brandé et test assisté.
- Ne pas utiliser les résultats Google comme proxy direct de ChatGPT, Claude, Perplexity ou Gemini.
- Ne pas automatiser en violation des conditions d’utilisation d’une plateforme.
- Conserver les réponses divergentes ; ne pas sélectionner seulement la meilleure.

### Annoter

Au moins deux états pour chaque champ : valeur et confiance. Les faits sensibles — prix, dirigeant, adresse, caractéristiques, santé, droit — exigent une validation contre le Digital Twin approuvé.

## Scoring V3

Ne jamais produire un score unique comme seule conclusion. Afficher exactement cinq dimensions séparées :

1. **F — Fondations** : santé technique et disponibilité des actifs nécessaires ;
2. **V — Visibilité** : présence observée, citations, sources, tonalité, volatilité et exactitude narrative ;
3. **O — Opportunité** : potentiel priorisé, sans le présenter comme performance actuelle ;
4. **E — Exécution** : maturité, avancement, risques et capacité d’implémentation ;
5. **M — Qualité de mesure** : couverture, fraîcheur, méthode, provenance et incertitude.

Afficher les résultats métier dans un bloc distinct, **hors score**. Ne jamais créer de moyenne globale F/V/O/E/M : les sens, unités et niveaux de preuve diffèrent.

Une synthèse directionnelle peut utiliser `Rouge / Orange / Vert` seulement si : seuils publiés, métriques homogènes, données suffisantes et absence de fausse précision. `N/D` reste une sortie valide.

## Contrôles par connecteur

### Search Console Generative AI

- Vérifier si le rapport est visible sur la propriété.
- S’il est absent, distinguer déploiement non disponible, volume insuffisant et exclusion éventuelle.
- Enregistrer pages, pays, appareils, période et évolution disponibles.
- Ne pas inventer de requêtes si le rapport ne les fournit pas.
- Conserver la mention « déployé à un sous-ensemble » jusqu’à mise à jour officielle.

### Bing AI Performance

- Afficher le badge `Public Preview`.
- Versionner les champs et gérer leur disparition/changement.
- Conserver citations, URLs citées et périodes selon ce qui est effectivement exposé.
- Ne pas extrapoler à l’ensemble de Microsoft ou du marché IA.

### Logs et crawlers

- Vérifier bot par User-Agent **et** méthode officielle/IP lorsque disponible.
- Distinguer search, user fetch, training et agents.
- Détecter 2xx vides, 3xx, 4xx, 5xx, challenges WAF et budgets de crawl.
- Hasher ou minimiser les URLs contenant des identifiants/données personnelles.
- Ne pas stocker cookies, authorization headers ou query strings sensibles.

### GA4 et CRM

- Définir événements et conversions avec le client.
- Conserver source/medium/campaign et landing page.
- Dédupliquer leads et ventes selon une règle documentée.
- Séparer attribution directe, assistée et influence déclarative.
- N’envoyer aucune donnée personnelle brute à un modèle.

## Alertes recommandées

- chute anormale d’impressions/citations sur période comparable ;
- nouvelle erreur narrative critique ;
- source dominante perdue ou gagnée ;
- changement robots/WAF affectant un crawler ;
- rapport/connecteur devenu indisponible ;
- croissance d’URLs exclues, orphelines ou en erreur ;
- divergence prix/stock/adresse/dirigeant ;
- hausse des conversions sans tracking attribuable, ou inversement ;
- données trop anciennes pour soutenir une recommandation.

Chaque alerte doit contenir preuve, seuil, fenêtre, impact potentiel, confiance et action recommandée. Une alerte n’est pas une causalité.

## QA avant reporting

- [ ] Fuseau, dates et périodes sont explicites.
- [ ] Droits et couverture de chaque connecteur sont enregistrés.
- [ ] Chaque valeur utilise un statut canonique `observed|proxy|client_reported|inferred|not_measured|unknown`.
- [ ] `not_measured` et `unknown` sont affichés `N/D`, jamais zéro.
- [ ] Données de terrain et laboratoire sont séparées.
- [ ] Panel, dénominateurs et répétitions sont visibles.
- [ ] Chaque plateforme est mesurée séparément.
- [ ] Les composants preview/expérimentaux portent un badge.
- [ ] Les réponses IA utilisées comme preuve sont archivées avec leur contexte.
- [ ] Les données métier sont agrégées/minimisées et restent hors score F/V/O/E/M.
- [ ] L’exactitude narrative est classée sous V, pas comme dimension autonome.
- [ ] Aucune promesse de classement, citation ou revenu n’est déduite d’une dimension.
