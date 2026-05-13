---
name: wiki-bootstrap
description: Smart end-to-end setup of the Obsidian LLM Wiki vault — detects an existing vault, creates one if missing, patches ~/.claude/CLAUDE.md, verifies the qmd CLI, and runs a health check. Usage /wiki-bootstrap [--vault PATH] [--verify] [--with-qmd | --no-qmd]
---

# /wiki-bootstrap

One-shot smart setup for the Obsidian LLM Wiki used by the `llm-wiki` skill and the `wiki-*` commands. Wraps `scripts/setup-wiki.sh` from your Skillz-Claude install — read the script for full behavior.

Use this when:

- Setting up the wiki for the first time on a new machine.
- Adding it to a project where it has not been wired yet.
- Re-verifying that the vault, the `~/.claude/CLAUDE.md` block, and the `qmd` index are all in sync.

For day-to-day work prefer the more focused commands:

- `/wiki-init` — bootstrap a *brand new* vault from scratch (raw structure only, no CLAUDE.md patching, no qmd integration).
- `/wiki-ingest` — add a source.
- `/wiki-query` — read.
- `/wiki-lint` — health check.

## What it does

1. **Detects existing vault** by reading `~/.claude/CLAUDE.md` for a `Vault memoire :` line. Reuses it if found.
2. **Creates the vault** at the chosen path (default `~/Documents/Obsidian-<git-user>/Wiki`) if missing, using `init_vault.py` from the `llm-wiki` skill.
3. **Patches `~/.claude/CLAUDE.md`** with an idempotent `<!-- BEGIN:llm-wiki-config --> … <!-- END:llm-wiki-config -->` block listing the vault path and the workflow.
4. **Checks the `qmd` CLI** (https://github.com/tobi/qmd). Optionally builds the index of the vault.
5. **Smoke tests** the vault with `lint_wiki.py`.

Idempotent: rerunning never duplicates the CLAUDE.md block and never overwrites an existing vault.

## Usage

```
/wiki-bootstrap                          # interactive
/wiki-bootstrap --vault ~/path/to/vault  # explicit path
/wiki-bootstrap --verify                 # health check only, no writes
/wiki-bootstrap --with-qmd               # also (re)build the qmd index
/wiki-bootstrap --no-qmd                 # skip qmd entirely
/wiki-bootstrap --non-interactive        # CI mode, fails if config missing
```

## How the agent should run it

1. Locate the script. Try in order:
   - `$REPO_ROOT/scripts/setup-wiki.sh` (when invoked from a Skillz-Claude clone)
   - `$(dirname $0)/scripts/setup-wiki.sh`
   - `~/.claude/skills/skillz-doctor/scripts/setup-wiki.sh` (future fallback)

2. If found, run it forwarding any `$ARGUMENTS`:

   ```bash
   bash <path-to>/scripts/setup-wiki.sh $ARGUMENTS
   ```

3. If not found, tell the user how to clone Skillz-Claude:

   ```
   git clone https://github.com/elsolal/Skillz-Claude-Codex-And-More.git
   bash Skillz-Claude-Codex-And-More/scripts/setup-wiki.sh
   ```

4. Report the resulting vault path back to the user, plus the next-step suggestions printed by the script.

## Notes

- The `qmd` binary itself is **not** vendored — install it separately (`brew install tobi/tap/qmd`).
- The script writes to `~/.claude/CLAUDE.md`. Permissions may prompt; that is expected.
- The vault structure follows the upstream `llm-wiki` schema — see `skills/llm-wiki/SKILL.md` for the full data model.
