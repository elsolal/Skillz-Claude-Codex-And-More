---
epic: EPIC-001
story_id: STORY-001
title: Installer le CLI memory sans collision
priority: P0
estimation: M
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
github_issue: 41
github_url: https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/41
dependencies: []
prd_requirements: [NFR-PERF-004, NFR-MNT-001]
architecture_decisions: [ADR-001, ADR-002, ADR-012]
---

# STORY-001 — Installer le CLI `memory` sans collision

## User Story

**En tant qu'** utilisateur de Skillz-Claude sur plusieurs agents,
**je veux** disposer d'une commande mémoire commune après l'installation,
**afin de** ne pas dépendre du chemin interne d'un provider ou d'un alias manuel.

## Contexte

Le runtime canonique reste `~/.claude/skills/llm-wiki/`. L'installateur doit
garantir `skillz-memory` et créer l'alias nominal `memory` seulement lorsqu'il
est libre ou déjà géré par Skillz-Claude.

## Critères d'acceptation

- [ ] **AC1** — Given Python >= 3.10 et une installation Skillz-Claude, When `install.sh install all` est exécuté, Then `skillz-memory --version` réussit depuis `PATH`.
- [ ] **AC2** — Given aucun binaire `memory` existant, When l'installation termine, Then `memory --version` résout le même runtime que `skillz-memory`.
- [ ] **AC3** — Given un binaire `memory` tiers, When l'installation est exécutée, Then ce binaire n'est pas modifié et un avertissement actionnable indique d'utiliser `skillz-memory`.
- [ ] **AC4** — Given une mise à jour répétée, When l'installateur est relancé, Then les liens gérés sont mis à jour idempotemment.
- [ ] **AC5** — Given une désinstallation, When elle est confirmée, Then seuls les liens identifiés comme gérés par Skillz-Claude sont supprimés.

## Tâches techniques

- [ ] Ajouter le wrapper minimal sous `.claude/skills/llm-wiki/bin/`.
- [ ] Ajouter `install_memory_cli` et le suivi `binary:*` dans `install.sh`.
- [ ] Gérer le contrôle de version Python et le diagnostic `PATH`.
- [ ] Ajouter des tests shell sur installation, collision, update et uninstall.
- [ ] Documenter les deux noms de commande et le comportement de collision.

## Notes

- Ne pas créer de nouvel environnement virtuel pendant l'installation.
- Ne jamais télécharger QMD ou un modèle depuis ce chemin.

## Definition of Done

- [ ] Critères automatisés sur installation propre et collision.
- [ ] Smoke test `skillz-memory --version` vert.
- [ ] Aucune régression des installations Claude/Codex/Gemini/OpenCode.
- [ ] Documentation d'installation mise à jour.
