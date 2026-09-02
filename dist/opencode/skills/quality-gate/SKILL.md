---
name: quality-gate
description: Bounded agentic quality loop that replaces human code re-reading before PR. Runs execution evidence (lint/types/tests/runtime verify), multi-lens reviews in fresh contexts, final structural maintainability review via thermo-nuclear-code-quality-review, adversarial counter-verification of every finding, loops until convergence, and writes a versioned gate file (PASS/CONCERNS/FAIL/WAIVED) with proof. Use after implementation in /dev, before PR in /ship, or standalone via /gate on any diff the user wants gated.
---

# Quality Gate — Convergence Loop

Replaces the one-shot "review ×3" with a bounded loop that produces an auditable verdict. The user reads the gate file instead of the diff.

**Inputs**:
- The diff to gate: `git diff <base>...HEAD` where `<base>` is the repo's default branch (`main`, or `master` if `main` does not exist), unless the caller designates another diff.
- The validated plan / acceptance criteria, when the caller has one.
- `.agents/verification.yaml` — if missing, run the `project-probe` skill first.
- The task level (0-4). Default: 2. The caller passes it; level 0 changes are not gated (no gate file).
- The mode: **integrated** (called by dev-workflow or ship-workflow — the loop fixes autonomously) or **standalone** (invoked via /gate or directly by the user — report first, the user arbitrates every fix; see step 4).

**Output**: a v2 envelope `docs/quality/GATE-<YYYY-MM-DD>-<slug>.yaml`, its JSON proof payload under `docs/quality/proofs/`, and a short summary to the caller. Both evidence files are committed together and must pass `gate_verify.py verify`.

## Loop bounds by level

| Level | Max rounds | Review lenses |
|---|---|---|
| 1 | 1 | one generalist reviewer with a quick structural-smell check |
| 2 | 3 | correctness+security · readability · performance · final `thermo-nuclear-code-quality-review` |
| 3-4 | 4 | level-2 lenses + `design-audit` / `seo-geo-audit` / `a11y-enforcer` for the surfaces the caller detected; `thermo-nuclear-code-quality-review` still runs last |

## One round

1. **EXECUTION EVIDENCE — always first, never skipped.**
   Run every command in the manifest's `commands`. If the harness provides the `verify` skill, drive the app's real affected flow (not just tests); otherwise use the manifest's `testability.runtime_verify` command to launch the app and drive the affected flow yourself. Any red → fix immediately → restart the round. A restart consumes a round from the cap; if execution evidence cannot be made green within the cap, the verdict is `FAIL`. (At level 1 the single-round exception below still applies: fixing and re-running green within that round is allowed and does not consume a second round.) Record each command and its actual result; a claim without the executed command's output is worthless.
   If the diff touches only docs/config with no runtime surface, still run the manifest commands and note the limitation in `absents` — never skip silently.

2. **MULTI-LENS REVIEWS — fresh contexts.**
   Each lens reviews the diff + plan only (no session history). Findings are classified P0 (must fix) / P1 (should fix) / P2-P3 (note).
   The lens order is deliberate:
   1. Core lenses: correctness+security, readability, performance.
   2. Conditional domain lenses: `design-audit`, `seo-geo-audit`, `a11y-enforcer` only when Phase 1 detected those surfaces.
   3. Final structural lens: `thermo-nuclear-code-quality-review` for level ≥ 2. This pass runs after the other lenses so it can judge the final implementation shape without duplicating their domains. It must ignore issues already covered as correctness, security, performance, UI/DS, SEO/GEO or a11y unless the same issue also creates a distinct structural maintainability regression. It only reports abstraction debt, giant-file growth, spaghetti branching, boundary leaks, unnecessary wrappers/casts, non-atomic orchestration, and missed simplification moves.
   **Runtime capabilities:**
   - *Claude Code*: use the native `/code-review` skill as the primary correctness lens (its CONFIRMED/PLAUSIBLE verdicts feed step 3 directly — CONFIRMED skips re-verification). Dispatch the remaining lenses as parallel subagents when useful, but keep `thermo-nuclear-code-quality-review` as the final pass after their outputs are available.
   - *Sequential runtimes (Codex CLI, OpenCode, Gemini)*: run the lenses one at a time in the order above, with an explicit mental reset between lenses. Run `thermo-nuclear-code-quality-review` last and de-duplicate it against already-recorded findings before step 3.

3. **ADVERSARIAL COUNTER-VERIFICATION — new findings only.**
   Maintain a findings registry across rounds. Stable id: `<file>:<category>:<8-char-hash-of-quoted-excerpt>`.
   - A finding already in the registry (confirmed or refuted) is not re-verified and not counted as new.
   - Each NEW finding goes to an independent verifier whose explicit job is to REFUTE it against the actual code. Uncertain → refuted (bias against false positives) — EXCEPT security findings (injection, auth bypass, secret exposure, trust-boundary violations): an uncertain security finding stays confirmed until positively disproven.
   - Confirmed → fix queue. Refuted → registry, never returns.

