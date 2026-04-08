# Changelog

All notable changes to the D-EPCT+R Workflow are documented in this file.

## v5.5.0 (2026-04-08)

**Codex-Native Workflow Prompts (the Real Ones)**

### Why
v5.4.0 blindly symlinked `~/.claude/commands/*.md` into `~/.codex/prompts/`. This looked fine structurally but didn't actually work in Codex CLI for three reasons:
1. Codex doesn't substitute `$ARGUMENTS` — it reads it as literal text (17/21 Claude commands use `$ARGUMENTS`)
2. Codex lacks the Claude-specific tools that the commands invoke (`SendMessage`, `TaskCreate`, `Task` with `subagent_type`)
3. The D-EPCT+R parallel subagent pattern (Code+Tests in parallel, Review ×3 in parallel) doesn't fit Codex's single-threaded execution model

### New: shared `*-workflow` skills
5 runtime-agnostic workflow skills added to `.claude/skills/`:
- `dev-workflow` — Explore → Plan → Implement → Review ×3 (sequential) → Ship, with STOP CHECKPOINTs
- `discovery-workflow` — Brainstorm → UX → PRD → UI → Architecture → Stories → GitHub
- `ship-workflow` — merge main → tests → pre-landing review → CHANGELOG → commit → push → PR (non-interactive)
- `quick-fix-workflow` — fast track for small bugs with max 3 files / 50 lines limit
- `status-workflow` — read-only project dashboard

These skills describe the workflows in single-threaded sequential form. The rigor of D-EPCT+R is preserved (stop checkpoints, 3-pass review) — only the execution pattern changes from parallel subagents to sequential in-context phases. They work in both Claude Code and Codex CLI.

### New: Codex-native prompts in `.codex/prompts/`
5 short BMad-style trigger prompts added to the repo at `.codex/prompts/`:
- `dev.md` → loads `dev-workflow` skill
- `discovery.md` → loads `discovery-workflow` skill
- `ship.md` → loads `ship-workflow` skill
- `quick-fix.md` → loads `quick-fix-workflow` skill
- `status.md` → loads `status-workflow` skill

Each prompt is ~10 lines, frontmatter-compliant with `disable-model-invocation: true`, and points the agent to the shared workflow skill. Pattern inspired by the BMad prompts shipped with Codex.

### install.sh changes
- **Removed**: the broken `~/.claude/commands → ~/.codex/prompts` symlink logic from v5.4.0
- **Added**: copy of `.codex/prompts/*.md` from the repo source to `~/.codex/prompts/` (real files, not symlinks — survives repo removal)
- **Preserved**: existing third-party prompts (BMad) are never overwritten — the copy only replaces symlinks or identical files
- **Preserved**: 21 broken symlinks from v5.4.0 are swept automatically by the dead-link sweep added in v5.4.0

### What works now in Codex
| Command | Status |
|---|---|
| `/dev <task>` | ✅ Works via dev-workflow skill |
| `/discovery <idea>` | ✅ Works via discovery-workflow skill |
| `/ship` | ✅ Works via ship-workflow skill |
| `/quick-fix "<problem>"` | ✅ Works via quick-fix-workflow skill |
| `/status` | ✅ Works via status-workflow skill |
| `/refactor`, `/pr-review`, `/retro`, etc. | ⏭️ Claude Code only (not yet adapted) |
| `/auto-dev`, `/auto-discovery`, `/auto-loop` | ⏭️ Claude Code only (RALPH is Claude-specific) |

### Maintenance note
Claude commands (`~/.claude/commands/*.md`) and Codex prompts (`.codex/prompts/*.md`) are now **two separate sets** that both delegate to the same `*-workflow` skills for their procedural content. When you change the workflow, edit the skill once. When you change the trigger/invocation, edit the relevant command or prompt.

### Files changed
- New: `.claude/skills/dev-workflow/`, `discovery-workflow/`, `ship-workflow/`, `quick-fix-workflow/`, `status-workflow/`
- New: `.codex/prompts/dev.md`, `discovery.md`, `ship.md`, `quick-fix.md`, `status.md`
- Updated: `install.sh` — replaced command symlink block with Codex prompt copy block; updated summary output
- Updated: `README.md`, `CHANGELOG.md`

---

## v5.4.0 (2026-04-08)

**Codex CLI Mirror + Manifest-based Drift Protection**

