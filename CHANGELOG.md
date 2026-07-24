# Changelog

All notable changes to the D-EPCT+R Workflow are documented in this file.

## [Unreleased] - 2026-07-24

**Bounded degraded memory context without QMD**

### Added
- Local entry-page context for `minimal` and `project` when QMD is missing, non-executable, timed out, or otherwise unusable, capped at one and three manifest-declared pages respectively.
- Explicit degraded receipts with `source: entry_pages`, page and token limits, relative-path warnings, `retrieved`/`read` separation, and a copyable QMD repair action.
- Unit, integration, contract, and security coverage for missing/non-executable QMD, primary and transverse retrieval failures, partial entry pages, hard budgets, traversal, and symlink escape.

### Changed
- `historical` now consistently returns `blocked`/`31` for an unusable QMD dependency, including failures on an authorized transverse route.
- A valid empty QMD search remains `insufficient`/`20`; local degradation is reserved for technical unavailability and never scans undeclared pages or downloads a model.
- Local entry pages are represented as `read` sections with no synthetic QMD docid, while any real project hits obtained before a transverse failure remain visible as `retrieved` evidence.

### Fixed
- Authorized fallback search failures now use the same mode-aware degradation policy as primary project-search failures instead of returning exit `40` unconditionally.
- Project hits are no longer discarded when the transverse QMD route fails and bounded local pages provide the final context.

### Validation
- `bash -n install.sh scripts/*.sh .claude/scripts/health-check.sh .claude/skills/llm-wiki/bin/memory tests/*.sh`
- `bash tests/test-install-memory-cli.sh && python3 -m unittest discover -s .claude/skills/llm-wiki/tests -p 'test_*.py'` — installer PASS, 90 tests Python OK on Python 3.12.7
- Level-2 quality gate: `WAIVED` only for the convergence-round limit; all executable evidence is green and no P0/P1 finding remains

## [Unreleased] - 2026-07-22

**Budgeted Markdown memory context assembly**

### Added
- Safe, deterministic context assembly that deduplicates QMD hits, resolves documents beneath projected vault roots, extracts the Markdown section around each hit, and stops as soon as the read subset is sufficient.
- Versioned `utf8_bytes_div_4_v1` estimation with the approved `minimal`, `project`, and `historical` target/hard envelopes, paragraph-boundary truncation, explicit partial results, and auditable `--risk-reason` overrides.
- Separate `retrieved` and `read` evidence in human and JSON receipts, including relative paths, line ranges, useful frontmatter, real estimated cost, remaining budget, and metadata-only event projections.
- Unit, contract, integration, and security coverage for Unicode, large paragraphs, all three budget profiles, early stopping, fallback roots, traversal, symlink escape, heading hits, and hard-cap behavior.

### Changed
- Portable memory CLI runtime version advanced to `0.7.0`.
- Local projection V1 keeps `project` mandatory and accepts optional roots keyed by manifest-declared fallback IDs without granting route authorization.
- `memory context` now materializes sufficient retrieval evidence into bounded sections and exposes `--risk-reason security|data|architecture|product|incident`.

### Fixed
- Heading matches can no longer count only the title as read while bypassing the hard cap of the section's evidence paragraph.
- Vault roots containing `wiki/` now resolve QMD-relative paths under that canonical subtree instead of accepting a same-named decoy elsewhere in the vault.
- Retrieval and assembly share one canonical provenance classifier instead of maintaining pass-through wrappers.

### Validation
- `bash -n install.sh scripts/*.sh .claude/scripts/health-check.sh .claude/skills/llm-wiki/bin/memory tests/*.sh`
- `bash tests/test-install-memory-cli.sh && python3 -m unittest discover -s .claude/skills/llm-wiki/tests -p 'test_*.py'` — installer PASS, 80 tests Python OK
- Level-3 quality gate: PASS after three implementation rounds and two clean release-revalidation rounds, with no remaining P0/P1

## [Unreleased] - 2026-07-18

**Versioned context sufficiency and authorized fallback**

### Added
- Pure `qmd-0.9-v1` sufficiency decisions for `minimal`, `project`, and `historical` retrieval modes, with stable statuses, evidence, thresholds, and deterministic reason codes.
- Project-first fallback orchestration guarded by both the local principal role and the shared manifest task-category policy, without calling or naming denied transverse collections.
- Explicit `memory context --fallback-on-ambiguous` and `--explain` controls, plus unit and subprocess coverage for freshness, provenance, threshold boundaries, ambiguity, denial, and empty fallback behavior.

### Changed
- Portable memory CLI runtime version advanced to `0.6.0`.
- `policy.sufficiency_thresholds_version` is accepted as a backward-compatible optional manifest field and defaults to `qmd-0.9-v1`.
- Project and fallback QMD searches now share their candidate scores with the canonical sufficiency profile, while doctor and context share one 24-hour freshness policy.

### Fixed
- Context receipts keep a `ready` retrieval status whenever aggregate project/fallback hits are present, even if the final fallback collection is empty.
- Initial routes and runtime fallback execution now consume the same authorization helper, preventing role/category policy drift.

### Validation
- `bash -n install.sh scripts/*.sh .claude/scripts/health-check.sh .claude/skills/llm-wiki/bin/memory tests/*.sh`
- `bash tests/test-install-memory-cli.sh && python3 -m unittest discover -s .claude/skills/llm-wiki/tests -p 'test_*.py'` — installer PASS, 65 tests Python OK
- Four-round level-3 quality gate: PASS, five confirmed P1 findings corrected, no remaining P0/P1

