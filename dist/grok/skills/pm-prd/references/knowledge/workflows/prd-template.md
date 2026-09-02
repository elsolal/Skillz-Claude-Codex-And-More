---
stepsCompleted: []
inputDocuments: []
workflowType: 'prd'
lastStep: 0
---

# Product Requirements Document - {{project_name}}

**Author:** {{user_name}}
**Date:** {{date}}
**Version:** 1.0
**Mode:** {{FULL | LIGHT}}

---

## 1. Executive Summary

### Vision
> Une phrase décrivant la vision du produit.

### Proposition de valeur
> "Pour [persona], qui [problème], notre produit [solution] contrairement à [alternatives]."

### Objectifs

| Objectif | Métrique | Cible |
|----------|----------|-------|
| Objectif 1 | Métrique mesurable | Valeur cible |
| Objectif 2 | Métrique mesurable | Valeur cible |

---

## 2. Problème

### Contexte
Décrire le contexte et pourquoi ce problème existe.

### Personas

#### Persona 1: [Nom]
- **Rôle:**
- **Pain points:**
  - Point 1
  - Point 2
- **Quote:** "Citation représentative"

### Jobs to be Done
1. **Quand** [situation], **je veux** [action], **pour** [bénéfice]
2. ...

---

## 3. Solution

### Description
Description de la solution proposée.

### Différenciateurs

| Feature | Nous | Concurrent A | Concurrent B |
|---------|------|--------------|--------------|
| Feature 1 | ✅ | ❌ | ⚠️ |
| Feature 2 | ✅ | ✅ | ❌ |

---

## 4. Scope

### In Scope (MVP)
- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

### Out of Scope (v1)
- [ ] Feature future 1
- [ ] Feature future 2

### Future (v2+)
- Feature envisagée 1
- Feature envisagée 2

---

## 5. User Stories Summary

### Epic 1: [Nom de l'Epic]

| Story | Priorité | Taille | Description |
|-------|----------|--------|-------------|
| Story 1.1 | P0 | M | Description courte |
| Story 1.2 | P1 | S | Description courte |

### Epic 2: [Nom de l'Epic]
...

---

## 6. Data Model (si applicable)

```typescript
interface Entity {
  id: string;
  field1: string;
  field2: number;
  created_at: Date;
}
```

---

## 7. Exigences non-fonctionnelles

| Catégorie | Exigence | Cible |
|-----------|----------|-------|
| Performance | Temps de chargement | < Xs |
| Sécurité | Authentification | Standard |
| Accessibilité | WCAG | AA |
| Disponibilité | Uptime | 99.X% |

---

## 8. Risques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Risque 1 | Low/Medium/High | Low/Medium/High | Action de mitigation |

---

## 9. Timeline

| Phase | Durée | Livrables |
|-------|-------|-----------|
| Phase 1 | Xj | Livrable 1 |
| Phase 2 | Xj | Livrable 2 |
| **Total** | **Xj** | |

---

## 10. Critères de succès

- [ ] Critère 1
- [ ] Critère 2
- [ ] Critère 3

---

## Annexes

### A. Références
- Lien vers brainstorm
- Lien vers research

### B. Glossaire
| Terme | Définition |
|-------|------------|
| Terme 1 | Définition |
