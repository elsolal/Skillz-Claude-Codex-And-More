---
title: SEO/GEO Audit Workflow
status: approved
approved_by: human
approved_at: 2026-06-09T19:45:00Z
slug: seo-geo-audit-workflow
related_pr: TBD
---

# SEO/GEO Audit Workflow

## Why

Skillz-Claude n'avait pas de workflow dédié pour auditer la visibilité organique d'un site ou d'une marque.

Les besoins couverts par le nouveau workflow:

- SEO technique: indexabilité, robots, sitemap, canonical, schema, performance.
- On-page: title, meta, H1, structure Hn, CTA, preuves, FAQ.
- Intentions de recherche: mots-clés, SERP dominante, cannibalisation, pages cibles.
- GEO: contenus citables par IA, `llms.txt`, prompts conversationnels, sources citées.
- Autorité: avis, Google Business Profile, NAP, mentions, réseaux sociaux, Reddit/forums.
- Roadmap exécutable: 7 jours, 30 jours, 90 jours.

## Source locale

Le design s'appuie sur `/Users/aymeric/Documents/PROJETS/DEV/SEO_Squad`, en particulier:

- `00_REGLES_COMMUNES.md` pour les garde-fous anti-hallucination.
- `01_MASTER_ORCHESTRATOR.md` pour la séquence d'audit.
- `templates/Grille_Notation_GEO.md` pour la notation de visibilité IA.
- `Outils_Verification_Externes.md` pour les checks déterministes.

Decision d'intégration:

- Copier le pack complet SEO_Squad dans `.claude/skills/seo-geo-audit/references/seo-squad/`.
- Garder `SKILL.md` comme entrée portable et utiliser les prompts complets comme sources autoritaires.
- Ajouter `/seo-geo-squad` pour forcer l'orchestration complète 11 agents.
- Garder `/seo-geo-audit` pour les audits compacts, ciblés ou ship-gate.
- Garder le statut de preuve `Confirmé / Déduit / Non vérifié`.
- Garder la double-vérification obligatoire des affirmations négatives.
- Garder les livrables actionnables, mais adapter au format Skillz-Claude.

## Scope

### Added

- Nouveau skill `.claude/skills/seo-geo-audit/SKILL.md`.
- Référence `.claude/skills/seo-geo-audit/references/seo-squad-framework.md`.
- Pack complet `.claude/skills/seo-geo-audit/references/seo-squad/` avec règles communes, master orchestrator, 11 prompts agents et templates.
- Nouvelle commande `.claude/commands/seo-geo-audit.md`.
- Nouvelle commande `.claude/commands/seo-geo-squad.md`.
- Prompts portables Codex, Gemini et OpenCode.
- Metadata OpenAI `agents/openai.yaml`.

### Updated

- `.claude/CLAUDE.md` route les demandes SEO/GEO vers `/seo-geo-audit` ou `/seo-geo-squad` selon la profondeur.
- README et docs provider listent la commande portable.
- `install.sh` installe, affiche et désinstalle la commande.
- `docs/WORKFLOW.md` documente la phase SEO/GEO.
- `CHANGELOG.md` trace la release `v5.14.0`.

## Audit axes

| Axis | What it protects |
|---|---|
| Stratégie | offre, cible, promesse, différenciation |
| Homepage/on-page | title, meta, H1, CTA, preuves, structure |
| Technique | indexation, robots, sitemap, canonical, schema, performance |
| Keywords/intent | requêtes business, locales, comparatives, FAQ |
| Concurrents | formats SERP, angles couverts, opportunités |
| Content SEO/GEO | pages, guides, FAQ, contenus citables IA |
| Autorité/local | avis, GBP, NAP, mentions, sociaux, forums |
| Visibilité IA | prompts, sources citées, concurrents cités, llms.txt |
| Cohérence | contradictions, négatifs non prouvés, scores incohérents |

## Workflow contract

```text
Input URL / domaine
  -> configuration sources + type business
  -> collecte factuelle
  -> statut Confirmé / Déduit / Non vérifié
  -> double-check des absences
  -> audit 9 axes ou orchestration complète 11 agents
  -> score SEO/GEO + score IA si possible
  -> roadmap 7j / 30j / 90j
  -> tickets /dev ou vérifications manuelles
```

## Squad contract

`/seo-geo-squad` charge obligatoirement:

1. `README.md`
2. `00_REGLES_COMMUNES.md`
3. `01_MASTER_ORCHESTRATOR.md`
4. `Outils_Verification_Externes.md`
5. les 11 prompts sous `agents/`
6. les templates sous `templates/`

Les livrables attendus sont le Brief Site, les fichiers agents intermédiaires, le rapport fusionné final, puis `Audit_<NomClient>_Note_Strategique` et `Plan_Implementation_<NomClient>` en PDF si possible, sinon Markdown/HTML.

## Non-goals

- Faire du ranking tracking quotidien.
- Remplacer Ahrefs, Semrush, GSC ou outils de monitoring IA.
- Promettre une position Google ou une citation IA.
- Générer automatiquement du contenu publié sans contrôle humain.
- Lancer un scraping massif ou des actions non conformes aux CGU.

## Validation

- `git diff --check`
- `bash -n install.sh`
- YAML parse des nouveaux fichiers skill/metadata
- TOML sanity check des commandes Gemini
- scan trailing whitespace des nouveaux fichiers `seo-geo-audit`

## Follow-ups

- Ajouter un exemple de rapport réel après le premier audit client.
- Ajouter un script optionnel pour vérifier automatiquement `robots.txt`, `sitemap.xml`, `llms.txt` et status HTTP.
- Ajouter une fixture installateur pour `/seo-geo-audit` et `/seo-geo-squad` sur Codex, Gemini et OpenCode.
