# Exemple : Simple API REST

> Projet exemple pour illustrer le workflow D-EPCT+R en mode LIGHT (v2.6)

## Contexte

Une API REST simple pour gérer une liste de tâches (Todo List).
- **Complexité** : LIGHT (< 1 jour)
- **Stack** : Node.js + Express + SQLite

## Fichiers

```
simple-api/
├── README.md           # Ce fichier
├── 01-PRD.md          # Product Requirements Document (LIGHT)
├── 02-STORIES.md      # User Stories
└── 03-IMPLEMENTATION.md # Notes d'implémentation
```

## Workflow utilisé

```bash
# Méthode 1 : Feature directe (recommandé pour projets simples)
/dev "API REST Todo List"

# Méthode 2 : Quick fix pour petits ajustements
/quick-fix "ajouter endpoint DELETE /todos/:id"
```

Pas besoin de `/discovery` complet pour un projet aussi simple.

## Fonctionnalités v2.6 utilisées

| Feature | Usage dans cet exemple |
|---------|------------------------|
| **Mode LIGHT** | PRD simplifié, pas de brainstorm |
| `/quick-fix` | Pour ajouter des endpoints rapidement |
| **Dynamic Context** | Le skill charge automatiquement le PRD |
| **Hook auto-lint** | Lint automatique après chaque modification |

## Commandes utiles v2.6

```bash
# Simplifier le code modifié (natif Claude Code)
/simplify

# Vérifier l'état du projet
/status
```

---

## Code généré

### Structure du projet

```
simple-api/
├── src/
│   ├── index.js           # Entry point
│   ├── routes/
│   │   └── todos.js       # Routes CRUD
│   ├── services/
│   │   └── todoService.js # Business logic
│   └── db/
│       └── database.js    # SQLite setup
├── tests/
│   └── todos.test.js      # Tests unitaires
└── package.json
```

### src/index.js

```javascript
const express = require('express');
const todosRouter = require('./routes/todos');

const app = express();
app.use(express.json());

app.use('/api/todos', todosRouter);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
```

### src/routes/todos.js

```javascript
const express = require('express');
const router = express.Router();
const todoService = require('../services/todoService');

// GET /api/todos
router.get('/', async (req, res) => {
  try {
    const todos = await todoService.getAll();
    res.json(todos);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /api/todos
router.post('/', async (req, res) => {
  try {
    const { title } = req.body;
    if (!title) {
      return res.status(400).json({ error: 'Title is required' });
    }
    const todo = await todoService.create(title);
    res.status(201).json(todo);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// PATCH /api/todos/:id
router.patch('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { completed } = req.body;
    const todo = await todoService.update(id, { completed });
    if (!todo) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json(todo);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// DELETE /api/todos/:id
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const deleted = await todoService.delete(id);
    if (!deleted) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
```

### src/services/todoService.js

```javascript
const db = require('../db/database');

const todoService = {
  async getAll() {
    return db.prepare('SELECT * FROM todos ORDER BY created_at DESC').all();
  },

  async create(title) {
    const result = db.prepare(
      'INSERT INTO todos (title) VALUES (?) RETURNING *'
    ).get(title);
    return result;
  },

  async update(id, { completed }) {
    const result = db.prepare(
      'UPDATE todos SET completed = ? WHERE id = ? RETURNING *'
    ).get(completed, id);
    return result;
  },

  async delete(id) {
    const result = db.prepare('DELETE FROM todos WHERE id = ?').run(id);
    return result.changes > 0;
  }
};

module.exports = todoService;
```

### tests/todos.test.js

```javascript
const request = require('supertest');
const app = require('../src/index');

describe('Todos API', () => {
  describe('GET /api/todos', () => {
    it('should_return_empty_array_when_no_todos', async () => {
      const res = await request(app).get('/api/todos');
      expect(res.status).toBe(200);
      expect(res.body).toEqual([]);
    });
  });

  describe('POST /api/todos', () => {
    it('should_create_todo_when_title_provided', async () => {
      const res = await request(app)
        .post('/api/todos')
        .send({ title: 'Test todo' });

      expect(res.status).toBe(201);
      expect(res.body.title).toBe('Test todo');
      expect(res.body.completed).toBe(false);
    });

    it('should_return_400_when_title_missing', async () => {
      const res = await request(app)
        .post('/api/todos')
        .send({});

      expect(res.status).toBe(400);
    });
  });
});
```
