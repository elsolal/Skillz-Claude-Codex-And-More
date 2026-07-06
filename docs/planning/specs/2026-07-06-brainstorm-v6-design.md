---
title: "Brainstorm v6 — Advanced Elicitation, anti-consensus, pressure-test"
status: approved
approved_by: aymeric
approved_at: 2026-07-06
created_at: 2026-07-06
slug: brainstorm-v6
level: 2
---

# Brainstorm v6 — Design (« second temps » de la refonte D-EPCT+R v6)

## 1. Contexte et décisions de cadrage

Second temps explicitement reporté par la spec `2026-07-05-epctr-v6-design.md` §10. Inspirations BMAD Method v6.8-6.10 (recherche du 2026-07-05) : Advanced Elicitation (19 lentilles), Party Mode anti-consensus room, `bmad-forge-idea`.

Décisions validées par Aymeric le 2026-07-06 :
- **Elicitation = skill dédié + commande `/elicit`** (pas un mode de rodin — deux gestes distincts : challenge socratique vs re-examen méthodique par lentille nommée).
- **Périmètre** : les 3 features brainstorm + nettoyage du vocabulaire FULL/LIGHT de `pm-prd`/`pm-stories`/`ux-designer`/`multi-mind`. `/pr-review` + gate file reste au backlog.
- Une seule vague, une PR. Conventions v6 : skill canonique en anglais, lanceurs minces (commande FR + prompt Codex EN signé loader).

## 2. Skill `elicitation` + `/elicit`

**Geste** : ré-examiner une sortie existante (PRD, plan, spec, code, décision) sous une lentille de raisonnement nommée — au lieu d'un « refais mieux » vague.

- `skills/elicitation/SKILL.md` (EN) : quand l'utiliser, le protocole (charger la lentille → relire la cible sous cette seule lentille → produire findings + révisions proposées → l'utilisateur arbitre), règles (une lentille à la fois ; la lentille ne réécrit pas, elle révèle ; sortie actionnable, pas dissertation).
- `knowledge/brainstorming/elicitation-methods.csv` : ~12 lentilles, colonnes `lens_id,name,description,core_question,best_for`. Set initial : Pre-mortem, Inversion, First Principles, Red Team vs Blue Team, Steelman-then-attack, Chesterton's Fence, 10-10-10, Second-Order Effects, Occam's Razor, Constraint Removal, Persona Shift (novice/expert/adversaire), Cost-of-Delay.
- `commands/elicit.md` (lanceur FR ≤ 15 lignes) : `/elicit <lentille> [cible]` ou `/elicit [cible]` → menu des lentilles. Prompt Codex `.codex/prompts/elicit.md` (signé loader).
- **Points d'accroche** (références légères, pas de refonte) : `discovery-workflow` propose le menu aux checkpoints (« [E] appliquer une lentille avant de valider ») ; `rodin` mentionne les lentilles comme méthodes nommées ; `idea-brainstorm` le propose à la synthèse.

## 3. Anti-consensus room dans `multi-mind`

- Nouveau persona **« Contrarian »** dans `knowledge/multi-mind/agent-personalities.md` : son unique mandat est de produire la plus forte objection au consensus émergent — il n'a pas le droit d'être d'accord.
- Règle dure dans `multi-mind/SKILL.md` : **aucun consensus ne peut être déclaré tant que le Contrarian n'a pas parlé au round final et que sa meilleure objection n'a pas reçu une réponse explicite** (réfutée avec raison, ou intégrée). Divergence documentée sinon.
- Déclenchable en cours de workflow (mid-brainstorm, mid-PRD) sans casser le fil : mode `--room anti-consensus` documenté.

## 4. Pressure-test « forge » dans `/discovery`

- Option **[P] Pressure-test d'abord** en Phase 1 de `discovery-workflow` : avant tout brainstorm, challenge socratique de l'idée (posture rodin + 2-3 lentilles d'elicitation choisies selon l'idée — typiquement Pre-mortem, Inversion, First Principles).
- Sortie : `docs/planning/forge/FORGE-<slug>-<date>.md` — thèse testée, objections fortes, kernel survivant (problème/pour qui/pari central), verdict continuer/pivoter/abandonner. Le kernel nourrit la Phase 2 (ou la tech-spec directe niveau 0-1).
- Pas de nouveau skill : c'est un chemin de `discovery-workflow` qui référence `rodin` et `elicitation`.

## 5. Nettoyage FULL/LIGHT (alignement grille 0-4)

`pm-prd`, `pm-stories`, `ux-designer`, `multi-mind` : remplacer le vocabulaire de mode FULL/LIGHT interne (menus [F]/[L], descriptions frontmatter) par la logique de niveaux ou un vocabulaire neutre (« PRD complet vs synthétique selon le niveau »). Pas de refonte de ces skills — substitution de vocabulaire + cohérence des références depuis discovery-workflow.

## 6. Test de sortie

Smoke « runtime naïf » : (a) `/elicit premortem` sur un doc scratch produit des findings actionnables sous la seule lentille ; (b) le protocole anti-consensus de multi-mind bloque structurellement un consensus sans objection Contrarian traitée (vérification du texte, pas d'appel API réel) ; (c) l'option [P] apparaît en Phase 1 de discovery et produit un forge-report ; (d) `git grep -i "full mode\|light mode\|mode full\|mode light"` repo-wide : plus aucun hit opératoire hors historique.

## 7. Backlog restant après cette vague

`/pr-review` consomme le gate file ; court-circuit CONCERNS-frais dans ship ; alignement `<base>` ship steps 1/2/5 ; références fantômes `pm-discovery` dans WORKFLOW.md ; exclusion du manifeste dans le hash (edge).
