# P0 vertical slice routes

The v6.1 pilot compiles `project-probe`, `quality-gate`, `status-workflow`, `dev-workflow` and
`quick-fix` from the legacy canonical sources without changing their bytes. Native packaging and
command aliases differ by runtime.

| Runtime | Native package | Exact route | Current evidence |
|---|---|---|---|
| Claude Code 2.1.257 | Generated `.claude-plugin/plugin.json` | `claude --plugin-dir "$PWD/dist/claude"`; invoke `/quick-fix` or the named skill | C1 structural parity; native behavioral discovery remains pending |
| Codex CLI 0.152.0 | Generated `.codex-plugin/plugin.json` plus marketplace | `codex plugin marketplace add "$PWD/dist/codex"`, then `codex plugin add skillz-claude@skillz-claude-dev`; invoke `$skillz-claude:dev-workflow` with the fix request | C2 marketplace, install, list, enablement and installed skills |
| OpenCode 1.18.25 | No JS/TS package claimed | Use `dist/opencode/skills/` and `dist/opencode/commands/quick-fix.md` through the flat installer route | C1 structural parity |

Codex does not expose the compiled `prompts/quick-fix.md` as a literal plugin slash command in the
observed native manifest format. The semantic plugin fallback is therefore the namespaced
`dev-workflow` skill. The flat prompt remains a legacy/diagnostic route until the manifest-aware
installer lands; it is not certified at the same level as native skill discovery.

The deterministic evidence file
`docs/compatibility/codex-plugin-0.152.0.json` intentionally records the remaining C3 limitations.
