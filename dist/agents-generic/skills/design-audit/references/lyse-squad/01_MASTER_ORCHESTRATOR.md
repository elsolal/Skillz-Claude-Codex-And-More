# Lyse Design Squad — Master Orchestrator

## Rôle

Piloter les 12 agents `design-audit-squad` dans le bon ordre, contrôler les preuves, fusionner les findings, empêcher les doublons et produire un rapport final actionnable.

## Références obligatoires

Lire avant de commencer:

1. `00_REGLES_COMMUNES.md`
2. `references/lyse/README.md`
3. `references/lyse/cli-runtime.md`
4. `references/lyse/rule-catalog.md`
5. `references/lyse/result-mapping.md`

## Configuration initiale

Déterminer:

- Cible: repo, chemin, URL locale/prod, Figma, screenshot.
- Mode: `quick`, `full`, `squad`, `ship-gate`.
- Objectif: audit informatif, blocage ship, dette DS, agent-readiness, IA UI.
- Runtime disponible: Node >= 22, browser, Figma MCP, Playwright, screenshots, rapport Lyse existant.
- Écriture autorisée: oui/non pour `audit-livrables/<nom>/`.

Si une info manque mais que l'audit peut avancer, continuer avec `Non vérifié`.

## Séquence complète

1. Agent 01 — Scope & Evidence Collector
2. Agent 02 — Lyse Static Runner & Parser
3. Agent 03 — Tokens Auditor
4. Agent 04 — Components & Contracts Auditor
5. Agent 05 — Stories & DS Docs Auditor
6. Agent 06 — Accessibility Auditor
7. Agent 07 — AI Surface Auditor
8. Agent 08 — AI Governance Auditor
9. Agent 09 — Figma/Code Drift Auditor
10. Agent 10 — Taste & Runtime UI Auditor
11. Agent 11 — Remediation Planner
12. Agent 12 — Final Report & Ship Gate

## Contrôle qualité avant chaque agent

Avant de lancer un agent:

- Le scope est connu ou marqué `Non vérifié`.
- Les preuves disponibles sont listées.
- Les outputs des agents précédents sont disponibles.
- Les blocants P0/P1 ont au moins une preuve précise.
- Les axes N/A sont explicités.

## Anti-doublons

| Agent | Mission stricte |
|---|---|
| 01 | Inventaire sources, surfaces, outils disponibles |
| 02 | Exécuter/interpréter Lyse, pas juger le goût visuel |
| 03 | Tokens uniquement |
| 04 | Composants, imports, props, contrats |
| 05 | Stories, examples, docs DS |
| 06 | A11y structurelle et runtime si possible |
| 07 | Surface agent-readable: AGENTS, manifest, MCP, llms.txt |
| 08 | Governance UI IA: marker, disclaimers, controls, value gate |
| 09 | Drift Figma/code |
| 10 | Taste visuel/runtime |
| 11 | Plan d'action priorisé |
| 12 | Synthèse finale, verdict et ship-gate |

## Livrables complets

Si écriture autorisée:

```text
audit-livrables/<nom>/
  01_scope_evidence.md
  02_lyse_static_report.md
  03_tokens.md
  04_components_contracts.md
  05_stories_docs.md
  06_accessibility.md
  07_ai_surface.md
  08_ai_governance.md
  09_figma_code_drift.md
  10_taste_runtime.md
  11_remediation_plan.md
  12_final_report_ship_gate.md
```

Sinon produire les mêmes sections en Markdown dans la réponse.

## Rapport final attendu

```markdown
# Lyse Design Squad Report — [Target]

## Executive verdict
- Verdict: Ship-ready | Fix P0/P1 first | Needs design loop
- Lyse: score/tier ou skipped
- Confidence: Élevé | Moyen | Faible
- Top blockers

## Axis scores
| Axis | Score | Source | Notes |

## Findings consolidated
| Sev | Axis | Where | Status | Issue | Fix |

## Ship gate
| Gate | Status | Reason |

## Roadmap
### 24-48h
### 7 jours
### 30 jours

## Non vérifié
```
