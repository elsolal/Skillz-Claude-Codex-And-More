---
name: thermo-nuclear-code-quality-review
description: Runs an unusually strict code-quality and maintainability review. Use when the user asks for a thermo-nuclear or thermonuclear review, a very harsh code-quality audit, a deep maintainability review, or a structural simplification pass before ship. Produces prioritized structural findings and concrete cleaner-design remedies.
---

# Thermo-Nuclear Code Quality Review

Use this skill for an unusually strict review focused on implementation quality,
maintainability, abstraction quality, and codebase health.

The goal is not to collect minor cleanup notes. The goal is to find structural
simplifications that preserve behavior while making the implementation smaller,
clearer, more direct, and easier to reason about.

## When To Use

- The user asks for a "thermo-nuclear", "thermonuclear", "very strict", "harsh",
  or "deep code quality" review.
- A PR or branch technically works but may have grown abstraction debt,
  large-file debt, or tangled conditional logic.
- `quality-gate` needs an extra maintainability lens beyond the normal
  correctness/readability/performance passes.
- Before `/ship`, when the risk is structural maintainability rather than only
  tests, security, performance, design, or SEO.

## When Not To Use

- For normal correctness review only: use `code-reviewer`.
- For security-specific findings: use `security-auditor` or the security lens in
  `quality-gate`.
- For visual/product UI quality: use `taste-critic`, `design-audit`, or
  `a11y-enforcer`.
- For performance-specific profiling: use `performance-auditor`.
- For implementation fixes: first produce the review. Only edit code if the user
  explicitly asks to fix the findings or if this skill is running inside an
  integrated `quality-gate` loop that already owns fixes.

## Runtime Compatibility

This skill is provider-neutral. It does not require Cursor-only metadata,
Claude-only slash commands, subagents, or MCP tools.

- Claude Code: may run as a skill or as one lens inside `quality-gate`.
- Codex CLI: read this `SKILL.md` fully, inspect the diff locally, and run the
  review inline. If multiple lenses are needed, run them sequentially with a
  clear mental reset between passes.
- OpenCode, Gemini, and generic agents: use the same local-diff workflow and the
  same output contract. If a provider cannot create inline comments, report
  findings with file and line references.
- Cursor: the original upstream skill uses Cursor metadata. In Skillz-Claude,
  that metadata is intentionally omitted so the same file works across providers.

## Inputs

Prefer the narrowest review target the user gave:

- Current branch diff: compare against the default branch (`main`, then
  `master`) unless the user names another base.
- PR number or URL: inspect the PR diff and relevant files.
- Path or file: review only that scope, but still inspect neighboring code when
  needed to judge ownership boundaries.
- No target: use the current branch diff.

If there is no diff and no explicit path, ask for the target instead of
inventing one.

## Process

1. **Find the review surface.**
   Inspect `git status --short --branch`, identify the base branch, and list the
   changed files. Do not assume the branch or diff shape.

2. **Read the surrounding architecture.**
   Read changed files plus the nearest existing helpers, modules, tests, and
   callers needed to understand the local design. Look for the canonical layer
   that already owns the concept.

3. **Measure structural movement.**
   Check whether the diff:
   - pushes any file from below 1000 lines to above 1000 lines,
   - adds repeated conditionals or feature flags in multiple places,
   - introduces new helpers that mostly pass data through,
   - adds casts, `any`, `unknown`, or optional shapes that hide invariants,
   - serializes independent work or creates partial-update states,
   - moves logic away from the package/module that owns the concept.

4. **Look for simplification moves.**
   For every meaningful change, ask whether behavior can stay the same while
   deleting concepts, branches, helpers, modes, or layers. Prefer remedies that
   remove complexity over remedies that merely reorganize it.

5. **Prioritize blockers.**
   Findings should lead with structural regressions and missed simplifications,
   not nits. If the code is acceptable, say that explicitly and name the residual
   risks.

6. **Do not edit in review mode.**
   Unless the caller is `quality-gate` integrated mode or the user asked for
   fixes, stop at the review report.

## Review Standards

Apply these standards aggressively:

1. **Structural simplification beats local polish.**
   Do not stop at "this could be cleaner". Search for reframings that make whole
   branches, helpers, modes, conditionals, or layers disappear.

2. **A file crossing 1000 lines is a strong smell.**
   If the PR pushes a file from below 1000 lines to above 1000 lines, ask whether
   it should be decomposed first. Waive only with a compelling structural reason.

3. **Do not normalize spaghetti growth.**
   Treat ad-hoc conditionals, scattered special cases, and one-off mode flags as
   design problems, even when they technically work.

4. **Prefer direct boring code over magic.**
   Flag generic machinery, identity wrappers, thin abstractions, and hidden data
   shape assumptions when they add indirection without clarity.

