---
name: a11y-enforcer
description: Audit accessibilité (WCAG 2.2 AA) sur URL ou code. Vérifie contrastes, ARIA roles, keyboard navigation, focus order, prefers-reduced-motion, alt text, semantic HTML, form labels. Output structuré avec sévérité, code de fix, et impact utilisateur. Utiliser dans /pr-review, /qa, ou avant /ship — risque légal réel (EAA EU 2025, ADA US, AODA Canada).
model: opus
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
user-invocable: true
argument-hint: <url-or-path>
---

# A11y Enforcer

Audit accessibilité systématique. Pas un nice-to-have — gate de compliance + UX réel.

## Pourquoi maintenant

- **EAA (EU)** : European Accessibility Act applicable depuis juin 2025 — produits B2C numériques en EU doivent être accessibles
- **ADA (US)** : interprété par les courts comme s'appliquant aux sites web depuis 2020 — class actions en hausse
- **AODA (Canada/Ontario)** : sites .ca commerciaux > certaines tailles obligés WCAG 2.0 AA
- **Risque marketing** : 1 utilisateur sur 6 a un handicap durable ou situationnel

## Skill Boundaries

- Audit uniquement (pas de fix automatique). Pour fix → output contient le code à appliquer.
- Pas d'audit visuel design (→ `taste-critic`)
- Pas d'audit perf (→ `performance-auditor`)
- Pas d'audit code quality (→ `code-reviewer`)
- Couvre WCAG 2.2 niveau AA (pas AAA, pas AA21)

## Inputs acceptés

| Input | Action |
|-------|--------|
| URL `https://...` | `WebFetch` + Playwright headless si dispo (axe-core, contrast checker) |
| Path code (`src/`, `app/`, `components/`) | `Glob` + `Read` + check statique des patterns |
| Composant unique (`Button.tsx`) | `Read` + check ciblé |

Si un rapport `design-audit` existe, reprendre ses findings P0/P1 a11y comme point de départ puis approfondir avec WCAG 2.2 AA. Si aucun rapport n'existe, l'audit reste autonome.

## Process

### 1. Inventaire

```markdown
♿ **A11y Enforcer**

**Input** : [URL/path]
**Scope** : [N pages / N composants détectés]
**Tools available** : [Playwright / axe-core / Pa11y / static-only]
```

### 2. Checks WCAG 2.2 AA — 8 catégories

#### A. Perceivable — Contrast (1.4.3 + 1.4.11)
- Texte normal : ratio ≥ 4.5:1
- Texte large (≥18pt ou ≥14pt bold) : ratio ≥ 3:1
- UI components et focus indicators : ratio ≥ 3:1
- ❌ Texte sur image/vidéo sans overlay garanti

**Comment vérifier** :
- Static : grep des combinaisons text-color × bg-color, calculer
- Dynamic : Playwright + axe-core sur chaque page

#### B. Perceivable — Alternative text (1.1.1)
- ❌ `<img>` sans `alt` (ou alt="" pour décoratif uniquement)
- ❌ Icons-only buttons sans `aria-label`
- ❌ SVG informatif sans `<title>` ou `aria-label`
- ❌ Background images informatives (devraient être `<img>`)

#### C. Operable — Keyboard (2.1.1 + 2.1.2)
- ❌ Composants custom (div + onClick) sans `role` + `tabindex` + handlers keyboard
- ❌ Focus traps (modal qui ne trap pas → focus continue derrière)
- ❌ Skip links absents (skip to main content)
- ❌ Tab order non-logique (tabindex > 0 utilisé)

#### D. Operable — Focus (2.4.7 + 2.4.11 — WCAG 2.2 nouvelle)
- ❌ `outline: none` sans replacement visible
- ❌ Focus indicator < 3:1 contraste avec adjacent
- ❌ Focus partiellement caché par éléments fixed (sticky header, etc.) — **WCAG 2.2 nouveau**
- ❌ Focus indicator < 2px d'épaisseur

#### E. Operable — Motion (2.3.3 + 2.2.2)
- ❌ Animations sans respect de `prefers-reduced-motion`
- ❌ Auto-play vidéo/carousel sans pause control
- ❌ Parallax extrême causant motion sickness
- ❌ Flash > 3 fois/seconde (seizure trigger)

