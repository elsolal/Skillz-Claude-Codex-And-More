---
title: "Observable second-brain efficiency — Design"
status: approved
approved_by: human
approved_at: 2026-07-16
created_at: 2026-07-16
slug: second-brain-efficiency
level: 4
owner: Aymeric
implementation_readiness: 15/15
pilots: [Skillz-Claude, Pleepole-back]
---

# Observable second-brain efficiency — Design consolidé

## 1. Mandat

Faire évoluer le système Obsidian + `llm-wiki` + QMD d'une mémoire disponible
mais non mesurée vers une mémoire projet portable, bornée et observable.

Le produit doit permettre à un humain ou un agent de :

1. reconstruire la liaison entre un repo et son mini-cerveau ;
2. partir de la tâche au lieu de précharger un index général ;
3. récupérer d'abord la mémoire du projet et élargir seulement si nécessaire ;
4. voir ce qui a été trouvé, lu, utilisé et cité ;
5. mesurer conjointement contexte, qualité, usage et maintenance ;
6. décider sur preuves si le système mérite un rollout plus large.

Le but n'est pas de minimiser les tokens à tout prix. Le but est d'améliorer
l'efficacité de la mémoire sans dégrader la justesse ni la confidentialité.

## 2. Sources validées

Cette spec consolide les documents approuvés suivants :

- `docs/planning/forge/FORGE-second-brain-token-efficiency-2026-07-16.md` ;
- `docs/planning/brainstorms/BRAINSTORM-second-brain-efficiency-2026-07-16.md` ;
- `docs/planning/ux/UX-second-brain-efficiency.md` ;
- `docs/planning/prd/PRD-second-brain-efficiency.md` ;
- `docs/planning/architecture/ARCH-second-brain-efficiency.md` ;
- `docs/stories/second-brain-efficiency-backlog.md` ;
- `docs/stories/IMPLEMENTATION-READINESS-second-brain-efficiency.md`.

En cas d'ambiguïté, l'ordre d'autorité est : cette spec approuvée, architecture,
PRD, UX, brainstorm, forge. Les stories précisent les lots d'implémentation sans
modifier le contrat produit.

## 3. Résultat attendu

### 3.1 Succès pilote

| Dimension | Cible |
|---|---|
| Activation | 100 % des deux pilotes avec manifeste et pages d'entrée valides. |
| Retrieval | >= 90 % des pages/sources attendues sur la première route bornée. |
| Qualité | Dégradation maximale de 5 % par rapport à la baseline. |
| Contexte | Réduction médiane >= 50 % par rapport à `index-first`. |
| Fallback index complet | < 10 % des récupérations. |
| Usage réel | 20 récupérations valides par pilote. |
| Fraîcheur | QMD mis à jour <= 24 h après merge mémoire. |
| Maintenance | Revue hebdomadaire <= 10 minutes. |
| Confidentialité | Zéro prompt, réponse, secret ou événement brut cross-vault. |

Le rollout global passe uniquement si toutes les dimensions obligatoires
passent ensemble. Un sous-module peut être conservé malgré un échec global.

### 3.2 Utilisateurs

- **Aymeric** : owner transverse, opérateur multi-projets et arbitre final.
- **Collaborateur projet** : utilisateur autorisé du repo et du mini-cerveau
  équipe, sans accès transverse implicite.

Les agents, QMD et Git sont des acteurs automatisés. Ils ne possèdent pas le
sens métier et ne valident jamais seuls une réécriture de mémoire partagée.

## 4. Scope V1

### Inclus

- manifeste `.agents/memory.yaml` portable et versionné ;
- projection locale ignorée et pointeurs multi-agent générés ;
- CLI unifié `memory` / `skillz-memory` ;
- modes `minimal`, `project`, `historical` ;
- route QMD projet-first et fallback transverse autorisé ;
- sufficiency gate déterministe et explicable ;
- budgets, hard caps et risk override ;
- reçus humain/JSON ;
- événements locaux metadata-only et rétention 30 jours ;
- `memory doctor`, `context`, `finish`, `test`, `report`, `purge` ;
- conflits mémoire ↔ repo et dette reviewable ;
- golden questions, holdouts et gate composite ;
- profil P1 de docs/contrats sélectionnés ;
- pilotes Skillz-Claude et Pleepole-back.

