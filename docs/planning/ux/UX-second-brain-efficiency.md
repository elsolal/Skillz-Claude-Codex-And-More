---
title: UX Design - Second-brain efficiency and observability
date: 2026-07-16
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
trigger: auto
source: brainstorm
source_file: docs/planning/brainstorms/BRAINSTORM-second-brain-efficiency-2026-07-16.md
depth: standard-targeted-cli
---

# UX Design — Second-brain efficiency and observability

## 1. Contexte UX

La V1 est une expérience CLI et agentique, pas une application graphique. Elle doit rendre la mémoire automatiquement utile tout en permettant aux humains de voir la route suivie, comprendre les preuves utilisées, corriger une information obsolète et partager une configuration portable.

Les acteurs automatisés exécutent le contrat, mais les personas humains restent propriétaires de la confiance, du sens et de la confidentialité.

## 2. Personas

### Persona principal — Aymeric, opérateur multi-projets

| Attribut | Détail |
|---|---|
| **Profil** | Utilise quotidiennement plusieurs agents de coding sur de nombreux repos et plusieurs vaults Obsidian synchronisés par Git. |
| **Objectif principal** | Reprendre une tâche avec le bon contexte sans répéter l'historique ni charger une mémoire excessive. |
| **Objectifs secondaires** | Comparer les agents, préserver les décisions projet, réduire le rework et prouver l'utilité des mini-cerveaux. |
| **Frustrations** | Pointeurs présents mais non lus, index trop volumineux, mémoire périmée, configuration différente selon les runtimes, absence de preuve d'utilisation. |
| **Motivations** | Continuité entre sessions, exécution rapide, qualité source-backed, partage des connaissances et contrôle du coût. |
| **Contexte d'usage** | Terminal macOS, Codex/Claude Code/autres agents, passages fréquents entre projets, sessions courtes ou longues. |
| **Niveau technique** | Expert ; accepte les détails quand ils servent une décision, mais ne veut pas administrer une plateforme de mémoire. |
| **Critère de confiance** | Le reçu montre ce qui a été chargé et utilisé ; le repo courant reste prioritaire ; les contradictions sont visibles. |

### Persona secondaire — Collaborateur projet

| Attribut | Détail |
|---|---|
| **Profil** | Développeur, designer, PM ou contributeur qui clone un repo projet et accède au mini-cerveau partagé correspondant. |
| **Objectif principal** | Obtenir rapidement le contexte projet maintenu par l'équipe sans connaître l'organisation personnelle d'Aymeric. |
| **Objectifs secondaires** | Installer la mémoire sur sa machine, comprendre les conventions, retrouver les décisions et proposer une correction reviewable. |
| **Frustrations** | Chemins absolus non portables, dépendances implicites, vault non cloné, QMD absent, page d'entrée cassée, vocabulaire mémoire inconnu. |
| **Motivations** | Onboarding plus rapide, décisions traçables, moins de questions répétées, contribution par Git. |
| **Contexte d'usage** | Machine et agent potentiellement différents ; accès limité au projet ; niveau variable en Obsidian et QMD. |
| **Niveau technique** | Intermédiaire à expert sur son métier, novice possible sur le memory system. |
| **Critère de confiance** | L'installation explique quoi faire, échoue proprement et ne demande aucun accès aux mémoires hors projet. |

### Acteurs automatisés — non-personas

| Acteur | Responsabilité UX |
|---|---|
| **CLI `memory`** | Appliquer le manifeste, récupérer, mesurer et produire des sorties déterministes. |
| **QMD** | Rechercher localement dans les collections autorisées et fournir scores, extraits et chemins. |
| **Agent de coding** | Utiliser le contexte récupéré, citer ce qui influence la réponse et signaler les contradictions. |
| **Git / CI** | Partager les manifests, golden questions et rapports agrégés ; valider les contrats portables. |

## 3. Principes UX issus des personas

