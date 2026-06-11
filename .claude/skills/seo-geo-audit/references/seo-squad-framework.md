# SEO/GEO Audit Framework

Référence condensée issue du framework Roso SEO Squad. À lire pour un audit compact, ciblé ou `--ship-gate` à enjeu SEO.

Pour `--full`, `--squad`, `/seo-geo-squad` ou toute demande "11 agents", charger le pack complet dans `references/seo-squad/` et traiter les prompts agents comme sources autoritaires.

## Séquence complète

| Phase | Nom | Sortie |
|---:|---|---|
| 1 | Data Collector | Brief Site avec preuves, statut et niveau de confiance |
| 2 | Stratégie & Positionnement SEO/GEO | Offre, cible, différenciation, angles business |
| 3 | Homepage & On-page | H1, title, meta, CTA, preuve, structure visible |
| 4 | SEO Technique & Données Structurées | indexabilité, robots, sitemap, canonical, schema, CWV |
| 5 | Keyword & Intent Research | 20 requêtes max, SERP intent, prompts conversationnels |
| 6 | Analyse Concurrentielle | écarts par rapport aux concurrents et formats SERP |
| 7 | Content SEO/GEO | pages business, FAQ, guides, contenus citables IA |
| 8 | Autorité, Brand & Local | avis, GBP, NAP, mentions, sociaux, forums |
| 9 | Visibilité IA & Plan d'Action | 25 prompts IA, roadmap, sources à conquérir |
| 10 | Auto-Test IA | score IA /100, Claude + Google AIO confirmés si possible |
| 11 | Rapport final | diagnostic + plan d'implémentation client-friendly |

## Garde-fous communs

- Anti-hallucination: ne jamais inventer ce qui n'a pas été lu.
- Anti-promesse: pas de ranking, trafic, citation IA ou délai garanti.
- Anti-danger: pas de PBN, faux avis, cloaking, doorway pages, keyword stuffing.
- Triple statut: Confirmé / Déduit / Non vérifié.
- Double-vérification des négatifs: test direct + recherche alternative.
- Auto-relecture: corriger contradictions avant sortie.
- Client-friendly: traduire les termes techniques au premier usage.

## Checks déterministes recommandés

| Check | Source gratuite | Confirme |
|---|---|---|
| HTTP status | httpstatus.io ou fetch direct | 200/301/404, redirections |
| robots.txt | `/robots.txt` | crawl, sitemap, bots IA |
| sitemap.xml | `/sitemap.xml` + validator | URLs déclarées, validité XML |
| schema | validator.schema.org + Rich Results Test | JSON-LD, erreurs, warnings |
| PageSpeed | pagespeed.web.dev | Perf, CWV, SEO score |
| Indexation | Google `site:domaine` | pages indexées, marque |
| Google Business Profile | Google/Maps/GBP | local, avis, NAP |
| Avis | Google, Trustpilot, sectoriels | note, volume, fraîcheur |
| Reddit/forums | `site:reddit.com "marque"` | mentions, sources IA |
| llms.txt | `/llms.txt`, `/llms-full.txt` | résumé lisible par IA |

## GEO content rules

- Réponse directe dans le premier paragraphe.
- Sources et citations visibles.
- Statistiques utiles, sourcées et placées tôt.
- FAQ en langage naturel.
- Ton expert mais lisible.
- Pas de keyword stuffing.
- Pages comparatives et alternatives si la SERP le justifie.
- Contenus "citable IA": définitions, tableaux, listes d'étapes, preuves, exemples.

## Grille GEO minimale

| Champ | Description |
|---|---|
| Prompt | requête exacte, sans forcer la marque |
| Plateforme | Claude, Google AIO, ChatGPT, Perplexity, Gemini |
| Marque citée | Oui / Non / À valider |
| Position | première mention / milieu / fin / non citée |
| Lien donné | URL citée ou aucun lien |
| Concurrents cités | marques concurrentes nommées |
| Source #1 | domaine cité ou probable source principale |
| Statut | Confirmé / Estimé Haute / Estimé Moyenne / Estimé Faible / À valider |
| Action | correction pour améliorer la présence |

## Roadmap limits

- 7 jours: 5 actions max, quick wins.
- 30 jours: 10 actions max, chantiers structurants.
- 90 jours: 10 actions max, contenu, autorité, itérations GEO.

Chaque action doit être concrète: verbe + objet + emplacement + impact.

## Ship-gate P0/P1

P0:
- page noindex involontaire;
- robots/sitemap/canonical cassant l'indexation;
- title/H1 absent sur page publique stratégique;
- schema invalide qui casse les rich results critiques;
- contenu IA trompeur, promesse SEO fausse ou technique dangereuse.

P1:
- meta/title faibles sur page business;
- llms.txt manquant sur site explicitement GEO;
- FAQ ou contenu citable absent sur page service centrale;
- données locales NAP incohérentes;
- absence d'action prioritaire pour une faiblesse Confirmée.
