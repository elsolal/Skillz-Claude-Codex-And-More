---
date: 2026-07-16
sujet: Second-brain efficiency and observability
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
approach: ai-recommended
ideas_count: 60
techniques_used: [morphological-analysis, observer-effect, resource-constraints]
domains_explored: [retrieval, knowledge-boundaries, user-experience, value, governance, anti-gaming, privacy, minimal-implementation]
next_step: ux
source_forge: docs/planning/forge/FORGE-second-brain-token-efficiency-2026-07-16.md
---

# Brainstorm — Second-brain efficiency and observability

## Contexte

Le système actuel combine Obsidian, `llm-wiki`, QMD, des pointeurs locaux dans les repos et plusieurs mini-cerveaux projet synchronisés sur GitHub. L'objectif initial était de réduire la consommation de tokens. Le pressure-test a fait pivoter le chantier vers un objectif plus robuste : prouver que la mémoire est utilisée, fraîche, correctement bornée et utile, avec les tokens comme contrainte d'efficacité plutôt que comme objectif isolé.

## Session Stats

- **Approche** : AI-Recommended
- **Idées générées** : 60
- **Techniques** : Morphological Analysis, Observer Effect, Resource Constraints
- **Domaines** : récupération, indexation, expérience, valeur, gouvernance, risques de mesure, confidentialité, MVP
- **Pilotes pressentis** : Skillz-Claude et Pleepole

## Contraintes consolidées

- Git et Markdown restent les couches de gouvernance durable.
- QMD reste un moteur local de recherche, pas une source de vérité.
- Le repo courant reste la source de vérité immédiate pour le code et les contrats.
- Aucun service hébergé ni base distante dans la V1.
- Aucun prompt, réponse complète ou transcript dans la télémétrie.
- Aucun index complet du code dans le wiki.
- Moins de 10 minutes de maintenance humaine hebdomadaire.
- Compatibilité Claude Code, Codex et agents compatibles `AGENTS.md`.

## Toutes les idées générées

### 1. Récupération et architecture fonctionnelle

1. **Task-to-memory retrieval** — La tâche utilisateur devient directement une requête mémoire ciblée au lieu de provoquer la lecture préalable d'un catalogue.
2. **Project-first cascade** — Interroger d'abord le mini-cerveau projet, puis Elsolal uniquement pour les patterns transverses ou l'historique.
3. **Manifest-driven router** — Un manifeste portable décrit les collections, pages pivots, owners et fallbacks autorisés.
4. **Deterministic-first sufficiency gate** — Score, fraîcheur, provenance et type de question décident du fallback ; l'agent arbitre seulement les cas ambigus.
5. **Multi-index trust hierarchy** — Séparer mémoire, documentation, contrats et index technique avec des niveaux de confiance distincts.
6. **Manifest allowlist** — Chaque projet choisit explicitement les dossiers et formats indexables.
7. **Product-and-contract profile** — Donner la priorité aux décisions produit, PRD, vocabulaire métier, runbooks, OpenAPI et schémas.
8. **Disposable code index** — Garder les métadonnées structurelles du code dans une collection séparée, régénérable et non durable.
9. **Tiered context envelope** — Appliquer des budgets différents aux modes `minimal`, `project` et `historical`.
10. **Quality-protected overflow** — Autoriser un dépassement lorsque le risque ou une contradiction le justifie, avec une raison structurée.

### 2. Expérience utilisateur et contrôle

11. **Memory receipt** — Afficher vault, pages, tokens estimés, fraîcheur et confiance après une récupération.
12. **Dual-phase memory receipt** — Annoncer la route prévue au début puis le coût et la route réels à la fin.
13. **Planned-versus-actual context** — Comparer l'enveloppe annoncée au contexte réellement chargé.
14. **Evidence-linked receipt** — Distinguer les pages trouvées de celles réellement utilisées et citées.
15. **Memory influence trace** — Indiquer les décisions influencées : convention appliquée, piège évité, commande réutilisée.
16. **Risk-aware conflict handling** — Prioriser le repo, avertir, puis demander un arbitrage uniquement si la contradiction change une décision risquée.
17. **Memory debt flag** — Transformer une page périmée ou contradictoire en dette mémoire ciblée.
18. **Evidence comparison** — Montrer côte à côte la mémoire historique et la preuve actuelle du repo.
19. **Feedback-to-maintenance loop** — Convertir `utile`, `obsolète` ou `incorrecte` en événement de maintenance.
20. **Human-gated memory repair** — L'agent prépare le patch ou la capture ; l'humain valide le sens et la confidentialité.

