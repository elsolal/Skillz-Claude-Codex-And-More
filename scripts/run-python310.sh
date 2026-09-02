#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1

candidates=()
if [ -n "${SKILLZ_PYTHON:-}" ]; then
  candidates+=("$SKILLZ_PYTHON")
fi
candidates+=(python3.13 python3.12 python3.11 python3.10 python3)

detected="not found"
for python_candidate in "${candidates[@]}"; do
  if ! command -v "$python_candidate" >/dev/null 2>&1; then
    continue
  fi
  python_path="$(command -v "$python_candidate")"
  detected="$($python_path --version 2>&1 || true) at $python_path"
  if "$python_path" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    export SKILLZ_SELECTED_PYTHON="$python_path"
    exec "$python_path" "$@"
  fi
done

echo "Python 3.10 or newer is required; detected ${detected}" >&2
exit 1
