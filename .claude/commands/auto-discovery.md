---
description: Planning v6 autonome (RALPH) — mêmes niveaux 0-4, zéro stop, spec en sortie toujours status draft à faire approuver par un humain. Usage: /auto-discovery "besoin"
---

# Auto-Discovery (RALPH) — $ARGUMENTS

**Session :** ${CLAUDE_SESSION_ID}

Charge le skill `discovery-workflow` et exécute-le en mode **autonome**.

- Besoin : **$ARGUMENTS** — zéro validation intermédiaire.
- La spec de sortie reste `status: draft`, `approved_by: ralph` : un humain doit l'approuver avant tout `/auto-dev`.
- Config RALPH : max **30** itérations (`--max N`), timeout **1h** (`--timeout Xh`), promise **"DISCOVERY COMPLETE"**, logs `docs/ralph-logs/${CLAUDE_SESSION_ID}.md`. Arrêt : `/cancel-ralph`.
