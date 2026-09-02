# Lyse CLI Runtime

Use Lyse as read-only evidence during `design-audit`. Prefer the local helper script:

```bash
.claude/skills/design-audit/scripts/run-lyse-audit.sh .
```

The helper checks Node >= 22 and runs:

```bash
npx -y @lyse-labs/lyse@0.2.0-alpha.1 audit <target> \
  --format=json \
  --limit=all \
  --static-only \
  --no-telemetry \
  --no-prompt \
  --yes \
  --quiet
```

## Requirements

- Node.js 22 or newer.
- Network access for `npx` unless Lyse is already cached/installed.
- A frontend, design-system or agent-surface repository.
- A non-destructive audit context. Never run `lyse fix` unless the user explicitly asks for fixes and the workflow has a clean git tree gate.

## Useful Lyse commands

| Command | Use inside Skillz-Claude |
|---|---|
| `lyse audit <path> --format=json` | Main read-only evidence source |
| `lyse audit <path> --format=sarif` | CI/security-tab integration, not default chat output |
| `lyse explain <rule-id>` | Deepen a finding when a rule is unclear |
| `lyse agents` | Generate agent-facing repo summary, use only when asked |
| `lyse mcp setup` | Configure Lyse MCP, use only when user asks for MCP setup |
| `lyse fix` | Mutating command; do not run during audit |

## Safe execution rules

- Treat non-zero exit code `1` as an audit result when a threshold is used; without threshold, inspect stderr/stdout before calling it failure.
- Treat exit codes `2` and `64` as execution/config errors.
- If `.lyse.yaml` exists, use it. If not, run with defaults before proposing config.
- Do not run `lyse init` during a read-only audit because it can write `.lyse.yaml` and MCP config.
- Do not run `lyse share` during automated audits because it touches clipboard/history.

## Report `Lyse: skipped` when

- Node is missing or below 22.
- `npx` cannot fetch the package.
- The target is a screenshot, Figma-only input or URL without local code.
- The repo has no relevant frontend/DS/agent files.
- The user asked for a pure visual critique.

Always include the reason, for example:

```markdown
**Lyse**: skipped (Node 20; Lyse requires Node >= 22)
```
