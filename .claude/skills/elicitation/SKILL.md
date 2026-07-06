---
name: elicitation
description: Re-examine an existing output (PRD, plan, spec, code, decision, doc) through ONE named reasoning lens — Pre-mortem, Inversion, First Principles, Red/Blue Team, Steelman, Chesterton's Fence and more — instead of a vague "make it better". Loaded by /elicit. Use after any phase output, before validating a checkpoint, or whenever a second structured look would beat a rewrite.
---

# Elicitation — Named Reasoning Lenses

A lens is a disciplined second pass over something that already exists. It reveals; it does not rewrite.

**Inputs**: a target (file path, or the conversation's latest phase output) and a lens id — or no lens, in which case present the menu.
**Output**: findings under that single lens + proposed revisions. The user arbitrates; nothing is applied without their pick.

## Protocol

1. **Load the lens** from `.claude/knowledge/brainstorming/elicitation-methods.csv` (columns: `lens_id,name,description,core_question,best_for`). No lens given → show the menu as a numbered table (name + core question + best_for) and let the user pick; suggest the 2-3 best fits for the target type.
2. **Re-read the target under that single lens.** Hold the `core_question` against every section. Do not mix lenses; do not drift into general review.
3. **Produce the findings**, structured:
   - **Lens**: name + core question
   - **Findings**: 3-8 bullets — each one names the section/claim it hits and what the lens reveals
   - **Proposed revisions**: concrete, minimal edits or additions (quote what would change) — proposals, not applied changes
   - **Verdict**: does the target survive this lens as-is, with revisions, or not at all?
4. **The user arbitrates**: apply some/all revisions, run another lens, or stop. One lens per pass — chaining lenses is fine, blending them is not.

## Rules

- One lens at a time. The value comes from the discipline of the single question.
- The lens reveals — it never rewrites the target itself. Revisions are proposals.
- Findings must point at specific sections/claims, never "overall it could be better".
- Actionable output over essay: every finding either triggers a proposed revision or names an accepted risk.
- If the target survives a lens with nothing found, say so plainly — an empty pass is information, not failure.

## Where this plugs in

- `discovery-workflow` checkpoints: offer `[E] apply a lens before validating`.
- `rodin` (socratic challenge): distinct gesture — rodin argues against the position; elicitation re-reads it under one question. Use rodin for "challenge this", a lens for "re-examine this under X".
- `idea-brainstorm` synthesis: offer a lens pass on the top ideas before closing.
- `multi-mind`: the Contrarian persona may pick any lens as its weapon.

## Anti-patterns

- Blending several lenses in one pass (produces generic review soup)
- Rewriting the target instead of proposing revisions
- Running a lens on nothing (the target must exist first — this is not ideation)
- Treating the menu as a checklist to run entirely (2-3 well-chosen lenses beat 12 mechanical ones)
