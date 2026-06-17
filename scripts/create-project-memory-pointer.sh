#!/usr/bin/env bash

# create-project-memory-pointer.sh - Create local, untracked project memory
# pointers for Claude Code and generic agents.
#
# These files intentionally contain machine-specific paths. This script writes
# them locally and protects them through .git/info/exclude when the target is a
# git repository.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  scripts/create-project-memory-pointer.sh \
    --project-dir PATH \
    --vault-path PATH \
    --qmd-collection NAME \
    [--project-name NAME] \
    [--memory-repo URL] \
    [--start-page PATH]...

Example:
  scripts/create-project-memory-pointer.sh \
    --project-dir ~/code/pleepole-product \
    --project-name pleepole-product \
    --vault-path "$OBSIDIAN_MEMORY_ROOT/Pleepole" \
    --memory-repo https://github.com/Pleepole/pleepole-memory.git \
    --qmd-collection pleepole-wiki \
    --start-page wiki/index.md \
    --start-page wiki/synthesis/pleepole-strategy.md
EOF
}

PROJECT_DIR=""
PROJECT_NAME=""
VAULT_PATH=""
MEMORY_REPO=""
QMD_COLLECTION=""
START_PAGES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-dir)
            PROJECT_DIR="${2:-}"; shift 2;;
        --project-dir=*)
            PROJECT_DIR="${1#*=}"; shift;;
        --project-name)
            PROJECT_NAME="${2:-}"; shift 2;;
        --project-name=*)
            PROJECT_NAME="${1#*=}"; shift;;
        --vault-path)
            VAULT_PATH="${2:-}"; shift 2;;
        --vault-path=*)
            VAULT_PATH="${1#*=}"; shift;;
        --memory-repo)
            MEMORY_REPO="${2:-}"; shift 2;;
        --memory-repo=*)
            MEMORY_REPO="${1#*=}"; shift;;
        --qmd-collection)
            QMD_COLLECTION="${2:-}"; shift 2;;
        --qmd-collection=*)
            QMD_COLLECTION="${1#*=}"; shift;;
        --start-page)
            START_PAGES+=("${2:-}"); shift 2;;
        --start-page=*)
            START_PAGES+=("${1#*=}"); shift;;
        --help|-h)
            usage; exit 0;;
        *)
            printf 'Unknown argument: %s\n' "$1" >&2
            usage >&2
            exit 2;;
    esac
done

if [[ -z "$PROJECT_DIR" || -z "$VAULT_PATH" || -z "$QMD_COLLECTION" ]]; then
    printf 'Missing required arguments.\n\n' >&2
    usage >&2
    exit 2
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
    printf 'Project directory does not exist: %s\n' "$PROJECT_DIR" >&2
    exit 1
fi

PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd -P)"
PROJECT_NAME="${PROJECT_NAME:-$(basename "$PROJECT_DIR")}"

if [[ -d "$VAULT_PATH" ]]; then
    VAULT_PATH="$(cd "$VAULT_PATH" && pwd -P)"
fi

if [[ ${#START_PAGES[@]} -eq 0 ]]; then
    START_PAGES=("wiki/index.md")
fi

CLAUDE_DIR="$PROJECT_DIR/.claude"
AGENTS_DIR="$PROJECT_DIR/.agents"
mkdir -p "$CLAUDE_DIR" "$AGENTS_DIR"

CLAUDE_POINTER="$CLAUDE_DIR/project-memory.md"
AGENTS_POINTER="$AGENTS_DIR/project-memory.md"

{
    printf '# Project Memory - %s\n\n' "$PROJECT_NAME"
    printf -- '- Project name: %s\n' "$PROJECT_NAME"
    printf -- '- Project path: `%s`\n' "$PROJECT_DIR"
    printf -- '- Long-term memory vault: `%s`\n' "$VAULT_PATH"
    if [[ -n "$MEMORY_REPO" ]]; then
        printf -- '- Memory repo: `%s`\n' "$MEMORY_REPO"
    fi
    printf -- '- QMD collection: `%s`\n' "$QMD_COLLECTION"
    printf -- '- Start pages:\n'
    for page in "${START_PAGES[@]}"; do
        printf '  - `%s`\n' "$page"
    done
    cat <<'EOF'

Before non-trivial work:
1. Read this file.
2. Read the relevant wiki index/synthesis/entity pages.
3. Use QMD if the index and linked pages are insufficient.
4. Re-check the live project repo before acting; memory is historical context, not the immediate source of truth.

Session capture: use `/wiki-capture-session` only for durable decisions, conventions, solved problems, validation commands, and next steps.

Git rule: this file is machine-specific and must stay ignored by Git.
EOF
} > "$CLAUDE_POINTER"

{
    printf '# Project Memory - %s\n\n' "$PROJECT_NAME"
    printf 'Read `.claude/project-memory.md` for the canonical local memory pointer.\n\n'
    printf 'Memory vault: `%s`\n' "$VAULT_PATH"
    printf 'QMD collection: `%s`\n' "$QMD_COLLECTION"
    if [[ -n "$MEMORY_REPO" ]]; then
        printf 'Memory repo: `%s`\n' "$MEMORY_REPO"
    fi
    printf '\nGit rule: this file is machine-specific and must stay ignored by Git.\n'
} > "$AGENTS_POINTER"

if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    GIT_DIR="$(git -C "$PROJECT_DIR" rev-parse --git-dir)"
    if [[ "$GIT_DIR" != /* ]]; then
        GIT_DIR="$PROJECT_DIR/$GIT_DIR"
    fi
    EXCLUDE_FILE="$GIT_DIR/info/exclude"
    mkdir -p "$(dirname "$EXCLUDE_FILE")"
    touch "$EXCLUDE_FILE"
    if ! grep -q '# Local agent memory pointers' "$EXCLUDE_FILE"; then
        printf '\n# Local agent memory pointers (machine-specific, not shared)\n' >> "$EXCLUDE_FILE"
    fi
    for pattern in \
        '.claude/project-memory.md' \
        '.agents/project-memory.md' \
        '.claude/project-memory.local.md' \
        '.agents/project-memory.local.md'
    do
        if ! grep -qxF "$pattern" "$EXCLUDE_FILE"; then
            printf '%s\n' "$pattern" >> "$EXCLUDE_FILE"
        fi
    done
fi

printf 'Created local project memory pointers:\n'
printf -- '- %s\n' "$CLAUDE_POINTER"
printf -- '- %s\n' "$AGENTS_POINTER"
printf 'These files are local-only. Do not commit them.\n'
