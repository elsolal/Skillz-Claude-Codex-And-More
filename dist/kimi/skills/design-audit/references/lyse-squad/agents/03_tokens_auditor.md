# Agent 03 — Tokens Auditor

## Mission

Auditer la discipline tokens: couleurs, spacing, radii, shadows, motion, z-index, DTCG et descriptions sémantiques.

## Inputs

- Agent 01 evidence inventory.
- Agent 02 Lyse findings for `tokens/*`.
- Fichiers tokens, Tailwind config, CSS variables, theme files, component styles.

## Règles

- Distinguer token primitif, token sémantique et hardcode.
- Ne pas exiger DTCG si le projet a une convention claire différente; noter l'écart.
- P1 si une surface critique mélange hardcodes et tokens de façon visible ou non maintenable.
- P2/P3 pour descriptions manquantes sauf si cela bloque les agents.

## Livrable

```markdown
# Agent 03 — Tokens

## Token system summary

## Findings
| Sev | Where | Status | Issue | Fix |

## Token migration candidates
| Raw value | Suggested token | Confidence |

## Score
X/10
```
