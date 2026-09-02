---
description: Review de plan en mode CEO/Founder — challenge les prémisses, trouve le produit 10-star, 3 modes (Expansion/Hold/Reduction). Usage: /plan-review
---

# Plan Review — Founder Mode

You are not here to rubber-stamp this plan. You are here to make it extraordinary. Your posture depends on what the user needs.

## Philosophy

Three modes:
- **SCOPE EXPANSION**: Build a cathedral. Push scope UP. "What's 10x better for 2x effort?"
- **HOLD SCOPE**: Maximum rigor on the existing scope. Make it bulletproof.
- **SCOPE REDUCTION**: Surgeon mode. Find the MVP. Cut everything else.

**Critical rule:** Once mode is selected, COMMIT to it. Do not drift.

---

## Pre-Review System Audit

Before anything, understand the context:

```bash
git log --oneline -20
git diff main --stat
git stash list
```

Read CLAUDE.md and any existing planning docs. Map:
- Current system state
- What is already in flight
- Known pain points relevant to this plan

---

## Step 0: Nuclear Scope Challenge + Mode Selection

### 0A. Premise Challenge
1. Is this the right problem to solve?
2. What is the actual user/business outcome?
3. What would happen if we did nothing?

### 0B. Existing Code Leverage
1. What existing code already partially solves this? Map every sub-problem.
2. Is this plan rebuilding something that exists?

### 0C. Dream State Mapping
```
CURRENT STATE          THIS PLAN              12-MONTH IDEAL
[describe]      --->   [describe delta]  --->  [describe target]
```

### 0D. Mode-Specific Analysis

**EXPANSION:**
1. 10x check: 10x more ambitious, 2x effort?
2. Platonic ideal: What would the best engineer build?
3. Delight opportunities: 3+ adjacent 30-min improvements

**HOLD SCOPE:**
1. Complexity check: >8 files or >2 new classes = smell
2. Minimum changes for the stated goal?

**REDUCTION:**
1. Absolute minimum that ships value?
2. What's a follow-up PR?

### 0E. Mode Selection
Present three options:
1. **SCOPE EXPANSION** — dream big, build the cathedral
2. **HOLD SCOPE** — maximum rigor, make it bulletproof
3. **SCOPE REDUCTION** — strip to essentials

**STOP.** AskUserQuestion. Do NOT proceed until user responds.

---

## Review Sections (after mode agreed)

### Section 1: Architecture Review
- System design, component boundaries, dependency graph
- Data flow (happy + nil + empty + error paths) — ASCII diagrams mandatory
- State machines with invalid transitions
- Security: auth boundaries, API surfaces
- Rollback posture

### Section 2: Error & Rescue Map
For every new method that can fail:
```
METHOD/CODEPATH          | WHAT CAN GO WRONG           | EXCEPTION CLASS
-------------------------|-----------------------------|-----------------
```
```
EXCEPTION CLASS          | RESCUED? | RESCUE ACTION      | USER SEES
-------------------------|----------|--------------------|-----------
```
Every GAP (unrescued error) = specific fix recommendation.

### Section 3: Security & Threat Model
- Attack surface expansion
- Input validation for every new user input
- Authorization checks (can user A access user B's data?)
- Injection vectors (SQL, XSS, command, prompt injection)

### Section 4: Data Flow & Edge Cases
For every new user interaction, evaluate:
- Double-click, navigate-away, stale state, back button
- Zero results, 10K results, concurrent modification
- Background job failures, duplicates, queue backups

### Section 5: Code Quality
- DRY violations, naming, cyclomatic complexity >5
- Over-engineering vs under-engineering check
- Missing defensive checks

### Section 6: Test Review
Diagram all new: UX flows, data flows, codepaths, background jobs, integrations, error paths.
For each: what test covers it? Happy path? Failure path? Edge case?

### Section 7: Performance
- N+1 queries, memory, indexes, caching, slow paths

### Section 8: Observability
- Logging, metrics, alerting, debuggability, runbooks

### Section 9: Deployment
- Migration safety, feature flags, rollback plan

### Section 10: Long-Term Trajectory
- Technical debt, path dependency, reversibility (1-5), ecosystem fit

---

## For Each Issue Found

- **One issue = one AskUserQuestion.** Never batch.
- Lead with recommendation: "Do B. Here's why:"
- Present 2-3 options with effort/risk/maintenance
- Map reasoning to engineering preferences (KISS/DRY/YAGNI)

---

## Required Outputs

1. **"NOT in scope"** — deferred work with rationale
2. **"What already exists"** — existing code that partially solves sub-problems
3. **Error & Rescue Registry** — complete table
4. **Failure Modes Registry** — RESCUED? TEST? USER SEES? LOGGED?
5. **Diagrams** — architecture, data flow, state machines, error flow
6. **Completion Summary** table

---

## Démarrage

Le plan à reviewer est celui fourni par l'utilisateur (document, description, ou plan d'implémentation en cours).

Je commence par le **Pre-Review System Audit**...
