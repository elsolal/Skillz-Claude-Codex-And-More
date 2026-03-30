---
name: ds-doc
description: Scanne le projet et génère/met à jour la section Design System dans CLAUDE.md. Documente tokens, composants UI, composants métier, patterns et règles. Lie chaque élément à son fichier code ET son URL Figma. Utiliser quand l'utilisateur dit "documenter le design system", "ds-doc", "mettre à jour le CLAUDE.md design", ou après avoir ajouté/modifié des composants UI.
model: opus
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - mcp__plugin_figma_figma__get_metadata
  - mcp__plugin_figma_figma__get_design_context
  - mcp__plugin_figma_figma__get_variable_defs
  - mcp__plugin_figma_figma__search_design_system
argument-hint: [--figma <url>] [--update]
user-invocable: true
---

# DS-Doc — Design System Documenter

Scanne un projet et génère la section `## Design System` dans le `CLAUDE.md` projet, pour que Claude puisse toujours réutiliser les composants et tokens existants.

## Principes

- **Le CLAUDE.md est la source de vérité pour Claude** — tout ce qu'on veut que Claude utilise doit y être
- **Lier code ET Figma** — chaque composant pointe vers son fichier ET son URL Figma
- **Concis mais complet** — tables, pas de prose. Claude a besoin de trouver vite
- **Idempotent** — relancer `/ds-doc` met à jour la section sans dupliquer

---

## Phase 0 — Collecter le contexte Figma

> **TOUJOURS demander l'URL Figma avant de commencer le scan.**

```markdown
🎨 **DS-Doc — Design System Documenter**

Avant de scanner le projet, j'ai besoin de lier ton design system à Figma.

**URL(s) Figma du design system :**
- [ ] URL du fichier principal (composants/tokens) : `figma.com/design/...`
- [ ] URL d'un fichier secondaire (optionnel) : `figma.com/design/...`
- [ ] Pas de Figma pour ce projet → je documente uniquement le code

Colle l'URL ou tape [S] pour skip Figma.
```

**⏸️ STOP** — Attendre l'URL ou le skip

Si URL fournie :
1. Extraire `fileKey` de l'URL
2. Appeler `get_metadata` pour récupérer le nom du fichier et la structure des pages
3. Appeler `get_variable_defs` pour récupérer les tokens existants
4. Stocker le `fileKey` pour construire les liens composants plus tard

---

## Phase 1 — Scan du projet

Scanner dans cet ordre, **en parallèle** quand possible :

### 1.1 Stack & config

| Cible | Action |
|-------|--------|
| `package.json` | `Read` — détecter : react, next, vue, tailwindcss, shadcn, radix, etc. |
| `tailwind.config.*` | `Glob` + `Read` — tokens custom (colors, spacing, borderRadius, fontFamily) |
| `src/styles/globals.css` ou `app/globals.css` | `Glob` + `Read` — CSS variables (--primary, --radius, etc.) |
| `components.json` | `Read` — config shadcn (style, rsc, aliases) |
| `figma.config.json` | `Read` — Code Connect existant (optionnel) |

### 1.2 Composants UI (base)

```bash
Glob: src/components/ui/**/*.{tsx,jsx,vue}
# ou : components/ui/**/*.{tsx,jsx,vue}
```

Pour chaque composant trouvé :
- Nom du composant (PascalCase)
- Fichier relatif
- `Grep` pour les variants/props exportées (chercher `variant`, `cva(`, `VariantProps`)
- Usage principal (1 ligne)

### 1.3 Composants métier

```bash
Glob: src/components/**/*.{tsx,jsx,vue}
# Exclure: src/components/ui/
```

Pour chaque composant :
- Nom
- Fichier relatif
- Rôle (inféré du nom + contenu)

### 1.4 Figma mapping (si URL fournie)

Pour les composants clés, chercher leur correspondance Figma :
1. Vérifier si Code Connect existe (`figma.config.json`) → mapper automatiquement
2. Sinon, utiliser `get_design_context` avec le `fileKey` pour trouver les composants Figma par nom
3. Utiliser `search_design_system` pour trouver les composants par nom dans les libraries
4. Construire l'URL Figma : `figma.com/design/{fileKey}/?node-id={nodeId}`

