# Provider-neutral build pipeline

`core/catalog.yaml` is the registry of semantic artifacts. During the migration it may identify a
legacy source explicitly; `migration_state: canonical` is reserved for content owned below `core/`.

Each `providers/<id>/` directory contains two contracts:

- `capabilities.yaml` states whether each artifact type is `supported`, `pending` or `unsupported`;
- `build-contract.json` maps supported types to an output template and a pure transform.

The six symmetric artifact types are instruction, skill, command, agent, MCP and hook. The compiler
fails when a capability claim has no implementation, a dependency or source is missing, an alias or
output collides, or a catalog references an unknown provider.

```bash
bash scripts/run-python310.sh tooling/build/compiler.py build --root . --output dist
bash scripts/run-python310.sh tooling/build/compiler.py check --root . --output dist
```

Builds happen in a temporary sibling directory and publish atomically. `dist/build-report.json`
records every targeted artifact and every provider capability; its `tree_hash` excludes the report
itself to avoid self-reference. `dist/` is committed during v6.1 migration so generated changes are
reviewable. Generated files must never be edited manually.

To add a provider, add a directory containing both contracts and list that provider on the relevant
catalog artifacts. The compiler discovers it without code changes. Structural output is C1 only;
native discovery and behavioral certification remain separate C2/C3 gates.

The upstream registry at `tooling/upstream/sources.yaml` is scanned locally with
`tooling/upstream/scan.py`. It hashes adoption snapshots but never performs network access, imports
upstream modules or executes upstream content.
