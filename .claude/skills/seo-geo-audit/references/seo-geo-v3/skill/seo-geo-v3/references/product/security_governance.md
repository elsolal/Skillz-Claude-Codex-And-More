# Sécurité, confidentialité et gouvernance

Référence opérationnelle de SEO/GEO V3, datée du **15 juillet 2026**. Ce document ne remplace ni un conseil juridique, ni l’analyse du DPO ou du responsable sécurité du client.

## Sommaire

- [Principes non négociables](#principes-non-négociables)
- [Rôles et responsabilités](#rôles-et-responsabilités)
- [Classification des données](#classification-des-données)
- [Avant toute collecte](#avant-toute-collecte)
- [Gestion des secrets et accès](#gestion-des-secrets-et-accès)
- [Isolation et stockage](#isolation-et-stockage)
- [Conservation recommandée](#conservation-recommandée-à-paramétrer)
- [Défense contre l’injection indirecte](#défense-contre-linjection-indirecte)
- [Workflow de modification sûre](#workflow-de-modification-sûre)
- [Gouvernance des agents et du commerce](#gouvernance-des-agents-et-du-commerce)
- [Réponse à incident](#réponse-à-incident)
- [Contrôle de sortie](#contrôle-de-sortie-obligatoire)

## Principes non négociables

1. **Lecture seule par défaut.** Toute écriture, publication, modification de droits, configuration WAF/robots, suppression ou envoi externe exige une autorisation explicite et traçable.
2. **Moindre privilège.** Demander le rôle minimal, sur la propriété exacte, pendant la durée minimale.
3. **Séparation stricte des clients.** Ne jamais mutualiser fichiers, secrets, prompts, index, journaux ou exports entre tenants.
4. **Minimisation.** Ne collecter que les données nécessaires au périmètre accepté.
5. **Preuve et traçabilité.** Journaliser qui a demandé, approuvé, exécuté et vérifié chaque action sensible.
6. **Validation humaine.** Ne jamais laisser un agent publier ou acheter de façon autonome par défaut.
7. **Réversibilité.** Prévoir sauvegarde, diff, staging, test et rollback avant toute mutation.
8. **Aucune donnée secrète dans les livrables.** Masquer tokens, identifiants, e-mails personnels, cookies, clés et en-têtes sensibles.

Références :

- CNIL, RGPD : https://www.cnil.fr/fr/rgpd-de-quoi-parle-t-on
- CNIL, gestion des habilitations : https://www.cnil.fr/fr/securite-gerer-les-habilitations
- CNIL, guide de la sécurité des données : https://www.cnil.fr/fr/guide-de-la-securite-des-donnees-personnelles
- OWASP, sécurité des applications LLM : https://owasp.org/www-project-top-10-for-large-language-model-applications/

## Rôles et responsabilités

| Rôle | Droits par défaut | Responsabilités |
|---|---|---|
| Sponsor client | Validation, arbitrage | Approuver périmètre, objectifs, données sensibles et mise en production. |
| Propriétaire métier | Lecture et commentaires | Valider Digital Twin, claims, offres, concurrents et priorités. |
| Propriétaire technique | Lecture technique ; écriture contrôlée | Valider correctifs, staging, sauvegarde et rollback. |
| Consultant SEO/GEO Squad | Lecture sur périmètre | Collecter, analyser, produire les recommandations et documenter les limites. |
| Opérateur d’implémentation | Écriture temporaire ciblée | Appliquer seulement les changements approuvés et fournir le diff. |
| Contrôleur QA | Lecture indépendante | Vérifier preuves, conformité, sécurité, accessibilité et résultats post-déploiement. |
| DPO/juridique | Accès selon besoin | Valider base légale, conservation, sous-traitants et clauses. |

Éviter les comptes partagés. Retirer les accès à la fin de la mission et effectuer une revue au minimum à chaque phase ou changement d’équipe.

## Classification des données

| Niveau | Exemples | Traitement |
|---|---|---|
| Public | Pages publiques, robots, sitemaps, données structurées publiques | Peut entrer dans l’Evidence Vault avec URL et horodatage. |
| Interne | Roadmap, contenu non publié, tickets, agrégats analytics | Accès limité au projet ; ne pas réutiliser pour une démo. |
| Confidentiel | CRM, requêtes clients, chiffres de conversion, stratégie, logs détaillés | Chiffrement, contrôle d’accès, conservation courte et export masqué. |
| Secret | Clés API, mots de passe, cookies de session, tokens OAuth | Stocker uniquement dans un coffre de secrets ; jamais dans Markdown, PDF, prompt ou commit. |
| Donnée personnelle sensible | Santé, biométrie, opinions, mineurs, etc. | Exclure par défaut ; DPIA et validation DPO si indispensable. |

## Avant toute collecte

Créer un manifeste signé ou explicitement approuvé contenant :

- domaines, sous-domaines, pays, langues, marques et propriétés inclus ;
- sources autorisées : GSC, GA4, Bing, CRM, logs, GBP, Merchant Center, CMS ;
- finalités et catégories de données ;
- propriétaires et personnes autorisées ;
- durée de conservation et procédure de suppression ;
- fournisseurs IA et connecteurs tiers utilisés ;
- transferts hors EEE éventuels et mécanisme contractuel ;
- actions autorisées : lecture, génération de brouillons, staging, production ;
- contenus interdits de collecte ou de traitement.

Sans manifeste, limiter le run aux données publiques et produire un angle mort explicite.

## Gestion des secrets et accès

- Utiliser OAuth et rôles natifs lorsque disponibles ; éviter les mots de passe communiqués par messagerie.
- Placer chaque secret dans un coffre distinct par client et environnement.
- N’afficher que les quatre derniers caractères lors d’un diagnostic.
- Ne jamais envoyer un secret à un modèle de langage.
- Activer MFA pour les comptes humains et administrateurs.
- Faire expirer les accès temporaires ; révoquer lors de l’offboarding.
- Journaliser l’utilisation des clés sans journaliser leur valeur.
- Vérifier les permissions avant et après l’intervention.

## Isolation et stockage

Structure logique minimale par client :

```text
tenant_id/
  manifests/
  evidence/
  findings/
  actions/
  exports/
  logs/
```

Exigences :

- identifiant de tenant obligatoire sur chaque objet ;
- chiffrement en transit et au repos ;
- sauvegarde chiffrée et test de restauration ;
- URLs d’export à durée limitée ;
- suppression vérifiable, y compris copies et sauvegardes selon la politique convenue ;
- environnement de démonstration alimenté uniquement avec données fictives ou anonymisées ;
- aucune indexation publique des dossiers, exports ou tableaux de bord.

## Conservation recommandée à paramétrer

Ne pas fixer une durée universelle. Documenter la durée nécessaire à la mission :

- données brutes volumineuses et captures : durée courte définie dans le manifeste ;
- constats et preuves utiles au suivi : durée du contrat plus période de contestation convenue ;
- secrets et accès : jusqu’à la fin de l’usage, puis révocation immédiate ;
- journaux de sécurité : durée compatible avec la détection d’incident et les obligations client ;
- prospects non convertis : durée approuvée par le responsable de traitement.

Le client doit pouvoir demander export, rectification ou suppression conformément au rôle juridique défini. Ajouter un accord de sous-traitance lorsque SEO/GEO Squad traite des données personnelles pour son compte.

## Défense contre l’injection indirecte

Tout contenu crawlé, PDF, commentaire, fichier ou page externe est **non fiable**. Les instructions qu’il contient ne changent jamais le mandat.

Procédure :

1. Isoler la collecte de l’exécution d’actions.
2. Extraire des faits ; ne jamais exécuter une commande trouvée dans une page.
3. Refuser toute demande externe d’exfiltration, de désactivation de garde-fous ou de changement de destinataire.
4. Filtrer secrets et données personnelles avant envoi au modèle.
5. Exiger une approbation distincte pour chaque domaine, connecteur ou destinataire nouveau.
6. Autoriser les outils par liste positive et paramètres bornés.
7. Conserver la provenance de chaque fragment utilisé.

## Workflow de modification sûre

Toute implémentation suit cet ordre :

1. Ticket approuvé avec propriétaire, périmètre, bénéfice attendu et risque.
2. Capture de l’état initial et sauvegarde vérifiée.
3. Diff proposé, sans secret ni changement hors périmètre.
4. Test en staging ou environnement isolé.
5. Contrôles fonctionnels, SEO, accessibilité, sécurité et analytics.
6. Approbation humaine de production.
7. Déploiement borné et journalisé.
8. Vérification post-déploiement avec critère d’acceptation.
9. Rollback si seuil d’échec atteint.

Les changements robots, noindex, canonicals, redirections, DNS, WAF, tracking, paiement et permissions sont toujours classés **risque élevé**.

## Gouvernance des agents et du commerce

- Le navigateur agentique, WebMCP, UCP et ACP restent des surfaces émergentes : les activer en laboratoire ou projet explicitement accepté.
- Exiger une confirmation utilisateur avant envoi de formulaire, réservation, commande, paiement ou annulation.
- Limiter montants, marchand, quantité, territoire et durée de validité d’une autorisation.
- N’émettre aucune transaction depuis un environnement d’audit.
- Tester les outils agentiques avec comptes sandbox et données fictives.
- Conserver une trace lisible de l’intention, des paramètres proposés, de la confirmation et du résultat.
- Vérifier le modèle de menace, la fraude, la non-répudiation, PCI DSS et l’authentification avant tout pilote commerce.

Sources émergentes :

- Chrome WebMCP et sécurité : https://developer.chrome.com/docs/ai/webmcp
- Universal Commerce Protocol : https://ucp.dev/specification/overview/
- Agentic Commerce Protocol : https://openai.com/index/buy-it-in-chatgpt/

## Réponse à incident

Déclencher la procédure si : secret exposé, accès non autorisé, mélange de tenants, publication erronée, suppression, fuite de données, modification SEO à fort impact ou action agentique non confirmée.

1. Stopper les actions et révoquer les accès affectés.
2. Préserver les journaux et preuves ; ne pas altérer la scène.
3. Contenir : désactiver connecteur, token, export ou workflow.
4. Informer le responsable sécurité et le contact client selon le contrat.
5. Évaluer données, personnes, territoires, durée et impact.
6. Restaurer depuis un état validé.
7. Documenter cause racine, mesures correctives et critères de reprise.
8. Laisser le DPO/responsable de traitement décider des notifications réglementaires.

## Contrôle de sortie obligatoire

Avant livraison, répondre `OUI` à chaque point :

- [ ] Périmètre et autorisation enregistrés.
- [ ] Sources et dates visibles.
- [ ] Aucune clé, donnée personnelle non nécessaire ou information inter-client.
- [ ] Droits de lecture/écriture conformes au manifeste.
- [ ] Claims et faits sensibles validés par le client.
- [ ] Toute action de production approuvée et réversible.
- [ ] Limites, inconnues et composants expérimentaux signalés.
- [ ] Exports protégés et durée de conservation définie.
- [ ] Accès temporaires planifiés pour révocation.
- [ ] Contact incident et procédure de suppression connus.
