---
name: wiki-query
description: Query project memory task-first through memory context, with a bounded entry_pages degradation path and an explicit legacy/non-pilot route for vaults without .agents/memory.yaml. Usage /wiki-query question
---

# /wiki-query

Ask project memory a question. The librarian starts from the task and selects the route from the nearest `.agents/memory.yaml` instead of preloading a complete wiki catalog.

## Usage

```
/wiki-query "<your question>"
/wiki-query "what does the wiki say about sparse autoencoders?"
/wiki-query "compare monosemanticity and polysemanticity across my sources"
```

## What happens

### Activated project

1. Keep the question as the task and detect the nearest `.agents/memory.yaml` plus local projection.
2. Run `memory context --mode project --task-category <category> "<task>"` against the declared project collection.
3. Consume only the returned `read` sections and preserve their receipt/provenance.
4. If QMD is unavailable, let `memory context` degrade to the declared `entry_pages` caps; never open an undeclared full index.
5. Synthesize with inline `[[wikilink]]` citations and offer to file substantive answers back.

### Vault without `.agents/memory.yaml`

Use the historical catalog-and-pages workflow documented in `references/query-workflow.md`. Mark it **legacy/non-pilot**: it does not call `memory context`, emit a memory receipt/event, or count as pilot usage.

## Output formats

The answer's format follows the question:

| Question shape | Output |
|---|---|
| "What is X?" | Markdown explanation with citations |
| "A vs B" | Comparison table |
| "Give me a slide deck on X" | Markdown synthesis → `/wiki-marp` to render |
| "Chart the trend in X" | Python script + saved chart in `wiki/assets/charts/` |

## Sub-agent

This command dispatches the `wiki-librarian` sub-agent. See `agents/wiki-librarian.md`.

## Scripts

- `engineering/llm-wiki/scripts/wiki_search.py` — BM25 fallback search
- `engineering/llm-wiki/scripts/append_log.py` — log filed answers

## Rules

- Start from the task and project collection for activated repositories.
- Do not bypass `memory context` when QMD is missing; its bounded `entry_pages` path is the supported degradation.
- Never attribute the legacy/non-pilot path to the bounded retrieval pilot.
- Every substantive claim cites a page with a `[[wikilink]]`.
- Offer to file back only answers worth keeping.

## Skill Reference

→ `engineering/llm-wiki/SKILL.md`
→ `engineering/llm-wiki/references/query-workflow.md`
