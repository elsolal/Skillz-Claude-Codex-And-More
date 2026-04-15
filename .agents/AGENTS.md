# Agent Instructions

> Source of truth: `.claude/CLAUDE.md`

This folder provides a generic compatibility layer for agents that read `AGENTS.md` and local skill directories.

## Layout

- `skills` points to `../.claude/skills`
- `knowledge` points to `../.claude/knowledge`
- Provider-specific slash commands live in `.codex/`, `.gemini/`, and `.opencode/`

## Rules

1. Read `.claude/CLAUDE.md` for the full project workflow.
2. Before using any skill, open its `SKILL.md` and follow that file.
3. Treat `.claude/` as the single source of truth. Do not duplicate skill logic in this folder.

## Core Workflows

| Workflow | Source skill |
|---|---|
| Feature development | `dev-workflow` |
| Discovery and planning | `discovery-workflow` |
| Shipping | `ship-workflow` |
| Quick fixes | `quick-fix-workflow` |
| Project status | `status-workflow` |
