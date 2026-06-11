---
description: Lance le workflow de planning complet (Brainstorm → PRD → Architecture → Stories). L'orchestrateur garde tout le contexte. Détecte automatiquement le mode FULL ou LIGHT.
---

# Discovery Session — $ARGUMENTS

## Architecture Orchestrateur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ORCHESTRATEUR PRINCIPAL (TOI) — garde tout le contexte                     │
│                                                                             │
│  Phase 1: Écoute    → Tu écoutes et analyses le scope                      │
│  Phase 2: Brainstorm → Tu facilites directement (si FULL)                  │
│  Phase 3: UX Design → Tu conçois les parcours (si score UX ≥ 4)           │
│  Phase 4: PRD       → Tu rédiges avec tout le contexte                     │
│  Phase 5: UI Design → Tu définis le design system (si score UI ≥ 3)       │
│  Phase 6: Archi     → Tu architectures avec le contexte complet (si FULL) │
│  Phase 7: Stories   → Tu découpes en stories                               │
│  Phase 8: GitHub    → Subagent crée les issues (travail mécanique)        │
│                                                                             │
│  [STOP] à chaque phase — validation avant de continuer                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Principe clé :** TOI, l'orchestrateur principal, tu gardes tout le contexte à travers TOUTES les phases. Tu ne délègues JAMAIS vers un skill forké. Tu suis le process de chaque skill directement. Tu dispatches uniquement le travail mécanique (création d'issues) via subagent.

---

## Phase 1: Écoute & Analyse

1. Écouter le besoin de l'utilisateur (speech-to-text OK, pas besoin d'être structuré)
2. Poser 2-3 questions de clarification si nécessaire
3. Analyser le scope pour détecter le mode :

| Critère | LIGHT | FULL |
|---------|-------|------|
| Nombre de features | 1-2 | 3+ |
| Complexité technique | Simple | Multi-composants |
| Écrans/pages UI | 1-2 | 3+ |
| Intégrations externes | 0 | 1+ |
| Estimation dev | < 1 jour | > 1 jour |