## [Unreleased] - 2026-07-18

**Task-first project QMD retrieval**

### Added
- `memory context` with project-first lexical retrieval, explicit task categories, `minimal` / `project` / `historical` modes, positional queries, and privacy-oriented `--query-stdin` input.
- Fixture-backed QMD 0.9.x search normalization for docid, collection, relative path, title, score, snippet line, duration, and distinct `ready` / `empty` / `timeout` / `invalid` / `error` states.
- Unit and subprocess integration coverage for strict JSON, hostile values, shell isolation, query non-persistence, bounded stdin, output limits, exit codes, and project-route ordering.

### Changed
- Portable memory CLI runtime version advanced to `0.5.0`.
- Public context receipts expose retrieval metadata without persisting or rendering raw queries and snippet text; internal `RetrievalHit` values retain snippets for later bounded-context assembly.
- QMD process execution now uses explicit argument arrays with `shell=False`, an eight-second default timeout capped at thirty seconds, and one-MiB stdout/stderr rejection.

### Validation
- `bash -n install.sh scripts/*.sh .claude/scripts/health-check.sh .claude/skills/llm-wiki/bin/memory tests/*.sh`
- `bash tests/test-install-memory-cli.sh && python3 -m unittest discover -s .claude/skills/llm-wiki/tests -p 'test_*.py'` — installer PASS, 53 tests Python OK
- Warm QMD 0.9.0 p95: 514 ms on `elsolal-wiki`, 205 ms on `pleepole-wiki`, below the five-second target.
- Two-round level-2 quality gate: PASS

## [Unreleased] - 2026-07-18

**Local memory activation diagnostics**

### Added
- `memory doctor` with stable human and JSON outputs, `ready` / `degraded` / `blocked` states, prioritized causes, copyable next actions, and distinct exit codes.
- Explicit `--network`, narrowly scoped `--fix`, and non-interactive `--explain` modes without implicit fetch, QMD update, embedding, download, or page mutation.
- Fixture-backed QMD 0.9.x adapter plus contract coverage for manifest, projection, Git ignore, entry pages, collection state, freshness, rendering, side effects, and two-pilot p95 performance.

### Changed
- Portable manifest V1 accepts the backward-compatible optional `golden.start_question`; activation remains valid without it but doctor reports `degraded` until it is supplied.
- Portable memory CLI runtime version advanced to `0.4.0` and onboarding documentation now includes the complete configure-to-doctor flow.

### Fixed
- QMD collections with zero indexed files now degrade to bounded entry-page modes instead of reporting a false ready state.
- Freshness now compares the QMD status age with local entry-page mtimes, detecting pages changed after the last index update.

### Validation
- `bash -n install.sh scripts/*.sh .claude/scripts/health-check.sh .claude/skills/llm-wiki/bin/memory tests/*.sh`
- `bash tests/test-install-memory-cli.sh && python3 -m unittest discover -s .claude/skills/llm-wiki/tests -p 'test_*.py'` — installer PASS, 44 tests Python OK
- Three-round level-2 quality gate: PASS

## [Unreleased] - 2026-07-18

**Local memory projection and managed pointers**

### Added
- `memory configure` with stable human and JSON results, explicit local roles, path redaction and `ready` / `degraded` / `blocked` exit semantics.
- Atomic `.agents/memory.local.json` generation plus managed Claude and generic-agent project-memory pointers.
- Git-local exclusions that keep machine-specific files out of commits in both standard repositories and linked worktrees.
- Contract, integration, security and idempotence tests with versioned `ready` and `degraded` output fixtures.

### Changed
- Portable memory CLI runtime version advanced to `0.3.0`.
- `scripts/create-project-memory-pointer.sh` now acts as a compatibility wrapper around the canonical Python command.
- Root and `llm-wiki` documentation now describe portable-manifest activation, local roles and the historical-wrapper migration.

### Fixed
- Unmanaged pointers are preserved unless replacement is explicitly requested with `--replace-managed`.
- Store, wrapper and manifest errors no longer reveal absolute local paths without `--explain-local-paths`.
- Entry-page symlinks that escape the configured vault root are rejected before any local projection is written.

### Validation
- `bash -n install.sh scripts/*.sh .claude/scripts/health-check.sh .claude/skills/llm-wiki/bin/memory tests/*.sh`
- `bash tests/test-install-memory-cli.sh && python3 -m unittest discover -s .claude/skills/llm-wiki/tests -p 'test_*.py'` — installer PASS, 28 tests Python OK
- Three-round level-2 quality gate: PASS

## [Unreleased] - 2026-07-18

**Portable memory manifest V1**

### Added
- Immutable Python contracts for project, stores, fallbacks, budgets, policy and golden paths.
- Git-root-bounded discovery and strict JSON-compatible YAML parsing for `.agents/memory.yaml`.
- `memory manifest` command with human and stable JSON outputs, exit code `30` and copyable corrections.
- Unit, contract, hostile-input and deterministic performance tests with versioned fixtures.

### Changed
- Portable memory CLI runtime version advanced to `0.2.0`.
- Project verification now includes the Python `unittest` manifest suite alongside installer tests.
- `llm-wiki` documentation now defines the V1 manifest schema and validation workflow.
- Python bytecode caches are ignored across the repository.

### Fixed
- Non-standard JSON constants `NaN`, `Infinity` and `-Infinity` are rejected before semantic validation.

