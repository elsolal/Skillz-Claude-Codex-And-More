# Quality gate v2

Gate v2 separates code identity, executable proof and envelope integrity:

- `GATE-*.yaml` names full base/head SHAs, the code diff hash, the exact payload and its hash.
- `proofs/*.json` records every manifest command, exit status, absences and review convergence.
- `scripts/gate_verify.py` seals the YAML and verifies both files against Git and
  `.agents/verification.yaml`.

Only `CHANGELOG.md` may be excluded from the code diff. The evidence commit may contain only the
named gate, the named proof payload and optionally `CHANGELOG.md`; another `docs/quality` change is
not implicitly trusted.

```bash
bash scripts/run-python310.sh scripts/gate_verify.py seal docs/quality/GATE-example.yaml
bash scripts/run-python310.sh scripts/gate_verify.py verify docs/quality/GATE-example.yaml --root .
```

Existing schema-v1 gates are retained as historical evidence. They must be regenerated as v2 before
`/ship` can consume them as fresh proof.
