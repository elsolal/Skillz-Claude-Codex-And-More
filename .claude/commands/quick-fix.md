---
description: Fix rapide sans passer par tout le workflow EPCT+R. Pour les petits bugs, typos, et corrections mineures. Usage: /quick-fix "description du problème"
---

# Quick Fix

**Session ID:** ${CLAUDE_SESSION_ID}

## 📥 Contexte à charger

**Identifier rapidement le problème à corriger.**

| Contexte | Action | Priorité |
|----------|--------|----------|
| État git | `Bash: git status --short` | Optionnel |
| Fichiers récents | `Bash: git diff --name-only HEAD~3` | Optionnel |
| Erreurs lint/types | `Bash: npm run lint` et `npm run typecheck` | Optionnel |

### Instructions de chargement
1. Vérifier l'état git actuel
2. Identifier les erreurs lint/types existantes
3. Localiser rapidement le fichier concerné

---

## Mode Quick Fix activé

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              QUICK FIX MODE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🎯 Objectif : Fix rapide, sans overhead                                    │
│                                                                             │
│  ✅ Pour :                                                                  │
│     - Typos et erreurs de frappe                                            │
│     - Petits bugs évidents                                                  │
│     - Ajustements mineurs                                                   │
│     - Corrections de lint/types                                             │
│                                                                             │
│  ❌ Pas pour :                                                              │
│     - Nouvelles features (utiliser /dev)                                    │
│     - Refactoring important (utiliser /refactor)                            │
│     - Changements architecturaux                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Process simplifié

### 1. Analyse rapide
- Identifier le problème
- Localiser le(s) fichier(s) concerné(s)
- Évaluer l'impact

### 2. Fix
- Appliquer la correction
- Vérifier lint/types

### 3. Validation (verification-before-completion)

**Vérifs minimales `/quick-fix`** (référence : `.claude/knowledge/workflows/verification-matrix.md`) :

- ✅ Lint OK
- ✅ Types OK
- ⚠️ Tests : optionnels selon contexte (typo doc → non, fix logique → oui)

```bash
npm run lint && npm run typecheck
# + npm test si le fix touche du code applicatif
```

**Si une vérif échoue → ne pas déclarer DONE.** Reporter l'erreur et corriger avant de proposer le commit.

---

## Règles Quick Fix

- ⛔ **Max 3 fichiers** - Si plus, utiliser `/dev`
- ⛔ **Max 50 lignes modifiées** - Si plus, utiliser `/dev`
- ⛔ **Pas de nouvelle dépendance** - Si besoin, utiliser `/dev`
- ✅ **Toujours vérifier lint/types** après le fix
- ✅ **Commit atomique** avec message clair

---

## Output

```markdown
## Quick Fix: [Description courte]

### Problème
[Description du problème]

### Solution
[Ce qui a été fait]

### Fichiers modifiés
- `path/to/file.ts` - [Description]

### Vérifications
- Lint: ✅/❌
- Types: ✅/❌
- Tests: ✅/❌

### Commit suggéré
fix(scope): [description courte]
```

---

## Démarrage

**Problème à fixer :** $ARGUMENTS

Je localise et corrige le problème...
