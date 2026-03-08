---
name: orchestrate
description: Decompose un objectif haut-niveau en taches independantes et les execute en agents paralleles. Utiliser quand l'utilisateur dit "orchestrer", "fais tout ca en parallele", "multi-agent", "lance plusieurs agents", "decompose et execute", ou donne un objectif complexe avec 3+ sous-taches independantes.
---

# Orchestrateur Multi-Agent

Decompose un objectif en taches independantes, les dispatche en agents paralleles, et aggrege les resultats.

## Quand utiliser

- Objectif avec 3+ sous-taches independantes
- Taches sans dependances entre elles (pas de state partage)
- Chaque tache peut etre completee par un agent isole
- L'utilisateur veut aller vite en parallelisant

## Quand NE PAS utiliser

- Taches sequentielles avec dependances
- Une seule tache simple
- Besoin de contexte partage entre les taches
- Code qui modifie les memes fichiers

## Processus

```
OBJECTIF → DECOMPOSE → VALIDE → DISPATCHE → MONITORE → AGREGE → RAPPORTE
```

### Etape 1 : Analyser l'objectif

Comprendre ce que l'utilisateur veut accomplir. Identifier :
- Les sous-taches naturelles
- Les dependances entre elles
- Les taches parallelisables vs sequentielles

### Etape 2 : Decomposer

Creer une liste de taches avec pour chacune :
- **Nom** : identifiant court
- **Description** : ce que l'agent doit faire (precis, actionnable)
- **Scope** : fichiers/repertoires concernes
- **Contraintes** : ce que l'agent ne doit PAS toucher
- **Output attendu** : ce que l'agent doit retourner

### Etape 3 : Valider avec l'utilisateur

Presenter la decomposition et demander confirmation AVANT de dispatcher.
Format :

```
## Plan d'orchestration

Objectif: [objectif]

| # | Tache | Type | Scope |
|---|-------|------|-------|
| 1 | ... | Agent (background) | ... |
| 2 | ... | Agent (background) | ... |
| 3 | ... | Agent (sequentiel apres 1+2) | ... |

Dependances: Tache 3 depend de 1 et 2
Estimation: ~X agents en parallele

Lancer ?
```

### Etape 4 : Dispatcher

Utiliser le tool `Agent` avec `run_in_background: true` pour les taches independantes.

**Regles critiques :**
- TOUJOURS creer un fichier de state AVANT de dispatcher :

```
~/.claude/orchestration-state.json
{
  "objective": "...",
  "started_at": "ISO timestamp",
  "tasks": [
    {
      "id": 1,
      "name": "...",
      "status": "running|completed|failed",
      "agent_id": "...",
      "result_summary": null
    }
  ]
}
```

- Lancer les taches independantes en UN SEUL message (multiple Agent tool calls)
- Chaque agent recoit un prompt COMPLET et AUTONOME (pas de references a d'autres agents)
- Chaque prompt inclut : contexte, objectif precis, fichiers concernes, contraintes, format de retour attendu

### Etape 5 : Aggreger

Quand tous les agents ont termine :
1. Lire les resultats de chaque agent
2. Verifier les conflits potentiels (memes fichiers modifies)
3. Si conflits : resoudre manuellement ou dispatcher un agent de merge
4. Mettre a jour le state file

### Etape 6 : Rapporter

Presenter un resume structure :

```
## Resultats d'orchestration

Objectif: [objectif]
Duree: Xm
Agents: N lances, N completes, N echoues

| # | Tache | Status | Resume |
|---|-------|--------|--------|
| 1 | ... | OK | ... |
| 2 | ... | OK | ... |
| 3 | ... | FAIL | ... |

### Actions restantes
- [si des taches ont echoue]
```

## Patterns de prompts pour agents

### Agent de recherche/exploration
```
Tu es un agent de recherche. Ton objectif :
[objectif precis]

Scope : [fichiers/repertoires]
Contraintes : NE MODIFIE AUCUN FICHIER. Recherche seulement.

Retourne :
- Ce que tu as trouve
- Fichiers pertinents avec chemins absolus
- Recommandations
```

### Agent d'implementation
```
Tu es un agent d'implementation. Ton objectif :
[objectif precis]

Contexte : [contexte necessaire]
Fichiers a modifier : [liste]
Contraintes : NE TOUCHE PAS aux fichiers hors scope.

Etapes :
1. Lis les fichiers concernes
2. Implemente les changements
3. Verifie que ca compile/lint
4. Resume ce que tu as fait

Retourne : Resume des changements avec fichiers modifies
```

### Agent de review
```
Tu es un agent de code review. Ton objectif :
Reviewer les changements dans [scope].

Criteres :
1. Correctness : bugs, edge cases
2. Readability : clarte, nommage
3. Performance : complexite, N+1

Retourne : Liste des issues trouvees (CRITICAL/WARNING/INFO)
```

## Garde-fous

- **Max 6 agents en parallele** (au-dela = diminishing returns + risque de conflits)
- **Jamais 2 agents sur les memes fichiers** (conflit garanti)
- **Toujours valider la decomposition** avec l'utilisateur en mode manuel
- **State file obligatoire** avant le dispatch
- **En cas d'echec** : ne pas re-dispatcher automatiquement, analyser d'abord
- **Taches sequentielles** : les chainer, pas les paralleliser

## Integration avec CMUX

Pour les taches TRES longues (>30 min estimees), preferer CMUX :
1. Creer un teammate via le menu Claude Code
2. Lui envoyer le prompt via team inbox
3. Monitorer via tmux

Pour les taches moyennes (<30 min) : Agent tool avec `run_in_background: true`
Pour les taches courtes (<5 min) : Agent tool en foreground
