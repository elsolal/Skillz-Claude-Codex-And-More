# D-EPCT+R Workflow

> Skills Claude Code pour un workflow de développement structuré — du brainstorm au déploiement.

An orchestrator-based workflow that guides you through the full development lifecycle across Claude Code, Codex, Gemini, OpenCode, and generic agents.

```
/discovery → /dev → /ship
```

---

## Features

- **Orchestrator pattern** — the main thread keeps full context across all phases. Only mechanical work (code, tests, reviews, issue creation) is dispatched to parallel subagents.
- **Three-command workflow** — `/discovery` for planning, `/dev` for implementation, `/ship` for delivery.
- **Autonomous mode (RALPH)** — `/auto-discovery`, `/auto-dev`, `/auto-loop` run the same workflows without validation stops, with safety gates to prevent runaway execution.
- **Multi-provider** — one source of truth in `.claude/`, mirrored into Codex, Gemini, OpenCode, and generic agent folders.
- **34 skills** — planning (PRD, architecture, stories), design (UX, UI, Figma integration), development (code, tests, review, security, performance), audio/video (ElevenLabs, Remotion).
- **48 knowledge files** — testing frameworks, workflow templates, brainstorming techniques, Supabase security.
- **Multi-Mind debate** — 6 AI agents (Claude, GPT, Gemini, DeepSeek, GLM, Kimi) validate PRDs and code through 5 iterative rounds.

---

## Installation

### Global (everywhere)

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install all
```

Installs into `~/.claude/`, `~/.codex/`, `~/.gemini/`, `~/.config/opencode/`, and `~/.agents/`. Claude is the source of truth; the others mirror it.

### Per-project

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install .
```

Creates `.claude/`, `.codex/`, `.gemini/`, `.opencode/`, `.agents/`, and `docs/` inside the current repository.

### Update

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- update all
```

Your provider config (`CLAUDE.md`, `settings.json`, `mcp.json`) is preserved — only the managed workflow section is refreshed.

<details>
<summary><strong>Install one provider at a time</strong></summary>

Claude must be installed first since the other providers mirror it.

```bash
# Global
./install.sh install claude
./install.sh install codex      # after Claude
./install.sh install gemini     # after Claude
./install.sh install opencode   # after Claude
./install.sh install agents     # after Claude

# Per-project — picks the providers you want
./install.sh install . --providers claude
./install.sh install . --providers codex,gemini
./install.sh install . --providers opencode
```

| Provider | Installed into | What you get |
|---|---|---|
| Claude Code | `~/.claude/` | Full skills, all Claude slash commands, knowledge, templates |
| OpenAI Codex CLI | `~/.codex/` | Skill symlinks, 5 Codex-native prompts, generated `AGENTS.md` |
| Google Gemini CLI | `~/.gemini/` | Skill symlinks, 5 Gemini-native commands, generated `GEMINI.md` |
| OpenCode | `~/.config/opencode/` | Skill symlinks, 5 OpenCode-native commands, generated `AGENTS.md` |
| Generic agents | `~/.agents/` | Skill symlinks and generated `AGENTS.md` |

</details>

<details>
<summary><strong>Update and uninstall</strong></summary>

```bash
# Update
./install.sh update all
./install.sh update claude
./install.sh update codex
./install.sh update gemini
./install.sh update opencode
./install.sh update agents

# Uninstall (keeps user-added content)
./install.sh uninstall all
./install.sh uninstall claude
./install.sh uninstall codex
./install.sh uninstall gemini
./install.sh uninstall opencode
./install.sh uninstall agents

# Per-project update
./install.sh update . --providers all
./install.sh update . --providers codex,gemini

# Help
./install.sh help
```

Drift protection: `~/.claude/.skillz-manifest` tracks skills and Claude commands installed by Skillz. During updates, items previously managed by Skillz but no longer in the source are removed. User-added skills are not touched.

</details>

<details>
<summary><strong>Provider-native packages (Claude plugin, Gemini extension)</strong></summary>

Use these only when you explicitly want a provider package instead of the universal installer.

| Provider | Command | Scope |
|---|---|---|
| Claude Code | `claude --plugin-dir /path/to/Skillz-Claude-Codex-And-More` | Loads the plugin from `.claude-plugin/plugin.json`. |
| Gemini CLI | `gemini --extension-dir /path/to/Skillz-Claude-Codex-And-More/.gemini` | Loads Gemini-native TOML commands plus `.gemini/GEMINI.md`. |
| OpenCode | `./install.sh install opencode` | No bundled JS/TS plugin yet — use the universal installer. |

```bash
gh repo clone elsolal/Skillz-Claude-Codex-And-More

