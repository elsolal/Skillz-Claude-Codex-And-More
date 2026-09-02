# Architecture d’exécution V3

## Sommaire

1. Principes
2. Graphe d’exécution
3. Modes
4. États et reprise
5. Frontières de modules

## 1. Principes

- Router avant de collecter.
- Collecter une fois, réutiliser partout.
- Séparer opérations déterministes et interprétation.
- Paralléliser uniquement les analyses qui lisent des preuves stables.
- Produire toutes les vues depuis les mêmes objets.
- Rendre chaque run rejouable ou expliquer pourquoi il ne l’est pas.

## 2. Graphe d’exécution

```text
intent_router
  ├─ advisory_only → réponse sourcée
  └─ persistent_run
       ↓
scope_and_consent
       ↓
digital_twin ──→ manifest
       ↓
deterministic_collection ──→ evidence_vault
       ↓
coverage_gate
  ├─ insufficient → gaps + demande ciblée
  └─ sufficient
       ↓
technical ─┬─ demand_strategy ─┬─ content ─┬─ authority_local ─┬─ geo_observatory
           └───────────────────┴───────────┴───────────────────┘
                               ↓
fact_and_conflict_resolution
                               ↓
scoring + prioritization
                               ↓
QA gate
  ├─ fail → correction ou limite explicite
  └─ pass → reports / tickets / dashboard
                               ↓
approved_implementation
                               ↓
validation + monitoring + delta
```

## 3. Modes

| Mode | Collecte maximale | Branches |
|---|---:|---|
| Express | Données publiques, 10 à 20 URLs | Technique léger, offre, GEO ciblé |
| Page | 1 URL + pages de comparaison | Technique page, intention, contenu |
| Full | Crawl configuré + connecteurs autorisés | Branches applicables au vertical |
| Content | Pages et sources du thème | Demande, contenu, claims |
| Authority | Sources, citations, entités | Autorité, local, GEO |
| Implement | Aucune nouvelle collecte sauf validation | Action, diff, test, rollback |
| Monitor | Périmètre identique au baseline | Mesures et Delta |

Une limite est un maximum de sécurité, jamais la preuve que la couverture est complète.

## 4. États et reprise

États persistés autorisés : `planned`, `collecting`, `analyzing`, `qa_ready`, `complete`, `paused`, `cancelled`. Les sous-étapes détaillées restent des événements ou des statuts d’action ; elles ne doivent pas créer un second vocabulaire concurrent dans le manifest. Un résultat partiel ou bloqué utilise `paused` avec une raison, un impact et la prochaine condition de reprise.

Chaque transition crée un événement append-only avec `event_id`, `run_id`, horodatage UTC, acteur, ancien état, nouvel état, raison et artefacts. Une reprise :

1. valide le dernier événement ;
2. vérifie les artefacts annoncés ;
3. détecte les écritures partielles ;
4. reprend la première étape non validée ;
5. ne répète pas une action externe déjà confirmée.

## 5. Frontières de modules

- **Audit** : constate et spécifie. Ne publie rien.
- **Build** : produit les ressources en staging. Ne fait pas de prospection.
- **Grow** : contenu, autorité, PR et campagnes approuvées.
- **Monitor** : observe, compare et alerte. Ne réécrit pas l’historique.

Une extension ne doit pas recréer une ressource déjà possédée par un autre module. Elle référence son identifiant et ajoute son propre état.
