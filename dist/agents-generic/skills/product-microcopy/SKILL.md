---
name: product-microcopy
description: Écrit la microcopy in-product — empty states, error messages, tooltips, button labels, confirmation dialogs, validation messages, success toasts, onboarding hints. Concis, action-oriented, anti-jargon. Voice and tone consistency. Utiliser pour SaaS, dashboards, apps, et toute UI où le copy court fait la différence UX.
model: opus
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
user-invocable: true
---

# Product Microcopy

La microcopy = les 3-15 mots qui apparaissent partout dans l'UI. Souvent négligée. Souvent ce qui distingue un produit qui se sent pro d'un qui se sent AI-généré.

## Scope

**Couvert** :
- Empty states (when there's nothing yet)
- Error messages (validation + system + recovery)
- Tooltips & helper text
- Button labels & action text
- Confirmation dialogs (destructive actions)
- Success toasts & notifications
- Form validation
- Loading states (when long)
- Onboarding hints & first-run UX
- Pagination, filters, sort labels

**Non-couvert** :
- Landing page copy (→ `landing-copy`)
- Long-form (blog, docs, marketing pages)
- AI-specific UI states (→ `ai-native-ui`)

## Voice & Tone (default)

Sauf si le brief impose un autre voice :

- **Direct** : pas de "We're sorry but..." (juste l'info + l'action)
- **Action-oriented** : verbe d'abord ("Save changes", "Delete project")
- **Concis** : si on peut couper 50% sans perdre de sens, on coupe
- **Specific** : "0 invoices" plutôt que "Nothing here yet"
- **Empathique sans flagornerie** : pas de "Awesome!", "Yay!", emoji surenchère
- **Same-language consistency** : si l'app dit "Project", elle ne dit pas "Workspace" ailleurs pour la même chose

## Anti-patterns à BANNIR

### Mots interdits
- "Oops!", "Whoops!", "Uh oh!" (infantilise)
- "Awesome!", "Yay!", "Hooray!", "Great!" (faux enthousiasme)
- "Just" ("Just click here") — minimise abusivement
- "Simply" ("Simply enter your email") — pareil, condescendant
- "Please" excessif (1-2 fois ok dans toute l'app, pas partout)
- "Sorry" excessif (réservé aux vraies fautes système)
- "Currently", "Actually", "Basically" (filler)
- "Friend", "Buddy", "Champ" (faux familier)

### Patterns interdits
- ❌ Empty states "No items found" (sans CTA pour en créer)
- ❌ Errors "Something went wrong. Please try again later." (vague + non-actionable)
- ❌ Tooltips qui répètent le label du bouton ("Settings — Open settings")
- ❌ Buttons "OK" / "Cancel" sur confirmations (utiliser "Delete project" / "Keep project")
- ❌ Validation "Invalid input" (dire **pourquoi** : "Email must include @")
- ❌ Success "Success!" (dire **quoi** : "Project created")
- ❌ Loading "Loading..." indéfini (préférer "Loading 12 of 50 invoices")
- ❌ Onboarding 8 étapes obligatoires before usage (max 2-3, skip toujours visible)

## Patterns à FAVORISER

### Empty states

**Structure** : `[ce qui manque + pourquoi c'est ok] + [action concrète + CTA]`

**Bons** :
- "No invoices yet — Create your first one to start tracking payments. **[Create invoice]**"
- "0 results for 'foobar' — Try a different keyword or **[clear filters]**"
- "Your team is just you for now — **[Invite teammates]** to collaborate"

**Mauvais** :
- "Nothing here yet" (sans CTA)
- "It's pretty quiet here..." (faux ton)
- "Oops, no items found!" (no Oops)

### Errors — typology

| Type | Format | Exemple |
|------|--------|---------|
| **Validation field** | `[Champ] [contrainte concrète]` | "Email must include @" / "Password ≥ 8 characters" |
| **Validation submit** | `[N] [problème] — [détail]` | "3 fields need attention — see below" |
| **System recoverable** | `[Ce qui s'est passé] — [action recovery]` | "Couldn't save — check your connection and **[retry]**" |
| **System non-recoverable** | `[Ce qui s'est passé] — [next step humain]` | "Server error (500). Our team is notified. Try again in a few minutes." |
| **Permission denied** | `[Action] requires [permission/role]` | "Deleting projects requires admin access. **[Request access]**" |
| **Rate limit** | `[Limit] [reset time]` | "API limit reached. Resets in 12 minutes." |
| **Quota exceeded** | `[Quota] [upgrade/wait]` | "Storage full (5 GB / 5 GB). **[Upgrade]** or delete files." |

### Tooltips

**Règle** : ne JAMAIS dupliquer le label visible. Ajouter info utile.

**Bons** :
- Bouton "Export" → tooltip "Export as CSV (max 10k rows)"
- Icon trash → tooltip "Move to trash (recoverable for 30 days)"
- Bouton "Sync" → tooltip "Last synced 3 minutes ago"

**Mauvais** :
- Bouton "Settings" → tooltip "Settings" (redondant)
- Icon ? → tooltip "Help" (vague)

### Confirmations destructives

**Pattern** : remplacer "OK / Cancel" par les **actions concrètes**.

**Bon** :
```
⚠️ Delete "Q3 Report" ?
This will permanently remove the project and 24 files. This cannot be undone.

  [Cancel]   [Delete project]
```

**Mauvais** :
```
Are you sure?
This action cannot be undone.

  [Cancel]   [OK]
```

### Success toasts

**Format** : `[Ce qui s'est passé] [optionnel: undo/view]`

**Bons** :
- "Invoice sent to alice@acme.com — **[Undo]** (10s)"
- "Project archived — **[View archived]**"
- "5 contacts imported"

**Mauvais** :
- "Success!"
- "Done!"
- "Awesome, your invoice was sent!" (verbeux + Awesome)

### Loading states

| Durée prévue | Pattern |
|--------------|---------|
| < 1s | Pas de loading visible (désactiver le bouton suffit) |
| 1-3s | Spinner + texte action ("Saving...") |
| 3-10s | Spinner + texte + ETA si possible ("Processing... ~5s") |
| > 10s | Progress bar + count ("Importing 247 of 1,250 contacts") |
| > 30s | Progress + cancel option + email-when-done option |

### Onboarding & first-run

- ✅ Max 2-3 steps obligatoires (le reste = optional/skippable)
- ✅ "Skip" toujours visible (même si discret)
- ✅ Empty states = mini-onboarding par contexte
- ✅ Tooltips contextuels (1 par feature découverte) > tour 8-steps imposé
- ❌ Pas de checklist "10 steps to unlock your account"
- ❌ Pas de modal qui bloque l'usage du produit

### Form validation

- ✅ Inline (sous le champ), apparaît au blur (pas au keystroke)
- ✅ Action-oriented : "Add an @ to make this a valid email"
- ✅ Symbole + couleur + texte (pas couleur seule pour a11y)
- ❌ "Invalid" (sans dire pourquoi)
- ❌ "Required" (utiliser plutôt "Please add a [thing]" ou marquer en amont)
- ❌ Tout valider en même temps après submit (frustrant si plusieurs erreurs)

## Process

### 1. Audit existant (si projet brownfield)

```bash
# Find all microcopy candidates in code
grep -rE '(toast|alert|message|placeholder|label|tooltip|empty)' src/ --include="*.tsx" --include="*.jsx" -l
```

```markdown
🧐 **Microcopy Audit**

**Project** : [name]
**Files scanned** : [N]
**Microcopy candidates found** : [N]

**Quick stats** :
- Empty states : [N] (X% have CTA)
- Error messages : [N] (X% are typed)
- Tooltips : [N] (X% redundant with label)
- Confirmations : [N] (X% use OK/Cancel vs concrete actions)

**Top violations** : [list 5-10]
```

### 2. Voice & tone definition (si projet greenfield)

```markdown
🎙️ **Voice & Tone Sheet**

**Voice** (qui on est, ne change pas) :
- [adjectif 1] — ex: "direct"
- [adjectif 2] — ex: "knowledgeable"
- [adjectif 3] — ex: "human, not corporate"

**Tone** (selon contexte, varie) :
| Context | Tone |
|---------|------|
| Errors | Calm, helpful, no blame |
| Success | Brief, no fanfare |
| Onboarding | Encouraging, never pushy |
| Destructive | Serious, clear consequences |
| Empty states | Inviting, action-oriented |

**Specific rules** :
- Never use : [list of banned words for this brand]
- Always use : [terminology — "project" not "workspace", "team" not "org", etc.]
- Punctuation : [periods at end of empty state text? At end of buttons? Decide once.]
```

### 3. Generate microcopy library

Produire un fichier `docs/planning/copy/microcopy-{slug}.md` :

```markdown
# Microcopy Library — [Project]

## Empty states

### Projects list — empty
"No projects yet — Create one to organize your work. **[Create project]**"

### Search — no results
"No results for '{query}' — Try a different keyword or **[clear filters]**"

[etc.]

## Errors

### Validation — Email
"Email must include @"

### Validation — Password
"Password ≥ 8 characters"

[etc.]

## Tooltips

### Sync button
"Last synced {N} {minutes/hours} ago"

[etc.]

## Confirmations

### Delete project
**Title**: Delete "{name}" ?
**Body**: This will permanently remove the project and all its files. This cannot be undone.
**Cancel button**: Cancel
**Confirm button**: Delete project

[etc.]
```

### 4. Validation

```markdown
### ✅ Checklist Microcopy

| Critère | Status |
|---------|--------|
| Aucun mot interdit (Oops, Awesome, Just, Sorry excessif) | ✅/❌ |
| Empty states ont tous un CTA | ✅/❌ |
| Errors typés (validation / system / permission / etc.) | ✅/❌ |
| Tooltips n'ont aucune redondance avec le label | ✅/❌ |
| Confirmations destructives utilisent actions concrètes (pas OK/Cancel) | ✅/❌ |
| Success toasts disent QUOI s'est passé | ✅/❌ |
| Voice cohérent (même terminologie partout) | ✅/❌ |
| Loading states adaptés à la durée prévue | ✅/❌ |
| Onboarding ≤ 3 steps obligatoires | ✅/❌ |
```

## Intégrations

| Workflow | Insertion |
|----------|-----------|
| `ui-designer` | Auto-trigger après définition des composants — pour générer la microcopy library |
| `pm-prd` | Mention dans la phase UX/UI — capturer voice/tone dès le PRD |
| `figma-implement-design` | Loader ce skill si Figma a `Lorem ipsum` ou copy générique |
| `code-implementer` | Reference les patterns lors d'écriture de UI |
| `taste-critic` | Cross-check : si taste-critic flag du copy générique, déléguer fix ici |

## Sources / inspiration

- Mailchimp Content Style Guide
- Microsoft Writing Style Guide
- Linear writing (in-product)
- Stripe Dashboard microcopy
- "Strategic Writing for UX" — Torrey Podmajersky
