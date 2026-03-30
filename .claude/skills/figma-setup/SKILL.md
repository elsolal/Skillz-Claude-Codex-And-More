---
name: figma-setup
description: Configure Code Connect dans un projet pour mapper les composants Figma vers le code existant. Utiliser pour initialiser l'intégration Figma dans un projet, quand l'utilisateur dit "setup figma", "configurer code connect", "lier figma", ou veut connecter son design system Figma à son code.
model: opus
context: fork
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
argument-hint: [figma-file-url]
user-invocable: true
knowledge:
  core:
    - figma/code-connect-guide.md
  advanced:
    - figma/mcp-tools-reference.md
---

# Figma Setup

## 📥 Contexte à charger

**Au démarrage, vérifier les prérequis pour Code Connect.**

| Contexte | Pattern/Action | Priorité |
|----------|----------------|----------|
| Package.json | `Read: package.json` (30 lignes) | Requis |
| Framework | `Grep: package.json` pour react/vue/angular/next | Requis |
| Code Connect existant | `Read: figma.config.json` | Optionnel |
| Composants UI | `Glob: src/components/ui/*.{tsx,jsx,vue}` | Requis |

### Instructions de chargement
1. Lire package.json pour vérifier Node.js et les dépendances
2. Détecter le framework frontend
3. Vérifier si Code Connect est déjà configuré
4. Scanner les composants UI existants à mapper

---

## Activation

> **Au démarrage :**
> 1. Check if official Figma MCP is available (mcp__plugin_figma_figma__ tools)
> 2. Vérifier les prérequis (Node 18+, package.json)
> 3. Détecter le framework frontend
> 4. Scanner les composants UI existants
> 5. Vérifier si Code Connect déjà configuré

## Rôle & Principes

**Rôle** : Configurer Code Connect pour mapper les composants Figma vers les composants code existants. Ne pas créer de nouveaux composants, juste établir les connexions.

**Principes** :
- **One-time setup** - Configuration initiale, pas d'usage quotidien
- **Non-invasif** - N'ajoute que des fichiers .figma.tsx, ne modifie pas le code existant
- **Mapper l'existant** - Utiliser les composants du projet, pas en créer de nouveaux
- **Developer experience** - Faciliter la vie des devs qui consultent Figma

**Règles** :
- ⛔ Ne JAMAIS modifier les composants existants
- ⛔ Ne JAMAIS créer de nouveaux composants UI
- ⛔ Ne JAMAIS commit les credentials Figma
- ✅ Toujours vérifier les prérequis avant installation
- ✅ Toujours scanner les composants existants
- ✅ Toujours valider les mappings avant publication

---

## Process

### 1. Vérification des prérequis

```markdown
🔧 **Figma Code Connect Setup**

**Prérequis :**
| Check | Status |
|-------|--------|
| Node.js 18+ | [✅/❌] (version: X.Y.Z) |
| package.json | [✅/❌] |
| Framework détecté | [React/Vue/HTML/❌] |
| Composants UI | [X fichiers trouvés/❌] |

**Code Connect existant :** [Oui/Non]

[Si prérequis manquants]
❌ Prérequis manquants. Actions requises :
- [Action 1]
- [Action 2]

[Si OK]
✅ Prérequis validés. On continue l'installation ?
```

**⏸️ STOP** - Validation prérequis

---

### 2. Installation de Code Connect

```bash
# Installation du package
npm install -D @figma/code-connect
```

Vérifier le succès de l'installation.

---

### 3. Configuration figma.config.json

```markdown
📝 **Configuration Code Connect**

Je vais créer `figma.config.json` :

```json
{
  "$schema": "https://figma.com/code-connect/schema",
  "codeConnect": {
    "parser": "[react|html|vue]",
    "include": ["src/components/**/*.figma.tsx"],
    "exclude": ["**/*.test.tsx", "**/*.stories.tsx"]
  }
}
```

**Parser détecté** : [parser] (basé sur package.json)

Cette configuration te convient ?
```

**⏸️ STOP** - Validation configuration

Créer le fichier après validation.

---

### 4. Scan des composants existants

```markdown
🔍 **Composants détectés**

| Composant | Chemin | Type |
|-----------|--------|------|
| Button | `src/components/ui/button.tsx` | Component |
| Input | `src/components/ui/input.tsx` | Component |
| Card | `src/components/ui/card.tsx` | Component |
| Dialog | `src/components/ui/dialog.tsx` | Component |
| ... | ... | ... |

**Total** : X composants candidats au mapping

Ces composants correspondent à ton design system Figma ?
```

**⏸️ STOP** - Validation liste composants

---

### 5. Authentification Figma

```markdown
🔐 **Authentification Figma**

**MCP Figma** : L'authentification est automatique via OAuth (aucune action requise).

**Code Connect CLI** : Pour publier les mappings via la CLI, exécute :

```bash
npx figma connect
```

⚠️ **Note** : Les credentials CLI sont stockés localement (~/.figma/) et ne sont PAS commités.

Exécute la commande CLI et confirme quand c'est fait.
```

**⏸️ STOP** - Attendre confirmation auth

---

### 6. Création des mappings

Pour chaque composant identifié, si l'utilisateur fournit une URL Figma :

**Option A — Via MCP officiel (recommandé)** :
1. `get_code_connect_suggestions(fileKey)` → Obtenir des suggestions AI de mapping
2. `add_code_connect_map(fileKey, ...)` → Créer le mapping
3. `send_code_connect_mappings(fileKey, ...)` → Publier vers Figma

