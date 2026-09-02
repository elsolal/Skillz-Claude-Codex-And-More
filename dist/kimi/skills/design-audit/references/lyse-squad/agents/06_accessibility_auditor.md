# Agent 06 — Accessibility Auditor

## Mission

Auditer les risques d'accessibilité structurels et, si possible, runtime.

## Inputs

- Agent 02 Lyse `a11y/essentials`.
- Fichiers UI, composants interactifs, pages publiques.
- Browser/Playwright/screenshot si disponible.
- Skill `a11y-enforcer` si P0/P1 probable.

## Règles

- P0 pour action impossible au clavier, focus piégé, label absent sur contrôle critique ou contenu inaccessible.
- P1 pour labels/roles/alt/focus/réduced-motion insuffisants sur flows importants.
- Signaler les limites: Lyse ne remplace pas un audit WCAG complet avec contraste runtime.

## Livrable

```markdown
# Agent 06 — Accessibility

## Checks performed
| Check | Tool/source | Status |

## Findings
| Sev | Where | Status | Issue | Fix |

## Delegate to a11y-enforcer
- Yes/No:
- Why:

## Score
X/10
```
