---
description: 'Quick fix for small bugs and typos — minimal overhead, max 3 files / 50 lines'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/quick-fix-workflow/SKILL.md`, READ its entire contents, and execute the 5 steps sequentially.

The user's problem description follows this line.

This workflow is for SMALL fixes only:
- Max 3 files modified
- Max 50 lines changed
- No new dependency
- No architectural change

If at any point the fix grows beyond these limits, STOP and tell the user to restart with `/dev`. Do not auto-commit — present the change and let the user decide.