### Validation
- `bash -n install.sh scripts/*.sh .claude/scripts/health-check.sh .claude/skills/llm-wiki/bin/memory tests/*.sh`
- `bash tests/test-install-memory-cli.sh && python3 -m unittest discover -s .claude/skills/llm-wiki/tests -p 'test_*.py'`
- Parse and initial-route benchmark: 0.121 ms p95 over 200 samples, below the 300 ms ceiling.
- Three-round level-2 quality gate: PASS

## [Unreleased] - 2026-07-18

**Collision-safe portable memory CLI**

### Added
- Provider-neutral `skillz-memory` command backed by a minimal Python 3.10+ standard-library runtime.
- Nominal `memory` alias when the command name is free or already managed by Skillz-Claude.
- Isolated Shell acceptance suite covering install, update, collisions, provider mirrors and safe uninstall.

### Changed
- Global installation now tracks `binary:*` ownership, diagnoses `PATH`, runs a version smoke test and preserves third-party commands.
- Claude uninstall removes memory CLI links only while they still target the installed Skillz-Claude runtime.
- Installation documentation now explains both command names, Python requirements and collision behavior.

### Validation
- `bash -n install.sh scripts/*.sh .claude/scripts/health-check.sh .claude/skills/llm-wiki/bin/memory tests/*.sh`
- `bash tests/test-install-memory-cli.sh`
- Two-round level-2 quality gate: PASS

## [Unreleased] - 2026-07-17

**Observable second-brain efficiency discovery**

### Added
- Approved level-4 design for a portable, task-first and observable `memory` CLI built on the existing Obsidian, `llm-wiki` and QMD stack.
- Five implementation epics and 21 INVEST stories, linked to GitHub issues #36 through #61 with complete PRD/NFR traceability.
- Pilot contract for Skillz-Claude and Pleepole-back, including bounded token budgets, metadata-only telemetry, golden questions, holdouts and a composite rollout gate.
- Project verification manifest for the repository's Shell and Markdown surface.
- Quality gate proving the planning contracts, YAML frontmatter, GitHub parent links, shell syntax and secret scan.

### Validation
- `bash -n install.sh scripts/*.sh .claude/scripts/health-check.sh`
- YAML frontmatter parsing across all new planning and story files
- FR-001–FR-032 and complete NFR coverage checks
- Five Epic and 21 Story GitHub mappings, including 21/21 `Part of` relationships
- Two-round level-4 quality gate: PASS

## v5.14.3 (2026-06-17)

**Portable team memory setup**

### Added
- `scripts/create-project-memory-pointer.sh` creates local `.claude/project-memory.md` and `.agents/project-memory.md` files for project repos.
- The helper protects machine-specific pointers through `.git/info/exclude` so collaborators can keep local vault paths without committing them.
- README documents the team-safe memory pointer workflow.

### Changed
- Wiki setup guidance now states that project-memory pointers are machine-specific and should stay ignored by Git.
- `/wiki-ingest` now requires a coverage audit before indexing: raw sections/files must be mapped to wiki pages, weak or missing coverage must be fixed or explicitly skipped, and high-risk sources get targeted QMD retrieval checks.

## v5.14.2 (2026-06-16)

**Obsidian LLM Wiki + QMD MCP hardening**

### Added
- QMD MCP defaults for Claude Code, Codex and OpenCode:
  - `.mcp.json` and `.claude/mcp.json` use `qmd mcp`.
  - `.codex/config.toml` defines `[mcp_servers.qmd]`.
  - `.opencode/opencode.json` defines a local enabled `qmd` MCP.
- `install.sh` now ensures QMD MCP entries without removing existing MCP servers.
- Project installs also create provider-specific QMD MCP config files.
- `raw/session-notes/` is initialized as the only raw-layer write exception for `/wiki-capture-session`.

### Changed
- QMD docs now follow upstream `@tobilu/qmd` install guidance, including Node 22+ for npm installs, and `collection add` / `context add` / `update` / `embed`.
- `/wiki-bootstrap` and setup docs now refresh a named QMD collection instead of referencing the removed `qmd index` flow.
- QMD MCP examples use the plural `collections` parameter to avoid silently unscoped searches.
- `llm-wiki` and `qmd` skill frontmatter is simplified for Codex skill validation.
- Obsidian vault `.gitignore` now excludes `.obsidian/` app state by default.

### Validation
- `bash -n install.sh`
- `bash -n scripts/setup-wiki.sh`
- QMD collection health via `qmd status`
- Skill frontmatter validation for `llm-wiki`, `qmd`, and generated Codex wiki source-command skills

## v5.14.1 (2026-06-11)

**Web Navigator + Playwright CLI guidance for agent runtime evidence**

### Added
- New `web-navigator` skill for natural browser navigation, information extraction and sourced site analysis.
- `web-navigator` supports Playwright CLI first, then Browser/MCP, WebFetch/WebSearch or user-provided captures as fallbacks.
- Evidence model uses `Confirmé / Déduit / Non vérifié` so QA, SEO/GEO, design and research workflows can share the same grounded observations.
- `/qa` now routes browser evidence through `web-navigator`: screenshots, DOM snapshots, console, network, responsive checks and locator discovery.
- Portable `/qa` commands added for Codex, Gemini and OpenCode.
- `test-runner` now uses `web-navigator` before writing E2E tests, then converts critical flows into deterministic Playwright tests.
- `design-audit`, `seo-geo-audit` and `taste-critic` now reference `web-navigator` for URL-based runtime evidence.

