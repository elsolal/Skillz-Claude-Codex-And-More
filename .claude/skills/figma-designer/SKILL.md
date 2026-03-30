---
name: figma-designer
description: Use when the user wants Claude to create or prototype UI designs directly in Figma. Triggers on "design this in Figma", "create a screen in Figma", "prototype this page", "make a mockup in Figma", "draw this layout", or when the user asks to visually design something. Uses the official Figma MCP (use_figma) for all write operations.
---

# Figma Designer

Claude creates designs directly in Figma via the official Figma MCP server.

## Prerequisites

The official Figma MCP must be available (`mcp__plugin_figma_figma__*` tools). Authentication is automatic via OAuth — no token or plugin needed.

If a `fileKey` is needed and the user hasn't provided a Figma URL, use `create_new_file` to create a new file (requires `planKey` from `whoami`).

## Core Rules

- **ALWAYS** call `search_design_system` at session start to find reusable components
- **ALWAYS** take a screenshot after creating/modifying visual elements (validation loop)
- **ALWAYS** place new elements inside a Section or Frame, never on blank canvas
- **ALWAYS** import existing components via `importComponentByKeyAsync` — don't recreate them
- **ALWAYS** pass `fileKey` to every `use_figma` call
- **NEVER** hardcode colors — bind to variables when available

## Visual Validation Loop (mandatory)

After ANY visual change:

```
1. CREATE  → use_figma (Plugin API code)
2. SCREENSHOT → get_screenshot (node or page)
3. ANALYZE → Check alignment, spacing, proportions, visual balance
4. ITERATE → Fix issues (max 3 iterations)
5. VERIFY  → Final screenshot to confirm
```

## Workflow

### 1. Setup & Context

```
whoami                     → Get user info + plans (if need to create a file)
create_new_file            → Create a new Figma file (if no existing file)
search_design_system       → Find reusable components from libraries (REQUIRED)
get_variable_defs          → Get existing tokens/variables
```

Present to user:

```markdown
**Figma connecté** : [file name / new file created]
**fileKey** : [key]

**Composants disponibles** : [N]
[list key components: Button, Card, Input, etc.]

**Variables/tokens** : [N collections]

Prêt à designer. Qu'est-ce qu'on crée ?
```

### 2. Design Planning

Before touching Figma, plan the layout:

```markdown
**Plan de design** : [screen name]

**Structure** :
├── Header (Auto Layout horizontal, fill)
│   ├── Logo
│   └── Nav items
├── Hero Section (Auto Layout vertical, center)
│   ├── Heading
│   ├── Subtext
│   └── CTA Button (→ composant existant)
└── Content (Grid 3 cols)
    ├── Card ×3 (→ composant existant)
    └── ...

**Composants réutilisés** : [list]
**Composants à créer** : [list or "aucun"]
**Dimensions** : [W × H, device target]

On lance ?
```

**STOP** — Validate plan with user before creating anything.

### 3. Build the Design

All code is executed via `use_figma(fileKey, code, description)`.

#### Container First

Always start with a parent container:

```javascript
// Find or create a Section
let section = figma.currentPage.findOne(
  n => n.type === 'SECTION' && n.name === 'Design'
);
if (!section) {
  section = figma.createSection();
  section.name = 'Design';
  section.x = 0;
  section.y = 0;
}

// Create the main frame inside
const frame = figma.createFrame();
frame.name = 'Screen Name';
frame.resize(1440, 900);
frame.layoutMode = 'VERTICAL';
frame.primaryAxisAlignItems = 'CENTER';
frame.counterAxisAlignItems = 'CENTER';
frame.paddingTop = 40;
frame.paddingBottom = 40;
frame.paddingLeft = 40;
frame.paddingRight = 40;
frame.itemSpacing = 24;
section.appendChild(frame);
```

#### Use Existing Components

Use `search_design_system` to find components, then import in `use_figma`:

```javascript
// Import a library component by key (from search_design_system results)
const component = await figma.importComponentByKeyAsync('COMPONENT_KEY');
const instance = component.createInstance();
parentFrame.appendChild(instance);

// For local components, find and instantiate
const buttons = figma.currentPage.findAll(
  n => n.type === 'COMPONENT' && n.name.includes('Button')
);
if (buttons.length > 0) {
  const buttonInstance = buttons[0].createInstance();
  parentFrame.appendChild(buttonInstance);
}
```

#### Create Primitives When Needed

```javascript
// Text
const heading = figma.createText();
await figma.loadFontAsync({ family: "Inter", style: "Bold" });
heading.characters = "Welcome";
heading.fontSize = 48;
heading.fontName = { family: "Inter", style: "Bold" };

// Rectangle / Card
const card = figma.createFrame();
card.name = 'Card';
card.resize(400, 300);
card.cornerRadius = 12;
card.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];

// Auto Layout
card.layoutMode = 'VERTICAL';
card.itemSpacing = 16;
card.paddingTop = 24;
card.paddingBottom = 24;
card.paddingLeft = 24;
card.paddingRight = 24;
```

#### Apply Variables/Tokens

