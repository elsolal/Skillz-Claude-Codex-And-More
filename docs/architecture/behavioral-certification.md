# Behavioral certification harness

The v6.1 harness separates structural contract cases from runtime certification. Case files use the
JSON-compatible YAML subset under `behavioral/cases/`; fixtures are local, secret-free and copied to
a temporary workspace for every iteration.

```bash
bash tests/test-behavioral.sh

# Direct selection/repetition
bash tests/run-python310.sh tooling/testing/behavioral_harness.py \
  --cases behavioral/cases \
  --case project-probe-node \
  --repeat 3 \
  --jobs 2 \
  --base-sha "$(git rev-parse HEAD^)" \
  --head-sha "$(git rev-parse HEAD)" \
  --output /tmp/run-result.json \
  --failure-dir /tmp/skillz-failures
```

`run-result.json` records case/iteration, runtime label, model/seed when declared, duration, exit
code, stdout/stderr, ordered events, hashes before/after, changed files and every assertion. Failed
workspaces are copied to the explicit failure directory before temporary cleanup. The envelope is
anchored to full `base_sha` and `head_sha` values.

Runtime versions are read from the executed binary. Captured stdout/stderr are bounded to 20,000
characters each and carry explicit truncation flags; this is evidence metadata, not a raw transcript
archive.

Generic assertions cover `files_exist`, `files_absent`, `files_unchanged`, `file_contains`,
`file_matches`, `stdout_contains`, ordered events and expected exit code. Commands containing known
permission-bypass flags are rejected before execution. The runner never adds permission flags.
Fixture and assertion paths are constrained to the copied workspace and symlinks are rejected.
This is deterministic filesystem isolation for trusted versioned cases, not an operating-system
sandbox for untrusted commands; cases must not contain secrets or network-dependent instructions.

The checked-in fixture cases prove harness behavior and workflow invariants at C1. They are not
model evaluations and cannot promote Claude, Codex or OpenCode to C3. Codex remains C2 from its
isolated native discovery evidence; a real headless skill invocation is still required before the
word “certified” is allowed without qualification.

`behavioral/manual-cases/codex-plugin-headless.yaml` defines that explicit C3 candidate. It uses
`workspace-write`, `--ephemeral` and no permission-bypass flag, expects the generated probe manifest
and fails when the skill marker is absent. It is excluded from CI because it requires an
authenticated Codex home with the development plugin already installed and makes model calls. Run
it only by explicitly selecting the manual case directory; its mere presence is not evidence.

Distribution goldens live at `docs/compatibility/golden/v6.1-p0-distribution.json`. Normal CI uses
`--check`. Updating requires both `--update` and `--approve-review`, making review intent explicit.