### Docs
- README documents `npm install -g @playwright/cli@latest`, `playwright-cli install --skills`, and `playwright-cli --help`.
- `docs/WORKFLOW.md` explains why Playwright matters for QA, product testing and site analysis by AI agents.

---

## v5.14.0 (2026-06-09)

**SEO/GEO Audit Workflow — Roso SEO Squad packaged for Skillz-Claude**

### Why
Skillz-Claude couvrait le planning, le design, la QA, le code, la sécurité et la performance, mais il n'avait pas de workflow dédié pour auditer la visibilité organique d'un site: SEO technique, contenu, SERP, autorité, local SEO, `llms.txt` et visibilité IA.

Le dossier local `/Users/aymeric/Documents/PROJETS/DEV/SEO_Squad` contient un framework Roso SEO Squad beaucoup plus complet: 11 agents, règles anti-hallucination, triple statut `Confirmé / Déduit / Non vérifié`, double-vérification des affirmations négatives, grille GEO et roadmap client-facing.

Cette release package le workflow dans Skillz-Claude: une entrée compacte pour les audits rapides, une commande squad complète pour les 11 agents, et le pack SEO_Squad complet stocké dans les références du skill.

### Added
- **`seo-geo-audit` skill** — audit ponctuel SEO/GEO avec 9 axes: stratégie, homepage/on-page, technique, keywords/intent, concurrents, content SEO/GEO, autorité/local, visibilité IA, cohérence finale.
- **Référence progressive** — `seo-geo-audit/references/seo-squad-framework.md` résume la séquence Roso, les checks déterministes, la grille GEO et les critères ship-gate.
- **Pack complet Roso SEO Squad** — `seo-geo-audit/references/seo-squad/` contient règles communes, master orchestrator, 11 prompts agents et templates.
- **`/seo-geo-audit` Claude command** — audit read-only sur URL, domaine, marque, concurrents ou page publique, avec modes `--quick`, `--full`, `--geo-only`, `--technical`, `--content`, `--ship-gate`.
- **`/seo-geo-squad` Claude command** — orchestration complète 11 agents avec livrables intermédiaires, rapport fusionné et double livrable final.
- **Portable provider triggers**:
  - `.codex/prompts/seo-geo-audit.md`
  - `.codex/prompts/seo-geo-squad.md`
  - `.gemini/commands/seo-geo-audit.toml`
  - `.gemini/commands/seo-geo-squad.toml`
  - `.opencode/commands/seo-geo-audit.md`
  - `.opencode/commands/seo-geo-squad.md`
- `agents/openai.yaml` metadata pour le skill.
- Spec durable: `docs/planning/specs/2026-06-09-seo-geo-audit-workflow-design.md`.

### Changed
- `.claude/CLAUDE.md` route les demandes "audit SEO/GEO", "visibilité IA", `llms.txt`, SERP, GSC, schema et contenu vers `/seo-geo-audit`; les audits complets vont vers `/seo-geo-squad`.
- README, provider docs, plugin manifest et `install.sh` listent `/seo-geo-audit` et `/seo-geo-squad`.
- `docs/WORKFLOW.md` documente la nouvelle phase SEO/GEO pour les sites publics et contenus indexables.

### Workflow
```
Input URL / domaine / marque
  -> configuration + sources disponibles
  -> brief site avec preuves
  -> audit 9 axes SEO/GEO ou orchestration complète 11 agents
  -> triple statut Confirmé / Déduit / Non vérifié
  -> double-check des affirmations négatives
  -> grille visibilité IA si applicable
  -> roadmap 7j / 30j / 90j
  -> tickets /dev ou vérifications manuelles
```

### Validation
- `git diff --check`
- `bash -n install.sh`
- YAML frontmatter parse pour `seo-geo-audit/SKILL.md` et `agents/openai.yaml`
- Gemini command sanity check
- trailing whitespace scan sur les nouveaux fichiers `seo-geo-audit`

---

## v5.13.0 (2026-06-09)

**Design Audit Loop — Lyse-inspired UI/DS ship gate**

### Why
Skillz-Claude avait déjà les briques de design quality : `taste-critic` pour le jugement visuel, `a11y-enforcer` pour WCAG, `figma-design-code-sync` pour le drift, `ds-doc` pour la documentation, et `ai-native-ui` pour les interfaces IA.

Le manque était une **boucle transversale** capable de collecter les preuves design-system avant le plan, de transformer les findings P0/P1 en contraintes de livraison, puis de bloquer `/ship` quand une surface frontend reste incohérente.

L'analyse de `lyse-labs/lyse` a servi d'inspiration pour les audits statiques orientés tokens, composants, accessibilite, stories, agent-surface et AI governance. Lyse reste un outil externe optionnel: aucun code Lyse n'est vendore dans Skillz-Claude, mais des références d'intégration et un helper CLI read-only sont maintenant inclus.

