---
title: PRD - Observable second-brain efficiency
author: Aymeric
date: 2026-07-16
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
version: 1.0
level: 4
project_type: cli_tool
domain: general
pilot_repositories: [Skillz-Claude, Pleepole-back]
---

# PRD — Observable second-brain efficiency

## 1. Executive Summary

### Vision

Permettre à un humain ou un agent de reprendre un projet avec le minimum de mémoire pertinente, de voir ce qui a réellement été récupéré et utilisé, puis de prouver que cette mémoire améliore le travail sans sacrifier la justesse pour économiser des tokens.

### Proposition de valeur

Pour Aymeric et les collaborateurs qui travaillent avec plusieurs agents sur des repos reliés à des mini-cerveaux Git, le produit fournit une récupération mémoire bornée, portable et observable. Contrairement au workflow actuel `index-first`, il part de la tâche, privilégie le vault projet, n'élargit la recherche que si nécessaire et mesure séparément coût, qualité, fraîcheur et usage attesté.

### Pourquoi maintenant

- La mémoire compilée dépasse désormais le volume qu'un index central peut raisonnablement injecter à chaque requête.
- Les pointeurs mémoire sont largement présents mais la chaîne d'autoload complète n'est pas systématique.
- Les mini-cerveaux partagés existent, mais Git, QMD et les pages d'entrée peuvent diverger sans signal commun.
- Le workflow canonique `index-first` contredit le workflow projet plus récent et consomme beaucoup plus de contexte.
- Aucune mesure ne relie actuellement récupération mémoire, tokens, qualité et maintenance.

### Objectifs

| Objectif | Métrique principale | Cible pilote |
|---|---|---|
| Réduire le contexte mémoire inutile | Tokens mémoire estimés médians | -50 % vs baseline `index-first` |
| Préserver la qualité | Exactitude/couverture sur golden questions et holdouts | Dégradation maximale de 5 % |
| Rendre l'activation prouvable | Événements CLI émis pour les récupérations pilotes | 100 % |
| Rendre la mémoire partageable | Manifeste portable et pages d'entrée valides | 100 % des deux pilotes |
| Limiter la maintenance | Temps humain hebdomadaire | <= 10 minutes |

## 2. Problème

### 2.1 Problème principal

Le système Obsidian + `llm-wiki` + QMD contient de la connaissance durable, mais il ne peut pas démontrer qu'un agent la consulte au bon moment, qu'il récupère seulement ce qui est nécessaire, ni que le résultat est plus utile que la redécouverte depuis le repo.

### 2.2 Symptômes observés

- Lecture systématique d'un index volumineux avant de connaître le besoin réel.
- Pointeurs présents mais non chargés par certains runtimes ou repos.
- Pages d'entrée manquantes et pointeurs qui deviennent eux-mêmes des documents d'architecture.
- Collections QMD et branches Git dont la fraîcheur varie entre vaults.
- Confusion possible entre pages trouvées, lues, utilisées et citées.
- Absence de preuve que les économies de contexte correspondent à des économies provider ou à moins de rework.
- Partage GitHub sans contrat portable reliant repo, vault, collections, owners et politiques.

### 2.3 Solution actuelle

L'utilisateur ou l'agent lit un pointeur local, parfois l'index du vault, ouvre plusieurs pages puis utilise QMD si le catalogue ne suffit pas. La maintenance combine captures, ingests, lint, Git et réindexation manuelle. Cette approche fonctionne, mais son activation et son coût ne sont ni bornés ni observables.

## 3. Utilisateurs et Jobs to Be Done

### 3.1 Personas

| Persona | Description | Besoins principaux |
|---|---|---|
| **Aymeric** | Opérateur expert multi-projets et multi-agents. | Continuité, contrôle, faible rework, comparaison des routes et preuve de valeur. |
| **Collaborateur projet** | Contributeur autorisé sur un repo et son mini-cerveau. | Installation portable, isolation, onboarding et correction reviewable. |

Les agents, QMD et Git/CI sont des acteurs automatisés, pas des propriétaires du sens.

### 3.2 Jobs to Be Done

