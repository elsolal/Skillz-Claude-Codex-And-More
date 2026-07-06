---
status: approved
approved_by: aymeric
approved_at: 2026-07-05
date: 2026-07-05
slug: epctr-v6
title: "D-EPCT+R v6 — Source unique, boucle qualité agentic, niveaux adaptatifs"
---

# D-EPCT+R v6 — Design

## 1. Contexte et objectifs

La chaîne D-EPCT+R v5.1 (`/dev`, `/discovery`, `/quick-fix`, `/ship`) fonctionne bien mais date d'une génération de techniques d'agentic coding. Trois problèmes constatés dans le repo :

1. **Duplication divergente** : chaque workflow existe en deux exemplaires complets (`commands/*.md` en français pour Claude Code, `skills/*-workflow/SKILL.md` en anglais pour Codex CLI). Des divergences de fond existent déjà (ex. le gate verification-before-completion présent dans `commands/dev.md` §5.0, absent de `skills/dev-workflow/SKILL.md`).
2. **Review one-shot, pas de boucle** : les 3 passes Correctness/Readability/Performance tournent une fois, sans contre-vérification des findings, sans re-review après correction, sans critère de convergence. L'utilisateur doit relire le code pour avoir confiance.
3. **Vérification non stack-agnostique** : `npm run lint && npm run typecheck && npm test` en dur avec un « adapt to project » vague ; la `verification-matrix.md` couvre 4 stacks.

**Objectifs de la v6** (décisions de cadrage validées par Aymeric le 2026-07-05) :

- **Une seule source de vérité** par workflow : le skill est canonique, la commande est un lanceur.
- **Checkpoint humain unique** : le plan. Ensuite le workflow tourne en autonomie jusqu'à une PR prête.
- **Boucle qualité agentic** qui remplace la relecture humaine du code : l'utilisateur lit un rapport de gate, jamais le diff — avec un filet humain sur les tâches à risque (niveaux 3-4).
- **Stack-agnostique** : fonctionne sur n'importe quel type de projet via un manifeste de vérification sondé.
- Périmètre : toute la chaîne (`/dev`, `/discovery`, `/quick-fix`, `/ship`, `/auto-dev`). Les améliorations brainstorm (inspirées BMAD v6) sont un second temps explicite (§10).

Inspirations retenues de BMAD Method v6.10 (recherche du 2026-07-05) : gate files versionnés (Test Architect), scale-adaptive 0-4 avec escalade automatique, ATDD en phase rouge, contexte par fichiers, `project-context` constitutionnel. Non retenu : le module TEA complet (9 workflows, trop lourd), les personas nommés.

## 2. Architecture cible

```
skills/
├── project-probe/SKILL.md       [NOUVEAU]  Sonde le projet → .agents/verification.yaml
├── quality-gate/SKILL.md        [NOUVEAU]  Boucle qualité → docs/quality/GATE-<slug>.yaml
├── dev-workflow/SKILL.md        [REFONDU]  Source unique /dev — niveaux 0-4, stop unique
├── discovery-workflow/SKILL.md  [REFONDU]  Source unique /discovery — niveaux au lieu de FULL/LIGHT
├── ship-workflow/SKILL.md       [REFONDU]  Consomme le gate file
└── quick-fix-workflow/          [SUPPRIMÉ] Absorbé : niveau 0-1 de dev-workflow

commands/  (lanceurs ≤ 15 lignes chacun)
├── dev.md        → dev-workflow, mode interactif
├── quick-fix.md  → dev-workflow, niveau 0 forcé
├── auto-dev.md   → dev-workflow, mode autonome + pre-flight gate RALPH (inchangé)
├── discovery.md  → discovery-workflow, mode interactif
├── auto-discovery.md → discovery-workflow, mode autonome
└── ship.md       → ship-workflow
```

Conventions :

