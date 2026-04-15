---
description: Quick fix for small bugs and typos
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `.opencode/skills/quick-fix-workflow/SKILL.md` if it exists, otherwise `.claude/skills/quick-fix-workflow/SKILL.md`, READ its entire contents, and execute the workflow sequentially.

The user's problem description is: $ARGUMENTS

This workflow is for SMALL fixes only:
- Max 3 files modified
- Max 50 lines changed
- No new dependency
- No architectural change

If at any point the fix grows beyond these limits, STOP and tell the user to restart with `/dev`. Do not auto-commit. Present the change and let the user decide.
