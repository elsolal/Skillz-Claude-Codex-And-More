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

### Global (user-level — all projects)

Install skills, commands, knowledge and templates into `~/.claude/` so they're available in **every project**. Preserves your existing CLAUDE.md, settings.json, and mcp.json.

```bash
# Install or update (same command)
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- --global
```

### Per-project (Mac / Linux)

```bash
# One-line install
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- .

# Update (preserves CLAUDE.md, settings.json, mcp.json)
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude/main/install.sh | bash -s -- . --update
```

### Windows (PowerShell)

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

### Claude Code only (without multi-agent dirs)

```bash
git clone --depth 1 https://github.com/elsolal/Skillz-Claude.git
cp -r Skillz-Claude/.claude/ .claude/
rm -rf Skillz-Claude
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

### Design

| Command | Description |
|---------|-------------|
| `/figma-setup [url]` | Configure Code Connect |
| `/figma-to-code <url>` | Generate code from Figma |
| `/supabase-security <url>` | Full Supabase security audit |

### RALPH (autonomous mode)

| Command | Max Iter | Timeout | Completion Promise |
|---------|----------|---------|-------------------|
| `/auto-loop "prompt"` | 20 | 1h | "DONE" |
| `/auto-discovery "idea"` | 30 | 1h | "DISCOVERY COMPLETE" |
| `/auto-dev #123` | 50 | 2h | "DEV COMPLETE" |

Options: `--max N`, `--timeout Xh`, `--verbose`

Stop: `/cancel-ralph` | Resume: `/resume-ralph [session-id]`

---

## Skills (21)

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
| `figma-setup` | Code Connect config | Mappings, publication |
| `figma-to-code` | Code generation | Figma URL → code with mapped components |
| `figma-designer` | Design in Figma | Create designs via MCP Console |
| `figma-design-system` | DS management | Tokens, audit, code→Figma, drift detection |
| `figma-design-code-sync` | Design-code sync | Bidirectional component sync |

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
├── commands/                        # 20 slash commands
│   ├── discovery.md                 # /discovery (orchestrator)
│   ├── dev.md                       # /dev (orchestrator + subagents)
│   ├── auto-discovery.md            # /auto-discovery (RALPH)
│   ├── auto-dev.md                  # /auto-dev (RALPH)
│   ├── ship.md, qa.md, ...          # Ship & QA commands
│   └── ...
├── skills/                          # 21 skills
│   ├── idea-brainstorm/
│   ├── pm-prd/
│   ├── architect/
│   ├── pm-stories/
│   ├── code-implementer/            # Agent worker
│   ├── test-runner/                 # Agent worker
│   ├── code-reviewer/               # Parallel-ready
│   ├── figma-*/                     # Figma integration (3 skills)
│   └── ...
├── knowledge/                       # 51 files
│   ├── testing/                     # 32 files (levels, priorities, fixtures...)
│   ├── workflows/                   # 10 files (templates, patterns, estimation)
│   ├── brainstorming/               # Techniques CSV (61 techniques)
│   ├── multi-mind/                  # Agent personalities, debate templates
│   ├── supabase-security/           # 7 audit files
│   └── figma/                       # Code Connect, MCP, tokens
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

51 files across testing (32), workflows (10), brainstorming (1), multi-mind (2), supabase-security (7), figma (3).

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

Works with Claude Code, OpenAI Codex, Google Gemini CLI, and OpenCode. The `.agents/`, `.codex/`, `.gemini/`, `.opencode/` directories are symlinks to `.claude/` — single source of truth.

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