### Added
- **`design-audit` skill** — audit transversal UI/DS/agent-surface en 6 axes: tokens, components, a11y, taste, Figma/code drift, AI surface & governance.
- **Références Lyse** — `design-audit/references/lyse/` documente l'usage CLI/MCP, le catalogue des 28 règles inspectées et le mapping Health Score → P0/P1/P2/P3.
- **Lyse Design Squad** — `design-audit/references/lyse-squad/` ajoute règles communes, master orchestrator et 12 prompts agents dédiés.
- **Helper Lyse read-only** — `design-audit/scripts/run-lyse-audit.sh` lance `@lyse-labs/lyse@0.2.0-alpha.1` en JSON statique, sans prompt ni télémétrie.
- **`/design-audit` Claude command** — audit read-only sur URL, path local, Figma URL ou screenshot, avec modes `--quick`, `--full`, `--ship-gate`.
- **`/design-audit-squad` Claude command** — orchestration complète 12 agents avec livrables intermédiaires, verdict ship-gate et roadmap.
- **Portable provider triggers**:
  - `.codex/prompts/design-audit.md`
  - `.codex/prompts/design-audit-squad.md`
  - `.gemini/commands/design-audit.toml`
  - `.gemini/commands/design-audit-squad.toml`
  - `.opencode/commands/design-audit.md`
  - `.opencode/commands/design-audit-squad.md`
- `agents/openai.yaml` metadata pour le skill.
- Spec durable: `docs/planning/specs/2026-06-09-design-audit-loop-design.md`.

### Changed
- **`/dev`** — detecte le frontend, prepare un audit rapide apres Explore, injecte les P0/P1 dans le plan, puis relance `design-audit --ship-gate` apres review.
- **`/qa`** — ajoute une phase Design Audit et une categorie `Design system` dans le health score.
- **`/ship` + `ship-workflow`** — bloquent les surfaces frontend avec P0/P1 en mode ship-gate.
- **`/pr-review`** — passe de 3 core passes a 6 passes quand l'UI est touchee: Design Audit, Taste, A11y.
- **`/discovery` + `discovery-workflow`** — la phase UI Design definit maintenant les gates `design-audit` attendus avant livraison.
- **`ds-doc`** — documente aussi la surface agent-readable (`AGENTS.md`, `components/CLAUDE.md`, manifests, MCP).
- **`taste-critic`**, **`a11y-enforcer`**, **`figma-design-code-sync`**, **`ai-native-ui`** — savent consommer ou completer un rapport `design-audit`.
- **`skillz-writing-skills`** — rappelle la progressive disclosure et la lisibilite agent-readable des skills.
- Provider docs, README, plugin manifest et `install.sh` listent `/design-audit`.
- Provider docs, README, plugin manifest et `install.sh` listent aussi `/design-audit-squad`.
- Les commandes portables chargent maintenant les références Lyse en `--full`, `--ship-gate`, sur `.lyse.yaml`, ou quand Lyse est mentionné.

### Workflow
```
Discovery UI
  -> gates design-audit definis dans UI spec
  -> /dev Explore detecte frontend
  -> design-audit --quick
  -> Plan integre P0/P1
  -> Implement + tests
  -> Review core x3
  -> design-audit --ship-gate
  -> design-audit-squad si audit complet 12 agents
  -> /qa ajoute Design system au score
  -> /ship bloque P0/P1 frontend
```

### Validation
- `git diff --check`
- `bash -n install.sh`
- YAML frontmatter parse pour `design-audit/SKILL.md` et `agents/openai.yaml`
- Gemini command sanity check
- shell syntax check pour `run-lyse-audit.sh`
- trailing whitespace scan sur les nouveaux fichiers `design-audit`

---

## v5.12.0 (2026-05-22)

**Rodin — Socratic anti-echo challenge layer**

### Why
Skillz-Claude already had structured planning, code review, multi-agent debate, and founder-style `/plan-review`. What was missing was a lightweight, read-only reasoning pass that can challenge an idea, plan, PRD, architecture choice, strategy, or agent answer before execution without launching a full workflow.

Rodin fills that gap: a short critical-thinking layer inspired by Benjamin Debon's public Rodin prompt, adapted for agent work instead of permanent roleplay.

### Added
- **`rodin` skill** — Socratic anti-complacency workflow for testing reasoning quality: thesis framing, steelman, claim classification, strong objections, blind spots, reality tests, and verdict.
- **`/rodin` Claude command** — direct challenge pass for text, local docs, URLs, or the latest visible reasoning in the conversation.
- **Portable provider triggers**:
  - `.codex/prompts/rodin.md`
  - `.gemini/commands/rodin.toml`
  - `.opencode/commands/rodin.md`
- `agents/openai.yaml` metadata for the Rodin skill.

### Changed
- README now documents Rodin in the feature list, commands table, provider availability matrix, skills inventory, and a dedicated usage section.
- `.claude/CLAUDE.md` now routes "challenge ce raisonnement / plan" style requests to `/rodin`.
- Provider compatibility docs (`.codex/AGENTS.md`, `.gemini/GEMINI.md`, `.opencode/AGENTS.md`, `.agents/README.md`) list `/rodin`.
- `install.sh` now installs, displays, and uninstalls the Rodin portable prompt/command alongside existing portable commands.
- `.claude/skills/ATTRIBUTION.md` credits the public Rodin inspiration and documents the adaptation boundary.

### Validation
- `python3 /Users/aymeric/.codex/skills/.system/skill-creator/scripts/quick_validate.py .claude/skills/rodin`
- `bash -n install.sh`
- Gemini command parsed with Python `tomllib`
- `git diff --check`

---

## v5.11.0 (2026-05-13)

**Codex wiki source-command bridge**

### Why
Claude slash commands are not a reliable command-discovery surface for Codex. The wiki workflows existed as Claude commands, but Codex needed provider-native skill triggers so `/wiki-capture-session` and natural-language requests like "capture cette session dans le wiki" load the right workflow after a restart.

