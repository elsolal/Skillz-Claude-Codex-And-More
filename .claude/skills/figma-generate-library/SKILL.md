---
name: figma-generate-library
description: "Build or update a professional-grade design system in Figma from a codebase. Use when the user wants to create variables/tokens, build component libraries, set up theming (light/dark modes), document foundations, or reconcile gaps between code and Figma. This skill teaches WHAT to build and in WHAT ORDER — it complements the `figma-use` skill which teaches HOW to call the Plugin API. Both skills should be loaded together."
disable-model-invocation: false
---

# Design System Builder — Figma MCP Skill

Build professional-grade design systems in Figma that match code. This skill orchestrates multi-phase workflows across 20–100+ `use_figma` calls, enforcing quality patterns from real-world design systems (Material 3, Polaris, Figma UI3, Simple DS).

**Prerequisites**: The `figma-use` skill MUST also be loaded for every `use_figma` call. It provides Plugin API syntax rules (return pattern, page reset, ID return, font loading, color range). This skill provides design system domain knowledge and workflow orchestration.

**Always pass `skillNames: "figma-generate-library"` when calling `use_figma` as part of this skill.** This is a logging parameter — it does not affect execution.

---

## 1. The One Rule That Matters Most

**This is NEVER a one-shot task.** Building a design system requires 20–100+ `use_figma` calls across multiple phases, with mandatory user checkpoints between them. Any attempt to create everything in one call WILL produce broken, incomplete, or unrecoverable results. Break every operation to the smallest useful unit, validate, get feedback, proceed.

---

## 2. Mandatory Workflow

Every design system build follows this phase order. Skipping or reordering phases causes structural failures that are expensive to undo.

```
Phase 0: DISCOVERY (always first — no use_figma writes yet)
  0a. Analyze codebase → extract tokens, components, naming conventions
  0b. Inspect Figma file → pages, variables, components, styles, existing conventions
  0c. Search subscribed libraries → use search_design_system for reusable assets
  0d. Lock v1 scope → agree on exact token set + component list before any creation
  0e. Map code → Figma → resolve conflicts (code and Figma disagree = ask user)
  USER CHECKPOINT: present full plan, await explicit approval

Phase 1: FOUNDATIONS (tokens first — always before components)
  1a. Create variable collections and modes
  1b. Create primitive variables (raw values, 1 mode)
  1c. Create semantic variables (aliased to primitives, mode-aware)
  1d. Set scopes on ALL variables
  1e. Set code syntax on ALL variables
  1f. Create effect styles (shadows) and text styles (typography)
  → Exit criteria: every token from the agreed plan exists, all scopes set, all code syntax set
  USER CHECKPOINT: show variable summary, await approval

Phase 2: FILE STRUCTURE (before components)
  2a. Create page skeleton: Cover → Getting Started → Foundations → --- → Components → --- → Utilities
  2b. Create foundations documentation pages (color swatches, type specimens, spacing bars)
  → Exit criteria: all planned pages exist, foundations docs are navigable
  USER CHECKPOINT: show page list + screenshot, await approval

Phase 3: COMPONENTS (one at a time — never batch)
  For EACH component (in dependency order: atoms before molecules):
    3a. Create dedicated page
    3b. Build base component with auto-layout + full variable bindings
    3c. Create all variant combinations (combineAsVariants + grid layout)
    3d. Add component properties (TEXT, BOOLEAN, INSTANCE_SWAP)
    3e. Link properties to child nodes
    3f. Add page documentation (title, description, usage notes)
    3g. Validate: get_metadata (structure) + get_screenshot (visual)
    3h. Optional: lightweight Code Connect mapping while context is fresh
    → Exit criteria: variant count correct, all bindings verified, screenshot looks right
    USER CHECKPOINT per component: show screenshot, await approval before next component

Phase 4: INTEGRATION + QA (final pass)
  4a. Finalize all Code Connect mappings
  4b. Accessibility audit (contrast, min touch targets, focus visibility)
  4c. Naming audit (no duplicates, no unnamed nodes, consistent casing)
  4d. Unresolved bindings audit (no hardcoded fills/strokes remaining)
  4e. Final review screenshots of every page
  USER CHECKPOINT: complete sign-off
```

