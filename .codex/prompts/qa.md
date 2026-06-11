---
description: 'QA systématique web: navigation, preuves runtime, design/SEO quick checks, health score et rapport'
disable-model-invocation: true
---

IT IS CRITICAL THAT YOU FOLLOW THIS COMMAND: LOAD the FULL `.claude/commands/qa.md`, READ its entire contents, then run the QA workflow for the provided URL, local app, preview, staging, production site, or latest visible browser context.

Before exploring the target, LOAD `~/.codex/skills/web-navigator/SKILL.md` if it exists, otherwise `.claude/skills/web-navigator/SKILL.md`, and use it for browser navigation, screenshots/snapshots, console, network, responsive checks and evidence status. If the app has UI/design-system surface, also load `design-audit`. If the target is public/indexable content, also load `seo-geo-audit` in quick mode.

This is a QA evidence pass. Do not commit, push, mutate production data, submit destructive forms, make purchases, or store browser auth state in the repo. Output the QA report with health score, top issues, evidence, reproduction steps, category, severity and next actions.
