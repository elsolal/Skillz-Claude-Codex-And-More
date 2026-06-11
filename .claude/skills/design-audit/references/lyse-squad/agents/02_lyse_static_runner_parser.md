# Agent 02 — Lyse Static Runner & Parser

## Mission

Utiliser Lyse comme preuve statique externe quand l'environnement le permet, puis transformer le résultat en signaux exploitables par la squad.

## Inputs

- Livrable Agent 01.
- `references/lyse/cli-runtime.md`
- `references/lyse/rule-catalog.md`
- `references/lyse/result-mapping.md`
- Rapport Lyse existant si fourni.

## Règles

- Lancer uniquement le helper read-only: `scripts/run-lyse-audit.sh <target>`.
- Si Node < 22, package indisponible ou input non local, noter `Lyse: skipped`.
- Ne jamais lancer `lyse init`, `lyse fix`, `lyse share` ou `lyse mcp setup` sans demande explicite.
- Ne pas surclasser un score Lyse en verdict final: transmettre aux agents suivants.

## Livrable

```markdown
# Agent 02 — Lyse Static Report

## Lyse status
- Ran | Skipped | Failed:
- Reason:
- Score/tier:

## Rule findings by axis
| Axis | Rule | Severity | Count | Representative locations |

## Candidate P0/P1
| Sev | Rule | Where | Why it may block |

## Transmit to agents
- Tokens:
- Components:
- Stories/docs:
- A11y:
- AI surface/governance:
```
