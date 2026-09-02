---
description: Génère ou met à jour la documentation du projet. Crée README, API docs, guides d'utilisation. Usage: /docs [type] où type = readme|api|guide|all
---

# Documentation Generator

**Session ID:** ${CLAUDE_SESSION_ID}

## 📥 Contexte à charger

**Rassembler le contexte pour générer la documentation.**

| Contexte | Pattern/Action | Priorité |
|----------|----------------|----------|
| Structure projet | `Bash: tree -L 2` ou listing de répertoires | Requis |
| Package.json | `Read: package.json` (40 lignes) | Requis |
| README existant | `Read: README.md` (30 lignes) | Optionnel |
| Docs existantes | `Glob: docs/*.md docs/**/*.md` | Optionnel |
| Exports API | `Grep: "export"` dans src/index.ts, lib/index.ts | Optionnel |

### Instructions de chargement
1. Explorer la structure du projet
2. Lire package.json pour nom, description, scripts
3. Vérifier si un README existe déjà
4. Lister la documentation existante pour éviter les doublons

---

## Mode Documentation activé

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DOCUMENTATION GENERATOR                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Types de documentation :                                                   │
│                                                                             │
│  📖 README     - Vue d'ensemble, installation, usage rapide                 │
│  📚 API        - Documentation des fonctions/classes exportées              │
│  📝 GUIDE      - Guide d'utilisation détaillé                               │
│  📋 ALL        - Génère tout                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Process

### 1. Détection du type demandé

**Argument reçu :** `$ARGUMENTS`

| Type | Action |
|------|--------|
| `readme` | Créer/mettre à jour README.md |
| `api` | Générer docs/API.md |
| `guide` | Générer docs/GUIDE.md |
| `all` | Générer tout |
| *(vide)* | Demander quel type |

---

### 2. Templates

#### README.md
```markdown
# [Nom du projet]

[Description courte - 1-2 lignes]

## Features

- [Feature 1]
- [Feature 2]

## Installation

\`\`\`bash
npm install [package]
# ou
git clone [repo]
cd [repo]
npm install
\`\`\`

## Quick Start

\`\`\`typescript
// Exemple de code minimal
\`\`\`

## Usage

[Exemples d'utilisation courants]

## API

[Résumé des exports principaux]

## Configuration

[Options de configuration si applicable]

## Contributing

[Instructions pour contribuer]

## License

[Type de license]
```

#### API.md
```markdown
# API Reference

## Table of Contents

- [Module A](#module-a)
- [Module B](#module-b)

## Module A

### `functionName(params): ReturnType`

Description de la fonction.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `param1` | `string` | Description |

**Returns:** `ReturnType` - Description

**Example:**
\`\`\`typescript
const result = functionName('value');
\`\`\`

---
```

#### GUIDE.md
```markdown
# User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Usage](#advanced-usage)
4. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- [Prerequisite 1]
- [Prerequisite 2]

### Installation

[Instructions détaillées]

## Basic Usage

[Cas d'usage simples avec exemples]

## Advanced Usage

[Cas d'usage avancés]

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| [Problème] | [Solution] |
```

---

### 3. Génération

Je vais :
1. Analyser le code source
2. Extraire les exports et leurs types
3. Générer la documentation appropriée
4. Créer/mettre à jour les fichiers

---

## Output

```markdown
## Documentation générée

### Fichiers créés/modifiés
- `README.md` - ✅ Créé/Mis à jour
- `docs/API.md` - ✅ Créé
- `docs/GUIDE.md` - ✅ Créé

### Statistiques
- Fonctions documentées : X
- Classes documentées : X
- Exemples ajoutés : X

### Prochaines étapes
- [ ] Relire et ajuster si nécessaire
- [ ] Ajouter des exemples supplémentaires
- [ ] Commiter les changements
```

---

## Démarrage

**Type demandé :** $ARGUMENTS

Je génère la documentation...