---

## 3. Critical Rules

**Plugin API basics** (from use_figma skill — enforced here too):
- Use `return` to send data back (auto-serialized). Do NOT wrap in IIFE or call closePlugin.
- Return ALL created/mutated node IDs in every return value
- Page context resets each call — always `await figma.setCurrentPageAsync(page)` at start
- `figma.notify()` throws — never use it
- Colors are 0–1 range, not 0–255
- Font MUST be loaded before any text write: `await figma.loadFontAsync({family, style})`. Use `await figma.listAvailableFontsAsync()` to discover available fonts and verify exact style strings.

**Design system rules**:
1. **Variables BEFORE components** — components bind to variables. No token = no component.
2. **Inspect before creating** — run read-only `use_figma` to discover existing conventions. Match them.
3. **One page per component** *(default)* — exception: tightly related families may share a page.
4. **Bind visual properties to variables** *(default)* — fills, strokes, padding, radius, gap.
5. **Scopes on every variable** — NEVER leave as `ALL_SCOPES`. Background: `FRAME_FILL, SHAPE_FILL`. Text: `TEXT_FILL`. Border: `STROKE_COLOR`. Spacing: `GAP`. Radii: `CORNER_RADIUS`. Primitives: `[]` (hidden).
6. **Code syntax on every variable** — WEB syntax MUST use the `var()` wrapper: `var(--color-bg-primary)`, not `--color-bg-primary`.
7. **Alias semantics to primitives** — `{ type: 'VARIABLE_ALIAS', id: primitiveVar.id }`. Never duplicate raw values in semantic layer.
8. **Position variants after combineAsVariants** — they stack at (0,0). Manually grid-layout + resize.
9. **INSTANCE_SWAP for icons** — never create a variant per icon.
10. **Deterministic naming** — use consistent, unique node names for idempotent cleanup.
11. **No destructive cleanup** — cleanup scripts identify nodes by name convention or returned IDs.
12. **Validate before proceeding** — never build on unvalidated work.
13. **NEVER parallelize `use_figma` calls** — strictly sequential.
14. **Never hallucinate Node IDs** — always read from state ledger.
15. **Use the helper scripts** — embed scripts from `scripts/` into your use_figma calls.
16. **Explicit phase approval** — at each checkpoint, name the next phase explicitly.

---

## 4. State Management (Required for Long Workflows)

> **`getPluginData()` / `setPluginData()` are NOT supported in `use_figma`.** Use `getSharedPluginData()` / `setSharedPluginData()` instead, or use name-based lookups and the state ledger (returned IDs).

Tag every created **scene node** immediately after creation:
```javascript
node.setSharedPluginData('dsb', 'run_id', RUN_ID);
node.setSharedPluginData('dsb', 'phase', 'phase3');
node.setSharedPluginData('dsb', 'key', 'component/button');
```

**State persistence**: Write state ledger to disk:
```
/tmp/dsb-state-{RUN_ID}.json
```

**Idempotency check** before every create: query by name + state ledger ID. If exists, skip or update — never duplicate.

---

## 5. search_design_system — Reuse Decision Matrix

Search FIRST in Phase 0, then again immediately before each component creation.

**Reuse if**: Component property API matches, token binding model compatible, naming conventions match, component is editable.

**Rebuild if**: API incompatibility, token model incompatible, ownership issue.

**Wrap if**: Visual match but API incompatible — import as nested instance inside a wrapper component.

**Three-way priority**: local existing → subscribed library import → create new.

---

## 6. User Checkpoints

Mandatory. Design decisions require human judgment.

