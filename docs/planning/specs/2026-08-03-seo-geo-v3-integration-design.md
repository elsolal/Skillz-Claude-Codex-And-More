---
title: SEO/GEO Squad V3.1 Integration
status: approved
approved_by: human
approved_at: 2026-08-03T12:00:00+01:00
slug: seo-geo-v3-integration
source_version: 3.1.0
---

# SEO/GEO Squad V3.1 Integration

## Context

Skillz-Claude currently exposes `seo-geo-audit` as a portable 11-agent prompt pack. The supplied SEO/GEO V3.1 kit is a materially different system: 21 routed specialists, persistent client projects, evidence-linked structured records, five separate score dimensions, deterministic QA, Delta monitoring, supervised implementation, and HTML/PDF delivery.

This is a level-4 migration because it adds executable code and persistent client-data contracts. The user approved this plan in the interactive checkpoint on 2026-08-03.

## Architecture decision

- Keep `seo-geo-audit` as the stable public skill and command name.
- Vendor the V3.1 kit under `references/seo-geo-v3/` as the authoritative method and runtime.
- Make the public `SKILL.md` a thin provider-neutral router into the V3 modes.
- Remove the legacy V1/V2 prompt corpus from the repository and prevent managed stale files from remaining authoritative after updates.
- Keep QA, PR review, quality-gate and ship-gate invocations read-only. Persistent projects, connectors, implementation and external writes require an explicit user request and approval.
- Preserve the V3 evidence chain: source -> evidence -> fact -> finding -> action -> implementation -> outcome.
- Never publish a single opaque score; expose F, V, O, E and M with coverage, confidence and freshness.

## Security adaptations

The vendored V3.1 source is hardened before distribution:

1. Restrict PDF `file://` requests to the input document tree and bundled assets.
2. Reject private, loopback, link-local, multicast and otherwise non-public network destinations in the rule-source checker, including redirects and DNS resolution.
3. Do not initialize an authorization timestamp before a real approver is recorded.
4. Remove instructions that recommend `pip --break-system-packages`; use an isolated environment instead.
5. Document Skillz-Claude patches and regenerate the V3 integrity manifest.

## Provider contract

- Claude commands, Codex prompts, Gemini commands and OpenCode commands remain thin launchers.
- `seo-geo-audit` selects the smallest V3 route that answers the request.
- `seo-geo-squad` loads the V3 orchestrator and routes relevant specialists; it never launches all 21 mechanically.
- Missing tools or connectors remain `not_measured`/`unknown`; the launcher must not simulate results.

## Acceptance criteria

1. The public names `/seo-geo-audit` and `/seo-geo-squad` continue to work across all four providers.
2. No active launcher or canonical skill instruction routes to the legacy 11-agent corpus.
3. The V3 manifest validates after the documented security patches and declares 21 specialists.
4. Audit and gate callers remain read-only unless the user explicitly requests a persistent or mutating V3 mode.
5. Security regression tests cover PDF local-file isolation and non-public network rejection.
6. A temporary V3 client project can be created and validated without writing into the repository.
7. Provider installation smoke tests prove the canonical skill and both launchers are installed without overwriting unrelated provider content.
8. Repository lint/tests and the level-4 quality-gate complete with an honest PASS, CONCERNS or FAIL verdict.

## Verification strategy

- P0: V3 integrity, all V3 unit tests, security regressions, authorization defaults.
- P1: create/validate temporary project; provider installation/update smoke tests; legacy routing absence.
- P2: repository manifest lint/test commands, YAML/TOML parsing, Node syntax, `git diff --check`.
- P3: PDF rendering in a disposable environment when Node 20, Playwright and Chromium are available. Live GSC/GA4/GEO connector proof is outside repository validation and must be reported as absent unless explicitly supplied.

## Out of scope

- Running an audit against a real client site.
- Installing optional PDF dependencies globally.
- Connecting client accounts or storing credentials.
- Publishing content or deploying changes to an audited site.
- Rewriting unrelated D-EPCT workflows or user-owned untracked files.
