# Skillz-Claude — D-EPCT+R v6.1

> Un workflow de développement agentique, de l'idée à la PR, avec une qualité **prouvée** plutôt que
> relue. Pour Claude Code, Codex, OpenCode, Gemini, Grok, Kimi et tout agent qui lit `AGENTS.md`.

```
/discovery  →  /dev  →  /gate  →  /ship
 planifier   construire  prouver    livrer
```

- **Un seul arrêt humain par feature** : `/dev` adapte sa rigueur au niveau de la tâche (0 à 4) et
  ne s'arrête qu'une fois, au plan.
- **Une qualité prouvée** : une boucle de revues produit un gate file versionné
  (`PASS / CONCERNS / FAIL / WAIVED`). Pas de PASS sans preuve exécutable réelle.
- **N'importe quelle stack** : les commandes de vérification du projet sont détectées, jamais codées
  en dur.

**Statut** : release candidate `6.1.0-rc.1`, **not stable** (non stable). Les skills et commandes
sont décrits dans `core/catalog.yaml` et compilés pour chaque runtime.

---

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install all
```

Installe tout dans `~/.claude/`, `~/.codex/`, `~/.gemini/`, `~/.config/opencode/` et `~/.agents/`.

| Besoin | Commande |
|---|---|
| Mettre à jour | `… \| bash -s -- update all` (ou `bash install.sh update all` depuis un clone) |
| Installer dans un seul projet | `… \| bash -s -- install .` |
| Ajouter la mémoire Obsidian | `bash install.sh install all --with-wiki` |
| Diagnostiquer | `/skillz-doctor` |

Installation agent par agent, bundles compilés `bin/skillz`, plugins natifs, Windows et Playwright :
voir **[docs/INSTALL.md](./docs/INSTALL.md)**.

---

## Le parcours

### 1. Une idée → une spec approuvée

```
/discovery "Je veux un suivi de dépenses avec catégories et alertes de budget"
```

Le niveau est évalué (0 à 4). Petit périmètre : tech-spec directe. Plus gros : Brainstorm → PRD →
Architecture → Stories, validés à chaque étape. Chaque discovery se termine par une **spec approuvée**
dans `docs/planning/specs/`, exigée par `/dev` pour un niveau 4.

### 2. Implémenter, avec un seul arrêt

```
/dev #123
```

Sonde du projet → exploration et niveau → **plan ⛔ (ton seul arrêt)** → tests d'acceptance rouges
(si un harnais existe) → implémentation pas à pas → **boucle quality-gate** → rapport de handoff. Tu
lis le rapport, pas le diff. Pour un petit correctif : `/quick-fix "description"`, même moteur au
niveau 0, qui monte de niveau si le périmètre grandit.

### 3. Prouver la qualité à la demande

```
/gate      # revue complète (niveau 3) du diff de la branche
/gate 1    # passe rapide, un seul relecteur
```

### 4. Livrer

```
/ship
```

Merge de la branche par défaut, preuves du manifeste, **consommation du gate file** (PASS frais →
PR directe ; périmé ou CONCERNS → nouveau gate ou waiver explicite), changelog, PR.

Le détail des niveaux, des phases et du moteur qualité est dans
**[docs/WORKFLOW.md](./docs/WORKFLOW.md)**.

---

## Le moteur qualité, en bref

- **`project-probe`** détecte une fois les commandes lint / typecheck / test / build du projet et
  les garde dans `.agents/verification.yaml`.
- **`quality-gate`** boucle : preuves d'exécution d'abord, puis revues en contexte neuf
  (correctness et sécurité, lisibilité, performance, design / SEO / a11y si concernés), puis
  `thermo-nuclear-code-quality-review` pour la maintenabilité. Chaque finding est contre-vérifié
  avant d'être corrigé. La boucle s'arrête après deux rounds propres, ou au plafond du niveau.
- **Le gate file** (`docs/quality/GATE-*.yaml`) lie le verdict au diff exact par SHA et hash ;
  `gate_verify.py` refuse un gate périmé ou retouché.

Règles dures : pas de PASS sans preuve exécutable (un projet sans tests plafonne à CONCERNS) ; un
CONCERNS n'est jamais accepté automatiquement ; la boucle est toujours bornée.

---

## Commandes

| Catégorie | Commande | Rôle |
|---|---|---|
| **Planifier** | `/discovery "idée"` | Planning niveaux 0-4, spec approuvée en sortie |
| **Développer** | `/dev [issue]` | Implémentation adaptative, un seul arrêt au plan, boucle quality-gate |
| | `/quick-fix "desc"` | Circuit court niveau 0, escalade automatique |
| **Qualité** | `/gate [niveau] [cible]` | Boucle quality-gate à la demande → gate file |
| | `/pr-review #123` | Revue d'une PR GitHub (3 passes + gates UI / SEO si besoin) |
| | `/qa [url]` | QA runtime systématique et score de santé |
| **Livrer** | `/ship` | Merge → preuves → gate → changelog → PR |
| **Réfléchir** | `/elicit [lentille] [cible]` | Ré-examiner une sortie sous une lentille nommée (12 disponibles) |
| | `/rodin <texte\|doc\|url>` | Challenge socratique anti-complaisance |
| | `/plan-review <doc>` | Relecture CEO/fondateur d'un plan (Expansion / Hold / Reduction) |
| **Auditer** | `/design-audit <cible>` | Audit UI / design system, preuve design pour le ship |
| | `/design-audit-squad <cible>` | Audit complet par les 12 agents Lyse Design Squad |
| | `/seo-geo-audit <cible>` | Audit SEO / GEO et visibilité dans les moteurs IA |
| | `/seo-geo-squad <cible>` | Orchestration SEO / GEO V3.1, 21 spécialistes routés |
| **Suivre** | `/status` | État du projet : Git, planning, gates, issues |
| | `/retro [--since 7d]` | Rétrospective engineering |
| | `/skillz-doctor` | Diagnostic de l'installation |
| **Mémoire** | `/wiki-bootstrap`, `/wiki-init` | Installer ou créer un vault Obsidian |
| | `/wiki-ingest`, `/wiki-capture-session` | Intégrer une source ou capturer une session |
| | `/wiki-query`, `/wiki-lint`, `/wiki-log` | Interroger, contrôler, consulter le log |