---

## Phase 2 — Générer la section CLAUDE.md

### Format de sortie

```markdown
## Design System

### Figma
- **Fichier principal** : [Nom du fichier](URL Figma)
- **Fichier secondaire** : [Nom](URL) _(optionnel)_

### Stack UI
- Framework: Next.js / React / Vue
- Styling: Tailwind CSS + CSS Variables (oklch)
- Composants: shadcn/ui (Radix primitives)
- Icônes: lucide-react
- Fonts: Geist Sans (UI) + Geist Mono (code)

### Tokens
Définis dans `tailwind.config.ts` et `app/globals.css`.

| Token | Variable CSS | Usage |
|-------|-------------|-------|
| Primary | `--primary` | CTA, actions principales |
| Secondary | `--secondary` | Actions secondaires |
| Muted | `--muted` | Fonds désactivés, texte secondaire |
| Destructive | `--destructive` | Suppression, erreurs |
| Radius | `--radius` | Border radius global |
| ... | ... | ... |

### Composants UI (`src/components/ui/`)
TOUJOURS réutiliser avant d'en créer un nouveau.

| Composant | Fichier | Figma | Variants | Quand utiliser |
|-----------|---------|-------|----------|----------------|
| Button | `button.tsx` | [→](figma-url) | default, secondary, destructive, outline, ghost, link | Actions |
| Card | `card.tsx` | [→](figma-url) | — | Container de contenu |
| Dialog | `dialog.tsx` | [→](figma-url) | — | Modales |
| ... | ... | ... | ... | ... |

### Composants métier (`src/components/`)

| Composant | Fichier | Figma | Usage |
|-----------|---------|-------|-------|
| AppHeader | `app-header.tsx` | [→](figma-url) | Header global avec nav + user menu |
| ... | ... | ... | ... |

### Patterns de composition

- **Page layout** : `<main className="container mx-auto py-6 space-y-6">`
- **Section** : `<Card>` avec `CardHeader` + `CardContent`
- **Formulaire** : `Form` + `FormField` + zod schema
- **Liste dense** : `Table` / Liste sparse : grid de `Card`
- **Action destructive** : `AlertDialog` obligatoire
- **Loading** : `Skeleton` qui mirror la forme du contenu
- **Empty state** : illustration + texte + CTA dans `Card`
- **Responsive** : mobile-first, breakpoints Tailwind (sm/md/lg/xl)

### Règles Design System

- JAMAIS de couleurs/spacing hardcodés → utiliser les tokens
- JAMAIS créer un composant UI si un shadcn existe → `npx shadcn@latest add <component>`
- TOUJOURS un état loading + empty + error pour les vues data
- TOUJOURS vérifier la responsive de chaque nouveau composant
- Typo : font-sans pour l'UI, font-mono pour code/IDs/timestamps
- Dark mode : supporté via `className="dark"` sur `<html>`
```

---

## Phase 2.5 — Générer le CLAUDE.md détaillé dans components/

> **Le CLAUDE.md racine est un index concis. Le `components/CLAUDE.md` est la référence complète.**
> Claude le lit quand il travaille dans `components/` — il a alors tout le détail sans polluer le CLAUDE.md racine.

Créer (ou mettre à jour) le fichier `src/components/CLAUDE.md` (ou `components/CLAUDE.md` selon la structure projet).

### Format de sortie

