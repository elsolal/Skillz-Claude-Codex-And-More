#!/usr/bin/env bash
set -euo pipefail

target_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
if [ ! -d "$target_root" ]; then
  echo "Shell lint root not found: $target_root" >&2
  exit 2
fi

shell_files=()
if [ -f "$target_root/install.sh" ]; then
  shell_files+=("$target_root/install.sh")
fi
for search_root in scripts .claude/scripts tests; do
  if [ ! -d "$target_root/$search_root" ]; then
    continue
  fi
  while IFS= read -r -d '' shell_file; do
    shell_files+=("$shell_file")
  done < <(find "$target_root/$search_root" -type f -name '*.sh' -print0)
done
memory_entrypoint="$target_root/.claude/skills/llm-wiki/bin/memory"
if [ -f "$memory_entrypoint" ]; then
  shell_files+=("$memory_entrypoint")
fi

for shell_file in "${shell_files[@]}"; do
  if ! bash -n "$shell_file"; then
    echo "Shell syntax failed: ${shell_file#"$target_root"/}" >&2
    exit 1
  fi
done

echo "Shell syntax verified: ${#shell_files[@]} files"