<details>
<summary><strong>Disponibilité selon l'agent</strong></summary>

Claude Code reçoit toutes les commandes ; Codex, Gemini et OpenCode reçoivent le sous-ensemble
portable.

| Commande | Claude | Codex | Gemini | OpenCode |
|---|---:|---:|---:|---:|
| `/dev`, `/discovery`, `/ship`, `/quick-fix`, `/qa`, `/status`, `/rodin` | Oui | Oui | Oui | Oui |
| `/design-audit(-squad)`, `/seo-geo-audit(-squad)` | Oui | Oui | Oui | Oui |
| `/elicit`, `/gate` | Oui | Oui | Non | Non |
| `/pr-review`, `/retro` et les autres utilitaires | Oui | Non | Non | Non |

</details>

---

## Skills

Les skills se déclenchent seuls à partir de leur description ; les commandes ci-dessus les chargent
explicitement.

**Moteur du workflow**

| Skill | Rôle |
|---|---|
| `discovery-workflow` | Moteur de `/discovery` : niveaux 0-4, spec approuvée |
| `dev-workflow` | Moteur de `/dev` et `/quick-fix` : probe → plan → implémentation → gate |
| `ship-workflow` | Moteur de `/ship` : merge, preuves, gate, changelog, PR |
| `status-workflow` | Moteur de `/status` : état du projet fondé sur des preuves, en lecture seule |
| `project-probe` | Détecte les commandes de vérification → `.agents/verification.yaml` |
| `quality-gate` | Boucle bornée de preuves et de revues → gate file |
| `thermo-nuclear-code-quality-review` | Dernière lentille du gate : maintenabilité structurelle stricte |

**Planification et réflexion**

| Skill | Rôle |
|---|---|
| `idea-brainstorm` | Brainstorming : 61 techniques, protocole anti-biais |
| `pm-prd` | PRD complet (niveaux 2-4) ou synthétique (0-1) |
| `architect` | Architecture technique : stack, structure, modèle de données, APIs |
| `pm-stories` | Epics et stories INVEST, publication en issues GitHub |
| `ux-designer` | Personas, parcours utilisateur, wireframes textuels |
| `ui-designer` | Design system, composants, direction visuelle |
| `elicitation` | 12 lentilles de raisonnement nommées (moteur de `/elicit`) |
| `rodin` | Challenge socratique anti-complaisance |

**Design et frontend**

| Skill | Rôle |
|---|---|
| `taste-router` | Choisit le taste-skill et règle ses 3 curseurs selon le brief |
| `taste-skill` | Frontend premium polyvalent, anti-« slop » |
| `soft-skill` | Rendu calme et haut de gamme, motion fluide |
| `minimalist-skill` | Éditorial type Notion / Linear |
| `redesign-skill` | Audit et montée en gamme d'une UI existante |
| `taste-critic` | Détecte le slop d'une UI (P0-P3) |
| `design-audit` | Audit UI / DS : tokens, composants, a11y, Figma, preuves runtime |
| `a11y-enforcer` | Audit WCAG 2.2 AA |
| `ai-native-ui` | Patterns d'interfaces IA : chat, copilots, agents |
| `landing-copy` | Copy de landing page premium |
| `product-microcopy` | Empty states, erreurs, tooltips, confirmations |
| `ds-doc` | Documente le design system dans `CLAUDE.md` |
| `figma-generate-library` | Construit le design system dans Figma depuis le code |
| `figma-design-code-sync` | Détecte et corrige la dérive entre Figma et le code |

