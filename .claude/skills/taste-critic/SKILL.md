---
name: taste-critic
description: Audit anti-slop d'une UI frontend (URL, screenshot, ou code) contre les règles des 9 taste-skills. Détecte les défauts génériques de l'AI (6-line wraps, gapless bento absent, motion plate, hierarchy molle, copy générique, density déséquilibrée). Output structuré avec sévérité P0-P3 et fix suggéré. Utiliser dans /pr-review (3e passe design), /qa, ou avant /ship pour gate la qualité visuelle.
model: opus
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
user-invocable: true
argument-hint: <url-or-path-or-screenshot>
---

# Taste Critic

Miroir des 9 `taste-skills` : ils disent **comment générer du bon goût**, ce skill détecte **où le mauvais goût a survécu**.

## Quand utiliser

- 3e passe design dans `/pr-review` (après Correctness/Readability/Performance)
- Gate visuelle avant `/ship`
- Audit de design dans `/qa` (couplé au health score)
- Standalone pour critiquer une PR/preview/screenshot d'inspiration

## Skill Boundaries

- Audit uniquement, **ne fix pas**. Pour fix → invoquer `redesign-skill` ou le `taste-skill` correspondant.
- Pas d'audit a11y (→ `a11y-enforcer`).
- Pas d'audit perf (→ `performance-auditor`).
- Pas d'audit code quality (→ `code-reviewer`).

## Inputs acceptés

| Input | Action |
|-------|--------|
| URL `https://...` | `WebFetch` + screenshot via Playwright/Chrome MCP si dispo |
| Path code (`src/`, `app/`, `components/`) | `Glob` + `Read` les fichiers UI (.tsx, .jsx, .vue, .svelte, .html, .css) |
| Path screenshot (`.png`, `.jpg`, `.webp`) | `Read` direct (multimodal) |
| Sélection Figma (si MCP connecté) | `get_design_context` via figma MCP |

## Process

### 1. Charger le contexte

```markdown
🔍 **Taste Critic**

**Input** : [URL/path/screenshot]
**Style attendu** : [détecté ou demandé — taste / soft / minimalist / brutalist / autre]
**Dials de référence** : DESIGN_VARIANCE=[X] / MOTION_INTENSITY=[Y] / VISUAL_DENSITY=[Z]
```

Si pas de style attendu, demander ou inférer depuis un PRD/UI doc existant via `Glob: docs/planning/{prd,ui}/*.md`.

Si un rapport `design-audit` existe dans la session ou le repo, le réutiliser pour tokens/components/Figma/a11y et concentrer `taste-critic` sur le jugement visuel. Sinon, noter `Design audit: not run` sans bloquer l'audit.

### 2. Audit en 8 catégories

Pour chaque catégorie, scorer 0-10 et lister les violations concrètes :

#### A. Typography
- ❌ H1 wrappant sur 6+ lignes (cause : container trop étroit)
- ❌ Échelle typographique compressée (h1=24px, h2=20px, h3=18px → manque contraste)
- ❌ Line-height ≥1.5 sur les headings (devrait être 1.0-1.2)
- ❌ Font weight uniform partout (pas de hiérarchie en weight)
- ❌ Inter / Helvetica / system-ui sans personnalité custom
- ❌ Texte body justify-aligned ou centered sur paragraphes longs
- ❌ Letter-spacing 0 sur uppercase (devrait être 0.05em+)

#### B. Spacing & Layout
- ❌ Bento grid avec gaps visibles (devrait être gapless ou très serré)
- ❌ Padding sections < 80px en desktop (devrait être 120-200px)
- ❌ Container max-width 1200px par défaut (often safer = 1280-1440 ou full-bleed)
- ❌ Vertical rhythm cassé (espacements incohérents entre sections)
- ❌ Composants dans des cards qui flottent sans connexion structurelle

#### C. Hierarchy
- ❌ Tous les éléments à la même importance visuelle
- ❌ CTA secondaires aussi voyants que le primary
- ❌ Pas d'eyebrow / kicker au-dessus des H1
- ❌ Labels meta type "SECTION 01" / "QUESTION 05" (cheap)
- ❌ Z-axis flat (aucune ombre / blur layer / depth)