# Claude Code plugin
claude --plugin-dir ./Skillz-Claude-Codex-And-More

# Gemini CLI extension
gemini --extension-dir ./Skillz-Claude-Codex-And-More/.gemini
```

Reload skills with `/reload-plugins` (Claude Code) or restart your agent after manifest changes.

</details>

Diagnostic: `/skillz-doctor` (v5.8.0+) and autonomous safety gates (v5.7.0+) are documented in [CHANGELOG.md](./CHANGELOG.md).

<details>
<summary><strong>Manual Windows install</strong></summary>

```powershell
git clone https://github.com/elsolal/Skillz-Claude-Codex-And-More.git
Copy-Item -Recurse -Force Skillz-Claude\.claude\ .\.claude\
Copy-Item -Recurse -Force Skillz-Claude\.agents\ .\.agents\
Copy-Item -Recurse -Force Skillz-Claude\.codex\ .\.codex\
Copy-Item -Recurse -Force Skillz-Claude\.gemini\ .\.gemini\
Copy-Item -Recurse -Force Skillz-Claude\.opencode\ .\.opencode\
New-Item -ItemType Directory -Force -Path docs\planning\brainstorms, docs\planning\ux, docs\planning\prd, docs\planning\ui, docs\planning\architecture, docs\stories, docs\ralph-logs, docs\debates, docs\security
Remove-Item -Recurse -Force Skillz-Claude
```

</details>

---

## Quick Start

### 1. New idea → full planning

```
/discovery
> "I want to build a personal expense tracker with categories and budget alerts"
```

The orchestrator guides you through Brainstorm → PRD → Architecture → Stories → GitHub Issues. You validate at each checkpoint.

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

## Commands

| Category | Command | Description |
|---|---|---|
| **Planning** | `/discovery` | Full planning with validation at each step |
| | `/auto-discovery "idea"` | Autonomous planning (RALPH) |
| **Dev** | `/dev [issue]` | Multi-agent implementation with validation |
| | `/auto-dev #123` | Autonomous implementation (RALPH) |
| | `/quick-fix "desc"` | Fix without full workflow |
| | `/refactor <file>` | Targeted refactor with 3-pass review |
| **Ship & QA** | `/ship [branch]` | Merge → tests → review → changelog → PR |
| | `/qa [url]` | Systematic QA + health score |
| | `/plan-review <doc>` | CEO/Founder review (Expansion/Hold/Reduction) |
| | `/retro [--since 7d]` | Engineering retrospective |
| **Utilities** | `/status` | Project state (docs, issues, RALPH) |
| | `/pr-review #123` | Review a PR (3 parallel agents) |
| | `/docs [type]` | Generate docs (readme\|api\|guide\|all) |
| | `/changelog [version]` | Generate CHANGELOG.md |
| | `/metrics` | Metrics dashboard |
| | `/init [template]` | Scaffold (next\|express\|api\|cli\|lib) |
| **Design** | `/ds-doc [--figma url]` | Document design system in CLAUDE.md |
| | `/supabase-security <url>` | Full Supabase security audit |

> Figma skills are auto-triggered via descriptions — no slash commands needed.

<details>
<summary><strong>RALPH autonomous commands (limits and overrides)</strong></summary>

| Command | Max Iter | Timeout | Completion Promise |
|---|---|---|---|
| `/auto-loop "prompt"` | 20 | 1h | `DONE` |
| `/auto-discovery "idea"` | 30 | 1h | `DISCOVERY COMPLETE` |
| `/auto-dev #123` | 50 | 2h | `DEV COMPLETE` |

Options: `--max N`, `--timeout Xh`, `--verbose`
Stop: `/cancel-ralph` — Resume: `/resume-ralph [session-id]`

</details>

<details>
<summary><strong>Command availability per provider</strong></summary>

Claude Code receives the full command set. Codex, Gemini, and OpenCode receive the portable subset:

