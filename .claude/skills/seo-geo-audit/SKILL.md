---
name: seo-geo-audit
description: Orchestre un audit SEO/GEO ponctuel ou complet avec la Roso SEO Squad. Utiliser pour audit SEO, visibilité IA, llms.txt, SERP, GSC, schema, contenu, autorité, local SEO, roadmap 7/30/90 ou workflow 11 agents via /seo-geo-squad.
---

# SEO/GEO Audit

Skill portable d'audit SEO + GEO (Generative Engine Optimization) basé sur la Roso SEO Squad. Le dossier `references/seo-squad/` est la source de vérité: il contient le master orchestrator, les règles communes, les prompts dédiés de chaque agent et les templates de livrables. Le présent `SKILL.md` sert d'entrée runtime pour Codex, Claude Code, Gemini, OpenCode et agents compatibles.

## Quand utiliser

- L'utilisateur demande un audit SEO, GEO, visibilité IA, llms.txt, schema, Search Console, SERP, mots-clés, contenu, autorité ou local SEO.
- Une landing, homepage, site vitrine, SaaS, e-commerce, média ou business local doit être audité avant refonte ou livraison.
- Il faut produire une roadmap SEO/GEO 7j / 30j / 90j.
- Il faut tester si une marque est citée par Claude, Google AI Overviews, ChatGPT, Perplexity ou Gemini.
- Il faut transformer un audit en tickets `/dev` ou recommandations client-friendly.
- L'utilisateur demande le workflow complet SEO_Squad, Roso, squad SEO/GEO, ou "les 11 agents".

## Quand NE PAS utiliser

- Audit marketing purement conversion/copy sans recherche organique: utiliser `landing-copy`.
- QA technique d'une app sans enjeu SEO: utiliser `/qa`.
- Audit design-system/UI: utiliser `design-audit`.
- Suivi quotidien de positions/ranking tracking: recommander GSC, Ahrefs, Semrush ou outil dédié; ce skill fait un audit ponctuel.

## Inputs

| Input | Usage |
|---|---|
| URL ou domaine | Surface à auditer |
| Type business | Local / SaaS / e-commerce / B2B / B2C / média / autre |
| Concurrents | Jusqu'à 5 concurrents nommés ou URLs |
| Données | GSC, GA4, PageSpeed, GBP, captures, exports, collages utilisateur |
| Mode | `--quick`, `--full`, `--squad`, `--geo-only`, `--technical`, `--content`, `--ship-gate` |
| Rythme squad | `step-by-step` ou `all-at-once` si mode `--squad` |

Si l'URL ou le type business manque, poser 1 à 3 questions maximum. Sinon avancer avec un statut `Non vérifié` pour les données manquantes.

## Principe d'adaptation portable

Les fichiers SEO_Squad originaux parlent souvent de Claude Pro, Claude in Chrome et Claude Projects. En runtime Skillz-Claude:

- Claude Code peut suivre ces indications directement quand les capacités existent.
- Codex remplace Claude in Chrome par les outils disponibles: browser local, Playwright, Web Search, WebFetch, connecteurs MCP ou captures/collages utilisateur.
- Gemini et OpenCode lisent les mêmes prompts via leurs dossiers provider après installation.
- Si une capacité n'existe pas dans le runtime courant, ne pas simuler le résultat: marquer `Non vérifié` et proposer le check manuel.
- Ne jamais modifier le site audité pendant l'audit. La sortie peut créer des livrables d'audit uniquement si l'utilisateur a demandé un rapport ou si le contexte autorise l'écriture.

## Chargement des références

### Mode compact

Pour `--quick`, `--geo-only`, `--technical`, `--content` ou `--ship-gate`, lire d'abord:

- `references/seo-squad-framework.md`

Puis charger seulement les fichiers complets nécessaires si le diagnostic touche un agent précis.

### Mode complet ou squad

Pour `--full`, `--squad`, "workflow complet", "11 agents", ou `/seo-geo-squad`, les fichiers suivants sont obligatoires et autoritaires. Ne pas résumer leurs règles avant exécution.

Lire d'abord:

