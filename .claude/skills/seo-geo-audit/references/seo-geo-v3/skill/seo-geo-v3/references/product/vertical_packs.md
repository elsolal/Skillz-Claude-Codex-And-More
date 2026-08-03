# Packs verticaux V3

Activer un pack vertical après le socle commun, jamais à la place de celui-ci. N’activer que les modules correspondant au modèle économique, aux surfaces de recherche et aux données réellement disponibles.

## Sommaire

- [Socle commun obligatoire](#socle-commun-obligatoire)
- [Sélecteur](#sélecteur)
- [Local et multi-sites](#pack-local--multi-sites)
- [SaaS et B2B](#pack-saas--b2b)
- [E-commerce et commerce agentique](#pack-e-commerce--commerce-agentique)
- [Média, éditeur et YMYL](#pack-média-éditeur--ymyl)
- [Marque personnelle et services experts](#pack-marque-personnelle--services-experts)
- [International et multilingue](#pack-international--multilingue)
- [QA d’un pack](#qa-dun-pack-vertical)

## Socle commun obligatoire

Chaque mission conserve :

- Digital Twin validé : entité, offres, claims, preuves, audiences et concurrents ;
- Evidence Vault avec source, date, méthode et confiance ;
- audit technique et crawl sur périmètre explicite ;
- cartographie demande → pages → sources → conversions ;
- GEO Observatory reproductible ;
- backlog priorisé avec propriétaire, effort, dépendances et validation ;
- politique de sécurité, accès en lecture seule et approbation humaine.

## Sélecteur

| Pack | Activer si | Ne pas activer automatiquement si |
|---|---|---|
| Local & multi-sites | L’achat dépend d’une zone, d’un établissement ou d’un rayon de service. | Activité purement nationale sans point de présence pertinent. |
| SaaS & B2B | Cycle d’achat long, démonstration, essai, documentation produit ou plusieurs décideurs. | Transaction simple sans contenu décisionnel. |
| E-commerce | Catalogue, disponibilité, prix, livraison ou transaction en ligne. | Site vitrine sans catalogue exploitable. |
| Média, éditeur & YMYL | Publication régulière ou contenu à fort impact santé/finance/droit/sécurité. | Site à faible production éditoriale et sans risque YMYL. |
| Marque personnelle & services experts | La confiance repose sur une personne, des preuves et une expertise déclarée. | Marque indépendante de tout expert identifiable. |
| International & multilingue | Plusieurs langues, pays, devises, entités ou offres localisées. | Simple traduction ponctuelle sans marché ciblé. |

## Pack Local & multi-sites

### Données et connecteurs

- Google Business Profile et catégories ;
- pages établissement, zones de service et coordonnées ;
- avis, réponses, annuaires majeurs et sources sectorielles ;
- Search Console, GA4, appels, formulaires et CRM par établissement ;
- horaires, services, accessibilité, réservation et attributs locaux.

### Contrôles spécifiques

- cohérence nom/adresse/téléphone et URL canonique de chaque établissement ;
- pages locales réellement distinctes, sans duplication industrielle ;
- fermeture, déménagement, fusion et redirection d’anciens établissements ;
- correspondance entre zones couvertes, claims et pages ;
- données structurées `LocalBusiness` adaptées au type réel ;
- présence dans listes, comparatifs et sources locales citées par les moteurs ;
- exactitude narrative : horaires, adresse, tarifs, disponibilité et zone.

### Livrables

- matrice établissement × surface × exactitude ;
- backlog par localisation ;
- playbook avis et réponses conforme aux politiques des plateformes ;
- liste de sources locales prioritaires ;
- modèle de page locale fondé sur les besoins réels, sans contenu cloné.

### KPI

Impressions locales, actions GBP, appels/formulaires qualifiés, pages citées, exactitude des réponses IA, part de voix locale et conversion par établissement.

## Pack SaaS & B2B

### Données et connecteurs

- CRM, analytics produit, démos, essais, support, documentation et recherche interne ;
- GSC/GA4, pipeline et revenus par étape ;
- retours sales, objections, appels et tickets ;
- intégrations, comparatifs, pages solutions et changelog.

### Contrôles spécifiques

- couverture des jobs-to-be-done, rôles acheteurs et stades du funnel ;
- cohérence entre marketing, documentation et produit réel ;
- preuves : cas client, benchmarks, sécurité, conformité et intégrations ;
- alternatives et comparatifs factuels, datés et vérifiables ;
- contenu de support indexable lorsque pertinent, sans exposer d’informations privées ;
- narration des IA sur prix, fonctionnalités, limites et catégorie produit.

### Livrables

- carte problème → persona → preuve → page → CTA ;
- registre d’objections et de claims autorisés ;
- content gap basé sur CRM/support, pas seulement sur mots-clés ;
- plan documentation et pages d’intégration ;
- citations sources/analystes et programme d’autorité sectorielle.

### KPI

Démos/essais qualifiés, pipeline influencé, conversion visite → lead, citations sur prompts non brandés, exactitude produit, taux de couverture des objections et délai de mise à jour.

## Pack E-commerce & commerce agentique

### Données et connecteurs

- Merchant Center, flux produits, CMS/PIM, stock, prix, promotions, livraison et retours ;
- Search Console, GA4, CRM/commande et support ;
- données structurées Product/Merchant listings ;
- journaux de crawl des catalogues et endpoints transactionnels.

### Contrôles spécifiques

- cohérence page ↔ flux ↔ données structurées ↔ checkout ;
- disponibilité, variantes, GTIN/identifiants, prix, devise, livraison et retours ;
- facettes, pagination, canonicals et produits indisponibles ;
- avis et notation sans auto-évaluation trompeuse ;
- images produit, données fabricant, guide d’achat et comparatifs ;
- sécurité des paiements, consentement et capacité de rollback.

### Laboratoire agentique

Classer **EXPÉRIMENTAL** :

- WebMCP, proposé et en origin trial au 15 juillet 2026 ;
- Universal Commerce Protocol (UCP) ;
- Agentic Commerce Protocol (ACP) et Instant Checkout selon disponibilité pays/marchand ;
- tests de recherche, panier, checkout, réservation et confirmation par agent.

Ne pas vendre une compatibilité universelle. Commencer par HTML sémantique, libellés ARIA, formulaires robustes, catalogue exact et confirmation humaine. Tester en sandbox, sans paiement réel.

Sources :

- Google, e-commerce et données structurées : https://developers.google.com/search/docs/specialty/ecommerce/include-structured-data-relevant-to-ecommerce
- Chrome WebMCP : https://developer.chrome.com/docs/ai/webmcp
- UCP : https://ucp.dev/specification/overview/
- ACP : https://openai.com/index/buy-it-in-chatgpt/

### KPI

Produits cités, pages produit citées, exactitude prix/stock, clics assistés, ajout panier, commandes, revenu attribué/assisté, erreurs de catalogue et taux de réussite des scénarios sandbox.

## Pack Média, éditeur & YMYL

### Données et connecteurs

- CMS, flux éditorial, auteurs, corrections, archives et analytics ;
- Search Console, Discover si disponible, newsletters et abonnements ;
- sources primaires, politique éditoriale et historique de mise à jour.

### Contrôles spécifiques

- auteur, expertise, sources, date de publication et date de mise à jour ;
- différenciation entre actualité, analyse, opinion, publicité et contenu sponsorisé ;
- correction publique et retrait des informations obsolètes ;
- contenu original, enquêtes, données et témoignages de première main ;
- protection des paywalls et conformité des données structurées ;
- revue experte renforcée en santé, finance, droit, sécurité et sujets civiques.

### Garde-fous YMYL

- Ne pas générer de diagnostic médical, conseil juridique ou recommandation financière personnalisée.
- Exiger auteur/relecteur qualifié, sources primaires et date de validité.
- Séparer information, hypothèse, opinion et publicité.
- Signaler les limites et orienter vers un professionnel lorsque nécessaire.
- Refuser statistiques, citations ou références impossibles à vérifier.

### KPI

Part de contenu original, fraîcheur, corrections, citations vers articles, abonnements/retours directs, couverture de sujets et exactitude narrative.

## Pack Marque personnelle & services experts

### Données et connecteurs

- biographie approuvée, diplômes, rôles, publications, interventions, avis et cas clients ;
- profils officiels, répertoires professionnels et réseaux pertinents ;
- CRM, prises de rendez-vous, appels et newsletter.

### Contrôles spécifiques

- unicité de l’entité et homonymes ;
- cohérence du nom, titre, société, zones et spécialités ;
- preuves de qualifications sans surclaim ;
- pages auteur et liens vers profils officiels ;
- témoignages avec consentement et contexte ;
- conformité déontologique selon profession réglementée.

### Livrables

- fiche Digital Twin personnelle validée ;
- matrice d’entité et sources de référence ;
- plan thought leadership fondé sur expérience réelle ;
- monitoring des erreurs de biographie, attribution et réputation.

### KPI

Exactitude de l’identité, mentions qualifiées, citations d’articles, demandes de rendez-vous, taux de conversion et erreurs/homonymies résolues.

## Pack International & multilingue

### Données et connecteurs

- marchés, langues, devises, entités juridiques et offres ;
- GSC/GA4/CRM segmentés par pays et langue ;
- inventaire hreflang, canonicals, domaines/sous-domaines/répertoires ;
- sources locales, moteurs et assistants réellement utilisés sur chaque marché.

### Contrôles spécifiques

- contenu localisé par un locuteur compétent, pas simple traduction mot à mot ;
- intent, terminologie, preuves, prix, droit et CTA propres au marché ;
- hreflang réciproque, `x-default`, canonicals cohérents et codes valides ;
- absence de redirections forcées empêchant crawl ou utilisateurs ;
- entités, coordonnées, stocks et politiques propres au pays ;
- prompts et tests exécutés dans la langue, locale et contexte appropriés.

### Livrables

- matrice marché × langue × offre × URL ;
- architecture internationale et migration ;
- panel de prompts natifs par marché ;
- source map et concurrents locaux ;
- règles de gouvernance des traductions et mises à jour.

### KPI

Couverture hreflang, indexation par marché, part de voix locale, exactitude, conversions, coût de localisation et délai de synchronisation.

## QA d’un pack vertical

- [ ] Le pack est justifié par le modèle économique.
- [ ] Ses sources de données sont autorisées et disponibles.
- [ ] Le socle commun n’a pas été contourné.
- [ ] Les règles sectorielles sont à jour et attribuées.
- [ ] Les KPI relient visibilité, comportement et résultat métier.
- [ ] Les éléments expérimentaux sont explicitement marqués.
- [ ] Aucun quota de pages, projets ou snippets ne force du remplissage.
- [ ] Les livrables indiquent ce qui n’a pas pu être mesuré.
