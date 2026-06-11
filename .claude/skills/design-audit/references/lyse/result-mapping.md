# Lyse Result Mapping

Use this mapping to translate Lyse evidence into a Skillz-Claude `Design Audit Report`.

## Score tiers

| Lyse score | Lyse reading | Skillz default verdict |
|---:|---|---|
| 90-100 | Excellent structural discipline | Ship-ready unless qualitative/a11y/Figma findings disagree |
| 75-89 | Healthy | Ship-ready or minor P2 polish |
| 60-74 | Fair | Ship if no P0/P1 and trend is acceptable |
| 40-59 | At risk | Needs design loop; P1 likely |
| 0-39 | Critical | Fix P0/P1 first |

Do not use the score alone. A score of 82 with one AI-governance `error` can still block ship; a score of 45 on a non-DS prototype may be informative but not blocking.

## Axis mapping

| Lyse axis | Skillz axis |
|---|---|
| `tokens` | Tokens |
| `components` | Components |
| `a11y` | A11y |
| `stories` | Components or DS documentation |
| `ai-surface` | AI surface & governance |
| `ai-governance` | AI surface & governance |

Skillz-only axes:

- Taste: hierarchy, density, typography, motion, polish, responsive behavior.
- Figma/code drift: variant, token and state mismatch between design and implementation.

## Severity mapping

| Lyse severity | Default Skillz severity |
|---|---|
| `error` | P1, P0 if user-visible/blocking/misleading |
| `warning` | P2, P1 in ship-gate when repeated or on critical surface |
| `info` | P3, P2 if it blocks agent-readability |
| `off` | Mention only if relevant to explain allowlists |

## Report shape

When Lyse runs, include:

```markdown
**Lyse**: 72/100, tier: Quantitative, rules: 28, findings: 14
```

Then cite top findings in the Design Audit table:

```markdown
| Sev | Axis | Where | Issue | Fix |
|---|---|---|---|---|
| P1 | Tokens | app/page.tsx:42 | Lyse `tokens/no-hardcoded-color` found raw color usage | Replace with semantic token |
```

## Conflict handling

- If Lyse says pass but screenshot/runtime looks poor, trust the combined audit and mark the gap as Taste/Figma/runtime.
- If Lyse cannot parse files but manual review finds token/component issues, report both `Lyse: failed/skipped` and manual findings.
- If Lyse reports many low-value findings in generated or vendored files, recommend `.lyse.yaml` exclusions instead of treating the repo as unhealthy.