1. **Zéro configuration cachée** — toute dépendance manquante doit produire une prochaine action exacte.
2. **Progressive disclosure** — une ligne de reçu par défaut, détails accessibles sans bruit permanent.
3. **Project isolation** — un collaborateur ne voit jamais une mémoire transverse non autorisée.
4. **Repo-first trust** — toute contradiction donne priorité à la preuve actuelle du repo.
5. **Human meaning ownership** — l'agent propose les corrections ; l'humain valide le sens et la confidentialité.

## 4. User journeys

### Journey A — Reprendre une tâche avec le bon contexte

#### Vue d'ensemble

```text
Demande utilisateur
  -> manifeste détecté
  -> reçu de route et budget
  -> recherche QMD projet
  -> sufficiency gate
      -> suffisant : contexte borné
      -> insuffisant et autorisé : fallback Elsolal
  -> vérification du repo courant
  -> travail de l'agent
  -> reçu final + événement local
```

| Étape | Action | Objectif | Émotion | Friction possible | Réponse UX |
|---|---|---|---|---|---|
| 1. Détection | L'agent exécute `memory context` depuis le repo. | Identifier le contrat mémoire sans intervention. | Neutre | Manifeste absent ou invalide. | Diagnostic court et commande exacte pour corriger. |
| 2. Route prévue | Le CLI affiche projet, fallback et budget. | Rendre le comportement prévisible. | Confiant | Reçu trop verbeux. | Une ligne par défaut, détails avec `--explain`. |
| 3. Récupération | QMD interroge la collection projet. | Obtenir le minimum pertinent. | Attentif | Résultats faibles ou obsolètes. | Score, fraîcheur et provenance alimentent le sufficiency gate. |
| 4. Fallback | Elsolal est interrogé uniquement si autorisé et nécessaire. | Ajouter du contexte transverse sans polluer chaque tâche. | En contrôle | Fallback personnel inaccessible au collaborateur. | Pas de fallback implicite ; continuer avec un statut `project-only`. |
| 5. Travail | L'agent confronte mémoire et repo avant d'agir. | Éviter une décision basée sur un historique périmé. | Productif | Contradiction silencieuse. | Repo prioritaire et avertissement de dette mémoire. |
| 6. Bilan | Le reçu final liste pages utilisées, impact et budget réel. | Comprendre la valeur de la mémoire. | Rassuré | Confondre pages trouvées et utilisées. | États séparés `retrieved/read/used/cited`. |

#### Moment critique

- **Satisfaction** : le reçu explique en une ligne qu'une convention ou décision a été réutilisée sans lecture de l'index complet.
- **Friction majeure** : le routeur ne trouve rien mais l'agent prétend avoir utilisé la mémoire. La télémétrie du CLI doit rendre ce cas impossible à présenter comme un succès.

### Journey B — Onboarder un collaborateur sur un mini-cerveau

#### Vue d'ensemble

```text
Clone du repo de code
  -> memory doctor
  -> lecture de .agents/memory.yaml
  -> détection du vault local
      -> présent : validation
      -> absent : commande de clone proposée
  -> génération des pointeurs locaux
  -> création/validation de la collection QMD
  -> premier memory context de démonstration
```

| Étape | Action collaborateur | Objectif | Friction possible | Réponse UX |
|---|---|---|---|---|
| 1. Diagnostic | Lance `memory doctor`. | Comprendre ce qui manque. | Liste d'erreurs techniques. | Résumé `ready / degraded / blocked`, puis actions ordonnées. |
| 2. Accès | Clone le repo mémoire autorisé. | Obtenir le vault projet partagé. | Remote privé ou droit manquant. | Distinguer clairement accès Git refusé et configuration locale absente. |
| 3. Projection | Génère les pointeurs locaux. | Adapter le contrat portable à sa machine. | Peur de committer des chemins absolus. | Confirmation que les fichiers générés sont ignorés et contrôle Git. |
| 4. QMD | Ajoute ou met à jour la collection. | Rendre la mémoire recherchable. | QMD absent ou embeddings longs. | Recherche lexicale disponible avant embeddings ; progression explicite. |
| 5. Premier succès | Exécute une question de démonstration. | Prouver immédiatement la valeur. | Test abstrait ou non pertinent. | Utiliser une golden question propre au projet. |