**Option B — Via fichiers .figma.tsx (traditionnel)** :

```markdown
🔗 **Mapping : [ComponentName]**

**Composant code** : `src/components/ui/[name].tsx`
**URL Figma** : [URL fournie ou à renseigner]

Je vais créer `src/components/ui/[name].figma.tsx` :

```tsx
import figma from "@figma/code-connect";
import { [ComponentName] } from "./[name]";

figma.connect([ComponentName], "[FIGMA_URL]", {
  props: {
    // Props détectées depuis le composant
    [propName]: figma.[type]("[Figma Prop Name]"),
  },
  example: (props) => (
    <[ComponentName] {...props}>
      {props.children}
    </[ComponentName]>
  ),
});
```

Ce mapping te convient ? (Tu peux aussi fournir l'URL Figma si pas encore fait)
```

**⏸️ STOP** - Validation mapping

Répéter pour chaque composant.

---

### 7. Publication des mappings

```markdown
📤 **Publication Code Connect**

**Fichiers créés** :
- `figma.config.json`
- `src/components/ui/button.figma.tsx`
- `src/components/ui/input.figma.tsx`
- ...

**Prêt à publier ?**

**Option A — Via MCP officiel** :
`send_code_connect_mappings(fileKey, ...)` → Publie directement via MCP (pas de CLI requise)

**Option B — Via CLI** :
```bash
npx figma connect publish
```

Cela va :
1. Valider tous les fichiers .figma.tsx
2. Uploader les mappings vers Figma
3. Rendre les connexions visibles dans l'inspecteur Figma

Confirme pour publier.
```

**⏸️ STOP** - Validation publication

---

### 8. Validation & Résumé

```markdown
## ✅ Figma Code Connect Configuré

**Fichiers créés** :
| Fichier | Description |
|---------|-------------|
| `figma.config.json` | Configuration Code Connect |
| `*.figma.tsx` | [N] fichiers de mapping |

**Composants mappés** : [N] / [Total]

**Workflow quotidien** :
1. Designer modifie dans Figma
2. Dev inspecte le composant dans Figma
3. Figma affiche le code du composant mappé
4. Dev copie/utilise le code

**Commandes utiles** :
```bash
# Via CLI
npx figma connect create "URL"  # Créer un nouveau mapping
npx figma connect publish       # Publier les changements
npx figma connect verify        # Vérifier les mappings

# Via MCP officiel (alternative sans CLI)
get_code_connect_suggestions    # Suggestions AI de mapping
send_code_connect_mappings      # Publier directement via MCP
```

**Prochaine étape ?**
- [A] Ajouter d'autres mappings (`/figma-setup [url]`)
- [F] Générer du code depuis Figma (`/figma-to-code`)
- [U] Importer les tokens dans UI Designer (`/ui-designer --from-figma`)
```

**⏸️ STOP** - Fin du setup

---

## Output Validation

Avant de terminer, valider :

```markdown
### ✅ Checklist Output Figma Setup

| Critère | Status |
|---------|--------|
| @figma/code-connect installé | ✅/❌ |
| figma.config.json créé | ✅/❌ |
| Auth Figma configurée | ✅/❌ |
| Au moins 1 mapping créé | ✅/❌ |
| Mappings publiés | ✅/❌ |

**Score : X/5** → Si < 4, compléter avant de terminer
```

---

## Templates

### figma.config.json (React)

```json
{
  "$schema": "https://figma.com/code-connect/schema",
  "codeConnect": {
    "parser": "react",
    "include": ["src/components/**/*.figma.tsx"],
    "exclude": ["**/*.test.tsx", "**/*.stories.tsx", "**/node_modules/**"]
  }
}
```

### figma.config.json (Vue)

```json
{
  "$schema": "https://figma.com/code-connect/schema",
  "codeConnect": {
    "parser": "html",
    "include": ["src/components/**/*.figma.ts"],
    "exclude": ["**/*.test.ts", "**/node_modules/**"]
  }
}
```

### Template .figma.tsx

```tsx
import figma from "@figma/code-connect";
import { ComponentName } from "./component-name";

figma.connect(ComponentName, "FIGMA_URL", {
  props: {
    // String prop
    label: figma.string("Label"),

    // Boolean prop
    disabled: figma.boolean("Disabled"),

    // Enum prop
    variant: figma.enum("Variant", {
      "Primary": "primary",
      "Secondary": "secondary",
    }),

    // Size prop
    size: figma.enum("Size", {
      "Small": "sm",
      "Medium": "md",
      "Large": "lg",
    }),

    // Instance prop (icon, slot)
    icon: figma.instance("Icon"),

    // Children
    children: figma.children("Content"),
  },
  example: (props) => (
    <ComponentName
      variant={props.variant}
      size={props.size}
      disabled={props.disabled}
    >
      {props.label}
    </ComponentName>
  ),
});
```

---

## Auto-Chain

Après le setup, proposer :

```markdown
## 🔗 Prochaine étape

✅ Figma Code Connect configuré avec [N] mappings.

**Suggestions :**

→ 🖼️ **`/figma-to-code [url]`** - Générer du code depuis une sélection Figma
→ 🎨 **`/ui-designer --from-figma`** - Importer les tokens Figma dans le design system

---

**[F] Figma to Code** | **[U] UI Designer** | **[X] Terminé**
```

**⏸️ STOP** - Attendre choix

---

## Transitions

- **Vers figma-to-code** : "On génère du code depuis un design Figma ?"
- **Vers ui-designer** : "On importe les tokens Figma dans le design system ?"
