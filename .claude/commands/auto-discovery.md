---
description: Lance le workflow de planning complet en mode RALPH autonome (Brainstorm → PRD → Architecture → Stories). L'orchestrateur garde tout le contexte et travaille seul jusqu'à avoir créé toutes les issues GitHub.
---

# Auto-Discovery — RALPH Mode

**Session ID:** ${CLAUDE_SESSION_ID}

## Architecture Orchestrateur + RALPH

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTO-DISCOVERY (RALPH MODE)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ORCHESTRATEUR PRINCIPAL (TOI) — garde tout le contexte                     │
│                                                                             │
│  Écoute → Brainstorm → [UX] → PRD → [UI] → Architecture → Stories → GitHub│
│   AUTO      AUTO        AUTO   AUTO   AUTO     AUTO          AUTO     AUTO │
│                                                                             │
│  Pas de validation intermédiaire — Full autonome                           │
│  Seule la publication GitHub est dispatchée en subagent                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Configuration RALPH

| Paramètre | Valeur |
|-----------|--------|
| Session | `${CLAUDE_SESSION_ID}` |
| Max iterations | **30** |
| Timeout | **1h** |
| Completion promise | **"DISCOVERY COMPLETE"** |
| Logs | `docs/ralph-logs/${CLAUDE_SESSION_ID}.md` |

## Exécution automatique

**Principe clé :** TOI, l'orchestrateur principal, tu gardes tout le contexte à travers TOUTES les phases. Tu ne forks JAMAIS vers un skill. Tu suis le process directement. Tu dispatches uniquement la création d'issues GitHub via subagent.

### Phase 1: Écoute & Analyse
- Analyser le besoin de `$ARGUMENTS`
- Détecter automatiquement FULL vs LIGHT (score ≥ 3 critères = FULL)
- Pas de STOP, valider automatiquement

