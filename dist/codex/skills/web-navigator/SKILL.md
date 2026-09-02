---
name: web-navigator
description: Navigue sur un site avec Playwright CLI, Browser/MCP ou WebFetch pour analyser, extraire et sourcer des informations. Utiliser pour "analyse ce site", benchmark concurrentiel, research web, SEO/GEO, QA exploratoire, audit design runtime ou récupération d'informations depuis une UI.
---

# Web Navigator

Skill transverse pour explorer un site reel comme un utilisateur, collecter des preuves et transformer une navigation browser en analyse sourcee. Playwright CLI est le runtime recommande quand il est disponible; Browser/MCP, WebFetch, captures ou contenu colle par l'utilisateur restent des fallbacks.

## Quand utiliser

- L'utilisateur demande d'analyser un site, une page, un tunnel, une app, un concurrent ou un contenu web.
- Un skill metier doit observer une URL avant de conclure: `seo-geo-audit`, `design-audit`, `/qa`, `test-runner`, `taste-critic`, `performance-auditor`.
- Il faut recuperer des informations visibles seulement apres navigation, interaction, login, tabs, scroll, filtres ou formulaires.
- Il faut produire des preuves: URLs visitees, screenshots, snapshots DOM, console, reseau, storage, locators, notes d'incertitude.

## Quand NE PAS utiliser

- Question purement statique sur un fichier local.
- Scraping massif ou crawl profond: utiliser un crawler dedie si disponible, puis revenir ici pour verifier les pages critiques.
- Actions destructrices, achats, suppressions, envois de formulaires reels ou changements de compte sans accord explicite.
- Contournement de login, paywall, captcha, robots.txt ou restrictions d'acces.

## References

Lire seulement si utile:

- `references/playwright-cli.md` — commandes Playwright CLI, installation et lien avec le skill officiel.
- `references/evidence-model.md` — format de preuve et niveaux `Confirmé / Déduit / Non vérifié`.
- `references/navigation-protocol.md` — protocole d'exploration pour site public, app connectee, concurrent ou tunnel.

## Process

### 1. Cadrer l'objectif

Identifier:
- cible: URL, domaine, app locale, preview, staging, prod;
- but: analyse informationnelle, benchmark, SEO/GEO, QA, design runtime, extraction de contenu;
- profondeur: page unique, top navigation, tunnel precis, 3-5 pages, ou exploration large;
- contraintes: login, compte test, actions interdites, donnees sensibles.

Si l'objectif est ambigu, poser une question courte. Sinon avancer avec une navigation read-only et prudente.

### 2. Choisir le runtime

Priorite:

1. Playwright CLI si `playwright-cli --help` fonctionne.
2. Browser/MCP ou navigateur integre si disponible.
3. WebFetch/WebSearch pour contenu statique public.
4. Capture, export HTML, texte colle ou screenshot fourni par l'utilisateur.

Si Playwright CLI est disponible, utiliser le skill officiel installe par `playwright-cli install --skills` quand l'environnement sait le charger. Sinon consulter `playwright-cli --help` et suivre `references/playwright-cli.md`.

### 3. Explorer sans polluer

- Ouvrir la cible et noter URL finale, title, status visible.
- Prendre snapshot ou capture avant interactions majeures.
- Cartographier navigation principale, CTA, formulaires, menus, tabs et liens internes.
- Interagir uniquement sur des actions read-only ou explicitement autorisees.
- Apres chaque interaction importante, relever console, reseau et changement d'URL ou d'etat.
- Pour login, utiliser compte test et stocker l'etat temporaire hors repo (`/tmp` ou chemin ignore).

### 4. Extraire et qualifier

Pour chaque information utile, conserver:

- source: URL, screenshot/snapshot, selector ou commande;
- statut: `Confirmé`, `Déduit`, `Non vérifié`;
- contexte: viewport, session, date si pertinent;
- limite: contenu inaccessible, login absent, JS bloque, geolocalisation, personnalisation, cache.

Ne jamais inventer a partir d'un souvenir de marque ou d'une page non visitee.

### 5. Restituer

Produire une synthese courte et exploitable:

```markdown
## Web Navigation Report

**Target**: ...
**Runtime**: Playwright CLI | Browser/MCP | WebFetch | user evidence
**Scope**: ...

### Pages visited
| Page | URL | Evidence | Notes |
|---|---|---|---|

### Findings
| Status | Finding | Evidence | Limit |
|---|---|---|---|

### Next actions
- ...
```

## Integrations

- `/qa`: utilise `web-navigator` pour naviguer, capturer, lire console/reseau, puis applique le health score QA.
- `seo-geo-audit`: utilise `web-navigator` pour pages publiques, concurrents, maillage, SERP manuelle et preuves `Confirmé / Déduit / Non vérifié`.
- `design-audit`: utilise `web-navigator` pour screenshots, responsive, taste runtime, drift visible et preuves d'interaction.
- `test-runner`: utilise `web-navigator` avant E2E pour confirmer le flow et extraire les locators.
- `taste-critic`: utilise `web-navigator` pour obtenir une capture/snapshot fiable avant critique visuelle.

## Exemples

```bash
# Analyse site public
playwright-cli open https://example.com --headed
playwright-cli snapshot
playwright-cli screenshot --filename=/tmp/example-home.png

# Flow app locale
playwright-cli open http://localhost:3000
playwright-cli console
playwright-cli requests
playwright-cli generate-locator e12 --raw
```

## Anti-patterns

- Confondre navigation exploratoire et test E2E versionne: le skill collecte des preuves; `test-runner` codifie les regressions.
- S'appuyer seulement sur WebFetch quand l'information depend du JavaScript, d'un menu, d'un login ou d'un viewport.
- Sauvegarder cookies, tokens, localStorage ou screenshots sensibles dans le repo.
- Conclure "absent" sans double verification: navigation, recherche interne, source alternative ou mention `Non vérifié`.
