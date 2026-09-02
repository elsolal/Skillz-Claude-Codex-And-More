---
title: "D-EPCT+R v6.1 — architecture provider-neutral et durcissement de la distribution"
document_id: plan.d-epct-v6-1-provider-neutral-hardening
version: "6.1"
lifecycle: current
superseded_by: null
amended_by: []
amends: []
status: draft
created_at: 2026-07-24
updated_at: 2026-09-01
owner: Aymeric
level: 4
source_audit: "ai-driven-dev/framework@1c41e0203465f67b84105c57cb08f7e804bc63d5"
source_recheck: "ai-driven-dev/framework@3082c8ff7f862df814f15f6e669a2005b50d3459"
source_release: "v5.9.0"
upstream_adoption_catalog: "docs/planning/upstream/aidd-v5.9.0/README.md"
implementation_requires_approved_spec: true
decisions:
  - remove_ralph
  - native_codex_plugin
  - provider_build_contracts
  - per_file_install_manifest
  - upstream_adoption_registry
---

# D-EPCT+R v6.1 — Architecture de référence et plan d'implémentation provider-neutral

> Ce document est un **plan d'exécution**, pas encore un mandat d'implémentation approuvé.
> Avant la première modification structurelle, consolider les décisions ouvertes dans une spec
> `docs/planning/specs/YYYY-MM-DD-provider-neutral-kernel-design.md` avec
> `status: approved` et `approved_by: human`.

**Mise à jour du 1er septembre 2026.** Le plan conserve son numéro 6.1 et intègre le recheck
d'`ai-driven-dev/framework` jusqu'à la release `v5.9.0`. Cette révision confirme la suppression de
RALPH et ajoute les mécanismes désormais suffisamment concrets pour guider l'implémentation :
plugin Codex natif, contrats de build par runtime et par artefact, drift hashé fichier par fichier,
harness d'évaluation comportementale et cycle de vie explicite des documents. Ces mécanismes sont
adaptés à D-EPCT+R ; le CLI TypeScript, l'orchestrateur autonome et les contournements de permissions
d'AIDD restent hors périmètre.

## 1. Décision exécutive

L'objectif n'est pas de remplacer D-EPCT+R par le framework AIDD. Le système existant reste le
produit principal et conserve son enchaînement adaptatif :

```text
PROBE → EXPLORE → PLAN → RED (conditionnel) → IMPLEMENT → GATE → HANDOFF
```

Le chantier v6.1 doit :

1. supprimer complètement RALPH et ses surfaces devenues inutiles ;
2. sortir la logique canonique de `.claude/` vers un noyau neutre ;
3. distribuer Codex comme plugin natif, et générer des adaptateurs natifs pour Claude Code,
   OpenCode, Kimi, Grok, Gemini et les agents génériques ;
4. prouver la compatibilité avec les runtimes réels, pas seulement avec des fichiers présents ;
5. durcir `project-probe`, `quality-gate`, l'installeur et les tests de distribution ;
6. reprendre d'AIDD uniquement les mécanismes qui améliorent la portabilité, l'évaluation et
   l'intégrité, sans importer son SDLC ni son orchestrateur asynchrone.

Oui, ce plan doit être plus détaillé que le résumé de l'audit : le risque principal n'est pas le
volume de code, mais une migration qui paraît multi-provider tout en cassant silencieusement la
découverte, les alias ou les garanties de qualité sur un runtime donné.

## 2. Résultats attendus

À la fin du chantier :

- aucune logique métier canonique ne dépend d'un répertoire nommé d'après un provider ;
- Claude, Codex et OpenCode sont certifiés comme cibles de premier rang ;
- Kimi et Grok disposent d'une route documentée et testable selon leur runtime réel ;
- les commandes et skills ont des **identifiants sémantiques stables**, même lorsque leur syntaxe
  native diffère selon l'hôte ;
- `install.sh` peut installer, mettre à jour, diagnostiquer et restaurer chaque cible sans écraser
  les fichiers utilisateur ;
- chaque build de distribution est reproductible et vérifié par des golden tests ;
- les skills critiques ont au moins un scénario comportemental automatisé ;
- Codex s'installe via son format plugin natif et la découverte est prouvée par le CLI, sans
  dépendre uniquement de copies dans `~/.codex/` ;
- chaque runtime implémente un contrat de build explicite pour les artefacts qu'il supporte et
  refuse proprement les autres ;
- le manifeste d'installation suit chaque fichier possédé avec son hash source et son hash
  installé afin de distinguer update légitime, drift utilisateur et fichier orphelin ;
- tout apport upstream possède une source épinglée, une décision d'adoption, une cible locale et
  des tests exigés dans le catalogue d'adoption ;
- un gate ne peut plus être déclaré frais à partir d'une preuve auto-déclarée ou modifiable hors
  du hash ;
- toutes les fonctions RALPH ont disparu du code, des docs, des hooks, des tests et des artefacts
  installés.

## 3. Décisions non négociables

### 3.1 Ce que l'on conserve

- D-EPCT+R et ses niveaux adaptatifs 0 à 4.
- Le stop humain au plan en mode manuel.
- La boucle bornée `quality-gate` et ses verdicts `PASS`, `CONCERNS`, `FAIL`, `WAIVED`.
- Les preuves exécutables avant les opinions de review.
- Les skills spécialisés existants et les workflows `/dev`, `/discovery`, `/quick-fix`, `/ship`,
  `/status`, `/pr-review`, `/qa` et les audits spécialisés.
- Le principe KISS/DRY/YAGNI et la migration progressive.

### 3.2 Ce que l'on supprime

- `/auto-loop`.
- `/auto-dev`.
- `/auto-discovery`.
- `/cancel-ralph`.
- `/resume-ralph`.
- Les hooks, fichiers d'état, promesses de sortie, timeouts et logs spécifiques à RALPH.
- Toute documentation ou test présentant RALPH comme mode supporté.

La suppression doit être complète. Une commande masquée ou un état résiduel continuerait à
augmenter la surface de maintenance et à brouiller le modèle mental du framework.

La suppression porte uniquement sur les artefacts **versionnés ou installés avec une preuve de
propriété Skillz**. Les fichiers locaux non suivis, notamment `.codex/hooks.json` et
`.codex/hooks/`, sont utilisateur-owned tant qu'aucun manifeste d'installation ne prouve le
contraire : ils ne doivent jamais être supprimés par un sweep de migration.

### 3.3 Ce que l'on n'importe pas d'AIDD

- Son cycle de développement comme remplacement de D-EPCT+R.
- Son orchestrateur GitHub asynchrone actuel.
- Les modes d'auto-acceptation ou de contournement des permissions.
- Une memory bank chargée systématiquement dans tous les contextes.
- Un découpage immédiat en plusieurs plugins indépendants.
- Des hooks qui indexent automatiquement des fichiers Git.
- Le CLI TypeScript complet d'AIDD et son prérequis Node `>=22.12` : v6.1 reprend les contrats,
  pas une plateforme de plus de 20 000 lignes.
- Le harness Claude-only utilisant `--dangerously-skip-permissions`.
- Des hooks de télémétrie ou d'installation dont la confiance, le chemin racine ou le chargement
  silencieux ne sont pas vérifiés par le runtime.
- Les backlogs, kanbans et banques mémoire parallèles déjà couverts par D-EPCT+R et `llm-wiki`.

Un orchestrateur asynchrone pourra être réévalué plus tard uniquement avec un besoin réel, une
nouvelle architecture et un threat model dédié.

### 3.4 Principe de portabilité

Un provider ou runtime n'est jamais « supporté » sur la seule base d'un dossier généré. Le support
est certifié à trois niveaux :

1. **Structurel** — les artefacts attendus sont générés et valides ;
2. **Découverte native** — le runtime ciblé liste ou charge effectivement les skills/commandes ;
3. **Comportemental** — un scénario minimal exécute la bonne intention et produit le bon contrat.

## 4. Vocabulaire et contrat de compatibilité

### 4.1 Distinguer modèle, provider et runtime hôte

Ces notions ne doivent plus être confondues :