### New: Codex CLI global install
- `install.sh --global` now also mirrors skills/commands into `~/.codex/` when Codex CLI is detected
- Skills are symlinked individually (`~/.codex/skills/X → ~/.claude/skills/X`) — single source of truth in `~/.claude/`
- Commands mirrored to `~/.codex/prompts/` as symlinks (Codex convention for slash commands)
- `~/.codex/AGENTS.md` generated from `~/.claude/CLAUDE.md` with auto-doc header (edits must go in `CLAUDE.md` and re-run install)
- Native `~/.codex/skills/.system/` folder (OpenAI built-in skills) is preserved — skills are linked alongside, never over
- `--no-codex` flag to skip the Codex mirror if you only want Claude
- Codex MCP servers in `config.toml` are intentionally left untouched — mirror them manually if needed

### Fix: drift protection via manifest
- `~/.claude/.skillz-manifest` tracks skills/commands installed by Skillz
- On each `--global` run, orphaned items (present in previous manifest but not in source) are purged automatically
- User-added skills outside the manifest are never touched — zero risk of collateral damage
- Dead Codex symlinks are swept at the start of every Codex mirror run
- Root cause fixed: previously, removed skills (e.g. the 4 legacy Figma skills from v5.3.0) accumulated in `~/.claude/skills/` after migrations because `rsync` has no `--delete` by default

### Cleanup: remaining `figma-console` references
- Removed the "Figma Console MCP (optional — advanced features)" section from `figma-design-code-sync` — the skill is now 100% aligned with the official Figma MCP (`use_figma` + `get_design_context` + `search_design_system`)
- No skill in the repo references the unofficial `figma-console` MCP anymore

### Files changed
- Updated: `install.sh` — `--no-codex` flag, Codex mirror block, manifest-based purge, dead-link sweep
- Updated: `.claude/skills/figma-design-code-sync/SKILL.md` — removed `figma-console` section
- Updated: `README.md` — documented Codex mirror behavior and drift protection

---

## v5.3.0 (2026-04-02)

**Official Figma Skills + ElevenLabs & Remotion Pipeline**

### Figma skills migration to official figma/mcp-server-guide
- Replaced 4 custom Figma skills with 7 official ones from Figma's own [mcp-server-guide](https://github.com/figma/mcp-server-guide/tree/main/skills):
  - `figma-use` — mandatory prerequisite for all `use_figma` calls (Plugin API rules, gotchas, pre-flight checklist)
  - `figma-implement-design` — Figma to production code with 1:1 visual fidelity (replaces `figma-to-code`)
  - `figma-generate-design` — build/update screens from design system components (replaces `figma-designer`)
  - `figma-generate-library` — build full design systems in Figma: tokens, components, docs (replaces `figma-design-system`)
  - `figma-code-connect` — parserless Code Connect templates (replaces `figma-setup`)
  - `figma-create-design-system-rules` — generate CLAUDE.md/AGENTS.md rules for Figma-to-code workflows (new)
  - `figma-create-new-file` — create new Figma files via MCP (new)
- Kept `figma-design-code-sync` (custom, no official equivalent)
- Downloaded 30+ reference files (gotchas, patterns, API reference, variable patterns, etc.) and 9 helper scripts
- Downloaded full Plugin API typings (`plugin-api-standalone.d.ts`, 450KB) for grep-based type lookup
- Removed legacy `knowledge/figma/` directory (3 files superseded by skill references)

### New skills: ElevenLabs + Remotion
- `elevenlabs` — comprehensive voice AI skill covering TTS (API + CLI), music generation, sound effects, batch pipeline, voice settings. Includes 3 reference files.
- `remotion` — React video creation with 40 official rule files from remotion-dev/skills (animations, audio, captions, charts, 3D, FFmpeg, transitions, text animations, etc.) + cloud rendering via inference.sh + full ElevenLabs→Remotion voiceover pipeline

### Pipeline enabled
```
Script → ElevenLabs API → Audio files → Remotion → Video
```

### Files changed
- New: 8 Figma skill directories with SKILL.md + references/ + scripts/
- New: `.claude/skills/elevenlabs/` (SKILL.md + 3 references)
- New: `.claude/skills/remotion/` (SKILL.md + 40 rules + 3 TSX assets)
- Removed: `figma-designer/`, `figma-to-code/`, `figma-design-system/`, `figma-setup/`, `knowledge/figma/`
- Updated: `install.sh` (skill count 22→28, new skill listings)
- Updated: `README.md`, `CHANGELOG.md`

---

## v5.2.0 (2026-03-19)

**Design System Documenter + Frontend-Aware Dev Workflow**

### New skill: `ds-doc`
- Scans project for tokens (tailwind.config, globals.css), UI components (shadcn), and business components
- Asks for Figma file URL(s) upfront to link every component to its Figma counterpart
- Generates two files:
  - `CLAUDE.md` (root) — concise index with tables (tokens, components, patterns, rules)
  - `src/components/CLAUDE.md` — detailed reference (props, variants, CSS values, Figma variable links, missing components list)
