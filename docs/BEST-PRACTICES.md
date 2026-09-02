# Best Practices - Claude Code & D-EPCT+R

> Conseils pour maximiser l'efficacité avec Claude Code et le workflow D-EPCT+R

---

## 1. Workflow optimal

### Commencer en mode Plan

Toujours démarrer une session en mode Plan (`Shift+Tab` deux fois) pour :
- Définir clairement l'objectif
- Laisser Claude analyser le contexte
- Valider l'approche avant exécution

```
# Bon workflow
1. Mode Plan → Claude analyse
2. Valider le plan → "ok"
3. Mode Auto → Claude exécute
```

### Sessions parallèles

Pour les gros projets, utiliser plusieurs instances :
- **Session 1** : Planning/PRD
- **Session 2** : Code
- **Session 3** : Tests
- **Session web** : Review et questions

### Découper les tâches

Préférer plusieurs petites tâches à une grosse :
```bash
# ❌ Éviter
/dev #big-feature-with-unclear-boundaries

# ✅ Préférer
/dev #feature-part1
/dev #feature-part2
/dev #feature-part3
```

---

## 2. CLAUDE.md efficace

### Enrichir régulièrement

Le fichier `.claude/CLAUDE.md` doit évoluer :
```markdown
## Erreurs courantes à éviter

- Ne pas utiliser `any` en TypeScript
- Toujours gérer les erreurs async
- Préférer les named exports

## Patterns du projet

- Services dans `src/services/`
- Composants dans `src/components/[feature]/`
- Tests à côté des fichiers (`*.test.ts`)
```

### Versionner en Git

Le CLAUDE.md doit être committé et partagé :
- Toute l'équipe peut l'enrichir
- Les erreurs observées sont documentées
- Les patterns sont cohérents

---

## 3. Boucle de validation

### Le secret de la qualité

> "Give Claude a way to verify its work" - La validation automatique multiplie par 2-3 la qualité.

### Implémentation

1. **Lint automatique** :
   ```bash
   # Hook PostToolUse pour formatter
   npm run lint:fix
   ```

2. **Types vérifiés** :
   ```bash
   npm run typecheck
   ```

3. **Tests exécutés** :
   ```bash
   npm test
   ```

4. **UI testée** (via Chrome extension MCP) :
   - Screenshots automatiques
   - Vérification visuelle

---

## 4. Slash commands optimisées

### Pré-calculer les données

Les slash commands peuvent inclure du bash pour pré-calculer :
```markdown
# .claude/commands/status.md

Affiche le statut du projet :

```bash
echo "=== Git Status ==="
git status --short

echo "=== Tests ==="
npm test 2>&1 | tail -5

echo "=== Lint ==="
npm run lint 2>&1 | tail -5
```

Analyse ces résultats et donne-moi un résumé.
```

### Créer des commandes métier

```markdown
# .claude/commands/deploy-preview.md

Déploie une preview :
1. Run les tests
2. Build le projet
3. Deploy sur Vercel preview
4. Retourne l'URL
```

---

## 5. MCP Servers

### Configuration recommandée

```json
// .claude/mcp.json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp@latest"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-slack"]
    },
    "sentry": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-sentry"]
    }
  }
}
```

### Usages courants

| MCP | Usage |
|-----|-------|
| **Context7** | Documentation up-to-date des libs |
| **GitHub** | Créer issues/PRs automatiquement |
| **Slack** | Notifications d'équipe |
| **Sentry** | Debug des erreurs en prod |
| **Figma** | Extraction des designs |
| **Chrome** | Tests UI automatisés |

---

## 6. Permissions granulaires

### Éviter --dangerously-skip-permissions

Utiliser `/permissions` pour pré-autoriser les commandes sûres :
```
/permissions add "npm test"
/permissions add "npm run lint"
/permissions add "npm run build"
```

### Commandes à autoriser

| Catégorie | Commandes |
|-----------|-----------|
| Tests | `npm test`, `vitest`, `playwright` |
| Lint | `npm run lint`, `eslint` |
| Build | `npm run build`, `tsc` |
| Git (read) | `git status`, `git log`, `git diff` |

### Commandes à valider manuellement

| Catégorie | Commandes |
|-----------|-----------|
| Git (write) | `git push`, `git commit` |
| Deploy | `vercel`, `netlify deploy` |
| Install | `npm install [pkg]` |
| Destructive | `rm -rf`, `git reset --hard` |

---

## 7. Subagents efficaces

### Quand utiliser un subagent

- **Recherche** : Explorer la codebase
- **Analyse** : Comprendre un bug
- **Refactoring** : Simplifier du code
- **Tests** : Écrire les tests d'un composant

### Pattern de subagent

```markdown
# Dans une commande ou skill

Lance un subagent pour :
1. Analyser tous les fichiers `*.test.ts`
2. Identifier les tests flaky (timing issues)
3. Proposer des fixes
```

---

## 8. Review de code avec GitHub

### GitHub Action @.claude

Configurer la GitHub Action pour enrichir les CLAUDE.md :
```yaml
# .github/workflows/claude-review.yml
name: Claude Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          command: "Review cette PR et suggère des améliorations au CLAUDE.md si nécessaire"
```

### Amélioration continue

Chaque PR peut :
1. Être reviewée par Claude
2. Ajouter des patterns au CLAUDE.md
3. Documenter les erreurs évitées

---

## 9. Modèle optimal

### Opus 4.5 avec thinking

Préférer Opus pour :
- Meilleure compréhension du contexte
- Moins d'allers-retours
- Résultats plus cohérents

```bash
# Configurer le modèle
claude --model opus
```

### Quand utiliser Sonnet

- Tâches simples et répétitives
- Budget limité
- Latence critique

---

## 10. Debugging efficace

### Preuves du quality gate

Toujours consulter le dernier gate file en cas de problème de validation :
```bash
gate_file=$(ls -t docs/quality/GATE-*.yaml | head -1)
cat "$gate_file"
```

### Pattern de debug

1. **Reproduire** : Identifier les étapes exactes
2. **Isoler** : Trouver le composant fautif
3. **Comprendre** : Lire les logs/erreurs
4. **Fixer** : Corriger avec tests
5. **Valider** : Vérifier que c'est fixé

### Commande de debug

```markdown
# .claude/commands/debug.md

Debug le problème :
1. Lis les derniers logs d'erreur
2. Identifie la cause root
3. Propose un fix avec test
```

---

## Résumé des bonnes pratiques

| Pratique | Impact |
|----------|--------|
| Mode Plan d'abord | Meilleure direction |
| CLAUDE.md enrichi | Moins d'erreurs répétées |
| Boucle de validation | 2-3x meilleure qualité |
| MCP intégrés | Plus d'autonomie |
| Permissions granulaires | Sécurité + vitesse |
| Sessions parallèles | Productivité max |
| Opus avec thinking | Meilleurs résultats |
