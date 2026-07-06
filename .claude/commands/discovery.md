---
description: Planning v6 en niveaux 0-4 — tech-spec directe pour les petits scopes, chaîne Brainstorm → PRD → Architecture → Stories au-delà, spec consolidée approuvée en sortie. Usage: /discovery "besoin"
---

# Discovery — $ARGUMENTS

Charge le skill `discovery-workflow` et exécute-le en mode **interactif**.

- Besoin : **$ARGUMENTS** (parle librement — speech-to-text OK)
- Checkpoints de validation à chaque phase (le planning garde l'humain dans la boucle).
- Niveau 0-1 → tech-spec directe (pas de PRD) ; escalade automatique en réutilisant l'acquis.
- Sortie obligatoire : la spec consolidée `docs/planning/specs/` que tu approuves au dernier checkpoint — elle donne le mandat à /dev et /auto-dev.
