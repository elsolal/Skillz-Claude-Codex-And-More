---
description: 'Audit UI, design system et agent-surface avec tokens, composants, a11y, taste, drift Figma/code et signal Lyse optionnel'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `~/.codex/skills/design-audit/SKILL.md` if it exists, otherwise `.claude/skills/design-audit/SKILL.md`, READ its entire contents, and apply the Design Audit workflow to the provided URL, local path, Figma link, screenshot, repo, or latest visible UI/design context.

This is a READ-ONLY audit pass. Do not modify files, commit, push, or run destructive commands. If the input is empty, audit the current repository or latest visible UI context. If the mode is full, squad, ship-gate, `.lyse.yaml` exists, or the user mentions Lyse, also load `references/lyse/README.md`, `cli-runtime.md`, `rule-catalog.md`, and `result-mapping.md`. If the mode is squad or the user asks for many agents, also load `references/lyse-squad/00_REGLES_COMMUNES.md`, `01_MASTER_ORCHESTRATOR.md`, and all `references/lyse-squad/agents/*.md`. If Lyse is useful and the environment supports it, run it as optional static evidence via the skill helper script; otherwise report `Lyse: skipped`. Output the Design Audit Report sections: Input, Mode, Lyse, Verdict, Axis scores, Findings, Top 3 fixes, Next action.
