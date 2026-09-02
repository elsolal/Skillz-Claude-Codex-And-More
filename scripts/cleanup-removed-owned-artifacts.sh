#!/usr/bin/env bash
set -euo pipefail

manifest="${1:-}"
target_root="${2:-}"
source_root="${3:-}"

if [ -z "$manifest" ] || [ -z "$target_root" ] || [ -z "$source_root" ]; then
  echo "Usage: $0 <manifest> <target-root> <source-root>" >&2
  exit 2
fi
if [ ! -f "$manifest" ]; then
  echo "Removed-artifact manifest not found: $manifest" >&2
  exit 2
fi
if [ ! -d "$target_root" ] || [ "$target_root" = "/" ]; then
  echo "Unsafe or missing target root: $target_root" >&2
  exit 2
fi
if [ ! -d "$source_root" ]; then
  echo "Source root not found: $source_root" >&2
  exit 2
fi

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    echo "No SHA-256 command available (expected shasum or sha256sum)" >&2
    return 2
  fi
}

validate_relative_path() {
  case "$1" in
    ""|/*|..|../*|*/../*|*/..)
      return 1
      ;;
  esac
  return 0
}

removed=0
replaced=0
preserved=0

while read -r action expected_hash relative_path replacement_path; do
  [ -z "${action:-}" ] && continue
  case "$action" in \#*) continue ;; esac

  if ! validate_relative_path "${relative_path:-}"; then
    echo "Unsafe migration path: ${relative_path:-<empty>}" >&2
    exit 2
  fi
  target="$target_root/$relative_path"
  if [ ! -e "$target" ] && [ ! -L "$target" ]; then
    continue
  fi
  if [ -L "$target" ] || [ ! -f "$target" ]; then
    echo "Preserved non-regular target: $relative_path" >&2
    preserved=$((preserved + 1))
    continue
  fi

  actual_hash="$(sha256_file "$target")"
  if [ "$actual_hash" != "$expected_hash" ]; then
    echo "Preserved modified target: $relative_path" >&2
    preserved=$((preserved + 1))
    continue
  fi

  case "$action" in
    delete)
      rm -f -- "$target"
      removed=$((removed + 1))
      ;;
    replace)
      if ! validate_relative_path "${replacement_path:-}"; then
        echo "Unsafe replacement path: ${replacement_path:-<empty>}" >&2
        exit 2
      fi
      replacement="$source_root/$replacement_path"
      if [ -L "$replacement" ] || [ ! -f "$replacement" ]; then
        echo "Replacement source missing or unsafe: $replacement_path" >&2
        exit 2
      fi
      temporary="$(mktemp "${target}.skillz.XXXXXX")"
      cp "$replacement" "$temporary"
      replacement_mode="$(stat -f %Lp "$replacement" 2>/dev/null || stat -c %a "$replacement")"
      chmod "$replacement_mode" "$temporary"
      mv -f -- "$temporary" "$target"
      replaced=$((replaced + 1))
      ;;
    *)
      echo "Unsupported migration action: $action" >&2
      exit 2
      ;;
  esac
done < "$manifest"

echo "Removed-artifact cleanup: removed=$removed replaced=$replaced preserved=$preserved"
