# Installation

> Retour au [README](../README.md). Statut : release candidate `6.1.0-rc.1`, non stable.

Il existe deux routes d'installation :

| Route | Pour qui | Statut |
|---|---|---|
| **`install.sh`** (universel) | Usage quotidien, tous les agents | Route publiée (distribution de compatibilité v6), recommandée tant que la RC n'est pas certifiée |
| **`bin/skillz`** (bundles compilés) | Installer les bundles générés v6.1, runtime par runtime | Route cible v6.1, en release candidate |

La compatibilité exacte par runtime est dans la [matrice v6.1](./compatibility/matrix-v6.1.md).
Pour passer de v6 à v6.1, voir le [guide de migration](./migrations/v6-to-v6.1.md).

---

## Route recommandée : `install.sh`

### Global (tous tes projets)

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install all
```

Installe la distribution de compatibilité v6 dans `~/.claude/`, `~/.codex/`, `~/.gemini/`, `~/.config/opencode/` et
`~/.agents/`. Les dossiers des autres agents pointent vers les skills de `~/.claude/skills`.

### Par projet

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install .
```

Crée `.claude/`, `.codex/`, `.gemini/`, `.opencode/`, `.agents/` et `docs/` dans le dépôt courant.

### Mise à jour

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- update all
```

Depuis un clone local : `bash install.sh update all`.

- Ta configuration de chaque agent est conservée.
- Les prompts gérés par Skillz se mettent à jour (signature de loader) ; les prompts tiers (BMad…)
  ne sont jamais touchés.
- Le manifeste `~/.claude/.skillz-manifest` protège contre la dérive : les skills et commandes
  retirés de la source sont purgés, ceux que tu as ajoutés sont conservés.
- Les liens morts vers des skills Skillz sont retirés de `~/.codex`, `~/.gemini`,
  `~/.config/opencode` et `~/.agents`. Un lien mort qui pointe ailleurs n'est pas touché.
- Les fichiers de knowledge retirés ne sont supprimés que s'ils sont restés identiques à la version
  livrée.

En installation par projet, `.claude/.skillz-manifest` joue le même rôle : chaque installation
l'écrit, chaque mise à jour purge ce qui n'est plus livré. Un projet installé avant ce manifeste
est nettoyé une fois, en ne supprimant que les fichiers identiques à la version livrée ; une copie
modifiée est conservée et signalée.

<details>
<summary><strong>Installer ou mettre à jour un seul agent</strong></summary>

```bash
# Global
./install.sh install claude
./install.sh install codex      # après Claude
./install.sh install gemini     # après Claude
./install.sh install opencode   # après Claude
./install.sh install agents     # après Claude

# Par projet : choisis les agents
./install.sh install . --providers claude
./install.sh install . --providers codex,gemini
./install.sh install . --providers opencode

# Mise à jour
./install.sh update all
./install.sh update codex
./install.sh update . --providers all

# Désinstallation (garde le contenu que tu as ajouté)
./install.sh uninstall all
./install.sh uninstall claude

# Aide
./install.sh help
```

| Agent | Installé dans | Contenu |
|---|---|---|
| Claude Code | `~/.claude/` | Tous les skills, toutes les commandes, knowledge, templates |
| OpenAI Codex CLI | `~/.codex/` | Liens vers les skills, prompts Codex natifs, skills `source-command-*` générés pour le wiki, `AGENTS.md` généré |
| Google Gemini CLI | `~/.gemini/` | Liens vers les skills, commandes Gemini natives, `GEMINI.md` généré |
| OpenCode | `~/.config/opencode/` | Liens vers les skills, commandes OpenCode natives, `AGENTS.md` généré |
| Agents génériques | `~/.agents/` | Liens vers les skills et `AGENTS.md` généré |

</details>

### CLI mémoire portable

L'installation globale de Claude installe aussi la commande mémoire :

```bash
skillz-memory --version
memory --version
```

- `skillz-memory` est le nom sans collision, toujours géré dans `~/.local/bin/skillz-memory`.
- `memory` est un alias créé seulement si ce nom est libre ou pointe déjà vers Skillz-Claude. Une
  commande `memory` tierce est préservée ; utilise alors `skillz-memory`.
- La CLI demande Python 3.10+ et n'utilise que la bibliothèque standard. L'installateur ne crée pas
  d'environnement virtuel et ne télécharge ni QMD ni modèle.
- Si `~/.local/bin` n'est pas dans ton `PATH` : `export PATH="$HOME/.local/bin:$PATH"`.
- Les mises à jour ne remplacent que les liens gérés par Skillz. `uninstall claude` et
  `uninstall all` ne retirent un lien que s'il pointe encore vers le runtime Skillz-Claude.

L'usage de la CLI (`memory context`, `memory doctor`, `memory test`, `memory report`) est décrit dans
[MEMORY.md](./MEMORY.md).

---

## Route release candidate : `bin/skillz`

Cette route n'installe que les fichiers générés dans `dist/<runtime>`. Elle enregistre un manifeste
local avec les hashes source et installés, refuse les collisions modifiées ou non possédées, garde
des snapshots de rollback et produit des diagnostics JSON. Inspecte toujours le dry-run avant de
viser un dossier existant.

```bash
# Construire et inspecter sans écrire la cible
bash tests/run-python310.sh tooling/build/compiler.py build --root . --output dist
bin/skillz --json install --dist-root dist --runtime codex --target /explicit/target --dry-run

