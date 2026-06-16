# Skills Attribution

This directory bundles skills authored by third parties. We mirror them into Skillz-Claude so they propagate through `install.sh` to every supported provider (Claude / Codex / Gemini / OpenCode / generic agents).

## Taste Skills (Leonxlnx/taste-skill)

The following 9 skills are integrated from [github.com/Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) by Leonxlnx, with the goal of giving the AI good frontend "taste" and blocking generic anti-patterns ("slop").

| Folder | Frontmatter `name` | Source path |
|--------|-------------------|-------------|
| `brutalist-skill/` | `industrial-brutalist-ui` | `skills/brutalist-skill/SKILL.md` |
| `gpt-tasteskill/` | `gpt-taste` | `skills/gpt-tasteskill/SKILL.md` |
| `images-taste-skill/` | `image-taste-frontend` | `skills/images-taste-skill/SKILL.md` |
| `minimalist-skill/` | `minimalist-ui` | `skills/minimalist-skill/SKILL.md` |
| `output-skill/` | `full-output-enforcement` | `skills/output-skill/SKILL.md` |
| `redesign-skill/` | `redesign-existing-projects` | `skills/redesign-skill/SKILL.md` |
| `soft-skill/` | `high-end-visual-design` | `skills/soft-skill/SKILL.md` |
| `stitch-skill/` | `stitch-design-taste` | `skills/stitch-skill/{SKILL.md,DESIGN.md}` |
| `taste-skill/` | `design-taste-frontend` | `skills/taste-skill/SKILL.md` |

