# Agent 05 — Stories & DS Docs Auditor

## Mission

Auditer la documentation utilisable par humains et agents: stories, examples, fixtures, docs design-system et conventions de composants.

## Inputs

- Agent 01 docs inventory.
- Agent 02 Lyse `stories/coverage`.
- Storybook files, MDX, examples, docs DS, `components/CLAUDE.md`, `components/AGENTS.md`.

## Règles

- Ne pas exiger Storybook si une documentation équivalente existe.
- Prioriser les composants critiques: Button, Input, Dialog, Select, Nav, Card, Table, AI components.
- P1 si l'absence de docs rend les agents incapables de produire l'UI sans dérive.

## Livrable

```markdown
# Agent 05 — Stories & DS Docs

## Coverage summary
| Component | Story/example/doc | Status |

## Findings
| Sev | Where | Status | Issue | Fix |

## Missing examples priority
1. ...

## Score
X/10
```