# Installer, diagnostiquer, mettre à jour, revenir en arrière
bin/skillz install --dist-root dist --runtime codex --target /explicit/target
bin/skillz --json doctor --dist-root dist --runtime codex --target /explicit/target
bin/skillz update --dist-root dist --runtime codex --target /explicit/target --dry-run
bin/skillz restore --target /explicit/target --dry-run
bin/skillz uninstall --target /explicit/target --dry-run
```

Elle n'adopte jamais un fichier existant en silence et ne touche à rien en dehors des chemins
enregistrés comme `ownership: skillz`. Le contrat est dans
[managed-installation.md](./architecture/managed-installation.md).

### Packages natifs (Claude, Codex, Gemini)

À utiliser seulement si tu veux un package natif plutôt que l'installateur universel.

| Agent | Commande | Portée |
|---|---|---|
| Claude Code | `claude --plugin-dir /path/to/repo/dist/claude` | Plugin généré depuis `dist/claude/.claude-plugin/plugin.json` |
| Codex CLI | `codex plugin marketplace add /path/to/repo/dist/codex && codex plugin add skillz-claude@skillz-claude-dev` | Plugin de développement v6.1 ; `install codex` reste la route de repli |
| Gemini CLI | `gemini extensions link /path/to/repo/dist/gemini` | Extension générée, niveau C1 seulement (Gemini non installé localement) |
| OpenCode | `bin/skillz install --dist-root dist --runtime opencode --target /explicit/target` | Route générée à plat, pas de package natif |

```bash
gh repo clone elsolal/Skillz-Claude-Codex-And-More
cd Skillz-Claude-Codex-And-More
bash tests/run-python310.sh tooling/build/compiler.py build --root . --output dist

claude --plugin-dir "$PWD/dist/claude"
codex plugin marketplace add "$PWD/dist/codex"
codex plugin add skillz-claude@skillz-claude-dev
gemini extensions link "$PWD/dist/gemini"
```

Recharge avec `/reload-plugins` (Claude Code) ou redémarre l'agent après un changement de manifeste.

---

## Compléments

### Playwright CLI (navigation par les agents)

`@playwright/cli` permet aux agents d'ouvrir un site, parcourir des flows, remplir des formulaires,
lire la console et le réseau, changer de viewport et faire des captures. Skillz-Claude passe par
`web-navigator`, puis `/qa`, `seo-geo-audit` et `design-audit` réutilisent les mêmes preuves.

```bash
npm install -g @playwright/cli@latest
playwright-cli install --skills          # skills compagnons pour Claude
playwright-cli install --skills=agents   # variante agents génériques
```

### Installation manuelle sous Windows

```powershell
git clone https://github.com/elsolal/Skillz-Claude-Codex-And-More.git Skillz-Claude
Copy-Item -Recurse -Force Skillz-Claude\.claude\ .\.claude\
Copy-Item -Recurse -Force Skillz-Claude\.agents\ .\.agents\
Copy-Item -Recurse -Force Skillz-Claude\.codex\ .\.codex\
Copy-Item -Recurse -Force Skillz-Claude\.gemini\ .\.gemini\
Copy-Item -Recurse -Force Skillz-Claude\.opencode\ .\.opencode\
New-Item -ItemType Directory -Force -Path docs\planning\brainstorms, docs\planning\ux, docs\planning\prd, docs\planning\ui, docs\planning\architecture, docs\stories, docs\quality, docs\security
Remove-Item -Recurse -Force Skillz-Claude
```

### Diagnostic

Lance `/skillz-doctor` en cas de doute, puis consulte [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).
