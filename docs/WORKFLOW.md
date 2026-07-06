# 🚀 D-EPCT+R Workflow - Kit Complet Claude Code

## 📋 Table des matières

1. [Qu'est-ce que c'est ?](#quest-ce-que-cest-)
2. [Structure du bundle](#structure-du-bundle)
3. [Installation pas à pas](#installation-pas-à-pas)
4. [Utilisation](#utilisation)
5. [Le workflow détaillé](#le-workflow-détaillé)
6. [Personnalisation](#personnalisation)
7. [Troubleshooting](#troubleshooting)

---

## Qu'est-ce que c'est ?

Un ensemble de **Skills** et **Commands** pour Claude Code qui automatise ton workflow de développement :

```
DISCOVERY → EXPLORE → PLAN (orchestrateur) → CODE+TESTS (subagents //) → REVIEW ×3 (subagents //)
```

### Pourquoi Skills plutôt qu'Agents ?

| Aspect | Skills ✅ | Agents (ancien) |
|--------|----------|-----------------|
| Déclenchement | Automatique | Manuel |
| Réutilisabilité | Portable entre projets | Spécifique |
| Maintenance | Modulaire | Monolithique |
| Tokens | Chargé à la demande | Tout en contexte |

**Les Skills sont la nouvelle approche recommandée par Anthropic.**

---

## Structure du bundle

```
d-epct-workflow/
│
├── 📄 README.md                          ← CE FICHIER
├── 📄 GUIDE-COMPLET.md                   ← Documentation détaillée
│
└── 📁 .claude/                           ← À COPIER DANS TON PROJET
    │
    ├── 📄 CLAUDE.md                      ← Instructions globales projet
    │
    ├── 📁 commands/                      ← Commandes /slash
    │   ├── 📄 discovery.md               ← /discovery
    │   └── 📄 feature.md                 ← /dev
    │
    └── 📁 skills/                        ← Skills auto-déclenchés
        ├── 📁 pm-discovery/
        │   └── 📄 SKILL.md               ← 🎯 Session PM
        ├── 📁 github-issue-reader/
        │   └── 📄 SKILL.md               ← 📋 Lecture issues
        ├── 📁 code-implementer/
        │   └── 📄 SKILL.md               ← 💻 Implémentation
        ├── 📁 test-runner/
        │   └── 📄 SKILL.md               ← 🧪 Tests
        └── 📁 code-reviewer/
            └── 📄 SKILL.md               ← 🔍 Boucle quality-gate
```

---

## Installation pas à pas

### Prérequis

- Claude Code installé (`npm install -g @anthropic-ai/claude-code` ou via l'app)
- Git configuré
- Accès GitHub (pour la création d'issues)

### Étape 1 : Télécharger et dézipper

```bash
# Dézipper le bundle
unzip d-epct-workflow.zip
cd d-epct-workflow
```

### Étape 2 : Copier dans ton projet

```bash
# Copier le dossier .claude dans ton projet
cp -r .claude /chemin/vers/ton-projet/

# Vérifier
ls -la /chemin/vers/ton-projet/.claude/
```

Tu dois voir :
```
.claude/
├── CLAUDE.md
├── commands/
│   ├── discovery.md
│   └── feature.md
└── skills/
    ├── pm-discovery/
    ├── github-issue-reader/
    ├── code-implementer/
    ├── test-runner/
    └── code-reviewer/
```

### Étape 3 : Commit dans ton repo

```bash
cd /chemin/vers/ton-projet
git add .claude/
git commit -m "chore: add D-EPCT+R workflow skills"
git push
```

### Étape 4 : Vérifier l'installation

```bash
# Lancer Claude Code dans ton projet
cd /chemin/vers/ton-projet
claude

# Tester que les skills sont détectés
> Quels skills sont disponibles ?
```

Claude doit lister les 7 skills.

---

## Utilisation

### Scénario 1 : Tu as une idée mais pas d'issue

```bash
# 1. Lancer Claude Code
claude

# 2. Démarrer une session Discovery
/discovery

# 3. Expliquer ton besoin (parle librement)
> J'aimerais qu'on ajoute un système de filtres sur la page produits.
> Les utilisateurs devraient pouvoir filtrer par catégorie, par prix,
> et par note. Et il faudrait que ça se souvienne de leurs préférences.

# 4. Répondre aux questions de Claude PM
# (Il va poser 2-3 questions pour clarifier)

# 5. Valider la synthèse quand il la propose

# 6. Valider les issues avant publication

# 7. Claude crée les issues sur GitHub
# → Epic #42 + Stories #43, #44, #45

# 8. Lancer l'implémentation d'une story
/dev #43
```

### Scénario 2 : Tu as déjà une issue GitHub

```bash
# Directement lancer l'implémentation
/dev https://github.com/ton-org/ton-repo/issues/123

# Ou avec juste le numéro (si tu es dans le bon repo)
/dev #123
```

### Scénario 3 : Juste utiliser un skill spécifique

```bash
# Les skills se déclenchent automatiquement selon le contexte
# Exemples :

> Analyse-moi le codebase pour comprendre l'architecture
# → Agent Explore (natif)

> Fais une code review de mes dernières modifications
# → Déclenche code-reviewer

> Aide-moi à planifier l'implémentation de cette feature
# → L'orchestrateur planifie directement (pas de Plan Mode)
```

---

## Le workflow détaillé

### Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   🎯 DISCOVERY                                                       │
│   ├─ Tu expliques ton besoin (speech-to-text OK)                    │
│   ├─ Claude PM pose des questions                                    │
│   ├─ Synthèse → Tu valides                                          │
│   ├─ Rédaction Epic + User Stories                                  │
│   └─ Publication GitHub → Tu obtiens #XX                            │
│                                                                      │
│   ⏸️ CHECKPOINT ─────────────────────────────────────────────────    │
│                                                                      │
│   📋 EXPLAIN                                                         │
│   ├─ Lecture de l'issue #XX                                         │
│   ├─ Analyse du codebase                                            │
│   └─ Cartographie des fichiers impactés                             │
│                                                                      │
│   ⏸️ CHECKPOINT ─────────────────────────────────────────────────    │
│                                                                      │
│   📝 PLAN                                                            │
│   ├─ Décomposition en étapes                                        │
│   ├─ Estimation complexité                                          │
│   └─ Identification des risques                                     │
│                                                                      │
│   ⏸️ CHECKPOINT ─────────────────────────────────────────────────    │
│                                                                      │
│   💻 CODE                                                            │
│   ├─ Implémentation étape par étape                                 │
│   ├─ Validation à chaque étape                                      │
│   └─ Respect des conventions                                        │
│                                                                      │
│   ⏸️ CHECKPOINT ─────────────────────────────────────────────────    │
│                                                                      │
│   🧪 TEST                                                            │
│   ├─ Écriture tests unitaires                                       │
│   ├─ Tests d'intégration                                            │
│   └─ Vérification coverage                                          │
│                                                                      │
│   ⏸️ CHECKPOINT ─────────────────────────────────────────────────    │
│                                                                      │
│   🔍 REVIEW ×3                                                       │
│   ├─ Pass 1: Correctness (logique, bugs)                            │
│   │   └─ Corrections → Validation                                   │
│   ├─ Pass 2: Readability (lisibilité, maintenance)                  │
│   │   └─ Améliorations → Validation                                 │
│   └─ Pass 3: Performance (optimisation)                             │
│       └─ Optimisations → Validation                                 │
│                                                                      │
│   🎨 DESIGN AUDIT (si UI/frontend)                                   │
│   ├─ Tokens + composants + a11y + taste                             │
│   ├─ Drift Figma/code + surface IA                                  │
│   └─ /design-audit-squad pour l'audit complet 12 agents             │
│                                                                      │
│   📈 SEO/GEO AUDIT (si site public / contenu indexable)              │
│   ├─ Technique + contenu + SERP + autorité                           │
│   ├─ llms.txt + visibilité IA + preuves                              │
│   └─ /seo-geo-squad pour l'audit complet 11 agents                   │
│                                                                      │
│   ✅ TERMINÉ                                                         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Détail de chaque phase

#### 🎯 DISCOVERY (pm-discovery)

**Objectif** : Transformer une idée vague en issues GitHub structurées.

**Ce que fait Claude** :
1. Écoute ton besoin sans interrompre
2. Pose des questions de clarification (max 3 à la fois)
3. Synthétise et te fait valider
4. Rédige Epic + User Stories au format standard
5. Publie sur GitHub avec les bons labels

**Format User Story produit** :
```markdown
**En tant que** [utilisateur],
**je veux** [fonctionnalité],
**afin de** [bénéfice].

## Critères d'acceptance
- [ ] Given X, when Y, then Z
```

#### 📋 EXPLORE (subagent Explore)

**Objectif** : Comprendre le contexte avant de coder.

**Ce que fait Claude** :
1. Dispatche un subagent Explore via `SendMessage`
2. Le subagent lit et parse l'issue GitHub
3. Analyse l'architecture du projet
4. Identifie les fichiers à modifier
5. Retourne une synthèse structurée à l'orchestrateur

#### 📝 PLAN (orchestrateur principal)

**Objectif** : Créer un plan d'implémentation validé.

**Ce que fait Claude** (l'orchestrateur garde le contexte et planifie directement) :
1. Décompose en étapes atomiques
2. Définit l'ordre des tâches et les fichiers impactés
3. Identifie les risques
4. Prépare les prompts complets et autonomes pour les subagents d'implémentation

#### 💻 CODE + 🧪 TESTS (2 subagents parallèles)

**Objectif** : Implémenter et tester en parallèle.

**Ce que fait Claude** :
1. Dispatche 2 subagents en parallèle via `SendMessage(run_in_background: true)`
2. **Subagent Code** : implémente selon le plan, lint/types obligatoires
3. **Subagent Tests** : écrit les tests P0-P3 risk-based
4. L'orchestrateur vérifie les résultats au retour

Pour les apps web, le subagent Tests peut charger `web-navigator`, qui utilise Playwright CLI comme runtime recommande avant de coder les E2E:

```bash
npm install -g @playwright/cli@latest
playwright-cli install --skills
playwright-cli --help
```

Playwright pilote un vrai navigateur. Dans Skillz-Claude, `web-navigator` l'utilise surtout pour produire des preuves agentiques reutilisables: pages visitees, screenshots, snapshot DOM, console, reseau, responsive, locators, extraction d'informations et reproduction utilisateur. Les flows critiques sont ensuite convertis en tests Playwright versionnes.

#### 🌐 WEB NAVIGATION (si URL/site a analyser)

**Objectif** : permettre aux agents de naviguer sur un site reel avant de conclure.

`web-navigator` est le skill transverse pour les demandes du type "analyse ce site", "recupere les infos", "compare ces concurrents", "inspecte ce tunnel" ou "observe cette page". Il choisit le runtime disponible:

1. Playwright CLI si `playwright-cli --help` fonctionne.
2. Browser/MCP ou navigateur integre.
3. WebFetch/WebSearch pour contenu public statique.
4. Capture, export HTML ou contenu colle par l'utilisateur.

Le livrable standardise les preuves avec `Confirmé / Déduit / Non vérifié`, puis les skills metier consomment ce rapport: `/qa`, `seo-geo-audit`, `design-audit`, `test-runner`, `taste-critic`.

#### 🔍 REVIEW ×3 (3 subagents parallèles)

**Objectif** : Valider le code avec 3 reviews spécialisées en parallèle.

**Ce que fait Claude** :
1. Dispatche 3 subagents review en parallèle via `SendMessage(run_in_background: true)`
2. Chaque subagent a un focus spécifique
3. L'orchestrateur synthétise les rapports et corrige les issues critiques

| Pass | Focus | Questions |
|------|-------|-----------|
| **#1 Correctness** | Le code fait ce qu'il doit ? | Bugs ? Cas limites ? Sécurité ? |
| **#2 Readability** | Le code est maintenable ? | Nommage ? Structure ? DRY ? |
| **#3 Performance** | Le code est optimal ? | Complexité ? Memory ? Scale ? |

#### 🎨 DESIGN AUDIT (si UI/frontend)

**Objectif** : fermer la boucle design avant livraison.

Quand une feature touche `.tsx`, `.jsx`, `.vue`, `.css`, des composants, tokens, Figma ou une UI IA, l'orchestrateur ajoute `design-audit`:

Utilise `/design-audit-squad` quand il faut un audit complet façon Lyse Design Squad: règles communes, orchestrateur, 12 agents, livrables intermédiaires, score statique Lyse optionnel, taste runtime, drift Figma/code et ship-gate final.

1. **Apres Explore** : audit rapide pour transformer les P0/P1 en contraintes de plan.
2. **Apres la boucle quality-gate** : `design-audit --ship-gate` sur la preview ou les chemins UI modifies.
3. **Dans `/qa`** : le health score inclut une categorie `Design system`.
4. **Dans `/ship`** : P0 bloque; P1 bloque sauf risque explicitement accepte.

| Axe | Controle |
|-----|----------|
| Tokens | Couleurs, spacing, radius, motion via variables/tokens |
| Components | Reutilisation DS, variants stricts, imports canoniques |
| A11y | Labels, alt, roles, keyboard, focus, contrastes |
| Taste | Hierarchie, densite, typo, motion, copy, responsive |
| Figma/code | Props, variants, tokens et etats synchronises |
| AI surface | Marker IA, disclaimer, explainability, feedback, human control |

En mode squad complet, le skill lit les prompts stockés dans `.claude/skills/design-audit/references/lyse-squad/` et conserve les règles dédiées de chaque agent.

#### 📈 SEO/GEO AUDIT (si site public / contenu indexable)

**Objectif** : auditer la capacité d'un site à être trouvé dans Google et cité par les moteurs IA.

Utilise `/seo-geo-audit` quand la feature touche une page publique, une landing, un site vitrine, une page service, du contenu éditorial, `robots.txt`, `sitemap.xml`, `schema`, `llms.txt`, les meta tags ou la stratégie de visibilité.

Utilise `/seo-geo-squad` quand il faut reprendre le workflow complet Roso SEO Squad: règles communes, master orchestrator, 11 agents, livrables intermédiaires, rapport fusionné et double livrable final client-facing.

Le workflow produit:

1. Un diagnostic SEO/GEO avec preuves `Confirmé / Déduit / Non vérifié`.
2. Des scores par axe: technique, on-page, contenu, keywords, autorité, local, visibilité IA.
3. Une grille GEO de prompts conversationnels si le sujet s'y prête.
4. Une roadmap 7j / 30j / 90j.
5. Des tâches transformables en `/dev`.

En mode squad complet, le skill lit les prompts originaux stockés dans `.claude/skills/seo-geo-audit/references/seo-squad/` et conserve les règles dédiées de chaque agent.

| Axe | Controle |
|-----|----------|
| Technique | HTTP, indexabilité, robots, sitemap, canonical, schema, Core Web Vitals |
| On-page | title, meta, H1, structure Hn, CTA, preuves, FAQ |
| Keywords | intentions, SERP dominante, cannibalisation, pages cibles |
| Content GEO | réponse directe, sources, stats, FAQ, contenus citables IA |
| Autorité/local | avis, GBP, NAP, mentions, backlinks connus, réseaux sociaux |
| Visibilité IA | llms.txt, prompts Claude/Google AIO/ChatGPT/Perplexity/Gemini, sources citées |

---

## Personnalisation

### Modifier le format des User Stories

Édite `.claude/skills/pm-discovery/SKILL.md`, section "Structure User Story".

### Modifier les conventions de code

Édite `.claude/skills/code-implementer/SKILL.md`, section "Principes de code".

### Modifier la checklist de review

Édite `.claude/skills/code-reviewer/SKILL.md`, les 3 sections de Pass.

### Ajouter un nouveau skill

```bash
# Créer le dossier
mkdir .claude/skills/mon-skill

# Créer le SKILL.md
cat > .claude/skills/mon-skill/SKILL.md << 'EOF'
---
name: mon-skill
description: Description claire de ce que fait le skill et QUAND l'utiliser.
---

# Mon Skill

## Instructions
1. Étape 1
2. Étape 2

## Output attendu
...
EOF

# Commit
git add .claude/skills/mon-skill/
git commit -m "feat: add mon-skill"
```

### Utiliser les skills globalement (tous tes projets)

```bash
# Copier dans ton home
cp -r .claude/skills/* ~/.claude/skills/

# Les skills seront disponibles dans TOUS tes projets
```

---

## Troubleshooting

### "Claude n'utilise pas mes skills"

1. **Vérifier que le dossier .claude existe**
   ```bash
   ls -la .claude/skills/
   ```

2. **Vérifier la syntaxe YAML** du SKILL.md
   ```bash
   head -10 .claude/skills/pm-discovery/SKILL.md
   # Doit commencer par ---
   # Puis name: et description:
   # Puis ---
   ```

3. **Vérifier la description** - C'est elle qui déclenche le skill. Si trop vague, Claude ne sait pas quand l'utiliser.

### "Les issues ne se créent pas sur GitHub"

1. **Vérifier que gh CLI est installé et authentifié**
   ```bash
   gh auth status
   ```

2. **Vérifier les permissions du repo**

### "Le workflow s'arrête en plein milieu"

C'est normal ! Le workflow attend ta validation à chaque checkpoint.
Réponds "ok", "continue", "validé" pour passer à l'étape suivante.

### "Je veux skip une étape"

Dis-le à Claude :
```
> Skip la phase de test, on verra ça après
```

---

## Ressources

- [Documentation officielle Skills](https://code.claude.com/docs/en/skills)
- [Best Practices Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices)
- [Blog Anthropic sur les Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

---

## Changelog

- **v1.0.0** - Version initiale
  - 5 skills : pm-discovery, github-issue-reader, code-implementer, test-runner, code-reviewer
  - 2 commands : /discovery, /dev
  - Documentation complète
