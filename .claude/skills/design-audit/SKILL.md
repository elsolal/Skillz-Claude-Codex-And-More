---
name: design-audit
description: Audit une UI ou design system via tokens, composants, stories/docs, a11y, taste, Figma, IA et Lyse. Utiliser avant /qa, /ship, /dev frontend, pour une boucle design, ou pour lancer une squad multi-agents via /design-audit-squad.
---

# Design Audit

Audit transversal pour verifier qu'une interface, un design system ou un flow frontend respecte les contrats visuels, techniques, accessibles et agent-readable. Le skill enrichit la boucle Skillz-Claude avec Lyse comme signal statique externe optionnel, puis chaine vers les skills qualitatifs existants.

## Quand utiliser

- Avant `/ship` sur une PR frontend, design system, Figma-to-code ou AI UI.
- Dans `/qa` pour compléter le health score avec une preuve design-system.
- Dans `/dev` quand la feature modifie des fichiers `.tsx`, `.jsx`, `.vue`, `.css`, des composants, tokens, pages ou flows UI.
- Quand l'utilisateur demande un audit design, une boucle design/code, un check de drift Figma/code, ou un score de qualite UI.
- Quand l'utilisateur mentionne Lyse, `@lyse-labs/lyse`, Health Score, `.lyse.yaml`, ou veut reprendre les règles Lyse dans une boucle Skillz-Claude.
- Quand l'utilisateur demande un workflow complet avec plusieurs agents, une "squad Lyse", ou un audit UI/DS approfondi.
- Quand un repo doit devenir plus lisible pour les agents: `AGENTS.md`, skills, MCP, manifest composants, docs DS.

## Quand NE PAS utiliser

- Bug backend pur sans surface UI ou DS.
- Simple critique esthétique d'un screenshot sans besoin de contrat technique: utiliser `taste-critic`.
- Audit accessibilite seul: utiliser `a11y-enforcer`.
- Sync Figma/code ciblé sur un composant connu: utiliser `figma-design-code-sync`.
- Creation de documentation DS exhaustive: utiliser `ds-doc`.

## Inputs

| Input | Usage |
|---|---|
| URL locale/prod | Audit runtime + screenshots + console si outils navigateur disponibles |
| Chemin repo | Audit statique des fichiers UI, tokens, composants, docs agent |
| Figma URL | Drift design/code + tokens + variants |
| Screenshot | Audit visuel qualitatif, sans preuve statique complète |
| `--quick` | Score rapide et top 5 risques |
| `--full` | Audit complet et plan de correction |
| `--squad` | Workflow complet Lyse Design Squad avec 12 agents |
| `--ship-gate` | Focus blocants P0/P1 avant ship |

## Références Lyse

Si l'utilisateur mentionne Lyse, si le repo contient `.lyse.yaml`, ou si le mode est `--full` / `--ship-gate` sur un repo frontend/design-system, lire:

1. `references/lyse/README.md`
2. `references/lyse/cli-runtime.md`
3. `references/lyse/rule-catalog.md`
4. `references/lyse/result-mapping.md`

Ces références sont des notes d'intégration Skillz-Claude. Ne pas copier le code Lyse: l'outil upstream est AGPL-3.0-only / commercial et reste une dépendance externe appelée via CLI ou MCP.

## Références Lyse Design Squad

Pour `--squad`, `/design-audit-squad`, "workflow complet", "plein d'agents", ou "squad Lyse", charger:

1. `references/lyse-squad/00_REGLES_COMMUNES.md`
2. `references/lyse-squad/01_MASTER_ORCHESTRATOR.md`
3. Tous les prompts dans `references/lyse-squad/agents/`, dans l'ordre défini par le master orchestrator.

Chaque prompt agent est autoritaire sur son périmètre. Ne pas résumer les règles au point de supprimer ses garde-fous.

## Process

### 1. Cadrer la surface

Identifier:
- type: app, landing, design system, composant, AI UI, repo agent-tooling;
- source: URL, path, Figma, screenshot;
- mode: quick, full, squad, ship-gate;
- seuil attendu: informatif, strict, ou bloquant.

Si le scope est ambigu, poser 1 question maximum. Sinon avancer avec l'hypothèse la plus conservatrice.

### 2. Collecter les preuves

Lire en priorité:
- `AGENTS.md`, `CLAUDE.md`, `components/CLAUDE.md`, `components/AGENTS.md`;
- `package.json`, `components.json`, `.mcp.json`, `.lyse.yaml`, `tailwind.config.*`, `tokens*.json`;
- fichiers UI pertinents (`components/`, `src/components/`, `app/`, `pages/`, `styles/`);
- docs planning/DS (`docs/planning/ui`, `docs/design-system`, `figma.config.json`).

Si Lyse est disponible et que le repo est frontend/DS/agent-surface, lancer un audit non destructif via le helper:

```bash
.claude/skills/design-audit/scripts/run-lyse-audit.sh .
```

Si Node < 22, Lyse absent, ou le repo n'est pas compatible, continuer en audit statique manuel et noter `Lyse: skipped`.

