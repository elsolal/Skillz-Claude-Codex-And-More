---
name: multi-mind
description: Débat multi-agents avec 6 IA pour valider PRD et code
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Task
  - WebFetch
---

# Multi-Mind Command

Lance un débat multi-agents pour valider un PRD ou reviewer du code.

## Usage

```bash
/multi-mind prd <file>      # Valider un PRD
/multi-mind review <file>   # Review multi-perspectives du code
/multi-mind --room anti-consensus <cible>   # session courte anti-consensus en cours de workflow
```

## Arguments

- `$ARGUMENTS` : Mode (`prd` ou `review`) suivi du fichier cible, OU `--room anti-consensus <cible>` pour une session courte

## Comportement

1. Détecter le mode et le fichier depuis `$ARGUMENTS`
2. Charger le skill Multi-Mind depuis `.claude/skills/multi-mind/SKILL.md`
3. Exécuter le workflow 5 rounds

## Exemple

```bash
/multi-mind prd docs/PRD/PRD-MyFeature.md
/multi-mind review src/components/Auth.tsx
```

---

## Exécution

Lire le skill Multi-Mind et l'exécuter avec les arguments fournis :

```
Mode: [premier argument de $ARGUMENTS]
Fichier: [second argument de $ARGUMENTS]
```

Suivre le workflow défini dans `.claude/skills/multi-mind/SKILL.md`.
