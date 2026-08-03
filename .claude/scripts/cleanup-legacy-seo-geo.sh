#!/bin/bash

# Remove only unmodified, Skillz-managed SEO/GEO V1 files after a V3 update.
# User-modified or unknown files are preserved and reported.

set -eu

skill_root="${1:-}"
checksum_file="${2:-${skill_root}/migrations/legacy-v1-sha256.txt}"

if [ -z "$skill_root" ] || [ ! -d "$skill_root" ] || [ ! -f "$checksum_file" ]; then
    exit 0
fi

hash_file() {
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        sha256sum "$1" | awk '{print $1}'
    fi
}

removed=0
preserved=0
legacy_brand="$(printf '\162\157\163\157')"
while IFS='  ' read -r expected relative_file; do
    [ -z "$expected" ] && continue
    case "$expected" in \#*) continue ;; esac
    relative_file="${relative_file# }"
    relative_file="${relative_file//\{legacy_brand\}/$legacy_brand}"
    case "$relative_file" in
        /*|../*|*/../*|*/..|*\\*)
            echo "Refusing unsafe legacy cleanup path: $relative_file" >&2
            exit 2
            ;;
    esac
    case "$relative_file" in
        references/seo-squad-framework.md|references/seo-squad/*|references/${legacy_brand}-v3/*) ;;
        *)
            echo "Refusing unsafe legacy cleanup path: $relative_file" >&2
            exit 2
            ;;
    esac
    target_file="$skill_root/$relative_file"
    [ -f "$target_file" ] || continue
    actual="$(hash_file "$target_file")"
    if [ "$actual" = "$expected" ]; then
        rm -f "$target_file"
        removed=$((removed + 1))
    else
        echo "Preserved modified legacy SEO/GEO file: $target_file" >&2
        preserved=$((preserved + 1))
    fi
done < "$checksum_file"

for legacy_dir in \
    "$skill_root/references/seo-squad" \
    "$skill_root/references/${legacy_brand}-v3"; do
    if [ -d "$legacy_dir" ]; then
        find "$legacy_dir" -depth -type d -empty -exec rmdir {} \; 2>/dev/null || true
    fi
done

echo "SEO/GEO legacy cleanup: removed=$removed preserved=$preserved"