En mode `--squad`, suivre `references/lyse-squad/01_MASTER_ORCHESTRATOR.md`, produire les 12 livrables agents, puis consolider le rapport final.

### 3. Auditer les axes Lyse + Skillz

#### A. Tokens
- Couleurs, spacing, radii, shadows, motion et z-index doivent passer par tokens ou variables.
- Les tokens semantiques doivent expliquer leur usage.
- DTCG ou convention locale doit rester coherente avec Figma/code.

#### B. Components
- Reutiliser les composants DS avant natif HTML.
- Props de variants strictes (`"primary" | "secondary"`, pas `string`/`any`).
- Imports depuis le module canonique du DS.
- Storybook ou examples couvrent les variantes critiques.

#### C. Stories / documentation in code
- Les composants DS critiques doivent avoir story, exemple, fixture ou documentation d'usage.
- Les absences Storybook sont P2 par défaut, P1 si l'équipe dépend des agents pour produire l'UI.

#### D. A11y
- Labels, alt, roles, keyboard, focus, contrastes, reduced motion.
- Deleguer les violations detaillees a `a11y-enforcer` si l'audit revele P0/P1.

#### E. Taste
- Hierarchie, layout, densite, typo, motion, copy, assets et responsive.
- Deleguer l'analyse qualitative a `taste-critic` pour URL/screenshot/code UI.

#### F. Figma/code drift
- Variants, props, tokens, et etats Figma doivent mapper vers le code.
- Si drift detecte, appeler `figma-design-code-sync` ou produire un handoff clair.

#### G. AI surface & governance
- Surface agent-readable: `AGENTS.md` command-first, MCP config, manifest composants, skills valides.
- UI IA: AI marker, disclaimer, explainability, feedback, loading/error states, stop/regenerate/edit/dismiss controls.
- Gate produit: "l'IA est-elle necessaire ?", fallback deterministe, permission/retry/citation.

### 4. Classer

| Niveau | Bloque ship ? | Definition |
|---|---:|---|
| P0 | Oui | Bug visible, a11y critique, drift DS cassant, action utilisateur bloquee |
| P1 | Oui en `--ship-gate` | Violation forte de tokens/components/a11y/AI governance |
| P2 | Non | Dette de qualite, risque de drift, polish utile |
| P3 | Non | Nits, suggestions, documentation |

### 5. Sortie

```markdown
## Design Audit Report

**Input**: ...
**Mode**: quick | full | squad | ship-gate
**Lyse**: score X/100 | skipped (raison)
**Verdict**: Ship-ready | Fix P0/P1 first | Needs design loop

### Axis scores
| Axis | Score | Evidence |
|---|---:|---|
| Tokens | ... | ... |
| Components | ... | ... |
| Stories/docs | ... | ... |
| A11y | ... | ... |
| Taste | ... | ... |
| Figma/code | ... | ... |
| AI surface | ... | ... |

### Findings
| Sev | Axis | Where | Issue | Fix |
|---|---|---|---|---|

### Top 3 fixes
1. ...

### Next action
- `taste-critic` / `a11y-enforcer` / `figma-design-code-sync` / `ds-doc` / `/dev`
```

## Livrables squad

En mode `--squad`, produire ou recommander:

- `01_scope_evidence.md`
- `02_lyse_static_report.md`
- `03_tokens.md`
- `04_components_contracts.md`
- `05_stories_docs.md`
- `06_accessibility.md`
- `07_ai_surface.md`
- `08_ai_governance.md`
- `09_figma_code_drift.md`
- `10_taste_runtime.md`
- `11_remediation_plan.md`
- `12_final_report_ship_gate.md`

## Integration workflow

- `/design-audit`: audit compact, ciblé ou ship-gate.
- `/design-audit-squad`: orchestration complète Lyse Design Squad avec 12 agents.
- `/dev`: utiliser après la phase Explore si frontend detecte, puis intégrer les P0/P1 au plan.
- `/qa`: ajouter le verdict Design Audit au health score.
- `/ship`: en `--ship-gate`, P0 bloque; P1 exige correction ou acknowledgement explicite.
- `/ds-doc`: après correction DS, documenter les nouveaux tokens/composants/manifestes.
- Lyse: si l'audit est complet, charger `references/lyse/` et utiliser le score comme preuve statique, pas comme verdict unique.

## Exemples

```bash
/design-audit . --quick
/design-audit http://localhost:3000 --ship-gate
/design-audit https://www.figma.com/design/... --full
```

Exemple de décision:

- `Lyse: 50/100, Defined`, mais findings centrés sur la taille des skills.
- Verdict Skillz: `Needs design loop` si les P0/P1 touchent tokens, composants, a11y, drift ou IA.
- Action: corriger les P0/P1 dans `/dev`, puis relancer `design-audit --ship-gate`.

## Anti-patterns

- Ne pas traiter Lyse comme source unique: c'est une preuve statique, pas un jugement complet.
- Ne pas copier de code Lyse dans Skillz-Claude; appeler l'outil externe ou utiliser les références d'intégration.
- Ne pas bloquer un repo non-UI parce que les axes tokens/a11y/components sont N/A.
- Ne pas transformer un audit en refonte: le livrable est un verdict + plan de correction priorise.
