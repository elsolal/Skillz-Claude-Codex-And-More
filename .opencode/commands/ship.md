---
description: Ship workflow: tests, review, changelog, commit, push, PR
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `.opencode/skills/ship-workflow/SKILL.md` if it exists, otherwise `.claude/skills/ship-workflow/SKILL.md`, READ its entire contents, and execute all steps sequentially.

This is a NON-INTERACTIVE workflow. The user said `/ship`, which means DO IT. Do not ask for confirmation on version bumps, commit messages, or CHANGELOG content. Only stop for:
- Current branch is `main` (abort)
- Merge conflicts that can't auto-resolve
- Test failures
- CRITICAL findings in pre-landing review
- Remote is ahead of local

Output the PR URL as the final line.
