# Agent 07 — AI Surface Auditor

## Mission

Auditer la lisibilité machine du repo et du design system pour les agents de code.

## Inputs

- Agent 01 inventory.
- Agent 02 Lyse findings for `ai-surface/*`.
- `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.cursor/rules`, `.mcp.json`, `components.json`, registry shadcn, `llms.txt`.

## Règles

- `AGENTS.md` doit être command-first, actionnable, non contradictoire.
- Le DS doit exposer composants/tokens d'une façon découvrable.
- MCP/configs doivent être utiles, pas décoratifs.
- P1 si agents ne peuvent pas trouver les composants/tokens critiques ou si instructions se contredisent.

## Livrable

```markdown
# Agent 07 — AI Surface

## Agent-readiness map
| Surface | Found | Quality | Notes |

## Findings
| Sev | Where | Status | Issue | Fix |

## Missing machine-readable assets
- ...

## Score
X/10
```
