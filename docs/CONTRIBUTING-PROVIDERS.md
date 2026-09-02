# Contributing artifacts, providers and behavioral evals

The source of truth is the provider-neutral graph under `core/`. Do not edit generated files under
`dist/`, and do not add new canonical workflow logic under a provider directory.

## Change or add an artifact

1. Add or edit `core/skills/<id>/SKILL.md` or `core/commands/<alias>.md`.
2. Keep canonical frontmatter to `name`, `description` and optional `license`.
3. Register the artifact in `core/catalog.yaml`: stable id, public name, type, dependencies,
   inputs, outputs, aliases, providers, risk and resource closure.
4. Put runtime-only frontmatter in `provider_metadata`, never in the canonical entrypoint.
5. Run the catalog validator, compiler check, golden check and relevant behavioral cases.

The migration helper is intentionally narrow:

```bash
bash tests/run-python310.sh tooling/migration/migrate_catalog.py \
  --root . \
  --report docs/compatibility/catalog-migration-v6.1.json
```

`--apply` exists for reviewed legacy relocation only. It refuses symlinks, path traversal and
canonical drift. Normal feature work edits `core/` directly.

## Add a provider

Create `providers/<id>/capabilities.yaml` and `providers/<id>/build-contract.json`. The capability
file records observed runtime/version and the honest C0-C3 level. The build contract maps each of
the six artifact types (`instruction`, `skill`, `command`, `agent`, `mcp`, `hook`) to
`supported`, `pending` or `unsupported`, plus an output template and a pure transform when
supported.

Then add the provider id only to artifacts it can generate. The generic compiler discovers the new
directory; provider-specific business logic in `tooling/build/compiler.py` is a design smell.
Generated output proves C1 only. Add a pinned native-discovery report for C2 and a behavioral smoke
for C3.

## Add a behavioral eval

Add a JSON-compatible YAML case under `behavioral/cases/` for deterministic structural coverage,
or under `behavioral/manual-cases/` when authentication/model calls are required. Declare the
runtime, fixture, command, repeat/timeout/permissions and invariant assertions. Never add a global
permission bypass.

```bash
bash tests/run-python310.sh tooling/testing/behavioral_harness.py \
  --cases behavioral/cases \
  --case <case-id> \
  --repeat 3 \
  --jobs 2 \
  --base-sha "$(git rev-parse HEAD^)" \
  --head-sha "$(git rev-parse HEAD)" \
  --output /tmp/run-result.json \
  --failure-dir /tmp/skillz-failures
```

Assertions should target ordered events, files, hashes and exit status—not exact model prose. A
manual case is not evidence until its result is captured against the pinned runtime and reviewed.

## Required checks

```bash
bash tests/run-python310.sh tooling/build/compiler.py check --root . --output dist
bash tests/run-python310.sh tooling/testing/golden_distribution.py \
  --dist-root dist \
  --output docs/compatibility/golden/v6.1-p0-distribution.json \
  --check
bash tests/test-behavioral.sh
```

Updating a golden requires `--update --approve-review`. Finish the scoped implementation with a
fresh v2 quality gate before proposing delivery.