```markdown
# Design System — Référence détaillée

> Ce fichier est la doc complète du design system pour Claude.
> Généré par `/ds-doc`. Relancer `/ds-doc --update` pour mettre à jour.

## Figma

| Fichier | URL | Usage |
|---------|-----|-------|
| [Nom fichier principal] | `figma.com/design/{fileKey}/...` | Composants + tokens |
| [Nom fichier secondaire] | `figma.com/design/{fileKey}/...` | Screens / prototypes |

---

## Tokens & Variables

### Couleurs

| Token | Variable CSS | Valeur | Figma Variable | Usage |
|-------|-------------|--------|----------------|-------|
| Primary | `--primary` | `oklch(...)` | `colors/primary` [→](figma-url) | CTA, liens, focus rings |
| Primary foreground | `--primary-foreground` | `oklch(...)` | `colors/primary-foreground` [→](figma-url) | Texte sur primary |
| Secondary | `--secondary` | `oklch(...)` | `colors/secondary` [→](figma-url) | Boutons secondaires |
| Destructive | `--destructive` | `oklch(...)` | `colors/destructive` [→](figma-url) | Erreurs, suppression |
| Muted | `--muted` | `oklch(...)` | `colors/muted` [→](figma-url) | Fonds désactivés |
| Background | `--background` | `oklch(...)` | `colors/background` [→](figma-url) | Fond de page |
| Card | `--card` | `oklch(...)` | `colors/card` [→](figma-url) | Fond des cards |
| Border | `--border` | `oklch(...)` | `colors/border` [→](figma-url) | Bordures |
| ... | ... | ... | ... | ... |

### Spacing

| Token Tailwind | Valeur | Figma Variable | Usage |
|---------------|--------|----------------|-------|
| `space-1` | 4px | `spacing/xs` [→](figma-url) | Micro-gaps |
| `space-2` | 8px | `spacing/sm` [→](figma-url) | Gaps serrés |
| `space-4` | 16px | `spacing/md` [→](figma-url) | Gap standard |
| `space-6` | 24px | `spacing/lg` [→](figma-url) | Sections |
| ... | ... | ... | ... |

### Typography

| Token | Font | Size | Weight | Figma Style | Usage |
|-------|------|------|--------|-------------|-------|
| `text-sm` | Geist Sans | 14px | 400 | `Body/Small` [→](figma-url) | Labels, captions |
| `text-base` | Geist Sans | 16px | 400 | `Body/Regular` [→](figma-url) | Corps de texte |
| `text-lg` | Geist Sans | 18px | 600 | `Heading/H4` [→](figma-url) | Sous-titres |
| `text-xl` | Geist Sans | 20px | 600 | `Heading/H3` [→](figma-url) | Titres de section |
| `font-mono` | Geist Mono | — | — | `Code` [→](figma-url) | Code, IDs, timestamps |
| ... | ... | ... | ... | ... | ... |

### Radius & Shadows

| Token | Variable CSS | Valeur | Figma | Usage |
|-------|-------------|--------|-------|-------|
| `rounded-sm` | — | 4px | `radius/sm` [→](figma-url) | Badges, chips |
| `rounded-md` | `--radius` | 6px | `radius/md` [→](figma-url) | Boutons, inputs |
| `rounded-lg` | — | 8px | `radius/lg` [→](figma-url) | Cards |
| `shadow-sm` | — | `0 1px 2px ...` | `elevation/sm` [→](figma-url) | Hover léger |
| `shadow-md` | — | `0 4px 6px ...` | `elevation/md` [→](figma-url) | Cards surélevées |

---

## Composants UI

### Button (`ui/button.tsx`)

**Figma** : [Button](figma-component-url)

| Variant | Classe | Quand utiliser |
|---------|--------|----------------|
| `default` | `bg-primary text-primary-foreground` | Action principale, CTA |
| `secondary` | `bg-secondary text-secondary-foreground` | Action secondaire |
| `destructive` | `bg-destructive text-destructive-foreground` | Suppression, danger |
| `outline` | `border border-input bg-background` | Action neutre |
| `ghost` | `hover:bg-accent` | Action tertiaire, menus |
| `link` | `text-primary underline` | Navigation inline |

| Size | Classe | Dimensions |
|------|--------|-----------|
| `sm` | `h-8 px-3 text-xs` | 32px height |
| `default` | `h-9 px-4 py-2` | 36px height |
| `lg` | `h-10 px-8` | 40px height |
| `icon` | `h-9 w-9` | Carré, icône seule |

**Props** : `variant`, `size`, `asChild`, `disabled`
**Dépendances** : Radix Slot, class-variance-authority

---

### Card (`ui/card.tsx`)

**Figma** : [Card](figma-component-url)

| Sub-composant | Usage |
|---------------|-------|
| `Card` | Container avec border + radius + shadow |
| `CardHeader` | Titre + description en haut |
| `CardTitle` | Titre (h3) |
| `CardDescription` | Sous-titre muted |
| `CardContent` | Corps du contenu |
| `CardFooter` | Actions en bas (flex row) |

**Pattern type** :
```tsx
<Card>
  <CardHeader>
    <CardTitle>Titre</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>...</CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

