# Core workflow migration

The first catalog migration moves the canonical workflow slice to `core/` without deleting the
legacy `.claude` surfaces. The catalog, compiler and generated report now identify these artifacts
as `canonical`:

- skills: `dev-workflow`, `discovery-workflow`, `project-probe`, `quality-gate`, `ship-workflow`,
  `status-workflow`;
- commands: `dev`, `discovery`, `quick-fix`, `ship`, `status`.

## Equivalence boundary

The legacy command bytes are preserved exactly. Canonical skill bodies differ only in their
portable references:

- `.claude/skills/<name>/SKILL.md` becomes `skill:<name>`;
- `.claude/knowledge/...` becomes a file below the skill's generated `references/` directory.

`tests/test_core_workflow_migration.py` enforces that closed difference set and verifies the four
resource copies. The reviewed distribution golden verifies the emitted skills, commands,
frontmatter, aliases, resources and manifests for all seven providers.

## Why legacy files remain

The current evidence is structural. Codex has C2 native package discovery, while the other P0
routes do not yet have a pinned C3 behavioral smoke for this canonical slice. The legacy sources
therefore remain available for rollback and current repository-local compatibility. They are not
the catalog source of truth and must not be deleted until the C3 gate is met.

No workflow behavior was intentionally changed in this migration lot. Bugs discovered later must
be fixed in a separate functional change so migration equivalence remains reviewable.
