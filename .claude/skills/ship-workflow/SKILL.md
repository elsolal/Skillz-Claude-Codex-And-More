---
name: ship-workflow
description: Automated ship workflow that takes a feature branch from "done" to "PR opened" in a single non-interactive pass. Loaded by /ship slash command in both Claude Code and Codex CLI. Use when the user has finished implementing a feature and wants to merge main, run tests, pre-landing review, CHANGELOG, commit, push, and create a PR in one go. Non-interactive by default — only stops for real blockers (merge conflicts, test failures, critical review findings).
---

# Ship Workflow — Release Engineer Mode

This skill describes the automated release pipeline executed by the `/ship` command. The key property is **non-interactivity**: when the user invokes `/ship`, the next thing they should see is the PR URL. No confirmation prompts except for genuine blockers.

**Input**: current branch state (assumes a feature branch with committed or stageable work).

**Output**: a GitHub PR URL.

---

## Core Principles

1. **Non-interactive by default** — the user said `/ship`, which means DO IT. Don't ask for confirmation on version bumps, commit messages, or CHANGELOG content.
2. **Only stop for real blockers** — merge conflicts that can't auto-resolve, test failures, critical review findings.
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

## Step 3 — Run tests

Detect the project's test command by reading `package.json`, `Makefile`, `pyproject.toml`, or common conventions:

```bash
# Detect and run the project test command:
npm test              # Node.js with package.json "scripts.test"
pytest                # Python with pyproject.toml or pytest.ini
bundle exec rspec     # Ruby
go test ./...         # Go
cargo test            # Rust
```

Capture output to `/tmp/ship_tests.txt` for possible debugging.

- **If any test fails**: display the failures and **STOP**.
- **If all pass**: note the counts briefly and continue.

---

## Step 4 — Pre-Landing Review

Do a two-pass review of the diff (`git diff origin/main`) to catch structural issues that tests don't catch.

### Pass 1 — CRITICAL (blocks `/ship`)

- **SQL & data safety**: string interpolation in SQL, TOCTOU races, bypassing model validations
- **Race conditions**: read-check-write without locks, find_or_create without unique index
- **Security**: XSS via unsafe HTML insertion (e.g. React `dangerously*` props, Rails `html_safe`), injection vectors, secret leakage in logs
- **Trust boundaries**: LLM or user output written to DB without validation or sanitization
- **Credentials**: hardcoded secrets, API keys, tokens in the diff

### Pass 2 — INFORMATIONAL (goes in PR body)

- Conditional side effects (one branch forgets a side effect)
- Magic numbers, string coupling
- Dead code, stale comments
- Test gaps (missing negative paths)
- Performance (N+1 queries, O(n²) hot loops, missing indexes)

**Output all findings.**

- **If CRITICAL issues found**: for each one, ask the user with options:
  - (A) Fix now → apply the fix
  - (B) Acknowledge and ship → note in PR body
  - (C) False positive → skip
- **If only informational**: note them in the PR body and continue automatically.
- **If no issues**: output "Pre-Landing Review: No issues found." and continue.

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

## Pre-Landing Review
<findings from Step 4, or "No issues found.">

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
- **Never ask for confirmation** except for CRITICAL review findings or merge conflicts.
- **The goal**: the user says `/ship`, the next thing they see is the PR URL.
