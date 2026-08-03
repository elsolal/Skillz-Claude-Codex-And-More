#!/bin/bash

set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
skill_root="$repo_root/.claude/skills/seo-geo-audit"
v3_root="$skill_root/references/seo-geo-v3"
forbidden_brand="$(printf '\162\157\163\157')"
forbidden_brand_pattern="(^|[^[:alnum:]])${forbidden_brand}[[:alnum:]_-]*"
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
    -s "$v3_root/skill/seo-geo-v3/scripts/advanced/tests" -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 "$python_bin" -m unittest discover \
    -s "$v3_root/skill/seo-geo-v3/scripts/tests" -p 'test_*.py'

node --test "$v3_root/skill/seo-geo-v3/tools/tests/local_file_policy.test.cjs"
node --check "$v3_root/skill/seo-geo-v3/tools/render_html_pdf.cjs"

if rg -n -i -e "$forbidden_brand_pattern" \
    "$skill_root" \
    "$repo_root/.claude/commands/seo-geo-audit.md" \
    "$repo_root/.claude/commands/seo-geo-squad.md" \
    "$repo_root/.codex/prompts/seo-geo-audit.md" \
    "$repo_root/.codex/prompts/seo-geo-squad.md" \
    "$repo_root/.gemini/commands/seo-geo-audit.toml" \
    "$repo_root/.gemini/commands/seo-geo-squad.toml" \
    "$repo_root/.opencode/commands/seo-geo-audit.md" \
    "$repo_root/.opencode/commands/seo-geo-squad.md"; then
    echo "Forbidden vendor branding remains in an active SEO/GEO surface" >&2
    exit 1
fi

temporary_root="$(mktemp -d)"
trap 'rm -rf "$temporary_root"' EXIT

provider_target="$temporary_root/provider-install"
mkdir -p "$provider_target"
bash "$repo_root/install.sh" install "$provider_target" --providers all \
    > "$temporary_root/provider-install.log"
for required_file in \
    "$provider_target/.claude/skills/seo-geo-audit/SKILL.md" \
    "$provider_target/.claude/skills/seo-geo-audit/references/seo-geo-v3/VERSION.json" \
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

legacy_template="$fixture_skill/references/seo-squad/Charte_PDF_${forbidden_brand}Squad.md"
printf 'legacy template\n' > "$legacy_template"
if command -v shasum >/dev/null 2>&1; then
    legacy_template_hash="$(shasum -a 256 "$legacy_template" | awk '{print $1}')"
else
    legacy_template_hash="$(sha256sum "$legacy_template" | awk '{print $1}')"
fi
printf '%s  references/seo-squad/Charte_PDF_{legacy_brand}Squad.md\n' \
    "$legacy_template_hash" > "$fixture_skill/migrations/tokenized.txt"
bash "$repo_root/.claude/scripts/cleanup-legacy-seo-geo.sh" \
    "$fixture_skill" "$fixture_skill/migrations/tokenized.txt"
test ! -e "$legacy_template"

legacy_v3_file="$fixture_skill/references/${forbidden_brand}-v3/START_HERE.md"
mkdir -p "$(dirname "$legacy_v3_file")"
printf 'managed branded V3 file\n' > "$legacy_v3_file"
if command -v shasum >/dev/null 2>&1; then
    legacy_v3_hash="$(shasum -a 256 "$legacy_v3_file" | awk '{print $1}')"
else
    legacy_v3_hash="$(sha256sum "$legacy_v3_file" | awk '{print $1}')"
fi
printf '%s  references/{legacy_brand}-v3/START_HERE.md\n' "$legacy_v3_hash" \
    > "$fixture_skill/migrations/branded-v3.txt"
bash "$repo_root/.claude/scripts/cleanup-legacy-seo-geo.sh" \
    "$fixture_skill" "$fixture_skill/migrations/branded-v3.txt"
test ! -e "$legacy_v3_file"

outside_file="$temporary_root/outside.txt"
printf 'managed legacy file\n' > "$outside_file"
if command -v shasum >/dev/null 2>&1; then
    outside_hash="$(shasum -a 256 "$outside_file" | awk '{print $1}')"
else
    outside_hash="$(sha256sum "$outside_file" | awk '{print $1}')"
fi
printf '%s  references/seo-squad/../../../outside.txt\n' "$outside_hash" \
    > "$fixture_skill/migrations/traversal.txt"
if bash "$repo_root/.claude/scripts/cleanup-legacy-seo-geo.sh" \
    "$fixture_skill" "$fixture_skill/migrations/traversal.txt"; then
    echo "Legacy cleanup accepted a path traversal" >&2
    exit 1
fi
test -e "$outside_file"

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