| Notion | Exemple | Conséquence pour Skillz |
|---|---|---|
| Modèle | Kimi K3, Grok, GPT | Ne détermine pas à lui seul les chemins ou commandes disponibles. |
| Provider API | OpenAI, Moonshot, xAI | Définit l'accès au modèle, pas nécessairement le format des skills. |
| Runtime hôte | Codex, Claude Code, OpenCode, Kimi CLI, Grok Build | Définit la découverte, les aliases, hooks, permissions et MCP. |
| Adaptateur Skillz | `providers/codex`, `providers/kimi` | Compile le noyau neutre vers le contrat du runtime hôte. |

Exemple : Kimi utilisé via OpenCodex doit passer par l'adaptateur **Codex**. Un Kimi CLI natif doit
passer par l'adaptateur **Kimi**. Les deux routes peuvent utiliser le même modèle mais ne partagent
pas nécessairement la même surface d'intégration.

### 4.2 Garantie des aliases

Le framework garantit :

- le même identifiant sémantique, par exemple `workflow.dev` ;
- la même intention et les mêmes entrées/sorties ;
- un alias natif documenté pour chaque runtime lorsqu'il est supporté ;
- un fallback explicite lorsque le runtime ne fournit pas de slash command native.

Il ne garantit pas que la chaîne littérale `/dev` fonctionne partout si le runtime ne permet pas
ce type d'alias. Les écarts doivent être visibles dans le rapport de capacité, jamais cachés.

## 5. État de départ et deltas connus

### 5.1 Forces actuelles

- D-EPCT+R possède déjà un workflow cohérent, adaptatif et plus riche que le SDLC AIDD pour les
  besoins du projet.
- `project-probe` et `quality-gate` créent une bonne séparation entre preuve structurelle,
  exécution et opinion.
- L'installeur cible déjà plusieurs environnements.
- Les skills sont majoritairement structurés autour de `SKILL.md` et donc proches d'un format
  portable.
- `llm-wiki` dispose déjà d'un niveau de test sensiblement supérieur au reste du framework et peut
  servir de référence pour les futurs tests comportementaux.

### 5.2 Gaps à corriger

| Gap | Impact | Priorité |
|---|---|---|
| `.claude/` est annoncé comme source canonique | Dépendance conceptuelle et technique à Claude | P0 |
| Surfaces natives inégales entre runtimes | Fonctionnalités manquantes ou aliases divergents | P0 |
| RALPH maintenu mais non utilisé | Coût de maintenance et complexité inutile | P0 |
| `project-probe` ignore certaines vraies entrées dans son fingerprint | Manifeste faussement frais | P0 |
| Le gate exclut son propre contenu du hash | Preuve modifiable sans invalidation | P0 |
| `install.sh` dépend implicitement de la version Python trouvée | Tests différents selon le PATH | P0 |
| La vérification shell actuelle peut ne parser qu'un fichier | Preuve de syntaxe surestimée | P1 |
| Peu de tests comportementaux sur le noyau | Régressions invisibles malgré des manifests valides | P0 |
| Le skill Supabase annonce du read-only mais contient une mutation HTTP | Contrat de sécurité incohérent | P0 |
| Pas de manifeste d'installation hashé et restaurable | Drift difficile à diagnostiquer ou réparer | P1 |
| Skills volumineux et très branchés | Découverte correcte mais comportement difficile à évaluer | P1 |

### 5.3 Recheck upstream du 1er septembre 2026

Le baseline initial pointait le commit `1c41e020` du 22 juillet. Le recheck porte sur
`3082c8ff`, qui correspond à la release `v5.9.0` du 28 août. Le delta est important — 627 fichiers,
21 932 insertions et 5 269 suppressions — mais seules les idées suivantes sont reprises :

La machine de référence utilisait `codex-cli 0.152.0` au moment du recheck. Son aide locale confirme
les commandes `codex plugin add`, `list`, `remove` et `marketplace add/list/upgrade/remove`. Cela
prouve l'existence de la surface native, pas encore le chargement comportemental du futur bundle
Skillz ; ce dernier reste un gate C2/C3 à exécuter pendant l'implémentation.

| Évolution upstream | Décision v6.1 | Adaptation Skillz |
|---|---|---|
| Plugin Codex et marketplace natifs | Reprendre en P0 | Compiler un vrai `.codex-plugin/plugin.json`, enregistrer le marketplace, installer puis prouver `codex plugin list`. |
| `ToolBuildContract` par runtime | Reprendre le concept | Contrat déclaratif minimal, symétrique par type d'artefact ; pas de portage du CLI TypeScript. |
| Détection/restauration du drift par fichier | Reprendre | Hash source, hash installé, ownership et décision `restore/keep/conflict` dans un manifeste local. |
| Skill contract router/action/reference/assets | Adapter | Garder le français et les contrats Skillz ; appliquer « un fait, un foyer » et des actions testables aux skills complexes. |
| Behavioral eval harness | Reprendre et généraliser | Fixtures isolées, assertions fichiers/stdout, répétitions et plusieurs runtimes ; aucune permission contournée. |
| Mémoire check-before-write + marqueurs | Reprendre partiellement | Ajouter au système `llm-wiki` seulement la validation des marqueurs et le contrôle avant écriture. |
| Lentille de rétrospective | Reprendre | Ajouter délai évitable, rework, contexte manquant et automatisation utile à `/retro`. |
| Cycle de vie des documents | Reprendre | Métadonnées `current`, `superseded`, `superseded_by`, `amended_by` et validation des liens. |
| Orchestrateur autonome | Rejeter | RALPH est supprimé ; le stop humain et les gates D-EPCT+R restent structurants. |

### 5.4 Limites observées chez l'upstream

Ces limites deviennent des tests négatifs obligatoires, pas des raisons de rejeter toutes les
idées upstream :

- l'installation Codex peut réussir alors que le runtime ne charge aucun plugin en headless ;
- le routage des hooks Codex peut perdre les hooks ou résoudre incorrectement `PLUGIN_ROOT` ;
- un hook non approuvé peut être ignoré silencieusement ;
- les agents Codex générés ne sont pas encore nécessairement câblés par le manifest plugin ;
- OpenCode expose une API plugin JavaScript qui ne doit pas être confondue avec les hooks
  déclaratifs d'autres runtimes ;
- les mappings Kimi et Gemini proviennent encore de travaux ouverts et doivent être vérifiés sur
  les versions épinglées avant d'annoncer un support C2/C3 ;
- le CLI upstream possède une chaîne de dépendances Node plus large, avec un signal de vulnérabilité
  transitive à traiter côté upstream, ce qui renforce la décision de ne pas l'importer.

## 6. Architecture cible

### 6.1 Arborescence logique

```text
Skillz-Claude/
├── core/
│   ├── skills/                 # logique canonique provider-neutral
│   ├── workflows/              # workflows et actions sémantiques
│   ├── knowledge/              # références partagées à chargement explicite
│   ├── assets/                 # templates et ressources copiables
│   ├── contracts/              # schémas, capacités, résultats, gates
│   └── catalog.yaml            # registre des skills/workflows/aliases
├── providers/
│   ├── claude/                 # build-contract + transforms + manifest natif
│   ├── codex/                  # build-contract + .codex-plugin + marketplace
│   ├── opencode/
│   ├── kimi/
│   ├── grok/
│   ├── gemini/
│   └── agents-generic/
├── tooling/
│   ├── build/                  # compilateur et validateurs
│   ├── doctor/                 # diagnostic et rapport de capacités
│   ├── evals/                  # fixtures, assertions, runners et résultats
│   ├── upstream/               # registre, scanner read-only et rapports d'adoption
│   └── lifecycle/              # install/update/doctor/restore/uninstall
├── dist/                       # artefacts générés, jamais source canonique
├── docs/
└── install.sh
```

Le nom final de `core/` pourra devenir `src/`, mais la séparation canonique/adaptateur ne doit pas
changer.

### 6.2 Flux de production

