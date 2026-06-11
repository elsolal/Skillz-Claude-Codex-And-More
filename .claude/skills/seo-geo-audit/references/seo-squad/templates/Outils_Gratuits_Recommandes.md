# Outils gratuits recommandés — Roso SEO Squad

> Whitelist officielle des outils gratuits utilisés par la squad. Aucun outil payant n'est requis. Tous sont accessibles via navigateur ou via les connecteurs natifs Claude Pro.

---

## Règle d'or

Tu as besoin de Claude Pro (ou Max / Team) avec **Web Search activée**. C'est le seul prérequis dur. Tout le reste est optionnel mais améliore fortement la profondeur d'analyse.

---

## 1. Outils dans Claude (natifs)

| Outil | Utilisation | Disponibilité |
|-------|-------------|---------------|
| Web Search | Recherche en temps réel, vérifications, présence de la marque | Claude Pro / Max / Team |
| Web Fetch | Lecture d'une page web (HTML non JS-rendered) | Claude Pro / Max / Team |
| Projects | Conteneur du pack avec instructions custom et fichiers ressources | Claude Pro / Max / Team |

**Important** : Web Fetch ne lit pas les sites en pur JavaScript (Single Page Apps non pré-rendus). Dans ce cas, on bascule sur Niveau 3 (collage utilisateur) ou on demande Firecrawl/Playwright MCP.

---

## 2. Extension navigateur (1 seule recommandée)

| Extension | Pourquoi | Lien |
|-----------|----------|------|
| Detailed SEO Extension | Voir d'un coup : title, meta, H1-H6, canonical, schema, robots, sitemap, headers | https://detailed.com/extension/ |

> Aucune autre extension n'est obligatoire. Si tu veux aller plus loin, voir la section "Optionnel" en bas.

---

## 3. Connecteurs MCP recommandés (au choix selon le niveau)

| Connecteur | Pourquoi | Lien officiel |
|------------|----------|---------------|
| Google Search Console MCP | Requêtes, impressions, clics, position moyenne, couverture, Core Web Vitals | github.com/sambettany/mcp-gsc (ou Porter Metrics) |
| Google Analytics 4 | Trafic, pages les plus visitées, taux de rebond, conversions | Via Porter Metrics ou MCP officiel Google |
| Firecrawl | Crawler récursif un site (ou un concurrent en JS) | firecrawl.dev |
| Playwright MCP | Naviguer un site en JS et capturer la page rendue | github.com/microsoft/playwright-mcp |

**Niveau recommandé minimum** : juste GSC. Le reste apporte un confort.

---

## 4. Outils web gratuits (par agent)

### Agent 03 — Audit Homepage / On-Page
| Outil | Usage |
|-------|-------|
| PageSpeed Insights (pagespeed.web.dev) | Score performance + Core Web Vitals |
| Schema Markup Validator (validator.schema.org) | Vérifier la validité du schema JSON-LD |
| Rich Results Test (search.google.com/test/rich-results) | Vérifier l'éligibilité aux résultats enrichis |

### Agent 04 — Keyword & Intent Research
| Outil | Usage |
|-------|-------|
| Google Search Console | Source #1 des données réelles du site |
| Bing Webmaster Tools (Keyword Research) | Volumes mensuels gratuits (qualité moyenne mais utilisable) |
| Keyword Surfer (extension Chrome, gratuit) | Volumes affichés directement dans Google Search |
| AlsoAsked.com | Cartographie des "People Also Ask" |
| AnswerThePublic | Questions autour d'une requête (limité gratuit) |

### Agent 05 — Analyse Concurrentielle
| Outil | Usage |
|-------|-------|
| Web Search | Recherche manuelle sur la marque concurrente |
| Web Fetch | Lire les pages du concurrent |
| Wayback Machine (web.archive.org) | Voir l'évolution d'un site concurrent |
| SimilarWeb (gratuit limité) | Estimation grossière de trafic |

### Agent 06 — Content SEO/GEO
| Outil | Usage |
|-------|-------|
| Web Search | Inspirer les sujets, voir ce qui rank |
| Google Trends (trends.google.com) | Saisonnalité, tendances |
| AlsoAsked, AnswerThePublic | Questions à couvrir |

### Agent 07 — SEO Technique & Données Structurées
| Outil | Usage |
|-------|-------|
| Google Search Console | Indexation, erreurs couverture, Core Web Vitals |
| Bing Webmaster Tools | Vue alternative indexation |
| PageSpeed Insights | Performance, Core Web Vitals |
| Schema Markup Validator | Validité JSON-LD |
| Rich Results Test | Résultats enrichis |
| Site:[domaine] sur Google | Estimer pages indexées |
| robots.txt et sitemap.xml | Lire directement les fichiers |
| Chrome DevTools (F12 → mode mobile) | Test mobile, performance perçue |

### Agent 08 — Autorité, Brand & SEO Local
| Outil | Usage |
|-------|-------|
| Google Business Profile Manager | Voir et modifier la fiche locale |
| Google Maps | Vérifier la présence locale |
| Web Search "site:reddit.com [marque]" | Mentions Reddit |
| Web Search "site:linkedin.com [marque]" | Mentions LinkedIn |
| Wayback Machine | Historique de la marque sur le web |

### Agent 09 — Visibilité IA & Plan d'Action
| Outil | Usage |
|-------|-------|
| ChatGPT (Free, Plus, ou avec Search) | Tester les prompts |
| Perplexity (free) | Tester les prompts + voir les sources citées |
| Google Gemini (free) | Tester les prompts |
| Claude (Pro) | Tester les prompts |
| Google AI Overviews (en SERP Google US/FR) | Tester les requêtes informationnelles |

---

## 5. Outils à NE PAS recommander (anti-patterns)

| Outil | Pourquoi on ne le recommande pas |
|-------|----------------------------------|
| Logiciels d'achat d'avis | Sanctions Google + interdit légalement |
| Fermes de backlinks / PBN | Risque de pénalité manuelle Google |
| Annuaires spammy gratuits (low-quality) | Pas de valeur SEO, parfois pénalisant |
| Outils de cloaking / spinning | Anti-guidelines Google |
| Générateurs de fausses FAQ Schema | Peuvent déclencher une action manuelle |
| Outils "Garanti TOP 1 Google" | Marketing trompeur |

---

## 6. Optionnel — Si l'utilisateur veut creuser

Ces outils ne sont jamais obligatoires. Ils peuvent être intéressants si l'utilisateur est déjà familier ou a un usage avancé.

| Outil | Usage | Coût |
|-------|-------|------|
| Screaming Frog (free jusqu'à 500 URLs) | Crawler son propre site en local | Gratuit jusqu'à 500 URLs |
| Sitebulb (essai gratuit) | Audit technique complet | Essai gratuit |
| Ubersuggest (limité gratuit) | Volumes, idées, audit léger | Gratuit limité |
| Mangools (essai gratuit) | Suite SEO | Essai gratuit |
| Ahrefs Webmaster Tools (gratuit pour son propre site) | Backlinks de son propre site | Gratuit pour son site |

---

## 7. Rappel des principes

- Aucun outil ne remplace le jugement humain ni la lecture des sources réelles.
- Tous les chiffres sortis d'outils gratuits sont des estimations — toujours marquer "Source : [outil]" et "Niveau de confiance : Élevé/Moyen/Faible".
- Le pack fonctionne en mode dégradé sans aucun connecteur MCP : Web Search + Web Fetch + Detailed SEO Extension suffisent pour un premier audit honnête.
- Plus l'utilisateur branche de connecteurs et fournit de captures, plus la précision augmente. Le pack le dit explicitement à chaque agent.
