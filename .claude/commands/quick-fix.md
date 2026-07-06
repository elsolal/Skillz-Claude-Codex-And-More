---
description: Fix rapide via le circuit court du workflow v6 (niveau 0 forcé, escalade automatique si ça grossit). Usage: /quick-fix "description du problème"
---

# Quick Fix — $ARGUMENTS

Charge le skill `dev-workflow` et exécute-le en mode **quick-fix** (niveau 0 forcé).

- Problème : **$ARGUMENTS**
- Circuit court : localiser → fixer → vérifs du manifeste → présenter. Pas de plan formel, pas de gate file.
- Si le fix dépasse le niveau 0 (4ᵉ fichier, >50 lignes, dépendance), le workflow **escalade tout seul** au niveau supérieur en gardant l'acquis — ne pas demander de relancer /dev.
- Ne pas auto-commit : présenter le fix et le commit suggéré.
