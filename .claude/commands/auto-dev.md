---
description: Développe une feature en mode RALPH autonome via le workflow v6 (mandat requis, zéro stop, gate PASS obligatoire). Usage: /auto-dev #123
---

# Auto-Dev (RALPH) — $ARGUMENTS

**Session :** ${CLAUDE_SESSION_ID}

Charge le skill `dev-workflow` et exécute-le en mode **autonomous**.

- Mandat : **$ARGUMENTS** — le gate de mandat du skill s'applique (issue GitHub valide OU spec approuvée dans `docs/planning/specs/` ; sinon refus avec options). `--allow-no-spec` = prototypage uniquement, loggé comme tel.
- Zéro stop humain. Verdict gate **PASS obligatoire** (CONCERNS jamais auto-accepté ; CONCERNS structurel → STOP immédiat).
- Config RALPH : max **50** itérations (`--max N`), timeout **2h** (`--timeout Xh`), promise **"DEV COMPLETE"**, logs `docs/ralph-logs/${CLAUDE_SESSION_ID}.md`.
- Arrêt manuel : `/cancel-ralph`. Reprise : `/resume-ralph ${CLAUDE_SESSION_ID}`.

Je vérifie le mandat puis j'enchaîne Phase 0 → Phase 6 sans validation intermédiaire.
