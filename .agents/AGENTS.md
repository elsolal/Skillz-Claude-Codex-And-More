<!-- PROJECT-MEMORY-START -->
## Local Project Memory

Before non-trivial work in this project, read the local memory pointer if it exists:

```text
.agents/project-memory.md
```

If that file points to `.claude/project-memory.md`, follow that canonical pointer. It links to durable project memory: related wiki page, long-term vault, QMD collection, and session-capture guidance. Read it first, then inspect the current codebase; the codebase remains the immediate source of truth.

At the end of useful sessions, capture durable decisions, conventions, solved problems, validation commands, and next steps with `/wiki-capture-session <project>`, then ingest the generated source with `/wiki-ingest raw/session-notes/<filename>.md`.

Do not store secrets, credentials, full logs, stack traces, or raw transcripts in memory.
<!-- PROJECT-MEMORY-END -->

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