#### Moment critique

- **Satisfaction** : un seul `memory doctor` produit une séquence d'actions reproductible.
- **Friction majeure** : demander l'accès à Elsolal. Le collaborateur reste strictement dans le vault projet, sauf autorisation explicite dans le manifeste.

### Journey C — Gérer une contradiction mémoire ↔ repo

#### Vue d'ensemble

```text
Page mémoire récupérée
  -> preuve actuelle du repo incompatible
  -> priorité au repo
  -> avertissement visible
  -> classification du risque
      -> faible : continuer + dette mémoire
      -> élevé : demander arbitrage
  -> feedback utile/obsolète/incorrect
  -> proposition de patch ou capture
  -> validation humaine
```

| Étape | Action | Objectif | Friction possible | Réponse UX |
|---|---|---|---|---|
| 1. Détection | L'agent compare le claim à la source courante. | Éviter une action obsolète. | Comparaison impossible. | Marquer `non vérifié` plutôt que conclure. |
| 2. Continuité | Le repo devient la référence active. | Ne pas bloquer les tâches à faible risque. | Avertissement ignoré. | Inclure la dette dans le reçu final. |
| 3. Arbitrage | L'humain intervient si produit, architecture, sécurité ou données changent. | Préserver le sens. | Trop d'interruptions. | Seuil de risque explicite, pas de confirmation systématique. |
| 4. Réparation | L'agent prépare une correction source-backed. | Réduire le coût de maintenance. | Écriture automatique dangereuse. | Aucun changement mémoire sans validation humaine. |

### Journey D — Revue hebdomadaire en dix minutes

#### Vue d'ensemble

```text
memory report --weekly
  -> memory doctor
  -> agrégation JSONL locale
  -> classement des dettes
  -> 3 à 7 arbitrages maximum
  -> corriger / ignorer / différer
  -> rapport Markdown régénéré
```

| Étape | Action | Objectif | Friction possible | Réponse UX |
|---|---|---|---|---|
| 1. Génération | Le CLI produit le digest. | Éviter la collecte manuelle. | Rapport trop long. | Cap de 7 arbitrages, reste disponible en annexe. |
| 2. Priorisation | Les problèmes sont classés par impact réel. | Traiter ce qui a affecté une tâche. | Pages anciennes mais sans usage mises en tête. | Usage réel et risque priment sur l'âge seul. |
| 3. Décision | Aymeric choisit corriger, ignorer ou différer. | Garder le contrôle. | Même alerte répétée. | `snooze_until` ou risque accepté avec justification. |
| 4. Partage | Seuls les agrégats autorisés vont dans le vault. | Informer l'équipe sans exposer les sessions. | Fuite cross-vault. | Filtrage par projet avant génération du Markdown. |

### Journey E — Fonctionnement dégradé sans QMD

```text
memory context
  -> QMD indisponible
  -> lecture bornée des pages d'entrée du manifeste
  -> statut degraded
  -> reçu avec limite explicite
  -> commande d'installation ou de réparation
```

Règles UX :

- Une tâche `minimal` ou `project` peut continuer avec les pages d'entrée si elles existent.
- Une tâche `historical` ne prétend jamais être couverte sans moteur de recherche ; elle demande l'installation de QMD ou un arbitrage.
- Le système ne télécharge pas automatiquement un modèle lourd sans information préalable.
- Le reçu final distingue `memory available` de `retrieval fully operational`.

## 5. Décisions de parcours

| Décision | Justification | Alternative écartée |
|---|---|---|
| Rechercher depuis la tâche | Réduit le contexte non pertinent. | Lire l'index systématiquement. |
| Projet avant Elsolal | Respecte isolation et pertinence. | Recherche fédérée par défaut. |
| Continuer sans QMD en mode borné | Le memory system ne doit pas bloquer le code. | Échec total si QMD manque. |
| Bloquer seulement les contradictions à risque | Limite les interruptions. | Demander confirmation à chaque divergence. |
| Cap de 7 arbitrages hebdomadaires | Protège la contrainte de dix minutes. | Exposer toute la dette à chaque revue. |

