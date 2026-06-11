# Lyse Rule Catalog

Current inspected package: `@lyse-labs/lyse@0.2.0-alpha.1`.

Lyse exposes 28 static rule IDs across six practical axes. Rule IDs are stable integration handles; the rule implementation stays in the external Lyse package.

## Tokens

| Rule ID | Default | Design-audit meaning |
|---|---|---|
| `tokens/no-hardcoded-color` | warning | Raw color values bypass the design token layer |
| `tokens/no-hardcoded-spacing` | warning | Off-scale spacing values create rhythm drift |
| `tokens/dtcg-conformance` | warning | Token JSON does not satisfy DTCG-style shape expectations |
| `tokens/description-coverage` | info | Semantic tokens lack useful descriptions for humans/agents |

## Components

| Rule ID | Default | Design-audit meaning |
|---|---|---|
| `components/no-native-shadows` | warning | Native HTML is used where a DS component should be used |
| `components/contracts-strictness` | warning | Component props/types are too loose or not shipped clearly |
| `naming/component-pascalcase` | warning | Component exports are not predictably PascalCase |
| `naming/hook-prefix` | warning | Custom hooks are not named with the expected `useX` pattern |

## Accessibility

| Rule ID | Default | Design-audit meaning |
|---|---|---|
| `a11y/essentials` | warning | JSX accessibility essentials need attention |

## Stories and Documentation

| Rule ID | Default | Design-audit meaning |
|---|---|---|
| `stories/coverage` | warning | DS components lack Storybook or equivalent usage examples |

## AI Surface

| Rule ID | Default | Design-audit meaning |
|---|---|---|
| `ai-surface/agents-md-quality` | warning | Agent instructions are not command-first/actionable enough |
| `ai-surface/component-manifest-json` | info | Component manifest is missing or not machine-readable |
| `ai-surface/ds-index-exported` | warning | DS package does not expose a clear index entry |
| `ai-surface/mcp-config-present` | warning | Repo does not expose MCP configuration where useful |
| `ai-surface/llms-txt-structure` | warning | `llms.txt` exists but is not structured for agents |
| `ai-surface/shadcn-registry-valid` | warning | shadcn-style registry is absent or invalid |
| `ai-surface/agent-instruction-files` | warning | Cursor/Claude/agent instruction files are missing or malformed |

## AI Governance

| Rule ID | Default | Design-audit meaning |
|---|---|---|
| `ai-governance/ai-tokens-reserved` | info | Reserved AI marker tokens should be inventoried |
| `ai-governance/ai-marker-component-present` | warning | DS lacks a visible marker for AI-generated/AI-assisted output |
| `ai-governance/explainability-affordance` | warning | AI UI lacks an explanation affordance |
| `ai-governance/ai-token-requires-marker` | error | AI token usage appears without co-located AI marker |
| `ai-governance/ai-loading-error-states` | warning | AI loading and error states are not explicit enough |
| `ai-governance/human-control-affordances` | warning | User cannot clearly edit, stop, retry, dismiss or override AI output |
| `ai-governance/ai-marker-anti-patterns` | warning | AI marker is hidden, ambiguous or misused |
| `ai-governance/ai-content-live-region` | warning | Streaming/generated output lacks live-region semantics |
| `ai-governance/disclaimer-present` | warning | AI-generated output lacks appropriate user-facing disclaimer |
| `ai-governance/feedback-control-present` | warning | AI output lacks feedback controls |
| `ai-governance/value-gate-doc-present` | warning | AI surface exists without a documented value/necessity gate |

## How to use this catalog

- Convert Lyse `error` findings to at least P1; upgrade to P0 when the issue blocks user action, breaks accessibility, or creates misleading AI behavior.
- Convert repeated `warning` findings on the same axis to P1 in `--ship-gate`.
- Treat `info` as P2/P3 unless it reveals missing agent-critical docs or token semantics.
- If Lyse marks an axis N/A, do not penalize it; explain why it is not applicable.
