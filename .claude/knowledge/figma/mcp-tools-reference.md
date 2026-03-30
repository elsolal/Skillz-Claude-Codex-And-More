# MCP Figma Tools Reference

## Overview

Le serveur MCP officiel Figma expose des outils pour lire ET écrire dans Figma depuis Claude. Il fonctionne en HTTP direct avec OAuth automatique — aucun plugin, bridge ou token à gérer.

**Serveur** : Plugin Figma MCP officiel (tools préfixés `mcp__plugin_figma_figma__`)

**Authentification** : OAuth automatique via le navigateur

**Capacités** : Lecture + Écriture + Création de fichiers + Code Connect + Design System

## Architecture : Official MCP vs Figma Console

| | Official Figma MCP | Figma Console MCP |
|---|---|---|
| **Statut** | **PRIMARY — utiliser par défaut** | OPTIONAL — cas avancés uniquement |
| **Transport** | HTTP direct | WebSocket bridge (localhost) |
| **Auth** | OAuth automatique | Token perso (FIGMA_ACCESS_TOKEN) |
| **Plugin requis** | Non | Oui (Desktop Bridge) |
| **Écriture** | `use_figma` (Plugin API complète) | `figma_execute` + 60+ tools granulaires |
| **Lecture** | 8 outils spécialisés | 20+ outils spécialisés |
| **Unique** | `generate_figma_design`, `create_new_file`, `get_code_connect_suggestions`, `search_design_system` | Console logging, DS audit/lint, batch variable tools |

**Règle** : Toujours utiliser le MCP officiel en premier. Ne recourir à figma-console que pour le debug console ou l'audit DS automatisé.

---

## Outils du MCP Officiel

### 1. use_figma ⭐ (outil principal d'écriture)

Exécute du JavaScript via la Plugin API Figma. C'est l'outil polyvalent pour toute opération d'écriture : créer des frames, composants, variables, styles, modifier des nodes, etc.

**Usage** :
```
use_figma(fileKey, code, description, skillNames?)
```