### Hors scope

- index complet du code dans Obsidian ou QMD ;
- Graphify comme dépendance obligatoire ;
- service hébergé, dashboard web ou base distante ;
- capture automatique de toutes les sessions ;
- mesure exacte de facturation pour tous les providers ;
- modification automatique du sens d'une page mémoire partagée ;
- rollout automatique aux autres repos.

## 5. Architecture cible

```text
Repo + Git            vérité immédiate du code et des contrats
        |
        v
.agents/memory.yaml   contrat portable partagé
        |
        v
memory CLI            policy plane Python stdlib
  |     |     |
  |     |     +------> receipts humain / JSON
  |     +------------> JSONL local metadata-only
  +------------------> QMD search, collection projet d'abord
                             |
                             +--> fallback autorisé si insuffisant

Obsidian + wiki       connaissance durable et gouvernée
QMD                   moteur local de retrieval, jamais source de vérité
Agent / humain        attestation et arbitrage du sens
```

### 5.1 Source de vérité code

Le code canonique vit sous :

```text
.claude/skills/llm-wiki/
├── bin/memory
├── memory_cli/
├── scripts/memory.py
├── tests/
└── expected_outputs/memory/
```

Le package utilise Python 3.10+ et la bibliothèque standard. QMD est appelé par
`subprocess.run` avec une liste d'arguments, `shell=False`, timeout et limites
de sortie.

### 5.2 Modules obligatoires

- `contracts` : dataclasses, enums et versions publiques ;
- `manifest` : découverte et validation ;
- `projection` : chemins locaux, pointeurs et Git exclude ;
- `routing` / `sufficiency` : politiques et décisions pures ;
- `qmd_adapter` : intégration QMD versionnée ;
- `context` / `tokens` : assemblage et budgets ;
- `events` : append-only, rétention et scanner privacy ;
- `receipts` / renderers : sorties humain/JSON ;
- `doctor`, `golden`, `report` : exploitation et preuve.

La logique métier ne dépend ni d'`argparse`, ni des couleurs, ni du format QMD
brut, ni d'un provider LLM.

## 6. Contrats partagés et locaux

### 6.1 Manifeste portable

Le fichier `.agents/memory.yaml` est du YAML 1.2 dans son sous-ensemble JSON.
Cette syntaxe est obligatoire en V1 pour rester stdlib, sûre et identique entre
runtimes.

```json
{
  "schema_version": 1,
  "project": {
    "id": "pleepole-back",
    "name": "Pleepole-back",
    "owner": "Pleepole"
  },
  "stores": {
    "project": {
      "remote": "https://github.com/Pleepole/pleepole-memory.git",
      "collection": "pleepole-wiki",
      "entry_pages": [
        "wiki/entities/pleepole-back.md",
        "wiki/synthesis/pleepole-operating-documentation-2026-06-17.md"
      ]
    }
  },
  "fallbacks": [
    {
      "id": "transverse",
      "collection": "elsolal-wiki",
      "allowed_roles": ["owner"],
      "task_categories": ["architecture", "operations", "historical"]
    }
  ],
  "budgets": {
    "minimal": {"target_tokens": 800, "hard_tokens": 1200},
    "project": {"target_tokens": 2500, "hard_tokens": 4000},
    "historical": {"target_tokens": 6000, "hard_tokens": 9000}
  },
  "policy": {
    "semantic_retrieval": "explicit",
    "full_index_fallback": true,
    "retention_days": 30
  }
}
```

Le manifeste refuse chemins absolus, commandes, interpolations shell, IDs
invalides et versions inconnues.

### 6.2 Projection locale

`.agents/memory.local.json` associe les stores logiques à des racines absolues
sur la machine. Il est local, ignoré par Git et créé avec permissions restrictives.

