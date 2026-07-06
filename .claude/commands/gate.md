---
description: Lance la boucle quality-gate en standalone sur un diff — reviews multi-lentilles, contre-vérification adversariale, gate file PASS/CONCERNS/FAIL/WAIVED. Usage: /gate [niveau 1-4] [cible]
---

# Gate — $ARGUMENTS

Charge le skill `quality-gate` et exécute-le en standalone.

- Arguments : **$ARGUMENTS** — un niveau optionnel (1-4, **défaut 3 = review complète** : correctness/sécurité, lisibilité, performance + lentilles design-audit/seo-geo/a11y si le diff touche ces surfaces, jusqu'à 4 tours) et/ou une cible (défaut : le diff de la branche par défaut, `git diff <base>...HEAD`). `/gate 1` pour un tour rapide mono-reviewer.
- Prérequis : lancer `project-probe` d'abord si `.agents/verification.yaml` est absent.
- Sortie : `docs/quality/GATE-<date>-<slug>.yaml` committé + résumé (verdict, tours, findings, `decisions_prises_en_ton_nom`).
- Rappel : PASS exige de la preuve exécutable réelle ; sans harness de test, le verdict plafonne à CONCERNS — c'est voulu, le gate ne prétend jamais plus que ce qu'il sait.
