---
description: D-EPCT+R v6 adaptive feature development: levels 0-4, single plan checkpoint, quality-gate loop
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `.opencode/skills/dev-workflow/SKILL.md` if it exists, otherwise `.claude/skills/dev-workflow/SKILL.md`, READ its entire contents, and execute the workflow in **interactive** mode, sequentially phase-by-phase.

The user's task description is: $ARGUMENTS

If the task looks like an issue reference (`#42`, `owner/repo#42`), fetch it with `gh issue view` as your first step of Phase 1. Otherwise treat the text as a direct feature description.

There is exactly ONE human checkpoint: the plan (Phase 2). Present the full single-screen plan and wait. Levels 3-4 additionally require showing `decisions_prises_en_ton_nom` before proposing ship. Never skip Phase 0 (probe) or Phase 1 (explore); follow the level circuits and the escalation rule exactly as written in the skill.
