---
title: Backlog - Observable second-brain efficiency
date: 2026-07-16
status: validated
validated_at: 2026-07-16
validated_by: Aymeric
prd: docs/planning/prd/PRD-second-brain-efficiency.md
architecture: docs/planning/architecture/ARCH-second-brain-efficiency.md
epics: 5
stories: 21
github_repository: elsolal/Skillz-Claude-Codex-And-More
github_publication: complete
github_publication_completed_at: 2026-07-17
---

# Backlog — Observable second-brain efficiency

## Objectif

Livrer puis éprouver un plan de contrôle `memory` qui rend les mini-cerveaux
projet portables, bornés et observables, sans indexer tout le code ni confondre
économie de contexte et qualité réelle.

## Ordre de réalisation

```text
EPIC-001 Portable activation
    -> EPIC-002 Bounded retrieval
        -> EPIC-003 Usage evidence
            -> EPIC-004 Measurement and maintenance
                -> EPIC-005 Pilots and rollout decision
```

`STORY-017` (profil docs/contrats) est P1 et peut avancer après le cœur retrieval
sans bloquer les pilotes P0.

## Epics

| Epic | Valeur | Stories | Priorité dominante |
|---|---|---:|---|
| [EPIC-001](EPIC-001-portable-activation/EPIC-001.md) | Un clone peut reconstruire et diagnostiquer sa liaison mémoire. | 4 | P0 |
| [EPIC-002](EPIC-002-bounded-retrieval/EPIC-002.md) | Une tâche obtient le minimum de mémoire pertinent et autorisé. | 5 | P0 |
| [EPIC-003](EPIC-003-usage-evidence/EPIC-003.md) | L'utilisateur distingue récupération mesurée et usage attesté. | 4 | P0 |
| [EPIC-004](EPIC-004-measurement-maintenance/EPIC-004.md) | La qualité, l'efficacité et la maintenance deviennent arbitrables. | 4 | P0/P1 |
| [EPIC-005](EPIC-005-pilots-rollout/EPIC-005.md) | Les deux pilotes produisent un verdict avant tout rollout global. | 4 | P0 |

## Publication GitHub

| Epic | Issue Epic | Issues Stories |
|---|---|---|
| EPIC-001 | [#36](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/36) | [#41](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/41), [#42](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/42), [#43](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/43), [#44](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/44) |
| EPIC-002 | [#37](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/37) | [#45](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/45), [#46](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/46), [#47](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/47), [#48](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/48), [#49](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/49) |
| EPIC-003 | [#38](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/38) | [#50](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/50), [#51](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/51), [#52](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/52), [#53](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/53) |
| EPIC-004 | [#39](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/39) | [#54](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/54), [#55](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/55), [#56](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/56), [#57](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/57) |
| EPIC-005 | [#40](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/40) | [#58](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/58), [#59](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/59), [#60](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/60), [#61](https://github.com/elsolal/Skillz-Claude-Codex-And-More/issues/61) |

## Règles transverses de Definition of Done

- Les tests déterministes correspondant au risque passent.
- Les sorties JSON modifiées conservent un `schema_version` explicite.
- Aucun prompt, réponse, secret ou chemin absolu n'entre dans la télémétrie.
- Les rendus humain et JSON représentent le même résultat métier.
- La documentation multi-runtime est mise à jour avec la source `.claude/`.
- Aucun changement n'est publié sur GitHub sans readiness score >= 13/15 et
  confirmation humaine distincte.