### 3. Valeur, exploitation et gouvernance

21. **Memory effectiveness score** — Mesurer qualité et rework avant temps et tokens.
22. **Persona-specific scorecards** — Interpréter la valeur différemment pour Aymeric, un collaborateur, un agent et un projet.
23. **Event-driven maintenance** — Déclencher la maintenance à partir des échecs réels de récupération.
24. **Ten-minute weekly digest** — Générer automatiquement les seuls arbitrages humains nécessaires chaque semaine.
25. **Automated monthly health review** — Auditer couverture, fraîcheur, Git, QMD, tests, budgets et tendances.
26. **Two-level memory ownership** — Aymeric possède les standards transverses ; un domain owner possède le sens dans chaque vault projet.
27. **Ownership in the manifest** — Déclarer owner, reviewers, politique de partage et catégories sensibles dans le manifeste.
28. **Agent-as-maintainer boundary** — Réserver aux agents la maintenance mécanique et aux humains les arbitrages de sens.
29. **Composite rollout gate** — Exiger qualité, économie, usage et maintenance avant tout déploiement.
30. **Modular project adoption** — Permettre à chaque projet d'activer seulement les couches qui créent de la valeur.

### 4. Observer Effect et risques de métriques

31. **Budget-induced under-retrieval** — Un agent peut omettre une source nécessaire pour préserver son score token.
32. **Citation inflation** — Le nombre de citations peut augmenter sans améliorer la preuve.
33. **Retrieved-but-unused memory** — Une page peut être comptée comme utilisée sans influencer le travail.
34. **Unsafe budget obedience** — Un agent peut éviter le mode historique malgré un risque nécessitant plus de contexte.
35. **Self-reported telemetry** — Une mesure déclarée par l'agent lui-même n'est pas suffisamment vérifiable.
36. **Golden-set overfitting** — Le système peut optimiser les questions connues sans s'améliorer sur les tâches réelles.
37. **Paired outcome gate** — Toujours évaluer tokens et qualité ensemble.
38. **Evidence state machine** — Tracer séparément `retrieved`, `read`, `used` et `cited`.
39. **Retrieval tool as measurement authority** — Faire produire les événements techniques par le CLI, pas par le texte de l'agent.
40. **Rotating holdout tests** — Conserver une partie variable des questions hors du workflow optimisé.

### 5. Confidentialité, éthique et visibilité

41. **Privacy-preserving real-session sampling** — Transformer des tâches réelles en scénarios nettoyés et validés.
42. **Accountable risk override** — Associer chaque dépassement à une catégorie de risque auditable.
43. **Metadata-only telemetry** — Stocker projet, route, pages, scores, tokens, durée et fraîcheur sans contenu conversationnel.
44. **Content-free task taxonomy** — Classer architecture, bug, produit ou historique sans conserver la demande originale.
45. **Human-sanitized golden cases** — N'ajouter un cas réel aux tests qu'après nettoyage humain.
46. **Aggregate team reporting** — Partager les tendances sans permettre de reconstruire une session.
47. **Optional repetition fingerprint** — Utiliser éventuellement un hash désactivable pour détecter les recherches répétées.
48. **Three-tier telemetry visibility** — Séparer détail local, santé projet agrégée et tendances transverses anonymisées.
49. **No cross-vault raw telemetry** — Interdire le passage d'événements détaillés entre projets.
50. **User-controlled retention and purge** — Rendre la télémétrie supprimable sans toucher au wiki durable.

### 6. Resource Constraints et MVP

51. **Unified memory CLI** — Exposer `context`, `doctor`, `test` et `report` derrière une commande portable commune.
52. **Context-first core** — Livrer complètement `memory context` avant d'enrichir les autres sous-commandes.
53. **Python policy plane + QMD retrieval plane** — Utiliser Python pour les règles et QMD pour la recherche.
54. **Dependency-light installation** — V1 en bibliothèque standard Python avec dégradation propre si QMD manque.
55. **Portable repository manifest** — Versionner `.agents/memory.yaml` comme contrat machine-neutre.
56. **Generated local projection** — Générer les pointeurs ignorés avec les chemins propres à chaque poste.
57. **Local append-only event log** — Écrire les événements détaillés dans un JSONL local et purgeable.
58. **Generated shareable Markdown report** — Produire depuis le JSONL une synthèse Markdown partageable dans le vault.
59. **Doctor-before-dashboard** — Valider manifeste, pages, Git, QMD et fraîcheur avant de présenter des statistiques.
60. **Test-before-rollout** — Utiliser les golden questions et holdouts comme gate obligatoire du déploiement modulaire.