5. **Make type and boundary invariants explicit.**
   Question unnecessary optionality, casts, `unknown`, `any`, and silent
   fallback behavior when a clearer boundary or model would simplify control
   flow.

6. **Keep logic in the canonical layer.**
   Reuse existing helpers and push feature logic toward the module, package, or
   service that already owns the concept.

7. **Treat unnecessary sequencing and non-atomic updates as design smells.**
   If independent work is serialized or related writes can leave half-applied
   state, ask whether a simpler parallel or atomic structure exists.

## Primary Questions

For every meaningful change, ask:

- Is there a simplification move that would make this dramatically smaller?
- Can the same behavior be represented with fewer branches or concepts?
- Did the diff improve or worsen the local architecture?
- Is the logic living in the right file, module, package, and layer?
- Did a cohesive module become more coupled, more stateful, or harder to scan?
- Are repeated conditionals signaling a missing model, helper, dispatcher, or
  policy object?
- Does the abstraction earn its keep, or is it just a wrapper?
- Did the diff introduce casts, optional shapes, or ad-hoc objects that obscure
  a real invariant?
- Did the change duplicate a canonical helper or create a near-duplicate?
- Is orchestration more sequential or less atomic than it needs to be?

## What To Flag Aggressively

Escalate high-conviction findings for:

- Complicated implementations where a cleaner reframing could delete whole
  categories of complexity.
- Refactors that move complexity around without reducing the number of concepts
  a reader must hold.
- Files crossing 1000 lines due to the diff.
- New conditionals bolted onto unrelated or already busy code paths.
- One-off booleans, nullable modes, or flags that complicate existing flow.
- Feature-specific logic leaking into general-purpose modules.
- Generic magic that hides simple structure.
- Thin wrappers or identity abstractions.
- Unnecessary casts, `any`, `unknown`, or optional params.
- Copy-pasted logic where a focused helper would clarify ownership.
- Edge-case handling inserted into a busy function.
- Temporary branching likely to become permanent debt.
- Bespoke helpers when the codebase already has a canonical utility.
- Logic added in the wrong layer or package.
- Avoidable sequential async work or non-atomic partial updates.

## Preferred Remedies

Prefer suggestions that:

- delete a whole layer of indirection,
- reframe the state model so conditionals disappear,
- move ownership to the canonical abstraction,
- turn special cases into a simpler default flow,
- extract a pure helper or focused module,
- split large files into cohesive smaller modules,
- replace condition chains with a typed model or dispatcher,
- separate orchestration from business logic,
- collapse duplicate branches into one clear path,
- remove wrappers that do not clarify the API,
- reuse an existing helper instead of adding a near-duplicate,
- make type boundaries explicit,
- parallelize independent work when it also simplifies orchestration,
- restructure related updates into an atomic flow.

## Output Contract

Lead with findings, ordered by severity and grounded in `file:line` references.

Use this shape:

```text
Findings
- [P1] <short title> - <file>:<line>
  <why this is a structural code-quality problem>
  Remedy: <specific simpler structure>

Open Questions
- <only questions that materially affect the verdict>

Verdict
<approve / concerns / block>, with a short reason.

Residual Risk
<tests or runtime checks not run, if any>
```

Severity guidance:

- P0: structural issue that can break behavior, data integrity, security, or
  maintainability immediately.
- P1: should block approval unless justified; clear structural regression or
  obvious missed simplification.
- P2: meaningful maintainability debt that should be fixed soon.
- P3: small cleanup, only include if no larger issues dominate.

## Approval Bar

Do not approve merely because behavior seems correct. Approval requires:

- no clear structural regression,
- no obvious simplification path that would materially reduce complexity,
- no unjustified file-size explosion,
- no obvious spaghetti growth,
- no hacky or magical abstraction that makes the code harder to reason about,
- no unnecessary wrapper, cast, or optionality churn obscuring the design,
- no clear architecture-boundary leak,
- no avoidable duplication of canonical helpers.

Treat these as presumptive blockers unless clearly justified:

- the diff preserves incidental complexity when a plausible simpler model exists,
- a file crosses from below 1000 lines to above 1000 lines,
- ad-hoc branching tangles an existing flow,
- feature checks are scattered through shared code,
- unnecessary wrappers or cast-heavy contracts make the design more indirect,
- logic duplicates an existing helper or lives in the wrong layer.

## Anti-Patterns

- Cosmetic-only feedback while structural debt is present.
- Asking for a rename when the real issue is ownership or model shape.
- Accepting "it works" while the codebase gets harder to reason about.
- Suggesting a refactor that only spreads the same complexity across more files.
- Editing files during standalone review mode.
