---
name: quick-fix-workflow
description: Quick fix workflow for small bugs, typos, and minor corrections without the full /dev ceremony. Loaded by /quick-fix slash command in both Claude Code and Codex CLI. Use when the problem is small enough (≤ 3 files, ≤ 50 lines changed, no new dependency), otherwise escalate to /dev.
---

# Quick Fix Workflow

This skill describes the minimal overhead fix workflow executed by `/quick-fix`. It skips the multi-phase ceremony of `/dev` because the change is supposed to be small and obvious.

**Input**: a short problem description passed as arguments after `/quick-fix` (e.g. `/quick-fix "the login button is misaligned"`).

**Output**: a committed fix, verified by lint + types + tests.

---

## When to use this workflow

Use `/quick-fix` for:
- ✅ Typos and text errors
- ✅ Small obvious bugs
- ✅ Minor UI/style adjustments
- ✅ Lint or type errors
- ✅ Off-by-one, wrong constant, swapped arguments

Do NOT use `/quick-fix` for:
- ❌ New features → use `/dev`
- ❌ Important refactoring → use `/refactor`
- ❌ Architectural changes → use `/dev`
- ❌ Anything requiring a new dependency → use `/dev`
- ❌ Anything that touches more than 3 files → use `/dev`
- ❌ Anything > 50 lines changed → use `/dev`

If at any point the fix grows beyond the limits above, **STOP** and tell the user to restart with `/dev`.

---

## Step 1 — Context sniff (≤ 30 seconds)

Gather only what's needed to locate the problem:

```bash
git status --short                        # What's already changed
git diff --name-only HEAD~3..HEAD          # Recently touched files
```

Optional (only if lint errors mentioned):
```bash
npm run lint 2>&1 | head -20
npm run typecheck 2>&1 | head -20
```

---

## Step 2 — Locate & understand

1. Read the target file(s). Don't skim — understand the function.
2. Identify the exact location of the bug.
3. Confirm that the fix is within the quick-fix limits (≤ 3 files, ≤ 50 lines, no new dependency).
4. If the fix exceeds the limits, STOP and escalate to `/dev`.

---

## Step 3 — Fix

Apply the minimal change. Respect the project's conventions (CLAUDE.md / AGENTS.md). No "while I'm here" refactoring — fix the bug, nothing else.

---

## Step 4 — Verify

Run the verification chain:

```bash
npm run lint && npm run typecheck && npm test
```

(adapt to the project's actual commands — check `package.json` scripts or Makefile)

- **All green**: proceed to Step 5.
- **Anything red**: fix the regression immediately. If it spirals, STOP and escalate to `/dev`.

---

## Step 5 — Output

Present the result in this format:

```markdown
## Quick Fix: <short description>

### Problem
<what was broken>

### Solution
<what was changed>

### Files modified
- `path/to/file.ts` — <reason>

### Verification
- Lint: ✅/❌
- Types: ✅/❌
- Tests: ✅/❌

### Suggested commit
fix(scope): <short description>
```

Do NOT auto-commit. The user should review and commit themselves (or run `/ship` if they want the full release workflow).

---

## Anti-patterns

- ❌ Using `/quick-fix` for a new feature "because it's simple"
- ❌ Expanding scope mid-fix ("while I'm here, let me clean up...")
- ❌ Skipping the lint/types/tests verification
- ❌ Auto-committing without presenting the change to the user
- ❌ Continuing past the 3-file / 50-line limit instead of escalating