## 6. Wireframes textuels CLI

### Surface A — `memory doctor`

**Objectif** : dire en moins de dix secondes si le projet est prêt et fournir les actions exactes dans l'ordre.

```text
Memory Doctor · Pleepole-back
Status: DEGRADED · 4/5 checks ready

[ok] manifest       .agents/memory.yaml · schema v1
[ok] project vault  pleepole-memory · access granted
[ok] local pointer  generated · ignored by Git
[!!] qmd collection pleepole-wiki · index 16 days old
[ok] entry pages    3/3 available

Next action
  qmd update
  qmd embed

Then verify
  memory doctor

Details: memory doctor --explain
Machine output: memory doctor --json
```

| État | Sortie attendue |
|---|---|
| **Ready** | Une ligne de succès et la golden question de démarrage. |
| **Degraded** | Le travail peut continuer, avec les capacités indisponibles clairement nommées. |
| **Blocked** | Cause unique prioritaire, commande suivante exacte et exit code non nul. |
| **No manifest** | Expliquer que le repo n'est pas activé ; ne jamais inventer un vault. |
| **Access denied** | Distinguer remote privé, credentials Git et chemin local manquant. |

### Surface B — Reçu initial de `memory context`

**Objectif** : rendre la route et le budget visibles sans interrompre le travail.

```text
Memory · PROJECT · Pleepole
Route: pleepole-wiki -> elsolal-wiki if insufficient and authorized
Budget: 2,500 estimated tokens · task: architecture
Status: retrieving project context…
```

Après récupération :

```text
Memory ready · project-only · 4 retrieved · 2 selected · ~840/2,500 tokens
Freshness: current · confidence: high · event: mem_01J...
```

Avec détails :

```text
$ memory context --explain

Selected
  #a1b2c3  wiki/entities/pleepole-back.md          score 0.86 · fresh
  #d4e5f6  wiki/concepts/proven-quality-gate.md   score 0.72 · fresh

Rejected
  #112233  wiki/index.md                           score 0.18 · below threshold

Fallback
  Elsolal not used · project context sufficient
```

| État | Sortie attendue |
|---|---|
| **Sufficient** | Retourner le contexte borné et ne pas consommer le reste du budget. |
| **Fallback used** | Nommer la raison déterministe du passage à Elsolal. |
| **Project-only** | Signaler que le fallback personnel n'est pas autorisé sans présenter cela comme une erreur. |
| **No result** | Retourner `insufficient`, ne jamais produire un reçu de succès. |
| **QMD missing** | Lire seulement les pages d'entrée autorisées et marquer `degraded`. |
| **Budget overflow** | Exiger `risk_reason`; sinon s'arrêter au budget. |

### Surface C — Reçu final

**Objectif** : distinguer les événements mesurés de l'usage attesté par l'agent.

```text
Memory final · event mem_01J...
Measured:  4 retrieved · 2 read · ~840/2,500 tokens · 1.2s
Attested:  2 used · 2 cited
Impact:    project convention applied · validation command reused
Health:    fresh · no conflict · no fallback
Sources:   #a1b2c3 · #d4e5f6
```

Règles :

- `retrieved`, coût, durée, scores et fraîcheur sont émis par le CLI.
- `read` est confirmé par une récupération de corps ou de plage de lignes via le CLI.
- `used`, `cited` et `impact` sont attestés par l'agent et libellés comme tels.
- Un docid `used` doit appartenir au jeu `retrieved`; sinon le reçu est invalide.
- Une absence d'impact est acceptable et ne doit pas être maquillée en succès.

### Surface D — Contradiction mémoire ↔ repo

**Objectif** : protéger la tâche tout en rendant la dette réparable.

