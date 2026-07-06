---
description: 'Ship v6: merge main, manifest evidence, quality-gate consumption (PASS or explicit waiver), CHANGELOG, commit, push, PR'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/ship-workflow/SKILL.md`, READ its entire contents, and execute all steps sequentially.

NON-INTERACTIVE: the user said /ship, so DO IT — the next thing they see is the PR URL. Quality comes from the committed gate file (`docs/quality/GATE-*.yaml`): PASS and fresh → straight to PR with the gate in the body; absent/stale/CONCERNS/FAIL → the skill runs quality-gate itself. Only stop for: main branch, unresolvable merge conflicts, red execution evidence, gate FAIL, or the explicit CONCERNS-waiver decision.
