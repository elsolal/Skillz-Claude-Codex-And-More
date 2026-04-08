---
name: status-workflow
description: Project status dashboard workflow that scans planning docs, GitHub issues, git state, and produces a concise summary of the current project state plus recommended next actions. Loaded by /status slash command in both Claude Code and Codex CLI.
---

# Status Workflow — Project Dashboard

This skill describes the read-only status workflow executed by `/status`. It gathers the project's current state across planning docs, GitHub, and git, then presents a dashboard and recommends the next action.

**Input**: none (the command is invoked without arguments).

**Output**: a dashboard table + next-step recommendation.

---

## Data sources to scan

Scan all of these in parallel (independent reads):

| Source | How | What to extract |
|---|---|---|
| Brainstorms | `Glob: docs/planning/brainstorms/*.md` | count + most recent |
| UX Design | `Glob: docs/planning/ux/*.md` | count + most recent |
| PRD | `Glob: docs/planning/prd/*.md` | count + most recent |
| UI Design | `Glob: docs/planning/ui/*.md` | count + most recent |
| Architecture | `Glob: docs/planning/architecture/*.md` | count + most recent |
| Stories | `Glob: docs/stories/*/STORY-*.md` | count per epic |
| GitHub Issues | `gh issue list --limit 20 --state all` | open/closed/in-progress breakdown |
| GitHub PRs | `gh pr list --limit 10` | open PRs |
| RALPH logs | `Glob: docs/ralph-logs/*.md` | latest session + status |
| Git state | `git status --short`, `git log --oneline -5`, `git branch --show-current` | clean/dirty, recent commits, current branch |

If any source returns empty (directory doesn't exist, no matches), mark it as "—" in the output instead of erroring.

---

## Output format

Present the state in 4 sections:

### Section 1 — Planning Checklist

```markdown
| Document | Status | File |
|---|---|---|
| Brainstorm | ✅ / ❌ / — | <path> |
| UX Design | ✅ / ❌ / ⏭️ (optional) | <path> |
| PRD | ✅ / ❌ | <path> |
| UI Design | ✅ / ❌ / ⏭️ | <path> |
| Architecture | ✅ / ❌ | <path> |
| Stories | ✅ (N stories) / ❌ | <path or count> |
```

### Section 2 — GitHub Sync

```markdown
| Metric | Value |
|---|---|
| Open issues | N |
| Closed issues (last 7 days) | N |
| Open PRs | N |
```

### Section 3 — Git State

```markdown
- Current branch: `branch-name`
- Working tree: clean / N files modified
- Last 5 commits: <brief list>
```

### Section 4 — Recommendations

Based on what's present and what's missing, suggest the next action:

- No planning docs at all → `/discovery` to start from scratch
- Brainstorm/PRD present but no stories → `/discovery` to finish planning
- Stories ready but no dev started → `/dev #<first P0 story>`
- Feature branch with work → `/ship` to open PR
- Working tree dirty on main → recommend a feature branch
- Everything clean + main up to date → "Project is idle — pick next priority"

Present as a single `Next step: <command>` line at the end.

---

## Read-only guarantee

This workflow must NEVER modify files, NEVER commit, NEVER push. It's a pure read. If the user wants changes, they run another command based on your recommendations.

---

## Anti-patterns

- ❌ Failing the whole command if one data source is missing — use "—" instead
- ❌ Running `git status -uall` (can be slow on large repos)
- ❌ Fetching every issue in paginated form — stick to `--limit 20`
- ❌ Writing to any file during `/status`
