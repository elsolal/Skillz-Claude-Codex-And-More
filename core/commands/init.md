---
description: Initialise un nouveau projet avec scaffolding. Usage: /init [template] où template = next|express|api|cli|lib
---

# Project Init 🚀

## Mode activé : Scaffolding

Je vais initialiser un nouveau projet avec la structure et configuration appropriées.

---

## 📥 Contexte à détecter

**Vérifier l'état du dossier avant initialisation.**

| Contexte | Action | Priorité |
|----------|--------|----------|
| Dossier actuel | `Bash: pwd` | Requis |
| Fichiers existants | `Bash: ls -la` | Requis |
| Git initialisé | `Bash: git status` | Optionnel |
| Package.json | `Read: package.json` (5 lignes) | Optionnel |

### Instructions de chargement
1. Vérifier si le dossier est vide ou contient déjà du code
2. Détecter si git est déjà initialisé
3. Si package.json existe, lire le nom et la description

---

## Arguments

| Argument | Description |
|----------|-------------|
| `next` | Next.js 14 App Router + TypeScript |
| `express` | Express.js API + TypeScript |
| `api` | API REST minimaliste (Hono/Fastify) |
| `cli` | CLI tool avec Commander.js |
| `lib` | Library npm publishable |
| (none) | Choix interactif |

### Options

| Option | Description |
|--------|-------------|
| `--name <name>` | Nom du projet |
| `--db <type>` | Base de données (postgres, mysql, sqlite) |
| `--auth` | Ajouter authentification |
| `--docker` | Ajouter Docker config |
| `--ci` | Ajouter GitHub Actions |

---

## Templates disponibles

### 1. Next.js (`next`)

```
project/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   └── api/
│   │       └── health/route.ts
│   ├── components/
│   │   └── ui/
│   └── lib/
│       └── utils.ts
├── public/
├── tests/
│   └── setup.ts
├── .env.example
├── .gitignore
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

**Stack** : Next.js 14, TypeScript, Tailwind CSS, ESLint, Prettier

### 2. Express API (`express`)

```
project/
├── src/
│   ├── index.ts
│   ├── routes/
│   │   ├── index.ts
│   │   └── health.ts
│   ├── middleware/
│   │   ├── error-handler.ts
│   │   └── validate.ts
│   ├── services/
│   ├── models/
│   └── utils/
│       └── logger.ts
├── tests/
│   └── setup.ts
├── .env.example
├── .gitignore
├── tsconfig.json
├── package.json
└── README.md
```

**Stack** : Express.js, TypeScript, Zod, Pino, ESLint

### 3. API minimaliste (`api`)

```
project/
├── src/
│   ├── index.ts
│   ├── routes.ts
│   └── handlers/
│       └── health.ts
├── tests/
├── .env.example
├── .gitignore
├── tsconfig.json
├── package.json
└── README.md
```

**Stack** : Hono ou Fastify, TypeScript, Zod

### 4. CLI (`cli`)

```
project/
├── src/
│   ├── index.ts
│   ├── commands/
│   │   └── example.ts
│   └── utils/
│       └── logger.ts
├── bin/
│   └── cli.js
├── tests/
├── .gitignore
├── tsconfig.json
├── package.json
└── README.md
```

**Stack** : Commander.js, TypeScript, Chalk, Ora

### 5. Library (`lib`)

```
project/
├── src/
│   ├── index.ts
│   └── utils/
├── tests/
├── .gitignore
├── tsconfig.json
├── tsup.config.ts
├── package.json
└── README.md
```

**Stack** : TypeScript, tsup, Vitest

---

## Process

### 1. Sélection du template

Si pas d'argument, je propose les choix :

```
🚀 Quel type de projet ?

[1] Next.js     - App web full-stack
[2] Express     - API REST complète
[3] API         - API minimaliste (Hono)
[4] CLI         - Outil en ligne de commande
[5] Library     - Package npm

> Choix :
```

**⏸️ STOP** - Attendre la sélection

### 2. Configuration

```
📝 Configuration du projet

Nom du projet : [auto-detect from folder or ask]
Base de données : [none/postgres/mysql/sqlite]
Authentification : [yes/no]
Docker : [yes/no]
GitHub Actions : [yes/no]
```

**⏸️ STOP** - Valider la configuration

### 3. Création de la structure

1. Créer les dossiers
2. Générer les fichiers de base
3. Initialiser package.json
4. Configurer TypeScript
5. Ajouter ESLint/Prettier
6. Créer .gitignore et .env.example

### 4. Options additionnelles

Si `--db` :
- Ajouter ORM (Prisma ou Drizzle)
- Créer schema de base
- Configurer connexion

Si `--auth` :
- Ajouter next-auth ou lucia-auth
- Créer routes auth de base
- Configurer session

Si `--docker` :
- Créer Dockerfile
- Créer docker-compose.yml
- Configurer multi-stage build

Si `--ci` :
- Copier templates GitHub Actions
- Configurer CI/CD

### 5. Finalisation

```bash
# Installer les dépendances
npm install

# Initialiser git
git init

# Premier commit
git add -A
git commit -m "chore: initial project setup"
```

**⏸️ STOP** - Valider avant installation

---

## Output

```
✅ Projet initialisé !

📁 Structure créée :
   - src/           Code source
   - tests/         Tests
   - package.json   Dépendances

📦 Dépendances installées :
   - typescript
   - eslint
   - [framework]
   - [additionnelles]

🚀 Prochaines étapes :
   1. cd [project-name]
   2. cp .env.example .env
   3. npm run dev

📚 Documentation :
   - README.md créé
   - .env.example avec variables
```

---

## Fichiers générés communs

### package.json (base)

```json
{
  "name": "[project-name]",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "[dev-command]",
    "build": "[build-command]",
    "start": "[start-command]",
    "lint": "eslint . --ext .ts,.tsx",
    "lint:fix": "eslint . --ext .ts,.tsx --fix",
    "typecheck": "tsc --noEmit",
    "test": "vitest",
    "test:coverage": "vitest --coverage"
  }
}
```

### tsconfig.json (base)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### .gitignore

```
node_modules/
dist/
.env
.env.local
*.log
.DS_Store
coverage/
.next/
```

### .env.example

```bash
# App
NODE_ENV=development
PORT=3000

# Database (if applicable)
DATABASE_URL=

# Auth (if applicable)
AUTH_SECRET=
```

---

## Exemples

### Next.js simple

```bash
/init next
```

### Express avec PostgreSQL

```bash
/init express --db postgres
```

### API avec tout

```bash
/init api --db sqlite --docker --ci
```

### Interactif

```bash
/init
```

---

## Démarrage 🚀

**Arguments reçus :** $ARGUMENTS

Je vais maintenant :
1. Détecter le contexte (dossier vide ?)
2. Proposer le template ou utiliser l'argument
3. Configurer les options
4. Créer la structure
5. Installer les dépendances

---

### Analyse en cours...
