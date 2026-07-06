---
description: Quick fix via the v6 workflow short circuit (level 0 forced, automatic re-classification)
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `.opencode/skills/dev-workflow/SKILL.md` if it exists, otherwise `.claude/skills/dev-workflow/SKILL.md`, READ its entire contents, and execute the workflow in **quick-fix** mode (level 0 forced).

The user's problem description is: $ARGUMENTS

Short circuit: locate → fix → run the manifest's verification commands → present the fix and a suggested commit. No formal plan, no gate file. If the fix grows beyond level 0 (4th file, >50 lines, new dependency), the workflow re-classifies against the level grid automatically, keeping all work — never tell the user to restart with `/dev`. Never auto-commit.