```javascript
// Bind to existing variables instead of hardcoding colors
const colorVars = await figma.variables.getLocalVariablesAsync('COLOR');
const primaryVar = colorVars.find(v => v.name.includes('primary'));
if (primaryVar) {
  frame.setBoundVariable('fills', 0, 'color', primaryVar.id);
}
```

### 4. Common Patterns

#### Responsive Layout

```javascript
// Fill container (not fixed width)
childFrame.layoutSizingHorizontal = 'FILL'; // NOT 'FIXED' or 'HUG'
childFrame.layoutSizingVertical = 'HUG';
```

#### Grid of Cards

```javascript
const grid = figma.createFrame();
grid.name = 'Cards Grid';
grid.layoutMode = 'HORIZONTAL';
grid.layoutWrap = 'WRAP';
grid.itemSpacing = 24;
grid.counterAxisSpacing = 24;
grid.layoutSizingHorizontal = 'FILL';

for (let i = 0; i < 3; i++) {
  const card = cardComponent.createInstance();
  card.layoutSizingHorizontal = 'FIXED';
  card.resize(400, 300);
  grid.appendChild(card);
}
```

#### Navigation Bar

```javascript
const nav = figma.createFrame();
nav.name = 'Navbar';
nav.layoutMode = 'HORIZONTAL';
nav.layoutSizingHorizontal = 'FILL';
nav.primaryAxisAlignItems = 'SPACE_BETWEEN';
nav.counterAxisAlignItems = 'CENTER';
nav.paddingLeft = 24;
nav.paddingRight = 24;
nav.resize(nav.width, 64);
nav.layoutSizingVertical = 'FIXED';
```

### 5. Screenshot & Validate

After building, ALWAYS:

```
get_screenshot(fileKey, nodeId) → Inspect result
```

Check for:
- Elements using "hug contents" that should "fill container" (lopsided layouts)
- Inconsistent padding
- Text/inputs not filling available width
- Items not centered in their containers
- Components floating outside their parent

Fix issues via `use_figma` and re-screenshot (max 3 iterations).

### 6. Present Result

```markdown
## Design créé : [Name]

**Screenshot** : [attached]

**Structure** :
- [N] composants réutilisés
- [N] éléments créés
- Dimensions : [W × H]

**Composants utilisés** : Button, Card, Input...

Le design te convient ? Je peux :
- [A] Ajuster des éléments
- [C] Créer un autre écran
- [E] Exporter vers du code (`/figma-to-code`)
```

## Capture Web → Figma

Pour capturer une page web existante (localhost ou externe) vers Figma :

```
generate_figma_design → Suivre les instructions de capture
```

C'est la meilleure approche quand on veut importer un design existant pour la première fois. Pour les modifications ultérieures, utiliser `use_figma`.

## Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Fixed width on elements that should fill | Use `layoutSizingHorizontal = 'FILL'` |
| Hug contents on containers | Check if fill is more appropriate |
| Forgetting `await figma.loadFontAsync()` before setting text | Always load fonts first |
| Creating components from scratch when they exist | Search first with `search_design_system` |
| Placing elements on blank canvas | Always use a Section or Frame parent |
| Not using Auto Layout | Use `layoutMode` on all container frames |
| Hardcoding colors instead of using variables | Bind to existing variables when available |
| Forgetting `fileKey` in `use_figma` calls | Always extract from URL or `create_new_file` result |

## Variable Management via use_figma

Pour créer/modifier des variables (tokens), utiliser `use_figma` avec du Plugin API code :

```javascript
// Create a variable collection
const collection = figma.variables.createVariableCollection('Design Tokens');

// Add modes
const lightModeId = collection.modes[0].modeId;
const darkModeId = collection.addMode('Dark');

// Create a color variable
const primaryColor = figma.variables.createVariable('Color/primary-500', collection.id, 'COLOR');
primaryColor.setValueForMode(lightModeId, { r: 0.231, g: 0.510, b: 0.965, a: 1 });
primaryColor.setValueForMode(darkModeId, { r: 0.376, g: 0.647, b: 0.980, a: 1 });

// Create a spacing variable
const spacingMd = figma.variables.createVariable('Spacing/md', collection.id, 'FLOAT');
spacingMd.setValueForMode(lightModeId, 16);
```

Pour créer beaucoup de variables d'un coup, regrouper dans un seul appel `use_figma` (plus efficace que des appels multiples).

## Figma Console Fallback

Si figma-console MCP est disponible, ces outils complémentaires peuvent être utiles :

- `figma_batch_create_variables` — Créer jusqu'à 100 variables par appel
- `figma_batch_update_variables` — Modifier jusqu'à 100 variables par appel
- `figma_setup_design_tokens` — Créer collection + modes + variables atomiquement
- `figma_audit_design_system` — Audit DS automatisé

Ces outils sont optionnels — `use_figma` couvre tous les mêmes cas via Plugin API.

## Auto-Chain

After design is complete:
- → `/figma-to-code <url>` — Convert to code
- → `/figma-design-code-sync` — Set up sync mappings
- → Create another screen
