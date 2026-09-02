---
description: Ship automatisé v6 — merge main, preuves du manifeste, consommation du gate file (PASS requis ou waiver explicite), CHANGELOG, commits bisectables, push, PR. Usage: /ship
---

# Ship — Release Engineer

Charge le skill `ship-workflow` et exécute-le intégralement, sans confirmation.

- Non-interactif : la prochaine chose que l'utilisateur voit est l'URL de la PR.
- La qualité vient du **gate file** (`docs/quality/GATE-*.yaml`) : PASS frais → PR directe ; absent/périmé/CONCERNS/FAIL → le skill relance quality-gate lui-même.
- Seuls arrêts : branche main, conflits non résolubles, preuve rouge, gate FAIL, décision de waiver CONCERNS.
