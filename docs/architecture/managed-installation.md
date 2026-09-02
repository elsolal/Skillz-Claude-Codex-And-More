# Manifest-owned installation

`bin/skillz` is the v6.1 installation path for compiled provider bundles. It consumes
`dist/<runtime>` plus `dist/build-report.json`; it does not mirror `.claude/` or read legacy source
directories during installation.

## Ownership contract

Each target stores `.skillz/install-manifest.json` with a UUID, release, runtime and one entry per
managed file. Paths are target-relative. Every entry records the source and installed SHA-256,
mode, semantic source id, `ownership: skillz` and `merge_strategy: replace_owned`. The manifest
contains no absolute home path, credential or secret.

The versioned contracts are `core/contracts/install-manifest.schema.json` and
`core/contracts/doctor-report.schema.json`.

Before any write, the engine classifies every in-scope path:

- an unchanged manifest-owned file may be replaced or removed;
- a missing owned file may be repaired;
- a modified or unverifiable owned file blocks the complete operation;
- an existing file not present in the previous manifest is `unexpected` and blocks adoption;
- files outside the manifest and incoming bundle paths are not scanned.

The preflight completes before the first mutation. A successful install/update snapshots only the
changed managed paths under `.skillz/backups/<install-id>/`. Snapshots are bounded (three by
default). `restore` replays the snapshot associated with the current install and restores the
previous manifest. A failed mutation attempts the same rollback before returning an error.

## Commands

```bash
bin/skillz install --dist-root dist --runtime codex --target /explicit/target --dry-run
bin/skillz update --dist-root dist --runtime codex --target /explicit/target --dry-run
bin/skillz uninstall --target /explicit/target --dry-run
bin/skillz restore --target /explicit/target --dry-run
bin/skillz --json doctor --dist-root dist --runtime codex --target /explicit/target
```

Remove `--dry-run` only after reviewing the action list. `install` requires no existing manifest;
`update` requires one and also supports an explicit downgrade. `uninstall` removes only exact
manifest-owned hashes. All mutating commands refuse target, state or bundle symlinks that could
escape the declared roots.

## Doctor states

The JSON and human outputs are projections of the same report. File states are:

- `missing`: an expected or owned file is absent;
- `modified`: an owned file no longer matches its installed hash;
- `unexpected`: an incoming bundle path exists but is not owned;
- `orphaned`: a manifest-owned path is absent from the current bundle;
- `unverifiable`: a symlink, special file or unsafe state prevents hashing;
- `ok`: current bytes match the manifest.

Doctor also reports runtime detection/version, provider certification, release drift, summary
counts and bounded repair guidance. Runtime or file failures are `broken`; version/release drift is
`partial`; only a matching runtime, manifest and file set is `healthy`.
