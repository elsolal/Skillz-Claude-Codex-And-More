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

## QMD (tobi/qmd)

The `qmd/` skill is vendored to give the agent a CLI for searching markdown vaults. The CLI itself (`qmd`) is **not** vendored — it must be installed separately by the user (`brew install tobi/tap/qmd` on macOS, or see upstream for other platforms). The skill teaches the agent how to call the binary, build collections, and index vaults.

| Asset | Source path |
|-------|-------------|
| `skills/qmd/SKILL.md` | (originally upstreamed, then customized locally) |
| `skills/qmd/references/` | reference docs for QMD CLI usage |

**Upstream (binary)** : https://github.com/tobi/qmd
**Author** : Tobias Lütke ([@tobi](https://github.com/tobi))
**License** : MIT

The Obsidian vault and its QMD index are managed together by `setup-wiki.sh` — the script verifies that `qmd` is on `PATH` and (optionally) builds the initial index of the vault.
