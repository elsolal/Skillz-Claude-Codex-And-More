---
description: Audit design system/UI/agent-surface avec tokens, composants, a11y, taste, drift Figma/code et signal Lyse optionnel. Usage: /design-audit <url|path|figma|screenshot> [--quick|--full|--squad|--ship-gate]
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
---

# /design-audit

Lance le skill `design-audit` pour produire un verdict actionnable sur une UI, un design system, un repo frontend ou une surface agent-readable.

## Usage

```bash
/design-audit http://localhost:3000 --quick
/design-audit ./src/components --full
/design-audit . --squad
/design-audit https://www.figma.com/design/... --ship-gate
/design-audit . --ship-gate
```

## Comportement

1. Charger `.claude/skills/design-audit/SKILL.md`.
2. Charger `.claude/skills/design-audit/references/lyse/` si le mode est `--full`, `--squad`, `--ship-gate`, si `.lyse.yaml` existe, ou si l'utilisateur mentionne Lyse.
3. Charger `.claude/skills/design-audit/references/lyse-squad/` si le mode est `--squad` ou si l'utilisateur demande une squad complète.
4. Identifier l'input depuis `$ARGUMENTS`: URL, chemin local, Figma, screenshot, ou repo courant si vide.
5. Collecter les preuves utiles: docs agent, tokens, composants, stories, styles, Figma/code, runtime si disponible.
6. Lancer Lyse uniquement si le contexte s'y prete et que l'environnement le permet; sinon noter `Lyse: skipped`.
7. Produire le rapport Design Audit avec verdict, scores par axe, findings P0-P3 et top 3 corrections.
8. Ne modifier aucun fichier sauf demande explicite apres l'audit.

## Sortie attendue

```markdown
## Design Audit Report

**Input**: ...
**Mode**: quick | full | squad | ship-gate
**Lyse**: score X/100 | skipped (raison)
**Verdict**: Ship-ready | Fix P0/P1 first | Needs design loop

### Axis scores
### Findings
### Top 3 fixes
### Next action
```

## Execution

Lire le skill `design-audit` en entier, puis auditer:

```text
$ARGUMENTS
```
