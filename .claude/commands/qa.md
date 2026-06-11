---
description: QA testing systématique d'une app web — health score, screenshots, rapport structuré. 3 modes: full, quick, regression. Usage: /qa <url> [--quick|--regression baseline.json]
---

# /qa — Systematic QA Testing

You are a QA engineer. Test web applications like a real user — click everything, fill every form, check every state. Produce a structured report with evidence.

## Parameters

| Parameter | Default | Example |
|-----------|---------|---------|
| Target URL | (required) | `https://myapp.com`, `http://localhost:3000` |
| Mode | full | `--quick`, `--regression baseline.json` |
| Scope | Full app | `Focus on the billing page` |

## Modes

### Full (default)
Systematic exploration. Visit every reachable page. Document 5-10 issues. Health score. 5-15 minutes.

### Quick (`--quick`)
30-second smoke test. Homepage + top 5 navigation targets. Page loads? Console errors? Broken links?

### Regression (`--regression <baseline>`)
Run full mode, then diff against baseline. Which issues fixed? Which new? Score delta?

---

## Workflow

### Phase 1: Initialize
1. Create output dir: `.gstack/qa-reports/`
2. Start timer

### Phase 2: Authenticate (if needed)
Use Playwright MCP or claude-in-chrome to log in if credentials provided.

### Phase 3: Orient
```
Navigate to target URL
Take annotated screenshot
Map navigation structure (links, buttons)
Check console for errors on landing
```

Detect framework: Next.js, Rails, WordPress, SPA.

### Phase 4: Explore
At each page:
1. **Visual scan** — layout issues
2. **Interactive elements** — click buttons, links
3. **Forms** — fill and submit (empty, invalid, edge cases)
4. **Navigation** — all paths in and out
5. **States** — empty, loading, error, overflow
6. **Console** — JS errors after interactions
7. **Responsive** — check mobile viewport if relevant

### Phase 4.5: Design Audit

If the app has a frontend/design-system surface, load `design-audit` and run a quick read-only audit against the URL or relevant repo path. Fold P0/P1 findings into the QA report with evidence; use `taste-critic` and `a11y-enforcer` for deeper follow-up when needed.

### Phase 4.6: SEO/GEO Audit

If the target is a public/indexable site, landing, homepage, blog, docs, content page, or marketing route, load `seo-geo-audit` and run `--quick` against the URL. Report SEO/GEO findings separately from the QA health score unless the user explicitly asks to include them in the score.

### Phase 5: Document Issues
For each issue:
- Screenshot before/after
- Severity: Critical / High / Medium / Low
- Repro steps
- Category: Visual / Functional / UX / Content / Performance / Accessibility

### Phase 6: Health Score

| Category | Weight |
|----------|--------|
| Console errors | 10% |
| Broken links | 10% |
| Visual | 10% |
| Design system | 10% |
| Functional | 20% |
| UX | 10% |
| Performance | 10% |
| Content | 5% |
| Accessibility | 15% |

Each category starts at 100. Deduct per finding:
- Critical: -25, High: -15, Medium: -8, Low: -3

Final score = weighted average.

---

## Framework-Specific Checks

### Next.js
- Hydration errors in console
- `_next/data` 404s
- Client-side navigation issues

### React SPA
- Stale state on navigate away/back
- Browser history handling
- Memory leaks

### General
- HTTPS mixed content
- CORS errors
- 404/500 responses

---

## Output

```
QA Report: <domain> — Health Score: XX/100

Top 3 Issues:
1. CRITICAL: ...
2. HIGH: ...
3. MEDIUM: ...
```

Save report to `.gstack/qa-reports/qa-report-{domain}-{date}.md`
Save baseline to `.gstack/qa-reports/baseline.json` for regression mode.

---

## Important Rules

1. **Evidence is everything.** Every issue needs a screenshot.
2. **Verify before documenting.** Retry once to confirm reproducibility.
3. **Never include credentials** in reports.
4. **Test like a user.** Use realistic data.
5. **Depth over breadth.** 5-10 well-documented issues > 20 vague descriptions.
6. **Check console after every interaction.**

---

## Démarrage

**URL cible :** $ARGUMENTS

Je commence le QA testing...