1. Quand je reprends une tâche projet, je veux récupérer automatiquement les décisions pertinentes sans relire le vault entier.
2. Quand une mémoire influence le travail, je veux voir les pages utilisées, le coût estimé et les décisions concernées.
3. Quand un collaborateur clone le repo, je veux qu'il puisse reconstruire la liaison mémoire sans chemins ou accès personnels.
4. Quand le repo contredit le wiki, je veux continuer avec la preuve courante et réparer la dette sous contrôle humain.
5. Chaque semaine, je veux arbitrer uniquement les problèmes mémoire qui ont réellement affecté le travail.

## 4. Scope

### 4.1 Pilotes V1

- Repo outillage : `Skillz-Claude` + vault Elsolal.
- Repo produit/code : `Pleepole-back` + vault Pleepole.
- Au moins 20 récupérations réelles par pilote.
- Dix golden questions par projet, dont 20 % en holdout rotatif.

### 4.2 Fonctionnalités MVP

| ID | Fonctionnalité | Description | Priorité |
|---|---|---|---|
| F-01 | Manifeste mémoire portable | Décrire collections, pages d'entrée, owners, fallbacks, allowlists et politiques sans chemin machine. | P0 |
| F-02 | Projection locale | Générer et vérifier les pointeurs locaux ignorés à partir du manifeste. | P0 |
| F-03 | `memory context` | Transformer la tâche en récupération bornée `minimal`, `project` ou `historical`. | P0 |
| F-04 | Cascade projet -> transverse | Interroger le projet puis Elsolal seulement si insuffisant, autorisé et utile. | P0 |
| F-05 | Sufficiency gate | Décider le fallback avec règles déterministes puis auto-évaluation limitée aux cas ambigus. | P0 |
| F-06 | Reçus début/fin | Afficher route, budget, résultats, fraîcheur, sources et impact attesté. | P0 |
| F-07 | Télémétrie locale | Journaliser des événements metadata-only, locaux, purgeables et retenus 30 jours. | P0 |
| F-08 | `memory doctor` | Vérifier manifeste, projection locale, accès au vault, pages d'entrée, QMD, Git et fraîcheur. | P0 |
| F-09 | Conflits et feedback | Donner priorité au repo, signaler la dette et préparer une correction validée humainement. | P1 |
| F-10 | `memory test` | Exécuter golden questions, holdouts et comparaisons qualité/contexte. | P0 |
| F-11 | `memory report` | Générer le digest hebdomadaire et le rapport Markdown agrégé. | P1 |
| F-12 | Profil docs/contrats | Autoriser une collection séparée de docs, ADR, PRD, OpenAPI et schémas sélectionnés. | P1 |

### 4.3 Hors scope V1

- Indexation complète du code dans Obsidian ou QMD.
- Graphify comme dépendance obligatoire.
- Dashboard web ou application graphique.
- Service de télémétrie hébergé ou base distante.
- Capture automatique de toutes les sessions.
- Rapprochement exact de facturation entre tous les providers.
- Déploiement aux 53 repos détectés.
- Accès d'un collaborateur à Elsolal sans autorisation explicite.

### 4.4 Futures options

- Collection technique jetable avec métadonnées/symboles du code.
- Adapter Graphify pour les questions structurelles non couvertes.
- Adapters provider pour input, cached input et output tokens réels.
- Rapport transverse multi-vault strictement agrégé.
- Automatisation optionnelle de la revue hebdomadaire.

## 5. Exigences fonctionnelles

### Manifeste et activation

- **FR-001** — Le produit doit découvrir `.agents/memory.yaml` depuis le repo courant.
- **FR-002** — Le manifeste doit être portable et ne contenir aucun chemin absolu obligatoire.
- **FR-003** — Le produit doit générer les pointeurs locaux nécessaires sans les rendre éligibles au commit.
- **FR-004** — `memory doctor` doit détecter un pointeur suivi par Git, une page d'entrée absente ou une collection inconnue.
- **FR-005** — Le manifeste doit définir owner, vault projet, remote mémoire, collections, pages d'entrée, fallbacks, allowlists et golden question de démarrage.

