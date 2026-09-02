#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
temporary_root=$(mktemp -d)
trap 'rm -rf "$temporary_root"' EXIT

head_sha=$(git -C "$repo_root" rev-parse HEAD)
if git -C "$repo_root" rev-parse HEAD^ >/dev/null 2>&1; then
  base_sha=$(git -C "$repo_root" rev-parse HEAD^)
else
  base_sha="$head_sha"
fi

result_output="${SKILLZ_RUN_RESULT_OUTPUT:-$temporary_root/run-result.json}"
failure_output="${SKILLZ_FAILURE_OUTPUT:-$temporary_root/failures}"
mkdir -p "$(dirname "$result_output")" "$(dirname "$failure_output")"

bash "$repo_root/tests/run-python310.sh" "$repo_root/tooling/testing/behavioral_harness.py" \
  --cases "$repo_root/behavioral/cases" \
  --repeat 1 \
  --jobs 4 \
  --base-sha "$base_sha" \
  --head-sha "$head_sha" \
  --output "$result_output" \
  --failure-dir "$failure_output" \
  --root "$repo_root"

python_bin=$(bash "$repo_root/tests/run-python310.sh" -c 'import sys; print(sys.executable)')
"$python_bin" - "$result_output" <<'PY'
import json
from pathlib import Path
import sys

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("schema_version") != 1 or payload.get("summary", {}).get("failed") != 0:
    raise SystemExit("behavioral run-result is invalid or contains failures")
print(f"Behavioral structural cases passed: {payload['summary']['passed']}")
PY
