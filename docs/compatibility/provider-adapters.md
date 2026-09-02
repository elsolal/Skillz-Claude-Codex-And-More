# Provider adapter routes

This matrix distinguishes the model, the runtime host and the generated adapter. A model name does
not select a filesystem or command contract by itself. In particular, Kimi used through a Codex or
OpenCodex host consumes the **Codex adapter**; only the standalone `kimi` executable consumes the
**Kimi adapter**.

| Route | Generated bundle | Exact structural route | Current certification |
|---|---|---|---|
| Kimi model via Codex/OpenCodex | `dist/codex/` | Install the Codex plugin, then select the Kimi-backed model in that host | Codex C2 discovery; alternate-model behavioral execution is not run |
| Kimi Code CLI native | `dist/kimi/skills/` | `kimi --skills-dir "$PWD/dist/kimi/skills"` then `/skill:dev-workflow` | C1 only; local launcher is broken because its Python interpreter is missing |
| Grok Build | `dist/grok/` | `grok --plugin-dir "$PWD/dist/grok" inspect`; invoke `/dev-workflow` or `/quick-fix` after discovery | C1 only; `grok` is not installed locally |
| Gemini CLI | `dist/gemini/` | `gemini extensions link "$PWD/dist/gemini"`; restart, then invoke `/quick-fix` | C1 only; `gemini` is not installed locally |

## Capability boundaries

- Kimi emits skills only. Its runtime exposes skills through `SKILL.md`, `.kimi/skills`, shared
  `.agents/skills`, and `--skills-dir`; Skillz does not invent a separate command or package layer.
- Grok emits a Claude-compatible plugin because the official runtime documents plugin skills,
  commands and `--plugin-dir`. Agents, MCP and hooks remain `pending` until a pinned local runtime
  discovers those Skillz artifacts.
- Gemini emits a native `gemini-extension.json`, `GEMINI.md`, skills and TOML commands. The compiler
  performs one pure syntax transform: Markdown command frontmatter becomes TOML metadata and
  `$ARGUMENTS` becomes Gemini's `{{args}}` placeholder.
- None of these adapters is called "supported" without qualification. C1 means the bundle is
  deterministic and structurally reviewable; C2 requires native discovery; C3 requires a
  behavioral smoke on a pinned runtime.

## Evidence sources and local observation

The contracts were checked against the official runtime documentation on 2026-09-02:

- [Kimi Code CLI Agent Skills](https://github.com/MoonshotAI/kimi-cli/blob/main/docs/en/customization/skills.md)
- [Grok Build skills, plugins and marketplaces](https://docs.x.ai/build/features/skills-plugins-marketplaces)
- [Gemini CLI extension reference](https://geminicli.com/docs/extensions/reference/)
- [Gemini CLI custom commands](https://geminicli.com/docs/cli/custom-commands/)

Local observation is deliberately narrower: `kimi --version` fails before startup, while `grok`
and `gemini` are absent from `PATH`. No installer, authentication flow or provider configuration was
started as part of this structural adapter lot.