### Récupération et budgets

- **FR-006** — `memory context` doit accepter un mode `minimal`, `project` ou `historical` et une catégorie de tâche sans conserver la demande originale.
- **FR-007** — Le mode `project` doit interroger la collection projet avant toute mémoire transverse.
- **FR-008** — Le fallback doit être interdit si le manifeste ne l'autorise pas.
- **FR-009** — Le sufficiency gate doit utiliser au minimum score, nombre de résultats, fraîcheur, provenance et type de tâche.
- **FR-010** — Le produit doit s'arrêter dès que le contexte est suffisant, même si le budget n'est pas consommé.
- **FR-011** — Un dépassement doit exiger une catégorie `risk_reason` et apparaître dans le reçu final.
- **FR-012** — Sans QMD, les modes `minimal` et `project` doivent pouvoir lire un jeu borné de pages d'entrée ; `historical` doit rester bloqué.
- **FR-013** — La recherche dans `wiki/index.md` complet doit être un fallback observable, jamais une étape obligatoire.

### Reçus, preuves et conflits

- **FR-014** — Le reçu initial doit afficher mode, route, budget, projet et statut de récupération.
- **FR-015** — Le reçu final doit séparer `retrieved`, `read`, `used` et `cited`.
- **FR-016** — `retrieved/read`, durée, scores, tokens estimés et fraîcheur doivent provenir du CLI.
- **FR-017** — `used/cited/impact` doivent être marqués comme attestations de l'agent.
- **FR-018** — Un docid attesté `used` ou `cited` doit appartenir aux résultats de l'événement.
- **FR-019** — Une contradiction avec le repo doit donner priorité à la source courante et produire une dette mémoire.
- **FR-020** — Une contradiction à risque produit, architecture, sécurité ou données doit demander un arbitrage humain.
- **FR-021** — Le produit peut préparer une correction, mais ne doit jamais modifier automatiquement le sens d'une page mémoire partagée.

### Observabilité et maintenance

- **FR-022** — Chaque récupération pilote doit produire un événement local avec un identifiant unique.
- **FR-023** — L'événement ne doit contenir ni prompt, ni réponse, ni transcript, ni secret.
- **FR-024** — Les événements détaillés doivent expirer après 30 jours par défaut et pouvoir être purgés immédiatement.
- **FR-025** — Les rapports partagés doivent contenir uniquement des agrégats filtrés par projet.
- **FR-026** — `memory report --weekly` doit limiter le chemin nominal à sept arbitrages maximum.
- **FR-027** — Un problème observé doit pouvoir être corrigé, ignoré avec justification ou différé avec une date.

### Tests et rollout

- **FR-028** — `memory test` doit exécuter dix golden questions par projet.
- **FR-029** — Au moins 20 % des questions doivent pouvoir rester hors du jeu visible par le workflow testé.
- **FR-030** — Les tests doivent comparer pages/sources attendues, qualité de réponse et contexte mémoire estimé.
- **FR-031** — Le rollout doit être refusé si l'une des dimensions qualité, efficacité, usage ou maintenance échoue.
- **FR-032** — L'adoption post-pilote doit rester modulaire par projet.

## 6. Exigences non fonctionnelles et sécurité

### 6.1 Performance

- **NFR-PERF-001** — Le parsing du manifeste et la décision de route doivent ajouter moins de 300 ms p95, hors processus QMD.
- **NFR-PERF-002** — `memory doctor` doit terminer ses contrôles locaux en moins de 2 s p95, hors opération réseau ou réindexation.
- **NFR-PERF-003** — Une recherche QMD chaude en mode projet doit viser moins de 5 s p95 sur les deux machines pilotes.
- **NFR-PERF-004** — Aucun modèle ou dépendance lourde ne doit être téléchargé implicitement pendant une tâche agent.

### 6.2 Fiabilité

