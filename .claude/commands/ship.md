---
description: Ship automatisé v6 — merge de la branche par défaut détectée, preuves du manifeste, gate vérifié (PASS, WAIVED explicite ou legacy compatible), CHANGELOG, push et PR. Usage: /ship
---

# Ship — Release Engineer

Charge le skill `ship-workflow` et exécute-le intégralement, sans confirmation.

- Non-interactif : la prochaine chose que l'utilisateur voit est l'URL de la PR.
- La qualité vient du **gate file** (`docs/quality/GATE-*.yaml`) : v2 PASS frais, v2 WAIVED complet ou v1 `LEGACY_VALID` pendant la fenêtre de compatibilité peuvent avancer.
- Un outil Skillz absent est `tooling-unavailable` et demande une réparation d'installation, jamais un waiver produit.
- Seuls arrêts : branche par défaut, base ambiguë, conflits non résolubles, preuve rouge, gate FAIL, outillage indisponible ou décision de waiver CONCERNS.
