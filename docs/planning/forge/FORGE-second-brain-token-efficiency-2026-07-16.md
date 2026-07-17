---
title: Pressure-test — Second-brain efficiency and observability
status: validated
created_at: 2026-07-16
validated_at: 2026-07-16
validated_by: Aymeric
slug: second-brain-token-efficiency
discovery_level: 4
lenses: [premortem, inversion, first-principles]
---

# FORGE — Second-brain efficiency and observability

## Thesis tested

Improve the Obsidian + llm-wiki + QMD second brain so that coding agents use it systematically, retrieve less irrelevant context, preserve more useful project and product knowledge, and expose evidence that the system is fresh, effective, and token-efficient across shared project vaults.

The initial implementation intuition was a small token-efficiency pass on `llm-wiki`: align contradictory query workflows, impose context budgets, add measurements, clarify whether code should be indexed, and monitor the Git-backed mini-brains.

## Verified starting facts

- Four Git-backed vaults are active locally: Elsolal, Ines, Pleepole, and Kering.
- 53 Git repositories were detected under `/Users/aymeric/Documents/PROJETS/DEV`.
- 47 repositories contain both local memory pointers, but only 32 have the complete Claude + AGENTS-compatible autoload chain. Presence of a pointer therefore does not prove activation.
- Six repositories have at least one missing start page in their pointer.
- The canonical `llm-wiki` query workflow still mandates `wiki/index.md` first and 3-10 full pages. The newer project-memory workflow recommends pointer -> project entity -> linked pages, with the index reserved for broad or historical questions.
- The previous token baseline measured roughly 16,564 tokens for the Elsolal index alone, roughly 1,424 tokens for the Skillz-Claude pointer + project entity route, and roughly 2,071 tokens for a filtered QMD route that returned two relevant full pages.
- QMD indexes the compiled `wiki/` directories only. It does not currently index the project codebases.
- No token budget, retrieval telemetry, provider-usage adapter, or executable golden-question dashboard exists in `llm-wiki`.
- Structural wiki lint is healthy. Operational freshness is weaker: Pleepole and Kering have log/index gaps, and a configured Git remote does not guarantee that useful local changes are merged and shared.
- At least one local pointer has grown into a 4.7 KB architecture memo. This shows that a pointer intended as a router can itself become recurring context overhead and a second source of truth.

## Lens 1 — Pre-mortem

**Core question:** It shipped and failed six months later — what killed it?

### Findings

1. **The project reports token savings that are not billable savings.** A local tokenizer estimate is presented as provider usage even though model tokenizers, caching, tool-call accounting, and agent runtimes differ.
2. **Mandatory memory loading raises the average context.** Every session reads a pointer, project page, and summary even when the task is trivial or fully explained by the live code.
3. **The rollout reaches 53 repositories before the retrieval contract is proven.** Broken loaders and generated pointers multiply while the team still cannot show better answers.
4. **Memory drift causes confident but stale decisions.** Code, product docs, and wiki pages evolve on different branches; agents trust the compiled explanation over the live repository.
5. **GitHub sharing is confused with readiness.** A vault has a remote, but changes remain local, on long-lived audit branches, or absent from QMD.
6. **Indexing all code creates noise and exposure.** Generated files, vendored definitions, secrets, and accidental technical hubs dominate retrieval while adding little product knowledge.
7. **The dashboard optimizes the wrong thing.** Teams chase lower token counts by retrieving too little context, decreasing answer quality and increasing rework.

### Required revisions

- Separate `estimated_memory_context_tokens` from provider-reported input, cached, and output tokens. Never merge them into one number.
- Make autoload conditional on task class: trivial/live-code tasks may load only the compact pointer; historical, architectural, and product questions may retrieve more.
- Pilot the contract on Skillz-Claude and one product-heavy shared vault before any fleet rollout.
- Attach provenance and freshness metadata to durable claims; always re-check the live repository before action.
- Measure Git share readiness independently from local vault health and QMD health.
- Use an allowlist for any code-adjacent index. Never ingest a whole repository into the wiki by default.
- Treat answer quality, citation correctness, and avoided rediscovery as primary metrics; tokens are an efficiency constraint.

### Verdict

The thesis survives only with revisions. A token-only project would likely optimize the visible metric while damaging memory usefulness.

## Lens 2 — Inversion

**Core question:** How would we guarantee this fails?

### Failure recipe

1. Always read the complete index first.
2. Read 3-10 full pages before checking whether the pointer already names the answer.
3. Copy code explanations into local pointers and duplicate source code inside Obsidian.
4. Index every file type in the same QMD collection.
5. Force every ingest to create or modify 5-15 pages regardless of information value.
6. Deploy loaders to every repository without checking that their entry pages exist.
7. Count corpus size, graph density, and tokens retrieved, but never test whether answers are correct.
8. Treat `qmd embed` freshness as proof that the underlying knowledge is true and shared.
9. Store full prompts or session content in telemetry to make measurement easy.
10. Add Graphify before establishing which code questions QMD and direct repository search cannot answer.

### Counter-rules

- Direct route first: pointer -> explicit entry page -> linked evidence.
- QMD route second: bounded top-k retrieval with a score threshold.
- Full index only for broad cross-project exploration or as a diagnosed fallback.
- Pointers remain routers, not architecture documents.
- Ingest touches only pages that gain durable meaning; no minimum page count.
- Code and memory use separate collections, freshness policies, and trust levels.
- Telemetry stores metadata by default, not prompt or answer content.
- Graphify remains an optional code-structure adapter evaluated against named code-navigation questions.

