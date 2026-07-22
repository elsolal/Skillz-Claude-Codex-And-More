# D-EPCT+R v6 — Agentic Dev Workflow

> Skills et workflows pour un développement piloté par agents — de l'idée à la PR, avec une qualité **prouvée** plutôt que relue.

One engine, four runtimes (Claude Code, Codex CLI, Gemini CLI, OpenCode), a single human checkpoint, and a **quality gate file** as proof — so you stop re-reading diffs.

```
/discovery  →  /dev  →  /gate  →  /ship
   plan         build     prove      deliver
```

---

## Why v6

| You get | How |
|---|---|
| **One human stop per feature** | `/dev` scales its rigor to the task level (0-4) and stops exactly once: at the plan. Levels 3-4 (auth, migrations, data) add one careful read before ship. |
| **Proven quality, not re-read code** | The `quality-gate` loop (execution evidence → multi-lens reviews → adversarial counter-verification) converges to a versioned **gate file** (`PASS/CONCERNS/FAIL/WAIVED`). `/ship` consumes it — no PASS without real executable proof. |
| **Any stack** | `project-probe` detects the project's real lint/typecheck/test/build commands into `.agents/verification.yaml`. Nothing hardcoded. |
| **Adaptive planning** | `/discovery` uses the same 0-4 grid: direct tech-spec for small scopes, full Brainstorm → PRD → Architecture → Stories above — always ending with an approved spec that mandates `/auto-dev`. |
| **Thinking tools** | `/elicit` (12 named reasoning lenses), `/rodin` (socratic anti-echo), `multi-mind` with its **anti-consensus Contrarian**, and a `[P]` pressure-test before any brainstorm. |
| **Autonomous mode (RALPH)** | `/auto-discovery`, `/auto-dev`, `/auto-loop` — zero stops, hard safety gates (mandate required, gate PASS required, structural-CONCERNS early stop). |
| **Quality squads** | `/design-audit(-squad)` — 12-agent Lyse Design Squad ; `/seo-geo-audit(-squad)` — 11-agent Roso SEO Squad. |
| **Second-brain memory** | Optional Obsidian LLM Wiki: durable decisions, sources and syntheses that compound across sessions. |
| **55+ skills, 55+ knowledge files** | Planning, design, Figma (8 skills), audio/video, security, web navigation — all auto-triggered from descriptions. |

---

## Installation

### Global (everywhere)

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install all
```

Installs into `~/.claude/`, `~/.codex/`, `~/.gemini/`, `~/.config/opencode/`, and `~/.agents/`. Claude is the source of truth; the others mirror it.

#### Portable memory CLI

Global Claude installation also installs the provider-neutral memory command:

```bash
skillz-memory --version
memory --version
```

`skillz-memory` is the collision-safe command and is always managed at
`~/.local/bin/skillz-memory`. `memory` is an alias created only when that name is
free or already points to the Skillz-Claude runtime. An existing third-party
`memory` command is preserved and the installer tells you to use
`skillz-memory` instead.

After a project has a portable manifest and local projection, run `memory
doctor` to verify pages, Git-local exclusions, QMD 0.9.x and local freshness.
The command is read-only and offline by default; `--network` and the narrowly
scoped `--fix` are always explicit. Use `--json` for automation.

Start task-aware retrieval with the project collection first:

```bash
memory context --mode project --task-category architecture "How is this project structured?"
memory context --mode project --task-category security --risk-reason security "Which security decision applies?"
printf '%s' "private task" | memory context --task-category security --query-stdin --json
```

The command uses lexical `qmd search` only, never persists the query, and emits
normalized metadata without raw snippets. A deterministic, versioned gate stops
after sufficient project evidence and only calls one transverse fallback when
the local role and shared manifest policy both allow it. Ambiguous evidence
requires the explicit `--fallback-on-ambiguous` option; `--explain` shows the
same reason codes and evidence exposed in JSON. Empty, timeout, invalid-output,
stale, ambiguous, and missing-QMD states remain distinct outcomes.

When retrieval is sufficient, the CLI emits only the Markdown sections needed
under the selected mode budget, distinguishes `retrieved` from `read`, and uses
the versioned `utf8_bytes_div_4_v1` estimate. Hard-cap overruns require an
explicit, auditable `--risk-reason`.

The CLI requires Python 3.10+ and uses the standard library only. The installer
does not create a virtual environment or download QMD, a model, or another
dependency. If `~/.local/bin` is not already available from your shell, add:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Updates replace only Skillz-managed links. `uninstall claude` and `uninstall
all` remove a recorded link only while it still points to the installed
Skillz-Claude runtime; a command replaced by another tool is preserved.

### Per-project

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- install .
```

