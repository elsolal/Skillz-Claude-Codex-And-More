#!/usr/bin/env bash

# Compatibility wrapper for the historical pointer generator.
# The Python `memory configure` command is now the single source of truth.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  scripts/create-project-memory-pointer.sh \
    --project-dir PATH \
    --vault-path PATH \
    [--role owner|collaborator] \
    [--replace-managed] \
    [--explain-local-paths] \
    [legacy metadata options]

Legacy metadata options remain accepted during migration, but their values are
now read from the project's versioned .agents/memory.yaml manifest:
  --project-name NAME
  --memory-repo URL
  --qmd-collection NAME
  --start-page PATH

Prefer the canonical command for new automation:
  memory configure --store project=/absolute/path/to/vault
EOF
}

script_dir="$(cd -P "$(dirname "$0")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
memory_bin="$repo_root/.claude/skills/llm-wiki/bin/memory"

project_dir=""
vault_path=""
role="collaborator"
replace_managed=false
explain_local_paths=false
legacy_metadata_seen=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-dir)
            project_dir="${2:-}"; shift 2;;
        --project-dir=*)
            project_dir="${1#*=}"; shift;;
        --vault-path)
            vault_path="${2:-}"; shift 2;;
        --vault-path=*)
            vault_path="${1#*=}"; shift;;
        --role)
            role="${2:-}"; shift 2;;
        --role=*)
            role="${1#*=}"; shift;;
        --replace-managed)
            replace_managed=true; shift;;
        --explain-local-paths)
            explain_local_paths=true; shift;;
        --project-name|--memory-repo|--qmd-collection|--start-page)
            if [[ -z "${2:-}" ]]; then
                printf 'Missing value for %s.\n' "$1" >&2
                exit 2
            fi
            legacy_metadata_seen=true
            shift 2;;
        --project-name=*|--memory-repo=*|--qmd-collection=*|--start-page=*)
            legacy_metadata_seen=true
            shift;;
        --help|-h)
            usage; exit 0;;
        *)
            printf 'Unknown argument: %s\n' "$1" >&2
            usage >&2
            exit 2;;
    esac
done

if [[ -z "$project_dir" || -z "$vault_path" ]]; then
    printf 'Missing required --project-dir or --vault-path.\n\n' >&2
    usage >&2
    exit 2
fi

if [[ ! -d "$project_dir" ]]; then
    printf 'Project directory does not exist: %s\n' "$project_dir" >&2
    exit 30
fi

if [[ ! -x "$memory_bin" ]]; then
    printf 'Portable memory CLI is unavailable: %s\n' "$memory_bin" >&2
    exit 31
fi

if [[ "$legacy_metadata_seen" == true ]]; then
    printf 'Warning: legacy metadata options are deprecated; .agents/memory.yaml is authoritative.\n' >&2
fi

configure_args=(
    configure
    --store "project=$vault_path"
    --role "$role"
)
if [[ "$replace_managed" == true ]]; then
    configure_args+=(--replace-managed)
fi
if [[ "$explain_local_paths" == true ]]; then
    configure_args+=(--explain-local-paths)
fi

cd "$project_dir"
exec "$memory_bin" "${configure_args[@]}"
