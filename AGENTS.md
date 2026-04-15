# Skillz-Claude — Agent Instructions (AGENTS.md)

Cross-agent context file (OpenCode, Aider, Codex CLI, generic agents) at repo root.

D-EPCT+R workflow (Explore → Plan → Implement → Review → Ship) + 34 skills + 22 slash commands.

## Source de vérité

`.claude/CLAUDE.md` contient le workflow complet. Ce fichier sert de point d'entrée portable pour tout agent qui respecte la convention `AGENTS.md`.

## Layout (repo root)

- `skills/` → symlink vers `.claude/skills/` (34 skills, format SKILL.md)
- `commands/` → symlink vers `.claude/commands/` (22 slash commands, format Markdown)
- `.claude-plugin/plugin.json` → manifest Claude Code plugin
- `.gemini/gemini-extension.json` + `.gemini/GEMINI.md` → extension Gemini CLI native
- `AGENTS.md` → ce fichier (OpenCode + fallback générique)
- `.claude/` → source de vérité + installation standalone via `install.sh`

## Règles projet

1. **Lire `.claude/CLAUDE.md`** pour le workflow complet (D-EPCT+R, RALPH, conventions).
2. **Avant d'utiliser un skill**, ouvrir son `SKILL.md` et suivre ce fichier exactement.
3. **Traiter `.claude/` comme source de vérité unique.** Ne pas dupliquer la logique des skills.
4. **Spec convention** : toute nouvelle feature doit avoir une spec dans `docs/planning/specs/YYYY-MM-DD-<slug>-design.md` avec frontmatter `status: approved, approved_by: human` avant d'être codée en mode autonome (RALPH).

## Commandes clés

| Commande | Usage |
|---|---|
| `/dev [issue]` | Workflow complet multi-agent |
| `/discovery` | Planning (Brainstorm → PRD → Architecture → Stories) |
| `/ship` | Merge main + tests + review + PR |
| `/quick-fix "desc"` | Fix rapide |
| `/auto-dev #123` | RALPH mode (autonome, gate pre-flight obligatoire) |
| `/skillz-doctor` | Diagnostic install |

Voir `.claude/CLAUDE.md` pour la liste complète (22 commandes).

## Installation

### Option 1 — Agent-native (preview selon ton agent)

- **Claude Code** : `claude --plugin-dir .` (utilise `.claude-plugin/plugin.json`, commandes namespacées par Claude Code)
- **Gemini CLI** : `gemini --extension-dir .gemini` (utilise `.gemini/gemini-extension.json` + commandes TOML)
- **OpenCode** : pas de plugin JS/TS packagé ici ; utiliser `./install.sh install opencode` ou les dossiers `.opencode/skills` + `.opencode/commands`

### Option 2 — Install universel (tous providers)

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install all
```

Installe dans `~/.claude/`, `~/.codex/`, `~/.gemini/`, `~/.config/opencode/`, et `~/.agents/` via dossiers provider dédiés.