Le reste de l'outillage Figma (`figma-use`, design-to-code, Code Connect…) vient du plugin officiel
`figma@claude-plugins-official`.

**Audits, web et mémoire**

| Skill | Rôle |
|---|---|
| `web-navigator` | Navigation et extraction sourcée (Playwright CLI, Browser / MCP, WebFetch) |
| `seo-geo-audit` | SEO / GEO V3.1 : 21 spécialistes, preuves structurées, suivi |
| `performance-auditor` | Lighthouse, Core Web Vitals, taille du bundle |
| `supabase-security` | Pentest Supabase : RLS, buckets, auth, clés exposées |
| `llm-wiki` | Maintient un wiki Obsidian persistant (moteur des `/wiki-*`) |
| `qmd` | Recherche locale dans les vaults et notes via les collections QMD |
| `skillz-writing-skills` | Guide pour créer ou modifier un skill de ce dépôt |

---

## Mémoire : Obsidian LLM Wiki

Une base de connaissances persistante (décisions, conventions, sources, synthèses) qui grandit d'une
session à l'autre, inspirée du [pattern LLM Wiki de Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
Installation, CLI `memory`, QMD et pointeurs par projet : **[docs/MEMORY.md](./docs/MEMORY.md)**.

---

## Compatibilité

Le compilateur produit un bundle par runtime dans `dist/<runtime>` : Claude Code, Codex CLI,
OpenCode, agents génériques (`AGENTS.md`), Gemini CLI, Grok Build et Kimi Code CLI. La compatibilité
est prouvée route par route :

| Niveau | Signification |
|---|---|
| **C1** | Bundle généré |
| **C2** | Découvert nativement par le runtime |
| **C3** | Comportement certifié sur une version épinglée |

Détail par runtime : [matrice v6.1](./docs/compatibility/matrix-v6.1.md).

<details>
<summary><strong>Structure du dépôt</strong></summary>

```text
core/
├── catalog.yaml          # graphe : identifiants, alias, ressources, métadonnées par runtime
├── skills/, commands/    # sources canoniques, neutres vis-à-vis des runtimes
├── knowledge/            # ressources partagées
└── contracts/            # schémas : artefacts, build, installateur, doctor, evals
providers/<runtime>/      # contrats de capacités et de build
tooling/                  # compilateur, installateur, evals, certification
dist/<runtime>/           # bundles générés et commités ; ne jamais éditer à la main
.claude/                  # miroir de compatibilité v6 (transitoire)
docs/compatibility/       # golden et preuves C1-C3
docs/quality/             # gates scellés et preuves JSON
```

</details>

---

## Aller plus loin

| Document | Contenu |
|---|---|
| [docs/INSTALL.md](./docs/INSTALL.md) | Toutes les méthodes d'installation |
| [docs/WORKFLOW.md](./docs/WORKFLOW.md) | Niveaux, phases, moteur qualité, ship |
| [docs/MEMORY.md](./docs/MEMORY.md) | Mémoire Obsidian et CLI `memory` |
| [docs/BEST-PRACTICES.md](./docs/BEST-PRACTICES.md) | Bonnes pratiques Claude Code |
| [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) | Résolution des problèmes courants |
| [docs/CONTRIBUTING-PROVIDERS.md](./docs/CONTRIBUTING-PROVIDERS.md) | Ajouter un artefact, un runtime ou une eval |
| [docs/migrations/](./docs/migrations/) | Guides de migration (v6 → v6.1, nettoyage des skills) |

## Contribuer

Ce projet est partagé **en lecture seule** : les pull requests et issues externes ne sont pas
acceptées. Tu es libre d'utiliser, copier et adapter ce workflow pour tes projets.

## Crédits

- **[BMAD-METHOD](https://github.com/bmadcode/BMAD-METHOD)** : fichiers de knowledge et structure
  des agents ; les gate files, niveaux adaptatifs et lentilles d'élicitation de la v6 s'en inspirent.
- **[rodin.md de Benjamin Debon](https://gist.github.com/bdebon/e22d0b728abc5f393227440907b334cf)** :
  posture socratique anti-écho du skill `rodin`.
- **[alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)** : base du
  LLM Wiki (MIT). Voir [ATTRIBUTION](./skills/ATTRIBUTION.md) pour tous les skills tiers.

## Historique

Voir [CHANGELOG.md](./CHANGELOG.md).
