---
description: Rétrospective engineering — analyse commits, sessions de travail, métriques, streaks, et tendances. Usage: /retro [7d|14d|30d|24h] [compare]
---

# /retro — Engineering Retrospective

Generates a comprehensive engineering retrospective analyzing commit history, work patterns, and code quality metrics. Team-aware: identifies contributors with per-person praise and growth opportunities.

This command is observational and read-only. It may propose changes for human review, but it must not mutate workflow files, planning documents, retrospectives, Git state, or project configuration.

## Arguments
- `/retro` — default: last 7 days
- `/retro 24h` — last 24 hours
- `/retro 14d` — last 14 days
- `/retro 30d` — last 30 days
- `/retro compare` — compare current window vs prior same-length window

**Argument validation:** If the argument doesn't match a number followed by `d`, `h`, or `w`, or the word `compare`, show usage and stop.

---

## Step 1: Gather Raw Data

Use the locally available `origin/main` ref and identify the current user. Do not fetch or mutate refs; report the ref timestamp so the human can judge freshness:
```bash
git config user.name
git config user.email
git log -1 --format="%H|%ai" origin/main
```

The name returned by `git config user.name` is **"you"** — the person reading this retro.

Run ALL of these git commands in parallel (they are independent):

```bash
# 1. All commits with timestamps, subject, hash, author, stats
git log origin/main --since="<window>" --format="%H|%aN|%ae|%ai|%s" --shortstat

# 2. Per-commit test vs total LOC breakdown
git log origin/main --since="<window>" --format="COMMIT:%H|%aN" --numstat

# 3. Commit timestamps for session detection
git log origin/main --since="<window>" --format="%at|%aN|%ai|%s" | sort -n

# 4. Files most frequently changed (hotspot analysis)
git log origin/main --since="<window>" --format="" --name-only | grep -v '^$' | sort | uniq -c | sort -rn

# 5. PR numbers from commit messages
git log origin/main --since="<window>" --format="%s" | grep -oE '#[0-9]+' | sort -n | uniq

# 6. Per-author commit counts
git shortlog origin/main --since="<window>" -sn --no-merges
```

---

## Step 2: Compute Metrics

| Metric | Value |
|--------|-------|
| Commits to main | N |
| Contributors | N |
| PRs merged | N |
| Total insertions | N |
| Total deletions | N |
| Net LOC added | N |
| Test LOC ratio | N% |
| Active days | N |
| Sessions detected | N |

**Per-author leaderboard:**
```
Contributor         Commits   +/-          Top area
You (name)               32   +2400/-300   src/
alice                    12   +800/-150    tests/
```

---

## Step 3: Commit Time Distribution

Show hourly histogram using bar chart:
```
Hour  Commits  ████████████████
 09:    5      █████
 22:    8      ████████
```

Identify: peak hours, dead zones, late-night clusters (after 10pm).

---

## Step 4: Work Session Detection

Detect sessions using **45-minute gap** threshold between consecutive commits.

Classify:
- **Deep sessions** (50+ min)
- **Medium sessions** (20-50 min)
- **Micro sessions** (<20 min)

Calculate: total active coding time, average session length, LOC per active hour.

---

## Step 5: Commit Type Breakdown

Categorize by conventional commit prefix (feat/fix/refactor/test/chore/docs). Show as percentage bar:
```
feat:     20  (40%)  ████████████████████
fix:      27  (54%)  ███████████████████████████
```

Flag if fix ratio exceeds 50% — signals "ship fast, fix fast" pattern.

---

## Step 6: Hotspot Analysis

Top 10 most-changed files. Flag:
- Files changed 5+ times (churn hotspots)
- Test files vs production files in hotspot list

---

## Step 7: PR Size Distribution

Bucket PRs by size:
- **Small** (<100 LOC)
- **Medium** (100-500 LOC)
- **Large** (500-1500 LOC)
- **XL** (1500+ LOC) — flag these

---

## Step 8: Focus Score + Ship of the Week

**Focus score:** % of commits touching the most-changed directory. Higher = deeper work.

**Ship of the week:** Highest-LOC PR — highlight PR number, title, LOC, why it matters.

---

## Step 9: Per-Contributor Analysis

For each contributor:
1. Commits and LOC
2. Top 3 areas of focus
3. Commit type mix (feat/fix/refactor)
4. Session patterns and peak hours
5. Test discipline (test LOC ratio)
6. Biggest ship

**For "You":** Deepest treatment — sessions, patterns, focus.

**For teammates:**
- **Praise** (1-2 specific, anchored in commits)
- **Opportunity for growth** (1 specific, constructive)

**AI collab:** Track `Co-Authored-By` AI trailers as a neutral metric.

---

## Step 10: Streak Tracking

```bash
# Count consecutive days with commits to origin/main
git log origin/main --format="%ad" --date=format:"%Y-%m-%d" | sort -u
```

Count backward from today.

---

## Step 11: Load History & Compare

```bash
ls -t .context/retros/*.json 2>/dev/null
```

If prior retros exist, load most recent. Show deltas:
```
                    Last        Now         Delta
Test ratio:         22%    →    41%         ↑19pp
Sessions:           10     →    14          ↑4
```

If first retro, skip comparison.

---

## Step 12: Rework Lens

Answer these four stable questions using only evidence gathered in this retro. Clearly label an answer `Insufficient evidence` instead of inventing causality.

1. **Quel délai ou détour aurait pu être évité ?**
2. **Quel rework a été provoqué par une hypothèse ou une preuve insuffisante ?**
3. **Quel contexte manquait au moment de décider ?**
4. **Quelle étape doit être supprimée, simplifiée ou automatisée la prochaine fois ?**

Each answer is an observation proposed to the human. It may include an evidence-backed suggestion, but it must never update a skill, command, process, plan, or configuration automatically.

---

## Step 13: Write the Narrative

Structure:

1. **Tweetable summary** (first line):
   `Week of Mar 1: 47 commits (3 contributors), 3.2k LOC, 38% tests, 12 PRs | Streak: 47d`

2. Summary Table (Step 2)
3. Trends vs Last Retro (Step 11)
4. Time & Session Patterns (Steps 3-4)
5. Shipping Velocity (Steps 5-7)
6. Code Quality Signals
7. Focus & Highlights (Step 8)
8. Your Week (personal deep-dive)
9. Team Breakdown (per teammate)
10. Top 3 Team Wins
11. 3 Things to Improve
12. Rework Lens (the four stable questions from Step 12)
13. 3 Habits for Next Week

---

## Compare Mode

When user runs `/retro compare`:
1. Compute metrics for current window
2. Compute metrics for prior same-length window
3. Show side-by-side comparison with deltas
4. Write narrative highlighting improvements and regressions

---

## Tone
- Encouraging but candid
- Specific and concrete — anchor in actual commits
- Skip generic praise — say what was good and why
- ~3000-4500 words output
- ALL output to conversation; do not save or mutate any project file

---

## Démarrage

**Arguments reçus :** $ARGUMENTS

Je collecte les données git pour la rétrospective...
