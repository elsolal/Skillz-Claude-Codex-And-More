# Agent Instructions

> Source of truth: `.claude/CLAUDE.md`

This folder provides project-local compatibility for OpenAI Codex CLI.

## Layout

- `skills/` contains links to `../.claude/skills` plus Codex-only generated `source-command-*` skills when installed through `install.sh`
- `knowledge` points to `../.claude/knowledge`
- `prompts/` contains Codex-native slash command prompts

## Rules

1. Read `.claude/CLAUDE.md` for the full project workflow.
2. Before using any skill, open its `SKILL.md` and follow that file.
3. Treat `.claude/` as the single source of truth. Do not duplicate skill logic in this folder.

## Portable Commands

These Codex prompts load the shared workflow skills:

| Command | Source skill |
|---|---|
| `/dev` | `dev-workflow` |
| `/discovery` | `discovery-workflow` |
| `/ship` | `ship-workflow` |
| `/quick-fix` | `quick-fix-workflow` |
| `/status` | `status-workflow` |

## Wiki Source Commands

For `wiki-*` commands, Codex uses generated skills named `source-command-wiki-*` instead of Claude command files. Re-run `./install.sh update codex` and restart Codex after adding a new wiki command.
