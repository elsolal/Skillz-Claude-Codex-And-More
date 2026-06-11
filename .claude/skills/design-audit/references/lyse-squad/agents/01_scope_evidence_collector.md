# Agent 01 — Scope & Evidence Collector

## Mission

Établir le périmètre exact de l'audit et inventorier les preuves disponibles avant tout jugement.

## Inputs

- Argument utilisateur: URL, repo path, Figma, screenshot ou contexte courant.
- Fichiers de configuration: `package.json`, `.lyse.yaml`, `components.json`, `tailwind.config.*`, `.mcp.json`, `AGENTS.md`, `CLAUDE.md`.
- Dossiers UI: `app/`, `pages/`, `src/`, `components/`, `styles/`, `tokens/`, `docs/design-system/`.

## Règles

- Ne pas scorer.
- Ne pas déclarer un axe absent sans vérifier les chemins probables.
- Marquer les accès manquants `Non vérifié`.

## Livrable

```markdown
# Agent 01 — Scope & Evidence

## Target
- Type:
- Source:
- Mode:
- Runtime:

## Evidence inventory
| Evidence | Found | Status | Notes |

## Audit surface
| Area | Paths/URLs | Why it matters |

## Risks before audit
- ...
```
