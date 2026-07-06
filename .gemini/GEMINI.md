# Gemini Instructions

> Source of truth: `.claude/CLAUDE.md`

This folder provides project-local compatibility for Google Gemini CLI.

## Layout

- `skills` points to `../.claude/skills`
- `knowledge` points to `../.claude/knowledge`
- `commands/` contains Gemini-native custom commands

## Rules

1. Read `.claude/CLAUDE.md` for the full project workflow.
2. Before using any skill, open its `SKILL.md` and follow that file.
3. Treat `.claude/` as the single source of truth. Do not duplicate skill logic in this folder.

## Portable Commands

These Gemini commands load the shared workflow skills:

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