`memory configure` génère également :

- `.claude/project-memory.md` ;
- `.agents/project-memory.md` ;
- les entrées `.git/info/exclude`.

Un rôle déclaré localement ne donne aucun accès supplémentaire : les permissions
filesystem/Git restent la frontière réelle et la policy partagée reste requise.

## 7. Contrat CLI

| Commande | Résultat |
|---|---|
| `memory configure` | Projection locale et pointeurs idempotents. |
| `memory doctor` | Statut ready/degraded/blocked et prochaine action. |
| `memory context` | Contexte borné, receipt et event ID. |
| `memory finish` | Attestation et conflit liés à l'événement parent. |
| `memory test` | Golden, holdout, baseline et gate disponible. |
| `memory report --weekly` | Agrégats et sept arbitrages maximum. |
| `memory purge` | Rétention ou purge immédiate du détail local. |

`skillz-memory` est toujours installé. `memory` est créé seulement si le nom est
libre ou déjà géré par Skillz-Claude. Aucun binaire tiers n'est écrasé.

### 7.1 Exit codes

```text
0   success
2   invalid CLI usage
10  degraded but usable
20  insufficient context
21  human arbitration required
30  invalid manifest or projection
31  missing required dependency
32  denied route or access
33  blocking freshness
40  retrieval failure or timeout
50  telemetry or contract integrity failure
```

Les sorties JSON possèdent toujours `schema_version`, `command`, `status`,
`project_id`, `event_id`, `data`, `warnings` et `errors`. stdout contient la
donnée ; stderr contient progression et diagnostic.

## 8. Retrieval et budgets

### 8.1 Ordre nominal

1. Découvrir et valider manifeste + projection.
2. Recevoir requête, mode et catégorie de tâche.
3. Interroger `stores.project.collection` avec `qmd search --json`.
4. Normaliser, dédupliquer et évaluer les hits.
5. S'arrêter si le contexte est suffisant.
6. Sinon, interroger uniquement un fallback autorisé.
7. Sélectionner les sections utiles sous budget.
8. Émettre contexte, receipt et événement metadata-only.

`wiki/index.md` complet est un fallback observable, jamais une étape obligatoire.

### 8.2 Pourquoi BM25 par défaut

Avec QMD 0.9.0, `vsearch` et `query` développent la requête avec un modèle local
et utilisent `llm_cache`. La V1 conforme utilise donc `qmd search` BM25, qui ne
persiste pas la requête.

Le sémantique profond peut être expérimenté uniquement avec
`semantic_retrieval: explicit`, avertissement de persistance locale et mesure
séparée. Il n'entre pas dans le chemin nominal du pilote.

### 8.3 Sufficiency gate

| Mode | Score candidat | Suffisance initiale | Contexte sans QMD |
|---|---:|---|---|
| `minimal` | >= 0,70 | 1 hit >= 0,75 | 1 page d'entrée |
| `project` | >= 0,55 | 1 hit >= 0,75 ou 2 >= 0,55 | 3 pages maximum |
| `historical` | >= 0,45 | 2 hits dont 1 source/synthesis | Bloqué |

Le gate utilise score, nombre, fraîcheur, provenance, catégorie et policy. Il
retourne `sufficient`, `insufficient`, `ambiguous` ou `blocked` avec reason codes.
Un cas ambigu est rendu à l'agent ; aucun LLM caché ne décide dans le CLI.

### 8.4 Assemblage

- résoudre chaque URI dans une racine autorisée ;
- refuser traversal et symlink escape ;
- sélectionner la section Markdown autour du hit ;
- compter seulement les sections émises comme `read` ;
- s'arrêter au budget cible ;
- exiger `risk_reason` pour dépasser le hard cap ;
- estimer avec `ceil(utf8_bytes / 4)`, version
  `utf8_bytes_div_4_v1`.

Les valeurs 800 / 2 500 / 6 000 sont initiales et calibrées par les golden
tests. Elles ne sont jamais auto-modifiées à partir des sessions réelles.

## 9. Preuves, événements et conflits

