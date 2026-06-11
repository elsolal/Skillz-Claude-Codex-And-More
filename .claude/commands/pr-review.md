---
description: Review une Pull Request GitHub avec 3 passes core, plus gates design/a11y si UI et SEO/GEO si surface publique. Usage: /pr-review #123 ou URL.
---

# PR Review (Multi-Agent)

**PR demandée : $ARGUMENTS**

## Chargement du contexte

1. `gh pr view $ARGUMENTS --json number,title,body,state,author,files,reviews`
2. `gh pr diff $ARGUMENTS --name-only` (fichiers modifiés)
3. `gh pr diff $ARGUMENTS` (diff complet)

---

## Détection scope UI (pour passes 4-6)

Avant de dispatcher : grep le diff pour détecter du UI/frontend changé :
- Patterns : `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.html`, `*.css`, `*.scss`, `*styled*`, `tailwind`, `figma`
- Si UI détecté → activer passes 4 (Design Audit), 5 (Design / taste-critic) et 6 (A11y / a11y-enforcer)
- Sinon → skip ces 3 passes (3 passes classiques uniquement)

## Détection scope SEO/GEO (pour pass 7)

Avant de dispatcher : grep le diff pour détecter une surface publique indexable :
- Patterns : `robots.txt`, `sitemap.*`, `llms.txt`, `metadata`, `schema`, `json-ld`, `.mdx`, blog, docs, landing, homepage, pages service, title/meta/H1/canonical/FAQ
- Si SEO/GEO détecté → activer pass 7 (`seo-geo-audit`)
- Sinon → skip cette passe

---

## Review parallèle (3 core + passes optionnelles)

Dispatcher **3 subagents core**, puis ajouter les subagents UI et/ou SEO/GEO si les détections ci-dessus sont positives :

### Subagent 1 : Correctness
```
SendMessage(run_in_background: true)
Prompt: "Tu es un reviewer expert en correctness. Review cette PR.

Diff fourni : [diff]

**Focus CORRECTNESS :**
- Logique métier correcte
- Edge cases gérés (null, undefined, empty, boundary)
- Pas de bugs, race conditions, data loss
- Types corrects
- Failles de sécurité (injection, XSS, auth bypass)
- Tests couvrent les changements

Classifie chaque issue : 🔴 Critical | 🟡 Medium | 🟢 Minor
Output : table Sévérité | Fichier | Ligne | Issue | Suggestion

Knowledge: .claude/knowledge/testing/error-handling.md, risk-governance.md, probability-impact.md"
```

### Subagent 2 : Readability
```
SendMessage(run_in_background: true)
Prompt: "Tu es un reviewer expert en lisibilité. Review cette PR.

Diff fourni : [diff]

**Focus READABILITY :**
- Nommage clair et cohérent
- Fonctions de taille raisonnable
- Commentaires utiles (logique complexe uniquement)
- Structure logique, early return
- Pas de code dupliqué (DRY)
- Abstractions appropriées

Output : table Type | Fichier | Suggestion | Impact

Knowledge: .claude/knowledge/testing/test-quality.md, nfr-criteria.md"
```

### Subagent 3 : Performance
```
SendMessage(run_in_background: true)
Prompt: "Tu es un reviewer expert en performance. Review cette PR.

Diff fourni : [diff]

**Focus PERFORMANCE :**
- O(n²) évitables
- Re-renders inutiles (si frontend)
- Queries optimisées (si DB) — N+1, missing indexes
- Memory leaks (event listeners, subscriptions)
- Lazy loading si pertinent
- Caching si pertinent

Output : table Type | Impact | Effort | Suggestion

Knowledge: .claude/knowledge/testing/nfr-criteria.md"
```

### Subagent 4 : Design Audit (uniquement si UI changé)
```
SendMessage(run_in_background: true)
Prompt: "Tu es design-audit. Audit transversal de cette PR.

Diff frontend fourni : [diff filtré aux fichiers UI]
Preview URL / Figma / paths : [si disponibles]

**Invoquer le skill `design-audit`** et appliquer les axes :
Tokens, Components, A11y, Taste, Figma/code drift, AI surface & governance.

Pour chaque finding :
- Localisation précise (file:line ou surface)
- Axe
- Sévérité P0-P3
- Fix concret
- Si Lyse est utile et disponible, l'utiliser comme preuve statique optionnelle

Output : rapport Design Audit.

P0 = blocking. P1 = blocking en ship-gate sauf justification explicite."
```

