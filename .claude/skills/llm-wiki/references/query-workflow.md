# Query Workflow

The flow the LLM follows when the user runs `/wiki-query <question>` or dispatches the `wiki-librarian` sub-agent.

## Core principle

**Start from the task and the nearest project memory contract.** An activated project retrieves through `memory context`; a standalone vault without `.agents/memory.yaml` keeps the historical wiki workflow as an explicit legacy/non-pilot route.

## Route selection

### 1. Identify the task and activation

Keep the user's question as the task. From the project repository, look for the nearest `.agents/memory.yaml` and its local projection. Do not preload a complete wiki index before choosing the route.

### 2. Activated project: use `memory context`

When `.agents/memory.yaml` is present and configured, choose the narrowest suitable mode and task category, then retrieve from the declared project collection first:

```bash
memory context --mode project --task-category <category> "<task>"
```

Use `--query-stdin` for sensitive task text. Consume the returned `read` sections and receipt; do not reopen every `retrieved` candidate. The CLI owns sufficiency, budget enforcement, freshness, provenance, and any authorized fallback.

If QMD is unavailable, keep using `memory context`. For `minimal` and `project`, it degrades only to the manifest-declared `entry_pages` under their one-page or three-page caps. It never scans the vault or opens an undeclared full index. `historical` reports that QMD is required.

If activation is invalid, report the `memory doctor` correction instead of silently switching to a broader route.

### 3. Vault without a manifest: legacy/non-pilot query

When no `.agents/memory.yaml` applies, preserve the historical `/wiki-query` behavior:

1. Open `wiki/index.md` as the standalone vault catalog.
2. Pick 3-10 relevant pages across `synthesis/`, `concepts/`, `sources/`, `entities/`, and `comparisons/`.
3. Read those pages, follow relevant wikilinks, and stop when the answer is supported.
4. If needed, run `python scripts/wiki_search.py --vault . --query "<terms>" --limit 5`.

This route is explicitly **legacy/non-pilot**. It does not invoke `memory context`, create a memory receipt/event, or count toward pilot usage. Do not describe it as evidence produced by the bounded retrieval pilot.

## Synthesize the answer

Compose the answer as:

- A direct answer in 1-3 sentences
- Supporting detail, organized thematically
- **Inline citations** using wikilinks to source pages: `[[sources/monosemanticity]]`
- **A "Related pages" section** at the end with 3-5 wikilinks

If the selected route does not provide enough evidence, say so. Do not invent content or broaden beyond the manifest policy.

## Offer to re-file

**Every good answer is a candidate wiki page.** At the end of the answer, ask:

> _Should I file this as a new page in the wiki? Suggested location:
> `wiki/comparisons/sae-vs-probing.md` — or I can append it to an existing page._

If the user says yes:

- Pick the right category (most often `comparisons/` or `synthesis/`)
- Use the appropriate template
- Add frontmatter with `category`, `summary`, `sources` (count of cited sources), `updated`
- Update `index.md`
- Append to `log.md` with `op: create` and the question as the title

## Output formats

- **Markdown page** (default) — filed back as a wiki page
- **Comparison table** — for "A vs B" questions
- **Marp slide deck** — via `python scripts/export_marp.py` on the synthesis page
- **Chart (matplotlib)** — for data-driven questions; save to `wiki/assets/charts/`
- **Obsidian Canvas** — for visual exploration (JSON format, stored at `wiki/canvases/`)

## Anti-patterns

- ❌ Preload a complete index before checking `.agents/memory.yaml`
- ❌ Bypass `memory context` because QMD is unavailable
- ❌ Attribute a legacy/non-pilot query to the bounded memory pilot
- ❌ Answer without citations
- ❌ Invent content not present in the selected evidence
- ❌ Skip the `log.md` entry when filing an answer back