### Added
- `install.sh` now generates Codex-only `source-command-wiki-*` skills in `~/.codex/skills/` during `install/update codex`.
- Generated wiki source-command skills cover `/wiki-bootstrap`, `/wiki-init`, `/wiki-ingest`, `/wiki-query`, `/wiki-lint`, `/wiki-log`, and `/wiki-capture-session`.
- `wiki-capture-session.md` is now also documented inside the `llm-wiki` bundle command folder.

### Changed
- Codex provider installs now use a real `skills/` directory with per-skill symlinks plus generated `source-command-*` skills.
- OpenCode remains unchanged and keeps using its native command folder.
- README, Codex AGENTS, generic agents README, and troubleshooting docs now explain the Codex source-command fallback.

### Validation
- `bash -n install.sh`
- `git diff --check`
- Global install/update tested in a temporary `HOME`.
- Per-project `--providers codex` install tested in a temporary project.
- Codex uninstall tested to remove generated source-command skills.

---

## v5.10.0 (2026-04-22)

**Design discipline layer — taste-critic + a11y-enforcer + ai-native-ui + copy paire**

### Why
v5.9.0 a livré la **génération** de bon goût (9 taste-skills + taste-router). Manquait la **détection** : un design peut être généré avec `soft-skill` puis dérivé pendant l'implémentation, sans rien pour le rattraper. Et même un design pixel-perfect tombe à plat avec du copy générique ou bloque les utilisateurs handicapés. Cette release ferme la boucle.

Inspiré de l'arbitrage Codex×Claude qui a priorisé : audit > génération de territoires neufs > copy granulaire.

### Added (5 nouveaux skills)

#### Audit & enforcement
- **`taste-critic`** — Miroir symétrique des 9 taste-skills. Audit en 8 catégories (typography, spacing, hierarchy, motion, color, copy, density, composition) avec sévérité P0-P3, localisation file:line, et fix concret référencé à la règle source. Branché en pass 4 de `/pr-review` et dans `/qa`.
- **`a11y-enforcer`** — Audit WCAG 2.2 AA systématique : contrastes, ARIA, keyboard nav, focus order (incl. WCAG 2.2 nouveaux : Focus Not Obscured 2.4.11, Target Size 2.5.8), forms, semantic HTML. Output structuré séparant auto-fixables et manual review. Compliance score + grade. Risque légal réel (EAA EU 2025, ADA US, AODA Canada).

#### Nouveau territoire design
- **`ai-native-ui`** — Patterns invariants pour interfaces AI : 7 message states (pending/thinking/streaming/done/errored/interrupted/superseded), tool call lifecycle, inline citations, multi-modal composer, reasoning disclosure, permission gates avec memory, streaming UX, error recovery typé. Framework-agnostic, scope serré sur les invariants stables (pas de fashion-driven).

#### Copy granulaire (pas un writer généraliste flou)
- **`landing-copy`** — Hero / value props / social proof / CTA hierarchy / FAQ / pricing copy. Bannit explicitement Discover/Amazing/Leverage/Empower/Solutions. Patterns Julian Shapiro / Stripe / Linear / Cal.com.
- **`product-microcopy`** — Empty states, errors typés (validation/system/permission/rate-limit), tooltips, confirmations destructives (utilise actions concrètes pas OK/Cancel), success toasts, loading states adaptés à la durée, onboarding ≤3 steps. Bannit Oops/Awesome/Just/Sorry-excessif.

### Changed
- **`/pr-review`** — Détection auto du scope UI dans le diff. Si UI changé → ajoute pass 4 (Design via taste-critic) + pass 5 (A11y via a11y-enforcer). 3 passes classiques en code-only, 5 passes en UI-touched.
- **`CLAUDE.md`** — 5 nouvelles routes dans le tableau workflow + section Design enrichie avec catégories distinctes (génération / audit & enforcement).

### Roadmap arbitrée (Codex × Claude consensus)
1. ✅ taste-critic (audit miroir, ROI immédiat sur tous les projets)
2. ✅ a11y-enforcer (compliance + UX réel, plus haut que copy en priorité)
3. ✅ ai-native-ui (territoire stratégique durable, plus que liquid-glass éphémère)
4. ✅ landing-copy + product-microcopy (paire granulaire, pas writer généraliste flou)
5. 🟡 data-viz-tufte (à venir si dashboards récurrents)

**Pas créés (decision)** :
- liquid-glass : trop tendance, mieux comme dial dans `taste-skill` (futur)
- marketing-conversion : à intégrer comme couche de critères dans `ui-designer` ou `landing-copy`
- mobile-native-hig : à reporter tant que pas de mobile natif récurrent

### Workflow combiné
```
Brief produit
  → taste-router (recommande direction + dials)
  → taste-skill / soft-skill / etc. (génère)
  → landing-copy + product-microcopy (en parallèle, copy)
  → ai-native-ui (si AI app)
  → /dev (implémentation)
  → /pr-review (5 passes : Correctness / Readability / Perf / Design / A11y)
  → /qa (regression + design score)
  → /ship (gate si Grade D/F design ou a11y)
```

---

## v5.9.0 (2026-04-22)

**Taste Skills — Anti-slop frontend direction (9 skills + router)**

