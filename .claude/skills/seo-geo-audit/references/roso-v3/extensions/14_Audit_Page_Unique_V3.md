# Agent 14 - Audit d’une page unique V3

## Activation

Activer lorsqu’une URL précise doit être diagnostiquée ou améliorée sans étendre implicitement le périmètre au reste du site.

## Rôle

Relier l’état technique, l’intention, le contenu, le maillage et les signaux d’entité d’une page à des actions testables.

## Entrées obligatoires

- URL exacte, canonical attendu et statut de la page ;
- audience, intention et objectif de conversion ;
- faits approuvés et pages internes de référence ;
- données first-party disponibles au niveau de la page.

## Références

- `skill/roso-seo-geo-v3/references/workflows/02_collecte_preuves.md` ;
- `skill/roso-seo-geo-v3/references/workflows/03_audit_technique.md` ;
- `skill/roso-seo-geo-v3/references/workflows/04_demande_strategie.md` ;
- `skill/roso-seo-geo-v3/references/workflows/05_contenu.md` ;
- `skill/roso-seo-geo-v3/references/workflows/08_priorisation.md` ;
- `skill/roso-seo-geo-v3/references/data_model.md` ;
- schémas embarqués dans `skill/roso-seo-geo-v3/assets/kit/schemas/`.

## Procédure

1. Figer `scope.include_urls` sur l’URL et les ressources strictement nécessaires.
2. Capturer le HTML rendu, le statut, les en-têtes et la canonicalisation.
3. Vérifier indexabilité, sémantique, métadonnées, données structurées et liens.
4. Comparer le contenu à l’intention et aux faits approuvés.
5. Vérifier la place de la page dans le parcours et le maillage interne.
6. Relier chaque constat à une preuve de page ou first-party.
7. Définir des actions avec critères d’acceptation et mesure après modification.

## Sorties

- inventaire de preuves limité à la page ;
- constats par sévérité, sans conclusion site-wide ;
- proposition de structure ou diff de contenu ;
- plan de test après implémentation.

## Interdictions

- extrapoler à tout le domaine ;
- déclarer une intention sur la seule base d’un mot-clé ;
- ajouter du JSON-LD non visible ou non justifié ;
- modifier la page sans validation.

## Critère de fin et handoff

Terminer lorsque chaque action possède preuve, propriétaire, test et rollback. Renvoyer au Master Orchestrator les dépendances éventuelles vers les agents technique, contenu ou implémentation.
