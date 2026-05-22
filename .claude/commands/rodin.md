---
description: Challenge socratique anti-complaisance d'une idee, decision, strategie, PRD, architecture ou reponse d'agent. Usage: /rodin <texte|path|url>
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
---

# Rodin Command

Lance une passe de challenge intellectuel avec le skill `rodin`.

## Usage

```bash
/rodin "Notre plan est de..."
/rodin docs/planning/specs/2026-05-22-feature-design.md
/rodin https://example.com/plan.md
```

## Comportement

1. Charger le skill `.claude/skills/rodin/SKILL.md`.
2. Identifier l'input depuis `$ARGUMENTS` :
   - chemin local : lire le fichier cible ;
   - URL : recuperer le contenu si possible ;
   - texte libre : utiliser directement l'argument ;
   - argument vide : challenger le dernier plan ou raisonnement visible dans la conversation.
3. Executer le workflow Rodin : these, steelman, classification, objections, angles morts, tests de realite, verdict.
4. Ne pas modifier de fichiers sauf demande explicite apres la review.

## Sortie attendue

```markdown
# Rodin Review

## These testee
## Steelman
## Points classes
## Objections fortes
## Angles morts
## Tests de realite
## Verdict
```

## Execution

Lire le skill `rodin` en entier, puis appliquer sa grille au contenu fourni :

```text
$ARGUMENTS
```
