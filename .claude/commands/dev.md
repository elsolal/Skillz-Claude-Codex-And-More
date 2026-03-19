---
description: Lance le workflow multi-agent pour développer une feature. Explore → Plan (orchestrateur) → Code+Tests (subagents //) → Review ×3 (subagents //) → Ship. Usage: /dev [issue] ou /dev "description"
---

# Dev: Feature Implementation — $ARGUMENTS

## Workflow Multi-Agent

```
┌──────────────────────────────────────────────────────────────────────────┐
│  EXPLORE        PLAN            IMPLEMENT          REVIEW        SHIP   │
│  (subagent)   (orchestrateur)  (subagents //)    (subagents //)  (/ship)│
│                                                                         │
│  Subagent  →  L'orchestrateur →  ┌─ Code Agent  →  ┌─ Correctness  →  │
│  Explore      garde le contexte  └─ Test Agent     ├─ Readability     │
│               et planifie                           └─ Performance     │
│                                                                         │
│  [STOP]       [STOP]              [STOP]             [STOP]     [STOP] │
└──────────────────────────────────────────────────────────────────────────┘
```

**Principe clé :** L'orchestrateur principal (TOI) gardes tout le contexte. Tu ne délègues JAMAIS la planification. Tu dispatches uniquement l'exécution (code, tests, reviews) via des subagents.

---

## Phase 1: EXPLORE

Lancer un **subagent Explore** pour comprendre le codebase :

1. Utiliser `SendMessage` pour dispatcher un subagent avec comme prompt :
   - "Analyse le codebase pour comprendre comment implémenter **$ARGUMENTS**. Identifie : architecture, fichiers impactés, patterns existants, dépendances, risques. Retourne une synthèse structurée."
2. Récupérer et lire l'issue GitHub si `$ARGUMENTS` contient un numéro d'issue (`gh issue view`)
3. Quand le subagent revient : synthétiser requirements, fichiers à modifier, patterns à suivre

**STOP CHECKPOINT 1** — Présenter la synthèse. Validation avant de planifier.

---

## Phase 1.5: FRONTEND DETECTION (automatique, pas de stop)

Après l'explore, détecter si la feature implique du **travail frontend** :

### Signaux de détection

| Signal | Comment vérifier | Poids |
|--------|-----------------|-------|
| URL Figma dans l'issue | `Grep` le body de l'issue pour `figma.com/design/` | Fort |
| Fichiers à modifier sont `.tsx/.jsx/.vue/.css` | Résultat de l'Explore (fichiers impactés) | Fort |
| `components/CLAUDE.md` existe | `Glob: **/components/CLAUDE.md` | Fort |
| `components.json` (shadcn) existe | `Glob: components.json` | Moyen |
| Keywords dans l'issue | "écran", "page", "composant", "UI", "design", "formulaire", "layout" | Faible |

**Si 1+ signal fort ou 2+ signaux faibles → FRONTEND = true**

### Si FRONTEND détecté

Afficher dans la synthèse :

```markdown
🎨 **Frontend détecté**
- Composants existants : [lire components/CLAUDE.md si existe]
- Design Figma : [URL si trouvée dans l'issue, sinon "aucun"]
- Design System : [documenté / non documenté]

→ Le plan intégrera les étapes design (réutilisation composants, tokens, Figma)
```

**Si URL Figma trouvée :** appeler `get_design_context` pour récupérer le design et l'inclure dans le contexte du plan.

**Si `components/CLAUDE.md` existe :** le lire pour connaître les composants et tokens disponibles — le plan devra prioriser la réutilisation.

---

## Phase 2: PLAN (orchestrateur = TOI)

**PAS de Plan Mode, PAS de subagent.** C'est TOI, l'orchestrateur principal, qui planifies directement.

Tu as tout le contexte de la Phase 1. Avec ce contexte :

1. Créer un plan d'implémentation avec étapes atomiques
2. Pour chaque étape, définir :
   - **Quoi** : description précise de ce qu'il faut faire
   - **Où** : fichiers à créer/modifier (chemins absolus)
   - **Comment** : pattern à suivre, références au code existant
   - **Contraintes** : ce que le subagent ne doit PAS toucher
3. Si **2+ étapes** → créer des Tasks (`TaskCreate`) pour tracking
4. **Si FRONTEND :** ajouter au plan :
   - Quels composants existants réutiliser (depuis `components/CLAUDE.md`)
   - Quels tokens/variables CSS utiliser (jamais de valeurs hardcodées)
   - Si design Figma fourni : mapper les éléments Figma → composants code
   - Si nouveaux composants créés : noter pour `/ds-doc --update` en Phase 5
5. Préparer les prompts des subagents de Phase 3 (chaque prompt doit être COMPLET et AUTONOME)

**STOP CHECKPOINT 2** — Validation du plan avant implémentation.

---

## Phase 3: IMPLEMENT (2 subagents parallèles)

Dispatcher **2 subagents en parallèle** via `SendMessage` dans un seul message :

### Subagent 1 : Code
```
SendMessage(run_in_background: true)
Prompt: "Tu es un développeur senior. Implémente les changements suivants :

[PLAN DÉTAILLÉ avec fichiers, patterns, contraintes]

Règles :
- Respecte les conventions du projet (CLAUDE.md)
- Vérifie lint + types après chaque modification
- Ne touche PAS aux fichiers hors scope
- Si FRONTEND : réutilise les composants existants (components/CLAUDE.md), utilise les tokens CSS (jamais de hex/spacing hardcodés), respecte les patterns de composition
- Résume ce que tu as fait à la fin (+ liste des nouveaux composants créés si frontend)

Knowledge refs: .claude/knowledge/testing/error-handling.md, feature-flags.md"
```

### Subagent 2 : Tests
```
SendMessage(run_in_background: true)
Prompt: "Tu es un Test Architect. Écris les tests pour la feature suivante :

[DESCRIPTION FEATURE + FICHIERS IMPLÉMENTÉS]

Règles :
- Priorités P0-P3, risk-based
- Pattern Arrange-Act-Assert
- Naming: should_[comportement]_when_[condition]
- Pas de hard waits, pas de flaky
- Résume ce que tu as fait à la fin

Knowledge refs: .claude/knowledge/testing/test-levels-framework.md,
test-priorities-matrix.md, test-quality.md, data-factories.md,
fixture-architecture.md, network-first.md, component-tdd.md,
test-healing-patterns.md, selector-resilience.md"
```

> **Note :** Si la feature est simple (1 seule étape), les 2 subagents peuvent être fusionnés en un seul.

Quand les 2 subagents reviennent :
1. Vérifier qu'il n'y a pas de conflits de fichiers
2. Vérifier que les tests passent (`npm test` ou équivalent)
3. Résoudre les problèmes si nécessaire

**STOP CHECKPOINT 3** — Vérifier que code + tests passent. Validation.

---

## Phase 4: REVIEW (3 subagents parallèles)

Dispatcher **3 subagents review en parallèle** via `SendMessage` dans un seul message :

### Subagent Correctness
```
SendMessage(run_in_background: true)
Prompt: "Tu es un reviewer expert en correctness. Review les changements suivants :

[git diff des fichiers modifiés]

**Focus CORRECTNESS :**
- Logique métier correcte
- Edge cases gérés (null, undefined, empty, boundary)
- Pas de bugs, race conditions, data loss
- Types corrects, pas de any non justifié
- Failles de sécurité (injection, XSS, auth bypass)
- Tests couvrent les changements

Classifie chaque issue :
- 🔴 Critical : bugs, failles sécurité, data loss → Fix obligatoire
- 🟡 Medium : performance, code smells → Fix recommandé
- 🟢 Minor : style, nommage → Nice-to-have

Output : table Sévérité | Fichier | Ligne | Issue | Suggestion

Knowledge: .claude/knowledge/testing/error-handling.md, risk-governance.md,
probability-impact.md"
```

### Subagent Readability
```
SendMessage(run_in_background: true)
Prompt: "Tu es un reviewer expert en lisibilité. Review les changements suivants :

[git diff des fichiers modifiés]

**Focus READABILITY :**
- Nommage clair et cohérent (verbNoun fonctions, noun variables)
- Fonctions de taille raisonnable (< 20 lignes)
- Commentaires utiles (logique complexe uniquement)
- Structure logique, early return
- Pas de code dupliqué (DRY)
- Abstractions appropriées (pas d'over-engineering)

Output : table Type | Fichier | Suggestion | Impact

Knowledge: .claude/knowledge/testing/test-quality.md, nfr-criteria.md"
```

### Subagent Performance
```
SendMessage(run_in_background: true)
Prompt: "Tu es un reviewer expert en performance. Review les changements suivants :

[git diff des fichiers modifiés]

**Focus PERFORMANCE :**
- Opérations O(n²) évitables
- Re-renders inutiles (si React/frontend)
- Queries optimisées (si DB) — N+1, missing indexes
- Memory leaks (event listeners, subscriptions)
- Lazy loading si pertinent
- Caching si pertinent

Output : table Type | Impact estimé | Effort | Suggestion

Knowledge: .claude/knowledge/testing/nfr-criteria.md"
```

Quand les 3 subagents reviennent :
1. **Synthétiser** les 3 rapports en un rapport consolidé
2. **Corriger** les issues 🔴 Critical (toi-même, pas un subagent — tu as le contexte)
3. **Relancer les tests** après corrections

**STOP CHECKPOINT 4** — Présenter le résumé review consolidé. Validation.

---

## Phase 5: SHIP

1. Vérifier que tous les tests passent après corrections review
2. **Si FRONTEND + nouveaux composants créés :**
   - Proposer `/ds-doc --update` pour mettre à jour la documentation design system
   - Mentionner les composants à lier dans Figma si pas encore liés
3. Proposer : **[S] /ship** (merge main, tests, review, changelog, PR) | **[D] /ds-doc --update puis ship** | **[C] Commit seulement** | **[R] Réviser encore**
4. Si l'utilisateur choisit [S] ou [D], lancer le workflow correspondant

---

## Démarrage

Issue à traiter : **$ARGUMENTS**

Je commence par **Phase 1: EXPLORE**.