```text
core + catalog + provider capabilities
                 │
                 ▼
          build déterministe
                 │
        ┌────────┼─────────┐
        ▼        ▼         ▼
     Claude    Codex    OpenCode ...
        │        │         │
        └────────┼─────────┘
                 ▼
    validation structurelle + golden diff
                 ▼
       runtime discovery smoke test
                 ▼
          behavioral eval report
```

### 6.3 Source canonique

- `core/`, `providers/` et les contrats sont éditables.
- `dist/` et les copies installées sont générés.
- Aucun fichier généré ne doit contenir une logique que le noyau ne possède pas.
- Les contributions restent possibles sans disposer de tous les runtimes : la CI structurelle
  valide toutes les cibles et les runners équipés certifient la découverte native.

### 6.4 Contrat de build par runtime et par artefact

Le compilateur ne doit pas contenir une succession de branches `if runtime == ...`. Chaque cible
implémente un `ProviderBuildContract` déclaratif et versionné. Il décrit séparément les six familles
d'artefacts : `instructions`, `skills`, `commands`, `agents`, `mcp` et `hooks`.

```yaml
schema_version: 1
runtime: codex
modes: [plugin, flat]
artifacts:
  instructions:
    strategy: copy
    target: AGENTS.md
  skills:
    strategy: copy_tree
    target: skills
  commands:
    strategy: unsupported
    fallback: skill_invocation
  agents:
    strategy: transform_toml
    target: agents
  mcp:
    strategy: merge_toml
    target: config.toml
  hooks:
    strategy: transform_json
    requires_runtime_probe: true
plugin:
  manifest: .codex-plugin/plugin.json
  marketplace: .agents/plugins/marketplace.json
```

Règles du contrat :

- une stratégie est pure : même entrée, même sortie, aucun accès au home utilisateur ;
- `unsupported` est un résultat valide et visible, jamais un skip silencieux ;
- la fusion de configuration produit un patch ou une structure intermédiaire, appliqué seulement
  par la couche lifecycle après contrôle d'ownership ;
- le build écrit d'abord dans un dossier temporaire, valide, puis effectue un remplacement
  atomique de `dist/<runtime>` ;
- l'ajout d'un runtime consiste à ajouter un contrat et ses transforms, pas à modifier les
  orchestrateurs génériques ;
- le build report liste pour chaque artefact `emitted`, `transformed`, `unsupported`, `skipped` ou
  `failed`, avec une raison obligatoire pour les trois derniers statuts.

### 6.5 Contrat interne d'un skill

Le Markdown reste canonique. Il n'est pas remplacé par un DSL propriétaire. Pour les skills
volumineux, la structure recommandée devient :

```text
core/skills/<skill>/
├── SKILL.md             # routeur court : déclenchement, choix de l'action, sortie
├── actions/             # procédures atomiques observables
├── references/          # faits détaillés, lus uniquement quand nécessaires
├── assets/              # templates et fichiers à copier
└── tests/               # cas structurels et comportementaux du skill
```

Contraintes : un fait a un seul foyer canonique ; le routeur lie vers les actions au lieu de les
dupliquer ; une action déclare préconditions, effets attendus et preuves observables ; les assets
ne contiennent aucune instruction cachée.

### 6.6 Responsabilités et frontières

| Composant | Responsabilité | Ne doit jamais |
|---|---|---|
| `core/catalog.yaml` | Référencer identifiants, sources, dépendances, risques et aliases. | Contenir des chemins home ou de la logique runtime. |
| `core/contracts/` | Définir les schémas stables de build, install, gate et eval. | Dépendre d'un provider ou d'un binaire local. |
| `providers/<runtime>/` | Déclarer capacités, chemins et transforms propres au runtime. | Dupliquer la logique métier d'un skill. |
| `tooling/build/` | Orchestrer validation et transforms pures vers `dist/`. | Écrire dans un home utilisateur. |
| `tooling/lifecycle/` | Appliquer install/update/restore après contrôle de drift. | Écraser un fichier sans ownership prouvé. |
| `tooling/doctor/` | Observer versions, paths, manifests, collisions et drift. | Réparer ou muter par défaut. |
| `tooling/evals/` | Exécuter fixtures et assertions structurelles/comportementales. | Contourner globalement les permissions. |
| `dist/<runtime>/` | Porter les bundles générés et inspectables. | Devenir une deuxième source canonique. |

### 6.7 Flux transactionnel d'une update

```text
bundle hashé
      │
      ▼
dry-run + lecture du manifeste précédent
      │
      ▼
comparaison fichier par fichier
      │
      ├── owned + inchangé ───────► remplaçable
      ├── owned + modifié ────────► conflit explicite
      ├── user-owned ─────────────► préserver
      └── ancien owned obsolète ──► proposer retrait
      │
      ▼
backup borné des fichiers Skillz touchés
      │
      ▼
écriture temporaire + validation + remplacement atomique
      │
      ▼
nouveau manifeste + doctor postcondition
      │
      ├── PASS ───────────────────► persistance atomique de l'état d'installation
      └── FAIL ───────────────────► restore du backup Skillz uniquement
```

La transaction concerne l'installation locale, pas Git ; aucun `git commit` n'est déclenché
automatiquement.

### 6.8 Source intake et adoption upstream

Le catalogue initial est versionné dans
[`docs/planning/upstream/aidd-v5.9.0/`](../upstream/aidd-v5.9.0/README.md). Il contient :

- l'[inventaire des 47 skills](../upstream/aidd-v5.9.0/skills-inventory.md), y compris ceux déjà
  couverts, en veille ou rejetés ;
