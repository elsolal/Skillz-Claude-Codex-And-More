# Template Stories

> Template pour les Epics et User Stories générées par le skill `pm-stories`.

## Structure Epic

```markdown
---
epic_id: EPIC-{num}
title: [Titre de l'Epic]
status: draft | ready | in_progress | done
priority: P0 | P1 | P2
stories_count: X
---

# EPIC-{num}: [Titre de l'Epic]

## Description
[Description de l'Epic - le "quoi" et le "pourquoi"]

## Objectifs
- [ ] [Objectif 1]
- [ ] [Objectif 2]
- [ ] [Objectif 3]

## Stories incluses
| ID | Story | Priorité | Estimation | Status |
|----|-------|----------|------------|--------|
| STORY-001 | [Titre] | P0 | M | draft |
| STORY-002 | [Titre] | P0 | S | draft |
| STORY-003 | [Titre] | P1 | L | draft |

## Critères de succès de l'Epic
- [ ] [Critère mesurable 1]
- [ ] [Critère mesurable 2]

## Dépendances
- Epic précédente : [EPIC-X] (si applicable)
- Externe : [Dépendance externe]

## Risques identifiés
| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| [Risque 1] | Medium | High | [Action] |
```

---

## Structure User Story

```markdown
---
epic: EPIC-{num}
story_id: STORY-{num}
title: [Titre court]
priority: P0 | P1 | P2
estimation: XS | S | M | L | XL
status: draft | ready | in_progress | review | done
assignee: (optionnel)
---

# STORY-{num}: [Titre de la Story]

## User Story

**En tant que** [persona/rôle utilisateur],
**je veux** [action/fonctionnalité souhaitée],
**afin de** [bénéfice/valeur obtenue].

## Contexte

[Contexte technique ou business pertinent]
[Lien vers la section d'architecture si applicable]
[Décisions techniques (ADR) liées]

## Critères d'acceptance

### AC1: [Nom du critère]
- **Given** [contexte initial / préconditions]
- **When** [action effectuée par l'utilisateur]
- **Then** [résultat attendu / postconditions]

### AC2: [Nom du critère]
- **Given** [contexte]
- **When** [action]
- **Then** [résultat]

### AC3: [Nom du critère]
- **Given** [contexte]
- **When** [action]
- **Then** [résultat]

## Tâches techniques

- [ ] [Tâche 1 - ex: Créer le composant X]
- [ ] [Tâche 2 - ex: Ajouter l'endpoint API Y]
- [ ] [Tâche 3 - ex: Écrire les tests pour Z]
- [ ] [Tâche 4 - ex: Mettre à jour la documentation]

## Maquettes / Wireframes

[Lien ou description des maquettes si applicable]

## Notes techniques

- [Note importante 1]
- [Contrainte technique]
- [Point d'attention]

## Dépendances

- **Bloqué par** : STORY-XXX (si applicable)
- **Bloque** : STORY-YYY (si applicable)
- **Liée à** : STORY-ZZZ (si applicable)

## Definition of Done

- [ ] Code implémenté selon les standards du projet
- [ ] Tests unitaires écrits (coverage > 80%)
- [ ] Tests d'intégration si applicable
- [ ] Gate file PASS (ou waiver explicite)
- [ ] Documentation mise à jour
- [ ] Pas de régression sur les tests existants
- [ ] Déployé en staging et validé
```

---

## Critères INVEST

Chaque story doit respecter les critères INVEST :

| Critère | Description | Check |
|---------|-------------|-------|
| **I**ndependent | Peut être développée indépendamment | La story n'a pas de dépendance bloquante |
| **N**egotiable | Peut être discutée et ajustée | Les détails peuvent évoluer |
| **V**aluable | Apporte de la valeur à l'utilisateur | Le "afin de" est clair et mesurable |
| **E**stimable | Peut être estimée | L'équipe comprend le scope |
| **S**mall | Assez petite (< 2 jours) | Si > L, découper |
| **T**estable | Peut être testée | Les AC sont vérifiables |

---

## Grille d'estimation

| Taille | Durée | Complexité | Exemple |
|--------|-------|------------|---------|
| **XS** | < 2h | Triviale | Fix typo, config change |
| **S** | 2-4h | Simple | CRUD basique, 1-2 fichiers |
| **M** | 4-8h | Modérée | Feature standard, plusieurs fichiers |
| **L** | 1-2j | Complexe | Feature avec logique métier complexe |
| **XL** | > 2j | Très complexe | **À découper obligatoirement** |

---

## Priorités

| Priorité | Critères | Exemples |
|----------|----------|----------|
| **P0** | Revenue-critical, Security, Data integrity | Paiement, Auth, RGPD |
| **P1** | Core user journeys, Features principales | Onboarding, Dashboard |
| **P2** | Features secondaires, Améliorations | Settings, Export |
| **P3** | Nice-to-have, Cosmétique | Animations, Easter eggs |

---

## Template GitHub Issue

```markdown
## User Story

**En tant que** [persona],
**je veux** [action],
**afin de** [bénéfice].

## Critères d'acceptance

- [ ] **AC1**: Given [contexte], When [action], Then [résultat]
- [ ] **AC2**: Given [contexte], When [action], Then [résultat]
- [ ] **AC3**: Given [contexte], When [action], Then [résultat]

## Tâches

- [ ] [Tâche 1]
- [ ] [Tâche 2]
- [ ] [Tâche 3]

## Notes

- [Note importante]

## Definition of Done

- [ ] Code implémenté
- [ ] Tests écrits et passent
- [ ] Code review OK
- [ ] Documentation à jour

---
Part of #[EPIC_NUMBER]
Estimation: [XS/S/M/L]
Priority: [P0/P1/P2]
```

---

## Checklist de qualité

### Pour chaque Story
- [ ] Respecte INVEST
- [ ] User Story complète (En tant que / Je veux / Afin de)
- [ ] Au moins 2 critères d'acceptance en Given/When/Then
- [ ] Estimation ≤ L (sinon découper)
- [ ] Tâches techniques listées
- [ ] Definition of Done claire

### Pour chaque Epic
- [ ] Description claire du périmètre
- [ ] Stories découpées logiquement
- [ ] Priorités cohérentes
- [ ] Dépendances identifiées
- [ ] Critères de succès mesurables
