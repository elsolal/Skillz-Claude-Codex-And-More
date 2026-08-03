# 01 — Intake et Digital Twin

## Objectif

Créer un périmètre auditable et une source de vérité client avant toute analyse. Ne jamais transformer une déclaration commerciale en fait vérifié sans preuve.

## Entrées minimales

- Identité du commanditaire, domaine principal, marchés, langues et fuseau horaire.
- Autorisation d'analyser les actifs indiqués et niveau d'accès accordé.
- Objectifs métier, offres prioritaires, conversions, contraintes, échéances et responsables.
- Documents de marque, offres, prix, implantations, équipes, preuves et mentions légales disponibles.

## Séparation obligatoire

- `evidence` : document, page ou export source, avec provenance et date.
- `fact` : assertion atomique reliée à une ou plusieurs preuves, avec un statut du schéma : `client_approved`, `observed`, `inferred`, `conflicted`, `expired` ou `unknown`.
- `finding` : écart ou opportunité déduit de faits ; ne pas en créer pendant l'intake sauf incohérence explicite.
- `action` : décision future ; ne pas en prescrire avant l'analyse.

## Procédure

1. Attribuer `client_id`, `audit_id`, `run_id`, date, version du kit et responsable. `create_project.py` ajoute un nonce à l’`audit_id` afin que deux missions du même client créées le même jour restent distinctes ; ne pas supprimer ce suffixe.
2. Définir les domaines, sous-domaines, pays, langues, appareils et périodes inclus/exclus.
3. Recueillir les objectifs par indicateur métier : leads, ventes, prises de rendez-vous, revenu, rétention ou visibilité. Marquer les objectifs non mesurables comme tels.
4. Construire le Digital Twin :
   - identité légale et marque ;
   - offres, prix, disponibilités et zones ;
   - audiences, métiers à accomplir et objections ;
   - dirigeants, experts, auteurs et établissements ;
   - concurrents métier déclarés et concurrents de visibilité à découvrir ;
   - claims autorisés, claims interdits, preuves associées et dates de validité ;
   - ton, vocabulaire, exigences réglementaires et sujets sensibles.
5. Identifier les sources de mesure : GSC, GA4, Bing Webmaster Tools, CRM, CMS, GBP, logs, outils tiers. Demander des accès en lecture seule et au moindre privilège.
6. Documenter consentement, finalité, durée de conservation, données personnelles autorisées et procédure de suppression.
7. Capturer une déclaration non vérifiée comme preuve `client_reported`. Ne la promouvoir en fait `client_approved` qu’après approbation humaine explicite ; sinon la conserver comme preuve déclarative ou question ouverte.
8. Lister les questions ouvertes, conflits, accès manquants et conséquences sur la couverture.
9. Faire valider le périmètre et le Digital Twin par un humain autorisé.

## Sorties structurées

- `client_profile` : identité, marchés, audiences, objectifs, conversions et responsables.
- `scope` : inclusions, exclusions, période, appareils, langues et limites.
- `digital_twin` : faits atomiques, statuts, preuves, validité et propriétaire.
- `access_manifest` : système, niveau, finalité, expiration et statut ; ne jamais stocker de secret.
- `open_questions` : question, impact, responsable, échéance et statut.
- `consent_record` : autorité, périmètre, date et restrictions.

## Vérifications

- Vérifier que chaque claim sensible possède une preuve et, s’il est autorisé, un fait `client_approved` avec approbateur et date. Une simple preuve `client_reported` ne vaut pas approbation.
- Vérifier que prix, zones, dirigeants, horaires et coordonnées ne se contredisent pas.
- Vérifier que les conversions et objectifs ont une définition calculable.
- Vérifier qu'aucun mot de passe, token, cookie ou donnée personnelle inutile n'est conservé.
- Faire confirmer toute extension de périmètre.

## Critères d'arrêt

- Arrêter toute collecte authentifiée sans autorisation ou finalité explicite.
- Bloquer les recommandations sensibles si l'identité, l'offre ou les obligations légales sont contestées.
- Poursuivre en mode limité si des accès non critiques manquent, en déclarant les angles morts.
- Ne jamais promettre résultat, classement, citation IA, trafic ou revenu.
