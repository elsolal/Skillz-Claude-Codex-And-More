# Le workflow D-EPCT+R v6

> Retour au [README](../README.md). La source de vérité reste les skills `discovery-workflow`,
> `dev-workflow`, `quality-gate` et `ship-workflow` sous `core/skills/` : cette page les résume.

L'orchestrateur (le fil principal de la conversation) garde **tout** le contexte. La rigueur s'adapte
au niveau de la tâche. Quand le périmètre grandit, la tâche est reclassée dans la grille en
réutilisant tout le travail déjà fait : on monte de niveau, on ne repart jamais de zéro.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLANIFIER (/discovery — niveaux 0-4)                                       │
│  [P] mise à l'épreuve → niveau 0-1 : tech-spec directe ────┐                │
│                       → niveau 2-4 : Brainstorm → [UX] →    ├→ SPEC         │
│                         PRD → [UI] → Architecture → Stories ┘   APPROUVÉE   │
│                                                                             │
│  DÉVELOPPER (/dev — niveaux 0-4)                                            │
│  PROBE → EXPLORE → PLAN ⛔ → RED → IMPLEMENT → GATE (boucle) → HANDOFF       │
│  manifeste +niveau  l'unique (cond.) (séquentiel)  gate file    rapport     │
│                     arrêt                                                   │
│                                                                             │
│  LIVRER (/ship)                                                             │
│  merge de la branche par défaut → preuves → gate → changelog → PR           │
├─────────────────────────────────────────────────────────────────────────────┤
│  UN SEUL ARRÊT HUMAIN : le PLAN ⛔ — les niveaux 3-4 ajoutent une lecture    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## La grille des niveaux

`/dev`, `/quick-fix` et `/discovery` partagent la même grille.

| Niveau | Signaux | Circuit de `/dev` |
|---|---|---|
| **0** | coquille, constante, style ; ≤ 3 fichiers, ≤ 50 lignes, aucun risque | Correctif → vérification du manifeste → présentation. Ni plan, ni gate file. |
| **1** | petit bug localisé, un groupe de fichiers | Exploration légère → mini-plan ⛔ → correctif → gate en 1 round, 1 relecteur avec contrôle rapide des défauts structurels. |
| **2** | feature standard, un composant | Circuit complet : plan ⛔, RED, implémentation séquentielle, gate ≤ 3 rounds + lentille finale thermo-nucléaire. |
| **3** | plusieurs composants, surface publique, UI riche | + lentilles design / SEO / a11y dans le gate, et lecture humaine du handoff. |
| **4** | epic, migration, auth, schéma de base, données | Refuse de démarrer sans spec approuvée : passer par `/discovery`, puis exécuter story par story en niveau 2-3. |

`/quick-fix` démarre au niveau 0 et monte automatiquement si le périmètre grandit.

---

## `/discovery` : de l'idée à la spec approuvée

1. **Niveau** : évalué de 0 à 4. `[P]` propose d'abord une mise à l'épreuve socratique de l'idée
   (rapport : thèse, objections, noyau qui survit, verdict). On n'investit dans le planning que si le
   noyau tient.
2. **Niveau 0-1** : tech-spec directe, sans brainstorm ni PRD complet.
3. **Niveau 2-4** : Brainstorm → [UX] → PRD → [UI] → Architecture → Stories, validés à chaque étape.
   `[E]` applique une lentille de raisonnement (`/elicit`) avant de valider.
4. **Sortie obligatoire** : une spec consolidée dans `docs/planning/specs/`, avec
   `status: approved`, `approved_by` et `approved_at`. Elle est exigée par `/dev` au niveau 4.
5. Seule la publication des stories sur GitHub est déléguée à un subagent (travail mécanique).

| Point de contrôle | Phase | Condition |
|---|---|---|
| Niveau | 1 | 0-4 évalué, `[P]` proposé |
| Brainstorm → Stories | 2-7 (niveaux 2-4) | Validé à chaque phase, `[E]` disponible |
| **Spec** | 7-bis | **Approuvée par l'humain** |
| Readiness | Stories | Score ≥ 13/15 |