- `--update` mode merges new components without overwriting manual Figma links
- Detects components present in Figma but not yet in code ("Composants manquants" section)
- Idempotent: re-running updates the section without duplicating

### Frontend detection in `/dev` and `/auto-dev`
- New **Phase 1.5: Frontend Detection** — automatically detects frontend work after the explore phase
- Detection signals: Figma URL in issue, `.tsx/.jsx/.css` files, `components/CLAUDE.md` presence, shadcn `components.json`
- When frontend detected: plan includes component reuse, token usage, Figma mapping
- Code agent receives DS-aware instructions (reuse components, never hardcode colors/spacing)
- Phase 5 proposes `/ds-doc --update` when new components were created (auto-runs in RALPH mode)

### Files changed
- New: `.claude/skills/ds-doc/SKILL.md`
- Updated: `.claude/commands/dev.md` — Phase 1.5 + frontend-aware plan/implement/ship
- Updated: `.claude/commands/auto-dev.md` — same frontend detection for RALPH mode
- Updated: `CLAUDE.md` — added `/ds-doc` to workflow routing and commands
- Updated: `README.md` — skills count 21→22, new command and skill listed

---

## v5.1.0 (2026-03-14)

**Orchestrator Architecture — Context Preservation**

With 1M token context windows, Plan Mode resets and `context: fork` isolation between phases are no longer necessary. This version replaces the fragmented approach with a persistent orchestrator pattern.

### Discovery workflow
- Orchestrator keeps full context across all phases (Brainstorm → PRD → Architecture → Stories)
- No more `context: fork` or `agent: Plan` on discovery-chain skills (brainstorm, pm-prd, architect, pm-stories, ux-designer, ui-designer)
- Only GitHub issue creation dispatched to subagent (mechanical work)
- Skills remain usable standalone with the same process

### Dev workflow
- Plan Mode (`EnterPlanMode`) removed — orchestrator plans directly with full exploration context
- Explore phase stays in main thread (context preserved)
- Implementation: 2 subagents in parallel (Code + Tests) via `SendMessage`
- Review: 3 subagents in parallel (Correctness + Readability + Performance) via `SendMessage`
- Orchestrator corrects Critical issues itself (has full context)

### PR Review
- 3 parallel subagents via `SendMessage` (Correctness, Readability, Performance)
- Consolidated report with severity classification

### Files changed
- `discovery.md`, `auto-discovery.md` — rewritten as orchestrator
- `dev.md`, `auto-dev.md` — rewritten as orchestrator + subagents
- `pr-review.md` — rewritten with subagent pattern
- 6 skills updated: removed `context: fork` and `agent: Plan`
- `CLAUDE.md`, `WORKFLOW.md`, `README.md` — documentation aligned

---

## v5.0.0

**New Commands & Rename (inspired by gstack)**

- `/feature` → `/dev` : renamed to avoid conflicts
- `/auto-feature` → `/auto-dev` : same rename for RALPH mode
- `/ship` : automated ship workflow (merge → tests → review → changelog → PR)
- `/qa` : systematic QA testing with health score (full/quick/regression)
- `/plan-review` : CEO/Founder review in 3 modes (Expansion/Hold/Reduction)
- `/retro` : engineering retrospective (sessions, streaks, trends)
- Review checklist externalized to `.claude/knowledge/review-checklist.md`

---

## v4.0.0

**Multi-Agent Architecture**

