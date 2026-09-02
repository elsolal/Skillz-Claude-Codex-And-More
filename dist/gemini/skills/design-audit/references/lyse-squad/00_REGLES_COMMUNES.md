# Lyse Design Squad — Règles communes

Ces règles s'appliquent à tous les agents du workflow `design-audit-squad`.

## Mission

Auditer une UI, un design system ou une surface agent-readable avec une approche structurée inspirée de Lyse: preuves statiques déterministes, axes design-system, score exploitable, puis enrichissement Skillz-Claude par le taste, le drift Figma/code et le ship-gate.

## Garde-fous

1. **Read-only par défaut**: ne modifier aucun fichier, ne lancer aucun fix, ne committer rien.
2. **Lyse n'est pas le verdict unique**: son score est une preuve statique; le verdict final combine Lyse, code, runtime, Figma, taste et accessibilité.
3. **Pas de code Lyse copié**: utiliser les références `references/lyse/` et le CLI externe si possible.
4. **Statut de preuve obligatoire**:
   - `Confirmé`: lu dans un fichier, un rapport Lyse, une capture, un navigateur ou une sortie outil.
   - `Déduit`: inféré depuis une preuve confirmée.
   - `Non vérifié`: inaccessible ou non fourni.
5. **N/A n'est pas un échec**: un axe sans surface applicable ne pénalise pas le verdict; expliquer pourquoi.
6. **Double-check des blocants**: avant P0/P1, citer au moins une preuve locale précise et l'impact utilisateur/ship.
7. **Scope strict par agent**: ne pas refaire l'audit d'un autre agent; signaler les dépendances au Master Orchestrator.
8. **Client-friendly**: traduire les termes techniques au premier usage.

## Sévérités Skillz

| Niveau | Bloque ship ? | Définition |
|---|---:|---|
| P0 | Oui | UI cassée, action bloquée, a11y critique, AI trompeuse ou design-system incohérent sur chemin critique |
| P1 | Oui en ship-gate | Violation forte tokens/components/a11y/AI governance, drift Figma/code significatif |
| P2 | Non | Dette design-system, documentation manquante, polish ou risque de dérive |
| P3 | Non | Nits, clarifications, opportunités futures |

## Livrable agent standard

Chaque agent produit:

```markdown
# Agent XX — [Nom]

## Synthèse 3 lignes
- ...

## Preuves utilisées
| Source | Statut | Notes |
|---|---|---|

## Findings
| Sev | Where | Status | Issue | Fix |
|---|---|---|---|---|

## Score agent
X/10 — justification courte

## À transmettre
- Points que l'agent suivant doit reprendre
```
