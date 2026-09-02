---
title: "D-EPCT+R v6.1 — Provider-neutral kernel"
document_id: spec.provider-neutral-kernel
version: "6.1"
status: approved
approved_by: aymeric
approved_at: 2026-09-01
created_at: 2026-09-01
slug: provider-neutral-kernel
level: 4
lifecycle: current
superseded_by: null
amended_by: []
amends: []
source_plan: docs/planning/plans/2026-07-24-d-epct-v6-1-provider-neutral-hardening-plan.md
source_release: ai-driven-dev/framework@3082c8ff7f862df814f15f6e669a2005b50d3459
---

# D-EPCT+R v6.1 — Provider-neutral kernel

## 1. Mandat

Cette spec approuve l'implementation du plan de reference
[`2026-07-24-d-epct-v6-1-provider-neutral-hardening-plan.md`](../plans/2026-07-24-d-epct-v6-1-provider-neutral-hardening-plan.md).
Le plan reste la source detaillee pour les vagues, criteres d'acceptation, risques, tests, rollback
et decoupage en PRs. En cas d'ambiguite, les decisions et invariants ci-dessous priment.

L'objectif est d'ameliorer Skillz-Claude sans remplacer D-EPCT+R : supprimer RALPH, etablir un
noyau canonique provider-neutral, compiler des distributions natives par runtime, prouver leur
decouverte et leur comportement, puis durcir l'installation et les preuves de qualite.

## 2. Decisions approuvees

1. Le noyau canonique est `core/`; `.claude/` devient progressivement une sortie provider.
2. `dist/` est committe pendant la migration afin de rendre les diffs et golden inspectables. Cette
   politique sera reexaminee apres stabilisation du pipeline de release.
3. Les cibles P0 sont Claude Code, Codex, OpenCode et les agents generiques. Kimi via OpenCodex suit
   le contrat Codex. Kimi CLI et Grok sont P1; Gemini est P2 tant que leur certification n'est pas
   etablie sur une version epinglee.
4. Un alias garantit un identifiant semantique et une intention stables. Sa syntaxe native et son
   fallback sont documentes par runtime; une slash command litterale identique n'est pas promisee.
5. La migration suit l'ordre baseline, suppression RALPH, durcissement probe/gate, contrats et
   build, vertical slice Claude/Codex/OpenCode, lifecycle, evals, puis migration du catalogue.
6. Les sorties legacy et compilees coexistent jusqu'a equivalence structurelle, decouverte native
   et smoke comportemental du vertical slice.
7. RALPH est retire sans mode de compatibilite v6.1. Seuls le changelog, le guide de migration et
   les documents historiques explicitement marques peuvent conserver une mention.
8. Les apports upstream sont reecrits localement et traces par release, SHA, licence, decision,
   destination et tests. Aucun code upstream n'est execute pendant le scan, le build ou l'install.

## 3. Invariants de securite et d'ownership

- Aucun build ne lit ou n'ecrit dans un home utilisateur.
- Toute mutation d'installation passe par la couche lifecycle apres dry-run et verification du
  manifeste d'ownership.
- Un fichier user-owned ou modifie depuis sa derniere installation n'est jamais ecrase ni supprime
  silencieusement.
- Les fichiers locaux non suivis, notamment `.codex/hooks.json`, `.codex/hooks/` et
  `.claude/settings.local.json`, sont exclus tant qu'aucune preuve d'ownership Skillz n'existe.
- Un runtime n'est declare supporte qu'au niveau C3; C1 signifie generable et C2 compatible
  structurellement.
- Une installation ou une commande retournee avec code 0 ne vaut pas preuve de decouverte native.
- Aucun runner n'utilise de contournement global de permissions.

## 4. Contrats d'architecture

- `core/catalog.yaml` porte les identifiants, sources, dependances, aliases, entrees/sorties et
  risques; il ne contient ni chemin home ni logique provider.
- Chaque `providers/<runtime>/build-contract.yaml` decrit separement `instructions`, `skills`,
  `commands`, `agents`, `mcp` et `hooks` avec une strategie pure ou un statut `unsupported` motive.
- `tooling/build/` transforme `core/` vers un repertoire temporaire, valide le resultat, puis
  remplace atomiquement `dist/<runtime>`.
- `tooling/lifecycle/` est seul autorise a appliquer un bundle dans un environnement utilisateur.
- `tooling/doctor/` observe versions, chemins, collisions, drift et certification sans mutation.
- `tooling/evals/` execute des fixtures isolees et produit des resultats structures et reproductibles.
- Le Markdown reste canonique pour les skills; aucune logique metier n'est deplacee vers un DSL.

## 5. Strategie d'execution

L'epic est implemente par tranches niveau 2 ou 3, chacune livrable, testee et munie de son propre
quality gate. Le decoupage en PRs du plan de reference fait foi. Les PRs 3 et 5 peuvent etre
preparees en parallele apres la baseline, mais aucun lot ne melange changement fonctionnel,
deplacement de source canonique et changement du compilateur.

La premiere tranche produit uniquement :

- un inventaire deterministe des surfaces versionnees actuelles et de leur ownership suppose;
- une matrice de compatibilite avec etat et version observes par runtime;
- des golden legacy lisibles et sans secret;
- la liste explicite des fichiers locaux user-owned exclus;
- une preuve que deux captures consecutives sont identiques et ne mutent pas le worktree.

## 6. Criteres d'acceptation globaux

Les criteres detailles des sections 10 a 25 du plan sont normatifs. Au minimum :

- RALPH disparait de toute surface active et installee sans toucher aux fichiers user-owned;
- `project-probe` invalide toute entree pertinente modifiee;
- `gate verify` refuse toute preuve stale, alteree ou liee a de mauvais SHAs;
- deux builds identiques produisent les memes hashes et tout statut non emis est motive;
- Claude Code, Codex et OpenCode atteignent C3 sur des versions epinglees avant l'annonce de support;
- install, update, uninstall et restore preservent le drift utilisateur;
- le build, l'installation et les tests structurels ne dependent d'aucun checkout upstream;
- le quality gate final est PASS, ou toute limitation externe est documentee et acceptee comme
  preuve absente plutot que transformee en succes.

## 7. Rollback

Chaque tranche conserve une distribution installable. Tant que le vertical slice n'est pas
certifie, les surfaces legacy restent disponibles. Le rollback reutilise un bundle versionne et
son manifeste; il ne reconstruit pas manuellement un etat et ne touche qu'aux fichiers dont
l'ownership Skillz est prouve.

## 8. Approbation

Aymeric a confirme le 1er septembre 2026 que le plan contient le cadrage necessaire et a demande de
passer directement a l'implementation sans nouvelle phase de discovery. Cette confirmation approuve
les defaults de la section 27 du plan et autorise l'execution sequentielle des tranches ci-dessus.
