# Mémoire : Obsidian LLM Wiki

> Retour au [README](../README.md).

Une base de connaissances persistante et maillée, qui grandit d'une session à l'autre, inspirée du
[pattern LLM Wiki de Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
Les sources sont lues une fois, intégrées dans un vault Obsidian partagé et tenues à jour par
l'agent.

- Les projets activés partent de la tâche et cherchent via `memory context` dans leur collection
  projet déclarée. Sans QMD, la recherche reste bornée aux `entry_pages` du manifeste.
- Les vaults sans `.agents/memory.yaml` gardent le parcours historique par catalogue (route legacy,
  hors pilote).

> Construit sur [`alirezarezvani/claude-skills`](https://github.com/alirezarezvani/claude-skills)
> (MIT), voir [`ATTRIBUTION.md`](../skills/ATTRIBUTION.md).

---

## Installation en une commande

```bash
bash install.sh install all --with-wiki
```

Lance l'installation standard **et** le bootstrap du wiki. `--no-wiki` saute le bootstrap. Tu peux le
relancer quand tu veux avec `bash scripts/setup-wiki.sh` (idempotent).

### Prérequis

| Outil | Requis | Installation | Rôle |
|---|---|---|---|
| **Obsidian** | Oui | [obsidian.md/download](https://obsidian.md/download) (gratuit) | Éditeur du vault |
| **Python 3.10+** | Oui | déjà requis par Skillz-Claude | project-probe, CLI mémoire, scripts du wiki (bibliothèque standard seulement) |
| **`qmd`** | Recommandé | `npm install -g @tobilu/qmd` (Node 22+) ou `bun install -g @tobilu/qmd`, voir [tobi/qmd](https://github.com/tobi/qmd) | Recherche locale dans le vault quand l'index ne suffit pas. Le script avertit sans bloquer s'il manque. |

### Ce que fait le bootstrap

1. **Détecte un vault existant** via la ligne `Vault memoire :` de `~/.claude/CLAUDE.md`, et le
   réutilise.
2. **Crée le vault** (par défaut `~/Documents/Obsidian-<git-user>/Wiki`) avec trois couches :
   `raw/`, `wiki/{entities,concepts,sources,comparisons,synthesis}`, `index.md` et `log.md`.
3. **Complète `~/.claude/CLAUDE.md`** avec un bloc idempotent
   `<!-- BEGIN:llm-wiki-config --> … <!-- END:llm-wiki-config -->`, pour que chaque session sache où
   est le vault.
4. **Vérifie** que `qmd` est dans le `PATH` (avertissement sinon).
5. **Crée ou rafraîchit la collection QMD** de `wiki/` (`--with-qmd` pour forcer), puis lance
   `qmd update` et `qmd embed`.
6. **Teste le vault** avec `lint_wiki.py` : orphelins, liens cassés, frontmatter, trous dans le log.

### Ouvrir le vault dans Obsidian

Lance Obsidian, clique **Open folder as vault** et choisis le chemin affiché par le script. La
plupart du temps, tu n'édites pas le vault à la main : tu passes par les commandes ci-dessous.

### Options avancées

```bash
bash scripts/setup-wiki.sh                       # interactif
bash scripts/setup-wiki.sh --vault ~/path        # chemin de vault explicite
bash scripts/setup-wiki.sh --verify              # vérification seule, aucune écriture
bash scripts/setup-wiki.sh --with-qmd            # met à jour la collection et les embeddings qmd
bash scripts/setup-wiki.sh --qmd-collection name # nom de collection qmd explicite
bash scripts/setup-wiki.sh --no-qmd              # ignore qmd
bash scripts/setup-wiki.sh --non-interactive     # mode CI, échoue si la config manque
```

---

## Commandes

```
/wiki-bootstrap               Relancer ou réparer l'installation (interactif)
/wiki-init <path> --topic …   Créer un vault vide (sans toucher à CLAUDE.md)
/wiki-ingest <file>           Intégrer une source de raw/ et mettre à jour les liens croisés
/wiki-query "<question>"      Interroger le wiki : l'agent lit 3 à 10 pages et répond avec des [[wikilinks]]
/wiki-lint                    Contrôle de santé : orphelins, liens cassés, pages périmées, trous dans le log
/wiki-log                     Dernières entrées du log (décisions, ingestions)
/wiki-capture-session [topic] Capturer les notes durables de la session dans raw/, avant /wiki-ingest
```

**Codex :** il ne lit pas les commandes slash de Claude. `install/update codex` génère donc des skills
propres à Codex, comme `source-command-wiki-capture-session` dans `~/.codex/skills/`. Après un
redémarrage de Codex, `/wiki-capture-session` ou « capture cette session dans le wiki » chargent le
bon workflow. OpenCode garde son dossier de commandes natif.

---

## QMD dans tous les agents

`install/update all` vérifie que le serveur MCP QMD local est déclaré dans les trois clients :

| Client | Fichier de config | Entrée QMD |
|---|---|---|
| Claude Code | `.mcp.json` du projet et `.claude/mcp.json` de Skillz | `"qmd": { "command": "qmd", "args": ["mcp"] }` |
| Codex | `~/.codex/config.toml` | `[mcp_servers.qmd]` avec `command = "qmd"` et `args = ["mcp"]` |
| OpenCode | `~/.config/opencode/opencode.json` | `"qmd": { "type": "local", "command": ["qmd", "mcp"], "enabled": true }` |

QMD n'est ajouté que s'il manque ; les autres serveurs MCP restent en place.

---

## Pointeurs de mémoire par projet

Les dépôts ne doivent pas committer de chemins propres à une machine. Les métadonnées partagées
vivent dans `.agents/memory.yaml` ; chaque collaborateur relie ce manifeste à sa machine :

```bash
cd /path/to/project-repo
memory configure --store "project=$OBSIDIAN_MEMORY_ROOT/Pleepole"
memory doctor
```

- La commande écrit `.agents/memory.local.json`, `.claude/project-memory.md` et
  `.agents/project-memory.md` (permissions utilisateur seulement quand c'est possible) et les ajoute
  au `info/exclude` local de Git.
- Des pages d'entrée manquantes donnent un résultat `degraded` utilisable (code de sortie `10`). Un
  contenu de pointeur non géré est préservé, sauf avec `--replace-managed`.
- `memory doctor` renvoie `ready`, `degraded` ou `blocked`, une action à copier et la question de
  départ du manifeste. Sans QMD, les modes `minimal` et `project` restent utilisables.
- Un profil optionnel `sources` peut exposer des ADR, docs produit, OpenAPI, schémas JSON et contrats
  SQL du dépôt via une collection QMD distincte. Il est désactivé par défaut, ne copie rien dans
  Obsidian et ne contourne jamais la liste d'exclusion (secrets, logs, build, code).
- `--explain` détaille chaque contrôle, `--json` donne l'enveloppe stable pour l'automatisation.
  L'accès réseau n'a lieu qu'avec `--network`, la réparation des fichiers gérés qu'avec `--fix`.
- Les chemins absolus restent masqués sauf avec `--explain-local-paths`. Le rôle local vaut
  `collaborator` par défaut (`--role owner` pour le changer) et n'accorde aucun accès.

L'ancien script `scripts/create-project-memory-pointer.sh` reste disponible comme surcouche de
compatibilité ; ses options de métadonnées sont dépréciées au profit du manifeste :

```bash
scripts/create-project-memory-pointer.sh \
  --project-dir /path/to/project-repo \
  --vault-path "$OBSIDIAN_MEMORY_ROOT/Pleepole"
```

---

## Recherche avec la CLI `memory`

```bash
memory context --mode project --task-category architecture "How is this project structured?"
memory context --mode project --task-category security --risk-reason security "Which security decision applies?"
printf '%s' "private task" | memory context --task-category security --query-stdin --json
memory test --json
memory test --holdout --json
memory test record-quality --input /path/to/quality.json --json
memory test gate --run-id run_... --json
memory report --weekly --json
memory report --weekly --export-markdown ./memory-weekly.md
```

- **`memory context`** utilise uniquement la recherche lexicale `qmd search`, ne conserve jamais la
  requête et n'émet que des métadonnées normalisées, sans extraits bruts. Un gate déterministe
  s'arrête dès que les preuves du projet suffisent, et n'appelle un repli transverse que si le rôle
  local et le manifeste l'autorisent tous les deux. Les cas ambigus demandent
  `--fallback-on-ambiguous` ; `--explain` montre les codes de raison. Vide, timeout, sortie
  invalide, périmé, ambigu et QMD absent restent des résultats distincts.
- Quand la recherche suffit, la CLI n'émet que les sections Markdown nécessaires dans le budget du
  mode choisi (estimation `utf8_bytes_div_4_v1`). Dépasser le plafond demande un `--risk-reason`
  explicite.
- **`memory test`** valide huit cas golden V1 visibles, puis compare la route projet bornée à un
  rejeu `index-first`. `--holdout` ajoute deux cas locaux ignorés par Git et n'en partage que
  l'agrégat. La qualité des réponses est notée à part (rubrique pondérée importée en métadonnées) ;
  le gate reste `incomplete` sans note et échoue au-delà de 5 % de dégradation.
- **`memory report --weekly`** agrège les événements, runs et notes du projet. Il limite la revue à
  sept dettes ouvertes, classées par risque puis par impact, et vérifie le Markdown final avant
  l'export.

---

## Ce qui n'entre jamais dans le wiki

Secrets, tokens, identifiants, logs complets, transcripts bruts, stack traces. Le wiki garde le
savoir durable : décisions, conventions, sources, synthèses. Le code reste la source de vérité
immédiate.
