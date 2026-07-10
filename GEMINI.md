# Skillz-Claude — Gemini CLI context

D-EPCT+R v6 workflow (Probe → Explore → Plan → Red → Implement → Gate → Handoff), adaptatif niveaux 0-4, avec des dizaines de skills, adapté pour Gemini CLI.

## Source de vérité

`.claude/CLAUDE.md` dans ce repo contient le workflow complet. Ce fichier `GEMINI.md` sert de context file d'entrée quand Gemini est lancé depuis la racine du repo.

## Layout

- `skills/` → symlink vers `.claude/skills/` (des dizaines de skills)
- `commands/` → symlink vers `.claude/commands/` (des dizaines de commandes Claude, format Markdown)
- `.gemini/commands/` → commandes Gemini natives (`.toml`) pour `/dev`, `/discovery`, `/ship`, `/quick-fix`, `/status`
- `.gemini/gemini-extension.json` → manifest recommandé pour `gemini --extension-dir`
- `.claude-plugin/plugin.json` → manifest Claude Code (parallèle)

## Règles projet

1. **Lire `.claude/CLAUDE.md`** pour le workflow complet (D-EPCT+R, RALPH, conventions).
2. **Avant d'utiliser un skill**, ouvrir son `SKILL.md` et suivre ce fichier exactement.
3. **Traiter `.claude/` comme source de vérité unique.** Ne pas dupliquer la logique des skills.
4. **Spec convention** : toute nouvelle feature doit avoir une spec dans `docs/planning/specs/YYYY-MM-DD-<slug>-design.md` avec frontmatter `status: approved, approved_by: human` avant d'être codée en mode autonome.

## Commandes natives Gemini

| Commande | Usage |
|---|---|
| `/dev [issue]` | Workflow adaptatif niveaux 0-4, stop unique au plan, boucle quality-gate |
| `/discovery` | Planning niveaux 0-4 : tech-spec directe ou chaîne complète, spec approuvée en sortie |
| `/ship` | Merge main + preuves manifeste + gate file (PASS ou waiver) + PR |
| `/quick-fix "desc"` | Fix rapide — niveau 0 du moteur dev-workflow, escalade auto |
| `/status` | État du projet |

Les autres commandes (`/auto-dev`, `/skillz-doctor`, `/pr-review`, etc.) restent Claude-native dans `.claude/commands/`. Gemini peut lire leurs instructions comme contexte, mais elles ne sont pas packagées en TOML natif.

## Skills partages

| Skill | Usage |
|---|---|
| `thermo-nuclear-code-quality-review` | Review maintenabilite tres stricte : abstractions, fichiers geants, branches spaghetti, simplification structurelle |

## Installation

### Option 1 — Extension Gemini (recommandé)

```bash
gh repo clone elsolal/Skillz-Claude-Codex-And-More
gemini --extension-dir ./Skillz-Claude-Codex-And-More/.gemini
```

### Option 2 — Install universel

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install all
```

## Différences avec Claude Code

- **Commands format** : Gemini attend du TOML (`.toml`) en natif. Les 5 commandes portables vivent dans `.gemini/commands/`; les autres commandes Markdown restent dans `.claude/commands/` pour Claude Code.
- **Skills** : 100% compatible (même format `SKILL.md` avec frontmatter).
- **MCP** : non configuré ici (à déclarer dans `.gemini/gemini-extension.json` > `mcpServers` si besoin).
