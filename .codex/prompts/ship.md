---
description: 'Ship workflow: merge main → tests → pre-landing review → CHANGELOG → commit → push → PR'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/ship-workflow/SKILL.md`, READ its entire contents, and execute all 8 steps sequentially.

This is a NON-INTERACTIVE workflow. The user said `/ship`, which means DO IT. Do not ask for confirmation on version bumps, commit messages, or CHANGELOG content. Only stop for:
- Current branch is `main` (abort)
- Merge conflicts that can't auto-resolve
- Test failures
- CRITICAL findings in pre-landing review
- Remote is ahead of local (unusual)

Output the PR URL as the final line. That's the whole output the user needs.
