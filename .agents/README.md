# Multi-Agent Compatibility Layer

Ce dossier permet aux différents outils IA (Codex, Gemini, OpenCode, etc.) d'accéder au même système de skills et knowledge que Claude Code.

## Architecture

```
.agents/          # Dossier générique (fallback)
.codex/           # OpenAI Codex CLI
.gemini/          # Google Gemini CLI
.opencode/        # OpenCode
    │
    ├── skills/       → symlink vers .claude/skills/
    ├── knowledge/    → symlink vers .claude/knowledge/
    ├── commands/     → commandes natives si supportées par le provider
    └── AGENTS.md     → instructions (référence CLAUDE.md)
```

## Source de vérité

Toutes les configurations sont dans **`.claude/`** :

| Dossier | Contenu |
|---------|---------|
| `.claude/skills/` | 33 skills (brainstorm, PRD, architecture, Figma, etc.) |
| `.claude/knowledge/` | 54 fichiers knowledge (testing, workflows, security, Figma) |
| `.claude/commands/` | 21 commandes Claude (discovery, dev, ship, etc.) |
| `.claude/CLAUDE.md` | Instructions principales |

## Utilisation

### Claude Code
```bash
claude
```
Lit automatiquement `.claude/CLAUDE.md`

### OpenAI Codex
```bash
codex
```
Lit `.codex/AGENTS.md` et les prompts dans `.codex/prompts/`

### Gemini CLI
```bash
gemini
```
Lit `.gemini/GEMINI.md` et les commandes dans `.gemini/commands/`

### OpenCode
```bash
opencode
```
Lit `.opencode/AGENTS.md` et les commandes dans `.opencode/commands/`

## Ajouter un nouvel outil

1. Créer le dossier : `mkdir .newtool`
2. Créer les symlinks :
   ```bash
   ln -sf ../.claude/skills .newtool/skills
   ln -sf ../.claude/knowledge .newtool/knowledge
   ```
3. Créer le fichier d'instructions (AGENTS.md, CONFIG.md, etc.)
4. Ajouter un dossier `commands/` ou `prompts/` si l'outil supporte les slash commands natives.

## Maintenance

Seul `.claude/` doit être modifié. Les symlinks propagent automatiquement les changements.