- `/dev` (ex-`/feature`) : multi-agent orchestrator (Explore → Plan → Code+Tests // → Review ×3 //)
- `/auto-dev` (ex-`/auto-feature`) : same workflow in RALPH autonomous mode
- `/pr-review` rewritten: 3 parallel review agents
- `code-implementer` slimmed (336→100 lines): agent worker without orchestration
- `test-runner` slimmed (376→170 lines): agent worker, 9 knowledge refs preserved
- `code-reviewer` restructured (287→150 lines): 3 self-contained passes, parallel-ready
- Removed `codebase-explainer` (replaced by native Agent Explore)
- Removed `implementation-planner` (replaced by main orchestrator)
- 3 new Figma skills: `figma-designer`, `figma-design-system`, `figma-design-code-sync`

---

## v3.8.0

**Figma Integration**

- New skill `/figma-setup` for Code Connect configuration
- New skill `/figma-to-code` for code generation from Figma
- `/ui-designer` enriched with `--from-figma` option for token import
- 3 knowledge files: code-connect-guide.md, mcp-tools-reference.md, tokens-mapping.md
- MCP Figma support: get_design_context, get_variable_defs, get_code_connect_map
- Automatic Figma Variables → CSS Variables mapping

---

## v3.7.0

**Supabase Security Audit**

- New skill `/supabase-security` for comprehensive Supabase project audit
- 7 phases: Detection, Extraction, API, Storage, Auth, Realtime, Functions
- P0/P1/P2 severity scoring aligned with CVSS
- Evidence collection with reproducible curl commands
- 7 knowledge files: checklist, severity matrix, RLS patterns, remediation templates

**Multi-Agent Compatibility**

- New directories `.agents/`, `.codex/`, `.gemini/`, `.opencode/`
- Symlinks to `.claude/skills/` and `.claude/knowledge/`
- Adapted instructions for each tool (AGENTS.md, GEMINI.md)
- Single source of truth: `.claude/`

---

## v3.6.0

**Brainstorming Enhanced (BMAD-inspired)**

- **61 techniques** in **10 categories** (collaborative, creative, deep, introspective, structured, theatrical, wild, biomimetic, quantum, cultural)
- **4 session approaches**: User-Selected, AI-Recommended, Random Discovery, Progressive Flow
- **Anti-Bias Protocol**: Domain pivot every 10 ideas to avoid semantic clustering
- **Energy Checkpoints**: Every 4-5 exchanges to maintain momentum
- **Quantity objective**: Aim for 50-100+ ideas before organizing

---

## v3.5.0

**Multi-Mind v3.5 — Iterative Debate**

- **5 rounds** instead of 4: new "Frictions" round + ping-pong debate
- Round 2: Friction identification (major disagreements)
- Round 3: Targeted iterative debate (max 3 turns per friction)
- Resolution: RESOLVED or DIVERGENCE MAINTAINED
- macOS compatibility, strict anti-substitution rules, retry logic

---

## v3.4.0

**Multi-Mind Debate System (initial)**

- New `multi-mind` skill for multi-agent debate
- 6 AIs: Claude, GPT, Gemini, DeepSeek, GLM, Kimi
- 4-round initial workflow
- Integration in pm-prd, code-reviewer, refactor (option [M])
- Reports in `docs/debates/`

---

## v3.3.0

**Task System in /dev**

- `implementation-planner` auto-creates Tasks if 2+ steps
- `code-implementer` updates Tasks (in_progress → completed)
- Dependencies between Tasks for sequencing

---

## v3.2.0

**Task System Integration**

- New Task system (TaskCreate, TaskList, TaskUpdate, TaskGet)
- Replaces obsolete TodoWrite in all skills
- `user-invocable: true` added to all skills
- Standardized frontmatter, `context: fork` added

---

## v3.1.0

**Git Hooks & DevContainer**

- Templates pre-commit and commit-msg (ESLint, TypeScript, Prettier, Secrets, Conventional Commits)
- DevContainer configuration (VS Code, Docker, PostgreSQL, Redis)
- New `performance-auditor` skill (Core Web Vitals, Lighthouse, bundle analysis)

---

## v3.0.0

**Database Designer & Init**

- New `database-designer` skill (ERD, migrations, indexes, Prisma/Drizzle)
- `/init` command with 5 templates (Next.js, Express, API, CLI, Library)
- GitHub issue templates (bug_report, feature_request)

---

## v2.9.0

- New `api-designer` skill (OpenAPI 3.1, REST/GraphQL, versioning)
- `/metrics` command (health score dashboard)
- PR template for GitHub

---

## v2.8.0

- New `security-auditor` skill (OWASP Top 10, CVE, secrets)
- GitHub Actions templates (CI, release, security, deploy, dependabot)
- `/changelog` command

---

## v2.7.0

- Skill chaining (auto-chain after validation)
- Output validation with checklist and minimum score
- RALPH metrics tracking
- `/resume-ralph` command
- Knowledge: prd-patterns.md, estimation-techniques.md, risk-assessment.md

---

## v2.6.0

- Dynamic context injection for all 12 skills
- Auto hooks (lint, coverage, GitHub auth check)
- Claude Opus on all skills
- New commands: `/pr-review`, `/quick-fix`, `/refactor`, `/docs`

---

## v2.5.0

- New UX Designer and UI Designer skills
- Auto-trigger UX/UI from brainstorm and PRD

---

## v2.4.0–v2.4.1

- Research-first in brainstorm
- Implementation Readiness Check (score /15)
- ATDD mode in test-runner

---

## v2.3.0

- Knowledge Base: 35+ files with progressive loading

---

## v2.1.0

- RALPH mode: autonomous loop with stop-hook

---

## v2.0.0

- Planning workflow: Brainstorm → PRD → Architecture → Stories
- FULL / LIGHT auto-detection

---

## v1.0.0

- Initial version with 7 skills
