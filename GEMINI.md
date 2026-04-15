# Skillz-Claude — Gemini CLI extension

D-EPCT+R workflow (Explore → Plan → Implement → Review → Ship) + 34 skills + 22 slash commands, adapté pour Gemini CLI.

## Source de vérité

`.claude/CLAUDE.md` dans ce repo contient le workflow complet. Ce fichier `GEMINI.md` sert de context file d'entrée pour Gemini CLI.

## Layout (extension root)

- `skills/` → symlink vers `.claude/skills/` (34 skills)
- `commands/` → symlink vers `.claude/commands/` (22 slash commands, format markdown)
- `.claude-plugin/plugin.json` → manifest Claude Code (parallèle)
- `gemini-extension.json` → ce manifest

## Règles projet

1. **Lire `.claude/CLAUDE.md`** pour le workflow complet (D-EPCT+R, RALPH, conventions).
2. **Avant d'utiliser un skill**, ouvrir son `SKILL.md` et suivre ce fichier exactement.
3. **Traiter `.claude/` comme source de vérité unique.** Ne pas dupliquer la logique des skills.
4. **Spec convention** : toute nouvelle feature doit avoir une spec dans `docs/planning/specs/YYYY-MM-DD-<slug>-design.md` avec frontmatter `status: approved, approved_by: human` avant d'être codée en mode autonome.

## Commandes clés (référence)

| Commande | Usage |
|---|---|
| `/dev [issue]` | Workflow complet multi-agent |
| `/discovery` | Planning (Brainstorm → PRD → Architecture → Stories) |
| `/ship` | Merge main + tests + review + PR |
| `/quick-fix "desc"` | Fix rapide |
| `/auto-dev #123` | RALPH mode (autonome, gate pre-flight obligatoire) |
| `/skillz-doctor` | Diagnostic install |

Voir `.claude/CLAUDE.md` pour la liste complète.

## Installation

### Option 1 — Extension Gemini (recommandé)

```bash
gh repo clone elsolal/Skillz-Claude-Codex-And-More
gemini --extension-dir ./Skillz-Claude-Codex-And-More
```

### Option 2 — Install universel

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install all
```

## Différences avec Claude Code

- **Commands format** : Gemini attend du TOML (`.toml`) en natif ; nos commandes sont Markdown. Gemini peut les lire via le skill `dev-workflow` / `discovery-workflow` / etc. qui encode le workflow portable.
- **Skills** : 100% compatible (même format `SKILL.md` avec frontmatter).
- **MCP** : non configuré ici (à déclarer dans `gemini-extension.json` > `mcpServers` si besoin).
