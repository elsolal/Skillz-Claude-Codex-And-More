# v6.1 runtime compatibility matrix

Certification labels are evidence levels, not marketing synonyms:

- **C1 — generable:** validated contracts, deterministic build and reviewed golden.
- **C2 — structurally compatible:** native runtime discovery on the pinned version.
- **C3 — certified:** behavioral smoke through the runtime on the pinned version.

Only C3 may be called “supported” without qualification.

| Runtime route | Observed version | Package / artifact route | Evidence | Exact invocation or fallback |
|---|---|---|---|---|
| Claude Code | `2.1.257` | `dist/claude/.claude-plugin/plugin.json`, skills and commands | C1 | `claude --plugin-dir "$PWD/dist/claude"`; `/dev`, `/quick-fix`, or a named skill. Native discovery and behavioral smoke remain pending. |
| Codex CLI | `0.152.0` | Native plugin + marketplace under `dist/codex/` | C2 | `codex plugin marketplace add "$PWD/dist/codex"`, then `codex plugin add skillz-claude@skillz-claude-dev`; invoke `$skillz-claude:dev-workflow`. Flat `prompts/*.md` are diagnostic/legacy fallbacks, not equivalent C2 evidence. |
| OpenCode | `1.18.25` | Flat `dist/opencode/skills/` and `commands/` | C1 | Install the generated bundle with `bin/skillz`; use the runtime's skill/command discovery. No native package is claimed. |
| Generic AGENTS.md convention | none | Flat `dist/agents-generic/skills/` | C1 | Point the reference agent at the generated skills and instructions. Commands, hooks, MCP and subagents are explicitly unsupported. A named reference runner is still required for C2. |
| Kimi model via Codex/OpenCodex | host-dependent | Codex adapter | Codex route C2 | Install the Codex plugin, then choose the Kimi-backed model in that host. Alternate-model behavioral execution is not yet evidence. |
| Kimi Code CLI native | launcher broken locally | `dist/kimi/skills/` only | C1 | Candidate route: `kimi --skills-dir "$PWD/dist/kimi/skills"`, then `/skill:dev-workflow`. Commands and package format are unsupported. |
| Grok Build | not installed | Claude-compatible plugin under `dist/grok/` | C1 | Candidate route: `grok --plugin-dir "$PWD/dist/grok"`; invoke `/dev-workflow` or `/quick-fix` only after native discovery. |
| Gemini CLI | not installed | Native extension under `dist/gemini/` | C1 | Candidate route: `gemini extensions link "$PWD/dist/gemini"`; commands are generated as TOML. Project trust and behavioral loading remain unverified. |

## Alias contract

The catalog's `aliases.default` is the stable semantic name. Provider-specific aliases override it
only when a runtime requires a different legal name. Skills and commands may share a public alias;
their internal catalog ids remain distinct and their artifact types prevent collisions.

| Intent | Claude | Codex native | OpenCode / Grok | Gemini | Kimi / generic |
|---|---|---|---|---|---|
| Develop | `/dev` | `$skillz-claude:dev-workflow` | `/dev` or `dev-workflow` | `/dev` TOML command | `dev-workflow` skill |
| Quick fix | `/quick-fix` | `$skillz-claude:dev-workflow` with level-0 intent; flat `quick-fix.md` is diagnostic | `/quick-fix` | `/quick-fix` TOML command | `dev-workflow` skill |
| Discovery | `/discovery` | `$skillz-claude:discovery-workflow` | `/discovery` | `/discovery` TOML command | `discovery-workflow` skill |
| Ship | `/ship` | `$skillz-claude:ship-workflow` | `/ship` | `/ship` TOML command | `ship-workflow` skill |
| Status | `/status` | `$skillz-claude:status-workflow` | `/status` | `/status` TOML command | `status-workflow` skill |

All other aliases are enumerated in `core/catalog.yaml` and emitted in
`docs/compatibility/catalog-migration-v6.1.json`. Unsupported artifact types appear as
`unsupported` in `dist/build-report.json`; they are never simulated.

## Evidence index

- Codex native C2: `docs/compatibility/codex-plugin-0.152.0.json`
- Full provider golden: `docs/compatibility/golden/v6.1-p0-distribution.json`
- Installer lifecycle: `docs/compatibility/install-lifecycle-v6.1.json`
- Kimi/Grok/Gemini observation: `docs/compatibility/provider-adapters.md`
- RC blockers: `docs/compatibility/release-candidate-v6.1.0-rc.1.json`
