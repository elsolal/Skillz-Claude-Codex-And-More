# Compatibility evidence

This directory stores versioned, reviewable evidence for the provider-neutral migration. It does
not claim runtime support on the basis of generated files alone.

## Legacy v6 baseline

- `baseline-2026-09-01.yaml` records observed runtimes, legacy routes, explicit absences and local
  user-owned exclusions.
- `golden/legacy-v6-distribution.json` inventories the tracked distribution surface before the
  v6.1 migration. Every entry contains a repository-relative path, ownership, type, mode, size and
  SHA-256 digest.
- `scripts/capture_distribution_baseline.py` is the deterministic generator and checker.

The inventory boundary is the Git index. An untracked file is not considered Skillz-owned merely
because it lives below `.claude/`, `.codex/`, `.gemini/` or another provider directory.
The baseline collector itself and `.agents/verification.yaml` are control-plane evidence, not
legacy installed artifacts, and are explicitly excluded from this snapshot.

The original snapshot was generated from the pinned legacy source state:

```bash
bash tests/run-python310.sh scripts/capture_distribution_baseline.py \
  --write docs/compatibility/golden/legacy-v6-distribution.json
```

Routine verification checks the historical snapshot itself:

```bash
bash tests/run-python310.sh -m unittest tests.test_distribution_baseline
```

A post-v6 checkout is expected to differ from this snapshot. Regenerate it only from the pinned
legacy source state when the capture itself is proven wrong. A changed golden is evidence to
review, not a file to update automatically. Runtime certification is tracked separately at C1
(structure), C2 (native discovery) and C3 (behavioral smoke).

## v6.1 generated providers

- `p0-vertical-slice.md` records the Claude, Codex and OpenCode pilot routes.
- `provider-adapters.md` records the Kimi native, Kimi-via-Codex, Grok Build and Gemini routes,
  including the exact structural command and the evidence that is still absent.
- `golden/v6.1-p0-distribution.json` is the reviewed deterministic snapshot for every provider
  currently emitted by the compiler. Its historical filename is retained to avoid silently
  replacing the review anchor during the adapter rollout.
