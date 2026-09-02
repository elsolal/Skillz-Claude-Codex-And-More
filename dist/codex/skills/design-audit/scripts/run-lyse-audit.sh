#!/usr/bin/env bash
set -euo pipefail

target="${1:-.}"

if ! command -v node >/dev/null 2>&1; then
  echo "Lyse skipped: node is not installed" >&2
  exit 78
fi

node_major="$(node -p 'Number(process.versions.node.split(".")[0])')"
if [ "$node_major" -lt 22 ]; then
  echo "Lyse skipped: Node >= 22 required, found $(node -v)" >&2
  exit 78
fi

LYSE_NO_MENU=1 \
LYSE_NO_EMAIL_PROMPT=1 \
LYSE_NO_EMAIL_POST=1 \
npx -y @lyse-labs/lyse@0.2.0-alpha.1 audit "$target" \
  --format=json \
  --limit=all \
  --static-only \
  --no-telemetry \
  --no-prompt \
  --yes \
  --quiet
