# Outils de vérification externes — Couche déterministe anti-hallucination

## Pourquoi ce fichier existe

Le kit Roso est intégralement no-code et passe par Claude (Claude in Chrome + Web Search + Web Fetch) pour collecter et analyser. Même avec les 7 garde-fous et la double-vérification des affirmations négatives, **un LLM peut encore halluciner sur certains checks factuels** (par exemple : déclarer un sitemap absent alors qu'il existe, donner un mauvais code HTTP, mal lire une longueur de title).

L'état de l'art (JeffLi1993/seo-audit-skill, claude-seo.md) utilise une couche de scripts pour les checks déterministes. On reproduit ce principe **sans casser le no-code** : tu copies-colles les résultats d'outils web gratuits dans Claude, et Claude les lit comme une source factuelle, pas comme une déduction.

Résultat : zéro hallucination possible sur les facts. Claude ne "déduit" plus, il "lit".

---

## Quand utiliser ces outils

À l'**Étape 1 de chaque agent** qui touche à des éléments techniques (Agents 03, 06, 07, 08, 09). Tu lances l'outil en parallèle de Claude in Chrome, tu copies le résultat dans la conversation, puis Claude utilise cette donnée comme **fait confirmé** (statut "Confirmé" dans le triple statut).

---

## Checklist des 10 vérifications déterministes recommandées

### 1. Statut HTTP de la homepage et URLs clés
**Outil** : [httpstatus.io](https://httpstatus.io/)
**Ce que tu vérifies** : code 200 / 301 / 302 / 404 / 500 + chaîne de redirections.
**À copier dans Claude** : la table de redirections complète (URL initiale → URL finale + statuts intermédiaires).

### 2. Robots.txt
**Outil** : `https://[ton-domaine.com]/robots.txt` (direct dans le navigateur) + [Search Console robots.txt tester](https://www.google.com/webmasters/tools/robots-testing-tool)
**Ce que tu vérifies** : présence du fichier, règles Allow/Disallow, mention du sitemap, blocage éventuel des bots IA (GPTBot, ClaudeBot, PerplexityBot, etc.).
**À copier dans Claude** : le contenu intégral du robots.txt.

### 3. Sitemap.xml
**Outil** : `https://[ton-domaine.com]/sitemap.xml` + [XML Sitemap Validator (sitemap.xml-checker)](https://www.xml-sitemaps.com/validate-xml-sitemap.html)
**Ce que tu vérifies** : existence, nombre d'URLs, dernière modification, validité du XML.
**À copier dans Claude** : URL du sitemap + nombre d'URLs déclarées + 5-10 URLs échantillon.

### 4. Validation Schema / Structured Data
**Outil** : [Schema Markup Validator (officiel schema.org)](https://validator.schema.org/) + [Google Rich Results Test](https://search.google.com/test/rich-results)
**Ce que tu vérifies** : présence de JSON-LD, types détectés (Organization, LocalBusiness, FAQPage, Article, Product, etc.), erreurs et warnings.
**À copier dans Claude** : liste des types schema détectés + erreurs éventuelles.

### 5. PageSpeed / Core Web Vitals
**Outil** : [PageSpeed Insights](https://pagespeed.web.dev/)
**Ce que tu vérifies** : scores mobile et desktop, LCP, INP, CLS, taille DOM, opportunités prioritaires.
**À copier dans Claude** : les 4 scores (Perf / Accessibilité / Best Practices / SEO) + les 3 opportunités principales.

### 6. Indexation Google de la marque et des pages-clés
**Outil** : Google direct avec opérateurs avancés
- `site:[ton-domaine.com]` → nombre de pages indexées
- `"[Nom Marque]"` → mentions externes
- `site:[ton-domaine.com] [mot-clé principal]` → vérifier le ranking d'une page sur une requête
**À copier dans Claude** : nombre approximatif de pages indexées + 5 premiers résultats pour la marque.

### 7. Présence Google Business Profile (si business local)
**Outil** : [google.com/business](https://www.google.com/business/) ou recherche directe Google "[Nom Marque] [Ville]"
**Ce que tu vérifies** : présence du GBP, nombre d'avis, note moyenne, photos, posts récents, catégorie principale.
**À copier dans Claude** : capture des infos GBP visibles dans le knowledge panel Google.

### 8. Avis Trustpilot / Google / sectoriel
**Outil** : recherche directe sur [Trustpilot](https://www.trustpilot.com/) + Google Maps + plateformes sectorielles (Booking, TripAdvisor, etc. selon le secteur)
**Ce que tu vérifies** : nombre d'avis total, note moyenne, dernier avis daté, taux de réponse aux avis.
**À copier dans Claude** : note + nombre d'avis + date du dernier avis.

### 9. Mentions Reddit
**Outil** : Google avec `site:reddit.com "[Nom Marque]"` + Reddit search direct
**Ce que tu vérifies** : présence sur Reddit (subreddit, threads, AMA), polarité des mentions.
**À copier dans Claude** : 3-5 threads les plus récents/pertinents trouvés.

### 10. llms.txt
**Outil** : `https://[ton-domaine.com]/llms.txt` (direct dans le navigateur)
**Ce que tu vérifies** : existence du fichier, contenu, présence d'une version `llms-full.txt`.
**À copier dans Claude** : contenu intégral si présent, ou confirmation 404 si absent.

---

## Comment intégrer ces checks au flow normal du kit

### Avant chaque agent technique (03, 07, 08, 09)

1. Tu exécutes les checks pertinents listés ci-dessus (5-10 min).
2. Tu copies les résultats bruts dans la conversation Claude.
3. Tu lances l'agent en précisant : "Voici les checks externes que j'ai effectués, à utiliser comme sources confirmées (statut Confirmé) dans ton analyse :"
4. L'agent intègre ces données comme faits vérifiés, pas comme déductions.

### Bénéfices

- **Statut "Confirmé"** au lieu de "Déduit" sur les éléments critiques → fiabilité maximale
- **Impossible d'halluciner** sur un fait que tu as toi-même copié-collé
- **Audit reproductible** : un autre utilisateur sur le même site obtient les mêmes données factuelles
- **Cohérence avec la Règle 6** (double-vérification des affirmations négatives) renforcée par une 3ᵉ couche externe

---

## Mode rapide (5 min) vs Mode complet (15-20 min)

### Mode rapide (5 min) — checks minimums recommandés avant de lancer la squad

1. Statut HTTP homepage (#1)
2. PageSpeed mobile (#5)
3. site:[domaine.com] sur Google (#6)

### Mode complet (15-20 min) — checks avant le mode complet

Les 10 checks ci-dessus. Tu sauvegardes les résultats dans un document partagé pour les re-injecter dans plusieurs agents.

---

## Référence avec les Règles communes du kit

- **Règle 1 (Anti-hallucination)** : ces outils éliminent le risque résiduel d'hallucination sur les checks factuels.
- **Règle 4 (Triple statut)** : un résultat collé d'un outil externe = statut "Confirmé".
- **Règle 6 (Double-vérification des affirmations négatives)** : un check externe constitue une preuve de niveau supérieur.

---

## Limites honnêtes

- Ces outils sont gratuits mais peuvent avoir des limites de requêtes/jour (PageSpeed limite à ~25 req/h en API, illimité en web).
- Certains outils ne fonctionnent pas derrière un firewall d'entreprise (rare mais possible).
- Trustpilot/GBP peuvent demander un compte pour certaines vues détaillées.
- Aucun de ces outils ne donne le ranking exact sur Google → utiliser GSC (Search Console) si l'utilisateur l'a connecté.

---

Si tu ne veux pas faire ces checks externes, le kit fonctionne quand même — mais sache que la fiabilité globale passe d'~9/10 (mode rigoureux) à ~7,5/10 (mode "tout-LLM"). C'est le seul vrai trade-off du kit.