### 9.1 Machine d'états

```text
retrieved  résultat renvoyé par le moteur
read       section effectivement émise par le CLI
used       page déclarée comme ayant influencé le travail
cited      page citée dans la sortie ou la preuve finale
```

`retrieved/read`, scores, durée, fraîcheur et tokens sont mesurés par le CLI.
`used/cited/impact` sont attestés et libellés comme tels. Un docid attesté doit
appartenir au résultat parent.

### 9.2 Event store

Les événements vivent sous `$XDG_STATE_HOME/skillz-memory` ou
`~/.local/state/skillz-memory`, par projet et par mois. Ils sont append-only,
créés en permissions utilisateur et purgés après 30 jours.

Ils peuvent contenir : projet, mode, catégorie, route, docids, chemins relatifs,
scores, fraîcheur, tokens estimés, durée, reason codes et impact codes.

Ils ne peuvent jamais contenir : requête, prompt, réponse, transcript, snippet,
corps de page, secret, chemin absolu ou événement brut d'un autre projet.

### 9.3 Conflit mémoire ↔ repo

- le repo et ses contrats exécutables prennent priorité opérationnelle ;
- un conflit faible peut devenir dette sans bloquer ;
- un conflit élevé sur produit, architecture, sécurité ou données retourne 21 ;
- le CLI peut préparer un brouillon local ;
- aucune page partagée n'est modifiée sans arbitrage humain.

## 10. Ce qui mérite d'être indexé

### Mémoire durable

- décisions produit et architecture ;
- concepts et vocabulaire métier ;
- synthèses et sources ;
- runbooks et conventions stables ;
- historique utile et contradictions documentées.

### Docs/contrats courants, collection séparée P1

- ADR, PRD et documentation repo ;
- OpenAPI et schémas de données ;
- SQL contractuel et runbooks d'exploitation ;
- fichiers explicitement allowlistés.

### Non indexé en V1

- code applicatif complet ;
- `.env`, secrets, credentials et logs ;
- artefacts de build et dépendances ;
- sorties Graphify ;
- transcripts de sessions.

Le codebase reste la source de vérité immédiate. Un futur index structurel est
jetable, séparé et évalué sur des questions d'architecture précises.

## 11. Plan d'implémentation

### EPIC-001 — Activation portable

1. STORY-001 — installer le CLI sans collision ;
2. STORY-002 — valider le manifeste v1 ;
3. STORY-003 — générer projection et pointeurs ;
4. STORY-004 — diagnostiquer avec `memory doctor`.

### EPIC-002 — Retrieval borné

5. STORY-005 — QMD task-first ;
6. STORY-006 — sufficiency et fallback ;
7. STORY-007 — contexte sous budget ;
8. STORY-008 — dégradation sans QMD ;
9. STORY-009 — alignement `llm-wiki`.

### EPIC-003 — Preuves d'usage

10. STORY-010 — reçus scriptables ;
11. STORY-011 — événements metadata-only ;
12. STORY-012 — attestations ;
13. STORY-013 — conflits et dette.

### EPIC-004 — Mesure et maintenance

14. STORY-014 — golden et baseline ;
15. STORY-015 — holdout et qualité ;
16. STORY-016 — rapport hebdomadaire ;
17. STORY-017 — profil docs/contrats P1.

### EPIC-005 — Pilotes et verdict

18. STORY-018 — pilote Skillz-Claude ;
19. STORY-019 — pilote Pleepole-back ;
20. STORY-020 — 20 usages réels par pilote ;
21. STORY-021 — verdict de rollout.

STORY-017 est P1 et peut avancer après le cœur retrieval sans bloquer les pilotes
P0. Toute implémentation commence par STORY-001 sur une branche dédiée ; aucun
commit direct sur `main`.

## 12. Stratégie de tests

Commande de base :

```bash
python3 -m unittest discover -s .claude/skills/llm-wiki/tests -p 'test_*.py'
```

### Obligatoire avant pilote

