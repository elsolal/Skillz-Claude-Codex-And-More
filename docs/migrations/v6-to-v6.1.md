---
title: "Migrate Skillz-Claude v6 to v6.1"
status: current
created_at: 2026-09-02
---

# Migrate Skillz-Claude v6 to v6.1

v6.1 moves canonical artifacts from the Claude tree to `core/`, builds runtime bundles under
`dist/`, and installs them with per-file ownership manifests. It also removes RALPH without a
compatibility launcher.

## Before updating

1. Commit or back up local provider files.
2. Run the legacy `/skillz-doctor` and inspect modified Skillz-owned files.
3. Preserve any user-authored hooks, commands or skills outside Skillz ownership.
4. Archive unfinished `docs/ralph-logs/` or `.claude/ralph-state.json` if they matter.

## Build and inspect the v6.1 bundle

```bash
bash tests/run-python310.sh tooling/build/compiler.py build --root . --output dist
bin/skillz --json install \
  --dist-root dist \
  --runtime codex \
  --target /explicit/provider/target \
  --dry-run
```

Use the runtime id from the compatibility matrix. The compiled installer never silently adopts an
existing file. A modified owned file, unexpected collision, symlink or unverifiable state blocks
the complete preflight before mutation.

After review, remove `--dry-run`, then run `doctor`. Update, restore and uninstall use the same
manifest; uninstall removes only current exact Skillz-owned hashes.

## Quality-gate transition

`project-probe` and `quality-gate` now own the Python selector and verifier resources they invoke.
Global installs, compiled provider bundles and per-project installs materialize the same resources.
Application repositories must not copy Skillz scripts into their own `scripts/` directory. If one
of these resources is missing, report `tooling-unavailable` and update or repair the Skillz
installation with the compiled installer or `./install.sh update all`; a product-quality waiver is
never the remedy for missing framework tooling.

Existing v1 gates remain `legacy-evidence`. Through the v6.1 release line, `/ship` may classify a
v1 `PASS` as `LEGACY_VALID` only when its recorded diff hash still matches the current branch
against the explicitly resolved default base and the manifest commands have just passed. A v1 gate
whose diff cannot be reconstructed requires a new v2 gate, but is not called stale merely because
its schema is old. New gates are always v2; the legacy acceptance path is scheduled for removal in
v6.2.

A v2 `WAIVED` gate must carry `reason`, `scope`, `approved_by` and timezone-aware `approved_at` in
its proof payload. It remains `WAIVED` in status and PR evidence and can be consumed without asking
the same human decision again.

## Breaking changes

- Removed commands: `/auto-loop`, `/auto-discovery`, `/auto-dev`, `/cancel-ralph`,
  `/resume-ralph`.
- Removed runtime surfaces: RALPH stop hook and active session-state contract.
- `.claude/` is a transitional compatibility mirror, not the canonical authoring location.
- Generated provider files under `dist/` must not be edited.
- Literal command syntax is not guaranteed across runtimes; use the documented semantic skill
  fallback where a native command surface is unavailable.
- Certification wording is evidence-bound: C1 generable, C2 discovered, C3 behaviorally certified.
- `/ship` resolves the remote default branch instead of assuming `origin/main`.

The complete removal and preservation policy remains in `docs/migrations/v6.1-ralph-removal.md`.

## Rollback

Use `bin/skillz restore --target /explicit/provider/target --dry-run`, review the action list, then
run without `--dry-run`. Restore is bounded to the installer's previous Skillz-owned snapshot and
does not overwrite user files created after installation.
