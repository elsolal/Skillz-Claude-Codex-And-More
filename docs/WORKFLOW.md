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
DISCOVERY → PROBE → EXPLORE → PLAN ⛔ (stop unique) → RED (conditionnel) → IMPLEMENT (séquentiel) → GATE (boucle quality-gate) → HANDOFF
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
│                                                                     │
│   🎯 DISCOVERY                                                       │
│   ├─ Tu expliques ton besoin (speech-to-text OK)                    │
│   ├─ Niveau 0-4 auto-détecté (tech-spec ou chaîne complète)         │
│   ├─ Synthèse → Tu valides                                          │
│   └─ Spec consolidée et approuvée → docs/planning/specs/            │
│                                                                     │
│   ⏸️ CHECKPOINT — spec approuvée ─────────────────────────────────  │
│                                                                     │
│   🔎 PROBE (silencieux)                                              │
│   └─ Lecture/rafraîchissement de .agents/verification.yaml          │
│                                                                     │
│   📋 EXPLORE                                                         │
│   ├─ Lecture de l'issue #XX                                         │
│   ├─ Analyse du codebase + détection surface (UI/SEO)               │
│   └─ Évaluation du niveau 0-4                                       │
│                                                                     │
│   📝 PLAN ⛔ (stop unique)                                            │
│   ├─ Décomposition en étapes + critères d'acceptance                │
│   └─ Validation utilisateur — seul arrêt avant le handoff           │
│                                                                     │
│   🔴 RED (conditionnel, niveau ≥ 2 + harness dispo)                  │
│   └─ Tests d'acceptance qui échouent pour la bonne raison           │
│                                                                     │
│   💻 IMPLEMENT (séquentiel)                                          │
│   ├─ Étape par étape : code + tests → manifeste vert                │
│   └─ Respect des conventions                                        │
│                                                                     │
│   🔄 GATE (boucle quality-gate)                                      │
│   ├─ Commit d'abord, gate sur le diff committé                      │
│   ├─ Design/SEO/a11y = lenses du gate (niv. 3-4)                    │
│   └─ Verdict PASS/CONCERNS/FAIL → docs/quality/GATE-*.yaml          │
│                                                                     │
│   🎨 DESIGN AUDIT (si UI/frontend, lens du gate)                     │
│   ├─ Tokens + composants + a11y + taste                             │
│   ├─ Drift Figma/code + surface IA                                  │
│   └─ /design-audit-squad pour l'audit complet 12 agents             │
│                                                                     │
│   📈 SEO/GEO AUDIT (si site public / contenu indexable)              │
│   ├─ Technique + contenu + SERP + autorité                          │
│   ├─ llms.txt + visibilité IA + preuves                             │
│   └─ /seo-geo-squad pour l'audit complet 11 agents                   │
│                                                                     │
│   ✅ HANDOFF                                                         │
│   ├─ Rapport : verdict, décisions prises en ton nom, absents        │
│   └─ [S] /ship  [C] commit seul  [R] re-run gate (niv. 1-2)         │
│                                                                     │
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

#### 🔎 PROBE (silencieux)

**Objectif** : établir les preuves d'exécution disponibles avant toute exploration.

**Ce que fait Claude** :
1. Charge le skill `project-probe`
2. Lit `.agents/verification.yaml` (lint, types, tests, build) ; le crée ou le rafraîchit s'il est absent ou périmé
3. Lit les conventions du repo (`CLAUDE.md` / `AGENTS.md`, pointeur mémoire local si présent)

#### 📋 EXPLORE (subagent Explore)

**Objectif** : comprendre le contexte et évaluer le niveau avant de planifier.

**Ce que fait Claude** :
1. Dispatche un subagent Explore via `SendMessage` (Claude Code) ou explore inline sur les runtimes séquentiels
2. Le subagent lit et parse l'issue GitHub (ou la spec issue de la discovery)
3. Analyse l'architecture du projet, les fichiers impactés, les patterns et les risques
4. Détecte la surface (frontend `.tsx/.jsx/.vue/.css`, SEO/GEO pages publiques) et évalue le niveau 0-4
5. Retourne une synthèse structurée à l'orchestrateur

#### 📝 PLAN ⛔ (stop unique)

**Objectif** : produire le plan validé — le seul arrêt humain avant le handoff.