Creates `.claude/`, `.codex/`, `.gemini/`, `.opencode/`, `.agents/`, and `docs/` inside the current repository.

### Update

```bash
curl -fsSL https://raw.githubusercontent.com/elsolal/Skillz-Claude-Codex-And-More/main/install.sh | bash -s -- update all
```

Your provider config is preserved. Skillz-managed prompts self-update (loader signature); user and third-party prompts (BMad, etc.) are never touched. Drift protection via `~/.claude/.skillz-manifest`: skills removed from the source are purged, user-added skills are kept.

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
| OpenAI Codex CLI | `~/.codex/` | Skill symlinks, Codex-native prompts, generated wiki `source-command-*` skills, generated `AGENTS.md` |
| Google Gemini CLI | `~/.gemini/` | Skill symlinks, Gemini-native commands, generated `GEMINI.md` |
| OpenCode | `~/.config/opencode/` | Skill symlinks, OpenCode-native commands, generated `AGENTS.md` |
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

<details>
<summary><strong>Optional: Playwright CLI for agent navigation</strong></summary>

Playwright automates real browsers. Installing `@playwright/cli` gives AI agents a terminal-driven way to open a product or public site, click through flows, fill forms, inspect console/network errors, resize viewports, capture screenshots and extract grounded information. Skillz-Claude routes this through `web-navigator`, then QA, SEO/GEO, design and test skills consume the same evidence.

```bash
npm install -g @playwright/cli@latest
playwright-cli install --skills
playwright-cli --help
```

Use it with `web-navigator`, `/qa`, `seo-geo-audit`, `test-runner` and `design-audit` when you want runtime evidence from a local, preview, staging or production URL. `playwright-cli install --skills` installs the companion skills for Claude by default; use `playwright-cli install --skills=agents` for generic agent skills.

</details>

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

Diagnostic: `/skillz-doctor` (v5.8.0+) and autonomous safety gates (v5.7.0+) are documented in [CHANGELOG.md](./CHANGELOG.md).

---

## Quick Start

### 1. New idea → approved spec

```
/discovery
> "I want to build a personal expense tracker with categories and budget alerts"
```

The workflow assesses the level (0-4). Small scope → direct tech-spec. Bigger → Brainstorm → PRD → Architecture → Stories, validated at each checkpoint (`[P]` pressure-tests the idea first, `[E]` applies a reasoning lens before validating). Every discovery ends with an **approved spec** in `docs/planning/specs/` — the mandate for `/auto-dev`.

### 2. Implement — one stop only

```
/dev #123
```

Probe (verification manifest) → Explore + level assessment → **Plan ⛔ (your only stop)** → RED acceptance tests (conditional) → sequential implementation → **quality-gate loop** → gate file + handoff report. You read the report — never the diff. Small fix? `/quick-fix "desc"` runs the same engine at level 0 and auto-escalates if scope grows.

### 3. Prove quality on demand

```
/gate            # complete review (level 3) of the current branch diff
/gate 1          # quick single-reviewer pass
```

Standalone quality-gate loop on any diff — same engine, same gate file as `/dev`.

### 4. Ship it

```
/ship
```

Merges main, runs the manifest evidence, **consumes the gate file** (PASS and fresh → straight to PR with the gate in the body; stale or CONCERNS → re-gates or asks for an explicit waiver), generates the changelog, creates the PR.

### 5. Autonomous mode (RALPH)

```
/auto-discovery "Personal expense tracker app"
/auto-dev #123
```

Zero stops. `/auto-dev` refuses to start without a mandate (GitHub issue or approved spec) and never ships without a PASS gate.

---

## The Quality Engine

The heart of v6 — `project-probe` and `quality-gate` are consumed by `/dev`, `/gate` and `/ship`; `quality-gate` also calls the final `thermo-nuclear-code-quality-review` lens for strict maintainability.

