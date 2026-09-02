---
name: figma-generate-library
description: "Build or update a professional-grade design system in Figma from a codebase. Use when the user wants to create variables/tokens, build component libraries, set up theming (light/dark modes), document foundations, or reconcile gaps between code and Figma. This skill teaches WHAT to build and in WHAT ORDER — it complements the `figma-use` skill which teaches HOW to call the Plugin API. Both skills should be loaded together."
---

# Design System Builder — Phase Router

Build or update a code-aligned Figma design system through one validated phase at a time. This file is the stable public contract and router; detailed procedures remain in phase-specific references.

## Mandatory prerequisite

Load the `figma-use` skill before every `use_figma` call. Always pass `skillNames: "figma-generate-library"` when this workflow invokes `use_figma`.

A design-system build is never one-shot. Calls are strictly sequential, creations are incremental, and every phase ends in validation plus an explicit human checkpoint.

## Route exactly one action

Determine the earliest incomplete phase from local code, Figma evidence, the approved plan, and the state ledger. Load only its action reference; do not preload every phase.

| Evidence state | Atomic action | Load |
|---|---|---|
| No approved scope mapping | Phase 0 — discover and lock scope | [discovery-phase.md](references/discovery-phase.md) |
| Scope approved; foundations incomplete | Phase 1 — create tokens and styles | [token-creation.md](references/token-creation.md) |
| Foundations approved; page skeleton incomplete | Phase 2 — create structure and documentation | [documentation-creation.md](references/documentation-creation.md) |
| Structure approved; a component incomplete | Phase 3 — create exactly one component | [component-creation.md](references/component-creation.md) |
| Components approved; integration incomplete | Phase 4 — Code Connect and final QA | [code-connect-setup.md](references/code-connect-setup.md) |
| Any script failed or state is inconsistent | Recovery — diagnose before retrying | [error-recovery.md](references/error-recovery.md) |

If evidence cannot identify the phase, stop and ask for the missing decision. Never infer approval. A new explicit user request, a validated phase transition, or an error may select a different action on the next turn.

Load [naming-conventions.md](references/naming-conventions.md) only when naming or auditing names. Load a helper under `scripts/` only for the selected action.

## Phase order and exit gates

```text
0 DISCOVERY
  code + Figma + subscribed libraries -> scope and conflict map
  CHECKPOINT: approve exact token and component scope

1 FOUNDATIONS
  collections -> primitives -> semantic aliases -> scopes -> code syntax -> styles
  CHECKPOINT: approve variable and style summary

2 FILE STRUCTURE
  Cover -> Getting Started -> Foundations -> separator -> Components -> separator -> Utilities
  CHECKPOINT: approve page list and screenshot

3 COMPONENTS
  one component at a time, atoms before molecules
  base -> bindings -> variants -> properties -> documentation -> validation
  CHECKPOINT: approve get_metadata + get_screenshot before the next component

4 INTEGRATION + QA
  Code Connect -> accessibility -> naming -> unresolved bindings -> screenshots
  CHECKPOINT: final sign-off
```

Never skip or reorder phases. Variables come before components. Never proceed from rejected or unvalidated work.

## Non-negotiable execution contract

- Inspect the codebase, current Figma file, and `search_design_system` before creating.
- Reuse priority: local existing → subscribed library import → create new. Wrap only when visuals match but the component API does not.
- Use `return` for tool output. Do not wrap code in an IIFE, call `closePlugin`, use `figma.notify()`, or rely on `console.log()`.
- Return all created or mutated node IDs from every call.
- Page context resets each call; use `await figma.setCurrentPageAsync(page)`.
- Await every Promise. Load the exact font before any text write. Colors use the 0–1 range.
- Never parallelize `use_figma` calls.
- Bind visual properties to variables by default. Set specific scopes on every variable; never leave `ALL_SCOPES`.
- Alias semantic variables to primitives instead of duplicating raw values.
- Set code syntax on every variable. WEB syntax includes the wrapper, for example `var(--color-bg-primary)`.
- Use `INSTANCE_SWAP` for icons; never create a variant per icon.
- Position variants after `combineAsVariants`; validate the resulting grid.
- Never hallucinate node IDs. Read them from returned values or the state ledger.
- Use deterministic names and returned IDs for cleanup. No destructive cleanup by broad search.
- Validate structure with `get_metadata` and visuals with `get_screenshot` before proceeding.
- On error, stop. Route to recovery, inspect evidence, then retry only the corrected atomic action.

## State and idempotency

Create a `RUN_ID` for long workflows. Tag every created scene node with shared plugin data:

```javascript
node.setSharedPluginData('dsb', 'run_id', RUN_ID);
node.setSharedPluginData('dsb', 'phase', 'phase3');
node.setSharedPluginData('dsb', 'key', 'component/button');
```

`getPluginData()` and `setPluginData()` are unsupported; use shared plugin data. Keep the returned-ID ledger at `/tmp/dsb-state-{RUN_ID}.json`. Before every creation, resolve by ledger ID plus deterministic name. If the target exists, validate and update or skip it—never duplicate it.

## Action resources

| Phase | Primary helpers |
|---|---|
| Discovery | [inspectFileStructure.js](scripts/inspectFileStructure.js) |
| Foundations | [createVariableCollection.js](scripts/createVariableCollection.js), [createSemanticTokens.js](scripts/createSemanticTokens.js) |
| Structure | [createDocumentationPage.js](scripts/createDocumentationPage.js) |
| Component | [createComponentWithVariants.js](scripts/createComponentWithVariants.js), [bindVariablesToComponent.js](scripts/bindVariablesToComponent.js), [validateCreation.js](scripts/validateCreation.js) |
| Recovery | [rehydrateState.js](scripts/rehydrateState.js), [cleanupOrphans.js](scripts/cleanupOrphans.js) |

Helper scripts are starting points, not permission to batch phases. Embed only the helper needed for the selected atomic call.

## Completion report

For each phase report:

- selected route and evidence;
- created, reused, updated, and skipped assets;
- returned node IDs and state-ledger path;
- validation evidence;
- unresolved conflicts;
- explicit checkpoint decision required next.

Do not claim completion from successful tool execution alone. Completion requires the phase exit criteria, structural and visual evidence, and the named human approval.
