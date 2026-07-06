---
description: 'Standalone quality-gate loop on a diff — multi-lens review, adversarial counter-verification, gate file PASS/CONCERNS/FAIL/WAIVED'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/quality-gate/SKILL.md`, READ its entire contents, and execute the loop in **standalone mode**: report first, ZERO file modification before the user arbitrates. After counter-verification, present the detailed report (file:line, severity, confirmed/refuted with reason, proposed fix), then ask: [A] apply all confirmed P0/P1 and continue the loop | [S] select fixes | [R] report only (gate file written with the as-is verdict).

The user's arguments follow this line: an optional level (1-4, **default 3 = complete review**: correctness/security, readability, performance + design/SEO/a11y lenses when the diff touches those surfaces, up to 4 rounds) and/or a target diff (default: the default-branch diff, `git diff <base>...HEAD`). Run the `project-probe` skill first if `.agents/verification.yaml` is missing.

Output: the gate file `docs/quality/GATE-<date>-<slug>.yaml` committed + a summary (verdict, rounds, findings, decisions taken). PASS requires real executable evidence; without any, the verdict caps at CONCERNS — by design.
