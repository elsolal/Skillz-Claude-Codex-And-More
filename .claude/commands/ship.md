---
description: Ship workflow automatisé — merge main, tests, pre-landing review, changelog, commit, push, PR. Usage: /ship [--skip-review]
---

# Ship: Release Engineer Mode

You are running the `/ship` workflow. This is a **non-interactive, fully automated** workflow. Do NOT ask for confirmation at any step. The user said `/ship` which means DO IT. Run straight through and output the PR URL at the end.

**Only stop for:**
- On `main` branch (abort)
- Merge conflicts that can't be auto-resolved (stop, show conflicts)
- Test failures (stop, show failures)
- Pre-landing review finds CRITICAL issues and user chooses to fix
- Uncommitted changes not staged

**Never stop for:**
- Version bump choice (auto-pick PATCH for 50+ LOC, else MICRO)
- CHANGELOG content (auto-generate from diff)
- Commit message approval (auto-commit)

---

## Step 1: Pre-flight (verification-before-completion gate)

Référence : `.claude/knowledge/workflows/verification-matrix.md` (ligne `/ship`).

1. Check current branch. If on `main`, **abort**: "You're on main. Ship from a feature branch."
2. Run `git status` (never use `-uall`). Note uncommitted changes.
   - **If working tree dirty (uncommitted changes) → ABORT.** Le ship requires tree clean.
3. Run `git diff main...HEAD --stat` and `git log main..HEAD --oneline` to understand what's being shipped.
4. Verify CHANGELOG.md will be modified (Step 5 will check).

**Si une condition échoue → ABORT avec message clair.** Le ship ne progresse pas avec une matrice incomplète.

---

## Step 2: Merge origin/main

Fetch and merge `origin/main` into the feature branch so tests run against the merged state:

```bash
git fetch origin main && git merge origin/main --no-edit
```

**If merge conflicts:** Try auto-resolve if simple. If complex, **STOP** and show them.
**If already up to date:** Continue silently.

---

## Step 3: Run tests

Detect the project's test command from package.json, Makefile, or conventions:

```bash
# Auto-detect and run (examples)
npm test 2>&1 | tee /tmp/ship_tests.txt          # Node.js
pytest 2>&1 | tee /tmp/ship_tests.txt             # Python
bundle exec rspec 2>&1 | tee /tmp/ship_tests.txt  # Ruby
go test ./... 2>&1 | tee /tmp/ship_tests.txt       # Go
```

**If any test fails:** Show failures and **STOP**.
**If all pass:** Note counts briefly and continue.

---

## Step 4: Pre-Landing Review

Review the diff for structural issues that tests don't catch.

1. Read `.claude/knowledge/review-checklist.md` if it exists. If not, use the default checklist below.
2. Run `git diff origin/main` to get the full diff.
3. Apply a two-pass review:

### Pass 1 — CRITICAL (blocks /ship)
- **SQL & Data Safety**: string interpolation in SQL, TOCTOU races, bypassing validations
- **Race Conditions**: read-check-write without locks, find_or_create without unique index
- **Security**: XSS via html_safe/dangerouslySetInnerHTML, injection vectors
- **Trust Boundaries**: LLM output written to DB without validation

### Pass 2 — INFORMATIONAL (in PR body)
- Conditional side effects (branch forgets side effect)
- Magic numbers & string coupling
- Dead code & stale comments
- Test gaps (missing negative paths)
- Performance (N+1, O(n²), missing indexes)

4. **Output all findings.**
5. **If CRITICAL issues found:** For EACH critical issue, use AskUserQuestion with:
   - The problem (file:line + description)
   - Recommended fix
   - Options: A) Fix now, B) Acknowledge and ship, C) False positive — skip
   After resolving: if user chose A, apply fixes then tell user to run `/ship` again.
6. **If only informational:** Output them, continue.
7. **If no issues:** Output "Pre-Landing Review: No issues found." and continue.

---

## Step 5: CHANGELOG (auto-generate)

1. Check if `CHANGELOG.md` exists. If not, create it.
2. Auto-generate entry from ALL commits on the branch:
   - Use `git log main..HEAD --oneline` for commit list
   - Use `git diff main...HEAD` for full diff
   - Categorize into: `### Added`, `### Changed`, `### Fixed`, `### Removed`
   - Insert after file header, dated today
   - Format: `## [Unreleased] - YYYY-MM-DD`

---

## Step 6: Commit (bisectable chunks)

**Goal:** Small, logical commits that work with `git bisect`.

1. Group changes into logical commits. Each = one coherent change.
2. **Commit ordering:**
   - Infrastructure (migrations, config, routes)
   - Models/services (with tests in same commit)
   - Controllers/views/components (with tests)
   - CHANGELOG (final commit)
3. Each commit independently valid — no broken imports.
4. Commit message format:
   ```
   type(scope): summary

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```
5. If total diff is small (<50 lines across <4 files), a single commit is fine.

---

## Step 7: Push

```bash
git push -u origin $(git branch --show-current)
```

---

## Step 8: Create PR

```bash
gh pr create --title "type(scope): summary" --body "$(cat <<'EOF'
## Summary
<bullet points from CHANGELOG>

## Pre-Landing Review
<findings from Step 4, or "No issues found.">

## Test plan
- [x] All tests pass

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**Output the PR URL** — this is the final output.

---

## Important Rules

- **Never skip tests.** If tests fail, stop.
- **Never force push.** Regular `git push` only.
- **Never ask for confirmation** except for CRITICAL review findings.
- **The goal is: user says `/ship`, next thing they see is the PR URL.**