- **NFR-REL-001** — Une panne de QMD ne doit pas bloquer le travail courant `minimal/project` si les pages d'entrée sont disponibles.
- **NFR-REL-002** — Une recherche vide, timeout ou erreur ne doit jamais être présentée comme une récupération réussie.
- **NFR-REL-003** — Les événements doivent être append-only ; une dernière ligne JSONL corrompue doit être diagnostiquée sans perdre les événements précédents.
- **NFR-REL-004** — Les sorties JSON doivent inclure `schema_version`; les changements incompatibles exigent une nouvelle version.
- **NFR-REL-005** — Les exit codes doivent distinguer succès, dégradé, configuration invalide, dépendance absente, insuffisance et conflit à arbitrer.

### 6.3 Sécurité et confidentialité

- **NFR-SEC-001** — La télémétrie locale doit être créée avec des permissions limitant l'accès à l'utilisateur courant quand la plateforme le permet.
- **NFR-SEC-002** — Aucun contenu de requête ou de réponse ne doit être persisté par défaut.
- **NFR-SEC-003** — Aucun événement détaillé ne doit traverser les frontières de vault ou être committé.
- **NFR-SEC-004** — Les chemins absolus ne doivent apparaître que dans une sortie locale explicitement demandée.
- **NFR-SEC-005** — Les chemins de manifeste doivent être résolus sans traversal hors des racines autorisées.
- **NFR-SEC-006** — Les commandes externes doivent être appelées sans interpolation shell de valeurs issues du manifeste.
- **NFR-SEC-007** — Les allowlists docs/contrats doivent exclure secrets, fichiers d'environnement, credentials, logs et artefacts générés.
- **NFR-SEC-008** — Le fallback transverse doit être refusé par défaut pour un collaborateur et activé uniquement par politique explicite.
- **NFR-SEC-009** — Toute exportation Markdown doit appliquer un contrôle metadata-only avant écriture.

### 6.4 Accessibilité et scriptabilité

- **NFR-AX-001** — Aucune information ne doit dépendre exclusivement de la couleur.
- **NFR-AX-002** — `NO_COLOR=1`, non-TTY et `--json` doivent préserver toute l'information fonctionnelle.
- **NFR-AX-003** — stdout doit contenir la donnée exploitable et stderr la progression/les diagnostics.
- **NFR-AX-004** — Toute action corrective affichée doit être copiable et non ambiguë.
- **NFR-AX-005** — Toute commande interactive doit proposer un mode non interactif.

### 6.5 Maintenabilité

- **NFR-MNT-001** — La V1 ne doit exiger aucun service hébergé ni base distante.
- **NFR-MNT-002** — La logique métier doit être indépendante du rendu humain/JSON et du moteur QMD.
- **NFR-MNT-003** — Les contrats manifest, événement et sortie doivent disposer de fixtures et tests de compatibilité.
- **NFR-MNT-004** — Le digest hebdomadaire doit rester arbitrable en moins de 10 minutes dans les pilotes.

## 7. Métriques et gate de succès

| Métrique | Cible | Méthode |
|---|---|---|
| Validité d'activation | 100 % des deux pilotes | `memory doctor` + CI manifest |
| Golden retrieval | >= 90 % page et source attendues dans la première route bornée | `memory test` |
| Qualité des réponses | Dégradation <= 5 % vs baseline non bornée | Rubrique versionnée + holdout |
| Réduction du contexte | >= 50 % de réduction médiane vs `index-first` | Tokens mémoire estimés |
| Fallback index complet | < 10 % des récupérations | Événements locaux |
| Télémétrie pilote | 100 % des récupérations émises | Comptage événements/commandes |
| Fraîcheur QMD | Mise à jour <= 24 h après merge mémoire | Git + état collection |
| Maintenance humaine | <= 10 min/semaine | Durée déclarée de la revue |
| Confidentialité | 0 prompt, réponse, secret ou événement cross-vault | Tests + scan des exports |
| Preuve réelle | >= 20 récupérations par pilote | Compteur local agrégé |

### Gate composite

Le pilote passe uniquement si :

1. Le manifeste et les pages d'entrée sont valides sur les deux repos.
2. La qualité ne dépasse pas la dégradation maximale.
3. La réduction médiane du contexte atteint la cible.
4. Les 40 récupérations réelles minimales ont été observées.
5. Le digest reste sous dix minutes de maintenance.
6. Aucun incident de confidentialité ou d'isolation n'est détecté.

