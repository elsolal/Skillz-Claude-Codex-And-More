---
description: Capture durable session notes into the Obsidian LLM Wiki raw layer. Usage: /wiki-capture-session [topic]
---

# /wiki-capture-session

Capture only durable learnings from the current coding session into the vault raw layer, then suggest ingesting it.

Vault target: `/Users/aymeric/Documents/Obsidian-Elsolal/Elsolal`

Output directory: `/Users/aymeric/Documents/Obsidian-Elsolal/Elsolal/raw/session-notes/`

## Important exception

The LLM Wiki iron rule says not to edit `raw/`. This command has one narrow exception: it may create a brand-new Markdown file under `raw/session-notes/` because the user explicitly wants session captures to become ingestible raw sources.

Never modify, rename, move, overwrite, or delete an existing file in `raw/`.

## Steps

1. Detect project context:
   - Current working directory.
   - Project name from the current directory basename.
   - Git branch if inside a git repo.
   - Remote URL if available.
   - Related issue or PR if mentioned in the session or arguments.
2. Create a concise source note. Do not include the full transcript.
3. Use this filename pattern:
   - `raw/session-notes/YYYY-MM-DD-<project-or-topic>-session.md`
   - Use lowercase kebab-case.
   - If the file already exists, append a numeric suffix like `-2`; never overwrite.
4. Write only durable content:
   - Project context.
   - Durable decisions.
   - Conventions learned.
   - Commands and validation results.
   - Problems encountered and resolutions.
   - Next steps.
5. End by recommending the exact ingest command:
   - `/wiki-ingest raw/session-notes/<filename>.md`

## Template

```markdown
# Session Capture - <Project or Topic>

Captured: YYYY-MM-DD HH:MM
Source type: coding session summary

## Project Context

- Project name: <name or none>
- Project path: `<absolute path or none>`
- Git branch: `<branch or none>`
- Git remote: `<remote or none>`
- Related issue/PR: <issue, PR, or none>

## Session Goal

- <one to three bullets>

## Durable Decisions

- <decision and rationale>

## Conventions Learned

- <project convention, user preference, reusable pattern>

## Commands / Validation

- `<command>` -> pass | fail | not run | relevant result

## Problems Encountered

- <problem> -> <resolution or current status>

## Next Steps

- <concrete next action>

## Suggested Ingest

Run:

```bash
/wiki-ingest raw/session-notes/<filename>.md
```
```

## Rules

- Keep the note short and useful.
- No secrets, tokens, credentials, full logs, stack traces, or raw transcript.
- If there is no durable learning, say so and do not create a file.
- If there is uncertainty, mark it as uncertainty.

Arguments: $ARGUMENTS
