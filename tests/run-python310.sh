#!/bin/bash

set -euo pipefail

for python_candidate in python3 python3.13 python3.12 python3.11 python3.10; do
    if command -v "$python_candidate" >/dev/null 2>&1 \
        && "$python_candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
        python_path="$(command -v "$python_candidate")"
        PATH="$(dirname "$python_path"):$PATH"
        export PATH
        exec "$python_path" "$@"
    fi
done

echo "Python 3.10 or newer is required" >&2
exit 1