---

## `/dev` : implémenter avec un seul arrêt

| Phase | Ce qui se passe | Condition de sortie |
|---|---|---|
| **0. PROBE** | `project-probe` lit ou rafraîchit `.agents/verification.yaml` | Manifeste à jour |
| **1. EXPLORE** | Lecture de l'issue (`gh issue view`), exploration du code, détection des surfaces frontend et SEO/GEO, évaluation du niveau | Niveau annoncé et justifié |
| **2. PLAN ⛔** | Étapes atomiques (quoi, où, comment, contraintes), critères d'acceptation testables, stratégie de test P0-P3 | **L'humain valide** : c'est l'unique arrêt |
| **3. RED** | Si niveau ≥ 2 et qu'un harnais de test existe : tests d'acceptation écrits et lancés pour prouver qu'ils échouent pour la bonne raison | Tests rouges |
| **4. IMPLEMENT** | Étapes exécutées dans l'ordre, chacune avec ses tests ; commandes du manifeste au vert avant l'étape suivante | Tout vert |
| **5. GATE** | Commit, puis boucle `quality-gate` sur le diff commité | Gate file (PASS ou waiver explicite) |
| **6. HANDOFF** | Rapport : verdict, findings, `decisions_prises_en_ton_nom`, absences, stats du diff | Niveaux 3-4 : l'humain lit les décisions |

Le handoff propose ensuite **[S] `/ship`**, **[C] commit seulement** ou **[R] relancer le gate**. Ce
menu est une décision de livraison, pas un second plan.

Sur Claude Code, l'exploration passe par un subagent Explore et les lentilles du gate tournent en
parallèle. Sur les runtimes séquentiels (Codex, OpenCode, Gemini), les mêmes phases s'exécutent dans
l'ordre, avec le même gate file.

---

## Le moteur qualité

### `project-probe` : savoir comment vérifier

`project-probe` détecte une fois les vraies commandes du projet (lint, typecheck, test, build, run)
et les met en cache dans un manifeste commité :

```yaml
# .agents/verification.yaml
fingerprint_schema_version: 2
generated_by: "project-probe/2.0.0"
stack: node-js
python: { required: "collector >=3.10", selected_interpreter: "python3.12" }
commands: { lint: "npm run lint", test: "npm test" }
command_sources: { lint: "package.json#scripts.lint", test: "package.json#scripts.test" }
testability: { harness: vitest, runtime_verify: "npm run dev" }
absents: ["no e2e harness"]        # explicite, jamais ignoré en silence
```

L'empreinte v2 hache les chemins et le contenu des scripts, skills, manifestes d'agents, CI et
lockfiles consommés. Dans un dépôt Git, seul l'index compte : les fichiers locaux non suivis
n'entrent pas dans la vérité du projet. Vérification :
`bash scripts/run-python310.sh scripts/project_probe.py --root . --check`.

### `quality-gate` : prouver au lieu de relire

Une boucle bornée, dont chaque round suit cet ordre :

1. **Preuves d'exécution**, toujours en premier : toutes les commandes du manifeste, plus le
   parcours réel de l'application quand c'est possible. Le moindre rouge est corrigé et le round
   recommence ; si les preuves ne passent pas au vert dans le plafond, le verdict est `FAIL`.
2. **Revues par lentilles**, chacune dans un contexte neuf : correctness et sécurité (`/code-review`
   natif sur Claude Code), lisibilité, performance, puis design / SEO / a11y si le diff touche ces
   surfaces. Pour le niveau ≥ 2, `thermo-nuclear-code-quality-review` passe en dernier, sur la
   maintenabilité structurelle.
3. **Contre-vérification adverse** : chaque nouveau finding est attaqué par un vérificateur chargé
   de le réfuter. Seuls les findings confirmés sont corrigés ; dans le doute, un finding est réfuté,
   sauf en sécurité.
4. **Correction** des P0/P1 confirmés. Les P2/P3 sont notés sans être corrigés (pas de dérive de
   périmètre).

