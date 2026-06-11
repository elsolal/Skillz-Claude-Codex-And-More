---
title: Design Audit Loop
status: approved
approved_by: human
approved_at: 2026-06-09T19:15:20Z
slug: design-audit-loop
related_pr: TBD
---

# Design Audit Loop

## Why

Skillz-Claude avait des skills design puissants mais fragmentes:

- `taste-critic` voyait le slop visuel.
- `a11y-enforcer` voyait les risques WCAG.
- `figma-design-code-sync` voyait le drift composant par composant.
- `ds-doc` documentait le design system.
- `ai-native-ui` couvrait les invariants d'interface IA.

Ce qui manquait etait une boucle commune capable de dire, avant ship: "cette surface UI respecte-t-elle les contrats design-system, accessibilite, Figma/code et agent-readable ?"

## Inspiration Lyse

`lyse-labs/lyse` apporte un angle utile: audit statique des repos UI/DS avec axes tokens, components, accessibility, stories, AI surface et governance.

Decision d'integration:

- Ne pas copier de code Lyse.
- Ne pas vendor le package.
- Ajouter des références d'intégration Lyse dans `design-audit/references/lyse/`.
- Ajouter une squad multi-agents dans `design-audit/references/lyse-squad/`.
- Ajouter un helper read-only `scripts/run-lyse-audit.sh` pour lancer le CLI avec garde-fous.
- Appeler `@lyse-labs/lyse` seulement comme preuve optionnelle quand l'environnement le permet.
- Re-ecrire les regles dans le vocabulaire Skillz-Claude: D-EPCT+R, P0/P1/P2/P3, gates `/dev`, `/qa`, `/ship`, `/pr-review`.

## Scope

### Added

- Nouveau skill `.claude/skills/design-audit/SKILL.md`.
- Références `.claude/skills/design-audit/references/lyse/`:
  - `README.md`
  - `cli-runtime.md`
  - `rule-catalog.md`
  - `result-mapping.md`
- Helper `.claude/skills/design-audit/scripts/run-lyse-audit.sh`.
- Pack `.claude/skills/design-audit/references/lyse-squad/` avec règles communes, master orchestrator et 12 prompts agents.
- Nouvelle commande `.claude/commands/design-audit.md`.
- Nouvelle commande `.claude/commands/design-audit-squad.md`.
- Prompts portables Codex, Gemini et OpenCode.
- Metadata OpenAI `agents/openai.yaml`.

### Updated

- `.claude/CLAUDE.md` route les demandes d'audit UI/DS vers `/design-audit` ou `/design-audit-squad` selon la profondeur.
- `/dev` lance un audit rapide au cadrage frontend puis un ship-gate apres review.
- `/qa` ajoute une phase Design Audit et une categorie Design system.
- `/ship` et `ship-workflow` bloquent les P0/P1 frontend.
- `/pr-review` ajoute une passe Design Audit avant Taste et A11y.
- `/discovery` et `discovery-workflow` demandent de definir les gates UI des la phase design.
- `ds-doc`, `taste-critic`, `a11y-enforcer`, `figma-design-code-sync`, `ai-native-ui` et `skillz-writing-skills` sont raccordes au nouveau rapport.

## Audit axes

| Axis | What it protects |
|---|---|
| Tokens | Couleurs, spacing, radii, motion, z-index via variables ou tokens |
| Components | Reutilisation DS, variants stricts, imports canoniques |
| Stories/docs | Couverture Storybook, exemples, docs d'usage composants |
| A11y | Labels, alt, roles, keyboard, focus, contrastes, reduced motion |
| Taste | Hierarchie, layout, densite, typo, motion, copy, assets, responsive |
| Figma/code | Variants, props, tokens et etats synchronises |
| AI surface/governance | AGENTS.md, manifest, MCP, llms.txt, AI marker, disclaimer, explainability, feedback, human control |

## Workflow contract

```text
Discovery UI
  -> definir gates design-audit
/dev Explore
  -> detecter frontend
  -> design-audit --quick
Plan
  -> P0/P1 deviennent contraintes
Review
  -> correctness/readability/performance
  -> design-audit --ship-gate
/design-audit-squad
  -> audit complet 12 agents si besoin
/qa
  -> Design system entre dans le health score
/ship
  -> P0 bloque
  -> P1 bloque sauf risque explicitement accepte
```

## Non-goals

- Remplacer `taste-critic`, `a11y-enforcer`, `ds-doc` ou `figma-design-code-sync`.
- Transformer chaque audit en refonte automatique.
- Bloquer les repos backend purs sur des axes UI non applicables.
- Faire de Lyse une source de verite unique.

## Validation

- `git diff --check`
- `bash -n install.sh`
- YAML parse des nouveaux fichiers skill/metadata
- TOML sanity check de la commande Gemini
- shell syntax check du helper Lyse
- scan trailing whitespace des nouveaux fichiers `design-audit`

## Follow-ups

- Ajouter un exemple de rapport reel apres le premier usage en projet UI.
- Ajouter une fixture de test installateur pour verifier que `/design-audit` et `/design-audit-squad` sont bien installes/desinstalles sur Codex, Gemini et OpenCode.
- Evaluer plus tard si certaines regles `design-audit` doivent devenir des scripts deterministes.