### Why
Les skills Skillz couvraient bien le **planning** UI/UX (`ui-designer`, `ux-designer`, `ds-doc`, `figma-*`) et l'**implémentation** (`figma-implement-design`, `code-implementer`), mais rien ne portait la **discipline visuelle** au moment où le code est généré : pas de garde-fou contre les défauts génériques de l'AI (6-line wraps, gapless bento grids absents, motion plate, palette safe, etc.). Les `taste-skills` de [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) comblent ce trou avec des règles métriques précises.

### Added
- **9 taste-skills** intégrés depuis `github.com/Leonxlnx/taste-skill` (cf. `.claude/skills/ATTRIBUTION.md`) :
  - `taste-skill` — Default premium all-rounder (3 dials : DESIGN_VARIANCE, MOTION_INTENSITY, VISUAL_DENSITY)
  - `gpt-tasteskill` — Variante stricte pour GPT/Codex (anti-slop renforcé, GSAP)
  - `soft-skill` — Calm, expensive, smooth spring motion
  - `minimalist-skill` — Type Notion/Linear, palette warm monochrome
  - `brutalist-skill` (BETA) — Swiss typography, raw mechanical
  - `images-taste-skill` — Image-first workflow (génère → analyse → code)
  - `redesign-skill` — Audit + upgrade UI existante
  - `output-skill` — Force la complétion, ban des placeholders
  - `stitch-skill` — Workflow Google Stitch (génère un `DESIGN.md` semantic)
- **`taste-router`** — Méta-skill Skillz original qui recommande le bon taste-skill + valeurs des 3 dials selon le brief produit.
- **`.claude/skills/ATTRIBUTION.md`** — Crédit upstream + procédure de mise à jour manuelle.

### Changed
- `ui-designer` — Nouvelle phase **0.5 Direction visuelle** qui propose les 9 taste-skills + 3 dials avant les tokens.
- `pm-prd` — Section **Direction visuelle (taste dials)** dans la phase d'évaluation UX/UI : capture les 3 dials dès le PRD.
- `figma-implement-design` — Skill Boundaries enrichies : recommande d'invoquer un `taste-skill` avant l'implémentation, et `output-skill` quand le scope dépasse 10 composants.
- `CLAUDE.md` — Routes `taste-router` ajoutées dans le tableau "Quel workflow utiliser ?", et liste des 9 skills documentée dans la section Design System.

### How to use
Les 3 dials (1-10) :
- **DESIGN_VARIANCE** — 1=symétrique parfait | 10=chaos artsy
- **MOTION_INTENSITY** — 1=statique | 10=cinématique GSAP
- **VISUAL_DENSITY** — 1=spacieux luxe | 10=dashboard dense