---

### [Répéter pour chaque composant UI scanné]

---

## Composants métier

### AppHeader (`app-header.tsx`)

**Figma** : [Header](figma-component-url)
**Rôle** : Header global de l'application
**Contient** : Logo, navigation principale, user menu (dropdown)
**Props** : `user`, `navigation`

### [Répéter pour chaque composant métier scanné]

---

## Composants manquants (à implémenter)

> Liste des composants présents dans Figma mais pas encore dans le code.

| Composant Figma | Page | Node URL | Priorité |
|----------------|------|----------|----------|
| [Nom composant] | [Page Figma] | [→](figma-url) | P0/P1/P2 |
| ... | ... | ... | ... |
```

### Règles de génération

- Pour chaque composant UI, lire le fichier source et extraire :
  - Les variants (chercher `cva(`, `variants:`, `VariantProps`)
  - Les sizes (chercher `size:`)
  - Les props exportées (chercher `interface.*Props` ou `type.*Props`)
  - Les sub-composants (chercher les exports nommés)
- Pour les tokens, extraire les valeurs réelles depuis `globals.css` et `tailwind.config`
- Pour les liens Figma, chercher dans Code Connect ou mapper par nom de composant
- La section "Composants manquants" compare Figma vs code et liste ce qui reste à implémenter

---

## Phase 3 — Insérer dans CLAUDE.md

### Si section `## Design System` existe déjà :
- **Remplacer** la section entière (de `## Design System` jusqu'au prochain `## `)
- Préserver tout le reste du fichier

### Si pas de section :
- **Insérer** après `# Project Rules` si cette section existe
- Sinon insérer en début de fichier, après le frontmatter éventuel

### Validation :

```markdown
✅ **DS-Doc terminé**

**Fichiers générés/mis à jour :**
1. `CLAUDE.md` (racine) → section `## Design System` (index concis)
2. `src/components/CLAUDE.md` → référence détaillée (tokens, props, variants, patterns, liens Figma)

**Résumé :**
- **Stack** : [détecté]
- **Tokens** : [X] couleurs, [X] spacing, [X] typo, [X] radius
- **Composants UI** : [X] composants (shadcn)
- **Composants métier** : [X] composants
- **Figma** : [X] composants liés / [X] sans lien
- **Patterns** : [X] patterns documentés
- **Manquants** : [X] composants dans Figma mais pas dans le code

Composants sans lien Figma :
- [ ] ComponentA — ajouter le lien manuellement ou lancer `/figma-setup`
- [ ] ComponentB

**Prochaine étape ?**
- [F] `/figma-setup` — Configurer Code Connect pour le mapping automatique
- [U] `/ds-doc --update` — Relancer après ajout de composants
- [D] Implémenter les composants manquants (listés dans components/CLAUDE.md)
- [X] Terminé
```

**⏸️ STOP** — Attendre le choix

---

## Mode `--update`

Quand lancé avec `--update` :
1. Lire le CLAUDE.md existant
2. Re-scanner le projet (nouvelles composants, tokens modifiés)
3. Merger les nouvelles infos (garder les liens Figma manuels existants)
4. Afficher le diff des changements

---

## Règles du skill

- ⛔ Ne JAMAIS supprimer des liens Figma existants manuellement ajoutés
- ⛔ Ne JAMAIS modifier les sections du CLAUDE.md hors `## Design System`
- ✅ Toujours demander l'URL Figma AVANT de scanner
- ✅ Toujours afficher un résumé des changements avant d'écrire
- ✅ Toujours proposer `/figma-setup` si des composants n'ont pas de lien Figma
- ✅ Rester concis — tables > prose. Claude doit scanner vite
