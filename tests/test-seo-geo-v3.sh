#!/bin/bash

set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
skill_root="$repo_root/.claude/skills/seo-geo-audit"
v3_root="$skill_root/references/roso-v3"
python_bin=""

for candidate in python3 python3.13 python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
        python_bin="$candidate"
        break
    fi
done

if [ -z "$python_bin" ]; then
    echo "Python 3.10+ is required for the SEO/GEO V3 tests" >&2
    exit 1
fi

PYTHONDONTWRITEBYTECODE=1 "$python_bin" "$v3_root/install.py" --check
PYTHONDONTWRITEBYTECODE=1 "$python_bin" "$v3_root/tools/build_manifest.py" --verify
PYTHONDONTWRITEBYTECODE=1 "$python_bin" -m unittest discover \
    -s "$v3_root/skill/roso-seo-geo-v3/scripts/advanced/tests" -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 "$python_bin" -m unittest discover \
    -s "$v3_root/skill/roso-seo-geo-v3/scripts/tests" -p 'test_*.py'

node --test "$v3_root/skill/roso-seo-geo-v3/tools/tests/local_file_policy.test.cjs"
node --check "$v3_root/skill/roso-seo-geo-v3/tools/render_html_pdf.cjs"

temporary_root="$(mktemp -d)"
trap 'rm -rf "$temporary_root"' EXIT

provider_target="$temporary_root/provider-install"
mkdir -p "$provider_target"
bash "$repo_root/install.sh" install "$provider_target" --providers all \
    > "$temporary_root/provider-install.log"
for required_file in \
    "$provider_target/.claude/skills/seo-geo-audit/SKILL.md" \
    "$provider_target/.claude/skills/seo-geo-audit/references/roso-v3/VERSION.json" \
    "$provider_target/.codex/prompts/seo-geo-audit.md" \
    "$provider_target/.gemini/commands/seo-geo-squad.toml" \
    "$provider_target/.opencode/commands/seo-geo-audit.md"; do
    test -e "$required_file" || {
        echo "Provider smoke install is missing $required_file" >&2
        exit 1
    }
done

fixture_skill="$temporary_root/seo-geo-audit"
mkdir -p "$fixture_skill/references/seo-squad" "$fixture_skill/migrations"
printf 'managed legacy file\n' > "$fixture_skill/references/seo-squad/README.md"
if command -v shasum >/dev/null 2>&1; then
    fixture_hash="$(shasum -a 256 "$fixture_skill/references/seo-squad/README.md" | awk '{print $1}')"
else
    fixture_hash="$(sha256sum "$fixture_skill/references/seo-squad/README.md" | awk '{print $1}')"
fi
printf '%s  references/seo-squad/README.md\n' "$fixture_hash" > "$fixture_skill/migrations/checksums.txt"
bash "$repo_root/.claude/scripts/cleanup-legacy-seo-geo.sh" \
    "$fixture_skill" "$fixture_skill/migrations/checksums.txt"
test ! -e "$fixture_skill/references/seo-squad/README.md"

mkdir -p "$fixture_skill/references/seo-squad"
printf 'user modified legacy file\n' > "$fixture_skill/references/seo-squad/README.md"
bash "$repo_root/.claude/scripts/cleanup-legacy-seo-geo.sh" \
    "$fixture_skill" "$fixture_skill/migrations/checksums.txt"
test -e "$fixture_skill/references/seo-squad/README.md"

if rg -n 'references/seo-squad/|seo-squad-framework|[Ee]xecute (the )?11-agent|exécuter.*11 agents|orchestration complète.*11 agents' \
    "$skill_root/SKILL.md" \
    "$repo_root/.claude/commands/seo-geo-audit.md" \
    "$repo_root/.claude/commands/seo-geo-squad.md" \
    "$repo_root/.codex/prompts/seo-geo-audit.md" \
    "$repo_root/.codex/prompts/seo-geo-squad.md" \
    "$repo_root/.gemini/commands/seo-geo-audit.toml" \
    "$repo_root/.gemini/commands/seo-geo-squad.toml" \
    "$repo_root/.opencode/commands/seo-geo-audit.md" \
    "$repo_root/.opencode/commands/seo-geo-squad.md"; then
    echo "Legacy SEO/GEO routing remains in an active launcher" >&2
    exit 1
fi

echo "SEO/GEO V3 verification passed"
