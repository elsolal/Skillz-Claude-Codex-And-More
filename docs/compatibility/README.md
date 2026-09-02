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

Regenerate intentionally:

```bash
bash tests/run-python310.sh scripts/capture_distribution_baseline.py \
  --write docs/compatibility/golden/legacy-v6-distribution.json
```

Check for drift without writing:

```bash
bash tests/run-python310.sh scripts/capture_distribution_baseline.py \
  --check docs/compatibility/golden/legacy-v6-distribution.json
```

A changed golden is evidence to review, not a file to update automatically. Runtime certification
is tracked separately at C1 (structure), C2 (native discovery) and C3 (behavioral smoke).