## Combinaison fonctionnelle retenue

```text
Tâche utilisateur
  -> .agents/memory.yaml
  -> memory context
      -> classification déterministe
      -> QMD projet
      -> sufficiency gate
      -> Elsolal si besoin transverse
      -> budget + éventuel risk override
  -> reçu de début
  -> travail agent sur repo + mémoire
  -> reçu final avec pages utilisées et impact
  -> événement JSONL local
  -> rapports et tests dérivés
```

## Top 5 idées

| # | Idée | Pourquoi elle compte | Potentiel |
|---|---|---|---|
| 1 | Task-aware project-first cascade | Évite l'index central coûteux tout en conservant un fallback transverse | Élevé |
| 2 | Portable manifest + local projection | Rend les mini-cerveaux réellement partageables entre machines et agents | Élevé |
| 3 | Trust-separated knowledge profiles | Sépare mémoire durable, docs, contrats et code jetable | Élevé |
| 4 | Evidence-linked dual receipt | Rend visible ce qui a été prévu, chargé et réellement utilisé | Élevé |
| 5 | Quality-protected observability | Empêche d'optimiser les tokens au détriment de la justesse | Élevé |

## Thèmes émergents

### La mémoire devient une route, pas un préchargement

Le système ne doit plus lire une grande page par réflexe. Il doit transformer la tâche en recherche, appliquer un budget et s'arrêter dès que le contexte est suffisant.

### La portabilité nécessite deux couches

Le manifeste partage le contrat ; les pointeurs générés matérialisent les chemins locaux. Les mélanger dans un même fichier empêche soit le partage, soit l'ergonomie.

### La qualité protège contre la fausse efficacité

Les tokens seuls sont manipulables. La mesure doit relier récupération, usage réel, décision influencée et qualité finale.

### Le code est indexable, mais n'est pas la mémoire

La documentation et les contrats sélectionnés peuvent être recherchés. Un index structurel du code reste optionnel, séparé et régénérable.

### La maintenance suit l'usage

Les dettes mémoire viennent des contradictions, pages périmées et échecs de récupération observés, puis alimentent une revue hebdomadaire très courte.

## Direction recommandée

### V1 pilote

1. Définir le schéma `.agents/memory.yaml`.
2. Implémenter le CLI Python unifié avec `memory context` complet.
3. Router projet -> Elsolal avec un sufficiency gate déterministe-first.
4. Produire les reçus début/fin.
5. Écrire une télémétrie JSONL locale sans contenu utilisateur.
6. Implémenter `memory doctor` pour la validité et la fraîcheur.
7. Créer les golden questions Skillz-Claude et Pleepole.
8. Générer un premier rapport Markdown et appliquer le gate composite.

### Hors V1

- Index complet du code.
- Graphify obligatoire.
- Service de télémétrie hébergé.
- Dashboard interactif.
- Capture automatique de toutes les sessions.
- Déploiement aux 53 repos.

## Score UX/UI

### UX : 4/5 — phase UX requise

- Multi-persona : oui — Aymeric, collaborateurs, agents.
- Parcours complexe : oui — installation, routage, récupération, correction, maintenance.
- Onboarding : oui — clone, génération locale, validation du manifeste.
- Formulaire/wizard : non.
- Première expérience importante : oui — un échec d'installation rend la mémoire invisible.

La phase UX doit rester orientée CLI et parcours, sans produire de maquettes d'écran inutiles.

### UI : 0/4 — phase UI à ignorer

Pas de design system, branding, thème ou surface visuelle complexe dans la V1.

## Questions ouvertes pour le PRD

1. Quels seuils exacts définissent la suffisance et les trois budgets ?
2. Quel schéma minimal de manifeste reste stable entre runtimes ?
3. Comment mesurer `used` sans accepter uniquement l'auto-déclaration de l'agent ?
4. Quelle fraîcheur Git/QMD bloque une réponse plutôt que de produire un avertissement ?
5. Quelles golden questions représentent réellement Skillz-Claude et Pleepole ?

## Prochaine étape

Valider le brainstorm puis produire le parcours UX CLI avant le PRD.