4. Proposer le mode détecté (l'utilisateur peut overrider)

**STOP CHECKPOINT 1** — Mode validé.

---

## Phase 2: Brainstorm (si FULL)

**TOI, l'orchestrateur, tu facilites le brainstorm directement.**

1. Charger les techniques : `Read .claude/knowledge/brainstorming/brain-techniques.csv`
2. Proposer les 4 approches de session :
   - [1] User-Selected — l'utilisateur choisit les techniques
   - [2] AI-Recommended — tu suggests les techniques adaptées
   - [3] Random Discovery — perspectives inattendues
   - [4] Progressive Flow — voyage créatif en 4 phases
   - [R] Research-first — valider des hypothèses d'abord
3. Faciliter l'exploration interactive :
   - Viser 50+ idées avant organisation
   - Anti-biais : pivoter de domaine tous les 10 idées
   - Energy checkpoints toutes les 4-5 échanges
4. Synthétiser : Top 5 idées, thèmes émergents, direction recommandée
5. Sauvegarder dans `docs/planning/brainstorms/BRAINSTORM-{slug}-{date}.md`
6. Évaluer si UX/UI nécessaire (scores UX ≥ 4 / UI ≥ 3)

Référence process détaillé : `.claude/skills/idea-brainstorm/SKILL.md`

**STOP CHECKPOINT 2** — Brainstorm validé + évaluation UX/UI.

---

## Phase 3: UX Design (si score UX ≥ 4)

**TOI, l'orchestrateur, tu conçois l'UX directement.** Tu as tout le contexte du brainstorm.

1. Définir les personas basés sur le brainstorm
2. Concevoir les user journeys (parcours principaux)
3. Créer les wireframes textuels (architecture des écrans)
4. Identifier les points de friction et optimisations
5. Sauvegarder dans `docs/planning/ux/UX-{slug}.md`

Référence process détaillé : `.claude/skills/ux-designer/SKILL.md`

**STOP CHECKPOINT 3** — UX validée.

---

## Phase 4: PRD

**TOI, l'orchestrateur, tu rédiges le PRD.** Tu as tout le contexte (brainstorm + UX).

1. Poser les questions essentielles (max 3-4 à la fois) :
   - Problème : Quel problème ? Pour qui ? Pourquoi maintenant ?
   - Solution : Comment c'est résolu aujourd'hui ? Solution envisagée ? Hors scope ?
   - Succès : Comment on sait que c'est réussi ? Contraintes ?
2. Rédiger le PRD (FULL ou LIGHT selon le mode) :
   - Mode FULL : Overview, Utilisateurs, Fonctionnalités, Requirements, Contraintes, Métriques
   - Mode LIGHT : Problème, Solution, Features, Critères de succès, Hors scope
3. Sauvegarder dans `docs/planning/prd/PRD-{slug}.md`
4. Évaluer si UI nécessaire (si pas déjà évalué)

Référence process détaillé : `.claude/skills/pm-prd/SKILL.md`
Knowledge : `.claude/knowledge/workflows/prd-template.md`, `domain-complexity.csv`, `project-types.csv`

**STOP CHECKPOINT 4** — PRD validé.

---

## Phase 5: UI Design (si score UI ≥ 3)

**TOI, l'orchestrateur, tu définis le design system.** Tu as tout le contexte (brainstorm + UX + PRD).

1. Définir la palette de couleurs et typographie
2. Créer les composants UI principaux
3. Établir les guidelines visuelles
4. Documenter les patterns d'interaction
5. Définir les gates `design-audit` pour la livraison: tokens, composants, a11y, taste, drift Figma/code, surface IA si pertinent
6. Si le produit est un site public, landing, média, e-commerce ou contenu indexable, définir les objectifs `seo-geo-audit`: mots-clés, SERP, contenu, schema, llms.txt, visibilité IA, KPIs GSC
7. Sauvegarder dans `docs/planning/ui/UI-{slug}.md`

Référence process détaillé : `.claude/skills/ui-designer/SKILL.md` + `.claude/skills/design-audit/SKILL.md` + `.claude/skills/seo-geo-audit/SKILL.md`

**STOP CHECKPOINT 5** — UI validée.

---

## Phase 6: Architecture (si FULL)

**TOI, l'orchestrateur, tu architectures.** Tu as TOUT le contexte (brainstorm + UX + PRD + UI).

1. Analyser le codebase existant (stack, patterns, structure)
2. Proposer le stack technique avec justifications
3. Définir la structure du projet, le data model, les APIs
4. Identifier les risques techniques et mitigations
5. Sauvegarder dans `docs/planning/architecture/ARCH-{slug}.md`

Référence process détaillé : `.claude/skills/architect/SKILL.md`

**STOP CHECKPOINT 6** — Architecture validée.

---

## Phase 7: Stories

**TOI, l'orchestrateur, tu découpes en stories.** Tu as TOUT le contexte de toutes les phases.

1. Identifier les Epics (groupes fonctionnels)
2. Créer les User Stories au format INVEST :
   - **En tant que** [persona], **je veux** [action], **afin de** [bénéfice]
   - Critères d'acceptance en Given/When/Then
   - Estimations : XS/S/M/L (max L = 2j, au-delà = découper)
3. Sauvegarder dans `docs/stories/EPIC-{num}-{slug}/`
4. Implementation Readiness Check (score ≥ 13/15 requis)

Référence process détaillé : `.claude/skills/pm-stories/SKILL.md`

**STOP CHECKPOINT 7** — Stories validées + Readiness OK.

---

## Phase 8: Publication GitHub (subagent)

Dispatcher un **subagent** via `SendMessage` pour créer les issues :

```
SendMessage(run_in_background: true)
Prompt: "Crée les issues GitHub suivantes :

Epic : [titre] — labels: epic, feature
Body : [contenu de l'epic]

Stories liées :
- [STORY-001] [titre] — body: [contenu], labels: story, Part of #[epic]
- [STORY-002] [titre] — body: [contenu], labels: story, Part of #[epic]
- ...

Utilise `gh issue create` ou MCP GitHub.
Retourne les numéros d'issues créées."
```

Quand le subagent revient :
1. Confirmer les issues créées
2. Présenter le résumé final avec liens

---

## Résumé final

```markdown
## Discovery Complete

### Documents générés
| Type | Fichier | Status |
|------|---------|--------|
| Brainstorm | docs/planning/brainstorms/BRAINSTORM-xxx.md | ✅/⏭️ |
| UX Design | docs/planning/ux/UX-xxx.md | ✅/⏭️ |
| PRD | docs/planning/prd/PRD-xxx.md | ✅ |
| UI Design | docs/planning/ui/UI-xxx.md | ✅/⏭️ |
| Architecture | docs/planning/architecture/ARCH-xxx.md | ✅/⏭️ |
| Stories | docs/stories/EPIC-xxx/ | ✅ |

### Issues GitHub
| Type | Count | Numéros |
|------|-------|---------|
| Epics | [X] | #[nums] |
| Stories | [X] | #[nums] |

### Prochaine étape
→ /dev #[première story P0]
```

---

## Démarrage

**Besoin à traiter :** $ARGUMENTS

Je commence par **Phase 1: Écoute & Analyse**.

Explique-moi ton besoin — parle comme tu veux, en mode speech-to-text, en bullet points, en paragraphes...