1. `references/seo-squad/README.md`
2. `references/seo-squad/00_REGLES_COMMUNES.md`
3. `references/seo-squad/01_MASTER_ORCHESTRATOR.md`
4. `references/seo-squad/Outils_Verification_Externes.md`

Puis lancer les agents dans cet ordre exact:

| Ordre | Agent | Prompt source |
|---:|---|---|
| 1 | Data Collector | `references/seo-squad/agents/01_Data_Collector.md` |
| 2 | Stratégie & Positionnement SEO/GEO | `references/seo-squad/agents/02_Strategie_Positionnement_SEO_GEO.md` |
| 3 | Audit Homepage & On-page | `references/seo-squad/agents/03_Audit_Homepage_On_Page.md` |
| 4 | SEO Technique & Données Structurées | `references/seo-squad/agents/07_SEO_Technique_Donnees_Structurees.md` |
| 5 | Keyword & Intent Research | `references/seo-squad/agents/04_Keyword_Intent_Research.md` |
| 6 | Analyse Concurrentielle | `references/seo-squad/agents/05_Analyse_Concurrentielle.md` |
| 7 | Content SEO/GEO | `references/seo-squad/agents/06_Content_SEO_GEO.md` |
| 8 | Autorité, Brand & SEO Local | `references/seo-squad/agents/08_Autorite_Brand_SEO_Local.md` |
| 9 | Visibilité IA & Plan d'Action | `references/seo-squad/agents/09_Visibilite_IA_Plan_Action.md` |
| 10 | Auto-Test Visibilité IA | `references/seo-squad/agents/09bis_Auto_Test_IA.md` |
| 11 | Master Final Report | `references/seo-squad/agents/10_Master_Final_Report.md` |

Templates disponibles:

- `references/seo-squad/templates/Brief_Site.md`
- `references/seo-squad/templates/Grille_Notation_GEO.md`
- `references/seo-squad/templates/Charte_PDF_RosoSquad.md`
- `references/seo-squad/templates/Outils_Gratuits_Recommandes.md`

## Règles de preuve

### Triple statut obligatoire

Chaque fait doit être classé:

- `Confirmé`: lu via web, outil, connecteur, capture ou collage utilisateur.
- `Déduit`: inféré depuis un fait confirmé, avec la source de l'inférence.
- `Non vérifié`: inaccessible ou non fourni.

### Double-vérification des affirmations négatives

Ne jamais écrire "absent", "manquant", "aucun", "zéro" ou "pas de" sans deux checks indépendants:

1. Test direct de l'URL canonique ou de la source attendue.
2. Recherche alternative ciblée (`site:`, marque + plateforme, SERP, outil externe).

Si un seul check passe ou si l'accès est bloqué, écrire `Non vérifié, à confirmer manuellement`.

### Interdits

- Promettre un ranking, une citation IA garantie, un volume de trafic ou un délai.
- Inventer volume, backlink, schema, sitemap, H1, avis, concurrent ou citation.
- Recommander PBN, achat de backlinks, faux avis, doorway pages, cloaking, keyword stuffing ou contenu IA massif sans contrôle humain.
- Montrer du jargon non traduit dans un livrable client.

## Process

### 1. Configurer l'audit

Collecter URL, marque, type business, pays/langue, objectifs SEO/GEO, accès disponibles, concurrents et mode. En `--squad`, reprendre le check de configuration du master orchestrator et demander le rythme `step-by-step` ou `all-at-once`.

### 2. Choisir la profondeur

- `--quick`: audit condensé homepage, technique de base, contenu GEO, visibilité IA et actions 7 jours.
- `--ship-gate`: blocants P0/P1 avant livraison d'une page publique.
- `--geo-only`, `--technical`, `--content`: charger les agents/références correspondant au périmètre.
- `--full` ou `--squad`: suivre le master orchestrator et les 11 agents complets.

### 3. Exécuter la collecte

Créer le Brief Site à partir du template si l'audit est complet. Vérifier homepage, title, meta, H1, hero, CTA, pages clés, `robots.txt`, `sitemap.xml`, canonical, `llms.txt`, statut HTTP, données GSC/GA4 si fournies, présence externe et signaux de marque.

