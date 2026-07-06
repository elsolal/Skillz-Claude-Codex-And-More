# Review Checklist

## Instructions

Review the `git diff origin/main` output for the issues listed below. Be specific — cite `file:line` and suggest fixes. Skip anything that's fine. Only flag real problems.

**Two-pass review:**
- **Pass 1 (CRITICAL):** Run these first. These can block `/ship`.
- **Pass 2 (INFORMATIONAL):** Included in the PR body but do not block.

**Output format:**

```
Review: N issues (X critical, Y informational)

**CRITICAL** (blocking /ship):
- [file:line] Problem description
  Fix: suggested fix

**Issues** (non-blocking):
- [file:line] Problem description
  Fix: suggested fix
```

If no issues found: `Review: No issues found.`

Be terse. One line problem, one line fix. No preamble.

---

## Review Categories

### Pass 1 — CRITICAL

#### SQL & Data Safety
- String interpolation in SQL queries (use parameterized queries / prepared statements)
- TOCTOU races: check-then-set that should be atomic
- Bypassing ORM validations on constrained fields
- N+1 queries: missing eager loading for associations used in loops

#### Race Conditions & Concurrency
- Read-check-write without uniqueness constraint or retry
- `findOrCreate` / `upsert` on columns without unique DB index
- Status transitions without atomic WHERE + UPDATE
- `dangerouslySetInnerHTML` / `html_safe` / `v-html` on user-controlled data (XSS)

#### Trust Boundaries
- LLM-generated values written to DB without format validation
- User input passed to shell commands (command injection)
- Unvalidated redirects based on user input
- File paths constructed from user input (path traversal)
- Structured output (JSON from API/LLM) accepted without type/shape checks

### Pass 2 — INFORMATIONAL

#### Conditional Side Effects
- Code paths that branch but forget a side effect on one branch
- Log messages claiming an action happened but the action was conditionally skipped

#### Magic Numbers & String Coupling
- Bare numeric literals in multiple files — should be named constants
- Error message strings used as query filters elsewhere

#### Dead Code & Consistency
- Variables assigned but never read
- Comments/docstrings describing old behavior after code changed
- Stale TODO/FIXME comments about work already done

#### Test Gaps
- Negative-path tests that assert type but not side effects
- Security features (auth, rate limiting) without integration tests
- Missing assertions on error messages or status codes

#### Performance
- O(n²) nested loops on potentially large datasets
- Missing database indexes on frequently queried columns
- Synchronous operations that could be async
- Large objects loaded into memory when streaming is possible

#### Frontend / View
- Inline styles in components (use CSS modules or tailwind)
- O(n*m) lookups in render loops (use maps/indexes)
- Missing loading/error states in async UI
- Missing alt text on images
- Missing keyboard navigation on interactive elements

---

## Gate Classification

```
CRITICAL (blocks /ship):          INFORMATIONAL (in PR body):
├─ SQL & Data Safety              ├─ Conditional Side Effects
├─ Race Conditions & Concurrency  ├─ Magic Numbers & String Coupling
└─ Trust Boundaries               ├─ Dead Code & Consistency
                                  ├─ Test Gaps
                                  ├─ Performance
                                  └─ Frontend / View
```

---

## Suppressions — DO NOT flag these

- Redundancy that aids readability (e.g., `!= null` when type already guarantees it)
- "Add a comment explaining why" — thresholds change, comments rot
- Consistency-only changes (wrapping to match nearby code style)
- "This assertion could be tighter" when it already covers the behavior
- Anything already addressed in the diff you're reviewing — read the FULL diff first
- Test threshold changes or configuration values
- Harmless no-ops
