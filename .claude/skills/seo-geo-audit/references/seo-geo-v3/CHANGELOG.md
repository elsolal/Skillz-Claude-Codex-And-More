# Ce qui change dans la version 3.1.0

**27 juillet 2026**

Cette version change une seule chose, mais c'est la plus visible : **les documents que tu remets à tes clients**.

---

## Tes rapports sont maintenant écrits, plus seulement générés

Avant, un script transformait les données de l'audit en document. Le résultat était juste, mais il se lisait comme une base de données : des listes d'identifiants, des tableaux bruts, aucune explication.

Maintenant, **c'est l'agent qui rédige le document**, en suivant une charte graphique complète. Concrètement, tes rapports contiennent :

- **un verdict en une phrase** sur la couverture, écrit en langage humain, au lieu d'un titre descriptif ;
- **un feu tricolore** en première partie : ce qui va bien, ce qui est moyen, ce qui bloque, par où commencer ;
- **des failles expliquées**, chacune avec sa preuve en français lisible — « Test direct de tonsite.fr/llms.txt : réponse 404, double-vérifié » — et non plus des codes comme `ev_a3f9` ;
- **un glossaire final** qui traduit chaque mot technique employé dans le document ;
- **un plan d'implémentation** avec des blocs de code prêts à coller et un tableau « où coller ce code » pour WordPress, Webflow, Wix et Shopify ;
- **une page « Quoi faire si tu es perdu »** à la fin du plan, pour le client qui referme le document sans savoir par où commencer.

Les identifiants techniques n'apparaissent plus dans le corps du rapport. Ils sont regroupés en annexe de fin, pour la traçabilité.

## Le mode « estimation ancrée » : plus de rapports à trous

C'est le changement le plus important pour toi au quotidien.

Jusqu'ici, si tu n'avais pas accès à ChatGPT, Perplexity ou à la Search Console de ton client, tout ce qui dépendait de ces sources tombait en « non mesuré ». Le rapport se vidait.

Désormais, le kit distingue **trois états** au lieu de deux :

| État | Ce que ça veut dire |
|---|---|
| **Mesuré** | Relevé par test direct. Valeur exacte. |
| **Estimé** | Déduit d'au moins trois sources web concordantes. Affiché en **fourchette**, jamais en chiffre unique, avec la mention « estimé ». |
| **Non mesuré** | Ni testé ni estimable. Dit en clair, avec la façon de le mesurer. |

Une garantie ne bouge pas : **une affirmation négative sur le site de ton client ne repose jamais sur une estimation**. Dire « ton llms.txt est absent » exige un test direct effectué deux fois. Une estimation ne sert jamais à prouver un manque.

## Des polices livrées avec le kit

Les rapports utilisent Inter et JetBrains Mono, **incluses dans le kit** sous licence libre. Tes PDF sortent identiques sur n'importe quelle machine, sans rien installer et sans connexion. Avant, l'apparence dépendait des polices présentes sur l'ordinateur.

## Une charte unique pour juger les rapports

La charte V3 définit directement la structure, la pédagogie, l'accessibilité et
la densité attendues. Les anciens PDF d'exemple brandés ne sont plus distribués.

## Le kit refuse maintenant de produire un document non conforme

Le moteur d'impression vérifie le document avant de l'imprimer. Il refuse de sortir un PDF dont la couverture serait illisible, qui dépendrait d'une police téléchargée sur Internet, ou dont les images n'auraient pas de description. Tu ne peux plus livrer un document cassé sans t'en apercevoir.

## Détails qui font gagner du temps

- **Les numéros de page du sommaire sont calculés automatiquement.** Ils sont désormais toujours justes.
- **Plus de quota de chantiers.** Le plan contient exactement un chantier par action réellement identifiée. Le kit n'invente plus de tâches pour remplir un document.
- **Le préflight prévient** dès le lancement si le moteur PDF n'est pas installé, avec la commande exacte à lancer.
- **Le contrôle d'intégrité ne se déclenche plus à tort.** Les dossiers créés par tes outils, comme `.claude` ou `node_modules`, ne sont plus comptés comme des fichiers étrangers.

---

## Ce que tu dois faire pour en profiter

1. Dézippe cette version dans un nouveau dossier.
2. Ouvre Claude Code ou Codex dedans.
3. Au premier lancement, accepte l'installation du moteur PDF quand l'agent te la propose.

Tes projets clients existants ne sont pas affectés : ils vivent en dehors du dossier du kit. Un audit lancé avec la 3.1.0 produira simplement des documents plus lisibles.

---

## Versions précédentes

**3.0.1** — Correction du branding sur les rapports clients, protocole de reprise en cas d'échec de mesure, résolution automatique de l'adresse du site avec ou sans `www`, proposition du type d'audit au démarrage.

**3.0.0** — Première version V3 : 21 agents, scoring sur cinq dimensions, projets clients persistants, six statuts de mesure, QA adversariale.
