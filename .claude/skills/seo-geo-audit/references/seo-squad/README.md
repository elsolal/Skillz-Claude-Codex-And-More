# Roso SEO Squad

**Version : Final 30 mai 2026**

Squad de **11 agents IA SEO/GEO** (10 agents d'audit + 1 Master Final Report client-facing) pour utilisateurs **Claude Pro / Max / Team**.

Pack no-code, sans API payante, conçu pour Claude Projects.

---

## Prérequis (obligatoires)

- Abonnement Claude Pro, Max ou Team actif
- Web Search activé dans Claude (icône globe dans le composer)
- Un Claude Project créé pour ce pack
- **Fortement recommandé : Claude in Chrome activé** (extension navigateur, via l'app de bureau en mode Cowork) → setup en 3 min, voir le guide d'utilisation PDF. C'est le booster n°1 du kit pour lire GSC, PageSpeed, GBP, Trustpilot, Reddit etc. en autopilote
- Optionnel (utilisateurs avancés) : connecteurs MCP custom (GSC, GA4) si tu veux passer par API au lieu de Chrome

---

## Ce qui rend cette version FIABLE

- **8 règles communes** dans `00_REGLES_COMMUNES.md` (anti-hallucination, anti-promesses, triple statut Confirmé / Déduit / Non vérifié, double-vérification obligatoire des affirmations négatives, auto-relecture pour cohérence interne, et **Règle 8 — vocabulaire client-friendly** : tout terme technique traduit en français normal dès sa première apparition + glossaire de 30 termes en section 13)
- **Protocole anti-faux-négatif** sur les Agents 07 (technique) et 08 (autorité) : aucune affirmation d'absence possible sans test HTTP de l'URL canonique + recherche Web ciblée
- **Règle 6 ter — Détection garantie des profils sociaux** : protocole obligatoire en 5 étapes (3 à 5 slugs candidats × 4 méthodes : Web Fetch + Claude in Chrome + recherche `site:` ciblée + recherche large), croisé avec les balises `sameAs` du JSON-LD et les `href` du footer du site. Conséquence : un compte LinkedIn / Instagram / Reddit avec 3 abonnés est désormais garanti détecté.
- **Échelle à 4 niveaux** pour les présences sociales (Absente / Présente mais vide / Présente sous-exploitée / Présente active) — fini les faux-négatifs binaires
- **Charte graphique PDF unifiée** : `templates/Charte_PDF_RosoSquad.md` — design professionnel appliqué automatiquement aux PDFs livrés par l'Agent 10, avec composants pédagogiques (feu tricolore, blocs « Où le coller », glossaire, page « Si tu es perdu »)
- **Phase 8 Cohérence finale** dans le Master Orchestrator : scan complet du rapport pour détecter les contradictions internes avant livraison
- **Agent 09bis Auto-Test IA (auto par défaut + Mode Expert optionnel)** : enchaînement automatique après l'Agent 09 pour exécuter les 25 prompts de test sur Claude et estimer le score global de Visibilité IA. Une section « Mode Expert » optionnelle (5 prompts max) apparaît **après** le rapport pour ceux qui veulent vérifier eux-mêmes — totalement ignorable.
- **Agent 10 Master Final Report (DOUBLE PDF)** : produit systématiquement **deux PDFs** au design professionnel :
  1. `Audit_[NomClient]_Note_Strategique.pdf` — le diagnostic (8 parties : Verdict avec feu tricolore en page 1 / Constat / Scores / Failles / Angles morts / Axes / Par où commencer / Glossaire)
  2. `Plan_Implementation_[NomClient].pdf` — l'exécution prête à copier-coller (13+ chantiers en 4 temps, snippets HTML / JSON-LD / llms.txt / textes meta / emails / posts Reddit-LinkedIn / checklist 7-30-90j / prompts ChatGPT-Perplexity, chaque snippet accompagné d'un bloc « Où le coller » WordPress/Webflow/Wix/Shopify, et une page finale « Quoi faire si tu es perdu »)
  La règle est non-négociable : jamais 1 seul PDF, toujours les 2.
- **Stats GEO sourcées + paper Princeton intégré** : section 10 de `00_REGLES_COMMUNES.md` cite ses sources (Ahrefs, Semrush, Search Engine Land, ZipTie, paper arXiv:2311.09735) — les stats contestées sont marquées comme telles, pas d'invention
- **Couche déterministe anti-hallucination** : `Outils_Verification_Externes.md` liste 10 outils gratuits (httpstatus.io, Schema Validator, PageSpeed, etc.) pour confirmer factuellement les checks techniques avant que Claude ne les analyse — élimine le risque résiduel d'hallucination sur les faits
- Méthode de collecte no-code à 3 niveaux explicites dans chaque agent (Claude in Chrome → Web natifs → Collage utilisateur)
- Mode adaptatif par type de business (Local / SaaS / E-commerce / Service B2B / B2C / Média)
- Critères chiffrés et quick wins concrets dans chaque agent
- Grille de notation GEO concrète (Agent 09)
- Intégration prioritaire **Claude in Chrome** pour lire GSC, PageSpeed, GBP, Reddit, Trustpilot en navigation autopilotée
- Compatibilité avec les connecteurs MCP custom (GSC, GA4, Firecrawl) pour utilisateurs avancés

---

## Ce que Roso fait — et ce que Roso ne fait pas

### Ce que Roso fait
- Audit SEO/GEO ponctuel et complet (11 agents, séquence unique) en 2 à 4h selon la taille du site et la data disponible
- 11 agents spécialisés (audit homepage, technique, keywords, concurrents, content, autorité, visibilité IA)
- Auto-test réel de 25 prompts sur Claude (Agent 09bis)
- Plan d'action client-facing avec Quick Wins, axes structurants, roadmap 7j/30j/90j (Agent 10)
- 8 règles communes anti-hallucination + Phase 8 cohérence finale + double-vérification des affirmations négatives
- Framework GEO du paper Princeton (Aggarwal et al., SIGKDD 2024) intégré aux agents Content et Visibilité IA

### Ce que Roso ne fait pas
- **Pas de monitoring continu** : Roso est un audit ponctuel, pas un tracker mensuel. Pour le monitoring en continu (mentions cross-IA, alertes), les outils dédiés sont Semrush AI Toolkit (~$170/mois), Ahrefs Brand Radar, Profound. Roso est complémentaire (29€ une fois) — pas un remplaçant.
- **Pas d'auto-correction** : Roso identifie et priorise, mais l'exécution (publier du contenu, modifier le code, créer un GBP) est faite par l'utilisateur. Ce n'est pas un agent autonome qui modifie ton site.
- **Pas de scraping en masse** : pas d'aspiration concurrentielle automatisée à grande échelle (limite par design no-code + respect des CGU plateformes).
- **Pas de ranking tracking** : pas de suivi quotidien de positions. Pour ça, GSC (gratuit) ou Ahrefs/Semrush.
- **Pas de backlinks discovery** : nécessite un outil tiers (Ahrefs, Semrush, Majestic, Ubersuggest gratuit limité).
- **Pas de génération automatique de contenu publié** : Roso recommande des sujets et angles, mais n'écrit pas les articles à ta place (par design — pour préserver la voix de marque).

---

## Comment l'utiliser

1. Crée un Claude Project nommé "Roso SEO Squad"
2. Uploade tout le contenu de ce dossier dans le Project (knowledge)
3. Copie le prompt de lancement (voir le guide d'utilisation PDF)
4. Lance la séquence

---

## Arborescence

```
/Roso_SEO_Squad
  README.md
  00_REGLES_COMMUNES.md              ← 8 règles communes absolues
  01_MASTER_ORCHESTRATOR.md          ← inclut Phase 8 Cohérence finale + Phase 9 lancement Agent 10
  Outils_Verification_Externes.md    ← couche déterministe anti-hallucination (10 outils gratuits)
  /agents
    01_Data_Collector.md
    02_Strategie_Positionnement_SEO_GEO.md
    03_Audit_Homepage_On_Page.md
    04_Keyword_Intent_Research.md
    05_Analyse_Concurrentielle.md
    06_Content_SEO_GEO.md
    07_SEO_Technique_Donnees_Structurees.md   ← protocole anti-faux-négatif
    08_Autorite_Brand_SEO_Local.md            ← protocole anti-faux-négatif + échelle 4 niveaux
    09_Visibilite_IA_Plan_Action.md
    09bis_Auto_Test_IA.md                      ← exécution auto des 25 prompts test
    10_Master_Final_Report.md                  ← livrable client final = 2 PDFs (Audit + Plan d'Implémentation)
  /templates
    Brief_Site.md
    Charte_PDF_RosoSquad.md                    ← charte graphique des PDFs livrés (+ composants pédagogiques)
    Grille_Notation_GEO.md
    Outils_Gratuits_Recommandes.md
```