#### F. Understandable — Forms (1.3.1 + 3.3.2)
- ❌ Inputs sans `<label>` associé (htmlFor / aria-labelledby)
- ❌ Erreurs de validation visuelles seules (couleur sans icône/texte)
- ❌ Required champs sans indication textuelle (juste l'astérisque rouge)
- ❌ Placeholders utilisés comme labels
- ❌ Touch targets < 24×24px — **WCAG 2.2 nouveau (2.5.8)**

#### G. Understandable — Language & content (3.1.1)
- ❌ `<html>` sans `lang="..."`
- ❌ Changements de langue inline sans `lang="..."`
- ❌ Acronymes sans `<abbr>` ou explication

#### H. Robust — Semantic HTML (4.1.2)
- ❌ `<div>` au lieu de `<button>` / `<a>` / `<nav>` / `<main>` / `<article>`
- ❌ Headings désordonnés (h1 → h3 → h2)
- ❌ Multiple `<h1>` par page
- ❌ Tables sans `<th>` / `scope`
- ❌ Listes faites avec `<div>` au lieu de `<ul>` / `<ol>`
- ❌ Attributs ARIA invalides ou redondants

### 3. Output structuré

```markdown
## ♿ A11y Audit Report

**Input** : [URL/path]
**WCAG version** : 2.2 AA
**Pages/components scanned** : [N]
**Total violations** : [N]
**Compliance score** : [X]% — **[Grade A/B/C/D/F]**

---

### Severity breakdown
- 🔴 P0 (blocker users from completing critical task) : [N]
- 🟠 P1 (frustrating but workable) : [N]
- 🟡 P2 (polish, edge cases) : [N]
- 🟢 P3 (best practice) : [N]

---

### Violations

#### 🔴 P0 — [Category, WCAG criterion]
**Where** : `components/Button.tsx:24` (or "Login page, submit button")
**What** : Icon-only button sans aria-label
**Who suffers** : Screen reader users — bouton annoncé "button" sans contexte
**Code current** :
```tsx
<button onClick={onSubmit}>
  <CheckIcon />
</button>
```
**Code fix** :
```tsx
<button onClick={onSubmit} aria-label="Submit form">
  <CheckIcon aria-hidden="true" />
</button>
```
**WCAG ref** : 1.1.1 Non-text Content (Level A) + 4.1.2 Name, Role, Value (Level A)

[répéter pour chaque violation]

---

### Auto-fixable (top 5)
Violations triviales qu'on peut fix en batch :
1. [3× missing alt text on decorative images → ajouter `alt=""`]
2. [2× missing lang on html → ajouter `lang="en"` (ou autre)]
3. ...

### Manual review needed
1. [Color contrast violations — nécessite décision design]
2. [Custom widgets sans rôle ARIA — refactor structurel]

---

### Next step
- [B] Apply auto-fixes en batch (les 5 ci-dessus)
- [M] Manual review des P0 (sourcing du design system)
- [R] Re-run après fixes pour valider
- [S] Skip (à tes risques — block /ship si Grade D/F)
```

## Règles

### Toujours
- ✅ Référencer le critère WCAG exact (ex: `2.4.7 Focus Visible (Level AA)`)
- ✅ Expliquer **qui** est impacté (screen reader / keyboard / low vision / etc.)
- ✅ Donner le code current + fix, pas juste une description
- ✅ Distinguer Level A (essentiel) de Level AA (cible)
- ✅ Localiser précisément (file:line ou page+region)

### Jamais
- ❌ Critiquer une règle Level AAA comme bloquante (overkill par défaut)
- ❌ Dupliquer ce que axe-core/Pa11y génèrent déjà — enrichir, pas répéter
- ❌ Ignorer les WCAG 2.2 nouveaux (2.4.11 Focus Not Obscured, 2.5.8 Target Size)
- ❌ "Add aria-label" sans dire **quel** label (donner le texte précis)

## Intégrations

| Workflow | Insertion |
|----------|-----------|
| `/pr-review` | 6e passe (après design-audit et taste-critic) — P0 = blocking |
| `/qa` | Catégorie "Accessibility" du health score |
| `/ship` | Gate STRICT : Grade D/F → confirm explicit avec la justification |
| `design-audit` | Sous-rapport approfondi pour l'axe A11y |
| `ui-designer` | Auto-trigger sur tokens couleurs (vérifier contraste) |
| `figma-implement-design` | Auto-trigger après implementation |
| Standalone | `a11y-enforcer <url-or-path>` |

## Tools fallback

Si pas de Playwright/axe-core/Pa11y disponibles :
- Static analysis only (grep patterns, contrast calc via Bash)
- Output explicit : "Static-only audit, dynamic checks recommandés via Playwright"
- Suggestion d'install :
  ```bash
  npm i -D @axe-core/cli playwright
  npx axe https://your-url.com --tags wcag2aa,wcag22aa --save report.json
  ```

## Output Validation

```markdown
### ✅ Checklist Output A11y Enforcer

| Critère | Status |
|---------|--------|
| WCAG version explicite (2.2 AA) | ✅/❌ |
| Score global + grade | ✅/❌ |
| Au moins 1 violation P0 localisée précisément | ✅/❌ |
| Chaque violation référence un critère WCAG numéroté | ✅/❌ |
| Code current + fix donnés | ✅/❌ |
| Auto-fixables séparés du manual | ✅/❌ |
| Tools dispo documentés | ✅/❌ |
```