### 4. Piloter les agents

En `--squad`, appliquer les contrôles du master orchestrator:

- ne pas passer à l'agent suivant si le Brief Site ou le livrable précédent manque;
- vérifier l'en-tête, la synthèse, le rapport complet, le tableau de statut et les sources;
- empêcher les chevauchements entre agents;
- proposer les tests live cross-IA avant 09bis quand le runtime le permet.

Si l'écriture est autorisée, créer les fichiers dans `audit-livrables/<nom-client>/`. Sinon, produire les livrables en sections markdown dans la réponse et indiquer les fichiers recommandés.

### 5. Consolider

Produire le rapport fusionné puis le Master Final Report client-facing. En environnement sans génération PDF, produire les deux livrables finaux en Markdown ou HTML exportable:

1. `Audit_<NomClient>_Note_Strategique`
2. `Plan_Implementation_<NomClient>`

## Livrables squad

En mode `--squad`, viser cette trace complète:

- `Brief_Site.md`
- `02_Strategie_Positionnement.md`
- `03_Audit_Homepage.md`
- `07_SEO_Technique_Donnees_Structurees.md`
- `04_Keyword_Intent_Research.md`
- `05_Analyse_Concurrentielle.md`
- `06_Content_SEO_GEO.md`
- `08_Autorite_Brand_SEO_Local.md`
- `09_Visibilite_IA_Plan_Action.md`
- `09bis_Auto_Test_IA.md`
- `Rapport_Fusionne_Final.md`
- `Audit_<NomClient>_Note_Strategique.pdf` ou `.md/.html`
- `Plan_Implementation_<NomClient>.pdf` ou `.md/.html`

## Output attendu

```markdown
## SEO/GEO Audit Report

**Input**: ...
**Mode**: quick | full | squad | geo-only | technical | content | ship-gate
**Business type**: ...
**Confidence**: Élevé | Moyen | Faible
**Verdict**: Ship-ready | Fix P0/P1 first | Needs SEO/GEO loop

### Axis scores
| Axis | Score | Evidence status | Notes |
|---|---:|---|---|

### Findings
| Sev | Axis | Where | Status | Issue | Fix |
|---|---|---|---|---|---|

### GEO visibility
| Prompt | Platform | Brand cited | Main source | Confidence | Action |
|---|---|---|---|---|---|

### Roadmap
#### 7 jours
#### 30 jours
#### 90 jours

### Non vérifié
| Element | Why not verified | Next check |
|---|---|---|

### Next action
- `/dev` tickets / content brief / manual verification / monitoring setup
```

## Intégrations

- `/seo-geo-audit`: audit compact ou ciblé.
- `/seo-geo-squad`: orchestration complète Roso SEO Squad avec les 11 agents.
- `/discovery`: si le produit/site a un enjeu SEO, définir les axes SEO/GEO à mesurer.
- `/dev`: transformer les P0/P1 techniques, schema, meta, contenus ou llms.txt en tâches.
- `/qa`: ajouter un check SEO/GEO rapide pour landing/site public.
- `/ship`: si une page publique SEO change, lancer `seo-geo-audit --ship-gate`.
- `design-audit`: complément UI/DS; ne remplace pas les preuves SEO/GEO.

## Références internes

- `references/seo-squad-framework.md`: synthèse compacte pour les audits rapides.
- `references/seo-squad/`: pack complet Roso SEO Squad, prompts agents, règles communes et templates. En `--full` ou `--squad`, ce dossier est prioritaire sur tout résumé.

## Anti-patterns

- Faire un audit "au feeling" sans statut de preuve.
- Lire seulement le résumé alors que l'utilisateur demande la squad complète.
- Dire qu'un fichier ou une présence sociale est absent sans double-check.
- Sortir 50 mots-clés génériques au lieu de 20 intentions priorisées.
- Confondre GEO avec "mettre des mots-clés pour ChatGPT".
- Donner une roadmap impossible à exécuter: limiter les actions et prioriser par impact/difficulté.