**Ce que fait Claude** (l'orchestrateur garde le contexte et planifie directement) :
1. Décompose en étapes atomiques : quoi / où / comment / contraintes / critères d'acceptance testables / stratégie de tests (P0-P3)
2. Identifie les composants/tokens à réutiliser (frontend) ou les fichiers publics concernés (SEO/GEO)
3. Présente un seul écran de validation : synthèse Explore + niveau détecté + plan complet + critères d'acceptance + stratégie de tests
4. En mode `/auto-dev`, ce stop est remplacé par le mandate gate (issue valide ou spec approuvée) — aucun arrêt humain

#### 🔴 RED (conditionnel)

**Objectif** : prouver que les tests d'acceptance échouent pour la bonne raison avant toute implémentation.

**Ce que fait Claude** :
1. N'exécute cette phase que si le niveau est ≥ 2 et qu'un harness de test existe dans le manifeste
2. Écrit les tests d'acceptance dérivés des critères validés en phase PLAN
3. Les exécute et vérifie qu'ils échouent pour la bonne raison (pas une erreur de setup)
4. Sans harness : les critères sont vérifiés à l'exécution pendant GATE, et le gate file consigne l'absence dans `absents`

#### 💻 IMPLEMENT (séquentiel)

**Objectif** : implémenter le plan étape par étape.

**Ce que fait Claude** :
1. Exécute les étapes du plan **séquentiellement** : code + ses tests unitaires ensemble à chaque étape
2. Lance les commandes du manifeste (lint, types, tests) — vert avant de passer à l'étape suivante
3. Respecte les conventions du repo, sans refactoring ni édition hors périmètre
4. Ne parallélise deux étapes que si leurs fichiers sont disjoints, idéalement en worktrees

Pour les apps web, la phase RED (ou IMPLEMENT) peut charger `web-navigator`, qui utilise Playwright CLI comme runtime recommande avant de coder les E2E:

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

#### 🔄 GATE (boucle quality-gate)

**Objectif** : prouver la qualité par un gate file plutôt que par une relecture humaine du diff.

**Ce que fait Claude** :
1. Commit l'implémentation d'abord — le gate évalue le diff committé (`<base>...HEAD`), le travail non committé lui est invisible
2. Lance le skill `quality-gate` avec le plan validé et le manifeste ; niveau de gate = niveau de la tâche (1 round au niveau 1 avec quick structural-smell check, ≤3 au niveau 2 avec `thermo-nuclear-code-quality-review` en dernière lentille, ≤4 + lenses design/SEO/a11y aux niveaux 3-4 pour les surfaces détectées en EXPLORE, puis `thermo-nuclear-code-quality-review` en dernière lentille)
3. Boucle jusqu'à un verdict : PASS, CONCERNS (jamais auto-accepté en mode autonome ; attend une décision explicite en mode interactif), ou FAIL (une itération de plus, puis STOP après 3 tentatives)
4. Commit le gate file avec la branche

| Verdict | Sens | Action |
|---------|------|--------|
| **PASS** | Preuves conformes au plan | Proposer `/ship` |
| **CONCERNS** | Findings non bloquants | Décision humaine explicite (waiver) ou nouvelle itération |
| **FAIL** | Findings confirmés bloquants | Corriger, jusqu'à 3 itérations, puis STOP |

Le gate file (`docs/quality/GATE-*.yaml`) est la seule preuve de qualité du système — il remplace les 3 passes de review humaines. La revue `thermo-nuclear-code-quality-review` fait partie du gate en dernière lentille de maintenabilité ; ne pas la relancer comme revue séparée après le gate.

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

#### ✅ HANDOFF

**Objectif** : clôturer la tâche avec un rapport et une décision claire, sans rouvrir le plan.

**Ce que fait Claude** :
1. Présente le rapport final : verdict du gate, nombre de rounds, résumé des findings, `decisions_prises_en_ton_nom` (tout écart au plan validé), `absents`, stats du diff, et la preuve RED→GREEN si la phase RED a tourné
2. Niveaux 0-2 (mode interactif) : propose **[S] `/ship`** | **[C] commit seul** | **[R] re-run du gate** (niveaux 1-2) — ce menu est la décision de handoff, pas un second checkpoint
3. Niveaux 3-4 (mode interactif) : exige la lecture complète de `decisions_prises_en_ton_nom` avant de proposer les mêmes options — c'est la seule relecture humaine restante
4. Mode autonome : enchaîne `/ship` directement si le gate est PASS ; le corps de la PR embarque le gate file

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