4. **FIX confirmed P0/P1**, then return to step 1. P2/P3 go to the gate file as notes, not fixes (no scope creep).
   - **Integrated mode**: the orchestrator fixes autonomously — it has the context and the loop's job is to converge without human input.
   - **Standalone mode**: NEVER modify a file before the user chooses. After counter-verification, present the **detailed report first** — one entry per finding: file:line, severity (P0-P3), confirmed/refuted with the verifier's reason, and the proposed fix (quoted). Then ask: **[A] apply all confirmed P0/P1 and continue the loop** | **[S] select which findings to fix** | **[R] report only** — write the gate file with the current verdict (unfixed confirmed P0/P1 ⇒ FAIL or CONCERNS per the verdict rules) and stop. On later rounds, present only the new findings (the delta) before fixing.

**Convergence**: two consecutive rounds with zero new confirmed P0/P1 findings → verdict (P2/P3 notes never count toward convergence). Cap reached without convergence → verdict `CONCERNS`, remaining findings listed. Never loop past the cap.
**Level-1 exception** (cap = 1 round): the verdict is decided on that single round — confirmed findings fixed + execution evidence re-run green → `PASS`. The Verdict-rules preconditions still apply: without at least one real executable proof, the verdict caps at `CONCERNS` even here.

## Verdict rules

- `PASS` requires ALL of: every available executable evidence green · zero confirmed P0/P1 findings remaining (confirmed P2/P3 are recorded as notes and do not block PASS) · at least one real executable proof (tests or runtime verify). A project with no executable evidence at all **caps at `CONCERNS`** — the gate cannot claim more than it knows.
- `FAIL`: confirmed P0 remaining that could not be fixed within the cap.
- `CONCERNS`: cap reached without convergence, or executable evidence too weak for PASS, or unfixed confirmed P1.
- `WAIVED`: only on explicit user request, with the reason recorded in the gate file.

## Gate v2 evidence and integrity

```yaml
# docs/quality/GATE-2026-07-05-auth-refresh.yaml
schema_version: 2
verdict: "PASS"
level: 2
base_sha: "<full 40-char code base SHA>"
head_sha: "<full 40-char last code SHA before evidence commit>"
code_diff_hash: "<sha256 of git diff base...head>"
code_diff_exclusions: ["CHANGELOG.md"]
proof_payload: "docs/quality/proofs/2026-07-05-auth-refresh.json"
proof_payload_hash: "<sha256 of exact JSON bytes>"
integrity_sha256: "<self-integrity hash written by gate seal>"
```

The proof payload is strict JSON (`schema_version: 1`) with the manifest fingerprint, one execution
entry for every command in `.agents/verification.yaml`, absences, opinion findings, rounds and
autonomous decisions. Every execution records the exact command, status and exit code. A PASS
payload contains no invented command, no missing command and no non-passing status.

`base_sha` and `head_sha` identify the code diff. Because a committed gate cannot contain the SHA
of its own commit, `head_sha` is the final code commit before the evidence-only commit. Verification
accepts current `HEAD == head_sha` or descendants whose entire delta is limited to the exact gate,
its named proof payload and `CHANGELOG.md`. Any other path, including another file below
`docs/quality/`, makes the gate stale.

The sole permitted code-diff exclusion is the exact `CHANGELOG.md` path. There is no blanket
`docs/quality` exclusion. Build the JSON payload, compute its byte hash, create the YAML with a
64-zero integrity placeholder, then run:

```bash
bash scripts/run-python310.sh scripts/gate_verify.py seal docs/quality/GATE-<date>-<slug>.yaml
git add docs/quality/GATE-<date>-<slug>.yaml docs/quality/proofs/<date>-<slug>.json
git commit -m "chore(quality): gate <slug>"
bash scripts/run-python310.sh scripts/gate_verify.py verify docs/quality/GATE-<date>-<slug>.yaml --root .
```

Never hand-edit a sealed gate or its proof. Regenerate and reseal instead. v1 gates remain historical
evidence but are not accepted as fresh v2 proof. A future GitHub Check may invoke the same verifier;
it is intentionally non-blocking until local rollout evidence is complete.

`decisions_prises_en_ton_nom` lists every autonomous deviation from the validated plan. **For levels 3-4 the calling workflow must show this section to the user before proposing ship** — it is the only careful read left to the human.

## Anti-patterns

- Claiming a command is green without showing its executed output.
- Re-verifying or re-counting registry findings (the loop never converges).
- Skipping execution evidence because "only docs changed".
- Fixing P2/P3 style findings during the loop (scope creep — note them instead).
- Looping past the cap, or emitting PASS on opinion alone.
- Modifying any file in standalone mode before the user has arbitrated the report.
