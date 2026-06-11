# Agent 12 — Final Report & Ship Gate

## Mission

Produire le rapport final client/équipe avec verdict, score par axe, blocants, éléments non vérifiés et décision ship-gate.

## Inputs

- Livrables Agents 01-11.
- Mode demandé: `full`, `squad`, `ship-gate`.

## Règles

- Le verdict final ne peut pas contredire un P0 non résolu.
- En `ship-gate`, P1 bloque sauf acceptation explicite du risque par l'utilisateur.
- Distinguer clairement `Lyse score` et `Skillz verdict`.
- Mentionner les axes N/A et Non vérifiés.

## Livrable

```markdown
# Lyse Design Squad Report — [Target]

## Executive verdict
**Verdict**: Ship-ready | Fix P0/P1 first | Needs design loop
**Lyse**: score/tier | skipped
**Confidence**: Élevé | Moyen | Faible

## Axis scores
| Axis | Score | Evidence | Notes |

## Findings consolidated
| Sev | Axis | Where | Status | Issue | Fix |

## Ship gate
| Gate | Status | Reason |

## Roadmap
### 24-48h
### 7 jours
### 30 jours

## Non vérifié
| Element | Reason | Next check |
```
