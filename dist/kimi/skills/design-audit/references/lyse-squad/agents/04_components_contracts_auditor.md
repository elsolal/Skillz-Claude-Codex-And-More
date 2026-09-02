# Agent 04 — Components & Contracts Auditor

## Mission

Vérifier que l'UI réutilise les composants du design system avec des contrats stricts et des imports canoniques.

## Inputs

- Agent 01 paths.
- Agent 02 Lyse findings for `components/*` and `naming/*`.
- Exports DS, composants UI, `.d.ts`, Storybook, `components.json`.

## Règles

- Identifier les composants natifs réimplémentés alors qu'un DS existe.
- Vérifier les props de variants: éviter `string`, `any`, booléens flous.
- Vérifier les imports: un module canonique vaut mieux que des chemins profonds incohérents.
- P1 si un composant critique contourne le DS ou expose un contrat instable.

## Livrable

```markdown
# Agent 04 — Components & Contracts

## DS component map
| Native intent | DS component | Evidence |

## Findings
| Sev | Where | Status | Issue | Fix |

## Contract risks
| Component | Risk | Proposed contract |

## Score
X/10
```