**Upstream** : https://github.com/Leonxlnx/taste-skill
**Author** : Leonxlnx ([@lexnlin](https://x.com/lexnlin)), Blueemi ([@blueemi99](https://x.com/blueemi99))
**Website** : https://tasteskill.dev

### Updating

To pull upstream changes :

```bash
cd /tmp && rm -rf taste-skill && git clone --depth 1 https://github.com/Leonxlnx/taste-skill.git
# Diff against current copy :
diff -r /tmp/taste-skill/skills/ .claude/skills/ | grep -E "^(Only in /tmp|diff)" | head
# Apply selectively (use cp for skills you want to refresh)
```

### Companion skill (Skillz-Claude original)

`taste-router/` — meta-skill that picks the right taste-skill + dial values from a brief. Authored locally, not from upstream.

## LLM Wiki (alirezarezvani/claude-skills)

The `llm-wiki/` skill and the six `wiki-*` slash commands are vendored from [github.com/alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) (MIT licensed). The skill turns Claude (and any compatible agent) into a disciplined Obsidian wiki maintainer that incrementally ingests sources and keeps cross-references current — inspired by [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

| Asset | Source path |
|-------|-------------|
| `skills/llm-wiki/` | `engineering/llm-wiki/` (full skill: SKILL.md, scripts, references, agents, expected_outputs) |
| `commands/wiki-init.md` | `commands/wiki-init.md` |
| `commands/wiki-ingest.md` | `commands/wiki-ingest.md` |
| `commands/wiki-query.md` | `commands/wiki-query.md` |
| `commands/wiki-lint.md` | `commands/wiki-lint.md` |
| `commands/wiki-log.md` | `commands/wiki-log.md` |
| `commands/wiki-capture-session.md` | (Skillz-Claude original — wraps `llm-wiki` workflow) |

**Upstream** : https://github.com/alirezarezvani/claude-skills
**Author** : Alireza Rezvani ([@nginitycloud](https://twitter.com/nginitycloud))
**License** : MIT

### Updating

```bash
cd /tmp && rm -rf claude-skills && git clone --depth 1 https://github.com/alirezarezvani/claude-skills.git
diff -r /tmp/claude-skills/engineering/llm-wiki/ skills/llm-wiki/ | head
# Apply selectively
```

### Companion script (Skillz-Claude original)

`scripts/setup-wiki.sh` — smart bootstrap that creates/configures the Obsidian vault, patches `~/.claude/CLAUDE.md`, verifies the `qmd` CLI, and runs a smoke test. Invoked by `install.sh` and by the `/wiki-bootstrap` slash command.

## Rodin (bdebon/rodin.md)

The `rodin/` skill and `/rodin` command are a Skillz-Claude adaptation inspired by Benjamin Debon's public Rodin prompt:

| Asset | Source |
|-------|--------|
| `skills/rodin/SKILL.md` | Original Skillz-Claude skill inspired by `bdebon/rodin.md` |
| `commands/rodin.md` | Skillz-Claude command wrapper |

**Source** : https://gist.github.com/bdebon/e22d0b728abc5f393227440907b334cf
**Author** : Benjamin Debon ([@bdebon](https://github.com/bdebon))

### Adaptation notes

The source prompt is a broad French "anti-chambre d'echo" interlocutor. Skillz-Claude keeps the useful reasoning protocol (anti-complaisance, steelman, claim classification, angles morts, tests de realite) and adapts it into a read-only agent workflow for challenging plans, PRDs, architecture decisions, strategies, and agent reasoning.

## Lyse Labs (lyse-labs/lyse)

The `design-audit/` skill and `/design-audit` command are Skillz-Claude originals inspired by Lyse Labs' approach to static design-system and AI-surface auditing.

| Asset | Source |
|-------|--------|
| `skills/design-audit/SKILL.md` | Original Skillz-Claude workflow inspired by Lyse concepts |
| `skills/design-audit/references/lyse/` | Skillz-Claude integration notes based on upstream docs/rule inventory |
| `skills/design-audit/references/lyse-squad/` | Skillz-Claude original 12-agent workflow based on Lyse audit axes |
| `skills/design-audit/scripts/run-lyse-audit.sh` | Skillz-Claude wrapper around the external npm CLI |
| `commands/design-audit.md` | Skillz-Claude command wrapper |
| `commands/design-audit-squad.md` | Full 12-agent squad command wrapper |

**Upstream** : https://github.com/lyse-labs/lyse
**Package** : `@lyse-labs/lyse`
**License note** : Lyse source code is not vendored here. The skill may call the upstream CLI as an optional external audit signal when the user's environment supports it. Skillz-Claude includes original integration notes and does not copy Lyse implementation files.

### Adaptation notes

Lyse's useful concepts are adapted into the Skillz-Claude loop as rewritten audit axes: tokens, components, stories/docs, accessibility, design taste, Figma/code drift, AI surface and AI governance. The upstream CLI remains optional evidence; the Skillz-Claude verdict comes from the combined workflow and existing skills.

## Roso SEO Squad (local Aymeric workflow)

The `seo-geo-audit/` skill packages the local SEO/GEO audit workflow from `/Users/aymeric/Documents/PROJETS/DEV/SEO_Squad` into the Skillz-Claude provider structure.

| Asset | Source |
|-------|--------|
| `skills/seo-geo-audit/SKILL.md` | Skillz-Claude portable entrypoint |
| `skills/seo-geo-audit/references/seo-squad-framework.md` | Skillz-Claude compact reference |
| `skills/seo-geo-audit/references/seo-squad/` | Full local SEO_Squad pack: rules, master orchestrator, 11 agent prompts, templates |
| `commands/seo-geo-audit.md` | Compact or targeted audit command |
| `commands/seo-geo-squad.md` | Full 11-agent squad orchestration command |

### Adaptation notes

The full SEO_Squad files are vendored as authoritative references so Codex, Claude Code, Gemini, OpenCode and generic agents can run the same workflow without relying on the external local folder. Claude-specific instructions such as Claude in Chrome are adapted at runtime to the available provider tools: browser, WebFetch, WebSearch, Playwright, MCP connectors, screenshots or user-provided exports.

## Playwright CLI (Microsoft)

The `web-navigator/` skill is a Skillz-Claude original orchestration layer that uses `@playwright/cli` as its preferred browser runtime when available. The upstream CLI and its official companion skill are not vendored here; users install them separately.

| Asset | Source |
|-------|--------|
| `skills/web-navigator/SKILL.md` | Skillz-Claude original browser navigation and evidence workflow |
| `skills/web-navigator/references/playwright-cli.md` | Integration notes for the external `@playwright/cli` package |

**Upstream** : https://github.com/microsoft/playwright-cli
**Package** : `@playwright/cli`
**License** : Apache-2.0

### Adaptation notes

Skillz-Claude keeps Playwright CLI as an external runtime and does not copy its implementation. The local workflow adds product-analysis rules on top: safe navigation, no destructive actions by default, evidence status `Confirmé / Déduit / Non vérifié`, and integration with `/qa`, `seo-geo-audit`, `design-audit`, `test-runner` and `taste-critic`.

## QMD (tobi/qmd)

The `qmd/` skill is vendored to give the agent a CLI for searching markdown vaults. The CLI itself (`qmd`) is **not** vendored — it must be installed separately by the user (`npm install -g @tobilu/qmd` or `bun install -g @tobilu/qmd`; see upstream for details). The skill teaches the agent how to call the binary, build collections, refresh embeddings, and expose the local MCP server.

| Asset | Source path |
|-------|-------------|
| `skills/qmd/SKILL.md` | (originally upstreamed, then customized locally) |
| `skills/qmd/references/` | reference docs for QMD CLI usage |

**Upstream (binary)** : https://github.com/tobi/qmd
**Author** : Tobias Lütke ([@tobi](https://github.com/tobi))
**License** : MIT

The Obsidian vault and its QMD index are managed together by `setup-wiki.sh` — the script verifies that `qmd` is on `PATH` and (optionally) builds the initial index of the vault.
