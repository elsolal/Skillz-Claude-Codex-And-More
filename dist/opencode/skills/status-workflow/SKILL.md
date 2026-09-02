---
name: status-workflow
description: Evidence-backed, read-only project status guide that classifies installation, runtime capabilities, probe, planning, implementation, quality-gate, and ship readiness without inventing state.
---

# Status Workflow — Evidence-backed Project Guide

`/status` is a read-only classifier. It reports only states supported by local evidence, cites that evidence next to every conclusion, and proposes one justified next action without executing it.

**Input**: none. An explicit installation target or runtime supplied by the user may narrow the scan.

**Output**: runtime/install health, project phase, evidence table, and one next-step recommendation.

## Invariants

- Never modify files, install or update anything, run project checks, commit, push, or fetch.
- Never infer that an installation, phase, test, or gate is healthy from the presence of source files alone.
- Distinguish `absent`, `stale`, `partial`, `ready`, and `unknown`. Missing proof means `unknown` unless the expected location was resolved and checked.
- Cite an exact local path, command result, hash comparison, branch fact, or runtime probe for every state and recommendation.
- Treat `docs/`, generated `dist/`, comments, and historical gates as context, not proof of current runtime or ship state.

## Evidence collection

Collect independent reads in parallel when the runtime supports it. A sequential fallback must produce the same classifications.

### 1. Runtime and installation

1. Inspect `providers/*/capabilities.yaml` for declared artifact support and certification level.
2. Probe only known runtime executables with `command -v`; record the resolved executable and observed version when available. A provider contract is not proof that its runtime is installed.
3. If the active runtime and installation target can be resolved, run the manifest-owned doctor in read-only mode:

   ```bash
   bash tests/run-python310.sh tooling/install/skillz.py --json doctor \
     --dist-root dist --runtime <runtime> --target <explicit-target>
   ```

4. Interpret doctor evidence exactly:
   - no manifest at a resolved target plus missing expected files → `not-installed`;
   - `broken`, file-state drift, or missing owned files → `partially-installed`;
   - `partial` or release/version drift → `partially-installed`;
   - `healthy` → `installed`;
   - unresolved target or unavailable doctor evidence → `installation-unknown`.

Never search an entire home directory. Never run install, update, restore, or uninstall from `/status`.

### 2. Project probe

- Missing `.agents/verification.yaml` → `project-unprobed`.
- Resolve the project-probe resources through the active skill registry. Missing or incompatible
  resources → `tooling-unavailable`; never reinterpret this as a project-quality concern.
- Otherwise run the read-only freshness check:

```bash
bash "skill:project-probe/scripts/run-python310.sh" "skill:project-probe/scripts/project_probe.py" \
  --root . --output .agents/verification.yaml --check
  ```

- Non-zero freshness result → `project-unprobed` with reason `stale manifest`.
- A fresh manifest proves only configured verification commands and declared absences; it does not prove those commands passed.

### 3. Planning lifecycle

Inspect current planning documents under `docs/planning/{plans,specs,prd,architecture}/`. When the lifecycle validator exists, run it read-only:

```bash
bash tests/run-python310.sh scripts/validate_planning_lifecycle.py --root . --json
```

For the work item associated with the current branch or user request:

- an applicable draft or missing approval fields → `plan-awaiting-approval`;
- an approved applicable spec plus no implementation evidence → planning is ready;
- `archived` and `superseded` documents are never selected as active instructions;
- multiple plausible current documents without a branch/task link → `planning-unknown`, not an invented match.

### 4. Implementation and gate

Read `git status --short`, `git branch --show-current`, `git log --oneline -5`, and local gate files under `docs/quality/`.

Resolve the comparison base read-only from an explicit caller value, then remote HEAD metadata, then
a unique local `main`/`master`/`trunk`. If more than one candidate remains, report
`planning-unknown` or `gate-migration-required` as applicable and ask for the base; never guess.

- A branch other than the resolved default branch, with commits or tracked work attributable to the
  current task → `implementation-in-progress`.
