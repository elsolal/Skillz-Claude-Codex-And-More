# D-EPCT+R Workflow

> Skills Claude Code pour un workflow de développement structuré — du brainstorm au déploiement.

## What It Does

An orchestrator-based workflow that guides you through the full development lifecycle:

```
/discovery → /dev → /ship
```

- **Discovery** — Brainstorm, PRD, Architecture, Stories, GitHub Issues
- **Dev** — Explore, Plan, Code+Tests (parallel), Review ×3 (parallel)
- **Ship** — Merge, Tests, Review, Changelog, PR

All workflows use an **orchestrator pattern**: the main thread keeps full context across all phases. Only mechanical work (code, tests, reviews, issue creation) is dispatched to parallel subagents.

---

## Installation

Skillz-Claude supports three installation paths. Pick the one matching your setup.

### Provider-native (v5.7.0+, per provider)

If your agent supports native plugins/extensions, use that first — no symlinks, cleanest upgrade path.

| Provider | Command | Manifest used |
|---|---|---|
| Claude Code | `claude --plugin-dir /path/to/Skillz-Claude` | `.claude-plugin/plugin.json` |
| Gemini CLI | `gemini --extension-dir /path/to/Skillz-Claude` | `gemini-extension.json` + `GEMINI.md` |
| OpenCode | Drop repo into `.opencode/plugins/skillz-claude/` | `skills/` + `AGENTS.md` |

```bash
gh repo clone elsolal/Skillz-Claude-Codex-And-More
# Claude Code
claude --plugin-dir ./Skillz-Claude-Codex-And-More
# Gemini CLI
gemini --extension-dir ./Skillz-Claude-Codex-And-More
```

Reload skills with `/reload-plugins` (Claude Code) or restart your agent after manifest changes.

### Universal fallback (works everywhere — this installer)

Skillz-Claude can be installed globally for every project, or locally inside one project. Claude remains the source of truth because the shared skills and knowledge live in `.claude/`; other providers mirror that content in their own native folders.

#### Recommended: install everything globally

Use this when you want the workflows available everywhere:

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- install all
```

This installs all supported global targets:

| Provider | Installed into | What you get |
|---|---|---|
| Claude Code | `~/.claude/` | Full skills, all Claude slash commands, knowledge, templates |
| OpenAI Codex CLI | `~/.codex/` | Skill symlinks, 5 Codex-native prompts, generated `AGENTS.md` |
| Google Gemini CLI | `~/.gemini/` | Skill symlinks, 5 Gemini-native commands, generated `GEMINI.md` |
| OpenCode | `~/.config/opencode/` | Skill symlinks, 5 OpenCode-native commands, generated `AGENTS.md` |
| Generic agents | `~/.agents/` | Skill symlinks and generated `AGENTS.md` |

To update later:

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- update all
```

Your provider config is preserved. For Claude this means `CLAUDE.md`, `settings.json`, and `mcp.json` are kept and only the managed workflow section is refreshed.

#### Global install by provider

Use these commands when you only want one environment:

```bash
# Claude Code only
./install.sh install claude

# Codex only, after Claude has been installed once
./install.sh install codex

# Gemini only, after Claude has been installed once
./install.sh install gemini

# OpenCode only, after Claude has been installed once
./install.sh install opencode

# Generic ~/.agents only, after Claude has been installed once
./install.sh install agents
```

Why install Claude first? The non-Claude providers are mirrors. They intentionally point to the same `~/.claude/skills` and `~/.claude/knowledge` content so you do not maintain five diverging copies.

#### Per-project install

Use this when you want Skillz only inside the current repository:

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- install .
```

This creates `.claude/` plus all provider compatibility folders in the project:

```text
.claude/      # source of truth: skills, commands, knowledge, templates
.codex/       # Codex prompts + symlinks to .claude
.gemini/      # Gemini commands + symlinks to .claude
.opencode/    # OpenCode commands + symlinks to .claude
.agents/      # generic agent instructions + symlinks to .claude
docs/         # planning, stories, RALPH logs, security reports
```

You can also install only the provider folders you need. `.claude/` is still installed as the local backing store:

```bash
# Claude only
./install.sh install . --providers claude