### Verdict

The current system already contains three elements of the failure recipe: index-first retrieval, potentially bloated pointers, and a normative 5-15-page ingest range. These should be corrected before adding new infrastructure.

## Lens 3 — First Principles

**Core question:** What do we actually know to be true here?

### Base facts

1. An LLM can only use memory that reaches its current context through instructions, file reads, search results, or tools.
2. A pointer on disk has zero value if the runtime does not load it or follow it.
3. Memory saves tokens only when the retrieved subset costs less than the re-exploration it prevents.
4. A smaller context is not better if it omits a decision that prevents a wrong implementation.
5. The live repository changes faster than the durable wiki and must remain the immediate source of truth.
6. Exact billable usage comes from provider telemetry; local token estimates remain useful for enforcing retrieval budgets.
7. Shared memory creates value when another human or agent can reproduce a correct answer, not when the vault merely contains many pages.

### Assumptions removed

- Autoload is not always beneficial; task-aware routing is better than unconditional loading.
- More indexed content does not imply better retrieval.
- A Git remote does not imply current, reviewed, or discoverable knowledge.
- One mini-brain per project is not automatically optimal; it is useful only when routing and cross-project synthesis remain clear.
- Golden questions alone do not represent real usage; they need periodic samples from actual sessions.
- Token reduction is not the product goal. The goal is lower total cost to reach a correct, source-backed action.

### Rebuilt solution kernel

**Problem:** Aymeric, collaborators, and coding agents cannot currently prove that project memory is automatically consulted, sufficiently fresh, correctly scoped, and cheaper than rediscovering context.

**For whom:** First Aymeric across Claude Code, Codex, and AGENTS-compatible agents; second, collaborators who clone the shared project-memory repositories.

**Central bet:** A small, task-aware retrieval contract backed by portable manifests, bounded context assembly, metadata-only telemetry, and executable retrieval tests will create more value than adding another knowledge store.

**Out of scope for the first release:**

- Full source-code ingestion into Obsidian.
- Automatic capture of every session.
- Fleet-wide rollout to all repositories before a pilot passes.
- Graphify installation as a mandatory dependency.
- A promise of exact cross-provider billing reconciliation.

### Verdict

The rebuilt kernel is stronger than the original token-efficiency framing. Continue, but pivot the project from **token reduction** to **memory effectiveness and efficiency observability**.

## Strongest objections that remain

1. **Instrumentation may cost more complexity than it saves.** The first release must use append-only, provider-neutral metadata and avoid a centralized service.
2. **Provider hooks are inconsistent.** The portable contract must work through explicit commands/loaders, with hooks used only as optional adapters.
3. **Golden tests can become stale theater.** Each vault needs a small owner-reviewed test set plus sampled real-session questions.
4. **Two pilot repositories may not represent the fleet.** Skillz-Claude should test tooling behavior; Pleepole should test product/code/team behavior. A third vault is added only if these expose incompatible needs.
5. **Task classification can become another expensive LLM step.** The first version should use simple declared modes (`minimal`, `project`, `historical`) rather than a sophisticated classifier.

## Surviving kernel

### Problem

The memory stack has durable knowledge and local retrieval, but no canonical bounded query contract, no proof of systematic activation, and no measurement connecting context cost to answer quality.

### For whom

Aymeric and collaborators using multiple coding-agent runtimes across Git-backed project vaults.

### Central bet

Standardize three retrieval modes, generate portable project-memory manifests, enforce context budgets, and run observable golden questions before considering a structural code graph.

## Recommended direction

1. **Baseline:** freeze representative questions and current retrieval/token measurements.
2. **Canonical contract:** define `minimal`, `project`, and `historical` retrieval modes with an explicit fallback ladder.
3. **Portable activation:** commit a machine-neutral memory manifest; generate ignored local paths from it.
4. **Observability:** record route, files, estimated memory tokens, timing, freshness, and outcome without storing query content by default.
5. **Quality tests:** execute golden questions across Claude Code, Codex, and one AGENTS-compatible runtime.
6. **Pilot:** Skillz-Claude + Pleepole only.
7. **Rollout gate:** expand only if quality does not regress and memory context materially decreases.
8. **Optional code layer:** evaluate a selected-docs QMD collection or Graphify only against code-navigation failures observed during the pilot.

## Candidate success thresholds to calibrate during baseline

- 100% of pilot repositories have a valid, portable activation path.
- Zero missing start pages in pilot pointers/manifests.
- At least 90% of golden questions retrieve the expected page and source in the first bounded route.
- No more than 5% degradation in answer correctness relative to the unrestricted baseline.
- At least 50% reduction in median memory-context tokens relative to the current index-first workflow.
- Full-index fallback below 10% of pilot queries.
- QMD refreshed within 24 hours of a merged wiki change.
- 100% of pilot retrieval executions emit a metadata-only telemetry event.
- Zero secrets or full prompt/answer bodies in telemetry and shared memory.

These are candidate gates, not promises. The baseline phase may adjust them before the PRD is approved.

## Final FORGE verdict

**PIVOT AND CONTINUE.**

Do not frame the product as a token optimizer. Frame it as an observable memory effectiveness system whose efficiency guardrail is token consumption. The first valuable release is not Graphify and not full code indexing; it is a proven retrieval contract on two representative projects.
