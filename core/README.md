# Provider-neutral core

`core/catalog.yaml` is the build graph and the source-of-truth registry for migrated artifacts.
Files below `core/skills/` and `core/commands/` contain provider-neutral workflow content. Provider
syntax, manifests, aliases and format transforms live below `providers/` and `tooling/build/`.

## Editing rules

1. Edit a canonical workflow in `core/`, not in `dist/`.
2. Declare every supporting file in the artifact's `resources` list. A skill must be deployable
   from its own generated directory without reaching into `.claude/knowledge` or a user home.
3. Use semantic skill references such as `skill:project-probe`; do not embed provider storage paths
   in canonical content.
4. Run the compiler and reviewed golden checks after catalog changes.
5. Keep the transitional `.claude` mirrors until the P0 runtime route has C3 behavioral evidence.
   Structural equality alone does not authorize their removal.

The compiler copies Markdown unchanged except for a transform explicitly declared by a provider
contract. The current non-copy transform is Gemini command Markdown to TOML.
