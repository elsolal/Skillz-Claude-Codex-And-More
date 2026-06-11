---
description: Orchestration complète Lyse Design Squad: 12 agents UI/DS/agent-surface, Lyse statique optionnel, taste, a11y, Figma/code, AI governance et ship-gate. Usage: /design-audit-squad <url|path|figma|screenshot> [--step-by-step|--all-at-once|--ship-gate]
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
---

# /design-audit-squad

Lance le skill `design-audit` en mode `--squad` pour exécuter la Lyse Design Squad complète avec 12 agents spécialisés.

## Usage

```bash
/design-audit-squad . --step-by-step
/design-audit-squad http://localhost:3000 --ship-gate
/design-audit-squad https://www.figma.com/design/... --all-at-once
```

## Comportement

1. Charger `.claude/skills/design-audit/SKILL.md`.
2. Charger les références Lyse:
   - `references/lyse/README.md`
   - `references/lyse/cli-runtime.md`
   - `references/lyse/rule-catalog.md`
   - `references/lyse/result-mapping.md`
3. Charger la squad complète:
   - `references/lyse-squad/00_REGLES_COMMUNES.md`
   - `references/lyse-squad/01_MASTER_ORCHESTRATOR.md`
   - tous les prompts `references/lyse-squad/agents/*.md`.
4. Suivre l'ordre exact du master orchestrator:
   1. Scope & Evidence Collector
   2. Lyse Static Runner & Parser
   3. Tokens Auditor
   4. Components & Contracts Auditor
   5. Stories & DS Docs Auditor
   6. Accessibility Auditor
   7. AI Surface Auditor
   8. AI Governance Auditor
   9. Figma/Code Drift Auditor
   10. Taste & Runtime UI Auditor
   11. Remediation Planner
   12. Final Report & Ship Gate
5. Lancer Lyse uniquement via le helper read-only si le runtime le permet; sinon noter `Lyse: skipped`.
6. Créer les livrables dans `audit-livrables/<nom>/` si le contexte autorise l'écriture; sinon les produire dans la réponse.
7. Ne pas modifier le site audité, le repo audité, ni lancer `lyse fix` pendant l'audit.

## Sortie attendue

- 12 livrables agents.
- Rapport final consolidé.
- Verdict `Ship-ready | Fix P0/P1 first | Needs design loop`.
- Roadmap 24-48h / 7 jours / 30 jours.
- Liste des éléments `Non vérifié`.

## Execution

Lire le skill `design-audit`, charger `references/lyse/` et `references/lyse-squad/`, puis auditer en mode `--squad`:

```text
$ARGUMENTS
```