La boucle converge après deux rounds consécutifs sans nouveau P0/P1, ou s'arrête au plafond du
niveau (1 round au niveau 1, 3 au niveau 2, 4 aux niveaux 3-4). Exception du niveau 1 : le verdict se
décide sur ce round unique, une fois les findings confirmés corrigés et les preuves relancées au vert.

| Verdict | Condition |
|---|---|
| `PASS` | Toutes les preuves au vert, aucun P0/P1 restant, au moins une preuve exécutable réelle |
| `CONCERNS` | Plafond atteint sans convergence, preuves trop faibles, ou P1 non corrigé. Un projet sans tests plafonne ici. |
| `FAIL` | P0 confirmé non corrigé, ou preuves d'exécution impossibles à remettre au vert dans le plafond |
| `WAIVED` | Uniquement sur décision humaine explicite, avec raison, portée, approbateur et date |

Le gate file lie les preuves au diff exact :

```yaml
# docs/quality/GATE-2026-07-06-my-feature.yaml
schema_version: 2
verdict: "PASS"                    # PASS | CONCERNS | FAIL | WAIVED
level: 2
base_sha: "<SHA Git complet>"
head_sha: "<dernier SHA de code>"
code_diff_hash: "<sha256>"
code_diff_exclusions: ["CHANGELOG.md"]
proof_payload: "docs/quality/proofs/2026-07-06-my-feature.json"
proof_payload_hash: "<sha256>"
integrity_sha256: "<sha256 scellé>"
```

`gate_verify.py verify` rejette un code modifié depuis le gate, des preuves retouchées, des SHAs
manquants, des commandes inventées et un PASS contenant une commande en échec. Le JSON de preuve
porte les résultats d'exécution, les findings et les `decisions_prises_en_ton_nom`.

`/gate [niveau]` lance la même boucle à la demande sur n'importe quel diff (niveau 3 par défaut).
Dans ce mode standalone, aucun fichier n'est modifié avant que tu aies arbitré le rapport ; appelé
par `/dev` ou `/ship`, le gate corrige seul.

---

## `/ship` : de la branche à la PR

Non interactif : la prochaine chose que tu vois est l'URL de la PR.

1. **Pré-vol** : refuse de partir depuis la branche par défaut ou avec un arbre de travail sale.
2. **Merge** de la branche par défaut résolue (jamais supposée) dans la branche de feature.
3. **Preuves** : toutes les commandes du manifeste. Rouge → arrêt.
4. **Gate** : un gate v2 PASS valide, un WAIVED complet ou un ancien gate v1 vérifié
   (`legacy-valid`, pendant la fenêtre v6.1) permet d'avancer. Absent, périmé, CONCERNS ou FAIL → le
   gate est relancé. Nouveau CONCERNS → décision de waiver explicite, jamais acceptée
   automatiquement ; nouveau FAIL → arrêt.
5. **CHANGELOG** généré depuis les commits de la branche.
6. **Commits** en petits morceaux cohérents, chacun valide seul.
7. **Push** (jamais de force-push) et **PR** avec le gate file dans la description.

---

## Outils de réflexion

- **`/elicit [lentille] [cible]`** : ré-examine une sortie existante sous **une** lentille nommée
  (Pre-mortem, Inversion, First Principles, Red/Blue Team, Steelman-then-attack, Chesterton's Fence,
  10-10-10, Second-Order Effects, Occam's Razor, Constraint Removal, Persona Shift, Cost-of-Delay).
  La lentille révèle sans réécrire : findings et révisions proposées, tu arbitres. Disponible à
  chaque étape de `/discovery` (`[E]`).
- **`/rodin`** : challenge socratique anti-complaisance (steelman → affirmations classées →
  objections fortes → tests de réalité → verdict), inspiré du
  [rodin.md de Benjamin Debon](https://gist.github.com/bdebon/e22d0b728abc5f393227440907b334cf).
- **`/plan-review`** : relecture CEO/fondateur d'un plan ou d'un PRD (Expansion / Hold / Reduction).