```text
Memory conflict · HIGH RISK

Historical claim
  #a1b2c3 · "Use index-first retrieval for every project query"

Current evidence
  .claude/project-memory.md · direct project page before broad search

Decision
  Current repository evidence takes precedence.
  Human arbitration required before changing the shared memory contract.

Actions
  [c] continue with repository evidence
  [i] inspect both sources
  [p] prepare a source-backed memory patch
```

Mode agent/non interactif :

```json
{
  "status": "conflict",
  "risk": "high",
  "precedence": "repository",
  "requires_human": true,
  "next_actions": ["continue", "inspect", "prepare_patch"]
}
```

### Surface E — Revue hebdomadaire

**Objectif** : limiter l'entretien à quelques décisions à forte valeur.

```text
Memory Weekly · 2026-07-16
Scope: local detail + shareable project aggregates
Review estimate: 8 minutes · 5 decisions

P0  1 broken entry page used by 3 repos
P1  2 stale pages contradicted current code
P1  pleepole-wiki index 16 days behind local changes
P2  1 budget overflow with accepted security reason
P3  4 unused retrieved pages suggest a noisy query

Actions
  memory report --item 1 --prepare-fix
  memory report --item 2 --snooze 7d
  memory report --export-markdown

Privacy
  0 prompts · 0 answers · 0 cross-vault raw events
```

| État | Sortie attendue |
|---|---|
| **No action** | `Healthy · no human decision required this week`. |
| **1-7 decisions** | Montrer impact, priorité et action exacte. |
| **More than 7** | Afficher les 7 premières et placer le reste en annexe. |
| **Insufficient telemetry** | Dire que la tendance est non concluante. |
| **Export** | Retirer tout événement détaillé avant génération du Markdown partagé. |

### Surface F — Premier succès collaborateur

**Objectif** : terminer l'onboarding par une preuve propre au projet.

```text
Memory ready · Pleepole

Try the project golden question
  memory context --mode project \
    --query "Quelle règle empêche de dupliquer une notification ?"

Expected
  project memory only · cited source · context below project budget
```

Le CLI ne doit pas afficher une question générique de démonstration si le manifeste fournit un cas projet.

## 7. Heuristiques UX

| Heuristique | Application au CLI | Statut |
|---|---|---|
| **Visibilité du statut** | Chaque commande retourne `ready`, `degraded`, `insufficient`, `conflict` ou `blocked`. | Conforme |
| **Correspondance système/réel** | Employer `vault`, `repo`, `page`, `source`, `budget` et `freshness`, définis dans le glossaire mémoire. | Conforme |
| **Contrôle utilisateur** | `--explain`, correction différée, purge locale, risk override justifié et aucune écriture automatique du wiki. | Conforme |
| **Cohérence** | Même structure de reçu et mêmes statuts en sortie humaine et JSON. | Conforme |
| **Prévention des erreurs** | Validation du manifeste, docids utilisés limités au jeu récupéré, priorité au repo et isolation des vaults. | Conforme |
| **Reconnaissance plutôt que rappel** | `memory doctor` affiche les commandes suivantes ; le manifeste fournit une golden question de démarrage. | Conforme |
| **Flexibilité** | Sortie compacte par défaut, `--explain` pour les experts et `--json` pour agents/CI. | Conforme |
| **Design minimaliste** | Une ligne pour le chemin nominal ; les détails et rejets restent masqués par défaut. | Conforme |
| **Récupération d'erreur** | Chaque état bloquant nomme une cause prioritaire, une action exacte et un exit code stable. | Conforme |
| **Aide et documentation** | `memory <command> --help`, exemples projet et distinction claire entre configuration portable et locale. | À spécifier dans le PRD. |

## 8. Accessibilité et robustesse des sorties

### Principes obligatoires

