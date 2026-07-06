---
name: quality-gate
description: Bounded agentic quality loop that replaces human code re-reading before PR. Runs execution evidence (lint/types/tests/runtime verify), multi-lens reviews in fresh contexts, adversarial counter-verification of every finding, loops until convergence, and writes a versioned gate file (PASS/CONCERNS/FAIL/WAIVED) with proof. Use after implementation in /dev, before PR in /ship, or standalone via /gate on any diff the user wants gated.
---

# Quality Gate — Convergence Loop

Replaces the one-shot "review ×3" with a bounded loop that produces an auditable verdict. The user reads the gate file instead of the diff.

**Inputs**:
- The diff to gate: `git diff <base>...HEAD` where `<base>` is the repo's default branch (`main`, or `master` if `main` does not exist), unless the caller designates another diff.
- The validated plan / acceptance criteria, when the caller has one.
- `.agents/verification.yaml` — if missing, run the `project-probe` skill first.
- The task level (0-4). Default: 2. The caller passes it; level 0 changes are not gated (no gate file).
- The mode: **integrated** (called by dev-workflow or ship-workflow — the loop fixes autonomously) or **standalone** (invoked via /gate or directly by the user — report first, the user arbitrates every fix; see step 4).

**Output**: `docs/quality/GATE-<YYYY-MM-DD>-<slug>.yaml` (slug = branch name or story slug, kebab-case) + a short summary to the caller.

## Loop bounds by level

| Level | Max rounds | Review lenses |
|---|---|---|
| 1 | 1 | one generalist reviewer |
| 2 | 3 | correctness+security · readability · performance |
| 3-4 | 4 | level-2 lenses + `design-audit` / `seo-geo-audit` / `a11y-enforcer` for the surfaces the caller detected |

## One round

1. **EXECUTION EVIDENCE — always first, never skipped.**
   Run every command in the manifest's `commands`. If the harness provides the `verify` skill, drive the app's real affected flow (not just tests); otherwise use the manifest's `testability.runtime_verify` command to launch the app and drive the affected flow yourself. Any red → fix immediately → restart the round. A restart consumes a round from the cap; if execution evidence cannot be made green within the cap, the verdict is `FAIL`. (At level 1 the single-round exception below still applies: fixing and re-running green within that round is allowed and does not consume a second round.) Record each command and its actual result; a claim without the executed command's output is worthless.
   If the diff touches only docs/config with no runtime surface, still run the manifest commands and note the limitation in `absents` — never skip silently.

2. **MULTI-LENS REVIEWS — fresh contexts.**
   Each lens reviews the diff + plan only (no session history). Findings are classified P0 (must fix) / P1 (should fix) / P2-P3 (note).
   **Runtime capabilities:**
   - *Claude Code*: use the native `/code-review` skill as the primary correctness lens (its CONFIRMED/PLAUSIBLE verdicts feed step 3 directly — CONFIRMED skips re-verification). Dispatch the remaining lenses as parallel subagents.
   - *Sequential runtimes (Codex CLI)*: run the lenses one at a time in distinct passes, with an explicit mental reset between lenses.

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

## Gate file format

```yaml
# docs/quality/GATE-2026-07-05-auth-refresh.yaml
verdict: PASS                # PASS | CONCERNS | FAIL | WAIVED
niveau: 2
tours: 3
diff_hash: "<sha256 of the gated diff>"   # freshness: consumers recompute and compare
preuve:
  executable:                # the only possible basis for a PASS
    lint:   { cmd: "npm run lint", statut: vert }
    types:  { cmd: "tsc --noEmit", statut: vert }
    tests:  { cmd: "npm test", statut: "vert (47 passed)" }
    verify: { flow: "login -> refresh -> logout", statut: vert }
  opinion:
    findings: { total: 9, confirmes: 4, refutes: 5, corriges: 4, restants: 0 }
decisions_prises_en_ton_nom:
  - "refresh token stored in httpOnly cookie instead of localStorage as the issue suggested — XSS"
absents:
  - "no e2e harness"
```

Compute `diff_hash` by hashing the gated diff excluding gate files themselves: `git diff <base>...HEAD -- ':(exclude)docs/quality' ':(exclude)CHANGELOG.md' | (shasum -a 256 2>/dev/null || sha256sum) | cut -d' ' -f1` — so neither committing the gate file nor the ship workflow's CHANGELOG entry invalidates the hash. Consumers recompute with the same exclusion.

`decisions_prises_en_ton_nom` lists every autonomous deviation from the validated plan. **For levels 3-4 the calling workflow must show this section to the user before proposing ship** — it is the only careful read left to the human.

## Anti-patterns

- Claiming a command is green without showing its executed output.
- Re-verifying or re-counting registry findings (the loop never converges).
- Skipping execution evidence because "only docs changed".
- Fixing P2/P3 style findings during the loop (scope creep — note them instead).
- Looping past the cap, or emitting PASS on opinion alone.
- Modifying any file in standalone mode before the user has arbitrated the report.
