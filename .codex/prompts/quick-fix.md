---
description: 'Quick fix via the v6 workflow short circuit (level 0 forced, automatic escalation)'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/dev-workflow/SKILL.md`, READ its entire contents, and execute the workflow in **quick-fix** mode (level 0 forced).

The user's problem description follows this line.

Short circuit: locate → fix → run the manifest's verification commands → present the fix and a suggested commit. No formal plan, no gate file. If the fix grows beyond level 0 (4th file, >50 lines, new dependency), the workflow re-classifies against the level grid automatically (it may jump straight to level 2), keeping all work — do not tell the user to restart with `/dev`. Never auto-commit.
