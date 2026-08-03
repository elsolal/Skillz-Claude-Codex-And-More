# RosoAI SEO/GEO Squad V3

Bienvenue ! Tu viens d’acquérir une escouade de 21 agents IA spécialisés en SEO et en GEO, la visibilité dans les réponses des moteurs IA. Tu lui confies ton site, elle l’audite avec des preuves datées, puis te livre un plan d’action priorisé et des rapports professionnels prêts à envoyer. Un orchestrateur dirige l’ensemble et ne mobilise que les agents utiles à ta mission.

## Ce dont tu as besoin

Claude Code ou Codex installé. Pour installer Claude Code, rends-toi sur le site officiel : https://claude.com/claude-code

Claude Code fonctionne avec un compte Claude payant (par exemple l’offre Pro), pas avec le compte gratuit. Prévois cet abonnement avant de commencer.

## Installation en 3 étapes

1. Dézippe le kit à l’endroit où tu veux le ranger.
2. Ouvre Claude Code (ou Codex), puis choisis le dossier du kit que tu viens de dézipper comme dossier de travail : dans l’application de bureau, tu le sélectionnes au démarrage ou via l’option d’ouverture de dossier. Si tu bloques à cette étape, la page officielle https://claude.com/claude-code explique comment ouvrir un dossier.
3. Colle la phrase de démarrage ci-dessous.

C’est tout. Aucune manipulation technique ne t’est demandée : l’agent s’occupe du reste.

## Ta phrase de démarrage

Copie-colle cette phrase dans Claude Code (ou Codex), en remplaçant tonsite.fr par l’adresse de ton site. Utilise l’adresse exacte qui s’affiche dans la barre de ton navigateur, avec le www si ton site en a un :

```text
Lis START_HERE.md, vérifie l’intégrité du kit, puis lance un audit de tonsite.fr
```

L’agent vérifie que le kit est complet et intact, puis démarre la mission en te posant les bonnes questions. Si un contrôle échoue ou qu’un outil manque sur ton ordinateur, l’agent s’en occupe : Claude Code (ou Codex) te proposera de l’installer pour toi, tu n’as qu’à accepter.

## Tu viens de la v2 ? Ce qui change

- La façon de l’utiliser : la v2 se collait dans un Claude Project, la v3 s’utilise avec Claude Code ou Codex, qui exécutent le moteur du kit automatiquement.
- L’escouade passe de 11 à 21 agents : les 9 modules d’extension sont devenus de vrais agents autonomes, rejoints par un nouvel agent Connecteurs et Mesure.
- Le scoring est refondu sur 5 dimensions (Fondations, Visibilité générative, Opportunité, Exécution, Mesure), avec couverture et confiance affichées. Il remplace l’estimation ±12 de la v2.
- Chaque donnée porte désormais un statut de mesure : une donnée non mesurée reste marquée comme telle, l’IA ne peut plus inventer de chiffre.
- Les projets clients sont persistants : chaque client a son dossier, et tu peux reprendre une mission à tout moment.
- Les rapports existent en PDF professionnel, en plus du markdown.
- L’orchestrateur ne lance jamais les 21 agents d’un coup : il mobilise uniquement ceux dont ta mission a besoin.
- Les audits v2 ne migrent pas automatiquement : un site déjà audité en v2 repart sur un projet v3 propre.

## Aller plus loin

- Pour les détails d’installation, de mise à jour et de retrait : `docs/INSTALLATION.md`.
- Toute la documentation du kit (méthode, agents, références) est lue et appliquée par l’agent. Tu peux aussi l’interroger directement : demande-lui par exemple de t’expliquer la méthode, une dimension du score ou un rapport.

## Pour l’agent

Cette section s’adresse à l’agent (Claude Code ou Codex). L’acheteur n’a pas besoin de la lire.

Ordre de lecture au démarrage d’une mission :

1. `SKILL.md` ;
2. `core/00_REGLES_COMMUNES_V3.md` ;
3. `core/01_MASTER_ORCHESTRATOR_V3.md` ;
4. `core/AGENTS_MANIFEST.json` ;
5. `skill/roso-seo-geo-v3/SKILL.md` ;
6. les cartes d’agents et références routées par l’orchestrateur.

Vérifications d’intégrité à exécuter depuis la racine du kit, avant la première mission puis à chaque doute :

```bash
python3 install.py --check
python3 tools/build_manifest.py --verify
```

Ces scripts exigent Python 3.10 ou plus récent. Si l’environnement ne le fournit pas, ou si un outil nécessaire à la mission manque, en proposer l’installation à l’utilisateur en langage simple, attendre son accord, puis procéder. Si un contrôle échoue, expliquer le problème simplement et demander confirmation avant toute correction. Pour installer le Squad comme Skill permanent et pour les moteurs PDF, suivre la section « Pour l’agent » de `docs/INSTALLATION.md`.

Au démarrage d’une mission d’audit dont le type n’est pas précisé, présenter brièvement les modes disponibles (audit complet, express, page unique, delta, suivi, contenu, implémentation, international) et demander lequel l’utilisateur souhaite, en proposant l’audit complet par défaut. Avant toute collecte, résoudre l’origine canonique du site (suivre les redirections, par exemple vers `www`) et l’utiliser comme URL de référence du run.

Version du kit : 3.1.0. Référentiel de règles : 27 juillet 2026.
