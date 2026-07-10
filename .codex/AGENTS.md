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

## MCP

Codex MCP servers live in `~/.codex/config.toml` for global installs and `.codex/config.toml` for project templates.
Skillz-Claude ensures:

```toml
[mcp_servers.qmd]
command = "qmd"
args = ["mcp"]
```

Use `qmd` when `wiki/index.md` is not enough to find project memory.

## Portable Commands

These Codex prompts load the shared workflow skills:

| Command | Source skill |
|---|---|
| `/dev` | `dev-workflow` |
| `/discovery` | `discovery-workflow` |
| `/ship` | `ship-workflow` |
| `/qa` | `web-navigator` + Claude `/qa` workflow |
| `/quick-fix` | `dev-workflow` (mode quick-fix) |
| `/status` | `status-workflow` |
| `/rodin` | `rodin` |
| `/design-audit` | `design-audit` |
| `/design-audit-squad` | `design-audit` |
| `/seo-geo-audit` | `seo-geo-audit` |
| `/seo-geo-squad` | `seo-geo-audit` |

## Shared Runtime Skills

| Skill | Usage |
|---|---|
| `web-navigator` | Natural browser navigation, extraction and runtime evidence via Playwright CLI, Browser/MCP or WebFetch fallback |
| `thermo-nuclear-code-quality-review` | Strict maintainability review lens for abstraction debt, giant files, spaghetti branching, and structural simplification |

## Wiki Source Commands

For `wiki-*` commands, Codex uses generated skills named `source-command-wiki-*` instead of Claude command files. Re-run `./install.sh update codex` and restart Codex after adding a new wiki command.