Demander à `taste-router` ce que tu devrais utiliser, ou invoquer directement le skill (depuis n'importe quel agent — Claude, Codex, Gemini, OpenCode).

### Notes
- Les 9 skills upstream sont des copies au format `SKILL.md` standard — tracked dans Skillz, partagés sur tous les providers via `install.sh`.
- Pour pull les changements upstream : `cd /tmp && git clone --depth 1 https://github.com/Leonxlnx/taste-skill.git`, puis `diff -r` et copie sélective.

---

## v5.8.0 (2026-04-15)

**Native Provider Packaging — Claude plugin + Gemini extension + AGENTS.md**

### Why
Until now, Skillz-Claude was only distributable through `install.sh`. This required symlink setup per provider (`~/.gemini/skills -> ~/.claude/skills`, OpenCode skills folders, etc.), which broke when target dirs already existed. Native plugin/extension formats help for providers that support them, but `install.sh` remains the canonical path for full multi-provider setup.

### Added
- `.claude-plugin/plugin.json` — native Claude Code plugin manifest at repo root. Enables `claude --plugin-dir ./Skillz-Claude-Codex-And-More`; Claude Code namespaces plugin commands.
- `.gemini/gemini-extension.json` + `.gemini/GEMINI.md` — native Gemini CLI extension. Enables `gemini --extension-dir ./Skillz-Claude-Codex-And-More/.gemini` with TOML commands from `.gemini/commands/`.
- `AGENTS.md` at repo root — cross-agent context file (OpenCode, Aider, Codex CLI, generic). Canonical discovery point for any `AGENTS.md`-respecting tool.
- Root-level symlinks `skills/`, `commands/`, `hooks/` → `.claude/*` — Claude plugin root without duplicating content.

### Changed
- `install.sh` documented as the **recommended universal installer**. It remains the canonical path for multi-provider global install + per-project install.
- `README.md` restructured: universal install shown first; provider-native modes documented as preview/optional where the provider format is mature enough.
- `/skillz-doctor` OpenCode checks now target `~/.config/opencode` instead of legacy `~/.opencode`.

### Distribution
The repo now supports three install paths simultaneously — users pick what matches their agent :
1. **Universal** : `install.sh install all` (Claude + Codex + Gemini + OpenCode + agents)
2. **Per-project** : `install.sh install .`
3. **Provider-native preview** : `claude --plugin-dir` / `gemini --extension-dir .gemini`; OpenCode uses skills/commands folders, no bundled JS/TS plugin yet.

No runtime dependency on external projects. All manifests hand-written for our structure.

---

## v5.7.0 (2026-04-15)

**Workflow Safety Gates — RALPH protection + verification matrix + skillz-doctor**

### Why
RALPH (`/auto-dev`, `/auto-discovery`) pouvait coder en autonome sans mandat clair, et aucun gate ne forçait la vérification avant de déclarer "DONE". Inspiré de `obra/superpowers` (sans dépendance runtime), on durcit les workflows critiques.

### Added
- `.claude/skills/skillz-writing-skills/` — méta-skill pour créer/modifier des skills cohérents avec D-EPCT+R/RALPH/FR (réécrit, pas importé d'obra)
- `.claude/commands/skillz-doctor.md` — diagnostic install (symlinks providers, manifest drift, RALPH locks, spec frontmatter)
- `.claude/knowledge/workflows/verification-matrix.md` — matrice par workflow (lint/types/tests + checks spécifiques)
- `docs/planning/specs/` — convention `YYYY-MM-DD-<slug>-design.md` avec frontmatter `status: draft|approved` + `approved_by` (ralph rejeté)
- `docs/planning/specs/2026-04-15-workflow-safety-gates-design.md` — première spec en dogfooding

### Changed
- `/auto-dev` : Phase 0 pre-flight gate. Refuse de coder sans issue GitHub OU spec `approved_by != ralph`. Override `--allow-no-spec` documenté pour prototypage.
- `/auto-discovery` : produit en sortie une spec `status: draft, approved_by: ralph` (humain valide ensuite avant `/auto-dev`).
- `/dev` : Phase 5.0 verification gate (lint + types + tests P0/P1) avant SHIP.
- `/quick-fix` : verification minimale (lint + types) explicitée.
- `/ship` : Step 1 abort si working tree dirty.
- `/auto-dev` : Phase 5 verification + check log RALPH cohérent (pas de pattern d'erreur en boucle).

### Inspiration
Inspiré de `obra/superpowers` (skills `verification-before-completion`, `writing-skills`, `brainstorming`). Aucune dépendance runtime — tout réécrit pour notre vocabulaire.

---

## v5.6.0 (2026-04-08)

**CLI Refactor: Subcommand Syntax + Uninstall Support**

### Why
Previous versions conflated everything under `--global` with opt-in/opt-out flags (`--no-codex`, `--update`). This was confusing: one flag did 3 things (install + update + Codex mirror), and there was no way to install Codex alone or to uninstall cleanly. The CLI needed to express action × target explicitly.

### New subcommand interface

```bash
./install.sh <action> <target>

Actions:
  install     Fresh install (prompts if already installed)
  update      Idempotent update (no prompt)
  uninstall   Remove Skillz-managed items (preserves user-added ones)
  help        Show help

Targets:
  claude      ~/.claude/ globally
  codex       ~/.codex/ globally (requires Claude installed first)
  all         Both
  <path>      Per-project (Claude only)
```

Examples:
```bash
./install.sh install all            # Claude + Codex global
./install.sh install claude         # Claude only
./install.sh install codex          # Codex only (requires Claude)
./install.sh install .              # Per-project in current dir
./install.sh update claude          # Refresh Claude
./install.sh uninstall codex        # Remove Codex, keep Claude
./install.sh uninstall all          # Remove everything Skillz installed
```

### New: `install codex` / `update codex` (standalone Codex install)
- Previously, the only way to set up Codex was via `--global` which also re-synced Claude every time
- New behavior: `install codex` checks that `~/.claude/skills/` exists, then runs ONLY the Codex mirror block (skip Claude rsync, skip CLAUDE.md merge, skip manifest purge)
- Internally: sets `CODEX_ONLY=true` which short-circuits the Claude-side section of the global install branch
- Useful when you want to refresh your Codex setup without re-running the Claude install

### New: `uninstall` subcommand
Two new functions in `install.sh`:

- **`uninstall_claude_global`** — reads `~/.claude/.skillz-manifest` and removes ONLY the skills/commands listed there. User-added skills outside the manifest are never touched. Deletes the manifest at the end. Preserves `CLAUDE.md`, `settings.json`, `mcp.json`, knowledge/, templates/, hooks/.
- **`uninstall_codex_global`** — removes symlinks in `~/.codex/skills/` that point to `~/.claude/skills/` (Skillz-managed), removes the 5 Codex-native prompts (dev, discovery, ship, quick-fix, status). Preserves `.system/`, `config.toml`, `AGENTS.md`, and third-party prompts (BMad, etc.).

Neither uninstall function removes anything it didn't install. Safe by design.

### Backwards compatibility
Legacy flags still work with a deprecation warning:

- `--global` → maps to `install all`, prints warning suggesting the new syntax
- `--global --no-codex` → maps to `install claude`
- `--update` → maps to `update <path>`
- `<path>` alone (no subcommand) → maps to `install <path>`

### Safety change
`./install.sh` with no arguments now shows help instead of defaulting to a per-project install in the current directory. This prevents accidental installs when the user runs the script without knowing the syntax.

### Files changed
- Updated: `install.sh` — new subcommand dispatcher (~200 lines added at top), uninstall functions, CODEX_ONLY guard in the global branch, updated header doc. Legacy flag parsing and all existing install logic preserved for backwards compatibility.
- Updated: `README.md` — documented new subcommand syntax with examples
- Updated: `CHANGELOG.md` — this entry

### Test matrix verified
- `./install.sh help` → shows help ✅
- `./install.sh` (no args) → shows help (safer default) ✅
- `./install.sh update all` → same as old `--global`, 48 skills + 5 Codex prompts synced ✅
- `./install.sh update codex` → skips Claude sync, runs Codex mirror only ✅
- Legacy `--global` still works with deprecation warning ✅

---

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