#### D. Motion
- ❌ Aucune animation (UI statique)
- ❌ Animations linéaires (pas d'easing custom)
- ❌ Hover transitions instantanées (transition: none)
- ❌ Pas de scroll-triggered behavior
- ❌ Pas de magnetic/proximity effects
- ❌ Animations qui ignorent `prefers-reduced-motion`

#### E. Color & Contrast
- ❌ Palette default Tailwind (slate-900, blue-600 plain)
- ❌ Aucun accent color custom
- ❌ Surfaces toutes blanches/noires sans nuance
- ❌ Gradients défauts (linear 45deg blue→purple)
- ❌ Pas de palette warm monochrome cohérente
- ❌ Boutons disabled invisibles (contraste < 3:1)

#### F. Copy
- ❌ "Discover our amazing features"
- ❌ Verbes faibles : "explore", "leverage", "unlock", "experience"
- ❌ H1 vagues sans sujet + bénéfice mesurable
- ❌ CTAs génériques "Get started", "Learn more"
- ❌ Placeholders "Lorem ipsum" laissés
- ❌ Microcopy IA générée (longs paragraphes corporate)

#### G. Density (selon VISUAL_DENSITY)
- Si DENSITY 1-3 : violations = trop dense (spacing < 64px, content au-dessus du fold dépassant)
- Si DENSITY 4-6 : violations = soit trop spacieux, soit trop dense
- Si DENSITY 7-10 : violations = trop spacieux (whitespace inutile, scroll excessif)

#### H. Composition (selon DESIGN_VARIANCE)
- Si VARIANCE 1-3 : violations = asymétries non-intentionnelles, hierarchy désalignée
- Si VARIANCE 7-10 : violations = symétrie ennuyeuse, blocs identiques répétés, layouts Left/Right en boucle

### 3. Output structuré

```markdown
## 🔍 Taste Critic Report

**Input** : [URL/path]
**Audited against** : `[taste-skill / soft-skill / etc.]`
**Overall score** : [X]/80 — **[Grade A/B/C/D/F]**

---

### Severity breakdown
- 🔴 P0 (broken/embarrassing) : [N]
- 🟠 P1 (visible to user) : [N]
- 🟡 P2 (polish) : [N]
- 🟢 P3 (nit) : [N]

---

### Violations

#### 🔴 P0 — [Catégorie]
**Where** : `path/to/file.tsx:42` ou "Hero section, screenshot region (X,Y)"
**What** : H1 wrappe sur 7 lignes — container `max-w-md` (448px) sur 92px de font-size
**Why it's slop** : signature défaut LLM "narrow container default"
**Fix** : `max-w-4xl` minimum + `text-balance`, ou réduire à 64px font-size
**Reference rule** : `taste-skill` — Typography section "Ban 6-line headings"

[répéter pour chaque violation]

---

### Quick wins (top 3)
1. [Le fix avec le ratio impact/effort le meilleur]
2. ...
3. ...

---

### Pas un problème (false-positives évités)
- [Si le brief demandait DENSITY=9, ne pas critiquer la densité]
- [Si VARIANCE=2 demandé, ne pas critiquer la symétrie]

---

### Next step
- [F] Lancer `redesign-skill` pour corriger automatiquement
- [T] Lancer `taste-skill` (ou variant) pour ré-implémenter from scratch
- [I] Iterate manuellement sur les 3 quick wins
- [P] Pause — exporter le rapport
```

## Règles d'audit

### Toujours
- ✅ Référencer la règle source (quel taste-skill, quelle section)
- ✅ Localiser précisément (file:line ou screenshot region)
- ✅ Donner un fix concret (code ou direction), pas juste "améliorer"
- ✅ Distinguer **intentionnel vs défaut** (un CTA secondaire discret peut être voulu)
- ✅ Respecter les dials du brief (un design DENSITY=9 ne doit pas être critiqué pour densité)

### Jamais
- ❌ Critiquer sans référence à une règle écrite
- ❌ "It's ugly" sans dire pourquoi mécaniquement
- ❌ Dupliquer ce que `code-reviewer` ou `a11y-enforcer` font déjà
- ❌ Inventer des violations (false positives) — silence > spéculation

## Auto-Chain

```markdown
## 🔗 Prochaine étape

✅ Audit terminé : [Grade], [N] violations P0+P1.

[Si Grade D ou F]
→ ⚠️ Bloquant pour ship. Lancer `redesign-skill` ?

[Si Grade C]
→ 🟡 Acceptable mais améliorable. Top 3 quick wins ci-dessus, lancer `redesign-skill` sur P0 ?

[Si Grade A ou B]
→ ✅ Ship-ready côté goût. Continuer `/ship` ?

---

**[F] Fix auto** | **[I] Iterate manuel** | **[S] Skip et ship** | **[P] Pause**
```

## Intégrations

| Workflow | Insertion point |
|----------|-----------------|
| `/pr-review` | 5e passe (après Design Audit) — flag P0 = blocking |
| `/qa` | Ajout au health score (catégorie "Visual Quality") |
| `/ship` | Gate optionnel : si Grade D/F détecté → confirm explicit |
| `design-audit` | Sous-rapport qualitatif pour l'axe Taste |
| Standalone | `taste-critic <url-or-path>` |

## Output Validation

```markdown
### ✅ Checklist Output Taste Critic

| Critère | Status |
|---------|--------|
| Style de référence identifié | ✅/❌ |
| Score global calculé | ✅/❌ |
| Au moins 1 violation localisée précisément (file:line ou region) | ✅/❌ |
| Chaque violation a un fix concret | ✅/❌ |
| Top 3 quick wins listés | ✅/❌ |
| Auto-chain proposé selon le grade | ✅/❌ |
```