- Les skills canoniques restent **en anglais** (cohérent avec l'existant, portable multi-runtimes) ; les commandes lanceurs restent en français.
- Chaque skill contient une section **Runtime capabilities** : « si le harnais offre X (subagents parallèles, /code-review, verify, Workflow tool), utilise-le ainsi ; sinon exécute la procédure séquentielle suivante ». Un seul fichier, deux chemins d'exécution. Le Workflow tool de Claude Code est une **optimisation optionnelle**, jamais une dépendance.
- Hors périmètre de cette passe : `/refactor`, `/pr-review` (pourra consommer le gate file plus tard), squads design/SEO, mécanique RALPH (`auto-loop`, `cancel-ralph`, `resume-ralph`), base `knowledge/`.

## 3. `project-probe` — manifeste de vérification

**Rôle** : rendre la vérification stack-agnostique. Invoqué en Phase 0 de tout workflow.

- Si `.agents/verification.yaml` existe et que les fichiers de config du projet n'ont pas changé depuis (hash ou mtime de `package.json`/`Makefile`/`pyproject.toml`/`Cargo.toml`/…) → le lire, ne rien re-sonder.
- Sinon : inspecter le projet (scripts package.json, Makefile, pyproject, CI configs…) et écrire le manifeste :

```yaml
# .agents/verification.yaml — généré par project-probe, committé
stack: node-ts            # détecté
commands:
  lint:      "npm run lint"
  typecheck: "npm run typecheck"
  test:      "npm test"
  build:     "npm run build"
  # une entrée absente = le projet n'a pas cette vérification
testability:
  harness: vitest          # none | <framework>
  runtime_verify: "npm run dev"   # comment lancer l'app pour le skill verify
absents:
  - "no e2e harness"       # toujours explicites, jamais masqués
```

- Un seul fichier, pas de miroir `.claude/` (éviter le drift) ; committé car c'est une vérité du projet, comme `package.json`.
- Toute instruction « vérifie lint/types/tests » des skills v6 référence ce manifeste. Une commande absente du manifeste est **notée dans le gate file** (`absents`), jamais silencieusement sautée.
- La `verification-matrix.md` existante est conservée comme table de fallback pour le sondage initial.

## 4. `quality-gate` — la boucle qualité

**Rôle** : remplacer la relecture humaine par une boucle bornée de preuve. Réutilisé par `/dev` (Phase 5), `/ship` (gate absent/périmé) et `/auto-dev`.

**Entrées** : diff (`git diff main...HEAD`), plan validé (critères d'acceptance), manifeste de vérification, niveau de la tâche.

**La boucle** (bornée : niveau 1 → 1 tour ; niveau 2 → max 3 tours ; niveaux 3-4 → max 4 tours) :

1. **Preuves d'exécution** — toujours en premier, jamais skippées : toutes les commandes du manifeste. Si le harnais offre le skill `verify` : piloter le flow réel de l'app (pas seulement les tests). Rouge → fix immédiat, le tour recommence.
2. **Reviews multi-lentilles** — contextes frais (subagents), alimentés par diff + plan uniquement, pas l'historique. Niveau 1 : 1 reviewer généraliste. Niveau 2+ : correctness/sécurité, lisibilité, performance ; + `design-audit` / `seo-geo-audit` / `a11y-enforcer` si les surfaces concernées ont été détectées en Explore. Sur Claude Code : `/code-review` natif sert de lentille principale (ses verdicts CONFIRMED/PLAUSIBLE alimentent directement l'étape 3) ; sur Codex : passes séquentielles décrites dans le skill.
3. **Contre-vérification adversariale** des findings **nouveaux** uniquement : un vérificateur indépendant par finding, chargé de le réfuter. Registre des findings à identifiant stable (`<fichier>:<règle>:<hash-extrait>`) : un finding réfuté n'est plus jamais re-vérifié ni compté.
4. **Fix** des findings confirmés P0/P1 → retour à l'étape 1.

**Convergence** : 2 tours consécutifs sans finding confirmé nouveau → verdict. Cap atteint sans convergence → verdict `CONCERNS` avec les findings restants listés. Jamais de boucle infinie. Exception niveau 1 (cap = 1 tour) : le verdict se décide sur ce tour unique — confirmés corrigés + preuve exécutable re-passée au vert → `PASS`, sans exigence de second tour.

**Le gate file** — `docs/quality/GATE-<date>-<slug>.yaml`, committé avec la branche, collé dans le corps de la PR :

```yaml
verdict: PASS            # PASS | CONCERNS | FAIL | WAIVED
niveau: 2
tours: 3
diff_hash: "sha256 du diff évalué"   # fraîcheur : /ship recalcule et compare
preuve:
  executable:            # la seule base possible d'un PASS
    lint:   { cmd: "npm run lint", statut: vert }
    types:  { cmd: "tsc --noEmit", statut: vert }
    tests:  { cmd: "npm test", statut: "vert (47 passed, 3 RED→GREEN)" }
    verify: { flow: "login → refresh → logout", statut: vert }
  opinion:
    findings: { total: 9, confirmés: 4, réfutés: 5, corrigés: 4, restants: 0 }
decisions_prises_en_ton_nom:
  - "<toute déviation du plan validé, avec sa raison>"
absents:
  - "<vérifications que le projet n'a pas — jamais masquées>"
```

**Règles de verdict** :

- `PASS` exige : tout le vert sur la preuve exécutable disponible ET zéro finding confirmé restant ET au moins une preuve exécutable réelle (tests ou verify). Un projet sans aucune preuve exécutable **plafonne à `CONCERNS`** — le gate ne peut pas prétendre plus que ce qu'il sait.
- `WAIVED` n'existe qu'à la demande explicite de l'utilisateur, avec raison dans le fichier.
- `decisions_prises_en_ton_nom` liste toute décision prise en autonomie qui dévie du plan validé. **C'est la seule lecture attentive qui reste à l'utilisateur.**

## 5. `dev-workflow` v6 — phases et niveaux

```
Phase 0 · PROBE     project-probe + lecture CLAUDE.md / project-memory. Silencieux.
Phase 1 · EXPLORE   Issue + codebase (subagent Explore si dispo). Détections
                    frontend/SEO/risque. Évaluation du niveau.
Phase 2 · PLAN      ⛔ STOP UNIQUE (mode interactif) : synthèse explore + niveau
                    + plan d'étapes + critères d'acceptance + stratégie de test,
                    en un seul écran. L'utilisateur valide/ajuste/change le niveau.
Phase 3 · RED       Tests d'acceptance en échec AVANT l'implémentation —
                    conditionnel (voir ci-dessous).
Phase 4 · IMPLEMENT Étape par étape : code + tests unitaires + vérif manifeste
                    à chaque étape. Séquentiel par défaut.
Phase 5 · GATE      Boucle quality-gate jusqu'à convergence → gate file.
Phase 6 · HANDOFF   Rapport : verdict, décisions prises en ton nom, diff stats.
                    Niveaux 0-2 : propose /ship. Niveaux 3-4 : exige la lecture
                    de decisions_prises_en_ton_nom avant de proposer /ship.
```

**Grille des niveaux** (détection en Phase 1, inspirée BMAD scale-adaptive) :

| Niveau | Signaux | Circuit |
|---|---|---|
| **0** | typo, constante, style ; ≤3 fichiers, ≤50 lignes | Fix direct → vérif manifeste → présentation. Pas de plan, pas de RED, pas de gate file. |
| **1** | petit bug, ajustement localisé | Explore léger → mini-plan ⛔ → fix → gate 1 tour, 1 reviewer. |
| **2** | feature standard, 1 composant | Flow complet. |
| **3** | multi-composants, surface publique, UI riche | Flow complet + lentilles design/SEO/a11y dans le gate + filet humain en Phase 6. |
| **4** | epic, migration, auth, schéma DB, données | Refus de démarrer sans spec approuvée (`docs/planning/specs/` avec frontmatter `status: approved`) → renvoi vers `/discovery`. Puis stories traitées en 2-3, filet humain. |

**Escalade automatique** : si l'explore ou l'implémentation révèle un scope supérieur (4ᵉ fichier touché en niveau 0, changement de schéma découvert en niveau 2…), le workflow monte de niveau **en réutilisant l'acquis** et le signale — il ne recommence pas et n'exige pas de relance manuelle.

**RED conditionnel** (correction Rodin) : la phase RED n'a lieu que si niveau ≥ 2 ET `testability.harness ≠ none` dans le manifeste. Sinon : les critères d'acceptance sont vérifiés au runtime (skill `verify` : piloter l'app) et le gate note `absents: ["no test harness — acceptance verified at runtime"]`.

**Fin du duo Code Agent + Test Agent parallèles** : l'implémentation est séquentielle par étape, chaque étape livre code + tests + vérification verte. La parallélisation de deux étapes est permise **uniquement** si leurs fichiers sont disjoints — et avec isolation worktree si le harnais l'offre. C'est l'exception explicite, pas le défaut.

**Modes** (portés par la commande lanceuse) :

- `interactif` (`/dev`) : stop Phase 2 + filet niveau 3-4.
- `niveau 0 forcé` (`/quick-fix`) : circuit court, escalade auto possible.
- `autonome` (`/auto-dev`) : zéro stop ; le pre-flight gate RALPH existant (mandat = issue GitHub ou spec approuvée) remplace le stop plan ; la mécanique RALPH (logs, itérations, promise) est conservée telle quelle.

## 6. `ship-workflow` v6

Mécanique conservée : pre-flight, merge origin/main, changelog, commits bisectables, push, PR, non-interactivité.

Changement : **la Pre-Landing Review (Step 4 actuel) est remplacée par la consommation du gate file** :

- Gate `PASS` et frais (le diff n'a pas changé depuis sa génération — comparaison du hash de diff enregistré dans le gate) → PR directe, gate file dans le corps.
- Gate absent, périmé ou `CONCERNS`/`FAIL` → `/ship` lance (ou relance) `quality-gate` lui-même avant de continuer.
- Une seule définition de la qualité dans tout le système ; les gates design/SEO de l'actuel Step 4 vivent désormais dans les lentilles de quality-gate.

## 7. `discovery-workflow` v6

- FULL/LIGHT remplacé par les niveaux : **0-1** → tech-spec courte directement (pas de PRD — Quick Flow) ; **2-3** → chaîne actuelle Brainstorm → (UX) → PRD → (UI) → Architecture → Stories ; **4** → chaîne complète + exigences NFR/sécurité formalisées comme critères de gate pour le dev.
- **Escalade** : une tech-spec qui révèle un scope 2+ devient l'entrée du PRD — l'acquis est réutilisé.
- Les specs produites portent le frontmatter (`status`, `approved_by`, `approved_at`) que le pre-flight `/auto-dev` sait déjà lire — la chaîne planning → dev autonome se referme.
- Les checkpoints de validation par phase sont conservés (le planning est l'endroit où l'humain doit être dans la boucle).
- Améliorations brainstorm : second temps (§10).

## 8. Corrections issues du challenge Rodin (traçabilité)

| # | Correction | Intégrée en |
|---|---|---|
| 1 | Force de preuve explicite dans le gate ; PASS impossible sans preuve exécutable | §4 règles de verdict |
| 2 | Boucle bornée + registre des findings réfutés + CONCERNS si non convergé | §4 la boucle |
| 3 | RED conditionnel à la testabilité détectée | §5 RED conditionnel |
| 4 | Section « décisions prises en ton nom » + filet humain niveaux 3-4 | §4 gate file, §5 Phase 6 |
| 5 | Migration par vagues ; réutilisation des briques natives (/code-review, verify) | §9, §4 étape 2 |

Risque résiduel assumé : le même modèle code, review et contre-vérifie (contextes frais ≠ indépendance totale). Mitigation : domination des preuves d'exécution sur les opinions, filet humain 3-4. Un PASS n'est pas une garantie absolue — c'est un niveau de preuve documenté.

## 9. Migration en 3 vagues (réversible)

| Vague | Contenu | Test de sortie |
|---|---|---|
| **1** | Créer `project-probe` + `quality-gate` ; brancher sur la chaîne existante (Phase 4 de l'actuel `/dev` appelle la boucle ; `verification-matrix.md` référence le manifeste) | Un `/dev` réel produit un gate file correct sur un projet Node et un projet Python |
| **2** | Refondre `dev-workflow` (niveaux, stop unique, RED conditionnel) ; `commands/dev.md`, `quick-fix.md`, `auto-dev.md` deviennent lanceurs ; supprimer `quick-fix-workflow` | `/quick-fix` et `/dev` niveaux 0-3 validés en usage réel ; escalade 0→2 observée |
| **3** | `ship-workflow` consomme le gate ; `discovery-workflow` passe aux niveaux ; `auto-discovery.md` lanceur ; mise à jour `install.sh`, `README`, `AGENTS.md`/`CLAUDE.md` (tableau des workflows) | Chaîne complète issue → PR sans relecture, gate dans le corps de PR |

Chaque vague = une branche + PR distincte. L'ancienne version reste dans git — rollback trivial.

## 10. Second temps (hors périmètre, à ne pas oublier)

- **Brainstorm/elicitation** (inspiration BMAD v6.8-6.10) : menu de lentilles « Advanced Elicitation » (Pre-mortem, Inversion, First Principles, Red/Blue Team) comme second-pass structuré sur la sortie d'une phase ; « anti-consensus room » dans `multi-mind` ; pressure-test d'idée type `forge-idea` en amont de `/discovery`.
- `/pr-review` consomme le gate file.
- Decision-log canonique par run (type `memlog`), à raccorder à `/wiki-capture-session`.

## 11. Références

- Recherche BMAD Method v6.10 (2026-07-05, session Claude) : scale-adaptive 0-4, Test Architect gate files PASS/CONCERNS/FAIL/WAIVED, ATDD, story-context, project-context, party mode anti-consensus.
- Repo actuel : `commands/dev.md`, `skills/dev-workflow/SKILL.md`, `skills/ship-workflow/SKILL.md`, `skills/quick-fix-workflow/SKILL.md`, `skills/discovery-workflow/SKILL.md`, `commands/auto-dev.md`, `.claude/knowledge/workflows/verification-matrix.md`.
- Principes : superpowers verification-before-completion, adversarial verification loops, loop-until-dry.

## 12. Errata post-implémentation (vague 1)

Les SKILL.md en arbre sont canoniques ; les extraits verbatim de ce document et du plan vague 1 sont figés à la date d'approbation. Corrections apportées pendant l'implémentation (commits ee597d6, da9fab2 et batch de la review finale) :

- `git diff main...HEAD` → détection de la branche par défaut (`<base>` = `main`, sinon `master`) dans quality-gate et ses appelants.
- Exception niveau 1 : les préconditions PASS s'appliquent aussi — sans preuve exécutable, CONCERNS même en 1 tour.
- Clés du gate file en ASCII sans accents : `confirmes`, `refutes`, `corriges` (contrat de parsing pour /ship en vague 3) ; l'exemple du §4 avec accents est obsolète.
- Un restart sur preuve rouge consomme un tour du cap ; preuve impossible à verdir dans le cap → verdict FAIL.
- Le fingerprint de project-probe couvre aussi `justfile` et `.github/workflows/*.yml`.
- La règle de fraîcheur du gate exclut aussi `CHANGELOG.md` (le bookkeeping de /ship ne périme pas le gate) — vague 3.