1. **Aucune information uniquement par couleur** — les libellés `[ok]`, `[!!]`, `READY`, `DEGRADED` et `BLOCKED` restent explicites avec ou sans ANSI.
2. **Ordre stable** — statut, route, budget, résultats, action suivante et identifiant d'événement apparaissent toujours dans le même ordre.
3. **Plain text complet** — `NO_COLOR=1` ou sortie non-TTY désactive couleurs, spinners et animations sans perte d'information.
4. **JSON versionné** — `--json` expose un `schema_version` et des champs stables, sans mélanger les messages humains sur stdout.
5. **stdout/stderr distincts** — données et contexte exploitable sur stdout ; diagnostics et progression sur stderr.
6. **Exit codes documentés** — succès, dégradé, configuration invalide, dépendance manquante, résultat insuffisant et conflit à arbitrer sont distinguables.
7. **Commandes copiables** — aucune ellipse ni placeholder ambigu dans la prochaine action proposée.
8. **Chemins sûrs** — affichage logique/relatif par défaut ; chemins absolus uniquement avec `--explain-local`.
9. **Langage clair** — une erreur dit ce qui manque, pourquoi cela compte et quelle commande lancer ensuite.
10. **Pas d'interaction forcée** — toute commande interactive possède une variante non interactive pour agents et CI.

### Matrice des canaux

| Canal | Usage | Garantie |
|---|---|---|
| **TTY humain** | Reçu compact et actions copiables. | Lisible sans couleur et sans largeur minimale stricte. |
| **Lecteur d'écran** | Ordre linéaire et libellés explicites. | Aucun tableau indispensable dans le chemin nominal. |
| **Agent** | `--json` et docids stables. | Aucun parsing du texte décoratif requis. |
| **CI** | Exit codes et JSON agrégé. | Aucun prompt interactif, spinner ou téléchargement implicite. |
| **Obsidian/Git** | Rapport Markdown généré. | Agrégats uniquement, liens relatifs et aucune donnée de session brute. |

### États de chargement

- En TTY : progression textuelle discrète avec étape courante et durée.
- En non-TTY : événements de progression sur stderr ou silence avec `--quiet`.
- Aucun téléchargement de modèle QMD sans taille annoncée et consentement dans le parcours humain.
- Un timeout retourne le dernier état connu et une commande de reprise ; il ne transforme pas l'absence de réponse en résultat vide.

## 9. Décisions UX consolidées

| Décision | Justification | Alternatives écartées |
|---|---|---|
| Deux personas humains, agents comme acteurs | Le sens, la confiance et la confidentialité restent humains. | Concevoir uniquement pour le runtime agent. |
| UX CLI standard ciblée | Les parcours sont complexes mais sans surface graphique. | Design d'application ou simple aide de commande. |
| Reçu début + fin | Rend prévision et consommation comparables. | Silence total ou bilan final uniquement. |
| Mesuré vs attesté | Évite une fausse objectivité sur l'usage réel. | Présenter toutes les métriques comme techniques. |
| Dégradation bornée sans QMD | Le memory system ne bloque pas le travail courant. | Échec total ou prétendue recherche historique. |
| Repo prioritaire | Le code et les contrats courants restent la vérité immédiate. | Laisser la mémoire historique gagner silencieusement. |
| Sept arbitrages maximum | Rend crédible la revue en dix minutes. | Dashboard exhaustif hebdomadaire. |
| Sortie humaine + JSON versionné | Sert humains, agents, CI et accessibilité sans double logique. | Parser la sortie terminal humaine. |

## 10. Checklist de complétude UX

| Critère | Statut |
|---|---|
| Fichier créé dans `docs/planning/ux/` | OK |
| Deux personas humains définis | OK |
| Cinq parcours documentés | OK |
| Six surfaces CLI wireframées | OK |
| Heuristiques vérifiées | OK |
| Accessibilité CLI documentée | OK |
| Décisions UX justifiées | OK |

**Score : 7/7**

## 11. Questions ouvertes

- Les seuils du sufficiency gate seront définis et testés dans le PRD puis l'architecture.
- Le mode `historical` sans QMD reste `blocked` par défaut.
- Le reçu affiche des identifiants logiques et liens relatifs, jamais les chemins absolus par défaut.
- Le protocole exact par lequel l'agent atteste `used/cited/impact` reste à définir dans l'architecture.
- Les exit codes et le schéma JSON seront contractualisés dans l'architecture.