### Phase 2: Brainstorm (si FULL)
- Charger techniques : `Read .claude/knowledge/brainstorming/brain-techniques.csv`
- Choisir les techniques adaptées au contexte (mode AI-Recommended)
- Générer 20-30 idées (mode autonome = plus concis qu'interactif)
- Synthétiser : top 5 idées, direction choisie
- Évaluer scores UX/UI pour décider des phases optionnelles
- Sauvegarder : `docs/planning/brainstorms/BRAINSTORM-{slug}-{date}.md`
- Référence : `.claude/skills/idea-brainstorm/SKILL.md`

### Phase 3: UX Design (si score UX ≥ 4)
- Personas, user journeys, wireframes textuels
- Sauvegarder : `docs/planning/ux/UX-{slug}.md`
- Référence : `.claude/skills/ux-designer/SKILL.md`

### Phase 4: PRD
- Tu as tout le contexte (brainstorm + UX) — pas besoin de relire les fichiers
- Rédiger le PRD complet (FULL) ou simplifié (LIGHT)
- Sauvegarder : `docs/planning/prd/PRD-{slug}.md`
- Référence : `.claude/skills/pm-prd/SKILL.md`
- Knowledge : `.claude/knowledge/workflows/prd-template.md`, `domain-complexity.csv`

### Phase 5: UI Design (si score UI ≥ 3)
- Design system, composants, guidelines visuelles
- Sauvegarder : `docs/planning/ui/UI-{slug}.md`
- Référence : `.claude/skills/ui-designer/SKILL.md`

### Phase 6: Architecture (si FULL)
- Tu as TOUT le contexte — architecturer directement
- Analyser le codebase existant, proposer le stack, data model, APIs
- Sauvegarder : `docs/planning/architecture/ARCH-{slug}.md`
- Référence : `.claude/skills/architect/SKILL.md`

### Phase 7: Stories
- Découper en Epics + User Stories (INVEST, Given/When/Then)
- Implementation Readiness Check
- Sauvegarder : `docs/stories/EPIC-{num}-{slug}/`
- Référence : `.claude/skills/pm-stories/SKILL.md`

### Phase 7.5: Spec design (sortie obligatoire)

Produire une spec consolidée pour permettre `/auto-dev` ensuite :

- Fichier : `docs/planning/specs/YYYY-MM-DD-{slug}-design.md`
- Frontmatter **obligatoire** :
  ```yaml
  ---
  title: <Titre du besoin>
  status: draft           # ← TOUJOURS draft en sortie auto-discovery
  approved_by: ralph      # ← interdit pour /auto-dev tant qu'humain n'a pas validé
  approved_at: <ISO-8601>
  slug: <slug>
  related_pr: TBD
  ---
  ```
- Contenu : synthèse du PRD + architecture + décisions clés (3-5 sections max)
- Le statut `status: approved` doit être appliqué **par un humain**, jamais par RALPH

Cette spec sert de gate à `/auto-dev` (Phase 0 pre-flight). Sans validation humaine de cette spec, `/auto-dev` refusera de démarrer.

### Phase 8: Publication GitHub (subagent)
- Dispatcher un subagent via `SendMessage(run_in_background: true)` pour créer les issues
- Prompt complet avec tous les titres, bodies, labels
- Au retour : confirmer les issues créées

## Critères de succès automatiques

Le loop considère la discovery "COMPLETE" quand :
- Mode détecté et phases appropriées exécutées
- Documents générés et sauvegardés
- Stories découpées avec estimations
- Readiness Check score ≥ 13/15
- Issues GitHub créées

## Métriques RALPH

```markdown
## Métriques Discovery

| Métrique | Valeur |
|----------|--------|
| **Durée totale** | [X]m [Y]s |
| **Itérations** | [N] / 30 |
| **Mode détecté** | FULL / LIGHT |

### Temps par phase
| Phase | Durée | Status |
|-------|-------|--------|
| Analyse initiale | [X]m | ✅ |
| Brainstorm | [X]m | ✅/⏭️ |
| UX Design | [X]m | ✅/⏭️ |
| PRD | [X]m | ✅ |
| UI Design | [X]m | ✅/⏭️ |
| Architecture | [X]m | ✅/⏭️ |
| Stories | [X]m | ✅ |
| GitHub (subagent) | [X]m | ✅ |

### Documents générés
| Type | Fichier | Status |
|------|---------|--------|
| Brainstorm | BRAINSTORM-xxx.md | ✅/⏭️ |
| UX Design | UX-xxx.md | ✅/⏭️ |
| PRD | PRD-xxx.md | ✅ |
| UI Design | UI-xxx.md | ✅/⏭️ |
| Architecture | ARCH-xxx.md | ✅/⏭️ |
| Stories | EPIC-xxx/ | ✅ |

### Issues GitHub
| Type | Count | Numéros |
|------|-------|---------|
| Epics | [X] | #[nums] |
| Stories | [X] | #[nums] |
```

## Arrêt manuel

```bash
/cancel-ralph
```

## Arguments supportés

| Argument | Default | Description |
|----------|---------|-------------|
| `--max N` | 30 | Nombre max d'itérations |
| `--timeout Xh` | 1h | Timeout global |
| `--verbose` | false | Mode debug avec logs détaillés |

---

## Démarrage

**Besoin à traiter :** $ARGUMENTS

### Initialisation RALPH

```json
{
  "active": true,
  "iteration": 1,
  "maxIterations": 30,
  "completionPromise": "DISCOVERY COMPLETE",
  "originalPrompt": "AUTO-DISCOVERY: $ARGUMENTS",
  "startTime": "[TIMESTAMP]",
  "timeoutSeconds": 3600,
  "logEnabled": true,
  "sessionId": "${CLAUDE_SESSION_ID}",
  "mode": "auto-discovery"
}
```

Je commence l'analyse de ton besoin : **$ARGUMENTS**

Phase 1: Analyse du scope...
