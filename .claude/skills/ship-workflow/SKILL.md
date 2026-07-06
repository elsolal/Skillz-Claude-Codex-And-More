---
name: ship-workflow
description: Automated ship workflow that takes a feature branch from "done" to "PR opened" in a single non-interactive pass. Loaded by /ship slash command in both Claude Code and Codex CLI. Use when the user has finished implementing a feature and wants to merge main, manifest verification, quality-gate consumption (PASS required or explicit waiver), CHANGELOG, commit, push, and create a PR in one go.
---

# Ship Workflow — Release Engineer Mode

This skill describes the automated release pipeline executed by the `/ship` command. The key property is **non-interactivity**: when the user invokes `/ship`, the next thing they should see is the PR URL. No confirmation prompts except for genuine blockers.

**Input**: current branch state (assumes a feature branch with committed or stageable work).

**Output**: a GitHub PR URL.

---

## Core Principles

1. **Non-interactive by default** — the user said `/ship`, which means DO IT. Don't ask for confirmation on version bumps, commit messages, or CHANGELOG content.
2. **Only stop for real blockers** — merge conflicts that can't auto-resolve, test failures, critical review findings, frontend design-audit P0/P1, public-page seo-geo-audit P0/P1.
3. **Never force-push** — regular `git push` only. Never `--force`.
4. **Never skip hooks** — no `--no-verify`, no `--no-gpg-sign` unless explicitly requested.
5. **Bisectable commits** — each commit should be independently valid (no broken imports between commits).

---

## Step 1 — Pre-flight

1. Check current branch: `git branch --show-current`.
2. **If on `main` or `master`**: abort with message "You're on main. Ship from a feature branch."
3. Run `git status` (never use `-uall`). Note uncommitted changes.
4. Run `git diff main...HEAD --stat` and `git log main..HEAD --oneline` to understand what's being shipped.

---

## Step 2 — Merge origin/main

Fetch and merge `origin/main` into the feature branch, so tests run against the merged state:

```bash
git fetch origin main && git merge origin/main --no-edit
```

- **If merge conflicts**: try to auto-resolve if they're trivial (e.g. formatting-only). If not, **STOP** and show the conflicts.
- **If already up to date**: continue silently.

---

## Step 3 — Execution evidence (manifest)

Run the `project-probe` skill (read `.agents/verification.yaml`, create if absent), then run every command in the manifest's `commands` (lint, typecheck, test, build), capturing output for possible debugging.

- **If anything is red**: display the failures and **STOP**.
- **If green**: note the counts briefly and continue. Entries absent from the manifest are reported as absent — never guessed, never faked.

---

## Step 4 — Quality gate consumption

Quality is proven by the gate file, not by a fresh review. One definition of quality in the whole system: the `quality-gate` skill.

1. Find the most recent `docs/quality/GATE-*.yaml` committed on this branch.
2. Check **freshness**: recompute the diff hash with the gate's exclusion rule —
   `git diff <base>...HEAD -- ':(exclude)docs/quality' | (shasum -a 256 2>/dev/null || sha256sum) | cut -d' ' -f1`
   (`<base>` = `main`, or `master` if `main` does not exist) and compare with the gate's `diff_hash`.
3. Decide:
   - **Gate PASS and fresh** → proceed. The gate file content goes into the PR body verbatim.
   - **Gate absent, stale, FAIL, or CONCERNS** → run the `quality-gate` skill now (level from the gate file if present, else 2; the run includes design/SEO/a11y lenses when the diff touches those surfaces — they live inside the gate, not as separate ship passes). Then:
     - New verdict **PASS** → commit the new gate file and proceed.
     - **CONCERNS** → non-interactive rule exception: present the gate summary and ask the user once — accept explicitly (verdict becomes `WAIVED` with the reason recorded in the gate file) or abort. Never auto-accept.
     - **FAIL** → **STOP** and show the confirmed findings.
4. If the gate's `decisions_prises_en_ton_nom` is non-empty and the gate level is 3-4, quote it in the PR body under its own heading — it is the reviewer-facing record of autonomous decisions.

---

## Step 5 — CHANGELOG

1. Check if `CHANGELOG.md` exists. If not, create it with a header.
2. Auto-generate the new entry from ALL commits on the branch (don't ask the user for content):
   - Use `git log main..HEAD --oneline` for the commit list
   - Use `git diff main...HEAD` for the full diff
   - Categorize into `### Added`, `### Changed`, `### Fixed`, `### Removed`
   - Insert after the file header, dated today
   - Format: `## [Unreleased] - YYYY-MM-DD` or next semantic version if the project uses SemVer

---

## Step 6 — Commit (bisectable chunks)

**Goal**: small, logical, bisectable commits.

1. Group changes into logical commits. Each commit = one coherent change.
2. **Commit ordering**:
   - Infrastructure first (migrations, config, routes)
   - Models/services (with their tests in the same commit)
   - Controllers/views/components (with their tests)
   - CHANGELOG as the final commit
3. Each commit must be independently valid — no broken imports between commits.
4. Commit message format:
   ```
   type(scope): summary

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
5. **Small diff exception**: if the total diff is small (< 50 lines across < 4 files), a single commit is fine.

---

## Step 7 — Push

```bash
git push -u origin $(git branch --show-current)
```

Never force-push. If the remote is ahead (unusual), **STOP** and show the situation.

---

## Step 8 — Create PR

```bash
gh pr create --title "type(scope): summary" --body "$(cat <<'EOF'
## Summary
<bullet points from CHANGELOG>

## Quality Gate
<the gate file content (yaml), verbatim>
<if levels 3-4: the decisions_prises_en_ton_nom section quoted>

## Test plan
- [x] All tests pass
- [ ] <any manual checks>
EOF
)"
```

**Output the PR URL** as the final line. This is the only output the user should need.

---

## Important rules

- **Never skip tests**. If tests fail, stop immediately.
- **Never force-push**. Regular `git push` only.
- **Never ask for confirmation** except for merge conflicts and an explicit CONCERNS waiver decision.
- **The goal**: the user says `/ship`, the next thing they see is the PR URL.