| Command | Claude | Codex | Gemini | OpenCode |
|---|---:|---:|---:|---:|
| `/dev <task>` | Yes | Yes | Yes | Yes |
| `/discovery <idea>` | Yes | Yes | Yes | Yes |
| `/ship` | Yes | Yes | Yes | Yes |
| `/quick-fix "<problem>"` | Yes | Yes | Yes | Yes |
| `/status` | Yes | Yes | Yes | Yes |
| `/refactor`, `/pr-review`, `/retro`, RALPH commands, etc. | Yes | No | No | No |

Model choice does not change command discovery — each CLI discovers commands from its own folder.

</details>

---

## Architecture

The orchestrator (main thread) keeps ALL context. It never forks to isolated skills for planning. Only execution (code, tests, reviews, issue creation) is dispatched to subagents via `SendMessage`.

**Frontend-aware:** after Explore, the workflow auto-detects frontend work (Figma URLs, `.tsx` files, `components/CLAUDE.md`) and prioritizes component reuse, token usage, and Figma mapping. After implementation, it proposes `/ds-doc --update` to keep design system documentation in sync.

<details>
<summary><strong>Full workflow diagram</strong></summary>

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

</details>

<details>
<summary><strong>Checkpoints and gates</strong></summary>

**Planning (orchestrator keeps context)**

| Checkpoint | Phase | Gate |
|---|---|---|
| Brainstorm | Discovery | Direction validated |
| UX Design | Discovery (optional) | Personas and journeys validated |
| PRD | Discovery | Scope defined |
| UI Design | Discovery (optional) | Tokens and components validated |
| Architecture | Discovery | Stack approved |
| **Readiness** | Stories | **Score ≥ 13/15** |

**Development (orchestrator + subagents)**

| Checkpoint | Phase | Gate |
|---|---|---|
| Explore | Subagent | Architecture understood |
| Plan | Orchestrator | Steps approved |
| Code+Tests | 2 parallel subagents | **Lint + Types pass** |
| Review | 3 parallel subagents | **3 passes OK** |

</details>

---

## Skills (34)

Six groups, all auto-triggered from skill descriptions.

- **Planning** — `idea-brainstorm`, `pm-prd`, `architect`, `pm-stories`, `api-designer`, `database-designer`
- **Design** — `ux-designer`, `ui-designer`, `ds-doc`
- **Figma integration (8)** — `figma-use`, `figma-implement-design`, `figma-generate-design`, `figma-generate-library`, `figma-code-connect`, `figma-create-design-system-rules`, `figma-create-new-file`, `figma-design-code-sync`
- **Audio & Video** — `elevenlabs`, `remotion`
- **Development** — `github-issue-reader`, `code-implementer`, `test-runner`, `code-reviewer`, `security-auditor`, `performance-auditor`, `supabase-security`, `multi-mind`

<details>
<summary><strong>Full skills breakdown with key features</strong></summary>

**Planning**

| Skill | Role | Key Features |
|---|---|---|
| `idea-brainstorm` | Creative exploration | 61 techniques, 10 categories, anti-bias protocol |
| `pm-prd` | Product Requirements | FULL/LIGHT auto-detection, templates |
| `architect` | Technical architecture | Stack, structure, data model, APIs |
| `pm-stories` | Epics + Stories | INVEST, Given/When/Then, Readiness Check /15 |
| `api-designer` | API design | OpenAPI 3.1, REST/GraphQL, versioning |
| `database-designer` | Database design | ERD, migrations, indexes, Prisma/Drizzle |

**Design (optional, auto-triggered)**

| Skill | Role | Key Features |
|---|---|---|
| `ux-designer` | User experience | Personas, user journeys, wireframes |
| `ui-designer` | Design system | Tokens, components, Figma import |
| `ds-doc` | DS documenter | Scan project → CLAUDE.md + components/CLAUDE.md with Figma links |

**Figma (from figma/mcp-server-guide)**

