# Installation du kit SEO/GEO V3 - Édition client

## Ce dont tu as besoin

Claude Code ou Codex installé. Pour installer Claude Code, rends-toi sur le site officiel : https://claude.com/claude-code

Claude Code fonctionne avec un compte Claude payant (par exemple l’offre Pro), pas avec le compte gratuit. Prévois cet abonnement avant de commencer.

## Installer et démarrer en 3 étapes

1. Dézippe le kit à l’endroit où tu veux le ranger, par exemple dans Documents.
2. Ouvre Claude Code (ou Codex), puis choisis le dossier du kit que tu viens de dézipper comme dossier de travail : dans l’application de bureau, tu le sélectionnes au démarrage ou via l’option d’ouverture de dossier. Si tu bloques à cette étape, la page officielle https://claude.com/claude-code explique comment ouvrir un dossier.
3. Colle la phrase de démarrage, en remplaçant tonsite.fr par l’adresse exacte de ton site (avec le www s’il en a un) :

```text
Lis START_HERE.md, vérifie l’intégrité du kit, puis lance un audit de tonsite.fr
```

L’agent vérifie que le kit est complet et intact, puis démarre la mission. Si un contrôle échoue ou qu’un outil manque sur ton ordinateur, Claude Code (ou Codex) te proposera de l’installer pour toi, tu n’as qu’à accepter.

## Ce que l’agent fait pour toi

- Il vérifie l’intégrité du kit : tu travailles toujours avec un kit complet et non modifié.
- Il crée un dossier de projet par client et y range preuves, analyses, plan d’action et rapports.
- Il te demande une confirmation avant d’installer quoi que ce soit ou de toucher à quoi que ce soit d’important.
- Il génère les rapports, y compris les PDF. Si un outil manque pour le PDF, il te propose de l’installer, tu n’as qu’à accepter.

## Installer le Squad en permanence (optionnel)

Si tu veux que l’escouade reste disponible dans tes outils sans dépendre de l’endroit où tu as dézippé le kit, demande simplement à l’agent : « Installe le Squad comme Skill permanent ». Il s’occupe de tout, te demande confirmation et t’indique l’emplacement choisi.

## Bonnes pratiques

- Range tes dossiers clients en dehors du dossier du kit : ils ne risquent rien lors des mises à jour.
- Avant une mise à jour du kit, demande à l’agent de sauvegarder l’ancienne installation.
- Pour retirer le kit, supprime simplement son dossier après avoir vérifié qu’aucun projet client n’y est rangé.

## Un problème ?

| Ce que tu observes | Ce qu’il faut faire |
|---|---|
| L’agent signale que le kit est incomplet ou modifié | Repars du fichier zip d’origine et dézippe-le à nouveau |
| L’agent indique qu’un outil manque | Accepte sa proposition : il l’installe pour toi et reprend |
| Un rapport PDF ne se génère pas | Demande à l’agent d’installer ce qu’il faut pour le PDF, puis relance |
| Un projet est signalé invalide | Demande à l’agent de le vérifier et de corriger ce qu’il indique |

Dans tous les cas, décris simplement le problème à l’agent : le dépannage fait partie de son travail.

## Pour l’agent

Cette section s’adresse à l’agent (Claude Code ou Codex). L’acheteur n’a pas besoin de la lire.

### Environnement requis

- Python 3.10 ou plus récent pour les scripts du kit.
- Pour les PDF balisés : Node.js, les dépendances du fichier `package-lock.json` du Skill et un navigateur Chromium compatible.
- Pour le moteur PDF de secours : les dépendances de `requirements-pdf.txt` du Skill.

Si un de ces outils manque, en proposer l’installation à l’utilisateur en langage simple, attendre son accord explicite, puis procéder.

### Vérifier avant installation

Depuis la racine du kit :

```bash
python3 install.py --check
python3 tools/build_manifest.py --verify
```

Les deux commandes doivent réussir. Le mode `--check` ne crée aucun dossier de destination.

### Installer le Skill

```bash
python3 install.py --destination /chemin/vers/le/dossier/skills
```

Le dossier créé contient toute l’escouade et se nomme :

```text
/chemin/vers/le/dossier/skills/seo-geo-squad-v3
```

Si ce dossier existe déjà, l’installateur refuse de l’écraser. Utiliser `--replace` uniquement après vérification : l’ancienne version est alors renommée en sauvegarde horodatée.

### Dépendances PDF optionnelles

Depuis le dossier du Squad installé, entrer dans le moteur méthodologique :

```bash
cd skill/seo-geo-v3
npm ci
python3 -m pip install -r requirements-pdf.txt
```

Le livrable client est composé en HTML par l'Agent 11, puis imprimé avec le moteur officiel :

```bash
node tools/render_html_pdf.cjs rapport.html rapport.pdf
```

Ce moteur imprime le HTML tel quel, en A4 balisé, et refuse tout document non conforme à `templates/Charte_PDF_SEO_GEO_V3.md`.

`tools/render_tagged_pdf.cjs` et `tools/render_markdown_pdf.py` sont des **outils de contrôle interne** : ils convertissent du Markdown avec leur propre mise en page, ne suivent pas la charte et ne produisent pas de livrable client. Les deux l'annoncent à chaque exécution.

### Premier test

```bash
python3 skill/seo-geo-v3/scripts/create_project.py /chemin/autorise/client-test \
  --client-name "Client test" --domain "https://example.com"

python3 skill/seo-geo-v3/scripts/validate_project.py /chemin/autorise/client-test
```

Le projet doit être créé avec un manifeste, des fichiers structurés, un journal d’événements et un dossier de rapports.

### Mise à jour et retrait

- Conserver les projets clients en dehors du dossier du Skill.
- Vérifier la version et la date des règles avant toute mise à jour.
- Sauvegarder l’ancienne installation avant remplacement.
- Pour retirer le Skill, supprimer uniquement son dossier d’installation après avoir confirmé qu’aucun projet client n’y est stocké.

### Dépannage technique

| Symptôme | Vérification |
|---|---|
| Préflight refusé | Lire les différences signalées par le manifeste et repartir d’une archive intacte |
| Python trop ancien | Utiliser Python 3.10 ou plus récent, en proposer l’installation à l’utilisateur si nécessaire |
| PDF balisé impossible | Installer les dépendances Node avec l’accord de l’utilisateur et vérifier Chromium |
| Projet invalide | Lancer `validate_project.py --json` et corriger les références indiquées |
| Score obsolète | Recalculer avec la même date `as_of` que les rapports et la QA |
