# Modèle de données et provenance

## Sommaire

1. Chaîne de traçabilité
2. Objets
3. Identifiants
4. Statuts de données
5. Confiance
6. Règles de conflit

## 1. Chaîne de traçabilité

```text
source brute → evidence → fact → finding → action → implementation → outcome
```

Ne jamais sauter directement d’une source brute à une recommandation. Un même fait peut s’appuyer sur plusieurs preuves ; un constat peut référencer plusieurs faits et preuves.

## 2. Objets

### Client / Digital Twin

Contient uniquement des informations approuvées ou explicitement marquées comme hypothèses : identité, entités, offres, prix, zones, personnes, audiences, claims, preuves, concurrents, ton, restrictions et objectifs.

### Manifest

Fige le run : version du kit, mode, périmètre, date, marché, langue, appareil, connecteurs, limites, règles, consentement et versions d’outils/modèles.

### Evidence

Une preuve est immuable. Champs essentiels : identifiant, type, URL ou source, méthode, date de collecte UTC, portée, statut HTTP si pertinent, extrait, emplacement du brut ou hash, contexte, fraîcheur, classification et confiance.

### Fact

Proposition vérifiable soutenue par des preuves. Inclure valeur, unité, période, entité, preuves, statut de validation, propriétaire et date d’expiration.

### Finding

Interprétation utile à une décision. Inclure catégorie, sévérité, dimension de score, URLs affectées, preuves, faits, confiance, impact, limites et règle appliquée.

### Action

Travail exécutable. Inclure résultat attendu, propriétaire, effort, impact, confiance, dépendances, préconditions, procédure, critère d’acceptation, mesure, risque, sauvegarde et rollback.

### GEO run

Capture un prompt et une réponse dans un contexte précis : moteur, modèle, marché, langue, session, navigation, personnalisation, date, réponse brute, citations, marques, tonalité, exactitude et évaluateur.

### Event

Entrée append-only décrivant une transition ou une action du système.

## 3. Identifiants

Utiliser des préfixes stables :

- `ev_` preuve ;
- `fact_` fait ;
- `finding_` constat ;
- `action_` action ;
- `geo_` run génératif ;
- `run_` mission ;
- `event_` événement.

Ne jamais réutiliser un identifiant supprimé. Pour une mise à jour, créer une nouvelle version et conserver `supersedes_id`.

## 4. Statuts de données

Les statuts ne sont pas interchangeables entre objets. Utiliser uniquement les valeurs autorisées par le schéma de l’objet concerné.

### Evidence et mesures

| Statut | Usage |
|---|---|
| `observed` | Observation directe ou donnée de première partie capturée |
| `proxy` | Mesure indirecte qui ne prouve pas le phénomène cible |
| `client_reported` | Information déclarée par le client, non encore vérifiée |
| `inferred` | Déduction raisonnable, jamais présentée comme un fait |
| `not_measured` | Absence volontaire ou contrainte de mesure |
| `unknown` | Information nécessaire mais inconnue |

### Facts

| Statut | Usage |
|---|---|
| `client_approved` | Fait explicitement approuvé, avec approbateur et date |
| `observed` | Fait dérivé d’une observation ou donnée de première partie traçable |
| `inferred` | Proposition déduite qui ne doit pas être présentée comme vérifiée |
| `conflicted` | Valeurs ou sources incompatibles non résolues |
| `expired` | Fait auparavant valide mais arrivé à expiration |
| `unknown` | Information nécessaire non établie |

Une déclaration client commence comme `evidence.status=client_reported`. Elle ne devient `fact.status=client_approved` qu’après approbation humaine explicite ; sinon elle reste une preuve déclarative ou une question ouverte.

## 5. Niveaux de confiance

| Niveau | Coefficient indicatif | Exemples |
|---|---:|---|
| `confirmed` | 1,00 | Donnée brute reproductible ou fait vérifié directement |
| `strong` | 0,85 | API officielle, observation directe ou sources indépendantes cohérentes |
| `moderate` | 0,65 | Outil tiers, information client partiellement étayée ou mesure incomplète |
| `weak` | 0,40 | Inférence, snippet ou information non vérifiée |

Le coefficient sert au calcul de qualité de mesure, pas à rendre une preuve faible « vraie ». Un constat critique `moderate` ou `weak` reste en validation.

## 6. Règles de conflit

1. Conserver les deux valeurs et leur provenance.
2. Comparer période, définition, périmètre, marché et unité avant de conclure à un conflit.
3. Préférer la source première partie correspondant au périmètre.
4. Ne jamais écraser silencieusement une valeur antérieure.
5. Créer un finding de conflit si la différence modifie une décision.
6. Marquer `unresolved` et demander une validation ciblée si aucune source ne domine.
