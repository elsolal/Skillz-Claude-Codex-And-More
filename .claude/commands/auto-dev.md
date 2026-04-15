---
description: Développe une feature GitHub en mode RALPH autonome avec multi-agent parallèle (Explore → Plan orchestrateur → Code+Tests // → Review ×3 // → Ship). Usage: /auto-dev #123
---

# Auto-Dev - RALPH Mode

**Session ID:** ${CLAUDE_SESSION_ID}

## Mode RALPH + Multi-Agent activé

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      AUTO-DEV (RALPH MODE)                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  EXPLORE    →  PLAN          →  IMPLEMENT      →  REVIEW       → DONE  │
│  Subagent      Orchestrateur    ┌─ Code Agent     ┌─ Correctness       │
│  Explore       (TOI, ici)       └─ Test Agent     ├─ Readability       │
│  (AUTO)        PAS de Plan      (SUBAGENTS //)    └─ Performance       │
│                Mode                                (SUBAGENTS //)      │
│                                                                         │
│  Pas de validation intermédiaire - Full autonome                       │
└──────────────────────────────────────────────────────────────────────────┘
```

## Configuration RALPH

| Paramètre | Valeur |
|-----------|--------|
| Session | `${CLAUDE_SESSION_ID}` |
| Max iterations | **50** |
| Timeout | **2h** |
| Completion promise | **"DEV COMPLETE"** |
| Logs | `docs/ralph-logs/${CLAUDE_SESSION_ID}.md` |

## Phase 0: PRE-FLIGHT GATE (obligatoire)

**Avant toute exécution autonome, vérifier qu'on a un mandat clair.** RALPH ne code pas dans le vide.

### Règle

```
SI $ARGUMENTS contient une issue GitHub (#NUM ou URL gh)
  → vérifier l'existence : gh issue view <num>
  → continuer
SINON
  → chercher une spec : Glob "docs/planning/specs/*-<slug>-design.md"
  → SI trouvée :
      → lire le frontmatter
      → SI status: approved ET approved_by != ralph → continuer
      → SINON : ARRÊTER, demander approbation humaine
  → SINON : ARRÊTER
```

### Si le gate échoue (pas d'issue ni de spec approuvée)

Refuser l'exécution avec ce message :

```
❌ Pre-flight gate échoué : pas de mandat clair pour /auto-dev

RALPH refuse de coder en autonome sans :
  - une issue GitHub valide (#NUM ou URL), OU
  - une spec docs/planning/specs/<date>-<slug>-design.md avec :
      status: approved
      approved_by: <humain> (pas "ralph")

Options :
  1. /discovery <besoin>      → produit une spec à valider (recommandé)
  2. /auto-discovery <besoin> → produit une spec status:draft (humain valide ensuite)
  3. gh issue create          → crée une issue puis relance /auto-dev #NUM
  4. /auto-dev --allow-no-spec → bypass (PROTOTYPAGE UNIQUEMENT, log RALPH le marque non-recommandé)
```

### Override `--allow-no-spec`

Réservé au **prototypage rapide**. Le log RALPH `docs/ralph-logs/${CLAUDE_SESSION_ID}.md` doit explicitement contenir :

```
⚠️ Pre-flight gate bypassed via --allow-no-spec
   Reason: <user-provided or "no reason given">
   Risk: code produit sans validation préalable, à reviewer manuellement avant /ship
```

## Exécution automatique

### Phase 1: EXPLORE (Subagent)
- Lire et parser l'issue GitHub (`gh issue view`)
- Dispatcher un subagent Explore via `SendMessage` pour analyser le codebase
- Identifier fichiers à modifier, patterns, risques
- Récupérer la synthèse du subagent

### Phase 1.5: FRONTEND DETECTION (automatique)
- Détecter si la feature implique du travail frontend :
  - URL Figma dans l'issue ? → `get_design_context` pour récupérer le design
  - Fichiers impactés sont `.tsx/.jsx/.vue/.css` ou dans `components/` ?
  - `components/CLAUDE.md` existe ? → Lire pour connaître composants/tokens disponibles
  - `components.json` (shadcn) existe ?
- Si FRONTEND détecté : le plan intégrera réutilisation composants, tokens, Figma

### Phase 2: PLAN (Orchestrateur = TOI)
- **PAS de Plan Mode, PAS de subagent** — TOI tu planifies directement
- Tu as tout le contexte de Phase 1
- Créer le plan d'implémentation avec étapes atomiques
- Pour chaque étape : quoi, où (chemins absolus), comment, contraintes
- **Si FRONTEND :** spécifier quels composants réutiliser, quels tokens, mapping Figma si applicable
- TaskCreate si 2+ étapes
- Préparer les prompts COMPLETS et AUTONOMES pour les subagents
- Valider automatiquement (pas de STOP)

### Phase 3: IMPLEMENT (2 subagents parallèles)
- **Subagent Code** via `SendMessage(run_in_background: true)` :
  - Prompt COMPLET avec plan, fichiers, patterns, contraintes
  - Lint/types obligatoires après chaque modification
- **Subagent Tests** via `SendMessage(run_in_background: true)` :
  - Prompt COMPLET avec description feature et fichiers impactés
  - Priorités P0-P3, risk-based
- Les 2 subagents tournent en parallèle
- Au retour : vérifier conflits, lancer tests

### Phase 4: REVIEW (3 subagents parallèles)
- **Subagent Correctness** via `SendMessage(run_in_background: true)` :
  - Bugs, logique, sécurité, edge cases
  - Classifie : 🔴 Critical | 🟡 Medium | 🟢 Minor
- **Subagent Readability** via `SendMessage(run_in_background: true)` :
  - Nommage, structure, DRY, abstractions
- **Subagent Performance** via `SendMessage(run_in_background: true)` :
  - O(n²), re-renders, queries, memory leaks, caching
- Corriger automatiquement les issues 🔴 Critical (TOI, pas un subagent)
- Relancer les tests après corrections

### Phase 5: FINALIZE (verification-before-completion gate)

Référence : `.claude/knowledge/workflows/verification-matrix.md` (ligne `/auto-dev`).

Vérifs **obligatoires** avant de marquer "DEV COMPLETE" :

| Check | Commande | Statut |
|---|---|---|
| Lint | `npm run lint` (ou équivalent stack) | ✅ |
| Types | `npm run typecheck` | ✅ |
| Tests P0/P1 | `npm test -- --filter=p0,p1` (ou équivalent) | ✅ |
| Log RALPH cohérent | inspecter les 3 dernières itérations dans `docs/ralph-logs/${CLAUDE_SESSION_ID}.md` — pas de pattern d'erreur en boucle | ✅ |

**Si une vérif échoue :** ne pas marquer COMPLETE, créer une nouvelle itération RALPH pour corriger. Si > 3 tentatives → STOP avec message clair pour l'utilisateur.

Puis :
- **Si FRONTEND + nouveaux composants créés :** lancer `/ds-doc --update` automatiquement
- Créer un résumé des changements
- Préparer pour PR

## Critères de succès automatiques

Le loop considère la feature "COMPLETE" quand :
- Code implémenté selon le plan
- Tous les tests passent
- 3 passes de review effectuées via subagents
- Aucune issue 🔴 Critical restante

## Métriques RALPH

```markdown
## Métriques Feature

| Métrique | Valeur |
|----------|--------|
| **Durée totale** | [X]m [Y]s |
| **Itérations** | [N] / 50 |
| **Issue** | #[NUM] |

### Temps par phase
| Phase | Durée | Status |
|-------|-------|--------|
| Explore (subagent) | [X]m | ? |
| Plan (orchestrateur) | [X]m | ? |
| Code + Tests (subagents //) | [X]m | ? |
| Review ×3 (subagents //) | [X]m | ? |

### Code Metrics
| Métrique | Valeur |
|----------|--------|
| Fichiers créés | [X] |
| Fichiers modifiés | [X] |
| Lignes ajoutées | +[X] |
| Lignes supprimées | -[X] |

### Review Summary
| Pass | Issues trouvées | Issues résolues |
|------|-----------------|-----------------|
| Correctness | [X] | [X] |
| Readability | [X] | [X] |
| Performance | [X] | [X] |
```

## Arrêt manuel

```bash
/cancel-ralph
```

## Arguments supportés

| Argument | Description |
|----------|-------------|
| `#123` | Numéro d'issue GitHub |
| `URL` | URL complète de l'issue |
| `--max N` | Override max iterations (default: 50) |
| `--timeout Xh` | Override timeout (default: 2h) |
| `--verbose` | Mode debug avec logs détaillés |
| `--allow-no-spec` | Bypass Phase 0 pre-flight gate (PROTOTYPAGE UNIQUEMENT) |

---

## Démarrage

**Issue à implémenter :** $ARGUMENTS

### Initialisation RALPH

```json
{
  "active": true,
  "iteration": 1,
  "maxIterations": 50,
  "completionPromise": "DEV COMPLETE",
  "originalPrompt": "AUTO-DEV: Implement $ARGUMENTS using multi-agent workflow",
  "startTime": [TIMESTAMP],
  "timeoutSeconds": 7200,
  "logEnabled": true,
  "sessionId": "${CLAUDE_SESSION_ID}",
  "mode": "auto-dev"
}
```

Je commence par **Phase 1: EXPLORE** — lecture de l'issue et analyse du codebase...