- parsing et contrats manifest/projection/event/result ;
- route projet-first et fallback interdit ;
- budgets et hard caps ;
- QMD empty/timeout/invalid JSON ;
- traversal, symlink escape et shell metacharacters ;
- absence de requête/secret/chemin absolu dans les événements ;
- concurrence JSONL et dernière ligne corrompue ;
- TTY, NO_COLOR, stdout/stderr et exit codes ;
- installation, collision et uninstall ;
- mode historical bloqué sans QMD.

### Preuve pilote

- huit golden visibles + deux holdouts locaux par projet ;
- baseline appariée avec le même estimateur ;
- qualité importée depuis une rubrique versionnée ;
- 20 usages réels par pilote ;
- audit privacy sur l'ensemble des événements ;
- revue hebdomadaire chronométrée.

## 13. Sécurité et garde-fous

1. Aucun chemin absolu obligatoire dans le manifeste partagé.
2. Toute résolution de fichier reste dans une racine autorisée après `resolve()`.
3. Toute commande externe utilise un tableau d'arguments et `shell=False`.
4. La denylist secrets/logs/build ne peut pas être assouplie par le manifeste.
5. Le fallback transverse requiert policy partagée et rôle local.
6. Le state dir est hors repo, permissions restrictives et purgeable.
7. Toute exportation Markdown passe le scanner metadata-only.
8. Aucun modèle lourd ou réseau n'est déclenché implicitement.
9. Le repo courant prévaut sur la mémoire historique.
10. Toute réparation sémantique partagée exige une validation humaine.

## 14. Risques acceptés

| Risque | Décision |
|---|---|
| BM25 manque certains synonymes | Mesurer avant d'activer le sémantique persistant. |
| JSON-compatible YAML moins agréable | Accepter en V1 pour sécurité et portabilité stdlib. |
| Seuils dépendants du corpus | Configurer et calibrer avec golden/holdout. |
| Usage auto-attesté par l'agent | Le séparer des mesures CLI et auditer des tâches réelles. |
| Parsing `qmd status` version-dépendant | Adapter isolé et support QMD `>=0.9,<1.0`. |
| JSONL concurrent | Verrou portable ; SQLite seulement si preuve d'échec. |
| Pilote Pleepole cross-repo | PR et revue séparées par le domain owner. |

## 15. Gates de livraison

### Gate de chaque story

- critères Given/When/Then verts ;
- lint/tests pertinents verts ;
- aucun contrat public modifié sans fixture ;
- documentation mise à jour ;
- quality-gate produit avant ship selon D-EPCT+R.

### Gate avant GitHub publication

- readiness 15/15 obtenu ;
- backlog validé humainement ;
- spec consolidée `status: approved` avec `approved_by: human` ;
- confirmation distincte de publication.

### Gate avant développement

Cette spec doit être approuvée humainement dans son frontmatter. Tant que
`status: draft`, aucun `/auto-dev` niveau 4 ne doit démarrer.

### Gate avant rollout global

- activation des deux pilotes ;
- qualité dans la tolérance ;
- réduction médiane >= 50 % ;
- 40 usages réels ;
- maintenance <= 10 minutes ;
- zéro incident privacy ;
- verdict humain documenté.

## 16. Definition of Done du chantier

Le chantier V1 est terminé lorsque :

1. les 21 stories P0/P1 retenues sont livrées ou explicitement déférées ;
2. les deux pilotes possèdent manifestes, golden sets et preuves réelles ;
3. les rapports permettent de recalculer le gate sans données conversationnelles ;
4. le workflow `llm-wiki` installé est task-first pour les projets activés ;
5. un verdict modulaire approuvé décide de la suite ;
6. aucun rollout global n'a contourné ce verdict.

## 17. Checkpoint d'approbation

Cette spec consolide les choix déjà validés. L'approbation humaine doit modifier
le frontmatter ainsi :

```yaml
status: approved
approved_by: human
approved_at: 2026-07-16
```

Après cette approbation, les issues GitHub peuvent être publiées puis STORY-001
peut entrer dans `/dev` sur une branche dédiée.