- dix [fiches d'adoption](../upstream/aidd-v5.9.0/candidates/) pour les apports retenus ;
- les [mécanismes non-skill](../upstream/aidd-v5.9.0/mechanisms.md) : build contract, drift,
  behavioral evals, plugin Codex et lifecycle documentaire.

Le futur composant `tooling/upstream/` automatise l'inventaire, jamais la décision :

```text
sources.yaml + SHA épinglé
          │
          ▼
fetch/scan read-only dans un cache temporaire
          │
          ▼
delta skills/agents/commands/hooks/MCP/build/tests/docs
          │
          ▼
rapport candidats + preuves + licence + cible locale
          │
          ▼
checkpoint humain ADAPT / COVERED / WATCH / REJECT
          │
          ▼
réécriture locale + golden/behavioral tests
```

Contrat du registre de sources :

```yaml
schema_version: 1
sources:
  - id: ai-driven-dev-framework
    repository: https://github.com/ai-driven-dev/framework.git
    release: v5.9.0
    sha: 3082c8ff7f862df814f15f6e669a2005b50d3459
    license: MIT
    watch:
      - plugins/*/skills/**
      - cli/src/domain/tools/**
      - cli/src/application/use-cases/framework/**
      - scripts/skill-eval/**
```

Règles :

- aucun lien vers `main` ne sert de preuve d'adoption ;
- le scanner ne lance aucun code upstream et ne suit aucun hook ;
- un delta produit un rapport, jamais une modification automatique de `core/` ;
- une fiche `ADAPT` décrit ce qui est conservé, réécrit et rejeté ;
- une reprise substantielle respecte la licence et conserve l'avis requis ;
- install, update et build restent hermétiques et ne contactent jamais l'upstream ;
- une nouvelle release upstream crée une nouvelle comparaison `from_sha → to_sha` et préserve les
  décisions antérieures dans l'historique.

## 7. Contrat de capacités par runtime

Chaque adaptateur doit exposer un manifeste versionné, par exemple
`providers/<runtime>/capabilities.yaml`, contenant au minimum :

```yaml
schema_version: 1
runtime: codex
runtime_version_observed: "0.152.0"
observed_at: "2026-09-01"
adapter_version: "1"
distribution:
  native_plugin_format: true
  manifest: ".codex-plugin/plugin.json"
  marketplace: ".agents/plugins/marketplace.json"
  install_command: "codex plugin add"
  discovery_command: "codex plugin list"
instructions:
  supported: true
  native_files: ["AGENTS.md"]
skills:
  supported: true
  discovery_paths: ["~/.codex/skills", "~/.agents/skills"]
commands:
  native_aliases: false
  fallback: "skill invocation"
hooks:
  supported: pending
  reason: "requires trust and PLUGIN_ROOT runtime verification"
subagents:
  emitted: true
  native_discovery: pending
mcp:
  supported: true
config_merge:
  strategy: "preserve-user-owned-keys"
certification:
  structural: pending
  discovery: pending
  behavioral: pending
unsupported: []
```

Règles :

- chaque champ `supported: true` exige une preuve testée sur la version déclarée ;
- `pending` interdit la publication d'une promesse de support et exige un test négatif de non-
  chargement silencieux ;
- une capacité absente vaut `false` avec raison et fallback ;
- les versions testées sont épinglées dans les rapports, sans promettre une compatibilité future ;
- `skillz doctor` compare le runtime local à la plage certifiée et affiche un avertissement en cas
  de drift ;
- une cible partielle reste utilisable, mais son niveau de certification est affiché.

## 8. Matrice initiale des cibles

| Cible | Vague | Route | Attente initiale |
|---|---:|---|---|
| Codex | P0 | Plugin natif + flat de secours | `.codex-plugin/plugin.json`, marketplace, skills, AGENTS, MCP, config et fallback sémantique des commandes. |
| Claude Code | P0 | Runtime natif | Skills, commandes, hooks, subagents et plugin natif. |
| OpenCode | P0 | Runtime natif | Skills, commandes/config natives et chemins `.agents` compatibles. |
| Agents génériques | P0 | Convention AGENTS.md | Instructions + skills standards, sans capacité inventée. |
| Kimi via OpenCodex | P0 | Adaptateur Codex | Même certification que Codex, provider modèle documenté séparément. |
| Kimi CLI natif | P1 | Adaptateur Kimi | Candidats à vérifier : skills `.agents/skills`, agents `.kimi-code/agents` ou `.agents/agents`; hooks/MCP/commandes restent inconnus. |
| Grok Build | P1 | Adaptateur Grok | À certifier après installation et pin de version. |
| Gemini CLI | P2 | Extension Gemini | Candidats à vérifier : skills `.agents/skills`, agents `.gemini/agents`, MCP/hooks dans `.gemini/settings.json`, instructions via `context.fileName`. |

## 9. Stratégie de migration

La migration ne doit pas être un big bang. Après chaque PR :

- le framework reste installable ;
- Claude, Codex et OpenCode gardent leurs surfaces existantes ou un fallback documenté ;
- les artefacts legacy et nouveaux sont comparés avant bascule ;
- le rollback consiste à réutiliser le dernier build certifié, pas à reconstruire à la main.

Ordre recommandé : retirer d'abord le code mort, sécuriser les preuves, introduire le noyau et le
compilateur, migrer un vertical slice, puis déplacer progressivement les skills restants.

### 9.1 Invariants de migration

- Une PR de déplacement ne change pas simultanément le comportement métier du skill.
- Toute suppression d'un artefact installé exige une preuve d'ownership antérieure.
- Aucun outil de migration ne parcourt ou ne supprime les hooks locaux non suivis.
- Un runtime qui échoue à charger un artefact rend la certification rouge même si l'installation
  a retourné un code 0.
- Les sorties legacy et v6.1 coexistent jusqu'à preuve d'équivalence du vertical slice.
- Chaque document actif déclare son statut ; toute spec remplacée pointe vers son successeur.

## 10. Vague 0 — Baseline, décisions et garde-fous

### Objectif

Transformer l'audit en baseline reproductible avant toute migration.

### Travaux

- [ ] Créer la spec consolidée `docs/planning/specs/2026-09-01-provider-neutral-kernel-design.md`.
- [ ] Faire approuver explicitement : arborescence, niveau de garantie des aliases, cibles P0/P1,
      politique de `dist/` et stratégie de compatibilité transitoire.
- [ ] Capturer l'inventaire machine-lisible des skills, commandes, hooks, agents, manifests et
      chemins installés actuels.
- [ ] Capturer les versions réelles de Codex, Claude Code, OpenCode et des runtimes optionnels.
- [ ] Produire une matrice baseline `docs/compatibility/baseline-2026-09-01.yaml`.
- [ ] Enregistrer le recheck `ai-driven-dev/framework@3082c8ff` et les URLs de provenance en
      données de baseline, sans dépendance runtime au repo upstream.
- [ ] Valider le catalogue
      [`docs/planning/upstream/aidd-v5.9.0/`](../upstream/aidd-v5.9.0/README.md) et ses décisions
      `ADAPT/COVERED/WATCH/REJECT` dans la spec consolidée.
- [ ] Ajouter un rapport des commandes/skills actuellement exposés par runtime.
- [ ] Identifier les fichiers générés actuellement modifiés à la main et leur source supposée.
- [ ] Définir une règle explicite de non-écrasement des configurations utilisateur.
- [ ] Geler des snapshots golden de la distribution actuelle avant migration.

### Critères d'acceptation

- [ ] Chaque surface actuelle a un propriétaire canonique ou est marquée `legacy/orphan`.
- [ ] Chaque cible possède un statut `installed`, `broken`, `not-installed` ou `not-tested`.
- [ ] La spec est `approved` par l'humain.
- [ ] Les fichiers utilisateur non liés au chantier sont listés et exclus des opérations de build.

### Vérification

- Inventaire déterministe exécuté deux fois avec résultat identique.
- `git status --short` ne montre aucun fichier utilisateur modifié par la capture.
- Golden snapshots lisibles en revue sans secret ni chemin personnel sensible.

## 11. Vague 1 — Suppression complète de RALPH

### Objectif

Réduire immédiatement la surface avant d'introduire la nouvelle architecture.

### Travaux

- [ ] Partir de l'inventaire versionné confirmé au 1er septembre :
  `.claude/commands/{auto-loop,auto-dev,auto-discovery,cancel-ralph,resume-ralph}.md`,
  `.claude/skills/source-command-cancel-ralph/`, `.claude/hooks/stop-hook.sh`, le hook `Stop` de
  `.claude/settings.json`, les branches RALPH de `install.sh`, les launchers et la documentation.
- [ ] Inventorier toutes les occurrences, y compris variantes de casse et noms indirects :
      `ralph`, `auto-loop`, `auto-dev`, `auto-discovery`, `cancel-ralph`, `resume-ralph`,
      `ralph-logs`, promesses et états.
- [ ] Supprimer les commandes et launchers RALPH de toutes les cibles.
- [ ] Supprimer les hooks d'arrêt/reprise et scripts d'état exclusivement utilisés par RALPH.
- [ ] Supprimer les tests et fixtures devenus sans objet ; convertir en tests manuels uniquement
      les scénarios encore utiles au workflow normal.
- [ ] Retirer RALPH du README, d'AGENTS.md, de CLAUDE.md, de GEMINI.md, des exemples et de l'aide.
- [ ] Modifier `discovery-workflow` pour que toute spec reste humainement approuvée, sans statut ou
      auteur artificiel `ralph`.
- [ ] Modifier `dev-workflow` pour supprimer les branches conditionnelles autonomes.
- [ ] Supprimer `docs/ralph-logs/` du contrat documentaire ; conserver l'historique Git sans
      supprimer de preuves encore utiles dans les branches existantes.
- [ ] Ajouter un test repo-wide interdisant le retour des tokens RALPH hors changelog/migration.
- [ ] Ajouter une note de migration expliquant les commandes retirées et les alternatives manuelles.

### Critères d'acceptation

- [ ] Aucun artefact installé ne propose une commande RALPH.
- [ ] Aucun hook runtime ne dépend d'un fichier d'état RALPH.
- [ ] `/dev` et `/discovery` manuels restent fonctionnels.
- [ ] La recherche repo-wide ne trouve que la note historique autorisée.
- [ ] L'installeur d'update retire proprement les anciens artefacts RALPH qu'il avait installés,
      sans effacer un fichier utilisateur homonyme non possédé.
- [ ] `.codex/hooks.json`, `.codex/hooks/` et `.claude/settings.local.json` non suivis restent
      byte-identical après migration, sauf consentement explicite et preuve d'ownership.

### Rollback

La dernière release v6 reste installable. Le manifeste de propriété doit permettre de restaurer
les anciens fichiers uniquement si l'utilisateur choisit explicitement de revenir en arrière.
Le rollback peut réintroduire RALPH uniquement en revenant au bundle v6 complet ; v6.1 ne conserve
aucun code RALPH dormant ni feature flag caché.

## 12. Vague 2 — Durcissement du noyau de vérification

### 12.1 `project-probe` v2

- [ ] Remplacer la liste réduite de fingerprint par un collecteur versionné couvrant : scripts
      shell, skills/workflows Markdown, manifests provider, CI, lockfiles et fichiers de config
      réellement consommés.
- [ ] Trier les entrées de façon déterministe et hasher à la fois leur chemin et leur contenu.
- [ ] Ajouter `fingerprint_schema_version` et `generated_by` au manifeste.
- [ ] Enregistrer les raisons d'absence et les sources de chaque commande détectée.
- [ ] Ajouter une détection explicite de la version Python requise par les outils du repo.
- [ ] Rendre la sonde non destructive et tester les scripts suspects via allowlist.
- [ ] Ajouter des fixtures Node, Python, shell-only, monorepo et projet mixte.

### 12.2 `quality-gate` v2

- [ ] Versionner le schéma du gate.
- [ ] Rendre `base_sha` et `head_sha` obligatoires.
- [ ] Séparer le hash du diff de code du hash du payload de preuve.
- [ ] Inclure le contenu du gate dans une enveloppe d'intégrité au lieu de lui faire confiance.
- [ ] Ajouter une commande mécanique `gate verify` qui contrôle schéma, SHAs, diff, payload et
      statut des commandes.
- [ ] Refuser un gate dont le commit courant ne correspond pas à `head_sha`.
- [ ] Documenter précisément les exclusions autorisées ; aucune exclusion implicite de
      `docs/quality` ne doit permettre de modifier la preuve sans invalidation.
- [ ] Préparer un futur GitHub Check indépendant, sans le rendre bloquant avant validation locale.

### 12.3 Outillage et tests

- [ ] Déclarer Python `>=3.10` là où il est requis et faire échouer tôt avec un message précis.
- [ ] Éviter le `python3` ambigu : détecter et journaliser l'interpréteur réellement sélectionné.
- [ ] Corriger la preuve de syntaxe shell avec une boucle par fichier ou un linter dédié.
- [ ] Ajouter tests positifs et négatifs : gate frais, gate stale, payload modifié, SHA absent,
      commande inventée, fingerprint inchangé et fingerprint modifié.
- [ ] Réparer le contrat du skill Supabase : soit strictement read-only, soit mutation explicite
      uniquement en sandbox avec autorisation et rollback réellement démontré.

### Critères d'acceptation

- [ ] Une modification d'un skill critique invalide le fingerprint.
- [ ] Une modification manuelle du gate invalide `gate verify`.
- [ ] Le test shell couvre individuellement tous les scripts ciblés.
- [ ] Les tests passent avec un interpréteur déclaré et échouent proprement avec Python 3.9.
- [ ] Aucun skill annoncé read-only n'effectue une mutation réseau.

## 13. Vague 3 — Noyau neutre, catalog et compilateur

### Objectif

Introduire la nouvelle architecture sans migrer immédiatement tous les skills.

### Travaux

- [ ] Créer `core/`, `providers/`, `tooling/` et les schémas initiaux.
- [ ] Définir `core/catalog.yaml` avec : identifiant stable, nom public, type, source, dépendances,
      inputs, outputs, aliases souhaités, providers requis et niveau de risque.
- [ ] Définir le schéma des capacités provider.
- [ ] Créer `tooling/upstream/sources.yaml` et le scanner read-only qui produit l'inventaire du
      delta sans exécuter de contenu upstream.
- [ ] Définir `ProviderBuildContract` et `ArtifactContract` ; le second doit couvrir symétriquement
      instructions, skills, commands, agents, MCP et hooks.
- [ ] Définir un Intermediate Representation minimal pour les métadonnées et wrappers, sans
      transformer le Markdown métier en DSL propriétaire.
- [ ] Construire un compilateur déterministe qui :
  - [ ] lit le catalog et les contrats ;
  - [ ] valide les références ;
  - [ ] résout les aliases par provider ;
  - [ ] génère les wrappers et manifests ;
  - [ ] applique uniquement les transforms pures déclarées par le contrat du runtime ;
  - [ ] refuse une capacité déclarée mais non implémentée ;
  - [ ] écrit dans un répertoire temporaire avant toute installation ;
  - [ ] produit un rapport de build machine-lisible.
- [ ] Ajouter `build --check` pour comparer le résultat au `dist/` attendu sans écrire.
- [ ] Ajouter des diagnostics de collision d'alias, dépendance manquante et fichier orphelin.
- [ ] Définir la politique Git de `dist/` : committé pour inspection ou produit de release. La
      décision doit être prise dans la spec avant implémentation.

### Vertical slice pilote

Migrer uniquement :

- [ ] `project-probe` ;
- [ ] `quality-gate` ;
- [ ] `status-workflow` ;
- [ ] un workflow simple comme `/quick-fix`.

Ce slice doit traverser tout le pipeline jusqu'à Claude, Codex et OpenCode avant d'élargir la
migration.

### Critères d'acceptation

- [ ] Deux builds consécutifs produisent exactement les mêmes hashes.
- [ ] L'ajout d'une cible fixture ne modifie pas l'orchestrateur de build générique.
- [ ] Chaque artefact supporté, non supporté ou pending apparaît dans le build report.
- [ ] Aucun wrapper généré n'est édité à la main.
- [ ] Une collision d'alias bloque le build avec un diagnostic actionnable.
- [ ] Les versions legacy et compilées du vertical slice ont le même comportement observable.

## 14. Vague 4 — Adaptateurs et aliases multi-runtime

### 14.1 Claude Code

- [ ] Générer plugin manifest, skills, commandes et hooks depuis le noyau.
- [ ] Préserver les clés et fichiers utilisateur non possédés par Skillz.
- [ ] Tester la découverte native des commandes et skills.
- [ ] Vérifier que les subagents et hooks ne sont utilisés que si la capacité est déclarée.

### 14.2 Codex

- [ ] Remplacer l'hypothèse actuelle « Codex n'a pas de plugin natif » dans `install.sh` et la
      documentation : le CLI observé expose `codex plugin add/list` et les marketplaces.
- [ ] Générer `.codex-plugin/plugin.json` et `.agents/plugins/marketplace.json` depuis le catalog.
- [ ] Générer les skills dans le bundle plugin, avec une route flat explicite uniquement pour le
      mode legacy ou le diagnostic.
- [ ] Générer/maintenir AGENTS.md comme surface d'instructions, pas comme duplication du noyau.
- [ ] Fournir les aliases sémantiques via le mécanisme disponible ; documenter le fallback si les
      slash commands littérales ne sont pas natives.
- [ ] Tester la découverte avec le binaire Codex épinglé.
- [ ] Prouver successivement : marketplace enregistrée, plugin installé, plugin listé, skill
      invoqué et comportement attendu observé dans une session isolée.
- [ ] Tester le mode headless séparément : un code de sortie 0 sans plugin réellement chargé est
      un échec.
- [ ] Tester hooks et `PLUGIN_ROOT` en fail-closed ; si le runtime ignore un hook non approuvé, le
      rapport doit être `pending/blocked`, jamais `PASS`.
- [ ] Ne déclarer les agents supportés qu'après découverte native ; leur simple transformation en
      TOML vaut uniquement une preuve C1.
- [ ] Tester la coexistence avec un provider modèle alternatif comme Kimi via OpenCodex.

### 14.3 OpenCode

- [ ] Générer les skills et commandes dans les chemins natifs OpenCode.
- [ ] Tester la priorité entre `.opencode`, `.agents` et les chemins compatibles Claude.
- [ ] Éviter les doublons lorsque plusieurs chemins sont visibles simultanément.
- [ ] Tester la découverte avec la version épinglée.

### 14.4 Kimi CLI natif

- [ ] Réparer ou réinstaller le runtime local avant certification.
- [ ] Épingler la version testée et vérifier `SKILL.md`, `--skills-dir` et l'invocation native.
- [ ] Générer les artefacts Kimi uniquement si le runtime est disponible ou lors d'un build CI
      structurel ; ne pas annoncer la certification locale sans exécution.
- [ ] Distinguer clairement cette route de Kimi via Codex/OpenCodex.

### 14.5 Grok Build

- [ ] Installer dans un environnement isolé ou utiliser un runner dédié.
- [ ] Épingler la version et vérifier skills, AGENTS.md, plugins, hooks et MCP au lieu de reprendre
      des promesses marketing comme contrat.
- [ ] Créer l'adaptateur sur la base des capacités réellement observées.
- [ ] Marquer explicitement les fonctions non vérifiées.

### 14.6 Gemini et agents génériques

- [ ] Migrer l'extension Gemini existante vers la génération par catalog.
- [ ] Conserver un fallback AGENTS.md + skills pour les agents génériques.
- [ ] Ne pas simuler commandes, hooks ou subagents sur une cible qui ne les fournit pas.

### Critères d'acceptation communs

- [ ] Chaque provider a un `capabilities.yaml` valide.
- [ ] Chaque capacité vraie possède une preuve et une version testée.
- [ ] Chaque écart d'alias est documenté avec son invocation exacte.
- [ ] Aucun adaptateur ne contient de logique métier divergente du noyau.

## 15. Vague 5 — Distribution, installation, doctor et restauration

### Travaux

- [ ] Faire consommer au nouvel installeur uniquement les artefacts issus du build.
- [ ] Créer un manifeste d'installation par cible avec chemin, hash, source et propriétaire.
- [ ] Avant écrasement, comparer le hash installé au dernier hash possédé par Skillz.
- [ ] Refuser d'écraser silencieusement un fichier modifié par l'utilisateur.
- [ ] Implémenter une sauvegarde locale bornée et une restauration explicite.
- [ ] Ajouter `skillz doctor` avec : runtimes détectés, versions, chemins, collisions, drift,
      certification et commandes de réparation.
- [ ] Ajouter un mode `--dry-run` à install/update/uninstall/restore.
- [ ] Garantir qu'un uninstall ne retire que les fichiers présents dans le manifeste de propriété.
- [ ] Tester installation fraîche, update, downgrade, fichiers utilisateur modifiés, runtime absent,
      lien symbolique cassé et chemin contenant des espaces.
- [ ] Produire un rapport JSON en plus de la sortie humaine.

### 15.1 Contrat du manifeste d'installation

```yaml
schema_version: 1
install_id: "<uuid>"
release: "6.1.0"
runtime: codex
installed_at: "<iso-8601>"
files:
  - path: "<resolved-relative-path>"
    artifact: skill
    source_id: "skill.project-probe"
    source_hash: "sha256:<hash>"
    installed_hash: "sha256:<hash>"
    ownership: skillz
    merge_strategy: replace_owned
```

Le manifeste ne stocke aucun secret ni chemin de home portable dans Git. Il vit dans l'état local
de l'installation et peut être exporté sous forme redacted. `source_hash` prouve le bundle attendu ;
`installed_hash` permet de détecter une modification après installation. La restauration centralise
la décision `restore`, `keep` ou `conflict` pour éviter que chaque runtime invente sa politique.

### Critères d'acceptation

- [ ] Une update ne modifie aucun fichier utilisateur non possédé.
- [ ] Un fichier Skillz modifié localement déclenche un conflit explicite.
- [ ] Une installation peut être restaurée à son état précédent.
- [ ] `doctor` explique précisément pourquoi une cible est partielle ou cassée.
- [ ] `doctor` distingue `missing`, `modified`, `unexpected`, `orphaned` et `unverifiable` fichier
      par fichier.

## 16. Vague 6 — Golden tests et certification comportementale

### 16.1 Golden distribution tests

- [ ] Snapshotter par provider l'arborescence, les manifests, frontmatters et aliases générés.
- [ ] Normaliser uniquement les valeurs réellement non déterministes.
- [ ] Exiger une revue explicite pour toute mise à jour de golden.
- [ ] Tester les suppressions de fichiers obsolètes, pas uniquement les ajouts.
- [ ] Vérifier qu'aucune référence Claude-only n'apparaît dans le noyau neutre.

### 16.2 Behavioral evals

Définir un format minimal :

```yaml
id: dev-level-1-plan-stop
runtime: codex
skill: workflow.dev
fixture: node-small-fix
input: "Corrige le bug décrit dans l'issue simulée"
repeat: 3
timeout_seconds: 180
permissions: workspace_fixture_only
expect:
  events_in_order: [probe, explore, plan]
  files_exist: [".agents/verification.yaml"]
  files_absent: [".git/refs/heads/unexpected"]
  files_unchanged: ["package-lock.json"]
  file_contains:
    "run-result.json": ["plan_is_presented_before_write"]
  file_matches:
    "run-result.json": ["\\\"verdict\\\":\\s*\\\"PASS\\\""]
  stdout_contains: ["Plan"]
```

- [ ] Créer des fixtures locales sans secret ni dépendance réseau obligatoire.
- [ ] Exécuter chaque cas dans un répertoire temporaire isolé et enregistrer runtime, version,
      modèle, seed éventuelle, durée, code de sortie et hashes avant/après.
- [ ] Évaluer d'abord les invariants critiques, pas la formulation exacte du texte.
- [ ] Ajouter des scénarios pour `/dev`, `/discovery`, `/quick-fix`, `/ship`, `project-probe`,
      `quality-gate` et `status`.
- [ ] Ajouter des scénarios négatifs : runtime sans capacité, alias absent, gate stale, permission
      refusée, test rouge et configuration utilisateur en conflit.
- [ ] Produire un `run-result.json` versionné comme seam d'intégration entre exécution, CI et audit.
- [ ] Supporter `--case`, `--repeat` et `--jobs`, avec agrégation des résultats et conservation des
      échecs reproductibles.
- [ ] Créer un runner par runtime derrière une interface commune ; aucun runner ne peut ajouter
      automatiquement `--dangerously-skip-permissions` ou son équivalent.
- [ ] Ajouter des assertions génériques `filesExist`, `filesAbsent`, `filesUnchanged`,
      `fileContains`, `fileMatches`, stdout et séquence d'événements.
- [ ] Ajouter un cas Codex plugin headless qui échoue si l'installation est réussie mais que le
      skill attendu n'est pas chargé.
- [ ] Ajouter un cas Gemini qui vérifie réellement `context.fileName`, la confiance du projet et
      la lecture de `.gemini/settings.json` avant de dépasser C1.
- [ ] Ancrer chaque review sur `base_sha`/`head_sha` pour éviter la review d'un diff mouvant.

### 16.3 Niveaux de certification

| Niveau | Preuve | Libellé autorisé |
|---|---|---|
| C0 | Build non exécuté | non supporté |
| C1 | Structure + golden | générable |
| C2 | Découverte native | compatible structurellement |
| C3 | Behavioral smoke | certifié sur version X |

Seul C3 autorise le mot « supporté » sans qualification dans la documentation utilisateur.

## 17. Vague 7 — Migration progressive du catalogue

### Ordre recommandé

1. Noyau workflow : `project-probe`, `quality-gate`, `dev-workflow`, `discovery-workflow`,
   `ship-workflow`, `status-workflow`, `quick-fix`.
2. Développement : architecture, implémentation, review, tests, sécurité.
3. Produit et planning : PRD, stories, elicitation, brainstorm.
4. Design/frontend : routeurs, audits, accessibilité, Figma, taste skills.
5. SEO, data et domaines spécialisés.
6. Wiki et utilitaires.

### Pour chaque lot

- [ ] Identifier la source legacy et ses wrappers.
- [ ] Déplacer la logique canonique vers `core/` sans changement fonctionnel intentionnel.
- [ ] Enregistrer dependencies, aliases et capacités dans le catalog.
- [ ] Générer toutes les cibles.
- [ ] Comparer aux golden snapshots.
- [ ] Exécuter au moins un behavioral smoke sur les cibles P0.
- [ ] Supprimer la source legacy uniquement après preuve d'équivalence.
- [ ] Mettre à jour la documentation et le rapport de compatibilité.

### Règle de taille

Une PR de migration ne doit pas mélanger :

- changement fonctionnel du skill ;
- déplacement de sa source canonique ;
- changement du compilateur.

Si un bug est découvert pendant la migration, le corriger dans une PR dédiée ou le documenter pour
la vague suivante afin de préserver une comparaison lisible.

## 18. Vague 8 — Router skills et onboarding guidé

### Router + actions atomiques

Reprendre l'idée AIDD uniquement pour les skills très branchés :

- [ ] Définir des seuils de décomposition : taille, nombre de branches, dépendances et taux d'échec.
- [ ] Transformer un gros skill pilote en router léger qui choisit une action atomique.
- [ ] Garder le contrat utilisateur stable.
- [ ] Mesurer contexte chargé, taux de réussite et temps avant/après.
- [ ] Généraliser seulement si le pilote apporte un gain réel.

### `/status` comme guide d'état

- [ ] Détecter l'état actuel : non installé, installé partiellement, projet non probé, plan en attente,
      implémentation en cours, gate stale, prêt à shipper.
- [ ] Proposer une prochaine action justifiée, sans l'exécuter automatiquement.
- [ ] Afficher les capacités runtime disponibles et les limitations.
- [ ] Éviter un assistant d'onboarding séparé si `/status` suffit.

### Écritures mémoire contrôlées

`llm-wiki` reste le système mémoire de Skillz. v6.1 n'importe pas la memory bank AIDD. Il ajoute
seulement deux garde-fous composables :

- [ ] effectuer un `check-before-write` pour détecter doublon, page canonique et contradiction
      avant toute création ou mise à jour ;
- [ ] délimiter les projections générées avec des marqueurs versionnés et valider les marqueurs
      non appariés, fences cassées et imports/liens invalides ;
- [ ] refuser de régénérer une zone dont les marqueurs sont absents ou ont été modifiés par
      l'utilisateur ;
- [ ] tester ces règles dans les tests existants de `llm-wiki` sans imposer une nouvelle base de
      données ni un chargement mémoire global.

### Rétrospective orientée rework

Compléter `/retro`, aujourd'hui surtout métrique, avec quatre questions stables :

1. Quel délai ou détour aurait pu être évité ?
2. Quel rework a été provoqué par une hypothèse ou une preuve insuffisante ?
3. Quel contexte manquait au moment de décider ?
4. Quelle étape doit être supprimée, simplifiée ou automatisée la prochaine fois ?

Les réponses restent des observations proposées à l'humain ; elles ne déclenchent aucune mutation
automatique du workflow.

### Cycle de vie des documents de planification

Ajouter un schéma léger au frontmatter des plans, specs, PRD et architectures :

```yaml
lifecycle: current        # current | superseded | archived
superseded_by: null       # chemin relatif obligatoire si superseded
amended_by: []            # documents qui complètent sans remplacer
```

- [ ] Un validateur refuse deux documents `current` pour le même `document_id` et la même version.
- [ ] Un document `superseded` doit pointer vers un fichier existant.
- [ ] Un lien `amended_by` est bidirectionnel ou signalé comme incomplet.
- [ ] Les documents historiques RALPH peuvent rester consultables dans Git ou être marqués
      `superseded`; ils ne doivent plus être interprétés comme instructions actives.

### Critères d'acceptation

- [ ] Le router pilote charge moins de contexte sans réduire les assertions réussies.
- [ ] `/status` n'invente jamais l'état d'une phase ; chaque proposition cite sa preuve locale.
- [ ] Les écritures mémoire et transitions documentaires échouent proprement sur drift utilisateur.

## 19. Vague 9 — Documentation, release et nettoyage

- [ ] Réécrire README autour du noyau neutre et des runtimes, pas autour de Claude.
- [ ] Documenter la différence modèle/provider/runtime avec les cas Kimi et Grok.
- [ ] Publier la matrice de compatibilité et les versions certifiées.
- [ ] Documenter les aliases exacts et fallbacks par cible.
- [ ] Documenter build, contribution, ajout d'un provider et ajout d'un behavioral eval.
- [ ] Documenter le format plugin Codex natif et le fallback flat, sans promettre que les deux ont
      le même niveau de certification.
- [ ] Ajouter le guide de migration depuis v6 et le retrait de RALPH.
- [ ] Générer un changelog détaillé avec breaking changes.
- [ ] Exécuter install/update/doctor/uninstall sur environnements propres par cible P0.
- [ ] Produire les rapports de certification C1-C3.
- [ ] Créer une release candidate, la laisser tourner sur des usages réels, puis corriger les écarts.
- [ ] Ne déclarer v6.1 stable qu'après un gate frais et une certification C3 des cibles P0.

## 20. Découpage recommandé en PRs

| PR | Contenu | Dépend de |
|---:|---|---|
| 1 | Baseline, spec approuvée, inventaire et golden legacy | — |
| 2 | Suppression RALPH + migration docs | PR 1 |
| 3 | `project-probe` v2 + runtime Python explicite | PR 1 |
| 4 | `quality-gate` v2 + `gate verify` | PR 3 |
| 5 | Schémas, catalog, capabilities et compilateur minimal | PR 1 |
| 6 | Plugin Codex natif + vertical slice P0 Claude/Codex/OpenCode | PR 4, PR 5 |
| 7 | Installeur manifesté, doctor et restore | PR 6 |
| 8 | Golden CI + behavioral harness + `run-result.json` | PR 6, PR 7 |
| 9 | Adaptateurs Kimi natif, Grok, Gemini | PR 8 |
| 10+ | Migration des lots de skills | PR 8 |
| transversale | Router pilote, mémoire contrôlée, `/retro` et lifecycle documentaire | PR 8 |
| finale | Status guidé, docs, certifications et release candidate | lots critiques |

Chaque PR doit rester livrable et disposer de son propre quality gate. Les PRs 3 et 5 peuvent être
préparées en parallèle après la baseline, mais leurs migrations ne doivent pas modifier les mêmes
fichiers.

## 21. Graphe de dépendances

```text
Baseline/spec
├── Suppression RALPH
├── project-probe v2 ──► quality-gate v2
└── catalog/compilateur ───────────────┐
                                       ▼
                     vertical slice multi-runtime
                         ├── installer/doctor/restore
                         └── golden + behavioral evals
                                      │
                   ┌──────────────────┴───────────────┐
                   ▼                                  ▼
           migration catalogue              Kimi/Grok/Gemini
                   └──────────────────┬───────────────┘
                                      ▼
                         router/status/docs/release
```

## 22. Matrice de tests minimale

| Domaine | Structurel | Intégration | Comportemental | Négatif |
|---|---|---|---|---|
| Build | Schémas et golden | Build toutes cibles | — | Collision/orphelin |
| Install | Manifest/hash | Fresh/update/restore | Runtime découvre | Fichier utilisateur modifié |
| Probe | YAML valide | Fixtures multi-stack | Bonne commande choisie | Config drift/destructif |
| Gate | Schéma/hash | SHAs + diff réel | PASS/CONCERNS correct | Payload tampered/stale |
| Aliases | Catalog complet | Résolution provider | Bonne intention lancée | Alias absent/collision |
| Workflows | Frontmatter | Dépendances disponibles | Ordre D-EPCT respecté | Stop/gate refusé |
| Sécurité | Lint contrats | Sandbox fixtures | Aucun side effect caché | Mutation non autorisée |

Les tests runtime dépendants d'un binaire absent doivent être `not-run` avec raison, jamais
transformés automatiquement en succès.

## 23. Risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|---|---:|---:|---|
| Le compilateur devient un nouveau framework complexe | Moyenne | Fort | IR minimal, Markdown reste canonique, aucune abstraction sans deux usages. |
| Drift entre core et dist | Moyenne | Fort | `build --check`, golden tests, aucun edit manuel du dist. |
| Faux support multi-provider | Élevée | Fort | Certification C1-C3 et versions épinglées. |
| Perte d'une capacité Claude pendant neutralisation | Moyenne | Fort | Capability flags + vertical slice + behavioral parity. |
| Écrasement de config utilisateur | Moyenne | Critique | Manifest de propriété, hash, dry-run, backup et restore. |
| Migration trop large à reviewer | Élevée | Fort | Lots verticaux et séparation mouvement/changement fonctionnel. |
| Tests LLM instables | Moyenne | Moyen | Assertions d'invariants, fixtures locales, retries bornés et rapport brut. |
| Grok/Kimi changent rapidement | Élevée | Moyen | Version certifiée explicite, adaptateur isolé, pas de promesse globale. |
| Gate auto-certifié reste falsifiable | Faible après v2 | Critique | SHAs, payload hash, vérificateur mécanique et futur check externe. |

## 24. Politique de rollback

- Chaque release produit un bundle versionné et son manifeste de hashes.
- L'update sauvegarde uniquement les fichiers Skillz qu'elle possède.
- Le rollback ne touche pas les fichiers créés ou modifiés par l'utilisateur après installation.
- Tant que le vertical slice n'est pas certifié, les surfaces legacy restent disponibles.
- La bascule de la source canonique se fait skill par skill après équivalence prouvée.
- En cas de régression runtime, désactiver l'adaptateur concerné sans revenir sur le noyau neutre.

## 25. Definition of Done globale

Le chantier est terminé lorsque :

- [ ] RALPH et toutes ses surfaces sont absents de la distribution.
- [ ] Aucun hook ou fichier local user-owned n'a été supprimé lors du retrait de RALPH.
- [ ] Le noyau canonique n'est situé sous aucun dossier provider.
- [ ] Claude, Codex et OpenCode atteignent C3 sur les versions épinglées.
- [ ] Le contrat agents génériques atteint C2 et passe son behavioral smoke sur au moins un runner
      de référence déclaré, sans transformer ce runner en garantie universelle.
- [ ] Kimi via Codex est documenté et certifié via l'adaptateur Codex.
- [ ] Kimi CLI, Grok et Gemini ont un statut honnête C0-C3 avec raisons et versions.
- [ ] Tous les aliases sémantiques du catalog sont résolus ou explicitement non supportés.
- [ ] `build --check`, golden tests, installer tests et behavioral evals critiques passent.
- [ ] `project-probe` invalide correctement toute entrée pertinente modifiée.
- [ ] `gate verify` refuse un gate stale ou altéré.
- [ ] `doctor` diagnostique sans mutation chaque cible installée.
- [ ] Codex est installé et découvert via un plugin natif ; le mode headless charge réellement le
      bundle lors du scénario de certification.
- [ ] Aucun runner comportemental n'utilise un contournement global de permissions.
- [ ] Update/uninstall/restore préservent les fichiers utilisateur.
- [ ] Le README et la documentation ne présentent plus Claude comme source de vérité.
- [ ] Les plans/specs actifs ont un lifecycle valide et les documents remplacés pointent vers leur
      successeur.
- [ ] Chaque mécanisme repris d'un upstream possède SHA, fichiers source, licence, décision,
      destination locale et tests dans un registre versionné.
- [ ] Le build et l'installation passent sans réseau ni checkout upstream.
- [ ] Le quality gate final est `PASS`, ou toute limitation externe restante est explicitement
      documentée et acceptée.

## 26. Hors périmètre

- Construire un nouveau service d'orchestration asynchrone.
- Garantir une syntaxe littérale identique sur tous les runtimes.
- Réécrire tous les skills en code ou dans un DSL.
- Modifier la logique produit de chaque skill pendant sa migration structurelle.
- Installer automatiquement Kimi/Grok/Gemini sans décision utilisateur.
- Ajouter des providers uniquement pour afficher une longue liste de compatibilité.

## 27. Décisions acquises et defaults à consolider

### Décision humaine acquise le 1er septembre 2026

RALPH est supprimé sans mode de compatibilité v6.1. Seuls le changelog et le guide de migration
peuvent conserver une mention historique. Aucun launcher, hook, état, test actif ou documentation
d'usage RALPH ne subsiste dans la distribution.

### Defaults recommandés pour la spec

1. nom du noyau : `core/` ;
2. `dist/` committé pendant la migration pour rendre les diffs et golden visibles, décision à
   réévaluer après stabilisation du pipeline de release ;
3. cibles P0 : Claude Code, Codex, OpenCode et agents génériques ;
4. contrat d'alias : identifiant sémantique stable, syntaxe native documentée, fallback explicite ;
5. ordre : baseline → suppression RALPH → preuves `probe/gate` → contrats/build → vertical slice ;
6. historique RALPH limité à `CHANGELOG.md`, aux anciennes specs marquées `superseded` et au guide
   de migration.

Ces defaults ne valent pas encore spec approuvée. Ils deviennent le contenu initial de
`docs/planning/specs/2026-09-01-provider-neutral-kernel-design.md`, puis sont approuvés ou amendés
au checkpoint humain avant la première modification structurelle.

## 28. Provenance et traçabilité du recheck

| Sujet | Source primaire | Usage dans v6.1 |
|---|---|---|
| Baseline juillet | [`1c41e020`](https://github.com/ai-driven-dev/framework/commit/1c41e0203465f67b84105c57cb08f7e804bc63d5) | Comparaison d'origine. |
| Release auditée | [`v5.9.0`](https://github.com/ai-driven-dev/framework/releases/tag/v5.9.0), [`3082c8ff`](https://github.com/ai-driven-dev/framework/commit/3082c8ff7f862df814f15f6e669a2005b50d3459) | Point de recheck du 1er septembre. |
| Plugin Codex | [PR #571](https://github.com/ai-driven-dev/framework/pull/571) | Format plugin, marketplace et transforms Codex. |
| Chargement silencieux | [Issue #703](https://github.com/ai-driven-dev/framework/issues/703) | Test headless négatif obligatoire. |
| Hooks Codex | [Issues #698](https://github.com/ai-driven-dev/framework/issues/698) et [#699](https://github.com/ai-driven-dev/framework/issues/699) | Trust, `PLUGIN_ROOT` et fail-closed. |
| Cycle de vie documentaire | [Issue #730](https://github.com/ai-driven-dev/framework/issues/730) | `current`, `superseded`, `superseded_by`, `amended_by`. |
| Gemini | [Issue #511](https://github.com/ai-driven-dev/framework/issues/511) | Mapping candidat, à certifier. |
| Kimi | [Issue #733](https://github.com/ai-driven-dev/framework/issues/733) | Mapping candidat, à certifier. |
| Orchestrateur rejeté | [Issue #625](https://github.com/ai-driven-dev/framework/issues/625) | Exemple de spec incomplète pouvant atteindre l'implémentation. |
| Dépendance transitive | [Issue #463](https://github.com/ai-driven-dev/framework/issues/463) | Raison supplémentaire de ne pas importer le CLI complet. |

Les issues ouvertes sont des signaux de conception, pas des contrats stables. Toute capacité Kimi,
Gemini, OpenCode ou hook doit être revérifiée contre la documentation officielle et le binaire
épinglé au moment de son implémentation.

## 29. Journal de révision du document

| Date | Révision | Décision |
|---|---|---|
| 2026-07-24 | Draft initial | Noyau provider-neutral, migration progressive et certification C0-C3. |
| 2026-09-01 | Recheck v5.9.0 | Plugin Codex natif, build contracts, drift par fichier, evals multi-runtime, lifecycle documentaire et suppression RALPH confirmée. |

Après approbation de la spec consolidée, l'exécution commence par la **Vague 0**, puis la
suppression de RALPH et le durcissement des preuves. Aucun déplacement massif de skills ne commence
avant que le vertical slice et les tests de distribution soient verts.
