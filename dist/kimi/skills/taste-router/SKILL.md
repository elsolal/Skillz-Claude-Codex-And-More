---
name: taste-router
description: Recommande quel taste-skill utiliser (et les valeurs des 3 dials DESIGN_VARIANCE / MOTION_INTENSITY / VISUAL_DENSITY) à partir d'un brief produit ou design. Utiliser quand l'utilisateur dit "quel style", "quel taste-skill", "comment je règle les dials", "design direction", ou avant d'attaquer une implémentation frontend premium.
model: sonnet
allowed-tools:
  - Read
  - Glob
user-invocable: true
---

# Taste Router

Méta-skill qui aide à choisir parmi les 9 `taste-skills` (intégrés depuis github.com/Leonxlnx/taste-skill) et à régler les 3 dials.

## Quand utiliser

- Avant `taste-skill` / `soft-skill` / etc., quand le choix n'est pas évident
- Pendant `pm-prd` ou `ui-designer` pour capturer la direction visuelle
- Quand l'utilisateur arrive avec "je veux que ça soit beau" sans direction précise

## Process

### 1. Charger le contexte

| Source | Action |
|--------|--------|
| PRD existant | `Glob: docs/planning/prd/*.md` → lire le plus récent |
| UX/UI existant | `Glob: docs/planning/{ux,ui}/*.md` |
| Brief direct | Demander à l'utilisateur 3 questions max |

### 2. 3 questions clés (si pas de doc)

1. **C'est quoi ?** Landing marketing / app SaaS / dashboard data / portfolio / e-commerce ?
2. **Vibe ?** Premium calme / éditorial pro / tech raw / minimal / dense info ?
3. **Implémenté par qui ?** Claude / GPT-Codex / Stitch / autre ?

### 3. Recommandation

Présenter une recommandation structurée :

```markdown
## 🎨 Recommandation Taste

**Skill recommandé** : `[name-skill]`
**Raison** : [1 phrase]

**Dials suggérés** :
- DESIGN_VARIANCE : [1-10] — [justification courte]
- MOTION_INTENSITY : [1-10] — [justification courte]
- VISUAL_DENSITY : [1-10] — [justification courte]

**Skills complémentaires** :
- [ ] `output-skill` — si scope > 10 composants
- [ ] `redesign-skill` — si projet existant à upgrader
- [ ] `images-taste-skill` — si on veut des refs visuelles d'abord

**Alternative** : [autre skill envisageable + pourquoi]
```

### 4. Matrice de décision

| Cas | Skill | DESIGN_VARIANCE | MOTION_INTENSITY | VISUAL_DENSITY |
|-----|-------|-----------------|------------------|----------------|
| Landing marketing premium | `taste-skill` | 8 | 7 | 4 |
| Landing GPT/Codex | `gpt-tasteskill` | 8 | 7 | 4 |
| App SaaS calme (Notion-like) | `minimalist-skill` | 4 | 3 | 5 |
| App SaaS premium (Linear-like) | `soft-skill` | 5 | 5 | 5 |
| Dashboard data dense | `taste-skill` | 4 | 4 | 9 |
| Portfolio créatif | `taste-skill` | 9 | 8 | 3 |
| Site éditorial / agence | `soft-skill` | 6 | 6 | 4 |
| Tech tool raw / dev tool | `brutalist-skill` | 7 | 4 | 7 |
| Refonte projet existant | `redesign-skill` | — | — | — |
| Projet visuel-first | `images-taste-skill` | — | — | — |
| Workflow Google Stitch | `stitch-skill` | — | — | — |

### 5. Output

Persister la décision quelque part de discoverable :
- Si dans le flow `pm-prd` → ajouter section `Style direction` au PRD
- Si dans le flow `ui-designer` → ajouter dans `docs/planning/ui/UI-{slug}.md`
- Sinon → afficher uniquement (l'utilisateur copiera dans son prompt)

## Règles

- Ne JAMAIS recommander 2 skills antagonistes (ex: brutalist + soft)
- Ne JAMAIS proposer un dial à 10 sans warner ("⚠️ chaos assumé")
- Toujours proposer 1 alternative pour permettre le choix
- Si le brief est ambigu, demander avant de recommander

## Auto-Chain

Après recommandation acceptée :

```markdown
## 🔗 Prochaine étape

✅ Direction taste choisie : `[skill]` + dials [X/Y/Z]

→ **Invoquer `[skill-name]` maintenant ?** (charge les règles anti-slop précises)
→ Ou **continuer le workflow** (`/ui-designer`, `/dev`, etc.) avec cette direction en contexte
```
