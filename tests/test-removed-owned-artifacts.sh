#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cleanup_script="$repo_root/scripts/cleanup-removed-owned-artifacts.sh"
fixture_root="$(mktemp -d)"
trap 'rm -rf "$fixture_root"' EXIT

source_root="$fixture_root/source"
target_root="$fixture_root/target"
mkdir -p "$source_root" "$target_root/commands" "$target_root/config"

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

sha256_text() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 | awk '{print $1}'
  else
    sha256sum | awk '{print $1}'
  fi
}

printf 'replacement\n' > "$source_root/settings.json"
printf 'owned legacy\n' > "$target_root/commands/owned.md"
printf 'user edit\n' > "$target_root/commands/preserved.md"
printf 'old settings\n' > "$target_root/config/settings.json"

owned_hash="$(sha256_file "$target_root/commands/owned.md")"
preserved_original_hash="$(printf 'original managed bytes\n' | sha256_text)"
settings_hash="$(sha256_file "$target_root/config/settings.json")"

manifest="$fixture_root/removed-artifacts.sha256"
{
  printf 'delete %s commands/owned.md\n' "$owned_hash"
  printf 'delete %s commands/preserved.md\n' "$preserved_original_hash"
  printf 'replace %s config/settings.json settings.json\n' "$settings_hash"
} > "$manifest"

output="$(bash "$cleanup_script" "$manifest" "$target_root" "$source_root")"

test ! -e "$target_root/commands/owned.md"
test "$(cat "$target_root/commands/preserved.md")" = "user edit"
test "$(cat "$target_root/config/settings.json")" = "replacement"
printf '%s\n' "$output" | grep -q 'removed=1 replaced=1 preserved=1'

unsafe_manifest="$fixture_root/unsafe.sha256"
printf 'delete %s ../outside.md\n' "$owned_hash" > "$unsafe_manifest"
if bash "$cleanup_script" "$unsafe_manifest" "$target_root" "$source_root" >/dev/null 2>&1; then
  echo "Expected unsafe migration path to be rejected" >&2
  exit 1
fi

echo "Removed-artifact cleanup verification passed"
