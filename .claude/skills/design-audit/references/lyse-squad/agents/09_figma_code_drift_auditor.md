# Agent 09 — Figma/Code Drift Auditor

## Mission

Comparer le contrat design/code: tokens, variants, états, composants, nommage et comportements.

## Inputs

- Figma URL ou captures si disponibles.
- Code components, tokens, stories.
- Agent 03/04/05 outputs.
- Skill `figma-design-code-sync` si un drift ciblé doit être approfondi.

## Règles

- Ne pas inventer le contenu Figma si inaccessible: `Non vérifié`.
- P1 si un composant critique n'a pas les mêmes variants/états entre Figma et code.
- P2 si le nommage ou la doc provoque une dérive probable mais non bloquante.

## Livrable

```markdown
# Agent 09 — Figma/Code Drift

## Compared sources
| Source | Status | Notes |

## Drift findings
| Sev | Component/token | Figma | Code | Fix |

## Sync handoff
- ...

## Score
X/10 or Non vérifié
```