- Unrelated or untracked files are reported separately and never treated as implementation proof.
- Identify a candidate gate only when its scope/branch metadata matches the current work. Resolve
  the quality-gate resources through the active skill registry and verify it mechanically:

  ```bash
  bash "skill:quality-gate/scripts/run-python310.sh" "skill:quality-gate/scripts/gate_verify.py" \
    --root . verify <gate-file> --allow-legacy --legacy-base-ref <resolved-base-ref>
  ```

- Missing verifier resources → `tooling-unavailable`, with installation repair as the next action.
- A v1 gate that cannot be matched to the current diff → `gate-migration-required`; call it
  `legacy-evidence`, never `stale-v2`.
- A v2 gate with failed envelope verification, mismatched diff hash, mismatched manifest fingerprint, or commits after the gate → `gate-stale`.
- A fresh `PASS` gate plus a clean scoped diff and a shippable feature branch → `ready-to-ship`.
- A fresh, mechanically valid `WAIVED` gate with complete decision metadata →
  `ready-to-ship-with-waiver`; quote its reason and scope and never relabel it PASS.
- A `legacy-valid` PASS gate during the compatibility window → `ready-to-ship-legacy`; report the
  reduced assurance and recommend v2 for the next gate.
- `CONCERNS` or `FAIL` never silently become ready; report the exact verdict and required action.

GitHub issue and PR reads are optional corroboration. A missing `gh` binary, authentication, or network is a limitation, not a reason to fail the local status report.

## State precedence and next action

Choose the first supported state in this order. Do not skip a higher-priority blocker.

| State | Minimum proof | Justified next action |
|---|---|---|
| `not-installed` | resolved target checked; no manifest and expected bundle absent | show the explicit dry-run install command |
| `partially-installed` | doctor reports broken/partial/drift | review doctor conflicts, then explicit update/restore action |
| `tooling-unavailable` | required skill-owned probe/verifier resource cannot resolve or execute | repair or update the Skillz installation; never request a quality waiver |
| `project-unprobed` | manifest missing or freshness check fails | run `project-probe` |
| `plan-awaiting-approval` | applicable plan/spec lacks required human approval | review and approve the named spec |
| `implementation-in-progress` | scoped branch commits or tracked changes; no fresh PASS gate | continue `/dev` at the evidenced phase |
| `gate-stale` | matching gate absent or mechanical verification fails | rerun `quality-gate` after checks |
| `gate-migration-required` | v1 is readable but its historical diff cannot be verified | generate a v2 gate with the repaired skill-owned tooling |
| `ready-to-ship` | fresh PASS gate, valid envelope, clean scoped state | `/ship <branch>` |
| `ready-to-ship-with-waiver` | fresh WAIVED gate with complete human decision metadata | `/ship <branch>` while preserving the waiver in the PR |
| `ready-to-ship-legacy` | matching v1 PASS plus fresh execution evidence during compatibility window | `/ship <branch>` with `LEGACY_VALID` disclosed |
| `idle-or-unknown` | no stronger state has adequate proof | ask for task scope or pick the next priority |

The recommendation must name the evidence that caused it and must not execute the action.

## Output format

```markdown
## Runtime and installation
| Runtime | Detected/version | Declared capabilities | Certification | Install health | Evidence/limitations |

## Project state
| Layer | State | Evidence |
| Installation | ... | ... |
| Probe | ... | ... |
| Planning | ... | ... |
| Implementation | ... | ... |
| Gate | ... | ... |

Current state: `<classified-state>`
Why: <one sentence citing exact proof>
Next step: `<command or human action>` — <why it is the next safe transition>
```

Use `unknown` or `not checked` in cells that lack evidence. Never replace missing values with reassuring language.

## Anti-patterns

- Treating `dist/<runtime>` or a provider contract as proof of installation
- Treating any feature branch or dirty file as proof that the current task is implemented
- Selecting the newest plan by date without checking lifecycle and task relevance
- Recommending `/ship` because a gate file exists without verifying its envelope and freshness
- Repairing installation drift, regenerating probe/gate files, or running checks from `/status`