Un échec bloque le rollout global mais n'empêche pas de conserver une sous-fonction utile sur un pilote.

## 8. Risques

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Optimisation des tokens au détriment de la qualité | Moyenne | Élevé | Gate couplé qualité/contexte et risk override. |
| Agent qui sur-déclare `used` | Élevée | Moyen | Libellé `attested`, validation docid et échantillons réels. |
| Golden-set overfitting | Moyenne | Élevé | 20 % holdout rotatif et tâches réelles nettoyées. |
| QMD absent ou froid | Moyenne | Moyen | Dégradation bornée, doctor et aucun téléchargement implicite. |
| Manifeste trop complexe | Moyenne | Moyen | Schéma V1 minimal, exemples pilotes et compatibilité testée. |
| Fuite de données par télémétrie | Faible | Élevé | Metadata-only, 30 jours, permissions locales et scans d'export. |
| Drift Git/QMD/wiki | Élevée | Élevé | Freshness checks, digest et statut explicite. |
| Maintenance supérieure à la valeur | Moyenne | Élevé | Cap de sept arbitrages et gate <= 10 minutes. |
| Index technique du code bruyant | Moyenne | Moyen | Hors V1 ; collection séparée et allowlist si expérimenté. |

## 9. Déroulé pilote

| Phase | Sortie attendue | Gate |
|---|---|---|
| Baseline | Questions, routes actuelles, tokens estimés et qualité de référence. | Baseline reproductible. |
| Activation | Manifests Skillz-Claude/Pleepole-back et projections locales. | `memory doctor` ready ou degraded accepté. |
| Retrieval | `memory context`, cascade, budgets et reçus. | Tests fonctionnels + aucun accès non autorisé. |
| Observabilité | JSONL 30 jours, `memory test`, rapport Markdown. | Metadata-only et schémas stables. |
| Usage réel | 20 récupérations par pilote. | Gate composite calculable. |
| Décision | Conserver, ajuster, modulariser ou arrêter. | Verdict documenté avant rollout. |

Aucune date calendrier ni promesse de déploiement global n'est attachée au PRD. Le pilote progresse par preuves.

## 10. Critères d'acceptation produit

- [ ] Un nouveau clone de chaque repo pilote peut reconstruire sa configuration mémoire à partir du manifeste partagé.
- [ ] Une tâche projet utilise QMD projet avant tout fallback transverse.
- [ ] Une tâche sans résultat ne produit jamais de reçu de succès.
- [ ] Une tâche sans QMD continue en mode borné ou bloque proprement en `historical`.
- [ ] Le reçu final distingue mesure et attestation.
- [ ] Une contradiction risquée demande un arbitrage et donne priorité au repo.
- [ ] Les événements locaux expirent après 30 jours et sont purgeables.
- [ ] Le rapport partagé ne contient aucune donnée brute de session.
- [ ] Les golden questions, holdouts et récupérations réelles permettent de calculer le gate composite.
- [ ] Le rollout global reste bloqué tant que le gate n'est pas satisfait.

## 11. Questions réservées à l'architecture

- Schéma exact de `.agents/memory.yaml` et stratégie de versionnement.
- Valeurs initiales des budgets `minimal/project/historical`.
- Seuils et ordre précis du sufficiency gate.
- Protocole d'attestation `used/cited/impact`.
- Taxonomie des exit codes et schéma JSON public.
- Estimateur de tokens provider-neutral et adapters provider optionnels.
- Emplacement local portable des événements selon la plateforme.

## 12. Références

- `docs/planning/forge/FORGE-second-brain-token-efficiency-2026-07-16.md`
- `docs/planning/brainstorms/BRAINSTORM-second-brain-efficiency-2026-07-16.md`
- `docs/planning/ux/UX-second-brain-efficiency.md`
- `.claude/skills/llm-wiki/`
- `scripts/create-project-memory-pointer.sh`
- `scripts/setup-wiki.sh`