# Codex + Gemini only
./install.sh install . --providers codex,gemini

# OpenCode only
./install.sh install . --providers opencode
```

Update a project install:

```bash
./install.sh update . --providers all
./install.sh update . --providers codex,gemini
```

#### Which commands are available?

Claude Code receives the full command set from `.claude/commands`.

Portable commands are installed natively for Codex, Gemini, and OpenCode:

| Command | Claude | Codex | Gemini | OpenCode | What it does |
|---|---:|---:|---:|---:|---|
| `/dev <task>` | Yes | Yes | Yes | Yes | Feature development: Explore → Plan → Implement → Review ×3 → Ship |
| `/discovery <idea>` | Yes | Yes | Yes | Yes | Planning: Brainstorm → PRD → Architecture → Stories → GitHub |
| `/ship` | Yes | Yes | Yes | Yes | Ship: merge main → tests → review → CHANGELOG → PR |
| `/quick-fix "<problem>"` | Yes | Yes | Yes | Yes | Small bug fix (max 3 files / 50 lines) |
| `/status` | Yes | Yes | Yes | Yes | Project dashboard (read-only) |
| `/refactor`, `/pr-review`, `/retro`, RALPH commands, etc. | Yes | No | No | No | Claude-native commands that rely on Claude-specific workflow assumptions |

Model choice does not change command discovery. Gemini CLI, OpenCode, and Codex discover commands from their own folders, independently of whether the selected model is Claude, Gemini, GPT, or another provider.

#### Update and uninstall

```bash
# Update global installs
./install.sh update all
./install.sh update claude
./install.sh update codex
./install.sh update gemini
./install.sh update opencode
./install.sh update agents

# Remove only Skillz-managed items for one provider
./install.sh uninstall claude
./install.sh uninstall codex
./install.sh uninstall gemini
./install.sh uninstall opencode
./install.sh uninstall agents

# Remove all global Skillz-managed items
./install.sh uninstall all