**`project-probe`** detects the project's real verification commands (lint, typecheck, test, build, run) once, and caches them into a committed manifest:

```yaml
# .agents/verification.yaml
stack: node-ts
commands: { lint: "npm run lint", test: "npm test", ... }
testability: { harness: vitest, runtime_verify: "npm run dev" }
absents: ["no e2e harness"]        # explicit, never silently skipped
```

**`quality-gate`** runs a bounded convergence loop: execution evidence first (never skipped) → multi-lens reviews in fresh contexts (correctness/security, readability, performance — plus design/SEO/a11y lenses when the diff touches those surfaces) → final `thermo-nuclear-code-quality-review` maintainability lens for level ≥ 2, de-duplicated against prior findings → **adversarial counter-verification** of every new finding (a refuter attacks it; only confirmed findings get fixed) → repeat until two clean rounds. Output:

```yaml
# docs/quality/GATE-2026-07-06-my-feature.yaml
verdict: PASS                      # PASS | CONCERNS | FAIL | WAIVED
preuve:
  executable: { lint: vert, tests: "vert (47 passed)", ... }
  opinion: { findings: { total: 9, confirmes: 4, corriges: 4, restants: 0 } }
decisions_prises_en_ton_nom: [...]  # the only careful read left to the human
```

**Hard rules**: no PASS without real executable evidence (a project without tests caps at CONCERNS — the gate never claims more than it knows) ; CONCERNS is never auto-accepted (explicit waiver → WAIVED, recorded) ; the loop is bounded (never infinite).

---

## Commands

