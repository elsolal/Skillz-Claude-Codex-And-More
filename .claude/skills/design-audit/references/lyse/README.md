# Lyse Integration Reference

Source inspected: `https://github.com/lyse-labs/lyse` on 2026-06-09.

Lyse is an external design-system health tool published as `@lyse-labs/lyse`. It audits frontend repositories with deterministic static rules and returns a Health Score from 0 to 100.

## Packaging decision

- Do not vendor Lyse source code into Skillz-Claude.
- Do not copy Lyse rule implementation files, codemods, tests or package internals.
- Keep Lyse as an optional external CLI/MCP signal.
- Store only Skillz-Claude-owned integration notes, rule inventory, command usage and result mapping in this skill.

Reason: Lyse is published under `AGPL-3.0-only` / commercial licensing. Skillz-Claude can call the CLI as an external tool, but should not silently absorb its code into this repository.

## When to load these references

Load this folder when:

- the user mentions Lyse directly;
- `/design-audit` is run with `--full` or `--ship-gate` on a frontend/design-system repository;
- a repo has `.lyse.yaml`;
- a previous Lyse JSON/SARIF/text report is provided;
- the audit concerns tokens, Storybook coverage, DS component contracts, agent-readable UI, MCP, `AGENTS.md`, `llms.txt`, or AI governance.

## Files

| File | Purpose |
|---|---|
| `cli-runtime.md` | How to safely run Lyse from a skill without mutating the repo |
| `rule-catalog.md` | Current rule IDs, axes and how each maps to design-audit findings |
| `result-mapping.md` | How to translate Lyse score/findings into Skillz-Claude verdicts |

## Runtime stance

Lyse evidence is useful but never the only verdict:

- Lyse covers static design-system structure.
- `design-audit` also checks taste, Figma/code drift, runtime UI behavior and product-specific AI UX.
- If Lyse cannot run because Node is too old, the package is unavailable, the repo is not frontend, or prompts are blocked, continue manually and report `Lyse: skipped`.
