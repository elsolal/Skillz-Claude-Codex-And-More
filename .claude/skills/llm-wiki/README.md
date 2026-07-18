# llm-wiki

> **A second brain for Claude Code + Obsidian.**
> Inspired by [Andrej Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Turn any LLM CLI into a disciplined wiki maintainer. You curate sources and ask questions. The LLM reads, files, cross-references, flags contradictions, and keeps a living synthesis current. Knowledge **compounds** instead of being re-derived by RAG on every query.

## The idea in one paragraph

Most LLM+docs workflows are RAG: retrieve fragments at query time, synthesize from scratch, forget. The wiki is **compounding**. The LLM reads each source once and integrates it into a persistent, interlinked Obsidian vault — updating entity pages, revising concept pages, flagging contradictions, and strengthening the synthesis. The wiki is the compiled artifact; RAG is the just-in-time retrieval. This plugin gives the LLM the discipline (SKILL.md), the delegation (sub-agents), the triggers (slash commands), and the bookkeeping (Python tools) to do the job.

## What's in the box

| Piece | What it does |
|---|---|
| **SKILL.md** | Master skill doc — architecture, workflows, iron rules, cross-tool compat. Has `context: fork` so other skills can chain into it. |
| **3 sub-agents** | `wiki-ingestor`, `wiki-librarian`, `wiki-linter` |
| **6 slash commands** | `/wiki-init`, `/wiki-ingest`, `/wiki-query`, `/wiki-lint`, `/wiki-log`, `/wiki-capture-session` |
| **8 Python tools** | Standard library only: `init_vault`, `ingest_source`, `update_index`, `append_log`, `wiki_search` (BM25), `lint_wiki`, `graph_analyzer`, `export_marp` |
| **Portable memory CLI** | `skillz-memory` plus the collision-safe `memory` alias; Python 3.10+ stdlib runtime |
| **8 reference docs** | Schema, page formats, ingest/query/lint workflows, Obsidian setup, cross-tool setup, Memex principles |
| **Vault templates** | `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `index.md`, `log.md`, plus 5 page templates (entity, concept, source, comparison, synthesis) |
| **Example vault** | A small worked example on "LLM interpretability" |

## Quick start

Install Skillz-Claude globally, then verify the provider-neutral entrypoint:

```bash
bash install.sh install all
skillz-memory --version
```

The installer creates `~/.local/bin/skillz-memory`. It also creates
`~/.local/bin/memory` when the name is free or already managed by Skillz-Claude.
A third-party `memory` command is never overwritten; use `skillz-memory` when
the installer reports a collision. Ensure `~/.local/bin` is present in `PATH`.

### Portable memory manifest V1

Each activated repository versions `.agents/memory.yaml`. Despite its `.yaml`
extension, V1 deliberately accepts only the JSON-compatible subset of YAML 1.2:
keys and strings are quoted, and comments, tags, includes, anchors, and other
YAML-only syntax are rejected. This keeps parsing deterministic with the Python
standard library and prevents partial interpretation of hostile input.

```json
{
  "schema_version": 1,
  "project": {
    "id": "skillz-claude",
    "name": "Skillz-Claude",
    "owner": "Aymeric"
  },
  "stores": {
    "project": {
      "remote": "https://github.com/elsolal/elsolal-memory.git",
      "collection": "elsolal-wiki",
      "entry_pages": [
        "wiki/entities/skillz-claude.md",
        "wiki/concepts/project-memory-workflow.md"
      ]
    }
  },
  "fallbacks": [],
  "budgets": {
    "minimal": {"target_tokens": 800, "hard_tokens": 1200},
    "project": {"target_tokens": 2500, "hard_tokens": 4000},
    "historical": {"target_tokens": 6000, "hard_tokens": 9000}
  },
  "policy": {
    "semantic_retrieval": "explicit",
    "full_index_fallback": true,
    "retention_days": 30,
    "sufficiency_thresholds_version": "qmd-0.9-v1"
  },
  "golden": {
    "visible_path": ".agents/memory/golden.json",
    "quality_rubric": ".agents/memory/quality-rubric.json",
    "start_question": "What should I know before working on this project?"
  }
}
```

All IDs use lowercase kebab-case. Manifest paths are portable POSIX-relative
paths: absolute paths, `..` traversal, backslashes, shell interpolation, and
unknown keys are rejected. Budgets are positive integers and each target must
remain below or equal to its hard cap. Machine-local roots belong in the ignored
projection created by the later `memory configure` workflow, never here.

Validate the nearest manifest without accessing QMD or the network:

```bash
memory manifest
memory manifest --json
```

Validation failures use exit code `30`, identify the exact field, and include a
copyable correction. `--json` always retains the public result envelope schema,
even when the manifest's own `schema_version` is unsupported.

Map the portable project store to an accessible local vault and generate the
ignored agent pointers:

```bash
memory configure --store "project=/absolute/path/to/vault"
memory configure --store "project=/absolute/path/to/vault" --role owner
memory configure --store "project=/absolute/path/to/vault" --json
```

The default role is `collaborator`. A local role is routing context only: it
never grants filesystem, Git, or remote access. The command creates
`.agents/memory.local.json`, `.claude/project-memory.md`, and
`.agents/project-memory.md` with mode `0600` where supported, then protects all
three through Git's local `info/exclude`, including in linked worktrees.

Generated pointers carry a managed marker. Divergent unmanaged content is
preserved by default; use `--replace-managed` only after reviewing the local
file. Re-running the same configuration does not rewrite identical files.
Missing declared entry pages create the projection but return `degraded` with
exit code `10`. Absolute paths remain absent from output unless
`--explain-local-paths` is explicitly requested.

Diagnose the resulting activation before starting work:

```bash
memory doctor
memory doctor --explain
memory doctor --json
```

`doctor` is local, read-only, and network-free by default. A complete activation
returns `ready`/`0` and prints the manifest's `golden.start_question`. Existing
V1 manifests without that backward-compatible field remain valid, but doctor
returns `degraded`/`10` with the exact addition required. Missing QMD and unknown
or empty collections are degraded; an index older than 24 hours or its entry
pages is degraded too. The `minimal` and `project` modes can still use the
declared entry pages. A missing required
entry page, invalid projection, tracked local pointer, or inaccessible store is
`blocked` with its documented non-zero exit code.

Network and repair behavior always require explicit options:

```bash
memory doctor --network  # git ls-remote only; never fetches or updates refs
memory doctor --fix      # managed projection files and Git exclusions only
```

`--fix` never edits wiki pages, untracks files, or invokes `qmd update`/`embed`.
The main exit codes are `0` ready, `10` degraded but usable, `30` invalid local
activation, `31` missing required dependency, and `32` denied local/remote
access. Human, non-TTY, `NO_COLOR=1`, and JSON modes expose the same functional
status without relying on color or prompts.

Retrieve bounded project memory directly from the task:

```bash
memory context --mode project --task-category architecture "How is the CLI structured?"
memory context --mode project --task-category architecture --explain "How is the CLI structured?"
printf '%s' "private task query" | \
  memory context --mode project --task-category security --query-stdin --json
```

`context` always calls `qmd search --json` against the manifest's project
collection first, with an argument array and no shell interpolation. The
versioned `qmd-0.9-v1` sufficiency gate evaluates score, coverage, collection
freshness, path provenance, mode, and task category. It stops immediately on a
sufficient project result. Otherwise it may query one manifest fallback only
when the local principal role and the shared role/category allowlists both
authorize it. A denied fallback is neither called nor named in output.

The initial thresholds are one hit at `0.75` for `minimal`, one hit at `0.75`
or two at `0.55` for `project`, and two at `0.45` including a `sources/` or
`synthesis/` hit for `historical`. A stale collection is visible and blocks
security, data, and historical evidence. Unknown evidence returns
`ambiguous`/`21`; no model decides silently. The caller may rerun with
`--fallback-on-ambiguous` to explicitly allow an otherwise authorized fallback.
`--explain` prints the same decision profile, evidence, and reason codes already
present in JSON.

The query is never written to an event, receipt field, or temporary file by
`memory`. JSON and human output expose normalized hit metadata—docid,
collection, relative path, title, score, and snippet line—but omit the raw query
and snippet text. `--query-stdin` keeps sensitive input out of shell history;
QMD still receives it transiently as its required positional process argument.

A sufficient retrieval returns `sufficient`/`0`. Incomplete evidence returns
`insufficient`/`20`; ambiguity requiring an explicit decision returns `21`, and
blocking freshness returns `33`. Missing QMD returns `blocked`/`31`; timeout,
invalid JSON, oversized output, and other engine failures return `blocked`/`40`
with a specific retrieval status and correction. The default timeout is eight
seconds per route and can never exceed thirty seconds inside the adapter.

```bash
# 1. Initialize a vault
python scripts/init_vault.py --path ~/vaults/research --topic "LLM interpretability" --tool all

# 2. Open in Obsidian
open -a Obsidian ~/vaults/research

# 3. Drop a source into raw/ and ingest
cp ~/Downloads/paper.pdf ~/vaults/research/raw/papers/
cd ~/vaults/research
# in Claude Code:
> /wiki-ingest raw/papers/paper.pdf

# 4. Ask questions
> /wiki-query "what does the paper say about sparse features?"

# 5. Health check
> /wiki-lint
```

## Cross-tool compatibility

The scripts are pure Python stdlib — they run anywhere. Only the **schema loader** changes per tool:

| Tool | Loader file |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex CLI (OpenAI) | `AGENTS.md` |
| Cursor (modern) | `AGENTS.md` |
| Cursor (legacy) | `.cursorrules` |
| Antigravity (Google) | `AGENTS.md` |
| OpenCode / Pi | `AGENTS.md` |
| Gemini CLI | `AGENTS.md` |

`init_vault.py --tool all` installs all three. You can run multiple CLIs against the same vault.

See `references/cross-tool-setup.md` for per-tool instructions.

## Architecture

```
<vault>/
├── raw/                    # IMMUTABLE sources (you own)
├── wiki/                   # LLM-owned knowledge base
│   ├── index.md            # content catalog
│   ├── log.md              # append-only timeline
│   ├── entities/           # people, orgs, places, products
│   ├── concepts/           # ideas, theories, frameworks
│   ├── sources/            # one summary per ingested source
│   ├── comparisons/        # cross-source analyses
│   └── synthesis/          # high-level overviews and theses
├── CLAUDE.md               # schema for Claude Code
├── AGENTS.md               # schema for Codex/Cursor/Antigravity
└── .cursorrules            # (optional) legacy Cursor
```

**Iron rule:** The LLM never edits `raw/`. All writes go to `wiki/`.

## Three operations

- **Ingest** — Read a source, discuss with user, write summary page, update 5-15 cross-referenced pages, update index, log it
- **Query** — Read index first, drill into 3-10 pages, synthesize answer with inline citations, offer to file back as a new page
- **Lint** — Mechanical + semantic health check; surface contradictions, orphans, stale claims, cross-reference gaps

## Why not just RAG?

| Plain RAG | LLM Wiki |
|---|---|
| Rediscover knowledge each query | Knowledge accumulates |
| Cross-references re-computed every time | Cross-references pre-written and maintained |
| Contradictions surface only if you ask | Contradictions flagged during ingest |
| Exploration disappears into chat history | Good answers re-filed as new pages |
| Scales by embeddings infrastructure | Scales by markdown + `index.md` + optional local search |

The wiki and RAG aren't opposites — RAG can sit on top of the wiki once you outgrow index-first search.

## Status

**v1.0.0** — initial release. SKILL + 3 agents + 6 commands + 8 scripts + 8 references + full vault templates + example vault.

## License

MIT.

## Related

- [Karpathy's original gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — the pattern this plugin implements
- Vannevar Bush, "As We May Think" (1945) — the Memex
- [qmd](https://github.com/tobi/qmd) — local hybrid search over markdown (pair with this when the wiki outgrows `index.md`)