| Category | Command | Description |
|---|---|---|
| **Planning** | `/discovery "idea"` | Planning in levels 0-4 — tech-spec direct (0-1) or full chain (2-4), approved spec output |
| | `/auto-discovery "idea"` | Autonomous planning (RALPH), spec stays draft until a human approves |
| **Dev** | `/dev [issue]` | Adaptive implementation, levels 0-4, single plan stop, quality-gate loop |
| | `/quick-fix "desc"` | Level-0 short circuit of the same engine, auto-escalates by the grid |
| | `/auto-dev #123` | Autonomous implementation (RALPH), mandate + PASS gate required |
| | `/refactor <file>` | Targeted refactor with review passes |
| **Quality** | `/gate [level] [target]` | **Standalone quality-gate loop** (default level 3 = complete review) → gate file |
| | `/pr-review #123` | Review a GitHub PR (3 core passes + UI/SEO gates when relevant) |
| | `/qa [url]` | Systematic runtime QA + health score |
| **Ship** | `/ship` | Merge → manifest evidence → gate consumption (PASS or waiver) → changelog → PR |
| **Thinking** | `/elicit [lens] [target]` | Re-examine any output through ONE named reasoning lens (12 available) |
| | `/rodin <text\|path\|url>` | Socratic anti-echo challenge of a plan or decision |
| | `/multi-mind prd\|review <file>` | 6-AI debate, 5 rounds, with the anti-consensus Contrarian |
| | `/multi-mind --room anti-consensus <target>` | Short mid-workflow contrarian session on a live decision |
| | `/plan-review <doc>` | CEO/Founder review (Expansion/Hold/Reduction) |
| **Audits** | `/design-audit <target>` | UI/DS audit + ship-gate design evidence |
| | `/design-audit-squad <target>` | Full 12-agent Lyse Design Squad audit |
| | `/seo-geo-audit <target>` | SEO/GEO audit + AI visibility roadmap |
| | `/seo-geo-squad <target>` | Full 11-agent Roso SEO Squad audit |
| **Utilities** | `/status` | Project state (docs, issues, RALPH) |
| | `/retro [--since 7d]` | Engineering retrospective |
| | `/docs [type]` | Generate docs (readme\|api\|guide\|all) |
| | `/changelog [version]` | Generate CHANGELOG.md |
| | `/metrics` | Metrics dashboard |
| | `/init [template]` | Scaffold (next\|express\|api\|cli\|lib) |
| | `/skillz-doctor` | Installation diagnostic |
| **Memory** | `/wiki-*` | Obsidian LLM Wiki commands — see [the wiki section](#obsidian-llm-wiki--second-brain-memory) |

> Figma skills, `ds-doc` (design-system documenter) and `supabase-security` (full Supabase audit) are auto-triggered via descriptions — no slash commands needed.

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

Claude Code receives the full command set. Codex, Gemini, and OpenCode receive the portable subset (Codex prompts carry a loader signature so the installer keeps them up to date):

| Command | Claude | Codex | Gemini | OpenCode |
|---|---:|---:|---:|---:|
| `/dev`, `/discovery`, `/ship`, `/quick-fix`, `/qa`, `/status` | Yes | Yes | Yes | Yes |
| `/rodin` | Yes | Yes | Yes | Yes |
| `/design-audit(-squad)`, `/seo-geo-audit(-squad)` | Yes | Yes | Yes | Yes |
| `/elicit`, `/gate` | Yes | Yes | No | No |
| `/refactor`, `/pr-review`, `/retro`, RALPH commands, etc. | Yes | No | No | No |

Model choice does not change command discovery — each CLI discovers commands from its own folder.

</details>

---

## The v6 Workflow

The orchestrator (main thread) keeps ALL context. Rigor scales with the task level; escalation re-classifies against the grid (a level-0 fix may jump straight to level 2) reusing all acquired work — never restarting.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLANNING (/discovery — levels 0-4)                                         │
│  [P] pressure-test → level 0-1: direct tech-spec ──────────┐               │
│                    → level 2-4: Brainstorm → [UX] → PRD →   ├→ APPROVED    │
│                      [UI] → Architecture → Stories ─────────┘   SPEC       │
│                                                                             │
│  DEVELOPMENT (/dev — levels 0-4)                                            │
│  PROBE → EXPLORE → PLAN ⛔ → RED → IMPLEMENT → GATE (loop) → HANDOFF        │
│  manifest  +level    the one   (cond.) (sequential)  gate file    report    │
│                      stop                                                   │
│                                                                             │
│  DELIVERY (/ship)                                                           │
│  merge main → manifest evidence → gate consumption → changelog → PR        │
├─────────────────────────────────────────────────────────────────────────────┤
│  MANUAL: one stop at PLAN ⛔ — levels 3-4 add a handoff read                │
│  RALPH: zero stops — mandate gate + PASS gate replace them                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

<details>
<summary><strong>Levels grid</strong></summary>

| Level | Signals | Dev circuit |
|---|---|---|
| **0** | typo, constant; ≤3 files, ≤50 lines | Fix → manifest verify → present. No plan, no gate file. |
| **1** | small localized bug | Light explore → mini-plan ⛔ → fix → 1-round gate with quick structural-smell check. |
| **2** | standard feature | Full flow: plan ⛔, RED, sequential implement, gate loop (≤3 rounds) + final thermo-nuclear maintainability lens. |
| **3** | multi-component, public surface | + design/SEO/a11y lenses in the gate, then final thermo-nuclear maintainability lens + human handoff read. |
| **4** | epic, migration, auth, DB schema | Refuses to start without an approved spec — route through `/discovery`. |

</details>

<details>
<summary><strong>Checkpoints and gates</strong></summary>

**Planning (interactive)**

| Checkpoint | Phase | Gate |
|---|---|---|
| Level | Phase 1 | 0-4 assessed, `[P]` pressure-test offered |
| Brainstorm → Stories | Phases 2-7 (levels 2-4) | Validated per phase, `[E]` lens available |
| **Spec** | Phase 7-bis | **Approved by the human** (`status: approved`) |
| Readiness | Stories | Score ≥ 13/15 |

**Development (adaptive)**

| Checkpoint | Phase | Gate |
|---|---|---|
| Probe | Phase 0 | Verification manifest read or refreshed |
| Plan | Phase 2 (⛔ the one stop) | Plan + acceptance criteria approved |
| RED | Phase 3 (level ≥ 2 + harness) | Acceptance tests fail for the right reason |
| Implement | Phase 4 | Manifest commands green per step |
| Gate | Phase 5 | **Gate file: PASS** (or explicit waiver) |
| Handoff | Phase 6 (levels 3-4) | `decisions_prises_en_ton_nom` read by the human |

</details>

---

## Thinking Tools

Three complementary gestures against complacency:

- **`/elicit`** — re-examine an existing output under **one named lens**: Pre-mortem, Inversion, First Principles, Red/Blue Team, Steelman-then-attack, Chesterton's Fence, 10-10-10, Second-Order Effects, Occam's Razor, Constraint Removal, Persona Shift, Cost-of-Delay. The lens reveals; it never rewrites — findings + proposed revisions, you arbitrate. Available at every `/discovery` checkpoint (`[E]`).
- **`/rodin`** — socratic anti-echo challenge (steelman → classified claims → strong objections → reality tests → verdict). Inspired by [Benjamin Debon's rodin.md](https://gist.github.com/bdebon/e22d0b728abc5f393227440907b334cf) — see [ATTRIBUTION](./skills/ATTRIBUTION.md).
- **`multi-mind`** — 6 AI agents (Claude, GPT, Gemini, DeepSeek, GLM, Kimi) debate through 5 rounds, **plus the Contrarian**: an anti-consensus persona whose only mandate is to produce the strongest objection to the emerging consensus — no consensus can be declared until it has been explicitly refuted or integrated. `--room anti-consensus` runs a short contrarian session mid-workflow without breaking your flow. Setup: `.env.local` with API keys (see `.env.example`), minimum 3 agents.

And before any brainstorm: **`[P]` pressure-test** in `/discovery` — challenge the idea socratically first, produce a forge-report (thesis / objections / surviving kernel / verdict) and only invest in planning if the kernel survives.

---

## Skills

Capability groups, all auto-triggered from skill descriptions.

- **Quality engine** — `project-probe`, `quality-gate`, `thermo-nuclear-code-quality-review`
- **Planning** — `idea-brainstorm`, `pm-prd`, `architect`, `pm-stories`, `api-designer`, `database-designer`
- **Thinking** — `elicitation`, `rodin`, `multi-mind`
- **Design** — `ux-designer`, `ui-designer`, `ds-doc`, `design-audit`
- **Web navigation** — `web-navigator`
- **SEO/GEO** — `seo-geo-audit`
- **Figma integration (8)** — `figma-use`, `figma-implement-design`, `figma-generate-design`, `figma-generate-library`, `figma-code-connect`, `figma-create-design-system-rules`, `figma-create-new-file`, `figma-design-code-sync`
- **Audio & Video** — `elevenlabs`, `remotion`
- **Development** — `github-issue-reader`, `code-implementer`, `test-runner`, `code-reviewer`, `security-auditor`, `performance-auditor`, `supabase-security`

<details>
<summary><strong>Full skills breakdown with key features</strong></summary>

**Quality engine**

| Skill | Role | Key Features |
|---|---|---|
| `project-probe` | Verification manifest | Detects lint/typecheck/test/build commands, any stack, fingerprinted cache in `.agents/verification.yaml` |
| `quality-gate` | Quality loop | Bounded convergence loop (evidence + multi-lens review + adversarial counter-verification) → gate file PASS/CONCERNS/FAIL/WAIVED |
| `thermo-nuclear-code-quality-review` | Strict maintainability lens | Harsh structural review for abstraction debt, giant files, spaghetti branching, boundary leaks, and missed simplification moves |

**Planning**

| Skill | Role | Key Features |
|---|---|---|
| `idea-brainstorm` | Creative exploration | 61 techniques, 10 categories, anti-bias protocol, `[E]` lens pass at synthesis |
| `pm-prd` | Product Requirements | Complete (levels 2-4) or synthetic (levels 0-1) PRD, templates |
| `architect` | Technical architecture | Stack, structure, data model, APIs |
| `pm-stories` | Epics + Stories | INVEST, Given/When/Then, Readiness Check /15 |
| `api-designer` | API design | OpenAPI 3.1, REST/GraphQL, versioning |
| `database-designer` | Database design | ERD, migrations, indexes, Prisma/Drizzle |

**Thinking**

| Skill | Role | Key Features |
|---|---|---|
| `elicitation` | Named reasoning lenses | 12 lenses (CSV), one lens at a time, reveals-not-rewrites protocol |
| `rodin` | Socratic challenger | Anti-echo review, steelman, claim classification, blind spots, reality tests |
| `multi-mind` | Multi-agent debate | 6 AIs, 5 iterative rounds, Contrarian anti-consensus room |

**Design (optional, auto-triggered)**

| Skill | Role | Key Features |
|---|---|---|
| `ux-designer` | User experience | Personas, user journeys, wireframes |
| `ui-designer` | Design system | Tokens, components, Figma import |
| `design-audit` | UI/DS audit | Tokens, components, stories/docs, a11y, taste, Figma/code drift, AI governance, Lyse references and 12-agent squad |
| `ds-doc` | DS documenter | Scan project → CLAUDE.md + components/CLAUDE.md with Figma links |

**Web Navigation**

| Skill | Role | Key Features |
|---|---|---|
| `web-navigator` | Web navigation | Playwright CLI, Browser/MCP and WebFetch fallback; pages visited, screenshots/snapshots, console/network and Confirmé/Déduit/Non vérifié evidence |

**SEO/GEO**

| Skill | Role | Key Features |
|---|---|---|
| `seo-geo-audit` | SEO/GEO audit | Technical SEO, content, SERP intent, authority, local SEO, llms.txt, AI visibility, full Roso SEO Squad references |

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
| `code-reviewer` | Review (3 passes) | Correctness → Readability → Performance — used by `/refactor` and `/pr-review` |
| `security-auditor` | Security audit | OWASP Top 10, CVE, secrets |
| `performance-auditor` | Performance audit | Core Web Vitals, Lighthouse, bundle |
| `supabase-security` | Supabase audit | RLS, buckets, auth, CVSS scoring |

</details>

---

## Obsidian LLM Wiki — second-brain memory

A persistent, interlinked knowledge base that grows across sessions, inspired by [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Sources are read once, integrated into a shared Obsidian vault, kept up to date by the agent. The agent reads `wiki/index.md` first, drills into pages, and synthesizes answers — instead of re-deriving everything via RAG on every query.

> **Built on top of [`alirezarezvani/claude-skills`](https://github.com/alirezarezvani/claude-skills) (MIT) — see [`skills/ATTRIBUTION.md`](./skills/ATTRIBUTION.md).**

### One-command install

```bash
bash install.sh install all --with-wiki
```

This runs the standard install **and** bootstraps the wiki: it asks for the vault path, creates the structure, patches `~/.claude/CLAUDE.md`, checks `qmd`, creates or refreshes a named QMD collection, and runs a health check. Skip the bootstrap with `--no-wiki`. Re-run anytime with `bash scripts/setup-wiki.sh` (idempotent).

### Prerequisites

| Tool | Required | Install | Why |
|------|----------|---------|-----|
| **Obsidian** | Yes | [obsidian.md/download](https://obsidian.md/download) (free) | Editor for the vault. Open the chosen folder as a vault inside Obsidian after bootstrap. |
| **Python 3.10+** | Yes | already required by Skillz-Claude | Powers the portable memory CLI and wiki scripts. Stdlib only — no pip install. |
| **`qmd` CLI** | Recommended | `npm install -g @tobilu/qmd` with Node 22+, or `bun install -g @tobilu/qmd`; see [tobi/qmd](https://github.com/tobi/qmd) | Local vector search across the vault for when the index alone is not enough. The setup script warns but does not block if absent. |

### What the bootstrap does

1. **Detects an existing vault** — parses `~/.claude/CLAUDE.md` for a previous `Vault memoire :` line. Reuses it if found.
2. **Creates the vault** at the chosen path (default `~/Documents/Obsidian-<git-user>/Wiki`) with the three-layer structure (`raw/`, `wiki/{entities,concepts,sources,comparisons,synthesis}`, `index.md`, `log.md`).
3. **Patches `~/.claude/CLAUDE.md`** with an idempotent `<!-- BEGIN:llm-wiki-config --> … <!-- END:llm-wiki-config -->` block so every new Claude session knows where the vault lives and how to use it.
4. **Verifies the `qmd` binary** is on your PATH (warns if not).
5. **Optionally creates or refreshes the QMD collection** for `wiki/` (`--with-qmd` to force, prompted in interactive mode), then runs `qmd update` and `qmd embed`.
6. **Smoke-tests** the vault with `lint_wiki.py` (orphans, broken links, frontmatter, log gap).

### QMD MCP across agents

`install/update all` ensures the local QMD MCP server is available in the three agent clients used by this setup:

| Client | Config file | QMD server entry |
|---|---|---|
| Claude Code | project `.mcp.json` and Skillz `.claude/mcp.json` | `"qmd": { "command": "qmd", "args": ["mcp"] }` |
| Codex | `~/.codex/config.toml` | `[mcp_servers.qmd]` with `command = "qmd"` and `args = ["mcp"]` |
| OpenCode | `~/.config/opencode/opencode.json` | `"qmd": { "type": "local", "command": ["qmd", "mcp"], "enabled": true }` |

The installer only adds QMD if it is missing. Existing MCP servers stay in place.

### Local project memory pointers

Project repos should not commit machine-specific memory paths. Shared metadata
lives in `.agents/memory.yaml`; each collaborator maps that portable manifest to
their machine with the memory CLI:

```bash
cd /path/to/project-repo
memory configure --store "project=$OBSIDIAN_MEMORY_ROOT/Pleepole"
memory doctor
```

The command writes `.agents/memory.local.json`, `.claude/project-memory.md`, and
`.agents/project-memory.md` with user-only permissions where supported. It also
adds their worktree-relative paths to Git's local `info/exclude`. Missing entry
pages produce a usable `degraded` result (exit `10`); unmanaged pointer content
is preserved unless replacement is explicitly requested with
`--replace-managed`.

`memory doctor` reports `ready`, `degraded`, or `blocked`, a copyable next
action, and the manifest's golden start question. QMD absence stays usable in
bounded `minimal`/`project` modes; missing required entry pages block activation.
Run `memory doctor --explain` for per-check details or `memory doctor --json` for
the stable machine-readable envelope. Network access occurs only with
`memory doctor --network`; safe managed-file repair occurs only with
`memory doctor --fix`.

Absolute paths stay hidden from command output unless
`--explain-local-paths` is passed. The local role defaults to `collaborator` and
can be declared with `--role owner`; this declaration never grants filesystem,
Git, or remote access.

The historical `scripts/create-project-memory-pointer.sh` interface remains a
compatibility wrapper. Its metadata options are deprecated because the portable
manifest is now authoritative:

```bash
scripts/create-project-memory-pointer.sh \
  --project-dir /path/to/project-repo \
  --vault-path "$OBSIDIAN_MEMORY_ROOT/Pleepole"
```

### Open the vault in Obsidian

After bootstrap:

1. Launch Obsidian.
2. Click **Open folder as vault** and pick the path printed by the script (default: `~/Documents/Obsidian-<your-name>/Wiki`).
3. The vault is now your second brain — but most of the time you will not edit it manually. Use the slash commands below.

### Commands available after install

```
/wiki-bootstrap              Re-run or repair the install (interactive).
/wiki-init <path> --topic …  Create a brand new empty vault (no CLAUDE.md patching).
/wiki-ingest <file>          Ingest a source from raw/ into the wiki, update cross-references.
/wiki-query "<question>"     Ask the wiki — agent drills into 3-10 pages and answers with [[wikilinks]].
/wiki-lint                   Health check: orphans, broken links, stale pages, log gap.
/wiki-log                    Show recent log entries (decisions, ingests).
/wiki-capture-session [topic] Capture durable notes from the current chat into raw/ for later /wiki-ingest.
```

Codex note: Codex does not reliably consume Claude slash command files directly. `install/update codex` generates Codex-only skills like `source-command-wiki-capture-session` in `~/.codex/skills/`, so natural triggers such as `/wiki-capture-session` or "capture cette session dans le wiki" load the right workflow after restarting Codex. OpenCode keeps using its native command folder.

### Manual / advanced flags

```bash
bash scripts/setup-wiki.sh                       # interactive
bash scripts/setup-wiki.sh --vault ~/path        # explicit vault path
bash scripts/setup-wiki.sh --verify              # health check only, no writes
bash scripts/setup-wiki.sh --with-qmd            # update qmd collection and embeddings
bash scripts/setup-wiki.sh --qmd-collection name # explicit qmd collection name
bash scripts/setup-wiki.sh --no-qmd              # skip qmd entirely
bash scripts/setup-wiki.sh --non-interactive     # CI mode, fails if config missing
```

### What never goes in the wiki

Secrets, tokens, credentials, full logs, raw transcripts, stack traces. The wiki is for durable knowledge — decisions, conventions, sources, syntheses. The codebase remains the immediate source of truth.

---

## Multi-Agent Compatibility

Works with Claude Code, OpenAI Codex CLI, Google Gemini CLI, OpenCode, and generic agents. `.agents/`, `.codex/`, `.gemini/`, and `.opencode/` mirror `.claude/` as the single source of truth, while provider-native command files live in each provider folder. Since v6, every workflow lives in ONE canonical skill (English) — commands and prompts are thin launchers, so there is nothing to keep in sync by hand.

<details>
<summary><strong>Project structure</strong></summary>

```
.claude/
├── CLAUDE.md                        # Project instructions (D-EPCT+R section = installer template)
├── commands/                        # Claude slash commands (thin launchers)
│   ├── dev.md, quick-fix.md         # → dev-workflow (interactive / level-0)
│   ├── auto-dev.md                  # → dev-workflow (autonomous, RALPH)
│   ├── discovery.md, auto-discovery.md  # → discovery-workflow
│   ├── ship.md                      # → ship-workflow
│   ├── gate.md                      # → quality-gate (standalone)
│   ├── elicit.md                    # → elicitation
│   └── ...
├── skills/                          # Canonical skills (single source of truth)
│   ├── dev-workflow/                # The adaptive engine (levels 0-4, 3 modes)
│   ├── discovery-workflow/          # Planning in levels + spec output
│   ├── ship-workflow/               # Gate consumption → PR
│   ├── project-probe/               # Verification manifest
│   ├── quality-gate/                # Quality loop → gate file
│   ├── thermo-nuclear-code-quality-review/ # Strict maintainability review lens
│   ├── elicitation/                 # 12 reasoning lenses
│   ├── multi-mind/                  # 6-AI debate + Contrarian
│   ├── rodin/                       # Socratic anti-echo challenger
│   ├── web-navigator/               # Browser navigation + evidence layer
│   ├── design-audit/, seo-geo-audit/# Squad audits
│   ├── figma-*/                     # Figma integration (8 skills)
│   ├── elevenlabs/, remotion/       # Audio & video
│   └── ...
├── knowledge/                       # 55+ files
│   ├── testing/                     # 32 files (levels, priorities, fixtures...)
│   ├── workflows/                   # templates, verification matrix, estimation
│   ├── brainstorming/               # 61 techniques + 12 elicitation lenses (CSV)
│   ├── multi-mind/                  # Agent personalities (incl. Contrarian), debate templates
│   └── supabase-security/           # 7 audit files
└── templates/                       # CI/CD, PR/issue, git hooks, devcontainer

docs/                                # Generated output
├── planning/                        # brainstorms/, prd/, architecture/, specs/, forge/
├── quality/                         # GATE-*.yaml (gate files)
├── stories/                         # EPIC-{num}-{slug}/
├── debates/                         # Multi-Mind reports
└── ralph-logs/                      # RALPH session logs

.agents/, .codex/, .gemini/, .opencode/  # Multi-agent compatibility (symlinks + native launchers)
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

55+ files across testing, workflows, brainstorming (techniques + elicitation lenses), multi-mind, and supabase-security. Figma references are bundled inside skills.

</details>

---

## Contributing

This project is shared **read-only**. Pull Requests and Issues are not accepted.

You are free to use, copy, and adapt this workflow for your own projects.

---

## Credits

- **[BMAD-METHOD](https://github.com/bmadcode/BMAD-METHOD)** — 32 knowledge files + agent structure; the v6 gate files, scale-adaptive levels, elicitation lenses and anti-consensus room are inspired by BMAD Method v6
- **[RALPH Protocol](https://ghuntley.com/ralph/)** — Autonomous loop mode
- **[Benjamin Debon's Rodin prompt](https://gist.github.com/bdebon/e22d0b728abc5f393227440907b334cf)** — anti-echo Socratic challenge posture adapted as the `rodin` skill
- **[alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)** — LLM Wiki foundation (MIT), see [ATTRIBUTION](./skills/ATTRIBUTION.md)

---

## Version History

See [CHANGELOG.md](./CHANGELOG.md) for the full version history.
