# Expected Outputs

Sample outputs for each script in `scripts/`. Use these as fixtures when testing
or to verify the scripts behave correctly end-to-end.

| Script | Fixture |
|---|---|
| `init_vault.py --json` | `init_vault.json` |
| `ingest_source.py --json` | `ingest_source.json` |
| `update_index.py --json` | `update_index.json` |
| `append_log.py --json` | `append_log.json` |
| `wiki_search.py --json` | `wiki_search.json` |
| `lint_wiki.py --json` | `lint_wiki.json` |
| `graph_analyzer.py --json` | `graph_analyzer.json` |
| `export_marp.py --json` | `export_marp.json` |
| `memory manifest --json` | `memory/manifest-valid.json` |
| invalid `memory manifest --json` | `memory/manifest-invalid-version.json` |
| `memory configure --json` | `memory/configure-ready.json` |
| degraded `memory configure --json` | `memory/configure-degraded.json` |
| `memory doctor --json` | `memory/doctor-ready.json` |
| `memory context --json` | `memory/context-ready.json` |
| degraded `memory context --json` without QMD | `memory/context-degraded.json` |
| initial and final human context receipts | `memory/context-receipts-human.txt` |
| `memory finish --json` | `memory/finish-ready.json` |
| empty human `memory finish` receipt | `memory/finish-receipt-human.txt` |
| high-risk `memory finish --conflict --json` | `memory/finish-conflict.json` |
| high-risk human `memory finish --conflict` receipt | `memory/finish-conflict-human.txt` |
| `memory purge --json` with fresh project events | `memory/purge-ready.json` |
| `memory test --json` | `memory/test-ready.json` |
| `memory test record-quality --json` | `memory/test-quality-recorded.json` |
| passing `memory test gate --json` | `memory/test-gate-pass.json` |

These were captured against a small 2-page example vault (one concept page and
one source page, both with proper frontmatter). Paths have been anonymized to
`/tmp/test-vault`.
