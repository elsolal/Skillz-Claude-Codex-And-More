---
description: Développe une feature avec le workflow adaptatif D-EPCT+R v6 (niveaux 0-4, stop unique au plan, boucle quality-gate). Usage: /dev [issue] ou /dev "description"
---

# Dev — $ARGUMENTS

Charge le skill `dev-workflow` et exécute-le en mode **interactive**.

- Tâche : **$ARGUMENTS** (issue `#NUM` → `gh issue view` en Phase 1)
- Un seul stop humain : le plan (Phase 2). Niveaux 3-4 : lecture des « décisions prises en ton nom » avant ship.
- Toute la logique (niveaux, escalade, RED, gate) vit dans le skill — ne pas improviser en dehors.

Je commence par Phase 0 (probe) puis Phase 1 (explore).
