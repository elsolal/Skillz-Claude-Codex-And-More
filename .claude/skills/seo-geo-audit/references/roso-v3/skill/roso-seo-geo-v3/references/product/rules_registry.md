# Registre des règles SEO, GEO et agentiques

Référence produit datée du **15 juillet 2026**. Relire les sources officielles avant chaque audit : les fonctionnalités de recherche générative évoluent rapidement.

## Sommaire

- [Mode d’emploi](#mode-demploi)
- [Règles fondamentales](#règles-fondamentales)
- [Contenu, données structurées et llms.txt](#contenu-données-structurées-et-llmstxt)
- [Exploration, indexation et diagnostic](#exploration-indexation-et-diagnostic)
- [Matrice officielle des crawlers](#matrice-officielle-des-crawlers)
- [Mesure IA et fonctionnalités émergentes](#mesure-ia-et-fonctionnalités-émergentes)
- [Règles de formulation client](#règles-de-formulation-client)
- [Processus de mise à jour](#processus-de-mise-à-jour)

## Mode d’emploi

Attribuer à chaque règle un identifiant stable et un statut :

- **EXIGÉ** : condition technique, légale ou contractuelle vérifiable.
- **RECOMMANDÉ** : bonne pratique fondée sur une source officielle ou des observations suffisamment robustes.
- **CONDITIONNEL** : utile seulement pour certains sites, marchés ou produits.
- **EXPÉRIMENTAL** : hypothèse à tester, jamais présentée comme facteur établi.
- **RETIRÉ** : ne plus vendre ni produire comme fonctionnalité active.

Pour toute conclusion, enregistrer `rule_id`, source, date de vérification, périmètre, preuve et niveau de confiance. Ne jamais transformer une corrélation en causalité.

## Règles fondamentales

| ID | Statut | Règle opérationnelle | Conséquence V3 |
|---|---|---|---|
| CORE-01 | EXIGÉ | Aucun outil tiers ne dispose des métriques internes de classement de Google ou de ses systèmes IA. | Qualifier les scores RosoAI de mesures, estimations ou proxys ; ne jamais les nommer « score Google ». |
| CORE-02 | EXIGÉ | Être explorable et conforme ne garantit ni crawl, ni indexation, ni classement, ni citation. | Interdire les promesses de résultat et afficher les limites dans chaque livrable. |
| CORE-03 | RECOMMANDÉ | Les fondamentaux SEO restent applicables aux fonctionnalités génératives de Google Search. | Traiter le GEO comme une couche de visibilité et de mesure complémentaire, pas comme un remplacement du SEO. |
| CORE-04 | RECOMMANDÉ | Produire un contenu utile, original, non interchangeable, démontrant expérience et expertise réelles. | Prioriser preuves, données propriétaires, exemples, auteurs et points de vue ; éviter les résumés génériques. |
| CORE-05 | EXIGÉ | La production automatisée à grande échelle sans valeur ajoutée peut relever du spam. | Soumettre toute génération en volume à un contrôle éditorial, à une justification utilisateur et à une validation humaine. |
| CORE-06 | RECOMMANDÉ | Il n’existe pas de longueur idéale, de nombre obligatoire de H2, de densité de mots-clés ou d’emplacement universel du mot-clé. | Transformer les anciennes règles absolues en heuristiques conditionnelles. |

Sources :

- Google, optimisation pour la recherche générative : https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Google, outils et conseils SEO tiers : https://developers.google.com/search/docs/fundamentals/third-party-seo
- Google, contenu généré par IA : https://developers.google.com/search/docs/fundamentals/using-gen-ai-content

## Contenu, données structurées et `llms.txt`

| ID | Statut | Règle opérationnelle | Conséquence V3 |
|---|---|---|---|
| CNT-01 | EXPÉRIMENTAL | `llms.txt` est une proposition communautaire, pas une exigence universelle. Google Search l’ignore : sa présence n’aide ni ne pénalise la visibilité Google. | Le générer seulement sur demande ou dans un test documenté ; ne jamais le vendre comme levier prioritaire ou facteur Google. |
| CNT-02 | RETIRÉ | Le résultat enrichi FAQ n’est plus affiché dans Google Search depuis le 7 mai 2026. | Retirer toute promesse de rich result FAQ. Une FAQ peut rester utile aux humains ; ne pas justifier sa création par cet ancien affichage. |
| CNT-03 | RECOMMANDÉ | Les données structurées doivent correspondre au contenu visible et aux types actuellement pris en charge. | Valider le JSON-LD et distinguer « balisage valide », « éligible » et « affiché » ; l’affichage n’est jamais garanti. |
| CNT-04 | EXIGÉ | Google n’exige aucun balisage Schema.org spécial pour ses réponses génératives. | Refuser les schémas « GEO » inventés ; utiliser les types pertinents pour Search, commerce et entités. |
| CNT-05 | CONDITIONNEL | Les contenus FAQ, glossaires et comparatifs peuvent faciliter la compréhension si la demande utilisateur les justifie. | Décider à partir du besoin, des preuves et du parcours, pas d’un quota de formats. |
| CNT-06 | RECOMMANDÉ | Images, vidéos, profils locaux et données marchandes peuvent créer des surfaces supplémentaires de découverte. | Activer les modules selon le vertical et mesurer séparément chaque surface. |

Sources :

- Google, clarification `llms.txt` et retrait FAQ : https://developers.google.com/search/updates
- Google, données structurées : https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data
- Proposition `llms.txt` : https://llmstxt.org/

## Exploration, indexation et diagnostic

| ID | Statut | Règle opérationnelle | Conséquence V3 |
|---|---|---|---|
| TECH-01 | EXIGÉ | Un audit technique sérieux requiert un crawl couvrant le périmètre convenu, puis des vérifications serveur et rendues lorsque nécessaire. | Ne pas appeler un échantillon de 3 à 5 pages « crawl complet ». Afficher couverture, exclusions et date. |
| TECH-02 | RECOMMANDÉ | Contrôler statuts HTTP, redirections, canonicals, noindex, robots, sitemaps, profondeur, pages orphelines, liens cassés, doublons, facettes, pagination, hreflang et rendu JavaScript. | Produire des preuves URL par URL et agréger sans masquer les exceptions. |
| TECH-03 | EXIGÉ | `site:` n’est pas un compteur fiable de pages indexées. | Utiliser l’inspection et les rapports Search Console ; qualifier `site:` de contrôle exploratoire uniquement. |
| TECH-04 | EXIGÉ | Soumettre une URL ou un sitemap ne force pas l’exploration ou l’indexation. | Écrire « demander une exploration » et non « forcer l’indexation ». |
| TECH-05 | EXIGÉ | Un code 200 peut correspondre à une page de connexion, une soft 404, un challenge WAF ou une réponse vide. | Valider statut, contenu, rendu, canonical et contexte avant de conclure « accessible ». |
| TECH-06 | RECOMMANDÉ | Vérifier l’identité d’un crawler avec DNS/IP publiées ou mécanismes officiels, car un User-Agent peut être usurpé. | Ne pas autoriser un bot au WAF sur le seul User-Agent. Conserver la méthode de vérification. |
| TECH-07 | EXIGÉ | Les Core Web Vitals de terrain et les tests Lighthouse de laboratoire ne mesurent pas la même chose. | Présenter séparément données CrUX/GSC et diagnostics Lighthouse. |

Sources :

- Google, opérateur `site:` : https://developers.google.com/search/docs/monitor-debug/search-operators/all-search-site
- Google, demander une nouvelle exploration : https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl
- Google, vérification des crawlers : https://developers.google.com/crawling/docs/crawlers-fetchers/verify-google-requests
- Google, Core Web Vitals : https://developers.google.com/search/docs/appearance/core-web-vitals

## Matrice officielle des crawlers

Ne jamais regrouper « recherche », « requête utilisateur » et « entraînement » sous un même libellé.

| Écosystème | Agent/token | Usage déclaré | Interprétation V3 |
|---|---|---|---|
| Google | `Googlebot` | Exploration pour Google Search, y compris les surfaces génératives de Search. | Son blocage peut affecter l’éligibilité Search ; tester robots, rendu et journaux. |
| Google | `Google-Extended` | Contrôle d’usage pour l’entraînement futur de Gemini et certains usages de grounding hors effet sur Search. Ce n’est pas un User-Agent HTTP séparé. | Ne pas affirmer qu’un blocage modifie le classement ou l’inclusion Google Search. |
| OpenAI | `OAI-SearchBot` | Découverte de contenu pour résumés et extraits de ChatGPT Search. | L’autoriser peut favoriser la découvrabilité ; aucune citation n’est garantie. |
| OpenAI | `GPTBot` | Collecte potentielle pour l’entraînement. | Traiter l’autorisation comme un choix de gouvernance distinct de Search. |
| Anthropic | `Claude-SearchBot` | Recherche et amélioration des résultats de recherche. | Son blocage peut réduire visibilité et exactitude, sans prouver une disparition totale. |
| Anthropic | `Claude-User` | Récupération déclenchée par une demande utilisateur. | Gouverner séparément des crawlers d’indexation et d’entraînement. |
| Anthropic | `ClaudeBot` | Collecte potentielle pour l’entraînement. | Choix séparé, documenté avec le client. |
| Perplexity | `PerplexityBot` | Exploration pour la recherche Perplexity. | Vérifier les plages IP officielles si une règle WAF est utilisée. |
| Perplexity | `Perplexity-User` | Récupération initiée par l’utilisateur ; Perplexity indique que ce fetcher ignore généralement `robots.txt`. | Ne pas promettre un contrôle absolu via robots ; traiter sécurité/WAF et accès utilisateur séparément. |

Le blocage d’un crawler peut réduire une capacité d’exploration, mais un service peut parfois découvrir un titre ou une URL par une autre source. Écrire « peut réduire l’éligibilité ou la visibilité », jamais « rend la marque invisible » sans test probant.

Sources :

- Google, liste des crawlers : https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
- OpenAI, éditeurs et développeurs : https://help.openai.com/en/articles/12627856-publishers-and-developers-faq
- Anthropic, bots Claude : https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- Perplexity, crawlers : https://docs.perplexity.ai/docs/resources/perplexity-crawlers

## Mesure IA et fonctionnalités émergentes

| ID | Statut | Règle opérationnelle | Conséquence V3 |
|---|---|---|---|
| MES-01 | CONDITIONNEL | Le rapport Generative AI de Search Console n’est déployé qu’à un sous-ensemble de propriétés au 15 juillet 2026. | Tester sa présence ; si absent, l’indiquer comme « non disponible », pas comme zéro performance. |
| MES-02 | EXPÉRIMENTAL | Bing AI Performance est en Public Preview. | Exploiter citations, pages citées et évolution si disponibles ; versionner le connecteur et prévoir un fallback. |
| MES-03 | EXIGÉ | Une réponse générative varie selon produit, modèle, date, locale, compte, personnalisation et activation de la recherche. | Enregistrer tout le contexte de test et répéter les prompts critiques. |
| MES-04 | EXIGÉ | Un test de prompts synthétiques n’est pas une mesure exhaustive de trafic ou de demande. | Distinguer « panel observé » et « performance réelle ». Ne pas extrapoler une part de marché. |
| MES-05 | EXPÉRIMENTAL | WebMCP, UCP et les protocoles de commerce agentique sont émergents. | Les placer dans un laboratoire ou une readiness assessment, jamais dans le socle obligatoire. |
| MES-06 | CONDITIONNEL | Google Preferred Sources permet aux utilisateurs de choisir un domaine ou sous-domaine et peut mettre ses contenus en avant avec un badge dans Top Stories, AI Mode et AI Overviews. | Vérifier l’éligibilité, proposer un deeplink ou bouton seulement à une audience existante et mesurer l’adoption ; ne jamais garantir une présence ni traiter ce choix utilisateur comme un facteur général de classement. |

Sources :

- Search Console, rapport Generative AI : https://support.google.com/webmasters/answer/16984139
- Bing AI Performance : https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview
- Chrome WebMCP : https://developer.chrome.com/docs/ai/webmcp
- Universal Commerce Protocol : https://ucp.dev/specification/overview/
- OpenAI, Agentic Commerce Protocol : https://openai.com/index/buy-it-in-chatgpt/
- Google Preferred Sources : https://developers.google.com/search/docs/appearance/preferred-sources

## Règles de formulation client

Toujours :

- dater la mesure et nommer la source ;
- distinguer **observé**, **déclaré par le client**, **issu d’un outil**, **proxy** et **non mesuré** ;
- écrire la portée exacte : URLs, marché, langue, appareil et période ;
- afficher les inconnues et limitations ;
- fournir un critère de validation post-implémentation.

Interdire :

- Formulations interdites : « visibilité garantie », « indexation forcée », « détection garantie » ;
- « Google recommande `llms.txt` » ;
- « le balisage FAQ apporte un rich result » ;
- « ce score est votre score Google/ChatGPT » ;
- « cette action générera X € » sans modèle de données, hypothèses et intervalle explicites ;
- toute fausse précision statistique ou « intervalle de confiance » sans protocole statistique réel.

## Processus de mise à jour

1. Vérifier chaque mois Google Search Updates, les documentations des crawlers et les connecteurs actifs.
2. Ouvrir immédiatement une revue lors d’un changement annoncé par Google, Microsoft, OpenAI, Anthropic ou Perplexity.
3. Enregistrer pour chaque règle : `effective_at`, `checked_at`, URL officielle, résumé, impact produit et propriétaire.
4. Marquer les règles affectées `À_REVALIDER` avant toute nouvelle vente ou génération de livrable.
5. Mettre à jour prompts, tests, exemples et supports commerciaux dans la même release.
6. Conserver l’historique : ne jamais écraser silencieusement une règle utilisée dans un ancien audit.