| After | Required artifacts | Ask |
|-------|-------------------|-----|
| Discovery + scope lock | Token list, component list, gap analysis | "Here's my plan. Approve before I create anything?" |
| Foundations | Variable summary, style list | "All tokens created. Review before file structure?" |
| File structure | Page list + screenshot | "Pages set up. Review before components?" |
| Each component | get_screenshot of component page | "Here's [Component] with N variants. Correct?" |
| Final QA | Per-page screenshots + audit report | "Complete. Sign off?" |

**If user rejects**: fix before moving on. Never build on rejected work.

---

## 7. Naming Conventions

Match existing file conventions. If starting fresh:

**Variables** (slash-separated):
```
color/bg/primary     color/text/secondary    color/border/default
spacing/xs  spacing/sm  spacing/md  spacing/lg  spacing/xl
radius/none  radius/sm  radius/md  radius/lg  radius/full
```

**Primitives**: `blue/50` → `blue/900`, `gray/50` → `gray/900`

**Component names**: `Button`, `Input`, `Card`, `Avatar`, `Badge`

**Variant names**: `Property=Value, Property=Value`

> Full naming reference: [naming-conventions.md](references/naming-conventions.md)

---

## 8. Token Architecture

| Complexity | Pattern |
|-----------|---------|
| < 50 tokens | Single collection, 2 modes (Light/Dark) |
| 50–200 tokens | **Standard**: Primitives (1 mode) + Color semantic (Light/Dark) + Spacing (1 mode) + Typography (1 mode) |
| 200+ tokens | **Advanced**: Multiple semantic collections, 4–8 modes |

---

## 9. Per-Phase Anti-Patterns

**Phase 0**: Starting to create before scope is locked. Ignoring existing conventions. Skipping `search_design_system`.

**Phase 1**: Using `ALL_SCOPES`. Duplicating raw values in semantic layer. Not setting code syntax.

**Phase 2**: Skipping cover page. Putting multiple unrelated components on one page.

**Phase 3**: Creating components before foundations. Hardcoding fills/strokes/spacing. Creating variant per icon. Not positioning variants after combineAsVariants.

**General**: Retrying failed scripts blindly. Parallelizing use_figma calls. Guessing node IDs.

---

## 10. Reference Docs

Load on demand — each reference is authoritative for its phase:

| Doc | Phase | Load when |
|-----|-------|-----------|
| [discovery-phase.md](references/discovery-phase.md) | 0 | Starting any build |
| [token-creation.md](references/token-creation.md) | 1 | Creating variables, collections, modes, styles |
| [documentation-creation.md](references/documentation-creation.md) | 2 | Creating cover page, foundations docs |
| [component-creation.md](references/component-creation.md) | 3 | Creating any component or variant |
| [code-connect-setup.md](references/code-connect-setup.md) | 3–4 | Setting up Code Connect |
| [naming-conventions.md](references/naming-conventions.md) | Any | Naming anything |
| [error-recovery.md](references/error-recovery.md) | Any | Script fails, recovery |

---

## 11. Scripts

Reusable Plugin API helper functions. Embed in `use_figma` calls:

| Script | Purpose |
|--------|---------|
| [inspectFileStructure.js](scripts/inspectFileStructure.js) | Discover all pages, components, variables, styles |
| [createVariableCollection.js](scripts/createVariableCollection.js) | Create a named collection with modes |
| [createSemanticTokens.js](scripts/createSemanticTokens.js) | Create aliased semantic variables |
| [createComponentWithVariants.js](scripts/createComponentWithVariants.js) | Build a component set from a variant matrix |
| [bindVariablesToComponent.js](scripts/bindVariablesToComponent.js) | Bind design tokens to component visual properties |
| [createDocumentationPage.js](scripts/createDocumentationPage.js) | Create a page with title + description |
| [validateCreation.js](scripts/validateCreation.js) | Verify created nodes match expected counts |
| [cleanupOrphans.js](scripts/cleanupOrphans.js) | Remove orphaned nodes |
| [rehydrateState.js](scripts/rehydrateState.js) | Scan file for state reconstruction |
