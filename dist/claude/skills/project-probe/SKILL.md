---
name: project-probe
description: Detect and cache a project's real verification commands into a versioned .agents/verification.yaml manifest. Use at the start of dev and ship workflows, before verification, when the manifest is missing or stale, or when a recorded command no longer exists. Covers Node, Python, shell-only, mixed and monorepo projects without executing destructive candidates.
---

# Project Probe v2 — Verification Manifest

Every workflow reads one provider-neutral manifest: `.agents/verification.yaml`. The probe is
read-only; it inventories configuration and never runs application scripts while collecting.

## Runtime contract

The collector and Python selector are resources owned by this skill. Resolve the semantic locators
below through the active runtime's skill registry to absolute paths before invoking the shell; do
not interpret `skill:` as a literal filesystem path and do not look for these files in the project:

```bash
bash "skill:project-probe/scripts/run-python310.sh" "skill:project-probe/scripts/project_probe.py" --root . --check
```

If either resource cannot be resolved or executed, classify the result as `tooling-unavailable`
and recommend repairing/updating the Skillz installation. This is not project evidence and never
justifies a quality waiver.

Python 3.10+ is required. A generated manifest records the selected interpreter and version. If the
selector cannot find a compatible runtime it fails before probing with the detected version.

## Freshness

1. Run the command above.
2. A zero exit means `config_fingerprint` is fresh: read the manifest and stop.
3. If it is stale or absent, inspect `.agents/project-probe.json` when present, then regenerate:

```bash
bash "skill:project-probe/scripts/run-python310.sh" "skill:project-probe/scripts/project_probe.py" --root .
```

`fingerprint_schema_version: 2` hashes each repository-relative path and its bytes, sorted
deterministically. In Git repositories only indexed files participate, so local user-owned files do
not become project truth. The versioned collector covers shell scripts, `SKILL.md` and command
workflows, provider manifests, CI workflows, lockfiles, workspace markers and consumed config. The
manifest itself is excluded to avoid a self-invalidating hash.

## Command detection

Collect signals in this order:

1. `.agents/project-probe.json` explicit overrides, if any;
2. package scripts and Python tool configuration;
3. allowlisted shell roles (`lint`, `check`, `test`, `verify`, `build`);
4. CI evidence inspected by the agent when it strengthens or contradicts a candidate.

Only `lint`, `typecheck`, `test` and `build` are verification commands. Reject a candidate whose
name or body can deploy, publish, reset a database, destroy state, download remote content or remove
files. Never execute `clean`, `seed`, `migrate`, `release`, `deploy` or a user-defined near-match as
a sanity check. A safe `--help`, `--version` or documented dry-run may be used after collection; if
it cannot be confirmed, omit the command and record the reason.

Each accepted command remains a string under `commands` for v1 consumer compatibility. Its exact
origin is mandatory under `command_sources`. Missing capabilities appear both as human-readable
`absents` and keyed `absence_reasons`; never invent a fallback merely because a stack usually has
one.

## Manifest contract

```yaml
fingerprint_schema_version: 2
generated_by: "project-probe/2.0.0"
stack: "mixed"
config_fingerprint: "<sha256>"
fingerprint_sources:
  - ".agents/project-probe.json"
python:
  required: ">=3.10"
  selected_interpreter: "python3.12"
  selected_version: "3.13.7"
commands:
  lint: "bash -n scripts/*.sh"
command_sources:
  lint: ".agents/project-probe.json#commands.lint"
testability:
  harness: "shell+unittest"
  e2e: none
  runtime_verify: none
absents:
  - "no configured typecheck command"
absence_reasons:
  typecheck: "no configured typecheck command"
```

Optional `monorepo` metadata records the package manager and workspace globs. The override file may
declare commands, stack, Python requirement, testability and absence reasons, but it cannot bypass
the destructive-command filter.

## Consumer rules

- Run verification only from `commands`; provenance metadata is evidence, not an executable field.
- Every `commands` entry must be auto-executable by an agent. Human ceremonies such as a live
  preproduction rehearsal, manual UAT, Access/OTP/TOTP or a bounded waiver belong in `absents` with
  their trigger condition. Rewrite any manifest that incorrectly lists one as a command.
- Report every relevant absence in checkpoints and gate files.
- If `--check` reports drift or a command fails because its tool disappeared, re-probe before
  drawing a conclusion.
- Never list a human-gated ceremony in `commands`; the ship runner executes every command literally.
- Do not create provider-specific mirrors of the manifest.
- Do not write outside the requested manifest path.