### Subagent 5 : Design Quality (uniquement si UI changé)
```
SendMessage(run_in_background: true)
Prompt: "Tu es taste-critic. Audit anti-slop de cette PR.

Diff frontend fourni : [diff filtré aux fichiers UI]
Style direction (si connu via PRD/UI doc) : [taste / soft / minimalist / brutalist / etc.]

**Invoquer le skill `taste-critic`** et appliquer ses 8 catégories :
Typography, Spacing & Layout, Hierarchy, Motion, Color & Contrast, Copy, Density, Composition.

Pour chaque violation :
- Localisation précise (file:line)
- Sévérité P0-P3
- Référence à la règle source (quel taste-skill, quelle section)
- Fix concret

Output : rapport hiérarchisé selon le format taste-critic.

Si aucune violation P0+P1 → Approve côté goût.
Si P0 détecté → Block + suggérer redesign-skill pour fix."
```

### Subagent 6 : Accessibility (uniquement si UI changé)
```
SendMessage(run_in_background: true)
Prompt: "Tu es a11y-enforcer. Audit WCAG 2.2 AA de cette PR.

Diff frontend fourni : [diff filtré aux fichiers UI]

**Invoquer le skill `a11y-enforcer`** et appliquer les 8 catégories :
Contrast, Alt text, Keyboard, Focus, Motion (reduced-motion), Forms, Language, Semantic HTML.

Pour chaque violation :
- Localisation (file:line)
- Critère WCAG numéroté (ex: 2.4.7 Focus Visible Level AA)
- Qui est impacté (screen reader / keyboard / low vision / etc.)
- Code current + code fix

Output : rapport selon le format a11y-enforcer, séparant auto-fixables vs manual.

P0 = blocking pour /ship (compliance EAA EU 2025 + ADA US)."
```

### Subagent 7 : SEO/GEO Audit (uniquement si surface publique indexable changée)
```
SendMessage(run_in_background: true)
Prompt: "Tu es seo-geo-audit. Audit SEO/GEO de cette PR.

Diff public/SEO fourni : [diff filtré aux fichiers publics/meta/schema/content]
Preview URL / paths : [si disponibles]

**Invoquer le skill `seo-geo-audit`** et appliquer les axes :
Technique, On-page, Keywords/intent, Content SEO/GEO, Autorité/local, Visibilité IA, Cohérence.

Pour chaque finding :
- Localisation précise
- Sévérité P0-P3
- Statut de preuve : Confirmé / Déduit / Non vérifié
- Fix concret
- Double-check obligatoire avant toute affirmation négative

Output : rapport SEO/GEO Audit.

P0 = blocking. P1 = blocking en ship-gate sauf justification explicite."
```

---

## Synthèse

Après les 3 subagents, produire le rapport consolidé :

```markdown
## PR Review: #[NUM] - [Titre]

### Résumé
- **Status**: Approved | Changes Requested | Blocked
- **Files reviewed**: X
- **Issues found**: X critical, X medium, X minor

### Pass 1: Correctness
| Sévérité | Fichier | Ligne | Issue | Suggestion |
|----------|---------|-------|-------|------------|

### Pass 2: Readability
| Type | Fichier | Suggestion |
|------|---------|------------|

### Pass 3: Performance
| Type | Impact | Effort | Suggestion |
|------|--------|--------|------------|

### Pass 4: Design Audit (si UI)
| Sévérité | Axe | Fichier | Issue | Fix |
|----------|-----|---------|-------|-----|
**Verdict** : [Ship-ready | Fix P0/P1 first | Needs design loop]

### Pass 5: Design Quality (si UI)
| Sévérité | Catégorie | Fichier | Violation | Fix | Règle |
|----------|-----------|---------|-----------|-----|-------|
**Grade global** : [A/B/C/D/F]

### Pass 6: Accessibility (si UI)
| Sévérité | WCAG | Fichier | Qui impacté | Fix |
|----------|------|---------|-------------|-----|
**Compliance score** : [X]% — Grade [A/B/C/D/F]

### Pass SEO/GEO: SEO/GEO Audit (si public/indexable)
| Sévérité | Axe | Fichier | Statut preuve | Issue | Fix |
|----------|-----|---------|---------------|-------|-----|
**Verdict** : [Ship-ready | Fix P0/P1 first | Needs SEO/GEO loop]

### Verdict
[Commentaire global et recommandation]
[Si Pass 4 bloque, Pass 5/6 = Grade D/F, ou Pass SEO/GEO bloque → bloquant pour /ship]
```

---

## Démarrage

**PR à reviewer :** $ARGUMENTS

Je récupère les infos de la PR puis lance les 3 subagents review en parallèle...