**Paramètres** :
| Param | Type | Description |
|-------|------|-------------|
| `fileKey` | string | **Requis** — Clé du fichier Figma |
| `code` | string | JavaScript à exécuter (accès à l'objet global `figma`) |
| `description` | string | Description concise de l'opération |
| `skillNames` | string? | Skills utilisés (pour logging) |

**Capacités** :
- Créer/modifier/supprimer des frames, composants, instances
- Gérer les variables (tokens) : CRUD complet
- Appliquer des styles, fills, strokes, effects
- Manipuler l'Auto Layout
- Instancier des composants existants
- Charger et utiliser des fonts
- Tout ce que la Plugin API Figma permet

**Exemple** :
```javascript
// Créer un frame avec Auto Layout
const frame = figma.createFrame();
frame.name = 'Card';
frame.resize(400, 300);
frame.layoutMode = 'VERTICAL';
frame.paddingTop = 24;
frame.paddingBottom = 24;
frame.paddingLeft = 24;
frame.paddingRight = 24;
frame.itemSpacing = 16;
frame.cornerRadius = 12;
frame.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
```

**Quand utiliser** : Toute opération de création/modification de design. C'est le remplacement de `figma_execute` (figma-console) avec une meilleure architecture (pas de plugin bridge requis).

**Quand NE PAS utiliser** : Pour capturer une page web → utiliser `generate_figma_design`.

---

### 2. generate_figma_design (capture web → Figma)

Capture une page web (localhost ou externe) et l'importe comme design Figma.

**Usage** :
```
generate_figma_design(outputMode?, fileKey?, fileName?, captureId?, nodeId?, planKey?)
```

**Workflow en 2 étapes** :
1. Appeler sans `outputMode` → reçoit les instructions de capture et options
2. Appeler avec `captureId` pour poll le résultat (toutes les 5s, max 10 fois)

**Modes de sortie** :
| Mode | Description |
|------|-------------|
| `newFile` | Crée un nouveau fichier Figma |
| `existingFile` | Ajoute à un fichier existant (avec `fileKey`) |
| `clipboard` | Copie dans le presse-papier Figma |

**Cas d'usage** : Capturer un dev server localhost, importer un site externe, synchroniser une page web vers Figma pour la première fois.

---

### 3. create_new_file

Crée un nouveau fichier Figma vide.

**Usage** :
```
create_new_file(fileName, planKey, editorType)
```

**Paramètres** :
| Param | Type | Description |
|-------|------|-------------|
| `fileName` | string | Nom du fichier |
| `planKey` | string | Team/org key (obtenu via `whoami`) |
| `editorType` | "design" \| "figjam" | Type de fichier |

**Retourne** : `fileKey` et URL du nouveau fichier.

---

### 4. search_design_system

Recherche des composants, variables et styles dans toutes les librairies de design.

**Usage** :
```
search_design_system(query, fileKey, includeComponents?, includeVariables?, includeStyles?, includeLibraryKeys?)
```

**Retourne** : Composants, variables et styles matchant la recherche, avec leurs keys pour instanciation.

**Remplace** : `figma_search_components` et `figma_get_library_components` de figma-console, en mieux (recherche cross-library).

---

### 5. get_design_context

Extrait le contexte de design d'un fichier ou node pour la génération de code.

**Usage** :
```
get_design_context(fileKey, nodeId?)
```

**Retourne** :
- Code généré (React+Tailwind enrichi de hints)
- Screenshot du design
- Code Connect snippets (si configurés)
- Documentation composant, annotations, tokens CSS

**Important** : Le code retourné est une **référence**, pas du code final. Toujours adapter au stack du projet.

---

### 6. get_variable_defs

Récupère les définitions de variables (tokens) d'un fichier.

**Usage** :
```
get_variable_defs(fileKey)
```

**Retourne** : Variables de couleur, typographie, espacement, collections et modes (light/dark).

---

### 7. get_screenshot

Capture une image d'un node ou fichier.

**Usage** :
```
get_screenshot(fileKey, nodeId?)
```

---

### 8. get_metadata

Récupère les métadonnées légères (structure XML, dimensions, types de nodes).

**Usage** :
```
get_metadata(fileKey, nodeId?)
```

---

### 9. get_figjam

Récupère le contenu d'un board FigJam.

---

### 10. generate_diagram

Crée un diagramme dans FigJam.

---

### 11-14. Code Connect Tools

| Outil | Usage |
|-------|-------|
| `get_code_connect_map(fileKey)` | Récupérer les mappings CC existants |
| `get_code_connect_suggestions(fileKey)` | **Nouveau** — Suggestions AI pour CC |
| `add_code_connect_map(fileKey, ...)` | Créer/modifier un mapping CC |
| `send_code_connect_mappings(fileKey, ...)` | Push les mappings vers Figma |

---

### 15. create_design_system_rules

Crée des règles de design system personnalisées.

---

### 16. whoami

Retourne les infos de l'utilisateur connecté et ses plans/teams.

---

## Workflows recommandés

### Créer un design dans Figma

```
1. whoami                    → Obtenir les plans disponibles
2. create_new_file           → Créer un fichier (ou utiliser un existant)
3. search_design_system      → Trouver les composants réutilisables
4. use_figma                 → Créer le design (Plugin API)
5. get_screenshot            → Valider visuellement
```

### Extraire un design pour le code

```
1. get_metadata              → Comprendre la structure
2. get_variable_defs         → Récupérer les tokens
3. get_design_context        → Extraire les détails pour le code
4. get_screenshot            → Valider visuellement
```

### Capturer un site web → Figma

```
1. generate_figma_design     → Lancer la capture (sans outputMode)
2. Choisir le mode de sortie (newFile, existingFile, clipboard)
3. generate_figma_design     → Poll avec captureId jusqu'à completion
```

### Configurer Code Connect

```
1. get_code_connect_map         → Voir les mappings existants
2. get_code_connect_suggestions → Obtenir des suggestions AI
3. add_code_connect_map         → Créer les mappings
4. send_code_connect_mappings   → Publier vers Figma
```

### Gérer les tokens/variables

```
1. get_variable_defs            → Lire les tokens existants
2. use_figma                    → Créer/modifier des variables via Plugin API
   // Ex: await figma.variables.createVariable(name, collectionId, type)
   // Ex: variable.setValueForMode(modeId, value)
3. get_screenshot               → Valider visuellement
```

## Parsing d'URL Figma

### Formats

```
https://figma.com/design/{file_key}/{file_name}?node-id={node_id}
https://figma.com/file/{file_key}/{file_name}?node-id={node_id}
https://figma.com/design/{file_key}/branch/{branch_key}/{file_name} → use branch_key
https://figma.com/make/{make_file_key}/{make_file_name} → use make_file_key
https://figma.com/board/{file_key}/{file_name} → FigJam file
```

### Extraction

```javascript
const figmaUrlRegex = /figma\.com\/(design|file|make|board)\/([a-zA-Z0-9]+)/;
const nodeIdRegex = /node-id=([0-9]+[-:][0-9]+)/;
// Note: convertir "-" en ":" dans nodeId
```

## Figma Console MCP (optionnel)

Si figma-console est installé, ces outils sont disponibles en **complément** :

| Outil | Cas d'usage unique |
|-------|-------------------|
| `figma_watch_console` | Debug temps réel des logs plugin |
| `figma_get_console_logs` | Lire les logs plugin |
| `figma_audit_design_system` | Audit DS automatisé |
| `figma_lint_design` | Lint du design |
| `figma_check_design_parity` | Vérifier parité code↔Figma |
| `figma_get_design_system_kit` | DS complet en un appel |
| `figma_batch_create_variables` | Créer 100 variables/appel |
| `figma_batch_update_variables` | Modifier 100 variables/appel |

**Prérequis figma-console** : Desktop Bridge plugin + FIGMA_ACCESS_TOKEN.

**Règle** : Si le même résultat est atteignable via `use_figma` du MCP officiel, préférer le MCP officiel.

## Gestion des erreurs

| Code | Signification | Action |
|------|---------------|--------|
| 401 | Non authentifié | Re-authentifier via OAuth (automatique) |
| 403 | Accès refusé au fichier | Vérifier les permissions |
| 404 | Fichier/node non trouvé | Vérifier l'URL/fileKey |
| 429 | Rate limit | Attendre et réessayer |

## Intégration avec les skills

| Skill | Outils principaux |
|-------|-------------------|
| `figma-designer` | `use_figma`, `search_design_system`, `get_screenshot`, `create_new_file` |
| `figma-to-code` | `get_design_context`, `get_variable_defs`, `get_code_connect_map`, `generate_figma_design` |
| `figma-design-system` | `use_figma`, `get_variable_defs`, `search_design_system`, `get_screenshot` |
| `figma-design-code-sync` | `get_design_context`, `get_code_connect_map`, `get_code_connect_suggestions`, `add_code_connect_map` |
| `figma-setup` | `get_code_connect_map`, `get_code_connect_suggestions`, `send_code_connect_mappings` |
| `ds-doc` | `get_metadata`, `get_design_context`, `get_variable_defs` |