# Show full help
./install.sh help
```

Drift protection: `~/.claude/.skillz-manifest` tracks skills and Claude commands installed by Skillz. During global updates, items that were previously managed by Skillz but no longer exist in the source are removed. User-added skills are not touched. Provider mirrors remove dead symlinks and preserve native config files.

#### Manual Windows install

```powershell
git clone https://github.com/elsolal/Skillz-Claude.git
Copy-Item -Recurse -Force Skillz-Claude\.claude\ .\.claude\
Copy-Item -Recurse -Force Skillz-Claude\.agents\ .\.agents\
Copy-Item -Recurse -Force Skillz-Claude\.codex\ .\.codex\
Copy-Item -Recurse -Force Skillz-Claude\.gemini\ .\.gemini\
Copy-Item -Recurse -Force Skillz-Claude\.opencode\ .\.opencode\
New-Item -ItemType Directory -Force -Path docs\planning\brainstorms, docs\planning\ux, docs\planning\prd, docs\planning\ui, docs\planning\architecture, docs\stories, docs\ralph-logs, docs\debates, docs\security
Remove-Item -Recurse -Force Skillz-Claude
```

---

## Quick Start

### 1. New idea → Full planning

```
/discovery
> "I want to build a personal expense tracker with categories and budget alerts"
```

The orchestrator will guide you through Brainstorm → PRD → Architecture → Stories → GitHub Issues, keeping full context across all phases. You validate at each checkpoint.

### 2. Implement an existing issue

```
/dev #123
```

The orchestrator explores the codebase, plans the implementation, then dispatches Code + Tests to 2 parallel subagents and Review ×3 to 3 parallel subagents.

### 3. Autonomous mode (RALPH)

```
/auto-discovery "Personal expense tracker app"
/auto-dev #123
```

Same workflows, zero validation stops. Claude works autonomously until completion.

### 4. Ship it

```
/ship
```

Merges main, runs tests, pre-landing review, generates changelog, creates PR.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WORKFLOW COMPLET                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PLANNING (orchestrateur garde tout le contexte)                           │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Brainstorm│ →  │   PRD    │ →  │  Archi   │ →  │ Stories  │ → GitHub    │
│  │ +Research │    │FULL/LIGHT│    │          │    │+Readiness│   (subagent)│
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│        │              │                                                     │
│        ▼              ▼                                                     │
│  ┌──────────┐    ┌──────────┐   (optional, auto-triggered)                │
│  │UX Design │ →  │UI Design │                                              │
│  └──────────┘    └──────────┘                                              │
│                                                                             │
│  DEVELOPMENT (orchestrateur + subagents parallèles)                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐  ┌──────────────┐        │
│  │  EXPLORE │    │   PLAN   │    │  IMPLEMENT   │  │   REVIEW     │        │
│  │ subagent │ →  │orchestr. │ →  │ ┌─ Code //  │→ │ ┌─ Correct  │→ SHIP  │
│  │          │    │(contexte)│    │ └─ Tests //  │  │ ├─ Read     │        │
│  │          │    │          │    │ (2 subagents) │  │ └─ Perf     │        │
│  └──────────┘    └──────────┘    └──────────────┘  └──────────────┘        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  MANUAL: Validation at each checkpoint                                      │
│  RALPH: Fully autonomous with parallel agents                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key principle:** The orchestrator (main thread) keeps ALL context. It never forks to isolated skills for planning. Only execution (code, tests, reviews, issue creation) is dispatched to subagents via `SendMessage`.

**Frontend-aware:** After the Explore phase, the workflow auto-detects frontend work (Figma URLs, `.tsx` files, `components/CLAUDE.md`). When detected, the plan prioritizes component reuse, token usage, and Figma mapping. After implementation, it proposes `/ds-doc --update` to keep the design system documentation in sync.

---

## Commands Reference

### Planning

| Command | Description |
|---------|-------------|
| `/discovery` | Full planning workflow with validation at each step |
| `/auto-discovery "idea"` | Autonomous planning (RALPH mode) |

### Development

| Command | Description |
|---------|-------------|
| `/dev [issue]` | Multi-agent implementation with validation |
| `/auto-dev #123` | Autonomous implementation (RALPH mode) |
| `/quick-fix "desc"` | Quick fix without full workflow |
| `/refactor <file>` | Targeted refactoring with 3-pass review |

### Ship & QA

| Command | Description |
|---------|-------------|
| `/ship [branch]` | Merge → tests → review → changelog → PR |
| `/qa [url]` | Systematic QA testing + health score |
| `/plan-review <doc>` | CEO/Founder review (Expansion/Hold/Reduction) |
| `/retro [--since 7d]` | Engineering retrospective |

### Utilities

| Command | Description |
|---------|-------------|
| `/status` | Project state (docs, issues, RALPH) |
| `/pr-review #123` | Review a GitHub PR (3 parallel agents) |
| `/docs [type]` | Generate documentation (readme\|api\|guide\|all) |
| `/changelog [version]` | Generate CHANGELOG.md |
| `/metrics` | Project metrics dashboard |
| `/init [template]` | Project scaffolding (next\|express\|api\|cli\|lib) |

### Design System & Figma

| Command | Description |
|---------|-------------|
| `/ds-doc [--figma url]` | Document design system in CLAUDE.md (scan + Figma links) |
| `/supabase-security <url>` | Full Supabase security audit |

