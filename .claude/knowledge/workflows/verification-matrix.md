# Verification Before Completion — Matrice par workflow

Avant de déclarer une feature/fix "DONE", "COMPLETE", "SHIPPED" ou de proposer une PR, chaque workflow doit valider les checks ci-dessous. **Si une vérif échoue → ne pas déclarer DONE**, reporter l'erreur et proposer correction.

## Matrice

| Workflow | Vérifications minimales |
|---|---|
| `/dev` | lint OK + types OK + tests P0/P1 verts |
| `/quick-fix` | lint OK + types OK (tests optionnels selon contexte) |
| `/refactor` | lint + types + **tous** les tests existants verts (refactor = no behavior change) |
| `/ship` | tout `/dev` + CHANGELOG.md modifié + branche != main + working tree clean |
| `/auto-dev` (RALPH) | tout `/dev` + dernier log RALPH cohérent (pas de pattern d'erreur en boucle dans les 3 dernières itérations) |
| `/auto-discovery` (RALPH) | spec produite avec frontmatter `status: draft, approved_by: ralph` (humain validera ensuite) |

## Commandes par stack

| Stack | Lint | Types | Tests |
|---|---|---|---|
| Node/TS | `npm run lint` | `npm run typecheck` ou `tsc --noEmit` | `npm test` |
| Python | `ruff check .` | `mypy .` | `pytest` |
| Go | `golangci-lint run` | `go vet ./...` | `go test ./...` |
| Rust | `cargo clippy` | (intégré) | `cargo test` |

Si la commande n'existe pas (pas de script `lint`, pas de typecheck), l'absence est OK — mais le **noter explicitement** dans le rapport de vérification (sinon RALPH peut prétendre "tout vert" alors qu'il n'a rien lancé).

## Output attendu

Avant de finaliser, présenter une **table de vérification** dans le résumé :

```markdown
### Vérifications avant completion

| Check | Commande | Résultat |
|---|---|---|
| Lint | npm run lint | ✅ |
| Types | npm run typecheck | ✅ |
| Tests P0/P1 | npm test -- --filter=p0,p1 | ✅ |
| (si /ship) CHANGELOG | grep new entry | ✅ |
| (si /ship) Branch | git branch --show-current | ✅ feature/X |
| (si /ship) Tree | git status --porcelain | ✅ clean |
```

## Anti-patterns

| Symptôme | Pourquoi mauvais | Fix |
|---|---|---|
| "Tests verts" sans avoir lancé `npm test` | Hallucination | Toujours afficher la commande exécutée + sa sortie |
| Skip vérif en autonome (RALPH) | C'est précisément là que la vérif compte | Ne JAMAIS skip en RALPH, c'est le risque #1 |
| `npm test` ignore les tests P2/P3 | Filter trop strict | Le filter P0/P1 est un défaut acceptable, mais `/ship` doit lancer **tous** les tests |
| Lint échoue → autofix puis claim DONE sans relancer | Régression possible | Relancer toute la matrice après chaque autofix |

## Référence

Inspiré du principe `superpowers/verification-before-completion` (obra/superpowers), adapté pour la matrice de workflows D-EPCT+R.
