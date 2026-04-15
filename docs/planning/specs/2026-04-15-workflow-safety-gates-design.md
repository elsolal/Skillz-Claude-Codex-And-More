---
title: Workflow Safety Gates
status: approved
approved_by: human
approved_at: 2026-04-15T11:00:00Z
slug: workflow-safety-gates
related_pr: TBD
---

# Workflow Safety Gates

## Why

Deux dettes structurelles repérées en comparant Skillz-Claude à `obra/superpowers` :

1. **RALPH peut dériver** — `/auto-dev` et `/auto-discovery` n'ont pas de gate dur. Une boucle autonome qui code sans spec ni issue valide produit du code "à côté" du besoin.
2. **Pas de norme pour ajouter des skills** — 33 skills aujourd'hui, on en ajoute régulièrement, aucun garde-fou qualité.

## Non-goals

- Bloquer les flows manuels (`/dev`, `/quick-fix`, `/discovery`) — ils gardent leur souplesse.
- Forcer TDD universel — `/quick-fix` reste légitime sans test.
- Importer des skills upstream tels quels — on garde notre vocabulaire D-EPCT+R.

## Design

### 1. Convention de spec

Toutes les specs de discovery/architecture vont dans :

```
docs/planning/specs/YYYY-MM-DD-<slug>-design.md
```

Frontmatter obligatoire :

```yaml
---
title: <Titre lisible>
status: draft | approved
approved_by: human | ralph | <name>
approved_at: <ISO-8601>
slug: <slug>
related_pr: <PR # ou TBD>
---
```

**Règle clé** : `approved_by: ralph` est rejeté par les hard gates. Seul un humain peut approuver.

### 2. Hard gates RALPH

`/auto-dev` au démarrage :

```
SI $ARGUMENTS contient une issue GitHub (#NUM ou URL gh)
  → vérifier que l'issue existe (gh issue view)
  → OK, continuer
SINON SI une spec docs/planning/specs/*-<slug>-design.md existe
  → lire frontmatter
  → SI status: approved ET approved_by != ralph → OK, continuer
  → SINON refuser
SINON
  → refuser : "Pas d'issue GitHub ni de spec approuvée"
  → suggérer : lancer /discovery ou /auto-discovery, ou créer une issue
  → override : --allow-no-spec (documenté, pour prototypage rapide uniquement)
```

`/auto-discovery` produit en sortie une spec avec `status: draft`. C'est l'humain qui passe à `approved` après revue.

### 3. Verification-before-completion (matrice)

Avant de déclarer "DONE" / "COMPLETE", chaque workflow vérifie :

| Workflow | Vérifs minimales |
|---|---|
| `/dev` | lint OK + types OK + tests P0/P1 verts |
| `/quick-fix` | lint OK + types OK |
| `/ship` | lint + types + tous tests + CHANGELOG.md modifié + branche != main + working tree clean |
| `/auto-dev` | lint + types + P0/P1 + dernier log RALPH cohérent (pas de pattern d'erreur en boucle) |

Si vérif échoue → ne pas déclarer DONE, reporter l'erreur, proposer correction.

### 4. Skill `skillz-writing-skills`

Méta-skill local (pas import obra) qui guide la création/modification d'un skill Skillz-Claude :

- Frontmatter `name`, `description` (avec triggers explicites)
- Structure : Why / When to use / Process / Output / Examples
- Vocabulaire D-EPCT+R / RALPH / FR par défaut
- Checklist qualité (description triggers, exemples concrets, no LLM-jargon)
- Test : invoquer le skill dans une session test

### 5. `/skillz-doctor` command

Diagnostic en 1 commande. Vérifie :

- **Symlinks** : `~/.gemini/skills`, `~/.codex/skills`, `~/.opencode/skills`, `~/.agents/skills` → résolus correctement
- **Manifest drift** : `~/.claude/.skillz-manifest` cohérent avec `~/.claude/skills/`
- **RALPH locks** : `docs/ralph-logs/*.md` orphelins (session > 24h sans completion)
- **Spec frontmatter** : toutes les specs ont un frontmatter valide
- **Provider files** : `GEMINI.md`, `AGENTS.md`, `gemini-extension.json` présents si dossier provider existe

Output : table colorée `OK` / `WARN` / `FAIL` + suggestion de fix par ligne.

## Implementation order

1. Spec convention (ce document) ✅
2. `skillz-writing-skills` skill
3. `skillz-doctor` command
4. Hard gates dans `auto-dev.md` et `auto-discovery.md`
5. Verification matrix dans `dev.md`, `quick-fix.md`, `ship.md`, `auto-dev.md`
6. Update CLAUDE.md (référence specs convention)
7. CHANGELOG entry

## Risks

- **Frontmatter manuel = friction** : ajout d'1 minute pour éditer le frontmatter post-discovery. Mitigation : `/auto-discovery` génère le frontmatter correctement (`status: draft, approved_by: ralph`), humain n'a qu'à passer à `approved` + son nom.
- **`--allow-no-spec` peut devenir l'échappatoire par défaut** : mitigation = documenter explicitement "prototypage uniquement" + log RALPH le marque comme non-recommandé.
- **`/skillz-doctor` peut faire des faux positifs** : version 1 minimale, on étend selon usage réel.
