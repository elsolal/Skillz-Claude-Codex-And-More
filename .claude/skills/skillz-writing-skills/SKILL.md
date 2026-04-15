---
name: skillz-writing-skills
description: Guide la création ou la modification d'un skill Skillz-Claude. Utiliser quand l'utilisateur demande "crée un skill", "ajoute un skill", "améliore ce skill", ou quand on doit ajouter/refactorer un fichier dans .claude/skills/. Garantit cohérence avec le vocabulaire D-EPCT+R, RALPH, et conventions FR du projet. Inspiré de superpowers/writing-skills mais réécrit pour notre stack.
---

# Skillz-Writing-Skills — Méta-skill création de skills

Tu es en train de créer ou modifier un skill dans `.claude/skills/`. Suis ce guide pour rester cohérent avec les 34 skills existants.

## Quand utiliser

- L'utilisateur dit "crée un skill X", "ajoute un skill", "fais un skill qui…"
- Tu vas modifier un `SKILL.md` existant (refactor, amélioration de la description, fix de comportement)
- Tu observes qu'un workflow récurrent mériterait d'être un skill réutilisable

## Quand NE PAS utiliser

- Pour créer une **commande slash** (`.claude/commands/*.md`) → c'est une autre couche d'abstraction, écris directement la commande
- Pour modifier `CLAUDE.md` → c'est de la doc projet, pas un skill
- Pour ajouter un fichier de **knowledge** (`.claude/knowledge/`) → pas de structure SKILL.md à respecter

## Process

### 1. Comprendre le besoin (1 min)

Avant d'écrire :

- Quel est le **trigger** ? Quand ce skill doit s'activer ?
- Quel est l'**output** attendu ? (un document, du code, une décision, une question à l'utilisateur)
- Existe-t-il déjà un skill qui couvre ce besoin ? (`ls .claude/skills/ | grep <mot-clé>`)
- Qui est l'utilisateur cible ? (toi en mode autonome, l'orchestrateur principal, un subagent ?)

Si un skill existant couvre déjà 70%+ du besoin → **modifier** plutôt que créer.

### 2. Choisir l'emplacement et le nom

- Emplacement : `.claude/skills/<nom-du-skill>/SKILL.md`
- Nom : kebab-case, descriptif, sans préfixe "skill-"
- Exemples bons : `code-implementer`, `pm-prd`, `figma-implement-design`
- Exemples mauvais : `helper`, `utility`, `skill-coder` (préfixe redondant)

### 3. Écrire le frontmatter (le plus important)

```yaml
---
name: <nom-du-skill>          # kebab-case, identique au nom de dossier
description: <1-3 phrases>    # voir règles ci-dessous
---
```

**Règles pour `description`** (c'est ce que Claude lit pour décider si activer le skill) :

- Commence par un verbe d'action : "Conçoit…", "Implémente…", "Audit…", "Génère…"
- Inclut **explicitement les triggers** : "Utiliser quand l'utilisateur dit X, ou quand Y se produit, ou quand le contexte est Z"
- Inclut **la sortie** : "Produit un document/code/rapport en…"
- 50-200 caractères pour description courte, jusqu'à 500 si triggers complexes

Mauvais : `description: helper for testing`
Bon : `description: Écrit et exécute les tests pour valider l'implémentation. Priorités P0-P3, risk-based. Utilisé comme agent worker depuis /dev ou en standalone.`

### 4. Structure du SKILL.md

Sections recommandées (dans cet ordre, omet ce qui n'apporte rien) :

```markdown
---
name: ...
description: ...
---

# Titre du skill

## Quand utiliser
- Triggers explicites, scénarios concrets

## Quand NE PAS utiliser
- Cas d'usage adjacents qui devraient utiliser un autre skill/commande

## Process
### 1. Étape 1 (titre actionnable)
### 2. Étape 2
### 3. Étape 3

## Output attendu
- Format précis (chemin de fichier, structure, contenu type)

## Exemples
[1-3 exemples concrets, pas d'abstrait]

## Anti-patterns
- À éviter, et pourquoi
```

### 5. Vocabulaire et conventions

- **Langue** : FR par défaut (cohérence projet). EN OK si le skill est purement technique sans contexte projet.
- **Workflow vocabulary** : D-EPCT+R, RALPH, Discovery, /dev, /quick-fix — utiliser ce vocabulaire quand pertinent
- **Phases** : Explore → Plan → Implement → Review → Ship (référencer les phases si applicable)
- **Pas de jargon LLM** : éviter "I will analyze", "let me think", "as an AI". Écrire en mode procédural.
- **Pas d'over-engineering** : KISS. Un skill = un objectif clair. Si tu décris 5 sous-skills, c'est 5 skills séparés.

### 6. Tester le skill

Avant de considérer le skill comme prêt :

1. **Self-review** : relire le frontmatter — est-ce qu'un Claude qui voit cette description saura quand l'utiliser ?
2. **Test session** : démarrer une session test, énoncer un trigger naturel, voir si Claude active le skill
3. **Cohérence** : vérifier qu'aucun autre skill ne se déclenche aussi (sinon clarifier la frontière dans les descriptions)

### 7. Documenter

- Mentionner le nouveau skill dans `CLAUDE.md` si c'est un workflow majeur (sinon non, la liste des skills est déjà longue)
- Si le skill est appelé par une commande slash, lier les deux explicitement dans la commande

## Output attendu

Un fichier `.claude/skills/<nom>/SKILL.md` :
- Frontmatter `name` + `description` riche en triggers
- Sections claires, FR, vocabulaire D-EPCT+R/RALPH
- < 200 lignes typiquement (sinon découper en plusieurs skills)
- Au moins 1 exemple concret
- Pas de copie de texte d'autres skills (DRY)

## Exemples de bons skills (modèles)

- `code-implementer/SKILL.md` — workflow worker depuis /dev, scope clair
- `pm-prd/SKILL.md` — output bien défini, triggers explicites
- `dev-workflow/SKILL.md` — exécution séquentielle runtime-agnostic, exemple de doc soigné

## Anti-patterns

| Symptôme | Pourquoi c'est mauvais | Fix |
|---|---|---|
| Description vague ("helper for X") | Claude n'activera jamais le skill | Reformuler avec triggers concrets + verbe d'action |
| Skill > 500 lignes | Trop de scopes mélangés | Découper en 2-3 skills orthogonaux |
| Description en EN, contenu en FR (ou inverse) | Incohérence avec le projet | Aligner sur la langue du projet (FR par défaut) |
| Importer du texte d'un skill upstream sans réécrire | Risque licence + incohérence vocabulaire | Réécrire avec nos termes (D-EPCT+R, RALPH, etc.) |
| Pas d'exemple concret | Skill abstrait, peu utilisable | Ajouter au moins 1 exemple end-to-end |
| Pas de "Quand NE PAS utiliser" | Skill sur-déclenché | Lister explicitement les cas adjacents avec leur skill correct |

## Référence

Inspiré de la philosophie `superpowers/writing-skills` (obra/superpowers), réécrit pour le vocabulaire D-EPCT+R + RALPH + multi-agent + FR de Skillz-Claude. Pas de dépendance runtime, pas de copie de contenu.