| Skill | Role | Key Features |
|---|---|---|
| `figma-use` | **Mandatory prereq** | Plugin API rules, gotchas, pre-flight checklist |
| `figma-implement-design` | Figma → Code | 7-step workflow: design context → screenshot → assets → translate → validate |
| `figma-generate-design` | Code → Figma | Build screens from design system components, variables, styles |
| `figma-generate-library` | Build DS in Figma | Multi-phase: tokens → file structure → components → QA |
| `figma-code-connect` | Code Connect | Parserless .figma.js templates mapping Figma components to code |
| `figma-create-design-system-rules` | DS rules | Generate CLAUDE.md/AGENTS.md rules for Figma-to-code workflows |
| `figma-create-new-file` | Create files | Create new Figma design or FigJam files via MCP |
| `figma-design-code-sync` | Bidirectional sync | Detect drift between Figma components and code counterparts |

**Audio & Video**

| Skill | Role | Key Features |
|---|---|---|
| `elevenlabs` | Voice AI | TTS (70+ languages, 22+ voices), music generation, SFX, batch pipeline |
| `remotion` | React video | 40 rule files, animations, captions, transitions, ElevenLabs→Remotion voiceover pipeline |

**Development**

| Skill | Role | Key Features |
|---|---|---|
| `github-issue-reader` | Issue reading | Categorization, ambiguity classification |
| `code-implementer` | Implementation | Lint/types mandatory, agent worker |
| `test-runner` | Tests | P0-P3 risk-based, 9 knowledge refs |
| `code-reviewer` | Review (3 passes) | Correctness → Readability → Performance |
| `security-auditor` | Security audit | OWASP Top 10, CVE, secrets |
| `performance-auditor` | Performance audit | Core Web Vitals, Lighthouse, bundle |
| `supabase-security` | Supabase audit | RLS, buckets, auth, CVSS scoring |
| `multi-mind` | Multi-agent debate | 6 AIs, 5 iterative rounds |

</details>

---

## Multi-Mind Debate

6 AI agents debate to validate PRDs and code through 5 rounds: Critique → Frictions → Debate → Convergence → Consensus.

```bash
/multi-mind prd docs/PRD/PRD-Feature.md    # Validate a PRD
/multi-mind review src/components/Auth.tsx  # Multi-perspective review
```

| Agent | Provider | Role | Cost |
|---|---|---|---|
| Claude | Anthropic | Prudent Architect | Included |
| GPT | OpenAI | Perfectionist | Paid |
| Gemini | Google | UX Innovator | Paid |
| DeepSeek | DeepSeek | Provocateur | Free |
| GLM | Zhipu AI | Frontend Craftsman | Free |
| Kimi | Moonshot | Product Thinker | Free |

Setup: create `.env.local` with API keys (see `.env.example`). Minimum 3 agents for a valid debate.

---

## Multi-Agent Compatibility

Works with Claude Code, OpenAI Codex CLI, Google Gemini CLI, OpenCode, and generic agents. `.agents/`, `.codex/`, `.gemini/`, and `.opencode/` mirror `.claude/` as the single source of truth, while provider-native command files live in each provider folder.

<details>
<summary><strong>Project structure</strong></summary>

```
.claude/
├── CLAUDE.md                        # Project instructions
├── commands/                        # 22 Claude slash commands
│   ├── discovery.md                 # /discovery (orchestrator)
│   ├── dev.md                       # /dev (orchestrator + subagents)
│   ├── auto-discovery.md            # /auto-discovery (RALPH)
│   ├── auto-dev.md                  # /auto-dev (RALPH)
│   ├── ship.md, qa.md, ...          # Ship & QA commands
│   └── ...
├── skills/                          # 34 skills
│   ├── idea-brainstorm/
│   ├── pm-prd/
│   ├── architect/
│   ├── pm-stories/
│   ├── code-implementer/            # Agent worker
│   ├── test-runner/                 # Agent worker
│   ├── code-reviewer/               # Parallel-ready
│   ├── figma-*/                     # Figma integration (8 skills)
│   ├── elevenlabs/                  # TTS, music, SFX
│   ├── remotion/                    # React video
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

</details>

<details>
<summary><strong>Knowledge system</strong></summary>

Progressive loading based on complexity:

| Level | When | Example |
|---|---|---|
| **core** | Always | `test-levels-framework.md` |
| **advanced** | If complex | `fixture-architecture.md` |
| **debugging** | If problem | `test-healing-patterns.md` |

48 files across testing (32), workflows (10), brainstorming (1), multi-mind (2), supabase-security (7). Figma references are bundled inside skills.

</details>

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