> Figma skills are now triggered automatically via descriptions — no slash commands needed. See [Skills](#skills-33) section.

### RALPH (autonomous mode)

| Command | Max Iter | Timeout | Completion Promise |
|---------|----------|---------|-------------------|
| `/auto-loop "prompt"` | 20 | 1h | "DONE" |
| `/auto-discovery "idea"` | 30 | 1h | "DISCOVERY COMPLETE" |
| `/auto-dev #123` | 50 | 2h | "DEV COMPLETE" |

Options: `--max N`, `--timeout Xh`, `--verbose`

Stop: `/cancel-ralph` | Resume: `/resume-ralph [session-id]`

---

## Skills (33)

### Planning Phase

| Skill | Role | Key Features |
|-------|------|-------------|
| `idea-brainstorm` | Creative exploration | 61 techniques, 10 categories, anti-bias protocol |
| `pm-prd` | Product Requirements | FULL/LIGHT auto-detection, templates |
| `architect` | Technical architecture | Stack, structure, data model, APIs |
| `pm-stories` | Epics + Stories | INVEST, Given/When/Then, Readiness Check /15 |
| `api-designer` | API design | OpenAPI 3.1, REST/GraphQL, versioning |
| `database-designer` | Database design | ERD, migrations, indexes, Prisma/Drizzle |

### Design Phase (optional, auto-triggered)

| Skill | Role | Key Features |
|-------|------|-------------|
| `ux-designer` | User experience | Personas, user journeys, wireframes |
| `ui-designer` | Design system | Tokens, components, Figma import |
| `ds-doc` | DS documenter | Scan project → CLAUDE.md + components/CLAUDE.md with Figma links |

### Figma Integration (8 skills — official from figma/mcp-server-guide)

| Skill | Role | Key Features |
|-------|------|-------------|
| `figma-use` | **Mandatory prereq** | Plugin API rules, gotchas, pre-flight checklist — load before every `use_figma` call |
| `figma-implement-design` | Figma → Code | 7-step workflow: design context → screenshot → assets → translate → validate |
| `figma-generate-design` | Code → Figma | Build screens from design system components, variables, styles |
| `figma-generate-library` | Build DS in Figma | Multi-phase: tokens → file structure → components → QA (20-100+ use_figma calls) |
| `figma-code-connect` | Code Connect | Parserless .figma.js templates mapping Figma components to code |
| `figma-create-design-system-rules` | DS rules | Generate CLAUDE.md/AGENTS.md rules for Figma-to-code workflows |
| `figma-create-new-file` | Create files | Create new Figma design or FigJam files via MCP |
| `figma-design-code-sync` | Bidirectional sync | Detect drift between Figma components and code counterparts |

### Audio & Video Pipeline

| Skill | Role | Key Features |
|-------|------|-------------|
| `elevenlabs` | Voice AI | TTS (70+ languages, 22+ voices), music generation, sound effects, batch pipeline |
| `remotion` | React video | 40 rule files, animations, captions, transitions, ElevenLabs→Remotion voiceover pipeline |

### Development Phase

| Skill | Role | Key Features |
|-------|------|-------------|
| `github-issue-reader` | Issue reading | Categorization, ambiguity classification |
| `code-implementer` | Implementation | Lint/types mandatory, agent worker |
| `test-runner` | Tests | P0-P3 risk-based, 9 knowledge refs |
| `code-reviewer` | Review (3 passes) | Correctness → Readability → Performance |
| `security-auditor` | Security audit | OWASP Top 10, CVE, secrets |
| `performance-auditor` | Performance audit | Core Web Vitals, Lighthouse, bundle |
| `supabase-security` | Supabase audit | RLS, buckets, auth, CVSS scoring |
| `multi-mind` | Multi-agent debate | 6 AIs, 5 iterative rounds |

---

## Multi-Mind Debate

6 AI agents debate to validate PRDs and code:

```bash
/multi-mind prd docs/PRD/PRD-Feature.md    # Validate a PRD
/multi-mind review src/components/Auth.tsx  # Multi-perspective review
```

| Agent | Provider | Role | Cost |
|-------|----------|------|------|
| Claude | Anthropic | Prudent Architect | Included |
| GPT | OpenAI | Perfectionist | Paid |
| Gemini | Google | UX Innovator | Paid |
| DeepSeek | DeepSeek | Provocateur | Free |
| GLM | Zhipu AI | Frontend Craftsman | Free |
| Kimi | Moonshot | Product Thinker | Free |

**Setup:** Create `.env.local` with API keys (see `.env.example`). Minimum 3 agents for a valid debate.

**5 Rounds:** Critique → Frictions → Debate → Convergence → Consensus

---

## Project Structure

```
.claude/
├── CLAUDE.md                        # Project instructions
├── commands/                        # 21 Claude slash commands
│   ├── discovery.md                 # /discovery (orchestrator)
│   ├── dev.md                       # /dev (orchestrator + subagents)
│   ├── auto-discovery.md            # /auto-discovery (RALPH)
│   ├── auto-dev.md                  # /auto-dev (RALPH)
│   ├── ship.md, qa.md, ...          # Ship & QA commands
│   └── ...
├── skills/                          # 33 skills
│   ├── idea-brainstorm/
│   ├── pm-prd/
│   ├── architect/
│   ├── pm-stories/
│   ├── code-implementer/            # Agent worker
│   ├── test-runner/                 # Agent worker
│   ├── code-reviewer/               # Parallel-ready
│   ├── figma-*/                     # Figma integration (8 skills from figma/mcp-server-guide)
│   ├── elevenlabs/                  # TTS, music, SFX (3 references)
│   ├── remotion/                    # React video (40 rules + 3 assets)
│   ├── ds-doc/                      # Design system documenter
│   └── ...
├── knowledge/                       # 48 files
│   ├── testing/                     # 32 files (levels, priorities, fixtures...)
│   ├── workflows/                   # 10 files (templates, patterns, estimation)
│   ├── brainstorming/               # Techniques CSV (61 techniques)
│   ├── multi-mind/                  # Agent personalities, debate templates
│   └── supabase-security/           # 7 audit files
└── templates/
    ├── github-actions/              # CI/CD templates
    ├── github/                      # PR & issue templates
    ├── git-hooks/                   # pre-commit, commit-msg
    └── devcontainer/                # Docker dev environment

docs/                                # Generated output
├── planning/                        # brainstorms/, ux/, prd/, ui/, architecture/
├── stories/                         # EPIC-{num}-{slug}/
├── debates/                         # Multi-Mind reports
├── security/                        # Supabase audit reports
└── ralph-logs/                      # RALPH session logs

.agents/, .codex/, .gemini/, .opencode/  # Multi-agent compatibility (symlinks)
```

---

## Knowledge System

Progressive loading based on complexity:

| Level | When | Example |
|-------|------|---------|
| **core** | Always | `test-levels-framework.md` |
| **advanced** | If complex | `fixture-architecture.md` |
| **debugging** | If problem | `test-healing-patterns.md` |

48 files across testing (32), workflows (10), brainstorming (1), multi-mind (2), supabase-security (7). Figma references are now bundled inside skills.

---

## Checkpoints

### Planning (orchestrator keeps context)

| Checkpoint | Phase | Gate |
|------------|-------|------|
| Brainstorm | Discovery | Direction validated |
| UX Design | Discovery (optional) | Personas and journeys validated |
| PRD | Discovery | Scope defined |
| UI Design | Discovery (optional) | Tokens and components validated |
| Architecture | Discovery | Stack approved |
| **Readiness** | Stories | **Score >= 13/15** |

### Development (orchestrator + subagents)

| Checkpoint | Phase | Gate |
|------------|-------|------|
| Explore | Subagent | Architecture understood |
| Plan | Orchestrator | Steps approved |
| Code+Tests | 2 parallel subagents | **Lint + Types pass** |
| Review | 3 parallel subagents | **3 passes OK** |

---

## Multi-Agent Compatibility

Works with Claude Code, OpenAI Codex CLI, Google Gemini CLI, OpenCode, and generic agents. The `.agents/`, `.codex/`, `.gemini/`, and `.opencode/` directories mirror `.claude/` as the single source of truth, while provider-native command files live in each provider folder.

---

## Contributing

This project is shared **read-only**. Pull Requests and Issues are not accepted.

You are free to use, copy, and adapt this workflow for your own projects.

---

## Credits

- **[BMAD-METHOD](https://github.com/bmadcode/BMAD-METHOD)** — 32 knowledge files + agent structure
- **[RALPH Protocol](https://ghuntley.com/ralph/)** — Autonomous loop mode

---

## Version History

See [CHANGELOG.md](./CHANGELOG.md) for the full version history.
